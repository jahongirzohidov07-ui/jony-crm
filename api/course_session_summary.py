"""Read-only observations for the current saved plan, never a proficiency score."""
from datetime import datetime, timedelta
from typing import Literal

from pydantic import BaseModel, Field
import course_motivation as m


class SummaryItem(BaseModel):
    question_id: str
    lesson: int
    prompt: str
    skill: str


class SummaryGroup(BaseModel):
    count: int = 0
    items: list[SummaryItem] = Field(default_factory=list)


class SummaryPlan(BaseModel):
    status: Literal["active", "missing"] = "missing"
    total: int = 0
    completed: int = 0


class NextReview(BaseModel):
    # Scheduler calendar date in Asia/Tashkent, not a promised recall outcome.
    due_at: str
    items: list[SummaryItem]


class Comparison(BaseModel):
    question_count: int
    before_correct: int
    after_correct: int


class SessionSummary(BaseModel):
    date: str
    language: Literal["en", "de"]
    plan: SummaryPlan = Field(default_factory=SummaryPlan)
    independent: SummaryGroup = Field(default_factory=SummaryGroup)
    corrections: SummaryGroup = Field(default_factory=SummaryGroup)
    needs_practice: SummaryGroup = Field(default_factory=SummaryGroup)
    ungraded: SummaryGroup = Field(default_factory=SummaryGroup)
    next_review: NextReview | None = None
    comparison: Comparison | None = None


def session_summary(db, student_id, language):
    clock = m.now()
    day = (clock + timedelta(hours=5)).date().isoformat()
    result = SessionSummary(date=day, language=language)
    saved = m.get(db, f"course-plan:v1:{student_id}:{language}:current")
    if not saved or saved.get("day") != day:
        return result
    known = m.canonical_questions(language)
    minutes = m.get(db, m.plan_preference_key(student_id, language), 15)
    # A plan stores a pool; only the selected budget's steps are current targets.
    targets = list(dict.fromkeys(step["question_id"] for step in
        m.plan_steps_for_budget(saved["steps"], minutes) if step["question_id"] in known))
    result.plan = SummaryPlan(status="active", total=len(targets))
    day_start = datetime.fromisoformat(day) - timedelta(hours=5)
    plan_start = datetime.fromisoformat(saved["created_at"])
    histories = {qid: [] for qid in targets}
    for attempt in m.question_attempts(db, student_id, language):
        qid = m.attempt_qid(attempt)
        if (qid in histories and attempt.created_at <= clock
                and attempt.answer and attempt.answer.strip()):
            histories[qid].append(attempt)
    comparison = []
    scheduled = []
    for qid, rows in histories.items():
        rows.sort(key=lambda a: (a.created_at, a.id))
        today = [a for a in rows if a.created_at >= max(day_start, plan_start)
                 and a.id > saved["after_id"]]
        if not today:
            continue
        result.plan.completed += 1  # Submitted effort, including wrong/ungraded.
        row, section, question = known[qid]
        item = SummaryItem(question_id=qid, lesson=row["lesson"],
                           prompt=question["prompt"], skill=section["skill"])
        if question["mode"] != "exact":
            # Self-rated answers are stored with correct=0; that is not a failure.
            result.ungraded.items.append(item)
            continue
        if rows[0].id == today[0].id and rows[0].correct == 1:
            result.independent.items.append(item)
        if today[-1].correct == 0:
            result.needs_practice.items.append(item)
        # Carry an unresolved earlier error into today's session. A previous
        # correct answer resets that baseline; only a new wrong->right counts.
        previous = [a for a in rows if (a.created_at, a.id) <
                    (today[0].created_at, today[0].id)]
        wrong_seen = bool(previous and previous[-1].correct == 0)
        for attempt in today:
            if attempt.correct == 0:
                wrong_seen = True
            elif attempt.correct == 1 and wrong_seen:
                result.corrections.items.append(item)
                break
        prior = [a for a in rows if a.created_at < day_start]
        if prior:
            comparison.append((prior[-1].correct == 1, today[-1].correct == 1))
        latest = rows[-1]
        state = m.review_state(db, student_id, qid, latest.created_at)
        if latest.correct == 0 or state["stage"] < len(m.REVIEW_INTERVALS):
            scheduled.append((state["due"], item))
    for group in (result.independent, result.corrections, result.ungraded, result.needs_practice):
        group.count = len(group.items)
    if comparison:
        result.comparison = Comparison(question_count=len(comparison),
            before_correct=sum(pair[0] for pair in comparison),
            after_correct=sum(pair[1] for pair in comparison))
    if scheduled:
        due = min(date for date, _ in scheduled)
        result.next_review = NextReview(due_at=due,
            items=[item for date, item in scheduled if date == due])
    return result
