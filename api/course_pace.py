"""Bounded client-reported focused time; never ability, progress or rewards."""
from statistics import median
from datetime import datetime, timedelta
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

import models
import course_motivation as motivation
from database import get_db


class PaceIn(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    language: Literal["en", "de"]
    lesson: int = Field(ge=1, le=192)
    question_id: str = Field(min_length=1, max_length=160)
    active_seconds: int = Field(ge=3, le=600)
    attempt_id: int = Field(ge=1)


def key(student_id, language):
    return f"course-pace:v1:{student_id}:{language}"


def estimates(db, student_id, language):
    samples = motivation.get(db, key(student_id, language), {}).get("samples", [])
    # Defensive dedupe for previously persisted payloads as well as POST retries.
    cutoff = motivation.now() - timedelta(days=28)
    return [s for s in list({s["attempt_id"]: s for s in samples}.values())[-60:]
            if cutoff <= datetime.fromisoformat(s["recorded_at"].removesuffix("Z")) <= motivation.now()
            and cutoff <= datetime.fromisoformat(s["attempt_created_at"].removesuffix("Z")) <= motivation.now()]


def estimate(samples, skill):
    selected = [s for s in samples if s["skill"] == skill]
    source = "default"
    used = []
    if len(samples) >= 5:
        used = selected if len(selected) >= 3 else samples
        source = "skill_median" if len(selected) >= 3 else "overall_median"
    seconds = max(30, min(600, median(s["active_seconds"] for s in used))) if used else 300
    return {"minutes": round(seconds / 60, 2), "estimate_source": source,
            "sample_count": len(used), "available_sample_count": len(samples),
            "time_basis": "client_reported_focused_time"}


def record(db, student, body, lesson_lookup):
    row = lesson_lookup(body.language, body.lesson)
    found = next(((s, q) for s in row["sections"] for q in s["questions"]
                  if q["id"] == body.question_id), None)
    if found is None:
        raise HTTPException(404, "Question not found in this lesson")
    section, question = found
    motivation.lock(db, student.id)
    attempt = db.get(models.SkillAttempt, body.attempt_id)
    if (attempt is None or attempt.student_id != student.id
            or attempt.ref != "course-practice:v1:" + question["id"]
            or attempt.skill != f"course-practice:{body.language}:{section['skill']}"
            or not motivation.meaningful(attempt)
            or not motivation.now() - timedelta(days=28) <= attempt.created_at <= motivation.now()):
        raise HTTPException(404, "Saved attempt not found in this scope")
    state = motivation.get(db, key(student.id, body.language), {"samples": [], "retired_through": 0})
    existing = next((s for s in state["samples"] if s["attempt_id"] == attempt.id), None)
    if existing:
        return {"saved": True, "duplicate": True, "sample": existing}
    # A scalar tombstone prevents evicted retries from becoming new samples.
    # Late samples older than the eviction watermark are intentionally ignored.
    if attempt.id <= state["retired_through"]:
        return {"saved": False, "duplicate": True, "reason": "outside_retained_window"}
    sample = {"attempt_id": attempt.id, "question_id": question["id"],
              "lesson": body.lesson, "language": body.language, "skill": section["skill"],
              "active_seconds": min(600, body.active_seconds), "client_reported": True,
              "recorded_at": motivation.now().isoformat() + "Z",
              "attempt_created_at": attempt.created_at.isoformat() + "Z"}
    state["samples"].append(sample)
    if len(state["samples"]) > 60:
        retired = state["samples"].pop(0)
        state["retired_through"] = max(state["retired_through"], retired["attempt_id"])
    motivation.put(db, key(student.id, body.language), state)
    return {"saved": True, "duplicate": False, "sample": sample}


def make_router(student_dependency, lesson_lookup):
    router = APIRouter(tags=["student-course-pace"])

    @router.post("/pace")
    def post_pace(body: PaceIn, db: Session = Depends(get_db), student=Depends(student_dependency)):
        try:
            result = record(db, student, body, lesson_lookup)
            db.commit()
            return result
        except Exception:
            db.rollback()
            raise

    return router
