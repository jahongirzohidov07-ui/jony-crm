"""Private, bounded creative evidence. Never contributes attempts, mastery or XP."""
import base64
import binascii
import json
from datetime import datetime, timezone
from typing import Literal
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from sqlalchemy import update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

import models
from database import get_db

MAX_AUDIO = 1024 * 1024
MAX_TOTAL_AUDIO = 8 * MAX_AUDIO
MAX_TOTAL_TEXT = 2 * 1024 * 1024
MAX_ENTRIES = 8
MAX_VERSIONS = 3
Language = Literal["en", "de"]
LIMITS = {"entries_per_lesson": MAX_ENTRIES, "versions": MAX_VERSIONS, "text": 6000,
          "audio_bytes": MAX_AUDIO, "total_audio_bytes": MAX_TOTAL_AUDIO,
          "total_text_bytes": MAX_TOTAL_TEXT}


class AudioIn(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    mime: Literal["audio/webm", "audio/webm;codecs=opus", "audio/ogg", "audio/ogg;codecs=opus", "audio/mp4"]
    base64: str = Field(min_length=1, max_length=4 * ((MAX_AUDIO + 2) // 3))

    @model_validator(mode="after")
    def validate_recording(self):
        try:
            raw = base64.b64decode(self.base64, validate=True)
        except (ValueError, binascii.Error):
            raise ValueError("Audio base64 formati noto‘g‘ri")
        if not raw or len(raw) > MAX_AUDIO:
            raise ValueError("Audio 1 MiB dan oshmasin")
        # Accept only known audio containers; URLs and disguised HTML are never served.
        valid = ((self.mime.startswith("audio/webm") and raw.startswith(b"\x1aE\xdf\xa3") and b"A_OPUS" in raw[:65536])
                 or (self.mime.startswith("audio/ogg") and raw.startswith(b"OggS") and b"OpusHead" in raw[:65536])
                 or (self.mime == "audio/mp4" and raw[4:8] == b"ftyp" and b"mp4a" in raw))
        if not valid:
            raise ValueError("Audio turi va yozuv formati mos emas")
        return self


class WorkIn(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    title: str = Field(min_length=1, max_length=100)
    type: Literal["dialogue", "story", "speaking"]
    text: str = Field(max_length=6000)
    audio: AudioIn | None = None

    @field_validator("title")
    @classmethod
    def title_not_blank(cls, value):
        if not value.strip():
            raise ValueError("Sarlavha yozing")
        return value.strip()

    @model_validator(mode="after")
    def has_content(self):
        if not self.text.strip() and self.audio is None:
            raise ValueError("Matn yoki ovozli yozuv kerak")
        return self


class RevisionIn(WorkIn):
    expected_version: int = Field(ge=1, le=MAX_VERSIONS)


def _load(db, student_id):
    key = f"course-portfolio:v1:{student_id}"
    raw = db.query(models.IntegrationSetting.value).filter_by(key=key).scalar()
    return key, raw, json.loads(raw) if raw else {"entries": []}


def _persist(db, key, old, state):
    # Optimistic compare-and-swap protects both immutable history and global quotas
    # across workers. No in-process lock or read/modify/write lost updates.
    raw = json.dumps(state, ensure_ascii=False, separators=(",", ":"))
    try:
        if old is None:
            db.add(models.IntegrationSetting(key=key, value=raw))
            db.flush()
        else:
            result = db.execute(update(models.IntegrationSetting).where(
                models.IntegrationSetting.key == key, models.IntegrationSetting.value == old
            ).values(value=raw).execution_options(synchronize_session=False))
            if result.rowcount != 1:
                db.rollback()
                raise HTTPException(409, "Portfolio o‘zgargan. Qayta ochib urinib ko‘ring.")
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Portfolio o‘zgargan. Qayta ochib urinib ko‘ring.")


def _entry(state, entry_id, language, lesson):
    for entry in state["entries"]:
        if entry["id"] == entry_id and entry["language"] == language and entry["lesson"] == lesson:
            return entry
    raise HTTPException(404, "Ijodiy ish topilmadi")


def _version(body, number):
    return {**body.model_dump(exclude={"expected_version"}), "number": number,
            "created_at": datetime.now(timezone.utc).isoformat()}


def _audio_bytes(state):
    return sum(len(base64.b64decode(v["audio"]["base64"])) for e in state["entries"]
               for v in e["versions"] if v["audio"])


def _text_bytes(state):
    return sum(len((v["title"] + v["text"]).encode("utf-8"))
               for e in state["entries"] for v in e["versions"])


def _check_quota(state):
    if _audio_bytes(state) > MAX_TOTAL_AUDIO:
        raise HTTPException(409, "Jami audio 8 MiB chegarasiga yetdi. Eski ishni tanlab o‘chirishingiz mumkin.")
    if _text_bytes(state) > MAX_TOTAL_TEXT:
        raise HTTPException(409, "Jami matn 2 MiB chegarasiga yetdi. Eski ishni tanlab o‘chirishingiz mumkin.")


def _summary(entry):
    latest = entry["versions"][-1]
    return {k: entry[k] for k in ("id", "language", "lesson")} | {
        "title": latest["title"], "type": latest["type"], "version_count": len(entry["versions"]),
        "updated_at": latest["created_at"], "has_audio": latest["audio"] is not None}


def make_router(student_dependency, lesson_lookup):
    router = APIRouter(prefix="/portfolio")

    def scope(response: Response, language: Language, lesson: int = Query(ge=1, le=192),
              student=Depends(student_dependency)):
        response.headers["Cache-Control"] = "private, no-store"
        response.headers["Vary"] = "Authorization"
        return student, language, lesson, lesson_lookup(language, lesson)

    @router.get("")
    def listing(context=Depends(scope), db: Session = Depends(get_db)):
        student, language, lesson, row = context
        _, _, state = _load(db, student.id)
        entries = [_summary(e) for e in state["entries"] if e["language"] == language and e["lesson"] == lesson]
        # Canonical task, not an AI-generated assessment or a skill score.
        task = next((q["prompt"] for s in row["sections"] for q in s["questions"] if q["mode"] == "self"), "")
        return {"entries": sorted(entries, key=lambda e: e["updated_at"], reverse=True),
                "limits": LIMITS, "total_entries": len(state["entries"]),
                "lesson_entries": len(entries), "total_text_bytes": _text_bytes(state),
                "total_audio_bytes": _audio_bytes(state), "lesson_title": row["title"],
                "prompt": task, "verified_mastery": False, "xp": 0}

    @router.get("/{entry_id}")
    def detail(entry_id: str, context=Depends(scope), db: Session = Depends(get_db)):
        student, language, lesson, _ = context
        return _entry(_load(db, student.id)[2], entry_id, language, lesson)

    @router.post("", status_code=201)
    def create(body: WorkIn, context=Depends(scope), db: Session = Depends(get_db)):
        student, language, lesson, _ = context
        key, old, state = _load(db, student.id)
        if sum(e["language"] == language and e["lesson"] == lesson for e in state["entries"]) >= MAX_ENTRIES:
            raise HTTPException(409, "Bu darsda 8 ish chegarasi. Yangi ish uchun eskisini tanlab o‘chiring.")
        entry = {"id": uuid4().hex, "language": language, "lesson": lesson, "versions": [_version(body, 1)]}
        state["entries"].append(entry)
        _check_quota(state)
        _persist(db, key, old, state)
        return entry

    @router.put("/{entry_id}")
    def revise(entry_id: str, body: RevisionIn, context=Depends(scope), db: Session = Depends(get_db)):
        student, language, lesson, _ = context
        key, old, state = _load(db, student.id)
        entry = _entry(state, entry_id, language, lesson)
        count = len(entry["versions"])
        if body.expected_version != count:
            raise HTTPException(409, "Yangi versiya mavjud. Ishni qayta oching.")
        if count >= MAX_VERSIONS:
            raise HTTPException(409, "3 versiya chegarasiga yetdi. Eski versiyalar saqlanadi.")
        entry["versions"].append(_version(body, count + 1))
        _check_quota(state)
        _persist(db, key, old, state)
        return entry

    @router.delete("/{entry_id}")
    def delete(entry_id: str, context=Depends(scope), db: Session = Depends(get_db)):
        student, language, lesson, _ = context
        key, old, state = _load(db, student.id)
        state["entries"].remove(_entry(state, entry_id, language, lesson))
        _persist(db, key, old, state)
        return {"deleted": True}

    return router
