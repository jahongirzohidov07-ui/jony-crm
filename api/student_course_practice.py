"""Private practice: feedback is visible only for the student's saved attempts."""
import json
import re
import unicodedata
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field, StrictStr
from sqlalchemy.orm import Session

import models
from auth import require_role
from database import get_db
from student_app import _me

router = APIRouter(prefix="/api/student/course-practice", tags=["student-course-practice"])
BANK = json.loads(Path(__file__).with_name("student_course_practice_data.json").read_text(encoding="utf-8"))
LESSONS = {lang: {row["lesson"]: row for row in rows} for lang, rows in BANK.items()}
Language = Literal["en", "de"]


class PositionIn(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    language: Language
    lesson: int = Field(ge=1, le=192)


class AnswerIn(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    language: Language
    lesson: int = Field(ge=1, le=192)
    question_id: StrictStr = Field(min_length=1, max_length=160)
    answer: StrictStr = Field(min_length=1, max_length=6000)


def _student(request: Request, db: Session = Depends(get_db),
             user=Depends(require_role("student"))):
    # Prevent legacy _me's name fallback from auto-linking somebody else's card.
    if not db.query(models.Student.id).filter_by(user_id=user.id).first():
        raise HTTPException(403, "Student account is not linked")
    student = _me(db, user)
    if student.user_id != user.id:
        raise HTTPException(403, "Student account does not match")
    if "student_id" in request.query_params:
        raise HTTPException(422, "student_id is not accepted")
    return student


def _lesson(language, lesson):
    row = LESSONS.get(language, {}).get(lesson)
    if row is None:
        raise HTTPException(404, "Lesson not found")
    return row


def _ref(question_id):
    return "course-practice:v1:" + question_id


def _normalize(value, case_sensitive=False):
    value = unicodedata.normalize("NFKC", value)
    value = value.translate(str.maketrans({"’": "'", "‘": "'", "`": "'"}))
    value = re.sub(r"[.!?,;:]", "", value)
    value = " ".join(value.split())
    return value if case_sensitive else value.casefold()


def _position_key(student_id, language):
    return f"course-position:v1:{student_id}:{language}"


def _save_position(db, student_id, language, lesson):
    # Position is state, not an attempt: analytics counts even incorrect attempts.
    # Atomic upsert prevents duplicate-key races on a student's first visit.
    if db.get_bind().dialect.name == "sqlite":
        from sqlalchemy.dialects.sqlite import insert
    else:
        from sqlalchemy.dialects.postgresql import insert
    table = models.IntegrationSetting.__table__
    statement = insert(table).values(
        key=_position_key(student_id, language), value=str(lesson))
    db.execute(statement.on_conflict_do_update(
        index_elements=[table.c.key],
        set_={"value": statement.excluded.value, "updated_at": statement.excluded.updated_at}))


def _resume(db, student_id, language):
    value = db.query(models.IntegrationSetting.value).filter_by(
        key=_position_key(student_id, language)).scalar()
    if value and value.isdigit():
        lesson = int(value)
        if lesson in LESSONS[language]:
            return lesson
    # Existing students can resume their latest answer before their first visit save.
    attempt = db.query(models.SkillAttempt).filter(
        models.SkillAttempt.student_id == student_id,
        models.SkillAttempt.ref.startswith("course-practice:v1:" + language + ":"),
    ).order_by(models.SkillAttempt.id.desc()).first()
    if attempt:
        parts = attempt.ref.split(":")
        if len(parts) > 3 and parts[3].isdigit() and int(parts[3]) in LESSONS[language]:
            return int(parts[3])
    return BANK[language][0]["lesson"]


def _progress(questions, refs, correct_refs):
    ids = {_ref(q["id"]) for q in questions}
    return {"question_count": len(ids), "submitted_count": len(ids & refs),
            "correct_count": len(ids & correct_refs), "completed": bool(ids) and ids <= refs}


def _feedback(section, question, correct):
    result = {"correct": correct, "expected": question["expected"],
              "explanation": question["explanation"], "saved": True}
    if "criteria" in question:
        result["criteria"] = question["criteria"]
    if section["skill"] == "listening":
        result["transcript"] = section["transcript"]
    return result


@router.post("/position")
def position(body: PositionIn, db: Session = Depends(get_db), student=Depends(_student)):
    _lesson(body.language, body.lesson)
    _save_position(db, student.id, body.language, body.lesson)
    db.commit()
    return {"saved": True, "language": body.language, "resume_lesson": body.lesson}


@router.get("")
def course(language: Language, db: Session = Depends(get_db), student=Depends(_student)):
    attempts = db.query(models.SkillAttempt.ref, models.SkillAttempt.correct).filter(
        models.SkillAttempt.student_id == student.id,
        models.SkillAttempt.ref.startswith("course-practice:v1:" + language + ":"),
    ).all()
    refs = {ref for ref, _ in attempts}
    correct_refs = {ref for ref, correct in attempts if correct == 1}
    lessons = []
    for row in BANK[language]:
        ids = {q["id"] for section in row["sections"] for q in section["questions"]}
        lessons.append({key: row[key] for key in ("lesson", "title", "level")} | {
            "question_count": len(ids),
            "submitted_count": sum(_ref(qid) in refs for qid in ids),
            "correct_count": sum(_ref(qid) in correct_refs for qid in ids),
            # Completion means submitted, including self checks, not proficiency.
            "completed": bool(ids) and all(_ref(qid) in refs for qid in ids),
        })
    resume = _resume(db, student.id, language)
    row = _lesson(language, resume)
    plan = {key: row[key] for key in ("language", "lesson", "title", "level", "audio_url")}
    plan.update(_progress([q for section in row["sections"] for q in section["questions"]], refs, correct_refs))
    plan["sections"] = [
        {key: section[key] for key in ("id", "title", "skill")} |
        _progress(section["questions"], refs, correct_refs) for section in row["sections"]
    ]
    return {"language": language, "title": "English" if language == "en" else "Deutsch",
            "lessons": lessons, "resume_lesson": resume, "plan": plan}


@router.get("/{lesson}")
def lesson_detail(lesson: int, language: Language, student=Depends(_student), db: Session = Depends(get_db)):
    row = _lesson(language, lesson)
    result = {key: row[key] for key in ("language", "lesson", "title", "audio_url")}
    attempts = db.query(models.SkillAttempt).filter(
        models.SkillAttempt.student_id == student.id,
        models.SkillAttempt.ref.startswith(f"course-practice:v1:{language}:{lesson}:"),
    ).order_by(models.SkillAttempt.id.desc()).all()
    latest = {}
    for attempt in attempts:
        latest.setdefault(attempt.ref, attempt)
    result["answers"] = {}
    for section in row["sections"]:
        for question in section["questions"]:
            attempt = latest.get(_ref(question["id"]))
            if attempt is not None:
                correct = None if question["mode"] == "self" else attempt.correct == 1
                result["answers"][question["id"]] = {
                    "answer": attempt.answer, "result": _feedback(section, question, correct)}
    result["sections"] = []
    for section in row["sections"]:
        public = {key: section[key] for key in ("id", "title", "skill")}
        if section["skill"] != "listening" and "text" in section:
            public["text"] = section["text"]
        public["questions"] = [
            {key: q[key] for key in ("id", "prompt", "mode", "options") if key in q}
            for q in section["questions"]
        ]
        result["sections"].append(public)
    return result


@router.post("/answer")
def answer(body: AnswerIn, db: Session = Depends(get_db), student=Depends(_student)):
    row = _lesson(body.language, body.lesson)
    found = next(((s, q) for s in row["sections"] for q in s["questions"]
                  if q["id"] == body.question_id), None)
    if found is None:
        raise HTTPException(404, "Question not found in this lesson")
    if not body.answer.strip():
        raise HTTPException(422, "Answer must not be blank")
    section, question = found
    correct = None
    if question["mode"] == "exact":
        case_sensitive = question.get("caseSensitive", False)
        correct = any(_normalize(body.answer, case_sensitive) == _normalize(expected, case_sensitive)
                      for expected in question["expected"])
    db.add(models.SkillAttempt(
        student_id=student.id,
        skill="course-practice:" + body.language + ":" + section["skill"],
        ref=_ref(question["id"]), answer=body.answer, correct=int(correct is True),
    ))
    # A delayed answer must never move the explicitly visited lesson backwards.
    db.commit()  # Deliberately no XP, coins or other reward mutation.
    return _feedback(section, question, correct)
