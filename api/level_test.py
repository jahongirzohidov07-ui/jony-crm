# =====================================================================
#  ADAPTIV DARAJA TESTI (2026-08-21)
#
#  Jahongir: "darajasini aniqlaydigan chuqur bir test qoshaylik level
#  test... masalan togri topsa ozgina qiyinlashtiradi, topsa
#  qiyinlashib ketaveradi darajasi yuqorilab, topolmasa osha darajadan
#  berib koradi yana topolmasa pastroq darajadan berib koradi, shunaqa
#  qilib aniq darajasini topadigan bolishi kerak, u darajasini
#  Grammar, Vocabular, Reading, Listeningdan aniqlashi kerak".
#
#  Qanday ishlaydi (zinapoya-adaptiv):
#   - 4 bo'lim ketma-ket: grammar -> vocabulary -> reading -> listening
#   - Har bo'lim A2 dan boshlanadi. To'g'ri topsa bir daraja yuqoriga.
#   - Xato qilsa O'SHA darajadan yana bitta savol; ikkinchisini ham
#     topolmasa bir daraja pastga.
#   - Pastga tushganda u daraja allaqachon yutilgan bo'lsa — bo'lim
#     tugaydi (daraja aniqlandi). Eng tepada topsa ham tugaydi.
#   - Har bo'limda ko'pi bilan 12 savol.
#   - Javob TEKSHIRUVI faqat serverda: to'g'ri javob mijozga oldindan
#     hech qachon yuborilmaydi.
#
#  Hech narsa o'chirilmaydi: eski urinishlar level_test_sessions va
#  level_test_results jadvallarida saqlanib qoladi.
# =====================================================================
import json
import random
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import Column, DateTime, Integer, String, Text
from sqlalchemy.orm import Session

import models
import roles
from auth import require_role
from common import ensure_tables
from database import Base, get_db
from student_app import _me

router = APIRouter()

# ---- jadval (create_all faqat yo'q jadvalni yaratadi) ----
if getattr(models, "LevelTestSession", None) is None:
    class LevelTestSession(Base):
        """Bitta test urinishi — holati JSON'da (server tomonda)."""

        __tablename__ = "level_test_sessions"
        __table_args__ = {"extend_existing": True}

        id = Column(Integer, primary_key=True, index=True)
        student_id = Column(Integer, index=True, nullable=False)
        status = Column(String, default="active")  # active|done|cancelled
        state = Column(Text)                       # JSON
        created_at = Column(DateTime, default=datetime.utcnow)
        finished_at = Column(DateTime)

    class LevelTestResult(Base):
        """Yakuniy natija — har ko'nikma bo'yicha CEFR daraja."""

        __tablename__ = "level_test_results"
        __table_args__ = {"extend_existing": True}

        id = Column(Integer, primary_key=True, index=True)
        student_id = Column(Integer, index=True, nullable=False)
        grammar_level = Column(String)
        vocab_level = Column(String)
        reading_level = Column(String)
        listening_level = Column(String)
        overall_level = Column(String)
        detail = Column(Text)                      # JSON (savollar soni va h.k.)
        created_at = Column(DateTime, default=datetime.utcnow)

    models.LevelTestSession = LevelTestSession
    models.LevelTestResult = LevelTestResult
    ensure_tables([LevelTestSession.__table__, LevelTestResult.__table__])

_S = models.LevelTestSession
_R = models.LevelTestResult

SECTIONS = ("grammar", "vocabulary", "reading", "listening")
SECTION_LABELS = {"grammar": "Grammar", "vocabulary": "Vocabulary",
                  "reading": "Reading", "listening": "Listening"}
LADDERS = {
    "grammar": ["A1", "A2", "B1", "B2"],
    "vocabulary": ["A1", "A2", "B1", "B2"],
    "reading": ["A1", "A2", "B1"],   # hozircha matnlar B1 gacha
    "listening": ["A1", "A2", "B1", "B2"],
}
MAX_PER_SECTION = 12
CEFR_ORDER = ["A1", "A2", "B1", "B2"]
CEFR_UZ = {"A1": "Boshlang'ich", "A2": "Elementary",
           "B1": "O'rta (Intermediate)", "B2": "Yuqori o'rta"}
# Taxminiy IELTS mosligi (natija kartasi uchun)
CEFR_IELTS = {"A1": "3.0", "A2": "4.0", "B1": "5.0-5.5", "B2": "6.0-6.5"}


def _new_state() -> dict:
    return {
        "sec_i": 0,          # SECTIONS bo'yicha indeks
        "idx": 1,            # zinadagi daraja indeksi (A2 dan boshlanadi)
        "tries": 0,          # joriy darajadagi xato urinishlar
        "passed": {},        # {"grammar": [false,true,...]}
        "failed": {},
        "count": 0,          # joriy bo'limda berilgan savollar
        "asked": [],         # takror bermaslik uchun ref'lar
        "results": {},       # {"grammar": "B1", ...}
        "totals": {},        # {"grammar": {"asked": 7, "correct": 4}}
        "cur": None,         # {"ref","answer","payload"}
    }


# ------------------------- savol tuzuvchilar -------------------------

def _mk_grammar(db, level, asked):
    qs = (db.query(models.GrammarQuestion)
          .filter(models.GrammarQuestion.is_active == 1,
                  models.GrammarQuestion.level == level,
                  models.GrammarQuestion.kind == "fill").all())
    qs = [q for q in qs if f"g:{q.id}" not in asked]
    if not qs:
        return None
    q = random.choice(qs)
    opts = json.loads(q.options)
    random.shuffle(opts)
    return {"ref": f"g:{q.id}", "answer": q.answer.strip(),
            "payload": {"kind": "mcq", "prompt": q.prompt,
                        "options": opts,
                        "hint": "Bo'sh joyga mosini tanlang"}}


def _vocab_pool(db, level):
    return (db.query(models.VocabWord)
            .filter(models.VocabWord.is_active == 1,
                    models.VocabWord.level == level,
                    (models.VocabWord.language == "en")
                    | (models.VocabWord.language.is_(None))).all())


def _mk_vocab(db, level, asked, listen=False):
    words = _vocab_pool(db, level)
    words = [w for w in words if w.translation]
    pool = [w for w in words if f"w:{w.id}" not in asked]
    if len(pool) < 1 or len(words) < 4:
        return None
    w = random.choice(pool)
    wrong = random.sample(
        [x.translation for x in words
         if x.id != w.id and x.translation != w.translation], 3)
    opts = wrong + [w.translation]
    random.shuffle(opts)
    payload = {"kind": "listen" if listen else "mcq",
               "options": opts}
    if listen:
        payload["say"] = w.word
        payload["hint"] = "Eshiting va tarjimasini tanlang"
    else:
        payload["prompt"] = w.word
        payload["hint"] = "So'zning tarjimasini tanlang"
    return {"ref": f"w:{w.id}", "answer": w.translation.strip(),
            "payload": payload}


def _mk_reading(db, level, asked):
    txts = (db.query(models.ReadingText)
            .filter(models.ReadingText.is_active == 1,
                    models.ReadingText.level == level).all())
    random.shuffle(txts)
    for t in txts:
        qs = (db.query(models.ReadingQuestion)
              .filter(models.ReadingQuestion.text_id == t.id).all())
        qs = [q for q in qs if f"r:{q.id}" not in asked]
        if qs:
            q = random.choice(qs)
            opts = json.loads(q.options)
            random.shuffle(opts)
            return {"ref": f"r:{q.id}", "answer": q.answer.strip(),
                    "payload": {"kind": "read", "text": t.body,
                                "title": t.title, "prompt": q.prompt,
                                "options": opts,
                                "hint": "Matnni o'qib javob bering"}}
    return None


def _make_question(db, st) -> bool:
    """Joriy bo'lim + daraja uchun savol tuzadi. False = savol qolmadi."""
    sec = SECTIONS[st["sec_i"]]
    ladder = LADDERS[sec]
    level = ladder[min(st["idx"], len(ladder) - 1)]
    if sec == "grammar":
        q = _mk_grammar(db, level, st["asked"])
    elif sec == "vocabulary":
        q = _mk_vocab(db, level, st["asked"])
    elif sec == "reading":
        q = _mk_reading(db, level, st["asked"])
    else:
        q = _mk_vocab(db, level, st["asked"], listen=True)
    if not q:
        return False
    st["cur"] = q
    st["asked"].append(q["ref"])
    st["count"] += 1
    tot = st["totals"].setdefault(sec, {"asked": 0, "correct": 0})
    tot["asked"] += 1
    return True


def _section_level(st, sec) -> str:
    """Bo'lim yakuni: eng yuqori YUTILGAN daraja (hech biri bo'lmasa A1)."""
    ladder = LADDERS[sec]
    passed = st["passed"].get(sec, [])
    best = None
    for i, ok in enumerate(passed):
        if ok:
            best = ladder[i]
    return best or ladder[0]


def _finish_section(db, st):
    sec = SECTIONS[st["sec_i"]]
    st["results"][sec] = _section_level(st, sec)
    st["sec_i"] += 1
    st["idx"] = 1
    st["tries"] = 0
    st["count"] = 0
    st["cur"] = None


def _overall(results: dict) -> str:
    idxs = [CEFR_ORDER.index(v) for v in results.values()
            if v in CEFR_ORDER]
    if not idxs:
        return "A1"
    return CEFR_ORDER[round(sum(idxs) / len(idxs))]


def _question_out(st) -> dict:
    sec = SECTIONS[st["sec_i"]]
    return {
        "done": False,
        "section": sec,
        "section_label": SECTION_LABELS[sec],
        "section_no": st["sec_i"] + 1,
        "sections_total": len(SECTIONS),
        "question_no": st["count"],
        "question": st["cur"]["payload"],
    }


def _result_out(res: "_R") -> dict:
    return {
        "done": True,
        "id": res.id,
        "grammar": res.grammar_level,
        "vocabulary": res.vocab_level,
        "reading": res.reading_level,
        "listening": res.listening_level,
        "overall": res.overall_level,
        "overall_label": CEFR_UZ.get(res.overall_level, res.overall_level),
        "ielts": CEFR_IELTS.get(res.overall_level),
        "detail": json.loads(res.detail or "{}"),
        "at": res.created_at.isoformat() if res.created_at else None,
    }


def _finalize(db, sess, st):
    overall = _overall(st["results"])
    res = _R(student_id=sess.student_id,
             grammar_level=st["results"].get("grammar"),
             vocab_level=st["results"].get("vocabulary"),
             reading_level=st["results"].get("reading"),
             listening_level=st["results"].get("listening"),
             overall_level=overall,
             detail=json.dumps({"totals": st["totals"]}))
    db.add(res)
    sess.status = "done"
    sess.finished_at = datetime.utcnow()
    sess.state = json.dumps(st)
    db.commit()
    db.refresh(res)
    return res


# ------------------------------ API ------------------------------

@router.post("/api/student/level-test/start")
def lt_start(db: Session = Depends(get_db),
             user=Depends(require_role(roles.STUDENT))):
    s = _me(db, user)
    # Oldingi tugallanmagani bo'lsa bekor qilinadi (o'chirilmaydi)
    for old in (db.query(_S).filter(_S.student_id == s.id,
                                    _S.status == "active").all()):
        old.status = "cancelled"
    st = _new_state()
    if not _make_question(db, st):
        raise HTTPException(400, "Savollar bazasi hali yuklanmagan")
    sess = _S(student_id=s.id, status="active", state=json.dumps(st))
    db.add(sess)
    db.commit()
    return _question_out(st)


@router.post("/api/student/level-test/answer")
def lt_answer(payload: dict, db: Session = Depends(get_db),
              user=Depends(require_role(roles.STUDENT))):
    s = _me(db, user)
    sess = (db.query(_S).filter(_S.student_id == s.id,
                                _S.status == "active")
            .order_by(_S.id.desc()).first())
    if not sess or not sess.state:
        raise HTTPException(404, "Faol test yo'q — avval boshlang")
    st = json.loads(sess.state)
    cur = st.get("cur")
    if not cur:
        raise HTTPException(400, "Savol topilmadi — testni qayta boshlang")

    given = str(payload.get("answer") or "").strip()
    correct = given.lower() == cur["answer"].strip().lower()

    sec = SECTIONS[st["sec_i"]]
    ladder = LADDERS[sec]
    passed = st["passed"].setdefault(sec, [False] * len(ladder))
    failed = st["failed"].setdefault(sec, [False] * len(ladder))
    if correct:
        st["totals"][sec]["correct"] += 1

    section_over = False
    if correct:
        passed[st["idx"]] = True
        st["tries"] = 0
        if st["idx"] >= len(ladder) - 1 or failed[st["idx"] + 1]:
            # Eng tepani ham topdi (yoki tepasi allaqachon yiqilgan)
            section_over = True
        else:
            st["idx"] += 1        # qiyinlashadi
    else:
        st["tries"] += 1
        if st["tries"] >= 2:      # o'sha darajadan 2-savol ham xato
            failed[st["idx"]] = True
            st["tries"] = 0
            if st["idx"] <= 0:
                section_over = True
            else:
                st["idx"] -= 1    # pastroqdan berib ko'radi
                if passed[st["idx"]]:
                    section_over = True   # bu daraja allaqachon yutilgan

    if st["count"] >= MAX_PER_SECTION:
        section_over = True

    out_correct = {"correct": correct,
                   "expected": None if correct else cur["answer"]}

    if section_over:
        _finish_section(db, st)
        if st["sec_i"] >= len(SECTIONS):
            res = _finalize(db, sess, st)
            return {**out_correct, **_result_out(res)}

    if not section_over:
        st["cur"] = None
    if not _make_question(db, st):
        # Bu darajada savol qolmadi — bo'limni yakunlaymiz
        _finish_section(db, st)
        if st["sec_i"] >= len(SECTIONS):
            res = _finalize(db, sess, st)
            return {**out_correct, **_result_out(res)}
        if not _make_question(db, st):
            # Keyingi bo'limda ham yo'q — butun testni yakunlaymiz
            while st["sec_i"] < len(SECTIONS):
                _finish_section(db, st)
            res = _finalize(db, sess, st)
            return {**out_correct, **_result_out(res)}

    sess.state = json.dumps(st)
    db.commit()
    return {**out_correct, **_question_out(st)}


@router.get("/api/student/level-test/status")
def lt_status(db: Session = Depends(get_db),
              user=Depends(require_role(roles.STUDENT))):
    """Faol test bo'lsa joriy savol, bo'lmasa oxirgi natija."""
    s = _me(db, user)
    sess = (db.query(_S).filter(_S.student_id == s.id,
                                _S.status == "active")
            .order_by(_S.id.desc()).first())
    if sess and sess.state:
        st = json.loads(sess.state)
        if st.get("cur"):
            return {"active": True, **_question_out(st)}
    res = (db.query(_R).filter(_R.student_id == s.id)
           .order_by(_R.id.desc()).first())
    if res:
        return {"active": False, **_result_out(res)}
    return {"active": False, "done": False}
