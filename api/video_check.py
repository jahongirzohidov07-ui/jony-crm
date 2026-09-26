"""VIDEO TEKSHIRUVI (2026-09-26).

Jahongir: "videoni yuklaganda tahlil qiladigan funksiya qosha olamizmi
masalan oxiridaggi tel raqam qoyilmagan, oxirida logo animation
qoshilmagan".

QANDAY ISHLAYDI:
  - Video BRAUZERDA ochiladi (serverga yuklanmaydi — Vercel'ga 100 MB
    video sig'maydi va trafik ham bekorga ketadi). Brauzer davomiylik,
    o'lcham va bir nechta kadrni (boshidan 2 ta, oxirgi 3 soniyadan 3 ta)
    kichik JPEG qilib yuboradi.
  - Server qoida bo'yicha tekshiradi: 9:16 (vertikal), sifat (720p+),
    davomiylik (5–90 s).
  - Kadrlarni Gemini ko'radi: oxirida TELEFON RAQAM bormi (qaysi raqam),
    oxirida LOGO bormi, logo kadrdan kadrga o'zgaryaptimi (animatsiya),
    SUBTITR bormi, birinchi soniyalarda HOOK matni bormi.
  - Natija kontentga yoziladi (video_checks), video o'zi saqlanmaydi.

AI kaliti bo'lmasa — qoida bo'yicha tekshiruv baribir ishlaydi, AI
bandlari "tekshirilmadi" deb aniq yoziladi (jim xato yo'q).
"""
import json
import os
import re

from fastapi import APIRouter, Body, Depends, HTTPException
from sqlalchemy.orm import Session

import audit
import models
import roles
from auth import require_role
from database import get_db

router = APIRouter()

MAX_FRAMES = 8
MAX_FRAME_B64 = 600_000          # ~450 KB JPEG

PROMPT = (
    "You are checking a short vertical marketing video (Instagram Reels) "
    "for an education centre in Uzbekistan. You get still frames with "
    "their timestamps: some from the START and some from the LAST 3 "
    "SECONDS (in time order). Answer ONLY with compact JSON, no prose:\n"
    '{"phone_at_end": true|false, "phone_text": "<number as seen or empty>",'
    ' "logo_at_end": true|false, "logo_animated": true|false|null,'
    ' "subtitles": true|false, "hook_text_start": true|false,'
    ' "notes_uz": "<1-2 short sentences in Uzbek latin about problems>"}\n'
    "phone_at_end: a phone number is clearly readable in the END frames. "
    "logo_at_end: a brand logo is visible in the END frames. "
    "logo_animated: the logo changes position/size/opacity between the "
    "END frames (null if no logo). subtitles: burned-in speech captions "
    "in any frame. hook_text_start: big title/hook text in START frames."
)


def _gemini(frames: list, meta: dict) -> dict:
    import httpx
    key = (os.getenv("GEMINI_API_KEY") or os.getenv("JonyTeacher")
           or os.getenv("JONYTEACHER") or "").strip()
    if not key:
        raise RuntimeError("no-key")
    parts = [{"text": PROMPT + f"\nVideo duration: {meta.get('duration')} s."}]
    for f in frames:
        parts.append({"text": f"Frame at {f.get('t')} s "
                              f"({'END' if f.get('end') else 'START'}):"})
        parts.append({"inlineData": {"mimeType": "image/jpeg",
                                     "data": f["data"].split(",")[-1]}})
    r = httpx.post(
        "https://generativelanguage.googleapis.com/v1beta/models/"
        "gemini-flash-latest:generateContent",
        headers={"x-goog-api-key": key},
        json={"contents": [{"role": "user", "parts": parts}],
              "generationConfig": {"temperature": 0}},
        timeout=60)
    r.raise_for_status()
    txt = " ".join(p.get("text", "") for p in
                   r.json()["candidates"][0]["content"]["parts"])
    m = re.search(r"\{.*\}", txt, re.S)
    if not m:
        raise RuntimeError("AI javobi tushunarsiz")
    return json.loads(m.group(0))


# Testlar tarmoqqa chiqmasligi uchun almashtiriladi
AI = {"call": _gemini}


def rule_checks(duration, width, height) -> list:
    out = []
    w, h = int(width or 0), int(height or 0)
    if w and h:
        ratio = w / h
        ok = 0.54 <= ratio <= 0.58
        out.append({"key": "ratio", "label": "Vertikal 9:16", "ok": ok,
                    "note": (f"{w}×{h}" if ok else
                             f"{w}×{h} — Reels uchun 9:16 (masalan "
                             f"1080×1920) bo'lishi kerak")})
        short = min(w, h)
        out.append({"key": "quality", "label": "Sifat 720p va yuqori",
                    "ok": short >= 720,
                    "note": (f"{short}p" if short >= 720 else
                             f"{short}p — past sifat, 1080×1920 tavsiya")})
    else:
        out.append({"key": "ratio", "label": "Vertikal 9:16", "ok": None,
                    "note": "O'lcham aniqlanmadi"})
    d = float(duration or 0)
    if d:
        ok = 5 <= d <= 90
        out.append({"key": "duration", "label": "Davomiylik 5–90 s",
                    "ok": ok,
                    "note": (f"{d:.0f} s" if ok else
                             (f"{d:.0f} s — juda qisqa" if d < 5 else
                              f"{d:.0f} s — Reels uchun uzun"))})
    return out


def ai_checks(ai: dict | None, err: str | None) -> list:
    labels = [("phone_at_end", "Oxirida telefon raqam"),
              ("logo_at_end", "Oxirida logo"),
              ("logo_animated", "Logo animatsiyasi"),
              ("subtitles", "Subtitr"),
              ("hook_text_start", "Boshida hook matni")]
    if ai is None:
        why = ("AI kaliti sozlanmagan" if err == "no-key"
               else f"AI tekshira olmadi: {err}")
        return [{"key": k, "label": lb, "ok": None, "note": why}
                for k, lb in labels]
    out = []
    for k, lb in labels:
        v = ai.get(k)
        note = ""
        if k == "phone_at_end":
            note = (ai.get("phone_text") or "") if v else \
                "Oxirgi soniyalarda telefon raqam ko'rinmadi — qo'shing"
        elif k == "logo_at_end" and not v:
            note = "Oxirida logo yo'q — brend outro qo'shing"
        elif k == "logo_animated":
            if v is None:
                note = "Logo yo'q — animatsiya ham yo'q"
                v = False
            elif not v:
                note = "Logo qimirlamayapti — logo animatsiyasini qo'shing"
        elif k == "subtitles" and not v:
            note = "Subtitr yo'q — ko'pchilik ovozsiz ko'radi"
        elif k == "hook_text_start" and not v:
            note = "Birinchi soniyada katta hook matni yo'q"
        out.append({"key": k, "label": lb,
                    "ok": bool(v) if v is not None else None, "note": note})
    return out


@router.post("/api/content/{cid}/video-check")
def video_check(cid: int, payload: dict = Body(...),
                db: Session = Depends(get_db),
                user=Depends(require_role(*roles.SMM_ACCESS))):
    c = db.query(models.Content).get(cid)
    if not c:
        raise HTTPException(404, "Kontent topilmadi")
    frames = [f for f in (payload.get("frames") or [])
              if isinstance(f, dict) and f.get("data")][:MAX_FRAMES]
    for f in frames:
        if len(f["data"]) > MAX_FRAME_B64:
            raise HTTPException(400, "Kadr juda katta (brauzer kichraytirishi kerak)")
    dur = payload.get("duration")
    w, h = payload.get("width"), payload.get("height")

    checks = rule_checks(dur, w, h)
    ai, err = None, None
    if frames:
        try:
            ai = AI["call"](frames, {"duration": dur})
        except Exception as e:           # AI yiqilsa ham qoida natijasi qoladi
            err = str(e)[:160]
    else:
        err = "kadr yuborilmadi"
    checks += ai_checks(ai, err)
    bad = [x for x in checks if x["ok"] is False]
    ok = not bad
    summary = ("Hammasi joyida" if ok else
               "Tuzatish kerak: " + "; ".join(x["label"] for x in bad))
    res = {"checks": checks, "ok": ok, "summary": summary,
           "ai_notes": (ai or {}).get("notes_uz"),
           "phone_text": (ai or {}).get("phone_text")}
    row = models.VideoCheck(
        content_id=c.id, file_name=(payload.get("file_name") or "")[:200],
        duration=float(dur) if dur else None,
        width=int(w) if w else None, height=int(h) if h else None,
        ok=1 if ok else 0, result=json.dumps(res, ensure_ascii=False),
        created_by=user.full_name)
    db.add(row)
    db.commit()
    try:
        audit.log(db, user, entity="content", action="video_check",
                  entity_id=c.id, entity_label=c.title,
                  note=f"Video tekshiruvi: {summary}"[:250],
                  branch_id=c.branch_id)
        db.commit()
    except Exception:
        db.rollback()
    return {"id": row.id, **res}


@router.get("/api/content/{cid}/video-checks")
def video_checks(cid: int, db: Session = Depends(get_db),
                 user=Depends(require_role(*roles.CONTENT_REQUESTER))):
    rows = (db.query(models.VideoCheck)
            .filter(models.VideoCheck.content_id == cid)
            .order_by(models.VideoCheck.id.desc()).limit(10).all())
    out = []
    for r in rows:
        try:
            res = json.loads(r.result or "{}")
        except Exception:
            res = {}
        out.append({"id": r.id, "file_name": r.file_name, "ok": bool(r.ok),
                    "by": r.created_by,
                    "at": r.created_at.isoformat() if r.created_at else None,
                    **res})
    return {"rows": out}
