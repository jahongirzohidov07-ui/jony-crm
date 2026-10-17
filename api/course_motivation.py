"""Canonical course rewards, spaced review and opt-in weekly cooperation.

No migrations: IntegrationSetting's primary key serializes learner writes;
XpTransaction's unique idempotency key claims rewards. Coins and attempts
commit in the same transaction. No AI decides correctness or mastery.
"""
import json
import re
import secrets
from datetime import datetime, timedelta
from pathlib import Path
from functools import lru_cache

from fastapi import HTTPException
from sqlalchemy import func
import models

PREFIX = "course-reward:v1:"
DAILY_TARGET = 5
REVIEW_INTERVALS = (1, 3, 7, 14)
ZERO = {"xp": 0, "coins": 0, "reason": "none"}


def now():
    return datetime.utcnow()


def local_day():
    return (now() + timedelta(hours=5)).date()


def calendar_week():
    return local_day().strftime("%G-W%V")


def practice():
    import student_course_practice
    return student_course_practice


def insert(db, table):
    if db.get_bind().dialect.name == "sqlite":
        from sqlalchemy.dialects.sqlite import insert as dialect_insert
    else:
        from sqlalchemy.dialects.postgresql import insert as dialect_insert
    return dialect_insert(table)


def put(db, key, value):
    table = models.IntegrationSetting.__table__
    stmt = insert(db, table).values(key=key, value=json.dumps(value), updated_at=now())
    db.execute(stmt.on_conflict_do_update(index_elements=[table.c.key],
        set_={"value": stmt.excluded.value, "updated_at": stmt.excluded.updated_at}))


def get(db, key, default=None):
    value = db.query(models.IntegrationSetting.value).filter_by(key=key).scalar()
    return json.loads(value) if value else default


def lock(db, student_id):
    # An actual DB write lock, not a process-local mutex or check-then-insert.
    # PostgreSQL and SQLite hold this until the enclosing transaction ends.
    put(db, f"course-lock:v1:{student_id}", True)


@lru_cache(maxsize=2)
def exact_questions(language):
    return {q["id"]: (row, section, q)
            for row in practice().BANK[language] for section in row["sections"]
            for q in section["questions"] if q["mode"] == "exact" and q.get("expected")}


def grade(question, answer):
    normalize = practice()._normalize
    sensitive = question.get("caseSensitive", False)
    return any(normalize(answer, sensitive) == normalize(e, sensitive)
               for e in question["expected"])


def txs(db, student_id, language):
    return db.query(models.XpTransaction).filter(
        models.XpTransaction.student_id == student_id,
        models.XpTransaction.idempotency_key.startswith(f"{PREFIX}{student_id}:{language}:"),
        models.XpTransaction.is_reversal == 0)


def demo_student(db, student):
    # The legacy global student leaderboard does not filter test branches.
    # Keep course demo practice usable, but never fund its global XP/coin ledger.
    if "(demo)" in student.full_name.casefold():
        return True
    branch = db.get(models.Branch, student.branch_id) if student.branch_id else None
    user = db.get(models.User, student.user_id) if student.user_id else None
    return bool((branch and branch.is_test) or
                (user and user.username.casefold().startswith("demo.")))


def reward(db, student, language, token, kind, xp, coins, question_id=None):
    if demo_student(db, student):
        return dict(ZERO)
    from common import _active_season, _recalc_gamification, _xp_rule, _rule_cap_hit
    # All course reward writers already hold the learner lock. Cap both
    # languages together so parallel calls or language switching cannot farm.
    day_start = datetime.combine(local_day(), datetime.min.time()) - timedelta(hours=5)
    count = db.query(models.XpTransaction.id).filter(
        models.XpTransaction.student_id == student.id,
        models.XpTransaction.idempotency_key.startswith(PREFIX),
        models.XpTransaction.created_at >= day_start,
        models.XpTransaction.created_at < day_start + timedelta(days=1),
    ).count()
    if count >= 20:
        return dict(ZERO, reason="daily_limit")
    rule = _xp_rule(db, "course_" + kind)
    if rule and not rule.is_active:
        return dict(ZERO)
    if rule and _rule_cap_hit(db, student.id, rule, local_day(), None):
        return dict(ZERO, reason="daily_limit")
    season = _active_season(db)
    meta = {"language": language, "day": local_day().isoformat(),
            "week": calendar_week(), "question_id": question_id, "kind": kind}
    stmt = insert(db, models.XpTransaction.__table__).values(
        student_id=student.id, amount=xp, category="academic",
        event_code="course_" + kind, source_type="course_motivation",
        group_id=student.group_id, branch_id=student.branch_id,
        season_id=season.id if season else None,
        idempotency_key=f"{PREFIX}{student.id}:{language}:{token}",
        meta=json.dumps(meta), reason="Verified course practice: " + kind,
        created_at=now(), updated_at=now(), is_reversal=0,
    ).on_conflict_do_nothing(index_elements=["idempotency_key"]).returning(models.XpTransaction.id)
    transaction_id = db.execute(stmt).scalar()
    if transaction_id is None:
        return dict(ZERO)
    if coins:
        db.add(models.CoinEntry(student_id=student.id, amount=coins,
               source="course_motivation:" + language, ref_id=transaction_id,
               note="Verified course practice: " + kind, created_at=now()))
    db.flush()
    _recalc_gamification(db, student.id, commit=False)
    return {"xp": xp, "coins": coins, "reason": kind}


def state_key(student_id, qid):
    return f"course-review:v1:{student_id}:{qid}"


def practice_reward(db, student, language, question, correct):
    if question["mode"] != "exact":
        return dict(ZERO)
    lock(db, student.id)
    previous = db.query(models.SkillAttempt).filter_by(
        student_id=student.id, ref=practice()._ref(question["id"])).all()
    mastered = next((a for a in previous if a.correct == 1), None)
    if mastered is not None:
        # Ordinary answer feedback reveals the key. Require another day before
        # rewarding recall instead of paying for copying freshly shown feedback.
        state = review_state(db, student.id, question["id"], mastered.created_at)
        if not correct:
            # Scheduling restarts after forgetting; reward-stage keys do NOT.
            state["stage"] = 0
            state["due"] = (local_day() + timedelta(days=1)).isoformat()
        else:
            state["due"] = max(state["due"], (local_day() + timedelta(days=1)).isoformat())
        put(db, state_key(student.id, question["id"]), state)
        return dict(ZERO)
    if not correct:
        put(db, state_key(student.id, question["id"]),
            {"stage": 0, "due": (local_day() + timedelta(days=1)).isoformat()})
        return dict(ZERO)
    kind = "correction" if previous else "practice_correct"
    earned = reward(db, student, language, "master:" + question["id"], kind,
                    2, 0, question["id"])
    if earned["xp"]:
        put(db, state_key(student.id, question["id"]),
            {"stage": 0, "due": (local_day() + timedelta(days=1)).isoformat()})
    return earned


def question_attempts(db, student_id, language):
    return db.query(models.SkillAttempt).filter(
        models.SkillAttempt.student_id == student_id,
        (models.SkillAttempt.ref.startswith("course-practice:v1:" + language + ":") |
         models.SkillAttempt.ref.startswith("course-review:v1:" + language + ":")),
    ).order_by(models.SkillAttempt.id).all()


def attempt_qid(attempt):
    return attempt.ref.split(":v1:", 1)[1]


def canonical_questions(language):
    return {q["id"]: (row, section, q)
            for row in practice().BANK[language] for section in row["sections"]
            for q in section["questions"]}


def meaningful(attempt):
    return bool(attempt.answer and any(c.isalnum() for c in attempt.answer))


def learning_attempts(db, student_id, language):
    known = canonical_questions(language)
    return [a for a in question_attempts(db, student_id, language)
            if attempt_qid(a) in known and meaningful(a) and a.created_at <= now()]


def exact_history(db, student_id, language):
    history = {}
    for a in learning_attempts(db, student_id, language):
        if attempt_qid(a) in exact_questions(language):
            history.setdefault(attempt_qid(a), []).append(a)
    for rows in history.values():
        rows.sort(key=lambda a: (a.created_at, a.id))
    return history


def delayed_attempts(rows):
    first = next((a.created_at for a in rows if a.correct == 1), None)
    return [a for a in rows if first is not None
            and a.ref.startswith("course-review:v1:")
            and a.created_at >= first + timedelta(hours=24)]


def mastery(db, student_id, language):
    """Durable evidence requires delayed recall and a currently correct answer."""
    return {qid: next(a.created_at for a in rows if a.correct == 1)
            for qid, rows in exact_history(db, student_id, language).items()
            if rows[-1].correct == 1 and any(
                a.correct == 1 and (a.created_at, a.id) > max(
                    ((failure.created_at, failure.id) for failure in rows if failure.correct != 1),
                    default=(datetime.min, 0)) for a in delayed_attempts(rows))}


def latest_attempts(db, student_id, language):
    return {qid: rows[-1] for qid, rows in exact_history(db, student_id, language).items()}


def lesson_coverage(language, question_ids):
    result = set()
    question_ids = set(question_ids)
    for row in practice().BANK[language]:
        available, covered = {}, {}
        for section in row["sections"]:
            ids = {q["id"] for q in section["questions"]
                   if q["mode"] == "exact" and q.get("expected")}
            if ids:
                available[section["id"]] = ids
                covered[section["id"]] = ids & question_ids
        count = sum(map(len, available.values()))
        if (count and sum(map(len, covered.values())) >= min(3, count)
                and sum(bool(ids) for ids in covered.values()) >= min(2, len(available))):
            result.add(row["lesson"])
    return result


def ready_lessons(db, student_id, language):
    return lesson_coverage(language, {qid for qid, a in latest_attempts(db, student_id, language).items()
                                     if a.correct == 1})


def evidence(db, student_id, language):
    """Distinct questions: first exact result and latest eligible delayed review result.

    Comparison pairs the earliest normal exact attempt with the latest eligible
    delayed review of the same question; questions without both are excluded.
    Historical first-attempt results stay fixed; delayed recall can regress.
    Neither self assessment nor XP is evidence of verified language proficiency.
    """
    known = canonical_questions(language)
    attempts = learning_attempts(db, student_id, language)
    history = exact_history(db, student_id, language)
    delayed = {qid: delayed_attempts(rows) for qid, rows in history.items()}
    comparison = {"total": 0, "before_correct": 0, "after_correct": 0}
    for qid, reviews in delayed.items():
        if not reviews:
            continue
        baseline = next((a for a in history[qid]
                         if a.ref.startswith("course-practice:v1:")), None)
        latest = reviews[-1]
        if baseline is None or (baseline.created_at, baseline.id) >= (latest.created_at, latest.id):
            continue
        comparison["total"] += 1
        comparison["before_correct"] += int(baseline.correct == 1)
        comparison["after_correct"] += int(latest.correct == 1)
    skills = []
    for skill in sorted({section["skill"] for _, section, _ in known.values()}):
        items = {qid: rows for qid, rows in history.items() if known[qid][1]["skill"] == skill}
        activity = [a for a in attempts if known[attempt_qid(a)][1]["skill"] == skill]
        dates = [a.created_at for a in activity]
        skills.append({"skill": skill, "correct": sum(rows[-1].correct == 1 for rows in items.values()),
                       "total": len(items),
                       "self_assessed": len({attempt_qid(a) for a in activity
                                             if known[attempt_qid(a)][2]["mode"] == "self"}),
                       "first_attempt_at": min(dates).isoformat() + "Z" if dates else None,
                       "last_attempt_at": max(dates).isoformat() + "Z" if dates else None})
    return {"lessons": {"ready": len(ready_lessons(db, student_id, language)),
                        "total": len(practice().BANK[language]),
                        "retained": len(mastered_lessons(db, student_id, language))},
            "first_attempt": {"correct": sum(rows[0].correct == 1 for rows in history.values()), "total": len(history)},
            "delayed_recall": {"correct": sum(bool(rows) and rows[-1].correct == 1 for rows in delayed.values()),
                               "total": sum(bool(rows) for rows in delayed.values())},
            "comparison": comparison,
            "skills": skills,
            "since": min(a.created_at for a in attempts).isoformat() + "Z" if attempts else None}


def daily_effort(db, student_id, language):
    start = datetime.combine(local_day(), datetime.min.time()) - timedelta(hours=5)
    end = start + timedelta(days=1)
    done = {attempt_qid(a) for a in learning_attempts(db, student_id, language)
            if start <= a.created_at < end}
    checkpoint_ids = {q["id"] for row in checkpoint_bank(language).values() for q in row["questions"]}
    for a in db.query(models.SkillAttempt).filter(
            models.SkillAttempt.student_id == student_id,
            models.SkillAttempt.ref.startswith("course-challenge:v1:" + language + ":"),
            models.SkillAttempt.created_at >= start,
            models.SkillAttempt.created_at < end,
            models.SkillAttempt.created_at <= now()).all():
        if attempt_qid(a) in checkpoint_ids and meaningful(a):
            done.add(attempt_qid(a))
    return done


def daily_plan(db, student_id, language, reviews):
    # motivation() already holds the learner lock: competing reads cannot replace a plan.
    key = f"course-plan:v1:{student_id}:{language}:current"
    saved = get(db, key)
    if saved and saved.get("day") != local_day().isoformat():
        saved = None
    attempts = learning_attempts(db, student_id, language)
    if saved is None:
        known = canonical_questions(language)
        latest = latest_attempts(db, student_id, language)
        current = practice()._resume(db, student_id, language)
        wrong = sorted((a for a in latest.values() if a.correct == 0),
                       key=lambda a: (a.created_at, a.id), reverse=True)
        weak = known[attempt_qid(wrong[0])][0]["lesson"] if wrong else current
        selected = []

        def add(qid, kind, reason):
            if qid in {step["question_id"] for step in selected}:
                return
            row, section, question = known[qid]
            selected.append({"id": f"{local_day()}:{language}:{len(selected) + 1}:{qid}",
                             "kind": kind, "lesson": row["lesson"], "question_id": qid,
                             "title": section["title"], "reason": reason, "minutes": 5})

        if reviews:
            add(reviews[0]["id"], "review", "Vaqti kelgan savolni yoddan takrorlang.")
        candidates = sorted(exact_questions(language), key=lambda qid: (
            known[qid][0]["lesson"] != weak,
            not (qid in latest and latest[qid].correct == 0),
            qid in latest, known[qid][0]["lesson"], qid))
        for qid in candidates:
            if len(selected) >= 2:
                break
            add(qid, "practice", "Xatoni tuzating yoki yangi savolni bajaring.")
        self_items = [qid for qid, (row, section, q) in known.items()
                      if row["lesson"] == current and q["mode"] == "self"]
        self_items.sort(key=lambda qid: known[qid][1]["skill"] != "speaking")
        if self_items:
            qid = self_items[0]
            kind = "speaking" if language == "en" and known[qid][1]["skill"] == "speaking" else "practice"
            add(qid, kind, "Mustaqil javob bering; bu harakat, bilim bahosi emas.")
        else:
            for qid in candidates:
                if len(selected) >= 3:
                    break
                add(qid, "practice", "Darsdagi keyingi savolni bajaring.")
        if selected:
            selected[-1]["minutes"] += 15 - sum(step["minutes"] for step in selected)
        saved = {"day": local_day().isoformat(), "created_at": now().isoformat(), "after_id": max((a.id for a in attempts), default=0), "steps": selected}
        put(db, key, saved)
    visible = {item["id"] for item in reviews}
    changed = False
    for step in saved["steps"]:
        if step["kind"] == "review" and step["question_id"] not in visible:
            # Feedback exposure can defer a frozen review target. Keep its identity
            # and action reachable; exposure alone never completes the task.
            step["kind"] = "practice"
            step["reason"] = "Takrorlash hozir yopiq. Shu savolni mashq qiling; bu recall bahosi emas."
            changed = True
    if changed:
        put(db, key, saved)
    start = max(datetime.fromisoformat(saved["created_at"]),
                datetime.combine(local_day(), datetime.min.time()) - timedelta(hours=5))
    end = datetime.combine(local_day() + timedelta(days=1), datetime.min.time()) - timedelta(hours=5)
    completed = {attempt_qid(a) for a in attempts
                 if start <= a.created_at < end and a.id > saved["after_id"]}
    steps = [step | {"done": step["question_id"] in completed} for step in saved["steps"]]
    return {"minutes": 15, "steps": steps, "completed": bool(steps) and all(step["done"] for step in steps)}


def get_many(db, keys):
    if not keys:
        return {}
    return {key: json.loads(value) for key, value in db.query(
        models.IntegrationSetting.key, models.IntegrationSetting.value
    ).filter(models.IntegrationSetting.key.in_(keys)).all() if value}


def review_state(db, student_id, qid, first_correct):
    return get(db, state_key(student_id, qid), {
        "stage": 0,
        "due": ((first_correct + timedelta(hours=5)).date() + timedelta(days=1)).isoformat(),
    })


def queue(db, student_id, language):
    key = f"course-review-day:v1:{student_id}:{language}:{local_day()}"
    ids = get(db, key)
    if ids is None:
        latest = latest_attempts(db, student_id, language)
        states = get_many(db, [state_key(student_id, qid) for qid in latest])
        due = []
        for qid, attempt in latest.items():
            state = states.get(state_key(student_id, qid), {
                "stage": 0,
                "due": ((attempt.created_at + timedelta(hours=5)).date() + timedelta(days=1)).isoformat(),
            })
            if (attempt.correct == 0 or state["stage"] < len(REVIEW_INTERVALS)) and state["due"] <= local_day().isoformat():
                # Unresolved errors first, then oldest due recall.
                due.append((attempt.correct, state["due"], qid))
        ids = [qid for _, _, qid in sorted(due)[:DAILY_TARGET]]
        put(db, key, ids)
    return ids


def expose_feedback(db, student_id, questions):
    """Record exact saved-answer feedback exposure without changing its payload."""
    if not questions:
        return
    lock(db, student_id)
    states = get_many(db, [state_key(student_id, qid) for qid in questions])
    tomorrow = (local_day() + timedelta(days=1)).isoformat()
    for qid, attempted_at in questions.items():
        state = states.get(state_key(student_id, qid), {"stage": 0, "due": tomorrow})
        state["due"] = max(state["due"], tomorrow)
        state["exposed_on"] = local_day().isoformat()
        put(db, state_key(student_id, qid), state)


def visible_review_ids(db, student_id, language, ids):
    keys = [state_key(student_id, qid) for qid in ids]
    keys += [review_result_key(student_id, language, qid) for qid in ids]
    states = get_many(db, keys)
    return [qid for qid in ids
            if review_result_key(student_id, language, qid) not in states
            and states.get(state_key(student_id, qid), {}).get("due", "") <= local_day().isoformat()]


def review_result_key(student_id, language, qid):
    return f"course-review-result:v1:{student_id}:{language}:{local_day()}:{qid}"


def public_item(question, row=None, section=None):
    result = {"id": question["id"], "prompt": question["prompt"]}
    if "options" in question:
        result["options"] = question["options"]
    if row is not None:
        result["lesson"] = row["lesson"]
        if section.get("text"):
            result["prompt"] = section["text"] + "\n\n" + result["prompt"]
        if section["skill"] == "listening":
            result["audio_url"] = row["audio_url"]
    return result


def submit_review(db, student, language, qid, answer):
    lock(db, student.id)
    previous = get(db, review_result_key(student.id, language, qid))
    if previous is not None:
        return previous | {"reward": dict(ZERO)}
    questions = exact_questions(language)
    if qid not in questions:
        raise HTTPException(404, "Takrorlash savoli topilmadi.")
    if qid not in queue(db, student.id, language):
        raise HTTPException(409, "Bu savol bugungi takrorlash navbatida emas.")
    row, section, question = questions[qid]
    latest = latest_attempts(db, student.id, language).get(qid)
    if latest is None:
        raise HTTPException(409, "Avval darsdagi savolni bajaring.")
    correction = latest.correct == 0
    state = review_state(db, student.id, qid, latest.created_at)
    if (not correction and state["stage"] >= len(REVIEW_INTERVALS)) or state["due"] > local_day().isoformat():
        raise HTTPException(409, "Takrorlash vaqti hali kelmagan.")
    correct = grade(question, answer)
    earned = dict(ZERO)
    if not correct:
        state["stage"] = 0
    if correct and correction:
        earned = reward(db, student, language, "master:" + qid, "correction", 2, 0, qid)
    elif correct:
        earned = reward(db, student, language, f"recall:{qid}:{state['stage']}",
                        "delayed_recall", 8, 1, qid)
        state["stage"] += 1
    delay = REVIEW_INTERVALS[min(state["stage"], len(REVIEW_INTERVALS) - 1)] if correct and not correction else 1
    state["due"] = (local_day() + timedelta(days=delay)).isoformat()
    put(db, state_key(student.id, qid), state)
    # Separate ref: review never overwrites lesson answers or changes resume.
    db.add(models.SkillAttempt(student_id=student.id, skill="course-review:" + language,
           ref=f"course-review:v1:{qid}", answer=answer, correct=int(correct), created_at=now()))
    result = {"correct": correct, "saved": True, "reward": earned,
              "expected": question["expected"], "explanation": question.get("explanation", "")}
    put(db, review_result_key(student.id, language, qid), result)
    return result


def checkpoint_bank(language):
    path = Path(__file__).with_name("course_checkpoint_data.json")
    try:
        return _checkpoint_bank(language, path.stat().st_mtime_ns)
    except OSError:
        return {}


@lru_cache(maxsize=4)
def _checkpoint_bank(language, modified_ns):
    path = Path(__file__).with_name("course_checkpoint_data.json")
    try:
        rows = json.loads(path.read_text(encoding="utf-8-sig"))[language]
        known_ids = {q["id"] for row in practice().BANK[language]
                     for section in row["sections"] for q in section["questions"]}
        known_prompts = {q["prompt"].strip() for row in practice().BANK[language]
                         for section in row["sections"] for q in section["questions"]}
        seen, prompts, result = set(), set(), {}
        for row in rows:
            week = row["week"]
            if type(week) is not int or not 1 <= week <= (32 if language == "en" else 24):
                raise ValueError("invalid week")
            if week in result or len(row["questions"]) != 3:
                raise ValueError("invalid checkpoint")
            for q in row["questions"]:
                if (not isinstance(q["id"], str) or not q["id"].startswith(f"{language}:boss:{week}:")
                        or q["id"] in seen or q["id"] in known_ids
                        or not isinstance(q["prompt"], str) or not q["prompt"].strip()
                        or q["prompt"].strip() in known_prompts or q["prompt"].strip() in prompts
                        or not isinstance(q["expected"], list) or not q["expected"]
                        or not all(isinstance(e, str) and e.strip() for e in q["expected"])
                        or not isinstance(q.get("explanation", ""), str)
                        or type(q.get("caseSensitive", False)) is not bool):
                    raise ValueError("invalid transfer question")
                seen.add(q["id"])
                prompts.add(q["prompt"].strip())
            result[week] = row
        return result
    except (OSError, ValueError, KeyError, TypeError):
        return {}  # Never substitute ordinary practice answers.


def boss_key(student_id, language, week):
    return f"course-boss:v1:{student_id}:{language}:{week}"


def mastered_lessons(db, student_id, language):
    return lesson_coverage(language, mastery(db, student_id, language))


def checkpoint_status(db, student_id, language, row, lessons=None, states=None):
    size = 6 if language == "en" else 3
    week = row["week"]
    lessons = ready_lessons(db, student_id, language) if lessons is None else lessons
    ready = all(n in lessons for n in range((week - 1) * size + 1, week * size + 1))
    key = boss_key(student_id, language, week)
    state = states.get(key) if states is not None else get(db, key)
    passed = bool(state and state["passed"])
    retry_ready = not state or now() >= datetime.fromisoformat(state["submitted_at"]) + timedelta(days=7)
    return {"week": week, "passed": passed, "available": ready and not passed and retry_ready}


def eligible(db, student):
    branch = db.get(models.Branch, student.branch_id) if student.branch_id else None
    user = db.get(models.User, student.user_id) if student.user_id else None
    return bool(branch and not branch.is_test and user and user.is_active
                and user.role == "student" and student.status == "active" and "(demo)" not in student.full_name.casefold()
                and not user.username.casefold().startswith("demo."))


def cohort_level(db, student_id, language):
    lessons = mastered_lessons(db, student_id, language)
    level = practice().BANK[language][0]["level"]
    for row in practice().BANK[language]:
        if row["lesson"] not in lessons:
            break
        level = row["level"]
    match = re.search(r"[ABC][12]", level)
    return match.group() if match else level


def cohort_key(student_id, language):
    return f"course-cohort:v1:{calendar_week()}:{language}:{student_id}"


def cohort_members_prefix(language, level, cohort):
    return f"course-cohort-member:v1:{calendar_week()}:{language}:{level}:{cohort}:"


def assign_cohort(db, student_id, language, level):
    # Serialize allocation per weekly language/level bucket across workers.
    bucket = f"course-cohort-slots:v1:{calendar_week()}:{language}:{level}"
    put(db, bucket + ":lock", True)
    cohorts = get(db, bucket, [])
    index = next((i for i, members in enumerate(cohorts) if len(members) < 20), len(cohorts))
    if index == len(cohorts):
        cohorts.append([])
    cohorts[index].append(student_id)
    put(db, bucket, cohorts)
    cohort = str(index + 1)
    put(db, cohort_members_prefix(language, level, cohort) + str(student_id), student_id)
    return cohort


def opt_in(db, student, language, opted_in):
    lock(db, student.id)
    key = cohort_key(student.id, language)
    record = get(db, key)
    if opted_in and not eligible(db, student):
        raise HTTPException(403, "Haftalik jamoa faqat haqiqiy faol o‘quvchilar uchun.")
    if record is None and not opted_in:
        return
    if record is None:
        level = cohort_level(db, student.id, language)
        record = {"student_id": student.id, "level": level,
                  "alias": "Learner-" + secrets.token_hex(4), "joined_at": now().isoformat(),
                  "cohort": assign_cohort(db, student.id, language, level)}
    elif "cohort" not in record:
        record["cohort"] = assign_cohort(db, student.id, language, record["level"])
    record["opted_in"] = opted_in
    put(db, key, record)


def weekly(db, student, language):
    mine = get(db, cohort_key(student.id, language))
    result = {"week": calendar_week(), "level": mine["level"] if mine else cohort_level(db, student.id, language),
              "opted_in": bool(mine and mine["opted_in"] and "cohort" in mine and eligible(db, student)),
              "participants": 0, "leaders": [], "team_done": 0, "team_target": 0, "my_points": 0}
    if not result["opted_in"]:
        return result
    prefix = cohort_members_prefix(language, mine["level"], mine["cohort"])
    ids = [json.loads(value) for (value,) in db.query(models.IntegrationSetting.value).filter(
        models.IntegrationSetting.key.startswith(prefix)).all()]
    records = get_many(db, [cohort_key(sid, language) for sid in ids])
    # Eligibility is rechecked in one join: a later move to a test branch or
    # disabled account cannot leave a demo contribution in the real cohort.
    valid_ids = {sid for (sid,) in db.query(models.Student.id).join(
        models.User, models.User.id == models.Student.user_id).join(
        models.Branch, models.Branch.id == models.Student.branch_id).filter(
        models.Student.id.in_(ids), models.Student.status == "active",
        models.User.is_active == 1, models.User.role == "student", models.Branch.is_test == 0,
        ~func.lower(models.Student.full_name).contains("(demo)"),
        ~func.lower(models.User.username).startswith("demo.")).all()}
    members = {sid: records[cohort_key(sid, language)] for sid in valid_ids
               if cohort_key(sid, language) in records
               and records[cohort_key(sid, language)]["opted_in"]
               and records[cohort_key(sid, language)]["level"] == mine["level"]
               and records[cohort_key(sid, language)].get("cohort") == mine["cohort"]}
    week_start = datetime.combine(local_day() - timedelta(days=local_day().weekday()),
                                  datetime.min.time()) - timedelta(hours=5)
    transactions = db.query(models.XpTransaction).filter(
        models.XpTransaction.student_id.in_(list(members)),
        models.XpTransaction.idempotency_key.startswith(PREFIX),
        models.XpTransaction.created_at >= week_start,
        models.XpTransaction.is_reversal == 0).all()
    activity = {sid: {} for sid in members}
    for tx in transactions:
        entry = members[tx.student_id]
        meta = json.loads(tx.meta or "{}")
        if (meta.get("language") == language and meta.get("week") == calendar_week()
                and tx.created_at >= datetime.fromisoformat(entry["joined_at"])):
            activity[tx.student_id].setdefault(meta["day"], set()).add(meta.get("question_id") or tx.idempotency_key)
    participants = []
    for sid, entry in members.items():
        points = min(20, sum(min(DAILY_TARGET, len(ids)) for ids in activity[sid].values()))
        participants.append({"alias": entry["alias"], "points": points})
        if sid == student.id:
            result["my_points"] = points
    result["participants"] = len(participants)
    result["team_done"] = sum(min(10, p["points"]) for p in participants)
    result["team_target"] = 10 * len(participants)
    if len(participants) >= 3:
        result["leaders"] = sorted((p for p in participants if p["points"] > 0),
                                  key=lambda p: (-p["points"], p["alias"]))[:3]
    return result


def motivation(db, student, language):
    lock(db, student.id)
    questions = exact_questions(language)
    reviews = [public_item(questions[qid][2], questions[qid][0], questions[qid][1])
               for qid in visible_review_ids(db, student.id, language, queue(db, student.id, language))
               if qid in questions]
    transactions = txs(db, student.id, language).all()
    done = daily_effort(db, student.id, language)
    coins = db.query(func.coalesce(func.sum(models.CoinEntry.amount), 0)).filter_by(
        student_id=student.id, source="course_motivation:" + language).scalar()
    lessons = ready_lessons(db, student.id, language)
    bank = checkpoint_bank(language)
    boss_states = get_many(db, [boss_key(student.id, language, w) for w in bank])
    checkpoints = [checkpoint_status(db, student.id, language, bank[w], lessons, boss_states) if w in bank
                   else {"week": w, "passed": False, "available": False}
                   for w in range(1, (32 if language == "en" else 24) + 1)]
    return {"daily": {"target": DAILY_TARGET, "done": min(DAILY_TARGET, len(done))},
            "rewards": {"xp": sum(tx.amount for tx in transactions), "coins": int(coins or 0)},
            "learning": {
                "independent": sum(tx.event_code == "course_challenge" for tx in transactions),
                "practice": sum(tx.event_code in ("course_practice_correct", "course_first_correct") for tx in transactions),
                "corrections": sum(tx.event_code == "course_correction" for tx in transactions),
                "recalls": sum(tx.event_code == "course_delayed_recall" for tx in transactions)},
            "plan": daily_plan(db, student.id, language, reviews),
            "evidence": evidence(db, student.id, language),
            "review": reviews, "weekly": weekly(db, student, language), "checkpoints": checkpoints}



def challenge_view(db, student_id, language, week):
    row = checkpoint_bank(language).get(week)
    if row is None:
        return {"week": week, "title": "Haftalik sinov", "available": False,
                "reason": "Bu hafta uchun tekshirilgan sinov hali tayyor emas.", "questions": [], "passed": False,
                "reward_pending": False}
    state = get(db, boss_key(student_id, language, week))
    status = checkpoint_status(db, student_id, language, row,
                               states={boss_key(student_id, language, week): state})
    if state and state["passed"]:
        reason = "Bu sinov topshirilgan."
    elif state:
        retry = datetime.fromisoformat(state["submitted_at"]) + timedelta(days=7, hours=5)
        reason = "Javoblar avval ko‘rsatilgan: bu tuzatish mashqi." if status["available"] else (
            f"Tuzatish uchun qayta urinish: {retry:%Y-%m-%d %H:%M} (Toshkent).")
    else:
        reason = "" if status["available"] else "Haftaning har bir darsida kamida 3 ta mavjud aniq savolni, kamida 2 ta mavjud bo‘limdan to‘g‘ri bajaring."
    return {"week": week, "title": row.get("title", "Haftalik sinov"),
            "available": status["available"], "reason": reason,
            "questions": [public_item(q) for q in row["questions"]] if status["available"] else [],
            "passed": status["passed"],
            "reward_pending": bool(state and state.get("reward_pending"))}


def claim_boss(db, student, language, week):
    lock(db, student.id)
    key = boss_key(student.id, language, week)
    state = get(db, key)
    if not state or not state["passed"]:
        raise HTTPException(409, "Avval haftalik sinovni muvaffaqiyatli topshiring.")
    if not state.get("reward_pending"):
        return {"reward": dict(ZERO), "pending": False}
    independent = state["independent_pass"]
    earned = reward(db, student, language, f"boss:{week}",
                    "challenge" if independent else "correction",
                    15 if independent else 2, 2 if independent else 0, f"{language}:boss:{week}")
    # A successful claim or an existing unique ledger claim ends pending state.
    claimed = db.query(models.XpTransaction.id).filter_by(
        idempotency_key=f"{PREFIX}{student.id}:{language}:boss:{week}").first()
    state["reward_pending"] = claimed is None
    if earned["xp"]:
        state["reward"] = earned
    put(db, key, state)
    return {"reward": earned, "pending": state["reward_pending"]}


def submit_challenge_batch(db, student, language, week, answers):
    lock(db, student.id)
    row = checkpoint_bank(language).get(week)
    if row is None:
        raise HTTPException(404, "Haftalik sinov topilmadi.")
    ids = {q["id"] for q in row["questions"]}
    if set(answers) != ids:
        raise HTTPException(422, "Aynan shu haftaning barcha savollariga javob yuboring.")
    key = boss_key(student.id, language, week)
    previous = get(db, key)
    if previous and (previous["passed"] or now() < datetime.fromisoformat(previous["submitted_at"]) + timedelta(days=7)):
        return {k: previous[k] for k in ("passed", "correct", "total", "feedback")} | {"reward": dict(ZERO)}
    if not checkpoint_status(db, student.id, language, row, states={key: previous})["available"]:
        raise HTTPException(409, "Avval haftaning har bir darsida tekshiriladigan savolni to‘g‘ri bajaring.")
    feedback = []
    for q in row["questions"]:
        correct = grade(q, answers[q["id"]])
        feedback.append({"id": q["id"], "correct": correct, "expected": q["expected"],
                         "explanation": q.get("explanation", "")})
        db.add(models.SkillAttempt(student_id=student.id, skill="course-challenge:" + language,
               ref="course-challenge:v1:" + q["id"], answer=answers[q["id"]],
               correct=int(correct), created_at=now()))
    passed = all(f["correct"] for f in feedback)
    earned = dict(ZERO)
    if passed:
        earned = reward(db, student, language, f"boss:{week}",
                        "correction" if previous else "challenge", 2 if previous else 15,
                        0 if previous else 2, f"{language}:boss:{week}")
    result = {"passed": passed, "correct": sum(f["correct"] for f in feedback),
              "total": len(feedback), "feedback": feedback, "reward": earned}
    put(db, key, result | {"submitted_at": now().isoformat(),
                          "round": previous["round"] + 1 if previous else 0,
                          "independent_pass": passed and previous is None,
                          "reward_pending": passed and earned["reason"] == "daily_limit"})
    return result
