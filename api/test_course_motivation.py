"""Isolated motivation tests: no live DB/provider; separate connections for races."""
import json
import tempfile
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import test_student_course_practice as baseline
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker

import course_motivation as motivation
import student_course_practice as practice
import models

BASE = "/api/student/course-practice"
BOSS = {
    lang: {1: {"week": 1, "title": "Independent transfer", "questions": [
        {"id": f"{lang}:boss:1:{i}", "prompt": f"New independent transfer item {lang} {i}",
         "expected": [f"verified{i}"], "explanation": "Canonical explanation", "caseSensitive": False}
        for i in range(1, 4)]}}
    for lang in ("en", "de")
}


class MotivationTests(unittest.TestCase):
    tearDown = baseline.CoursePracticeTests.tearDown
    post = baseline.CoursePracticeTests.post
    detail = baseline.CoursePracticeTests.detail
    position = baseline.CoursePracticeTests.position
    speak = baseline.CoursePracticeTests.speak

    def setUp(self):
        baseline.CoursePracticeTests.setUp(self)
        self.clock = patch.object(motivation, "now", return_value=datetime(2026, 10, 19, 8))
        self.time = self.clock.start()
        self.addCleanup(self.clock.stop)
        self.bank = patch.object(motivation, "checkpoint_bank", side_effect=lambda lang: BOSS[lang])
        self.bank.start()
        self.addCleanup(self.bank.stop)
        self.db.add(models.Branch(id=1, name="Real", is_test=0))
        self.db.add(models.Branch(id=2, name="Sandbox", is_test=1))
        for sid, uid in [(1, 11), (2, 22)]:
            self.db.get(models.Student, sid).branch_id = 1
            self.db.add(models.User(id=uid, username=f"real{uid}", password_hash="unused",
                                   full_name=f"Private Name {uid}", role="student", is_active=1))
        self.db.commit()

    def q(self, language="en", lesson=1):
        return next(q for row, section, q in motivation.exact_questions(language).values()
                    if row["lesson"] == lesson)

    def get_motivation(self, language="en"):
        response = self.client.get(BASE + "/motivation", params={"language": language})
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()

    def review(self, q, answer, language="en"):
        return self.client.post(BASE + "/motivation/review", json={
            "language": language, "question_id": q["id"], "answer": answer})

    def unlock(self, language="en", student_id=1, db=None):
        db = db or self.db
        for n in range(1, (6 if language == "en" else 3) + 1):
            for row, section, q in motivation.exact_questions(language).values():
                if row["lesson"] == n:
                    db.add(models.SkillAttempt(student_id=student_id, skill="course-practice:" + language + ":" + section["skill"],
                           ref=practice._ref(q["id"]), answer=q["expected"][0], correct=1, created_at=motivation.now()))
        db.commit()

    def boss(self, language="en", **changes):
        body = {"language": language, "week": 1,
                "answers": {q["id"]: q["expected"][0] for q in BOSS.get(language, BOSS["en"])[1]["questions"]}}
        body.update(changes)
        return self.client.post(BASE + "/motivation/challenge", json=body)

    def league(self, enabled=True, language="en"):
        return self.client.post(BASE + "/motivation/league", json={"language": language, "enabled": enabled})

    def test_first_correct_correction_replay_and_no_self_rewards(self):
        q = self.q()
        result = self.post(q["id"], q["expected"][0]).json()
        self.assertEqual(result["reward"], {"xp": 2, "coins": 0, "reason": "practice_correct"})
        self.assertEqual(self.post(q["id"], q["expected"][0]).json()["reward"], motivation.ZERO)
        other = self.q(lesson=2)
        self.post(other["id"], "wrong", lesson=2)
        result = self.post(other["id"], other["expected"][0], lesson=2).json()
        self.assertEqual(result["reward"], {"xp": 2, "coins": 0, "reason": "correction"})
        selfq = next(q for s in practice.BANK["en"][0]["sections"] for q in s["questions"] if q["mode"] == "self")
        self.assertEqual(self.post(selfq["id"], "self answer").json()["reward"], motivation.ZERO)
        self.assertTrue(self.speak([{"role": "student", "text": "Hello"}]).json()["saved"])
        self.assertEqual(self.db.query(models.XpTransaction).count(), 2)
        self.assertEqual(self.db.query(models.CoinEntry).count(), 0)
        self.assertEqual(self.db.query(models.StudentGamification).one().lifetime_xp, 4)
        result = self.get_motivation()
        self.assertEqual(result["rewards"], {"xp": 4, "coins": 0})
        self.assertEqual(result["daily"], {"target": 5, "done": 3})  # Open practice counts effort, never XP/mastery.
        self.assertEqual(result["review"], [])
        self.assertFalse(result["weekly"]["opted_in"])
        self.assertEqual(result["weekly"]["leaders"], [])
        self.assertEqual(self.get_motivation("de")["rewards"]["xp"], 0)

    def test_review_delays_four_stages_and_immutable_daily_first_answer(self):
        q = self.q()
        self.post(q["id"], q["expected"][0])
        self.assertEqual(self.review(q, q["expected"][0]).status_code, 409)
        self.db.rollback()
        self.time.return_value += timedelta(days=1)
        queued = self.get_motivation()["review"]
        self.assertEqual(len(queued), 1)
        self.assertLessEqual(set(queued[0]), {"id", "lesson", "prompt", "options", "audio_url"})
        self.assertEqual(self.review(q, "wrong").json()["reward"], motivation.ZERO)
        replay = self.review(q, q["expected"][0]).json()
        self.assertFalse(replay["correct"])
        self.assertEqual(replay["reward"], motivation.ZERO)
        self.assertEqual(self.get_motivation()["review"], [])
        self.time.return_value += timedelta(days=1)
        correction = self.review(q, q["expected"][0]).json()
        self.assertTrue(correction["correct"])
        self.assertEqual(correction["reward"], motivation.ZERO)  # Already earned the base claim.
        self.time.return_value += timedelta(days=1)
        for delay in (3, 7, 14, 14):
            self.assertEqual(len(self.get_motivation()["review"]), 1)
            result = self.review(q, q["expected"][0]).json()
            self.assertEqual(result["reward"], {"xp": 8, "coins": 1, "reason": "delayed_recall"})
            self.assertEqual(self.review(q, q["expected"][0]).json()["reward"], motivation.ZERO)
            self.time.return_value += timedelta(days=delay)
        self.assertEqual(self.get_motivation()["review"], [])
        self.assertEqual(self.db.query(models.XpTransaction).count(), 5)
        self.assertEqual(self.detail()["answers"][q["id"]]["answer"], q["expected"][0])

    def test_queue_finite_no_refill_no_position_changes_and_language_isolation(self):
        self.position(lesson=12)
        for n in range(1, 8):
            q = self.q(lesson=n)
            self.post(q["id"], q["expected"][0], lesson=n)
        self.assertEqual(self.get_motivation()["daily"]["done"], 5)
        self.time.return_value += timedelta(days=1)
        queue = self.get_motivation()["review"]
        self.assertEqual(len(queue), 5)
        for item in queue:
            q = motivation.exact_questions("en")[item["id"]][2]
            self.assertTrue(self.review(q, q["expected"][0]).json()["correct"])
        self.assertEqual(self.get_motivation()["review"], [])
        self.assertEqual(self.get_motivation("de")["review"], [])
        self.assertEqual(practice._resume(self.db, 1, "en"), 12)
        self.time.return_value += timedelta(days=1)
        self.assertEqual(len(self.get_motivation()["review"]), 2)

    def test_review_feedback_today_prevents_immediate_recall_reward(self):
        q = self.q()
        self.post(q["id"], q["expected"][0])
        self.time.return_value += timedelta(days=1)
        self.assertEqual(len(self.get_motivation()["review"]), 1)
        self.post(q["id"], "show me answer")
        self.assertEqual(self.review(q, q["expected"][0]).status_code, 409)

    def test_boss_whole_first_attempt_feedback_no_keys_and_no_retry_mastery(self):
        unavailable = self.client.get(BASE + "/motivation/challenge?language=en&week=1").json()
        self.assertFalse(unavailable["available"])
        self.assertEqual(unavailable["questions"], [])
        self.unlock()
        view = self.client.get(BASE + "/motivation/challenge?language=en&week=1").json()
        self.assertTrue(view["available"])
        self.assertEqual(len(view["questions"]), 3)
        self.assertNotIn("expected", json.dumps(view))
        answers = {q["id"]: q["expected"][0] for q in BOSS["en"][1]["questions"]}
        answers["en:boss:1:1"] = "incorrect"
        result = self.boss(answers=answers).json()
        self.assertFalse(result["passed"])
        self.assertEqual((result["correct"], result["total"]), (2, 3))
        self.assertEqual(result["reward"], motivation.ZERO)
        self.assertIn("expected", result["feedback"][0])
        replay = self.boss().json()
        self.assertFalse(replay["passed"])
        self.assertEqual(replay["correct"], 2)
        self.assertEqual(replay["reward"], motivation.ZERO)
        self.assertEqual(self.db.query(models.XpTransaction).count(), 0)
        self.assertEqual(self.db.query(models.SkillAttempt).filter(
            models.SkillAttempt.ref.startswith("course-challenge:")).count(), 3)
        final = self.client.get(BASE + "/motivation/challenge?language=en&week=1").json()
        self.assertFalse(final["available"])
        self.assertEqual(final["questions"], [])

    def test_boss_pass_reward_once_scope_and_bad_payloads(self):
        self.unlock()
        self.assertEqual(self.boss().json()["reward"], {"xp": 15, "coins": 2, "reason": "challenge"})
        self.assertEqual(self.boss().json()["reward"], motivation.ZERO)
        self.assertTrue(self.get_motivation()["checkpoints"][0]["passed"])
        self.assertEqual(self.db.query(models.XpTransaction).count(), 1)
        self.assertEqual(self.db.query(models.CoinEntry).one().amount, 2)
        self.user = SimpleNamespace(id=22, role="student", full_name="Two", is_active=1)
        self.assertFalse(self.get_motivation()["checkpoints"][0]["passed"])
        self.assertEqual(self.boss().status_code, 409)
        self.db.rollback()
        for body in [{"week": True}, {"language": "fr"}, {"answers": {}},
                     {"answers": {"bad1": "x", "bad2": "y", "bad3": "z"}},
                     {"answers": {"en:boss:1:1": "x" * 1001, "en:boss:1:2": "y", "en:boss:1:3": "z"}}]:
            self.assertEqual(self.boss(**body).status_code, 422)
            self.db.rollback()
        self.assertEqual(self.boss(language="de").status_code, 409)
        self.db.rollback()

    def test_opt_in_masking_demo_exclusion_level_language_and_week_scope(self):
        self.assertEqual(self.get_motivation()["weekly"]["participants"], 0)
        self.assertEqual(self.league().json(), {"saved": True})
        initial = motivation.get(self.db, motivation.cohort_key(1, "en"))
        self.time.return_value += timedelta(seconds=1)
        q = self.q()
        self.post(q["id"], q["expected"][0])
        self.user = SimpleNamespace(id=22, role="student", full_name="Two", is_active=1)
        self.assertEqual(self.league().status_code, 200)
        self.assertEqual(self.get_motivation()["weekly"]["participants"], 2)
        self.assertEqual(self.get_motivation()["weekly"]["leaders"], [])
        self.db.get(models.Student, 2).branch_id = 2
        self.db.commit()
        self.assertEqual(self.league().status_code, 403)
        self.db.rollback()
        self.user = SimpleNamespace(id=11, role="student", full_name="One", is_active=1)
        self.assertEqual(self.get_motivation()["weekly"]["participants"], 1)
        self.assertEqual(self.get_motivation("de")["weekly"]["participants"], 0)
        self.assertEqual(self.league(False).status_code, 200)
        self.assertEqual(self.get_motivation()["weekly"]["participants"], 0)
        self.assertEqual(self.league(True).status_code, 200)
        self.assertEqual(motivation.get(self.db, motivation.cohort_key(1, "en"))["alias"], initial["alias"])
        self.assertEqual(motivation.get(self.db, motivation.cohort_key(1, "en"))["level"], initial["level"])
        self.time.return_value += timedelta(days=7)
        self.assertFalse(self.get_motivation()["weekly"]["opted_in"])
        self.assertEqual(self.get_motivation()["weekly"]["leaders"], [])

    def test_weekly_caps_no_bottom_list_and_no_pii(self):
        self.league()
        for sid in (2, 4, 5):
            if sid != 2:
                uid = sid * 11
                self.db.add(models.User(id=uid, username=f"real{uid}", password_hash="unused",
                    full_name="PRIVATE", role="student", is_active=1))
                self.db.add(models.Student(id=sid, user_id=uid, full_name="PRIVATE", branch_id=1, status="active"))
                self.db.commit()
            motivation.opt_in(self.db, self.db.get(models.Student, sid), "en", True)
            self.db.commit()
        # Different level excludes even an opted-in real account.
        key = motivation.cohort_key(5, "en")
        entry = motivation.get(self.db, key)
        entry["level"] = "B2"
        motivation.put(self.db, key, entry)
        for day in range(7):
            for n in range(8):
                self.db.add(models.XpTransaction(student_id=1, amount=1, is_reversal=0,
                    idempotency_key=f"{motivation.PREFIX}1:en:test:{day}:{n}",
                    created_at=motivation.now() + timedelta(seconds=1),
                    meta=json.dumps({"language": "en", "week": motivation.calendar_week(), "day": f"day{day}",
                                     "question_id": f"q{day}:{n}"})))
        self.db.commit()
        weekly = self.get_motivation()["weekly"]
        self.assertEqual(weekly["participants"], 3)
        self.assertEqual(weekly["leaders"][0]["points"], 20)
        self.assertEqual(weekly["team_done"], 10)
        self.assertEqual(weekly["team_target"], 30)
        self.assertEqual(len(weekly["leaders"]), 1)
        self.assertEqual(set(weekly["leaders"][0]), {"alias", "points"})
        for private in ("PRIVATE", "Private Name", "student_id", "rank", "username"):
            self.assertNotIn(private, json.dumps(weekly))

    def test_reward_failure_rolls_back_attempt_and_claim(self):
        q = self.q()
        with patch("common._recalc_gamification", side_effect=RuntimeError("injected failure")):
            with self.assertRaises(RuntimeError):
                self.post(q["id"], q["expected"][0])
        self.db.rollback()
        self.assertEqual(self.db.query(models.XpTransaction).count(), 0)
        self.assertEqual(self.db.query(models.CoinEntry).count(), 0)
        self.assertEqual(self.db.query(models.SkillAttempt).count(), 0)
        self.assertEqual(self.post(q["id"], q["expected"][0]).json()["reward"]["xp"], 2)

    def test_self_and_foreign_question_cannot_be_reviewed(self):
        selfq = next(q for s in practice.BANK["en"][0]["sections"] for q in s["questions"] if q["mode"] == "self")
        self.assertEqual(self.review(selfq, "My own response").status_code, 404)
        self.db.rollback()
        self.assertEqual(self.review(self.q("de"), "Buch").status_code, 404)
        self.db.rollback()
        self.assertEqual(self.client.get(BASE + "/motivation?language=en&student_id=2").status_code, 422)
        self.assertEqual(self.league("yes").status_code, 422)
        self.assertEqual(self.db.query(models.XpTransaction).count(), 0)

    def test_parallel_reward_and_review_and_boss_claims_use_independent_connections(self):
        with tempfile.TemporaryDirectory() as directory:
            engine = create_engine("sqlite:///" + str(Path(directory) / "race.db"),
                                   connect_args={"check_same_thread": False, "timeout": 30})
            for table in (models.Student, models.IntegrationSetting, models.SkillAttempt,
                          models.XpTransaction, models.CoinEntry, models.XpSeason,
                          models.XpLeague, models.XpRule, models.StudentGamification, models.StudentLeagueHistory,
                          models.User, models.Branch):
                table.__table__.create(engine)
            sessions = sessionmaker(bind=engine)
            with sessions() as db:
                db.add(models.Student(id=1, full_name="One", user_id=11, status="active"))
                db.commit()
            q = self.q()

            def race(action):
                barrier = threading.Barrier(2)
                def worker(_):
                    with sessions() as db:
                        student = db.get(models.Student, 1)
                        barrier.wait(timeout=10)
                        result = action(db, student)
                        db.commit()
                        return result
                with ThreadPoolExecutor(max_workers=2) as pool:
                    return list(pool.map(worker, range(2)))

            replies = race(lambda db, s: practice.answer(practice.AnswerIn(
                language="en", lesson=1, question_id=q["id"], answer=q["expected"][0]), db, s))
            self.assertEqual(sorted(r["reward"]["xp"] for r in replies), [0, 2])
            self.time.return_value += timedelta(days=1)
            replies = race(lambda db, s: motivation.submit_review(db, s, "en", q["id"], q["expected"][0]))
            self.assertEqual(sorted(r["reward"]["xp"] for r in replies), [0, 8])
            with sessions() as db:
                self.unlock(db=db)
            answers = {q["id"]: q["expected"][0] for q in BOSS["en"][1]["questions"]}
            replies = race(lambda db, s: motivation.submit_challenge_batch(db, s, "en", 1, answers))
            self.assertEqual(sorted(r["reward"]["xp"] for r in replies), [0, 15])
            with sessions() as db:
                self.assertEqual(db.query(models.XpTransaction).count(), 3)
                self.assertEqual(db.query(func.sum(models.CoinEntry.amount)).scalar(), 3)
                self.assertEqual(db.query(models.StudentGamification).one().lifetime_xp, 25)
            engine.dispose()


    def test_unresolved_wrong_answers_due_tomorrow_and_lower_correction_reward(self):
        q = self.q()
        self.post(q["id"], "wrong")
        self.assertEqual(self.get_motivation()["review"], [])
        self.time.return_value += timedelta(days=1)
        items = self.get_motivation()["review"]
        self.assertEqual([item["id"] for item in items], [q["id"]])
        result = self.review(q, q["expected"][0]).json()
        self.assertEqual(result["reward"], {"xp": 2, "coins": 0, "reason": "correction"})
        self.assertEqual(self.review(q, q["expected"][0]).json()["reward"], motivation.ZERO)
        self.assertEqual(self.get_motivation()["learning"], {"independent": 0, "practice": 0, "corrections": 1, "recalls": 0})
        self.time.return_value += timedelta(days=1)
        self.assertEqual(self.review(q, q["expected"][0]).json()["reward"]["reason"], "delayed_recall")

    def test_failed_boss_retry_seven_days_is_correction_not_independent_mastery(self):
        self.unlock()
        answers = {q["id"]: "wrong" for q in BOSS["en"][1]["questions"]}
        self.assertFalse(self.boss(answers=answers).json()["passed"])
        self.time.return_value += timedelta(days=7, seconds=-1)
        self.assertFalse(self.boss().json()["passed"])
        view = self.client.get(BASE + "/motivation/challenge?language=en&week=1").json()
        self.assertFalse(view["available"])
        self.assertIn("qayta", view["reason"])
        self.time.return_value += timedelta(seconds=1)
        self.assertTrue(self.client.get(BASE + "/motivation/challenge?language=en&week=1").json()["available"])
        result = self.boss().json()
        self.assertTrue(result["passed"])
        self.assertEqual(result["reward"], {"xp": 2, "coins": 0, "reason": "correction"})
        state = motivation.get(self.db, motivation.boss_key(1, "en", 1))
        self.assertFalse(state["independent_pass"])
        self.assertEqual(state["round"], 1)
        self.assertEqual(self.boss().json()["reward"], motivation.ZERO)
        self.assertEqual(self.get_motivation()["learning"]["independent"], 0)

    def test_reward_twenty_per_local_day_across_languages_and_config_rule(self):
        questions = list(motivation.exact_questions("en").values())[:21]
        for row, section, q in questions:
            self.post(q["id"], q["expected"][0], lesson=row["lesson"])
        self.assertEqual(self.db.query(models.XpTransaction).count(), 20)
        q = self.q("de")
        self.assertEqual(self.post(q["id"], q["expected"][0], language="de").json()["reward"], dict(motivation.ZERO, reason="daily_limit"))
        self.time.return_value += timedelta(days=1)
        row, section, newq = list(motivation.exact_questions("en").values())[22]
        self.db.add(models.XpRule(event_code="course_practice_correct", name="Paused", is_active=0))
        self.db.commit()
        self.assertEqual(self.post(newq["id"], newq["expected"][0], lesson=row["lesson"]).json()["reward"], motivation.ZERO)
        self.assertEqual(self.db.query(models.XpTransaction).count(), 20)

    def test_fixed_small_cohort_capacity_and_stable_rejoin(self):
        for sid in range(4, 25):
            self.db.add(models.User(id=sid * 100, username=f"user{sid}", password_hash="unused",
                full_name="Private", role="student", is_active=1))
            self.db.add(models.Student(id=sid, user_id=sid * 100, full_name="Private", status="active", branch_id=1))
        self.db.commit()
        students = [1, 2] + list(range(4, 25))
        for sid in students:
            motivation.opt_in(self.db, self.db.get(models.Student, sid), "en", True)
            self.db.commit()
        first = motivation.get(self.db, motivation.cohort_key(1, "en"))
        last = motivation.get(self.db, motivation.cohort_key(24, "en"))
        self.assertNotEqual(first["cohort"], last["cohort"])
        self.assertEqual(self.get_motivation()["weekly"]["participants"], 20)
        motivation.opt_in(self.db, self.db.get(models.Student, 1), "en", False)
        self.db.commit()
        motivation.opt_in(self.db, self.db.get(models.Student, 1), "en", True)
        self.db.commit()
        self.assertEqual(motivation.get(self.db, motivation.cohort_key(1, "en"))["cohort"], first["cohort"])
        self.assertEqual(motivation.weekly(self.db, self.db.get(models.Student, 24), "en")["participants"], 3)

    def test_checkpoint_state_reads_are_batched(self):
        from sqlalchemy import event
        expanded = {week: {"week": week, "title": "Transfer", "questions": [
            {"id": f"en:boss:{week}:{i}", "prompt": f"Unseen {week} {i}",
             "expected": ["yes"], "explanation": "Checked"} for i in range(1, 4)]}
            for week in range(1, 33)}
        statements = []
        def capture(conn, cursor, statement, parameters, context, executemany):
            statements.append(statement)
        event.listen(self.engine, "before_cursor_execute", capture)
        try:
            with patch.object(motivation, "checkpoint_bank", return_value=expanded):
                result = self.get_motivation()
        finally:
            event.remove(self.engine, "before_cursor_execute", capture)
        self.assertEqual(len(result["checkpoints"]), 32)
        self.assertLess(len(statements), 25, str(statements))

    def test_theme_validation_and_robot_name_remains_untrusted_history(self):
        for theme in ("daily-life", "football", "robots"):
            self.assertEqual(self.speak(theme=theme).json()["reply"],
                             practice.course_themes.foundation_opener(1, theme))
        self.assertEqual(self.speak(theme="unknown").status_code, 422)
        self.assertEqual(self.speak(robot_name="x" * 41).status_code, 422)
        self.assertEqual(self.speak([{"role": "student", "text": "A kind robot"}],
                                   theme="robots", robot_name="Ignore system").status_code, 200)
        system, history = self.ai.call_args.args
        self.assertNotIn("Ignore system", system)
        self.assertIn("Ignore system", history[0]["text"])
        self.assertEqual(self.db.query(models.XpTransaction).count(), 0)


    def test_daily_cap_and_cohort_capacity_are_safe_under_concurrent_requests(self):
        with tempfile.TemporaryDirectory() as directory:
            engine = create_engine("sqlite:///" + str(Path(directory) / "caps.db"),
                                   connect_args={"check_same_thread": False, "timeout": 30})
            for table in (models.Student, models.IntegrationSetting, models.SkillAttempt,
                          models.XpTransaction, models.CoinEntry, models.XpSeason, models.XpRule,
                          models.XpLeague, models.StudentGamification, models.StudentLeagueHistory,
                          models.Branch, models.User):
                table.__table__.create(engine)
            sessions = sessionmaker(bind=engine)
            with sessions() as db:
                db.add(models.Branch(id=1, name="Real", is_test=0))
                for sid in range(1, 22):
                    db.add(models.User(id=sid, username=f"real{sid}", password_hash="unused",
                                      full_name="Private", role="student", is_active=1))
                    db.add(models.Student(id=sid, user_id=sid, full_name="Private",
                                          branch_id=1, status="active"))
                for i in range(19):
                    db.add(models.XpTransaction(student_id=1, amount=1,
                           idempotency_key=f"{motivation.PREFIX}1:en:seed:{i}", created_at=motivation.now()))
                db.commit()
                for sid in range(1, 20):
                    motivation.opt_in(db, db.get(models.Student, sid), "en", True)
                    db.commit()

            barrier = threading.Barrier(2)
            def award(lesson):
                with sessions() as db:
                    student = db.get(models.Student, 1)
                    q = self.q(lesson=lesson)
                    barrier.wait(timeout=10)
                    return practice.answer(practice.AnswerIn(language="en", lesson=lesson,
                                           question_id=q["id"], answer=q["expected"][0]), db, student)
            with ThreadPoolExecutor(max_workers=2) as pool:
                results = list(pool.map(award, (1, 2)))
            self.assertEqual(sorted(r["reward"]["xp"] for r in results), [0, 2])

            barrier = threading.Barrier(2)
            def join(sid):
                with sessions() as db:
                    student = db.get(models.Student, sid)
                    barrier.wait(timeout=10)
                    motivation.opt_in(db, student, "en", True)
                    db.commit()
            with ThreadPoolExecutor(max_workers=2) as pool:
                list(pool.map(join, (20, 21)))
            with sessions() as db:
                slots = motivation.get(db, f"course-cohort-slots:v1:{motivation.calendar_week()}:en:A1")
                self.assertEqual(sorted(map(len, slots)), [1, 20])
                self.assertEqual(db.query(models.XpTransaction).count(), 20)
                self.assertEqual(db.query(models.CoinEntry).count(), 0)
            engine.dispose()

    def test_real_bank_is_available_and_checked_without_mock(self):
        self.bank.stop()
        self.assertEqual(len(motivation.checkpoint_bank("en")), 32)
        self.assertEqual(len(motivation.checkpoint_bank("de")), 24)
        self.unlock()
        view = self.client.get(BASE + "/motivation/challenge?language=en&week=1").json()
        self.assertTrue(view["available"])
        self.assertEqual(len(view["questions"]), 3)
        answers = {q["id"]: q["expected"][0]
                   for q in motivation.checkpoint_bank("en")[1]["questions"]}
        response = self.client.post(BASE + "/motivation/challenge", json={
            "language": "en", "week": 1, "answers": answers})
        self.assertTrue(response.json()["passed"], response.text)

    def test_german_review_and_checkpoint_canonical_case_grading(self):
        q = next(q for row, section, q in motivation.exact_questions("de").values()
                 if q["id"].endswith("g001-q1"))
        self.assertFalse(self.post(q["id"], "buch", language="de").json()["correct"])
        self.time.return_value += timedelta(days=1)
        self.assertEqual(self.get_motivation("de")["review"][0]["id"], q["id"])
        self.assertTrue(self.review(q, "Buch", language="de").json()["correct"])
        self.assertEqual(self.get_motivation("en")["learning"]["corrections"], 0)
        self.assertEqual(self.get_motivation("de")["learning"]["corrections"], 1)
        self.unlock("de")
        self.assertTrue(self.boss(language="de").json()["passed"])
        self.assertEqual(self.get_motivation("en")["rewards"]["xp"], 0)


    def test_demo_test_branch_and_demo_login_never_receive_global_rewards(self):
        for marker in ("branch", "name", "login"):
            student = self.db.get(models.Student, 1)
            user = self.db.get(models.User, 11)
            student.branch_id = 2 if marker == "branch" else 1
            student.full_name = "Learner (DEMO)" if marker == "name" else "One"
            user.username = "demo.learner" if marker == "login" else "real11"
            self.db.commit()
            lesson = {"branch": 1, "name": 2, "login": 3}[marker]
            q = self.q(lesson=lesson)
            self.assertEqual(self.post(q["id"], q["expected"][0], lesson=lesson).json()["reward"], motivation.ZERO)
        self.unlock()
        self.assertTrue(self.boss().json()["passed"])
        self.assertEqual(self.db.query(models.XpTransaction).count(), 0)
        self.assertEqual(self.db.query(models.CoinEntry).count(), 0)
        self.assertEqual(self.db.query(models.StudentGamification).count(), 0)



    def seed_daily_cap(self, db=None, student_id=1):
        db = db or self.db
        for i in range(20):
            db.add(models.XpTransaction(student_id=student_id, amount=1, is_reversal=0,
                event_code="course_practice_correct", created_at=motivation.now(),
                idempotency_key=f"{motivation.PREFIX}{student_id}:en:cap:{motivation.local_day()}:{i}"))
        db.commit()

    def test_saved_exact_feedback_exposure_defers_existing_queue_and_stale_post(self):
        q = self.q()
        self.post(q["id"], q["expected"][0])
        self.time.return_value += timedelta(days=1)
        self.assertIn(q["id"], [item["id"] for item in self.get_motivation()["review"]])
        detail = self.detail()
        self.assertEqual(detail["answers"][q["id"]]["result"]["expected"], q["expected"])
        self.assertNotIn(q["id"], [item["id"] for item in self.get_motivation()["review"]])
        self.assertEqual(self.review(q, q["expected"][0]).status_code, 409)
        self.db.rollback()
        self.assertEqual(self.db.query(models.XpTransaction).count(), 1)
        self.time.return_value += timedelta(days=1)
        self.assertIn(q["id"], [item["id"] for item in self.get_motivation()["review"]])
        self.assertEqual(self.review(q, q["expected"][0]).json()["reward"]["xp"], 8)

    def test_self_only_lesson_feedback_has_no_review_exposure(self):
        selfq = next(q for s in practice.BANK["en"][0]["sections"] for q in s["questions"] if q["mode"] == "self")
        self.post(selfq["id"], "Own answer")
        self.detail()
        self.assertEqual(self.db.query(models.IntegrationSetting).count(), 0)

    def test_completed_review_restarts_after_new_error_without_farming_old_stage_claims(self):
        q = self.q()
        self.post(q["id"], q["expected"][0])
        self.time.return_value += timedelta(days=1)
        for delay in (3, 7, 14, 14):
            self.assertEqual(self.review(q, q["expected"][0]).json()["reward"]["xp"], 8)
            self.time.return_value += timedelta(days=delay)
        self.assertEqual(motivation.get(self.db, motivation.state_key(1, q["id"]))["stage"], 4)
        self.post(q["id"], "forgot")
        self.assertEqual(motivation.get(self.db, motivation.state_key(1, q["id"]))["stage"], 0)
        self.time.return_value += timedelta(days=1)
        self.assertIn(q["id"], [item["id"] for item in self.get_motivation()["review"]])
        self.assertEqual(self.review(q, q["expected"][0]).json()["reward"], motivation.ZERO)
        self.time.return_value += timedelta(days=1)
        self.assertIn(q["id"], [item["id"] for item in self.get_motivation()["review"]])
        self.assertEqual(self.review(q, q["expected"][0]).json()["reward"], motivation.ZERO)
        self.assertEqual(motivation.get(self.db, motivation.state_key(1, q["id"]))["stage"], 1)
        self.assertEqual(self.db.query(models.XpTransaction).count(), 5)

    def claim(self, language="en", week=1, **extra):
        return self.client.post(BASE + "/motivation/claim", json={"language": language, "week": week, **extra})

    def test_capped_independent_boss_pass_claim_after_reset_preserves_original_classification(self):
        self.unlock()
        self.seed_daily_cap()
        result = self.boss().json()
        self.assertTrue(result["passed"])
        self.assertEqual(result["reward"], dict(motivation.ZERO, reason="daily_limit"))
        view = self.client.get(BASE + "/motivation/challenge?language=en&week=1").json()
        self.assertTrue(view["reward_pending"])
        self.assertTrue(self.claim().json()["pending"])
        self.assertEqual(self.claim().json()["reward"]["reason"], "daily_limit")
        self.assertEqual(self.db.query(models.XpTransaction).count(), 20)
        self.user = SimpleNamespace(id=22, role="student", full_name="Two", is_active=1)
        self.assertEqual(self.claim().status_code, 409)
        self.db.rollback()
        self.user = SimpleNamespace(id=11, role="student", full_name="One", is_active=1)
        self.assertEqual(self.claim(language="de").status_code, 409)
        self.db.rollback()
        self.assertEqual(self.claim(student_id=2).status_code, 422)
        self.time.return_value += timedelta(days=1)
        result = self.claim().json()
        self.assertEqual(result, {"reward": {"xp": 15, "coins": 2, "reason": "challenge"}, "pending": False})
        self.assertEqual(self.claim().json(), {"reward": motivation.ZERO, "pending": False})
        self.assertFalse(self.client.get(BASE + "/motivation/challenge?language=en&week=1").json()["reward_pending"])
        state = motivation.get(self.db, motivation.boss_key(1, "en", 1))
        self.assertTrue(state["independent_pass"])
        self.assertEqual(state["round"], 0)
        self.assertEqual(self.get_motivation()["learning"]["independent"], 1)

    def test_capped_corrected_boss_pass_remains_correction_when_claimed(self):
        self.unlock()
        wrong = {q["id"]: "wrong" for q in BOSS["en"][1]["questions"]}
        self.boss(answers=wrong)
        self.time.return_value += timedelta(days=7)
        self.seed_daily_cap()
        self.assertEqual(self.boss().json()["reward"]["reason"], "daily_limit")
        self.time.return_value += timedelta(days=1)
        self.assertEqual(self.claim().json()["reward"], {"xp": 2, "coins": 0, "reason": "correction"})
        self.assertEqual(self.get_motivation()["learning"]["independent"], 0)
        self.assertFalse(motivation.get(self.db, motivation.boss_key(1, "en", 1))["independent_pass"])


    def test_pending_boss_claim_parallel_connections_award_exactly_once(self):
        with tempfile.TemporaryDirectory() as directory:
            engine = create_engine("sqlite:///" + str(Path(directory) / "claim.db"),
                                   connect_args={"check_same_thread": False, "timeout": 30})
            for table in (models.Student, models.IntegrationSetting, models.SkillAttempt,
                          models.XpTransaction, models.CoinEntry, models.XpSeason, models.XpRule,
                          models.XpLeague, models.StudentGamification, models.StudentLeagueHistory,
                          models.User, models.Branch):
                table.__table__.create(engine)
            sessions = sessionmaker(bind=engine)
            with sessions() as db:
                db.add(models.Student(id=1, full_name="One", user_id=11, status="active"))
                db.commit()
                self.unlock(db=db)
                self.seed_daily_cap(db=db)
                answers = {q["id"]: q["expected"][0] for q in BOSS["en"][1]["questions"]}
                result = motivation.submit_challenge_batch(db, db.get(models.Student, 1), "en", 1, answers)
                db.commit()
                self.assertEqual(result["reward"]["reason"], "daily_limit")
            self.time.return_value += timedelta(days=1)
            barrier = threading.Barrier(2)
            def worker(_):
                with sessions() as db:
                    student = db.get(models.Student, 1)
                    barrier.wait(timeout=10)
                    result = motivation.claim_boss(db, student, "en", 1)
                    db.commit()
                    return result
            with ThreadPoolExecutor(max_workers=2) as pool:
                results = list(pool.map(worker, range(2)))
            self.assertEqual(sorted(r["reward"]["xp"] for r in results), [0, 15])
            self.assertTrue(all(not r["pending"] for r in results))
            with sessions() as db:
                self.assertEqual(db.query(models.XpTransaction).count(), 21)
                self.assertEqual(db.query(models.CoinEntry).one().amount, 2)
                state = motivation.get(db, motivation.boss_key(1, "en", 1))
                self.assertTrue(state["independent_pass"])
                self.assertFalse(state["reward_pending"])
            engine.dispose()


if __name__ == "__main__":
    unittest.main(verbosity=2)
