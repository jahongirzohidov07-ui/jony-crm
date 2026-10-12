"""Authenticated Russian course content and isolated practice progress."""
import copy
import json
import re
import unicodedata
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, ConfigDict, StrictStr
from sqlalchemy import case
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.orm import Session

import models
from auth import require_role
from database import get_db
from student_app import _me
from student_russian_models import StudentRussianProgress

router = APIRouter(prefix="/api/student/russian", tags=["student-russian"])
LESSONS = json.loads(Path(__file__).with_name("student_russian_data.json").read_text(encoding="utf-8"))
_BY_NO = {lesson["no"]: lesson for lesson in LESSONS}


class CheckIn(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    kind: Literal["grammar", "vocabulary"]
    answers: list[StrictStr]


def _student(request: Request, db: Session = Depends(get_db),
             user=Depends(require_role("student"))):
    # The legacy resolver can return or auto-link a same-name student's card.
    # This API requires a pre-existing explicit account link.
    if not db.query(models.Student.id).filter_by(user_id=user.id).first():
        raise HTTPException(403, "O'quvchi hisobi bog'lanmagan")
    student = _me(db, user)
    if student.user_id != user.id:
        raise HTTPException(403, "O'quvchi hisobi mos kelmaydi")
    if "student_id" in request.query_params:
        raise HTTPException(422, "student_id is not accepted")
    return student


def _lesson(no: int):
    lesson = _BY_NO.get(no)
    if lesson is None:
        raise HTTPException(404, "Dars topilmadi")
    return lesson


def normalize(value: str) -> str:
    # Apostrophe glyphs used in Uzbek are equivalent; punctuation is ignored.
    value = unicodedata.normalize("NFKC", value).casefold()
    value = "".join(c for c in value
                    if not unicodedata.category(c).startswith("P")
                    and c not in "ʻʼ")
    return " ".join(value.split())


def _matches(value: str, expected: str) -> bool:
    actual = normalize(value)
    if not actual:
        return False
    # Only explicit, space-delimited alternatives in the canonical answer.
    variants = [expected, *re.split(r"\s+/\s+", expected)]
    return any(actual == normalize(answer) for answer in variants)


def _progress(row):
    return {key: getattr(row, key) for key in
            ("lesson_no", "kind", "best_score", "total", "attempts")}


@router.get("/course")
def course(db: Session = Depends(get_db), student=Depends(_student)):
    rows = (db.query(StudentRussianProgress)
            .filter_by(student_id=student.id)
            .order_by(StudentRussianProgress.lesson_no, StudentRussianProgress.kind).all())
    return {
        "lessons": [{**{key: lesson[key] for key in ("no", "month", "title", "objective")},
                     "phrase_count": len(lesson["phrases"]),
                     "grammar_title": lesson["grammar"]["title"]} for lesson in LESSONS],
        "progress": [_progress(row) for row in rows],
    }


@router.get("/lessons/{no}")
def lesson(no: int, student=Depends(_student)):
    result = copy.deepcopy(_lesson(no))
    result["grammar"]["exercises"] = [
        {"prompt": item["prompt"]} for item in result["grammar"]["exercises"]]
    return result


@router.post("/lessons/{no}/check")
def check(no: int, body: CheckIn, db: Session = Depends(get_db), student=Depends(_student)):
    data = _lesson(no)
    items = (data["grammar"]["exercises"] if body.kind == "grammar" else
             [{"prompt": phrase["ru"], "answer": phrase["uz"], "explanation": ""}
              for phrase in data["phrases"]])
    if len(body.answers) != len(items):
        raise HTTPException(422, "Javoblar soni mashqlar soniga teng bo'lishi kerak")
    results = [{"correct": _matches(answer, item["answer"]),
                "answer": item["answer"], "explanation": item["explanation"]}
               for answer, item in zip(body.answers, items)]
    score, total = sum(result["correct"] for result in results), len(items)
    model = StudentRussianProgress
    insert = sqlite_insert if db.get_bind().dialect.name == "sqlite" else pg_insert
    statement = insert(model).values(
        student_id=student.id, lesson_no=no, kind=body.kind,
        best_score=score, total=total, attempts=1)
    # Atomic upsert also protects the first attempt and concurrent retries.
    statement = statement.on_conflict_do_update(
        index_elements=["student_id", "lesson_no", "kind"],
        set_={"best_score": case((model.best_score < score, score), else_=model.best_score),
              "total": total, "attempts": model.attempts + 1})
    db.execute(statement)
    db.commit()
    row = db.query(model).filter_by(student_id=student.id, lesson_no=no, kind=body.kind).one()
    return {"score": score, "total": total, "results": results, "progress": _progress(row)}
