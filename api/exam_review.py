"""IMTIHON NATIJASI VA XATOLAR TAHLILI — O'QUVCHIGA (2026-10-03).

Jahongir: "imtihon natijalari o'ziga ko'rinib turishi kerak qayerdadir,
lekin bosh sahifada alohida bo'lim ochma; keyin shu imtihonning tahlili
ko'rinishi kerak — javoblarni yodlab oladigan emas, xatosini tushunadigan
bo'lsin, mavzu yuzasidan bersin tahlilni, aynan savolning o'zini bersin".

Qoidalar:
  * Faqat examiner natijani E'LON QILGANDAN keyin (ustoz/ota-ona ko'rgan
    payt bilan bir xil) va faqat o'zining topshirig'i.
  * To'g'ri javob O'QUVCHIGA BERILMAYDI. Har xato savol: savolning o'zi,
    o'quvchining javobi, mavzu va qoida tushuntirishi (AI, o'zbekcha).
    AI'ga to'g'ri javob ichki ma'lumot sifatida beriladi (aniq
    tushuntirishi uchun), lekin uni aytmaslik buyuriladi; javobda
    to'g'ri variant matni chiqib qolsa — tozalanadi.
  * Mavzu kesimi: har mavzu bo'yicha to'g'ri/jami — qaysi mavzuni
    takrorlash kerakligi ko'rinadi.
  * Tahlil bir marta yaratiladi va saqlanadi (exam_reviews) — keyingi
    ochilishda AI chaqirilmaydi. AI yo'q bo'lsa — mavzu bo'yicha oddiy
    maslahat, keyinroq qayta urinadi.
"""
import json
import re
from datetime import datetime

from fastapi import Depends, HTTPException
from sqlalchemy import Column, DateTime, Integer, Text
from sqlalchemy.orm import Session

import models
import roles
import exam_online as EO
from common import ensure_tables
from database import Base as _Base
from main import app, get_db, require_role

if getattr(models, "ExamReview", None) is None:
    class ExamReview(_Base):
        """Bitta topshiriqning tayyor tahlili (AI tushuntirishlari)."""
        __tablename__ = "exam_reviews"
        __table_args__ = {"extend_existing": True}

        id = Column(Integer, primary_key=True, index=True)
        submission_id = Column(Integer, unique=True, index=True,
                               nullable=False)
        items_json = Column(Text, nullable=False)   # {qid: tushuntirish}
        ai = Column(Integer, default=1)             # 0 — AI'siz zaxira
        created_at = Column(DateTime, default=datetime.utcnow)

    models.ExamReview = ExamReview
    ensure_tables([ExamReview.__table__])

_RV = models.ExamReview

# Testda almashtiriladi: fn(system, user_text) -> str (JSON)
AI = {"call": None}


def _ai_call(system: str, user_text: str) -> str:
    fn = AI.get("call")
    if fn is not None:
        return fn(system, user_text)
    from student_app import _ai_reply
    return _ai_reply(system, [{"role": "user", "text": user_text}],
                     max_tokens=4000, temperature=0.2, json_mode=True,
                     per_call=20)


_SYSTEM = (
    "Siz o'zbek o'quvchilariga dars beradigan tajribali o'qituvchisiz. "
    "Sizga o'quvchi imtihonda XATO qilgan savollar beriladi: savol, "
    "variantlar, o'quvchining javobi, mavzu va (faqat siz uchun) to'g'ri "
    "javob. Har bir savol uchun O'ZBEK tilida 2-4 gapli tushuntirish "
    "yozing: (1) bu savol qaysi qoida/mavzuni tekshiradi, (2) o'quvchining "
    "javobi nega mos emas, (3) qoidani eslatuvchi BOSHQA, savoldagidan "
    "farqli bitta misol. QAT'IY TAQIQ: to'g'ri javobni, to'g'ri variant "
    "harfini yoki to'g'ri so'zni AYTMANG — o'quvchi javobni yodlamasin, "
    "qoidani tushunib o'zi topsin. Inglizcha misollar inglizcha qolsin. "
    "Faqat JSON qaytaring: {\"items\": [{\"id\": \"...\", \"explain\": "
    "\"...\"}]}"
)


def _fallback(item: dict) -> str:
    t = item.get("topic")
    if t:
        return (f"Bu savol \"{t}\" mavzusini tekshiradi. Shu mavzu "
                "qoidasini qaytadan ko'rib chiqing va savolni yana bir "
                "bor o'zingiz yechib ko'ring.")
    return ("Savolni diqqat bilan qayta o'qing: qaysi so'z yoki qoida "
            "javobni belgilashini toping va o'zingiz yana yechib ko'ring.")


def _scrub(text: str, correct: str | None) -> str:
    """To'g'ri javob tushuntirishda chiqib qolsa — yashiriladi: variant
    harfi ("B)", "B variant", "variant B", "(B)") va 3+ harfli javob
    matni. Qisqa so'z ("is", "a") o'chirilmaydi — u qoida misollarida
    tabiiy uchraydi va javobni o'zi bermaydi."""
    if not correct:
        return text
    for part in re.split(r"\s*/\s*|,\s*", correct):
        lm = re.match(r"^([A-H])\)", part.strip())
        if lm:
            L = lm.group(1)
            for pat in (rf"\(?\b{L}\)", rf"\b{L}\s+variant\w*",
                        rf"variant\w*\s+{L}\b", rf"\b{L}\s+javob\w*"):
                text = re.sub(pat, "…", text, flags=re.I)
        p = re.sub(r"^[A-H]\)\s*", "", part).strip()
        if len(p) >= 3:
            text = re.sub(re.escape(p), "…", text, flags=re.I)
    return text


def _explain(wrong: list, subject: str) -> tuple[dict, bool]:
    """{qid: tushuntirish}, AI ishladimi."""
    if not wrong:
        return {}, True
    payload = [{"id": w["id"], "topic": w.get("topic") or "",
                "question": w["q"], "options": w.get("options") or [],
                "student_answer": w.get("given_text") or "(javob berilmagan)",
                "correct_for_teacher_only": w.get("correct") or ""}
               for w in wrong]
    try:
        raw = _ai_call(_SYSTEM, f"Fan: {subject}\n" + json.dumps(
            {"items": payload}, ensure_ascii=False))
        m = re.search(r"\{.*\}", raw or "", re.S)
        data = json.loads(m.group(0)) if m else {}
        got = {str(x.get("id")): str(x.get("explain") or "").strip()
               for x in data.get("items") or [] if isinstance(x, dict)}
    except Exception:  # noqa: BLE001 — AI bo'lmasa ham sahifa ochilsin
        return {w["id"]: _fallback(w) for w in wrong}, False
    out = {}
    for w in wrong:
        txt = got.get(str(w["id"])) or ""
        out[w["id"]] = _scrub(txt, w.get("correct"))[:900] if txt \
            else _fallback(w)
    return out, bool(got)


def _my_student(db: Session, user):
    s = db.query(models.Student).filter(
        models.Student.user_id == user.id).first()
    if not s:
        raise HTTPException(404, "O'quvchi topilmadi")
    return s


@app.get("/api/student/results")
def student_results(db: Session = Depends(get_db),
                    user=Depends(require_role(roles.STUDENT))):
    """Imtihon natijalari (Profil -> Imtihon natijalarim). Online
    topshirilgan va e'lon qilinganlarida tahlil bor."""
    s = _my_student(db, user)
    rows = (db.query(models.ExamResult, models.Exam)
            .join(models.Exam, models.ExamResult.exam_id == models.Exam.id)
            .filter(models.ExamResult.student_id == s.id,
                    models.Exam.status.in_(["approved", "done"]))
            .order_by(models.Exam.date.desc()).limit(60).all())
    ids = [ex.id for _, ex in rows]
    reviewable = set()
    if ids:
        pub = {o.exam_id for o in db.query(models.ExamOnline).filter(
            models.ExamOnline.exam_id.in_(ids),
            models.ExamOnline.published_at.isnot(None)).all()}
        for sub in db.query(models.ExamSubmission).filter(
                models.ExamSubmission.exam_id.in_(list(pub) or [-1]),
                models.ExamSubmission.student_id == s.id,
                models.ExamSubmission.status == "placed").all():
            reviewable.add(sub.exam_id)
    return {"rows": [{
        "exam_id": ex.id,
        "title": ex.title or roles.exam_title(ex.kind, ex.unit_no),
        "kind": ex.kind,
        "date": ex.date.isoformat() if ex.date else None,
        "score": er.score, "max_score": ex.max_score,
        "percent": er.percent, "band": er.band,
        "absent": bool(er.absent),
        "has_review": ex.id in reviewable,
    } for er, ex in rows]}


@app.get("/api/student/results/{exam_id}/review")
def student_review(exam_id: int, db: Session = Depends(get_db),
                   user=Depends(require_role(roles.STUDENT))):
    s = _my_student(db, user)
    exam = db.query(models.Exam).get(exam_id)
    o = EO._online_of(db, exam_id) if exam else None
    if not exam or not o or not o.published_at:
        raise HTTPException(404, "Tahlil hali tayyor emas")
    sub = (db.query(models.ExamSubmission)
           .filter(models.ExamSubmission.exam_id == exam_id,
                   models.ExamSubmission.student_id == s.id,
                   models.ExamSubmission.status == "placed")
           .order_by(models.ExamSubmission.id.desc()).first())
    if not sub:
        raise HTTPException(404, "Bu imtihonni online topshirmagansiz")

    parts = EO._load(o.parts)
    qmap = EO._qmap(parts)
    sheet = EO._answer_sheet(EO._load(sub.detail), qmap)
    graded = [x for x in sheet if x.get("ok") is not None]

    # Mavzu kesimi
    topics: dict = {}
    for x in graded:
        t = x.get("topic") or "Umumiy"
        a = topics.setdefault(t, {"topic": t, "total": 0, "correct": 0})
        a["total"] += 1
        a["correct"] += 1 if x.get("ok") else 0
    topic_rows = sorted(topics.values(),
                        key=lambda r: (r["correct"] / r["total"], r["topic"]))

    wrong = []
    for x in graded:
        if x.get("ok"):
            continue
        q = qmap.get(x["id"]) or {}
        wrong.append({**x, "options": q.get("options") or []})

    rv = db.query(_RV).filter(_RV.submission_id == sub.id).first()
    expl = json.loads(rv.items_json) if rv else None
    # AI'siz zaxira saqlangan bo'lsa — keyingi ochilishda yana urinadi
    if expl is None or (rv and not rv.ai):
        subject = roles.SUBJECT_LABELS.get(
            getattr(db.query(models.Group).get(exam.group_id), "subject",
                    None) or "", "Ingliz tili")
        expl, ok = _explain(wrong, subject)
        if rv is None:
            rv = _RV(submission_id=sub.id, items_json="{}")
            db.add(rv)
        rv.items_json = json.dumps(expl, ensure_ascii=False)
        rv.ai = 1 if ok else 0
        db.commit()

    res = db.query(models.ExamResult).filter(
        models.ExamResult.exam_id == exam_id,
        models.ExamResult.student_id == s.id).first()
    return {
        "exam_id": exam_id,
        "title": exam.title or roles.exam_title(exam.kind, exam.unit_no),
        "date": exam.date.isoformat() if exam.date else None,
        "score": res.score if res else None,
        "max_score": exam.max_score,
        "percent": res.percent if res else None,
        "online_correct": sum(1 for x in graded if x.get("ok")),
        "online_total": len(graded),
        "topics": topic_rows,
        # To'g'ri javob ATAYLAB yo'q — faqat savol, o'z javobi, tahlil
        "mistakes": [{
            "n": w.get("n"), "part": w.get("part"),
            "q": w.get("q"), "options": w.get("options") or [],
            "image": w.get("image"),
            "your_answer": w.get("given_text"),
            "topic": w.get("topic"),
            "explain": expl.get(w["id"]) or _fallback(w),
        } for w in wrong],
    }
