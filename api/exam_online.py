"""ONLINE TEST — LINK ORQALI (2026-09-18).

Jahongir: "guruhga test biriktirganda unit midterm yoki end of course
link paydo bo'lsin shu linkni examiner telegramdan tashlab bersa
o'quvchilar kirib baholay olsin natijalar to'g'ridan to'g'ri guruhga
biriktirilgan exam natijalarga tushaversin ismi familyasi xato yoki
yangi o'quvchilar bo'lsa qizil chiziqdan pastdan alohida ko'rinsin
examiner uni to'g'irlasa o'z o'rniga tushib qolsin".

  - Test bazasi (ExamTemplate): daraja + tur + unit bo'yicha savollar.
    Examinerlar boshlig'i tahrirlaydi, examinerlar ko'radi.
  - Guruh testiga link (ExamOnline): savollar link ochilgan paytda
    nusxalanadi. Link ochiq/yopiq bo'ladi.
  - O'quvchi ro'yxatdan o'zini tanlaydi (yo'q bo'lsa ismini yozadi),
    kameradan rasm oladi, testni yechadi — server tekshiradi.
  - Ro'yxatdan tanlangan natija guruh testidagi o'z qatoriga tushadi
    (exams._apply_exam_marks: foiz, coin, XP, sertifikat — qo'lda
    kiritish bilan bir xil). Qolganlari "pending" — examiner
    biriktiradi.
  - Writing + Speaking qog'ozda: paper_max > 0 bo'lsa natija qog'oz
    bali kiritilgandagina yoziladi (yarim ball bilan coin berilmaydi).
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import random
import re
import secrets
import time
from datetime import datetime, timedelta
from types import SimpleNamespace
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session, undefer

import audit
import models
import roles
import schemas
import exams as _exams
from auth import require_role
from database import get_db
from common import _group_students, _get_group_in_scope, _seed_done, _seed_mark
import common as _common

router = APIRouter()

# Natija kirita oladiganlar (exams.save_exam_results bilan bir xil)
RESULT_ROLES = [r for r in roles.TEACHING_ACCESS
                if r not in (roles.TEACHER, roles.SUPPORT_TEACHER)]
# Natijalarni TASDIQLAYDI (e'lon qiladi) — examiner tomoni (2026-09-18)
PUBLISH_ROLES = list(dict.fromkeys(roles.EXAM_ACCESS + roles.EXAM_EDIT))

PHOTO_MAX_CHARS = 400_000          # ~300KB rasm (frontend 480px ga kichraytiradi)
_HITS: dict = {}
_MAX_PER_HOUR = 300                # bitta sinf bitta Wi-Fi (bitta IP) dan kiradi
COUNTDOWN_SEC = 10                 # "Start"dan keyin teskari sanoq
AWAY_LIMIT_DEFAULT = 5             # sahifadan chiqishga ruxsat (undan keyin chetlatiladi)
# MOCK — QAT'IY TARTIB (2026-09-27, Jahongir: "mock test faqat kompyuterda
# ishlanadi bizda telda mumkinmas, boshqa joyga ham chiqshi mumkinmas
# qatiy tizim bo'lishi kerak"). Examiner chegara qo'ymagan bo'lsa mockda
# 2 marta chiqishga ruxsat — 3-chisida chetlatiladi. Unit / mid / end
# testlar avvalgidek (telefon ham mumkin, AWAY_LIMIT_DEFAULT).
MOCK_AWAY_LIMIT = 2
MOBILE_MSG = "Mock test faqat kompyuterda ishlanadi"
MOBILE_UA_RE = re.compile(
    r"Android|iPhone|iPad|iPod|Mobile|Tablet|Silk|Kindle|IEMobile|Opera Mini",
    re.I)
# Chiqish sababi (sahifa /away ga yuboradi) — chetlatish izohida examinerga
AWAY_REASONS = {
    "tab": "boshqa varaqqa o'tdi",
    "blur": "boshqa oyna yoki ilovaga o'tdi",
    "fullscreen": "to'liq ekrandan chiqdi",
    "extension": "brauzer kengaytmasi aniqlandi",
    "printscreen": "ekran rasmini olishga urindi",
    "devtools": "dasturchi vositalarini ochdi",
}
NOFS_NOTE = "To'liq ekran ishlamadi (brauzer ruxsat bermadi)"
AWAY_EIDS_KEEP = 40
# O'TISH (mid) VA YAKUNIY (end) TESTLAR 100 BALLIK (2026-09-25,
# Jahongir: "o'tish testi midterm end of course maks ball 100
# bo'ladi"). Unit testlarda esa maksimal ball savollar soniga teng
# bo'lib qolaveradi.
#
# Online qismi savollar sonidan chiqadi (masalan 45), qolgani —
# Writing va Speaking qog'ozda (55). Ikkalasi qo'shilib 100 bo'ladi,
# shuning uchun bu yerda faqat JAMISI belgilanadi; taqsimot
# avtomat: qog'oz = 100 − savollar soni.
MID_END_TOTAL = 100.0
# MOCK = IELTS band (0-9), xom ball emas (src/lib/exams.ts MOCK_MAX_BAND)
MOCK_BAND_MAX = 9.0
GRACE_SEC = 90                     # vaqt tugagach avtomatik topshirish muhlati


def timer_state(o) -> str:
    """waiting — examiner hali Start bosmagan; countdown — teskari sanoq;
    running — savollar ochiq; finished — vaqt tugadi."""
    if not o or not o.started_at or not o.ends_at:
        return "waiting"
    now = datetime.utcnow()
    if now < o.started_at:
        return "countdown"
    if now < o.ends_at:
        return "running"
    return "finished"


def _iso(d):
    # Server vaqti UTC — brauzer to'g'ri hisoblashi uchun "Z" bilan
    return d.isoformat() + "Z" if d else None


# ------------------------------------------------------------- yordamchi
def _norm(s) -> str:
    """Matnli javobni solishtirish uchun: kichik harf, faqat harf va
    raqam ("the USA" = "theusa", "he SA" = "hesa")."""
    s = str(s or "").lower().replace("’", "'").replace("‘", "'")
    return re.sub(r"[^0-9a-zа-яёўқғҳ]", "", s)


def _load(txt) -> list:
    try:
        v = json.loads(txt or "[]")
        return v if isinstance(v, list) else []
    except Exception:
        return []


def _questions(parts: list):
    for p in parts:
        for q in p.get("questions") or []:
            yield q


IMAGE_MAX_CHARS = 300_000          # savol rasmi (data URL) ~220KB
ESSAY_MAX_CHARS = 12_000           # Writing javobi (~1500 so'z)

# TAKRORLANGAN RAQAM VA HARF (2026-09-27, Jahongir skrinshoti:
# "11. 11 The land ..." va "A A a reservoir."). Mock bazasi matnlarida
# savol raqami va variant harfi matnning ICHIDA yozilgan edi, ekran esa
# ularni o'zi qo'shadi. Faqat aniq naqsh olib tashlanadi: raqamdan keyin
# ikki bo'shliq yoki nuqta/qavs ("11  The", "24 and 25  Choose",
# "3. What"); variant harfi esa faqat HAMMA variant ketma-ket A, B, C ...
# bilan boshlansa. "1998 was ..." yoki "3.5 million" kabi oddiy matnga
# tegilmaydi.
_QNUM_RE = re.compile(
    r"^\s*\d{1,3}(?:\s*(?:-|–|and)\s*\d{1,3})?(?:\s{2,}|[.)]\s+)")
_OPT_LETTERS = "ABCDEFGHIJKLMNOP"


def strip_q_prefix(text) -> str:
    s = str(text or "")
    t = _QNUM_RE.sub("", s, count=1)
    return t if t.strip() else s


def strip_opt_prefixes(opts):
    if not opts or len(opts) > len(_OPT_LETTERS):
        return opts
    pats = [re.compile(r"^%s(?:\)\s*|\.\s+|\s+)" % _OPT_LETTERS[i])
            for i in range(len(opts))]
    if not all(isinstance(o, str) and pats[i].match(o)
               for i, o in enumerate(opts)):
        return opts
    new = [pats[i].sub("", o, count=1) for i, o in enumerate(opts)]
    return new if all(x.strip() for x in new) else opts


def strip_prefixes(parts: list) -> list:
    """Bo'limlar nusxasi — savol raqami va variant harfi takrorlanmasin."""
    out = []
    for p in parts or []:
        qs = []
        for q in p.get("questions") or []:
            q2 = dict(q)
            if "q" in q2:
                q2["q"] = strip_q_prefix(q2.get("q"))
            if q2.get("options"):
                q2["options"] = strip_opt_prefixes(list(q2["options"]))
            qs.append(q2)
        out.append({**p, "questions": qs})
    return out


def _clean_image(v, where: str):
    """Savol rasmi: yuklangan (data:image/…) yoki loyihadagi statik fayl
    (/exam-img/…). Boshqa manzilga ruxsat yo'q — begona sayt rasmi
    o'quvchi sahifasiga tushmasin."""
    v = str(v or "").strip()
    if not v:
        return None
    if v.startswith("/exam-img/") and ".." not in v:
        return v
    if v.startswith("data:image/") and len(v) <= IMAGE_MAX_CHARS:
        return v
    raise HTTPException(400, f"{where}: rasm noto'g'ri yoki juda katta")


def clean_parts(parts) -> list:
    """Test bazasidan kelgan bo'limlarni tekshiradi va savollarni
    1 dan boshlab raqamlaydi. Xato bo'lsa 400."""
    if not isinstance(parts, list) or not parts:
        raise HTTPException(400, "Kamida bitta bo'lim bo'lishi kerak")
    out, n, seen = [], 0, set()
    for pi, p in enumerate(parts):
        if not isinstance(p, dict):
            raise HTTPException(400, "Bo'lim noto'g'ri")
        qs = []
        for q in p.get("questions") or []:
            n += 1
            typ = q.get("type") or "choice"
            text = strip_q_prefix(str(q.get("q") or "").strip()).strip()
            qid = str(q.get("id") or "").strip() or f"q{n}"
            while qid in seen:
                qid = f"{qid}_{n}"
            seen.add(qid)
            item = {"id": qid, "n": n, "type": typ, "q": text}
            # MAVZU (2026-09-26, #177): "Grammar · Present simple" kabi —
            # keyin o'quvchi/guruh/ustoz kesimida qaysi mavzuda ko'p xato
            # qilingani chiqadi. Bo'sh bo'lsa yozilmaydi.
            topic = str(q.get("topic") or "").strip()[:80]
            if topic:
                item["topic"] = topic
            img = _clean_image(q.get("image"), f"{n}-savol")
            if img:
                item["image"] = img
            if typ == "choice":
                opts = strip_opt_prefixes(
                    [str(o).strip() for o in (q.get("options") or [])
                     if str(o).strip()])
                if len(opts) < 2:
                    raise HTTPException(
                        400, f"{n}-savol: kamida 2 ta variant kerak")
                a = q.get("answer")
                if not isinstance(a, int) or not (0 <= a < len(opts)):
                    raise HTTPException(
                        400, f"{n}-savol: to'g'ri variant belgilanmagan")
                item["options"] = opts
                item["answer"] = a
            elif typ == "text":
                ans = q.get("answer")
                if isinstance(ans, str):
                    ans = [x for x in re.split(r"[/;\n]", ans)]
                ans = [str(x).strip() for x in (ans or []) if str(x).strip()]
                if not ans:
                    raise HTTPException(
                        400, f"{n}-savol: to'g'ri javob yozilmagan")
                item["answer"] = ans
            elif typ == "multi":
                # KO'P JAVOBLI (2026-09-26, IELTS mock): "Choose TWO
                # letters, A-E" — o'quvchi bir nechta variantni belgilaydi,
                # hammasi to'g'ri bo'lsagina 1 ball beriladi.
                opts = strip_opt_prefixes(
                    [str(o).strip() for o in (q.get("options") or [])
                     if str(o).strip()])
                if len(opts) < 3:
                    raise HTTPException(
                        400, f"{n}-savol: kamida 3 ta variant kerak")
                a = q.get("answer")
                if not isinstance(a, list):
                    raise HTTPException(
                        400, f"{n}-savol: javob ro'yxat bo'lishi kerak")
                try:
                    a = sorted({int(x) for x in a})
                except (TypeError, ValueError):
                    raise HTTPException(400, f"{n}-savol: javob noto'g'ri")
                if len(a) < 2 or any(not (0 <= i < len(opts)) for i in a):
                    raise HTTPException(
                        400, f"{n}-savol: kamida 2 ta to'g'ri variant kerak")
                item["options"] = opts
                item["answer"] = a
                item["pick"] = len(a)
            elif typ == "essay":
                # QOG'OZDA BAHOLANADI (2026-09-26, IELTS mock Writing):
                # o'quvchi kompyuterda matn yozadi, avtomat tekshirilmaydi —
                # examiner o'qib qog'oz balini qo'yadi. Maksimal ballga
                # ham, foizga ham kirmaydi.
                item["answer"] = []
                item["min_words"] = max(0, int(q.get("min_words") or 0))
            else:
                raise HTTPException(400, f"{n}-savol: noma'lum tur")
            qs.append(item)
        out.append({
            "title": str(p.get("title") or f"Part {pi + 1}").strip(),
            "instructions": str(p.get("instructions") or "").strip(),
            "passage": str(p.get("passage") or "").strip(),
            "audio_url": (str(p.get("audio_url") or "").strip() or None),
            # Bo'lim rasmi — masalan A–G kasblar jadvali (2026-09-18)
            "image": _clean_image(p.get("image"), p.get("title") or "Bo'lim"),
            # KO'NIKMA (2026-09-26, mock bazasi): "ielts_listening",
            # "ielts_reading", "cefr_listening", "writing" ... — xom
            # ballni qaysi jadval bo'yicha bandga o'girishni shu
            # belgilaydi (mock_band). Bo'lim nomiga tayanib bo'lmaydi:
            # IELTS Listening bo'limlari ham shunchaki "Part 1" deyiladi.
            "skill": (str(p.get("skill") or "").strip().lower()[:40] or None),
            # LISTENING SKRIPTI (2026-09-26, variantlar): audio yo'q
            # variantlarda examiner o'qib beradigan matn. Faqat
            # examinerga — public_parts'ga tushmaydi.
            "script": str(p.get("script") or "").strip()[:6000],
            "questions": qs,
        })
    if n == 0:
        raise HTTPException(400, "Kamida bitta savol bo'lishi kerak")
    return out


def public_parts(parts: list) -> list:
    """O'quvchiga boradigan nusxa — to'g'ri javoblarsiz. Prefikslar shu
    yerda ham tozalanadi: tuzatishdan oldin ochilgan linklarning
    nusxasida ular hali saqlangan."""
    out = []
    for p in strip_prefixes(parts):
        out.append({
            **{k: p.get(k) for k in ("title", "instructions", "passage",
                                     "audio_url", "image")},
            "questions": [{k: q.get(k) for k in ("id", "n", "type", "q",
                                                 "options", "image",
                                                 "pick", "min_words")}
                          for q in p.get("questions") or []],
        })
    return out


_NO_SHUFFLE_OPTS = {"true", "false", "not given", "yes", "no"}


def _is_listening(p: dict, o: dict) -> bool:
    """Tinglash bo'limimi (2026-10-21, Jahongir: "listening savol ketma
    ketligi bir xil bo'lsin variantlari xar xil bo'lsin hammada").
    Bazadagi listening bo'limlarining ko'pida audio ham, skript ham yo'q
    — audioni examiner sinfda qo'yadi. Shuning uchun bo'lim nomi /
    ko'nikma / ko'rsatmasidan ham aniqlanadi."""
    if p.get("audio_url") or o.get("script") or o.get("audio_url"):
        return True
    t = " ".join(str(x.get(k) or "") for x in (p, o)
                 for k in ("skill", "title", "instructions")).lower()
    return "listening" in t or "tinglash" in t or "tinglang" in t


def shuffle_for(pub: list, orig: list, seed: str | None) -> list:
    """HAR O'QUVCHIGA ARALASH (2026-10-03, Jahongir: "guruhda hammaga
    bir xil test chiqadi ... aralashtirib ber").

    Seed — o'quvchining topshiriq kaliti: qayta kirsa ham, boshqa
    telefondan kirsa ham tartib O'SHA-O'SHA. Javob ASL raqamda
    saqlanadi (variant uchun "opt" — asl indekslar), shuning uchun
    baholash va examiner ko'rinishi o'zgarmaydi.

    Savollar tartibi faqat matn/audio/rasmga bog'lanmagan bo'limda
    aralashadi (o'qish va tinglashda savollar matn ketma-ketligida
    turadi). Variantlar: kamida 3 ta va harf (A, B..) yoki True/False
    bo'lmasa."""
    import random
    if not seed:
        return pub
    rnd = random.Random(seed)
    out = []
    for i, p in enumerate(pub):
        o = orig[i] if i < len(orig) else {}
        qs = [dict(q) for q in p.get("questions") or []]
        # Tinglashda savollar audio ketma-ketligida — hammada bir xil
        # tartib; faqat javob variantlari har o'quvchida boshqacha
        tied = bool(p.get("passage") or p.get("image")
                    or _is_listening(p, o))
        if not tied and len(qs) > 1:
            nums = [q.get("n") for q in qs]
            rnd.shuffle(qs)
            for q, n in zip(qs, nums):
                q["n"] = n
        for q in qs:
            opts = q.get("options") or []
            if (q.get("type") in ("choice", "multi") and len(opts) >= 3
                    and not q.get("image")
                    and all(len(str(x).strip()) > 2 for x in opts)
                    and not ({str(x).strip().lower() for x in opts}
                             & _NO_SHUFFLE_OPTS)):
                idx = list(range(len(opts)))
                rnd.shuffle(idx)
                q["options"] = [opts[j] for j in idx]
                q["opt"] = idx
        out.append({**p, "questions": qs})
    return out


def grade(parts: list, answers: dict):
    """(ball, maksimal, tafsilot). Har savol 1 ball."""
    score, total, detail = 0, 0, []
    for q in _questions(parts):
        given = answers.get(q["id"])
        typ = q["type"]
        if typ == "essay":
            # Avtomat tekshirilmaydi — examiner qog'oz balini qo'yadi.
            detail.append({"id": q["id"], "n": q["n"], "ok": None,
                           "given": None if given is None
                           else str(given)[:ESSAY_MAX_CHARS]})
            continue
        total += 1
        if typ == "choice":
            try:
                ok = given is not None and int(given) == int(q["answer"])
            except (TypeError, ValueError):
                ok = False
        elif typ == "multi":
            try:
                g = sorted({int(x) for x in (given or [])})
            except (TypeError, ValueError):
                g = []
            ok = bool(g) and g == sorted(q["answer"])
            given = ",".join(str(i) for i in g) if g else None
        else:
            g = _norm(given)
            ok = bool(g) and any(g == _norm(a) for a in q["answer"])
        score += 1 if ok else 0
        detail.append({"id": q["id"], "n": q["n"], "ok": ok,
                       "given": None if given is None else str(given)[:200]})
    return float(score), float(total), detail


def _system_user():
    return SimpleNamespace(id=None, role="system", full_name="Online test")


def _roster(db: Session, group_id: int) -> list:
    return [s for s in _group_students(db, group_id)
            if (s.status or "active") in ("active", "trial", "frozen")] \
        or list(_group_students(db, group_id))


def _mark_for(exam: models.Exam, online: models.ExamOnline,
              sub: models.ExamSubmission):
    """Bitta topshiriq uchun guruh testiga yoziladigan baho.

    MOCK = band (0-9), ball emas — exams._apply_exam_marks mock uchun
    aynan band talab qiladi. IELTS Listening/Reading xom bali rasmiy
    jadval bo'yicha bandga o'giriladi (mock_band). CEFR Multilevel'da
    rasmiy o'tkazish jadvali yo'q (qo'llanmalar mytests.uz ga
    yo'naltiradi), shuning uchun TAXMINIY band yozilmaydi: None
    qaytadi va darajani examiner xom balga qarab o'zi qo'yadi.
    Writing/Speaking mocklarida avtomat savol yo'q — bandni examiner
    qog'oz bali sifatida kiritadi.

    Ikki joydan chaqiriladi: topshiriq o'quvchiga joylashganda
    (_write_result) va examiner hammasini tasdiqlaganda
    (publish_online). Ilgari ikkinchisi mockni hisobga olmay
    to'g'ridan-to'g'ri ball yozardi va mock tasdiqlanmasdan 400
    qaytarardi.
    """
    if (exam.kind or "") == "mock":
        parts = _load(online.parts)
        b = mock_band(parts, sub.online_score, sub.online_max)
        if b is None:
            # CEFR Multilevel: natija 0-75 REYTING, guruh jadvalidagi
            # mock ustuni esa 0-9 band. Ikkisi bir xil shkala emas,
            # shuning uchun avtomat hech narsa yozilmaydi — examiner
            # xom ballni va reytingni ko'rib darajani o'zi qo'yadi
            # (2026-09-26, rasmiy reyting jadvali shablon ichida).
            if _mock_section(parts).startswith("cefr"):
                return None
            if (sub.online_max or 0) > 0:
                return None
            b = sub.paper_score or 0
        return schemas.ExamScoreMark(student_id=sub.student_id,
                                     band=round(float(b) * 2) / 2,
                                     absent=False)
    return schemas.ExamScoreMark(
        student_id=sub.student_id,
        score=(sub.online_score or 0) + (sub.paper_score or 0), absent=False)


def _write_result(db: Session, exam: models.Exam, online: models.ExamOnline,
                  sub: models.ExamSubmission, user) -> None:
    """Joylashtirilgan topshiriqni guruh testining natijasiga yozadi.
    Qog'oz qismi bor, lekin hali kiritilmagan bo'lsa — kutadi."""
    if not sub.student_id or sub.status != "placed":
        return
    if not online.published_at:
        return          # examiner hali tasdiqlamagan
    if (online.paper_max or 0) > 0 and sub.paper_score is None:
        return
    mark = _mark_for(exam, online, sub)
    if mark is None:
        return
    _exams._apply_exam_marks(db, exam, schemas.ExamScoreBulk(marks=[mark]),
                             user)


def _place(db: Session, exam, online, sub, student_id: int, user) -> None:
    """Topshiriqni o'quvchiga biriktiradi. Shu o'quvchining avvalgi
    joylashgan topshirig'i "replaced" bo'ladi."""
    for old in (db.query(models.ExamSubmission)
                .filter(models.ExamSubmission.exam_id == exam.id,
                        models.ExamSubmission.student_id == student_id,
                        models.ExamSubmission.status == "placed",
                        models.ExamSubmission.id != sub.id).all()):
        old.status = "replaced"
        if sub.paper_score is None:
            sub.paper_score = old.paper_score
            # Kim qo'ygani ham (AI bahosi bo'lsa — yangi urinishning
            # AI bahosi kelganda almashadi, examinerniki — yo'q)
            sub.paper_by = old.paper_by
    sub.student_id = student_id
    sub.status = "placed"
    sub.placed_by = user.full_name
    sub.placed_at = datetime.utcnow()
    db.commit()
    _write_result(db, exam, online, sub, user)


def bank_max(db: Session, group, kind: str, unit_no=None):
    """Test bazasidagi mos testning maksimal bali (savollar soni +
    qog'oz qismi). Guruh darajasi, tur va unit bo'yicha; topilmasa None.
    (2026-09-18, Jahongir: "xamma biriktirilgan test unitlarini
    maksimal ballini test soniga qarab o'zing belgilab chiq")"""
    if kind not in ("unit", "mid", "end", "mock") or not group             or not group.level:
        return None
    q = db.query(models.ExamTemplate).filter(
        models.ExamTemplate.is_active == 1,
        models.ExamTemplate.level == group.level,
        models.ExamTemplate.kind == kind)
    if kind == "unit":
        if not unit_no:
            return None
        q = q.filter(models.ExamTemplate.unit_no == unit_no)
    # Guruh faniga mos shablon (english / math …, 2026-09-26)
    t = next((x for x in q.order_by(models.ExamTemplate.id).all()
              if _subj(x) == _subj(group)), None)
    if not t:
        return None
    if kind == "mock":
        # Mock natijasi bandda yoziladi: Listening/Reading xom bali
        # _write_result'da rasmiy jadval bo'yicha bandga o'giriladi,
        # Writing/Speaking bandini examiner qog'ozdan kiritadi.
        return MOCK_BAND_MAX
    # Essay (Writing) savollari avtomat tekshirilmaydi — maksimal ballga
    # kirmaydi, ular paper_max orqali hisoblanadi.
    n = sum(1 for q in _questions(_load(t.parts))
            if q.get("type") != "essay")
    if kind in ("mid", "end") and _subj(t) == "english":
        # Qog'oz qismi (Writing/Speaking) bazada belgilanmagan bo'lsa
        # ham jami 100 — faqat ingliz tilida; matematikada qog'oz yo'q
        return max(float(n), MID_END_TOTAL)
    return float(n) + float(t.paper_max or 0)


# ----------------------------------------------------- IELTS mock -> band
# Rasmiy Cambridge xom ball -> band jadvallari (40 savollik bo'lim).
# Listening va Academic Reading chegaralari boshqa-boshqa.
_BAND_LISTENING = [(39, 9.0), (37, 8.5), (35, 8.0), (32, 7.5), (30, 7.0),
                   (26, 6.5), (23, 6.0), (18, 5.5), (16, 5.0), (13, 4.5),
                   (11, 4.0), (8, 3.5), (6, 3.0), (4, 2.5)]
_BAND_READING = [(39, 9.0), (37, 8.5), (35, 8.0), (33, 7.5), (30, 7.0),
                 (27, 6.5), (23, 6.0), (19, 5.5), (15, 5.0), (13, 4.5),
                 (10, 4.0), (8, 3.5), (6, 3.0), (4, 2.5)]


def _mock_section(parts: list) -> str:
    """Qaysi ko'nikma va qaysi imtihon: "ielts_listening",
    "ielts_reading", "cefr_listening", ... Avval bo'limdagi aniq
    "skill" maydoni o'qiladi; u yo'q bo'lsa (eski yozuvlar) bo'lim
    nomiga qaraladi — ilgari faqat IELTS bor edi."""
    for p in parts:
        sk = str(p.get("skill") or "").strip().lower()
        if sk:
            return sk
    t = " ".join(str(p.get("title") or "") for p in parts).lower()
    if "listening" in t:
        return "ielts_listening"
    if "reading" in t:
        return "ielts_reading"
    return ""


def mock_band(parts: list, score, total) -> Optional[float]:
    """Xom ballni IELTS bandiga o'giradi (mock testlar uchun).
    Bo'lim Listening/Reading bo'lmasa yoki savol bo'lmasa — None."""
    try:
        score, total = float(score or 0), float(total or 0)
    except (TypeError, ValueError):
        return None
    if total <= 0:
        return None
    sec = _mock_section(parts)
    if sec not in ("ielts_listening", "ielts_reading"):
        # CEFR Multilevel: qo'llanmalarda xom balldan darajaga rasmiy
        # o'tkazish jadvali yo'q — taxminiy band o'ylab topilmaydi.
        return None
    raw = int(round(score / total * 40))
    table = _BAND_LISTENING if sec == "ielts_listening" else _BAND_READING
    for low, band in table:
        if raw >= low:
            return band
    return 2.0 if raw >= 3 else 1.0


def _exam_open_for_results(exam: models.Exam) -> bool:
    return (exam.status or "done") in ("approved", "done")


# ------------------------------------------------------------ test bazasi
class TemplateIn(BaseModel):
    level: Optional[str] = None
    kind: str = "unit"
    unit_no: Optional[int] = None
    title: str
    parts: list
    paper_max: float = 0
    is_active: bool = True
    variant: Optional[str] = None      # A/B/C/D/E (bo'sh = A)
    subject: Optional[str] = None      # english (bo'sh) / math / …
    # XODIMLAR MOCK MASHQI (2026-09-27, Jahongir: "ustozlarga ular ham
    # experience qilib xatolarni aytadida"). Seed har mock faylini 3
    # darajaga yozadi — tuzatish qolgan daraja nusxalariga ham tushsin
    # (faqat tahrirdan oldin AYNAN bir xil bo'lganlariga) va shu
    # tuzatish bilan yopilgan xodim xabarlari "tuzatildi" bo'lsin.
    sync_siblings: bool = False
    resolve_issue_ids: Optional[List[int]] = None


def _clean_subject(v) -> Optional[str]:
    v = (str(v or "").strip().lower() or "english")
    if v not in roles.SUBJECT_LABELS:
        raise HTTPException(400, "Noto'g'ri fan")
    return None if v == "english" else v


def _subj(x) -> str:
    """Shablon yoki guruh fani (NULL = english)."""
    return (getattr(x, "subject", None) or "english")


def _clean_variant(v) -> str:
    # A-Z (2026-09-27): mock bazasida CEFR Speaking I-J va Reading
    # Challenge I-Q variantlari bor — A-H cheklovi ularni tahrirlab
    # saqlashga yo'l qo'ymasdi (examiner "400" olardi).
    v = (str(v or "A").strip().upper() or "A")[:1]
    if not ("A" <= v <= "Z"):
        raise HTTPException(400, "Variant lotin harfi (A–Z) bo'lishi kerak")
    return v


def _tpl_summary(t: models.ExamTemplate) -> dict:
    parts = _load(t.parts)
    return {
        "id": t.id, "level": t.level, "kind": t.kind, "unit_no": t.unit_no,
        "variant": (t.variant or "A"), "subject": _subj(t),
        "title": t.title, "paper_max": t.paper_max or 0,
        "q_count": sum(1 for _ in _questions(parts)),
        "is_active": bool(t.is_active),
        "updated_at": t.updated_at.isoformat() if t.updated_at else None,
    }


def _validate_tpl(p: TemplateIn):
    if p.kind not in ("unit", "mid", "end", "mock"):
        raise HTTPException(400, "Online test faqat Unit, Mid-course, "
                                 "End of course va Mock uchun")
    if p.kind == "unit" and not (p.unit_no and 1 <= p.unit_no <= roles.UNIT_COUNT):
        raise HTTPException(400, f"Unit raqami 1-{roles.UNIT_COUNT} oralig'ida")
    if p.level and p.level not in roles.ALL_LEVELS:
        raise HTTPException(400, "Noto'g'ri daraja")
    if p.paper_max < 0 or p.paper_max > 500:
        raise HTTPException(400, "Writing/Speaking bali noto'g'ri")
    if not p.title.strip():
        raise HTTPException(400, "Nomini yozing")


# ---------------------------------------------------- mock bazalari
# Jahongir (2026-09-27): "mock testlarni imtihon bo'limiga o'tkazasan
# IELTS va CEFR nikini". Bir joyda: qaysi bazada nechta variant bor,
# nechta savol avtomat tekshiriladi va NATIJA QANDAY CHIQADI —
# kamchiliklar yashirin qolmasin.
_BANK_LABELS = {
    "ielts": "IELTS Academic",
    "cefr": "CEFR Multilevel",
    "challenge25": "Reading Challenge (25 kun)",
}
# Mock imtihon EMAS — mashq to'plami: band qo'yilmaydi, bo'limlari
# to'liq imtihon tuzilishini bermaydi.
_PRACTICE_BANKS = {"challenge25"}
_BANK_ORDER = {"ielts": 0, "cefr": 1}
# Bo'limlar imtihondagi tartibda: Listening, Reading, Writing, Speaking
# (2026-09-28, Jahongir: "Speakingdan oldin Writing tursin"). Ilgari
# alifbo bo'yicha edi — Speaking Writing'dan oldin chiqardi.
_SEC_ORDER = {"listening": 0, "reading": 1, "writing": 2, "speaking": 3}

# Har bo'lim QANCHA VAQT oladi — faqat ko'rsatish uchun (2026-09-28,
# Jahongir: "qancha vaqt olishi kerak"). L/R/W — mock_practice.DURATION
# bilan bir xil (sinov taymeri o'sha yerda); Speaking yuzma-yuz:
# IELTS rasmiy 11-14 daqiqa, CEFR shablonida "taxminan 15 daqiqa".
_SECTION_TIME = {
    ("ielts", "listening"): "30 daqiqa",
    ("ielts", "reading"): "60 daqiqa",
    ("ielts", "writing"): "60 daqiqa",
    ("ielts", "speaking"): "11–14 daqiqa",
    ("cefr", "listening"): "35 daqiqa",
    ("cefr", "reading"): "60 daqiqa",
    ("cefr", "writing"): "60 daqiqa",
    ("cefr", "speaking"): "~15 daqiqa",
}

# Har bo'lim qanday baholanadi. "auto" — tizim o'zi chiqaradi.
# Matnlar qisqa, xom ball raqamlarisiz (2026-09-28, Jahongir: "xom
# ballar degan narsalar kerak emas") — hisob-kitob kalkulyatorda.
_GRADING = {
    ("ielts", "listening"): (
        True, "Band (0–9) avtomat chiqadi va guruh jadvaliga tushadi."),
    ("ielts", "reading"): (
        True, "Band (0–9) avtomat chiqadi va guruh jadvaliga tushadi."),
    # Writing — AI baholaydi (writing_ai.py, 2026-09-28): har topshiriq
    # 4 mezon bo'yicha, band avtomat; examiner xohlasa o'zgartiradi.
    ("ielts", "writing"): (
        True, "AI har topshiriqni 4 mezon bo'yicha baholaydi, band "
              "avtomat chiqadi. Examiner xohlasa o'zgartiradi."),
    ("ielts", "speaking"): (
        False, "Yuzma-yuz. Examiner 4 mezonga baho qo'yadi, bandni "
               "kalkulyator chiqaradi."),
    ("cefr", "listening"): (
        False, "Tizim taxminiy darajani ko'rsatadi, yakuniy ballni "
               "examiner tasdiqlaydi."),
    ("cefr", "reading"): (
        False, "Tizim taxminiy darajani ko'rsatadi, yakuniy ballni "
               "examiner tasdiqlaydi."),
    ("cefr", "writing"): (
        True, "AI har topshiriqni rasmiy shkala bo'yicha baholaydi, "
              "ball (0–75) va daraja examiner panelida avtomat chiqadi. "
              "Examiner xohlasa o'zgartiradi."),
    ("cefr", "speaking"): (
        False, "Yuzma-yuz. Examiner baho qo'yadi, ball va darajani "
               "kalkulyator chiqaradi."),
    ("challenge25", "reading"): (
        False, "Mashq uchun: band qo'yilmaydi, javoblar avtomat "
               "tekshiriladi."),
}


class MarkIn(BaseModel):
    skill: str
    # ielts_*, cefr_speaking va cefr_writing (yangi, 3 topshiriq) uchun:
    # mezon/element/topshiriq ballari
    marks: Optional[list] = None
    # cefr_writing_old (eski 2 topshiriqli format) uchun:
    # [{"marks": [4 ta], "words": N}, ...]
    tasks: Optional[list] = None


@router.get("/api/mock-schemes")
def mock_schemes(user=Depends(require_role(*RESULT_ROLES))):
    """Baholash sxemalari: qaysi mezonlar, har biri necha balldan.
    Examiner formasi shundan quriladi."""
    import mock_marking
    return mock_marking.SCHEMES


@router.post("/api/mock-score")
def mock_score(payload: MarkIn, user=Depends(require_role(*RESULT_ROLES))):
    """MEZON BALLARIDAN YAKUNIY BALL (2026-09-27, Jahongir:
    "Examinerga iloji boricha kam ish qoldir").

    Examiner har mezonga baho qo'yadi, yakuniy ballni rasmiy jadval
    bo'yicha tizim hisoblaydi — qo'lda hisoblash va xato qilish
    o'rniga."""
    import mock_marking
    res = mock_marking.compute(payload.skill,
                               {"marks": payload.marks,
                                "tasks": payload.tasks})
    if res is None:
        raise HTTPException(400, "Baholash sxemasi yoki ballar noto'g'ri")
    return res


@router.get("/api/mock-banks")
def mock_banks(db: Session = Depends(get_db),
               user=Depends(require_role(*RESULT_ROLES))):
    """Mock bazalarining qisqacha ko'rinishi: qaysi imtihon, qaysi
    bo'lim, nechta variant, nechta avtomat savol va natija qanday
    chiqadi."""
    rows = (db.query(models.ExamTemplate)
            .filter(models.ExamTemplate.kind == "mock",
                    models.ExamTemplate.is_active == 1).all())
    banks: dict = {}
    for t in rows:
        parts = _load(t.parts)
        skill = _mock_section(parts)
        bank, _, sec = skill.partition("_")
        if not sec:
            bank, sec = "ielts", skill or "?"
        b = banks.setdefault(bank, {})
        s = b.setdefault(sec, {"variants": set(), "levels": set(),
                               "qs": [], "paper_max": set(), "tasks": []})
        s["variants"].add(t.variant or "A")
        if t.level:
            s["levels"].add(t.level)
        s["paper_max"].add(float(t.paper_max or 0))
        n = sum(1 for q in _questions(parts) if q.get("type") != "essay")
        s["qs"].append(n)
        # Writing/Speaking: nechta topshiriq (insho / og'zaki qism)
        s["tasks"].append(sum(1 for q in _questions(parts)
                              if q.get("type") == "essay"))
    # BANKLAR TARTIBI va MASHQ AJRATILISHI (2026-09-27).
    #
    # Jahongir: "challenge 25 nima qilyabdi bu mock emasku shunchaki
    # mashq edi". To'g'ri — Challenge 25 bu IELTS Reading savollari
    # to'plami, mock imtihon emas va band qo'yilmaydi. Shuning uchun
    # u "practice" deb belgilanadi va ro'yxatda mocklardan keyin,
    # alohida ko'rsatiladi. Bazadan o'chirilmaydi: ustozlar uni
    # avvalgidek test qilib bera oladi.
    out = []
    for bank in sorted(banks, key=lambda b: (b in _PRACTICE_BANKS,
                                             _BANK_ORDER.get(b, 9), b)):
        secs = []
        for sec in sorted(banks[bank],
                          key=lambda x: (_SEC_ORDER.get(x, 9), x)):
            s = banks[bank][sec]
            auto, note = _GRADING.get((bank, sec), (False, ""))
            qs = s["qs"] or [0]
            secs.append({
                "section": sec,
                "variants": sorted(s["variants"]),
                "levels": sorted(s["levels"]),
                # To'plamlarda savol soni har xil bo'lishi mumkin
                # (challenge25) — shuning uchun oralig'i ham beriladi
                "questions": min(qs),
                "questions_max": max(qs),
                "tasks": max(s["tasks"] or [0]),
                "paper_max": max(s["paper_max"]) if s["paper_max"] else 0,
                "time": _SECTION_TIME.get((bank, sec)),
                "auto": auto,
                "grading": note,
            })
        out.append({"bank": bank,
                    "label": _BANK_LABELS.get(bank, bank),
                    "practice": bank in _PRACTICE_BANKS,
                    "sections": secs})
    return out


@router.get("/api/exam-templates")
def list_templates(level: Optional[str] = None, kind: Optional[str] = None,
                   hidden: bool = False,
                   db: Session = Depends(get_db),
                   user=Depends(require_role(*RESULT_ROLES))):
    q = db.query(models.ExamTemplate)
    if level:
        q = q.filter(models.ExamTemplate.level == level)
    if kind:
        q = q.filter(models.ExamTemplate.kind == kind)
    if not hidden:
        # Tizim "(dublikat)" deb yashirgan MOCK nusxalari ro'yxatni
        # to'ldirib yubormasin (2026-09-27: mock seedi bilan dublikat
        # qoidasi bir-birini aylantirib, har startda 69 tadan nusxa
        # qoldirgan). Unit/Mid/End va examiner yashirganlari (nomida
        # "(dublikat)" yo'q) avvalgidek ko'rinadi; hammasini ko'rish —
        # ?hidden=true (Test bazasidagi "yashirin nusxalar" belgisi).
        from sqlalchemy import and_, func, not_
        q = q.filter(not_(and_(
            models.ExamTemplate.kind == "mock",
            models.ExamTemplate.is_active != 1,
            func.coalesce(models.ExamTemplate.title, "").like("%(dublikat)"))))
    rows = q.order_by(models.ExamTemplate.level, models.ExamTemplate.kind,
                      models.ExamTemplate.unit_no,
                      models.ExamTemplate.variant).all()
    return [_tpl_summary(t) for t in rows]


@router.get("/api/exam-templates/topics")
def template_topics(db: Session = Depends(get_db),
                    user=Depends(require_role(*roles.EXAM_ACCESS,
                                              *roles.EXAM_EDIT))):
    """Bazadagi barcha mavzular (tahrir oynasidagi tanlagich uchun):
    boshlang'ich ro'yxat + examinerlar qo'shganlari, nechta savolda
    ishlatilgani bilan (#177)."""
    counts: dict = {}
    for name in _bank_topic_names():
        counts.setdefault(name, 0)
    for (parts_txt,) in db.query(models.ExamTemplate.parts).all():
        for q in _questions(_load(parts_txt)):
            t = q.get("topic")
            if t:
                counts[t] = counts.get(t, 0) + 1
    return [{"topic": k, "count": v}
            for k, v in sorted(counts.items(), key=lambda x: (x[0].split(" · ")[0], x[0]))]


@router.get("/api/exam-templates/{tid}")
def get_template(tid: int, db: Session = Depends(get_db),
                 user=Depends(require_role(*roles.EXAM_ACCESS,
                                           *roles.EXAM_EDIT))):
    t = db.query(models.ExamTemplate).get(tid)
    if not t:
        raise HTTPException(404, "Test topilmadi")
    return {**_tpl_summary(t), "parts": _load(t.parts)}


@router.post("/api/exam-templates")
def create_template(payload: TemplateIn, db: Session = Depends(get_db),
                    user=Depends(require_role(*roles.EXAM_EDIT))):
    _validate_tpl(payload)
    t = models.ExamTemplate(
        level=payload.level or None, kind=payload.kind,
        unit_no=payload.unit_no if payload.kind == "unit" else None,
        title=payload.title.strip(),
        parts=json.dumps(clean_parts(payload.parts), ensure_ascii=False),
        paper_max=payload.paper_max, is_active=1 if payload.is_active else 0,
        variant=_clean_variant(payload.variant),
        subject=_clean_subject(payload.subject),
        created_by=user.full_name)
    db.add(t)
    db.commit()
    audit.log(db, user, entity="exam_template", action="create",
              entity_id=t.id, entity_label=t.title, commit=True)
    return {**_tpl_summary(t), "parts": _load(t.parts)}


@router.put("/api/exam-templates/{tid}")
def update_template(tid: int, payload: TemplateIn,
                    db: Session = Depends(get_db),
                    user=Depends(require_role(*roles.EXAM_EDIT))):
    t = db.query(models.ExamTemplate).get(tid)
    if not t:
        raise HTTPException(404, "Test topilmadi")
    _validate_tpl(payload)
    # Tahrirdan OLDINGI holat — daraja nusxalari shu bilan solishtiriladi
    old_parts = _load(t.parts)
    old_title, old_variant, old_subj = t.title, (t.variant or "A"), _subj(t)
    t.level = payload.level or None
    t.kind = payload.kind
    t.unit_no = payload.unit_no if payload.kind == "unit" else None
    t.title = payload.title.strip()
    t.parts = json.dumps(clean_parts(payload.parts), ensure_ascii=False)
    t.paper_max = payload.paper_max
    t.is_active = 1 if payload.is_active else 0
    if payload.variant is not None:
        t.variant = _clean_variant(payload.variant)
    if payload.subject is not None:
        t.subject = _clean_subject(payload.subject)
    db.commit()
    audit.log(db, user, entity="exam_template", action="update",
              entity_id=t.id, entity_label=t.title, commit=True)
    synced, diverged = [], []
    if t.kind == "mock" and payload.sync_siblings:
        # DARAJA NUSXALARI (2026-09-27): seed bitta faylni ielts_intro /
        # foundation / graduation ga alohida qator qilib yozadi. Tuzatish
        # faqat tahrirdan oldin shu qator bilan AYNAN bir xil bo'lgan
        # nusxalarga ko'chiriladi; boshqacha tahrirlangani "diverged"
        # bo'lib qaytadi va tegilmaydi. Yashirin "(dublikat)" qatorlar
        # ham kiradi (canon_title).
        from mock_seed import canon_title
        key = canon_title(old_title)
        new_parts = _load(t.parts)
        for sib in (db.query(models.ExamTemplate)
                    .filter(models.ExamTemplate.kind == "mock",
                            models.ExamTemplate.id != t.id)
                    .order_by(models.ExamTemplate.id).all()):
            if canon_title(sib.title) != key or \
                    (sib.variant or "A") != old_variant or \
                    _subj(sib) != old_subj:
                continue
            sp = _load(sib.parts)
            if sp == new_parts:
                continue
            if sp != old_parts:
                diverged.append(sib)
                continue
            sib.parts = t.parts
            synced.append(sib.id)
            audit.log(db, user, entity="exam_template", action="sync",
                      entity_id=sib.id, entity_label=sib.title,
                      note=f"#{t.id} tahriridan nusxa")
        db.commit()
    resolved = 0
    if payload.resolve_issue_ids:
        now = datetime.utcnow()
        ids = sorted({int(x) for x in payload.resolve_issue_ids})[:500]
        for i in (db.query(models.MockIssue)
                  .filter(models.MockIssue.id.in_(ids),
                          models.MockIssue.status == "open").all()):
            i.status = "fixed"
            i.resolved_by = user.full_name
            i.resolved_at = now
            resolved += 1
        if resolved:
            audit.log(db, user, entity="mock_issue", action="fixed",
                      entity_id=t.id, entity_label=t.title,
                      note=f"shablon tahriri bilan {resolved} ta xabar yopildi")
        db.commit()
    return {**_tpl_summary(t), "parts": _load(t.parts),
            "synced": synced, "diverged": [s.id for s in diverged],
            "diverged_rows": [{"id": s.id, "level": s.level,
                               "variant": s.variant or "A",
                               "is_active": bool(s.is_active)}
                              for s in diverged],
            "resolved": resolved}


@router.delete("/api/exam-templates/{tid}")
def delete_template(tid: int, db: Session = Depends(get_db),
                    user=Depends(require_role(*roles.EXAM_EDIT))):
    t = db.query(models.ExamTemplate).get(tid)
    if not t:
        raise HTTPException(404, "Test topilmadi")
    used = db.query(models.ExamOnline).filter(
        models.ExamOnline.template_id == tid).count()
    if used:
        # Ishlatilgan test o'chirilmaydi — faqat yashiriladi
        t.is_active = 0
    else:
        db.delete(t)
    db.commit()
    audit.log(db, user, entity="exam_template", action="delete",
              entity_id=tid, entity_label=t.title, commit=True)
    return {"ok": True, "hidden": bool(used)}


# ---------------------------------------------------- guruh testining linki
class OnlineIn(BaseModel):
    template_id: int
    paper_max: Optional[float] = None
    # "mix" (odatiy) — har bo'lim shu daraja/tur/unit'ning tasodifiy
    # variantidan; "single" — faqat tanlangan shablon (2026-09-26)
    mode: str = "mix"


def _family(db: Session, t: models.ExamTemplate) -> list:
    """Bir daraja + tur + unit'ning barcha faol variantlari (A, B, …)."""
    q = db.query(models.ExamTemplate).filter(
        models.ExamTemplate.is_active == 1,
        models.ExamTemplate.kind == t.kind,
        models.ExamTemplate.level == t.level)
    if t.kind == "unit":
        q = q.filter(models.ExamTemplate.unit_no == t.unit_no)
    # KO'NIKMA BO'YICHA HAM AJRATILADI (2026-09-26). Aks holda bitta
    # darajadagi hamma mock bitta oila bo'lib qolardi va tasodifan bir
    # xil tuzilishga tushgan boshqa bazaning matni (masalan tashqi
    # "challenge" to'plami) akademiyaning o'z bazasiga aralashib
    # ketishi mumkin edi.
    sk = _tpl_skill(t)
    rows = [x for x in q.all()
            if _subj(x) == _subj(t) and _tpl_skill(x) == sk]
    rows.sort(key=lambda x: (x.variant or "A", x.id))
    return rows


def _tpl_skill(t) -> str:
    """Shablonning ko'nikma belgisi ("ielts_reading", "cefr_listening",
    ...). Eski shablonlarda yo'q — bo'sh satr qaytadi va ular
    o'zaro bir oila bo'lib qolaveradi."""
    try:
        return _mock_section(_load(t.parts))
    except Exception:
        return ""


def _shape(parts: list) -> tuple:
    return tuple(len(p.get("questions") or []) for p in parts)


def mix_parts(base: models.ExamTemplate, family: list, rnd=None) -> tuple:
    """VARIANTLARNI ARALASHTIRISH (2026-09-26, Jahongir: "ustozlar aynan
    testga tayyorlash holatlari kuzatilyabdi").

    Har bo'lim uchun tasodifiy variant tanlanadi (5 variant × 5 bo'lim =
    3 125 kombinatsiya) — ustoz qaysi savollar tushishini oldindan
    bilolmaydi. Faqat TUZILISHI bir xil (bo'lim va savollar soni)
    variantlar aralashadi; boshqacha tuzilganlari chetda qoladi.
    Qaytaradi: (parts, "B,A,D,C,E")."""
    rnd = rnd or random
    base_parts = _load(base.parts)
    shape = _shape(base_parts)
    pool = {}
    for t in family:
        parts = _load(t.parts)
        if _shape(parts) == shape:
            pool[t.variant or "A"] = parts
    if len(pool) <= 1:
        return base_parts, (base.variant or "A")
    letters = sorted(pool)
    out, chosen = [], []
    for i in range(len(base_parts)):
        L = rnd.choice(letters)
        out.append(json.loads(json.dumps(pool[L][i])))
        chosen.append(L)
    # Hech bo'lmaganda bitta bo'lim boshqa variantdan bo'lsin — hammasi
    # tasodifan bir xil chiqib qolmasin (5 bo'limda 1/625 ehtimol)
    if len(set(chosen)) == 1 and len(letters) > 1:
        i = rnd.randrange(len(out))
        alt = rnd.choice([x for x in letters if x != chosen[i]])
        out[i] = json.loads(json.dumps(pool[alt][i]))
        chosen[i] = alt
    return clean_parts(out), ",".join(chosen)


class OnlineToggle(BaseModel):
    is_open: bool


class AssignIn(BaseModel):
    student_id: int


class PaperMark(BaseModel):
    student_id: int
    paper: Optional[float] = None


class PaperBulk(BaseModel):
    marks: List[PaperMark]


def _online_of(db: Session, exam_id: int):
    return db.query(models.ExamOnline).filter(
        models.ExamOnline.exam_id == exam_id).first()


def _answer_sheet(detail: list, qmap: dict) -> list:
    """Examiner uchun javob varag'i (2026-09-18, Jahongir: "ustiga
    bossa javoblari ham ko'rinsin aynan nimada xato qilganini examiner
    isbotlay olsin"). Savol matni va to'g'ri javob link ochilgan
    paytdagi nusxadan olinadi — keyin bazada test tahrirlansa ham
    o'quvchi yechgan savollar ko'rinadi."""
    out = []
    for d in detail:
        q = qmap.get(d.get("id")) or {}
        given = d.get("given")
        opts = q.get("options") or []
        if q.get("type") == "choice":
            try:
                gi = int(given) if given not in (None, "") else None
            except (TypeError, ValueError):
                gi = None
            given_text = (_opt_label(opts, gi)
                          if gi is not None and 0 <= gi < len(opts) else None)
            a = q.get("answer")
            correct = (_opt_label(opts, a)
                       if isinstance(a, int) and 0 <= a < len(opts) else None)
        elif q.get("type") == "multi":
            def _lab(v):
                try:
                    idx = sorted({int(x) for x in str(v or "").split(",")
                                  if str(x).strip() != ""})
                except (TypeError, ValueError):
                    return None
                idx = [i for i in idx if 0 <= i < len(opts)]
                return ", ".join(_opt_label(opts, i) for i in idx) or None
            given_text = _lab(given)
            correct = ", ".join(_opt_label(opts, i)
                                for i in (q.get("answer") or [])
                                if 0 <= i < len(opts)) or None
        elif q.get("type") == "essay":
            given_text = given if given not in (None, "") else None
            correct = None
        else:
            given_text = given if given not in (None, "") else None
            correct = " / ".join(q.get("answer") or [])
        img = q.get("image") or ""
        out.append({**d, "part": q.get("part"), "q": q.get("q") or "",
                    # Statik rasm (manzil) javob varag'ida ham ko'rinadi;
                    # yuklangan (data:) rasm ro'yxatni og'irlashtirmasin
                    "image": img if img.startswith("/exam-img/") else None,
                    "has_image": bool(img),
                    "type": q.get("type"), "given_text": given_text,
                    "correct": correct,
                    # Mavzu — examiner javob varag'ida ko'radi (#177)
                    "topic": q.get("topic") or None})
    return out


def _opt_label(opts: list, i: int) -> str:
    """ "B) is" — variant faqat harfning o'zi bo'lsa (rasmdan tanlash) "B"."""
    letter = "ABCDEFGH"[i]
    return letter if opts[i] == letter else f"{letter}) {opts[i]}"


def _qmap(parts: list) -> dict:
    m = {}
    for p in strip_prefixes(parts):
        for q in p.get("questions") or []:
            m[q["id"]] = {**q, "part": p.get("title")}
    return m


def _cefr_info(parts: list, sub: models.ExamSubmission) -> Optional[dict]:
    """CEFR Multilevel mockida TAXMINIY daraja (2026-09-27).

    Rasmiy hujjatga ko'ra tinglab tushunish va o'qish Rasch metodi
    bilan hisoblanadi — aniq ball savollar kalibrovkasiga va guruh
    statistikasiga bog'liq, shuning uchun qat'iy jadval yo'q. Hujjat
    faqat taxminiy to'g'ri javoblar sonini beradi; examiner shuni
    ko'rib darajani o'zi qo'yadi."""
    sec = _mock_section(parts)
    if sec not in ("cefr_listening", "cefr_reading"):
        return None
    if not (sub.online_max or 0):
        return None
    try:
        from cefr_score import lr_approx
        return lr_approx(sub.online_score or 0, int(sub.online_max))
    except Exception:          # noqa: BLE001
        return None


def _sub_out(s: models.ExamSubmission, names: dict,
             qmap: Optional[dict] = None,
             cefr: Optional[dict] = None) -> dict:
    return {
        "id": s.id, "student_id": s.student_id,
        "student_name": names.get(s.student_id) if s.student_id else None,
        "typed_name": s.typed_name, "status": s.status,
        "online_score": s.online_score, "online_max": s.online_max,
        "paper_score": s.paper_score,
        "submitted_at": s.submitted_at.isoformat() if s.submitted_at else None,
        "placed_by": s.placed_by,
        "away_count": s.away_count or 0,
        "away_sec": s.away_sec or 0,
        "note": s.note,
        "photo": s.photo,
        "detail": _answer_sheet(_load(s.detail), qmap or {}),
        # CEFR mockida taxminiy daraja (boshqa testlarda None)
        "cefr": cefr,
        # Writing AI bahosi (2026-09-28); paper_by — "ai" yoki examiner
        "ai_status": s.ai_status,
        "ai_score": s.ai_score,
        "ai_review": _ai_public(s.ai_review),
        "paper_by": s.paper_by,
    }


def _ai_public(txt) -> Optional[dict]:
    """AI natijasi examiner uchun: mezonlar, izohlar, xato kodi."""
    d = _load_dict(txt)
    if not d:
        return None
    d.pop("started", None)
    d.pop("prev", None)
    return d


@router.get("/api/groups/{group_id}/exam-bank-max")
def exam_bank_max(group_id: int, kind: str, unit_no: Optional[int] = None,
                  db: Session = Depends(get_db),
                  user=Depends(require_role(*roles.TEACHING_ACCESS))):
    """Yangi test formasi uchun: shu guruh darajasida mos test bazada
    bo'lsa — maksimal ball (savollar soni)."""
    group = _get_group_in_scope(db, group_id, user)
    return {"max_score": bank_max(db, group, kind, unit_no)}


@router.get("/api/exams/{exam_id}/online")
def get_online(exam_id: int, db: Session = Depends(get_db),
               user=Depends(require_role(*roles.TEACHING_ACCESS))):
    exam = _exams._exam_in_scope(db, exam_id, user)
    group = db.query(models.Group).get(exam.group_id)
    o = _online_of(db, exam.id)
    if o:
        finalize_expired(db, o, exam)
    subs = (db.query(models.ExamSubmission)
            .options(undefer(models.ExamSubmission.photo))
            .filter(models.ExamSubmission.exam_id == exam.id)
            .order_by(models.ExamSubmission.submitted_at).all())
    published = bool(o and o.published_at)
    can_see = (published or user.role in PUBLISH_ROLES
               or user.role in RESULT_ROLES)
    if not can_see:
        subs = []       # ustoz: examiner tasdiqlaguncha natija ko'rinmaydi
    ids = {s.student_id for s in subs if s.student_id}
    names = {st.id: st.full_name for st in db.query(models.Student)
             .filter(models.Student.id.in_(ids)).all()} if ids else {}
    tq = db.query(models.ExamTemplate).filter(
        models.ExamTemplate.is_active == 1,
        models.ExamTemplate.kind == exam.kind)
    if exam.kind == "unit" and exam.unit_no:
        tq = tq.filter(models.ExamTemplate.unit_no == exam.unit_no)
    # Faqat guruh faniga mos shablonlar (english / math …, 2026-09-26)
    gsubj = _subj(group) if group else "english"
    templates = [_tpl_summary(t) for t in tq.all() if _subj(t) == gsubj]
    lvl = (group.level if group else None)
    # Guruh darajasiga moslari birinchi
    templates.sort(key=lambda t: (t["level"] != lvl, t["title"], t["variant"]))
    online = None
    o_parts = _load(o.parts) if o else []
    qmap = _qmap(o_parts) if o else {}
    can_manage = user.role in RESULT_ROLES
    if o:
        t = db.query(models.ExamTemplate).get(o.template_id)
        q_total = sum(len(p.get("questions") or []) for p in o_parts)
        online = {
            "token": o.token, "is_open": bool(o.is_open),
            "template_id": o.template_id,
            "template_title": t.title if t else None,
            # Variantlar va listening skripti — FAQAT examinerga
            # (ustoz ko'rmaydi, 2026-09-26)
            "variants": (o.variants or None) if can_manage else None,
            "scripts": ([{"part": p.get("title"), "script": p.get("script")}
                         for p in o_parts if p.get("script")]
                        if can_manage else []),
            "online_max": o.online_max, "paper_max": o.paper_max,
            # Mock Writing — AI baholaydi (sahifa kutilayotganlarni
            # bittadan baholatadi, 2026-09-28)
            "ai_writing": _is_ai_writing(o_parts),
            "published_at": (o.published_at.isoformat()
                             if o.published_at else None),
            "published_by": o.published_by,
            "state": timer_state(o),
            "server_now": _iso(datetime.utcnow()),
            "starts_at": _iso(o.started_at),
            "ends_at": _iso(o.ends_at),
            "duration_min": o.duration_min,
            "in_progress": sum(1 for s in subs if s.status == "in_progress"),
            # Mockda examiner belgilamagan bo'lsa — 2 (Start oynasida shu
            # son turadi, 2026-09-27)
            "away_limit": away_limit_of(o, exam),
            "live": [
                {"id": s.id,
                 "name": s.typed_name or names.get(s.student_id) or "—",
                 "away_count": s.away_count or 0, "away_sec": s.away_sec or 0,
                 # masalan "To'liq ekran ishlamadi" (mock, 2026-09-27)
                 "note": s.note,
                 # JONLI JARAYON (2026-10-03): nechta savolga javob
                 # bergan (javoblar 15 soniyada saqlanadi)
                 "answered": _answered_count(s.answers),
                 "total": q_total}
                for s in subs if s.status == "in_progress"
            ],
            # Linkni hali umuman ochmaganlar (faol o'quvchilar)
            "not_joined": ([
                {"id": st.id, "name": st.full_name}
                for st in _group_students(db, exam.group_id)
                if (st.status or "active") == "active"
                and st.id not in {x.student_id for x in subs}]
                if timer_state(o) in ("waiting", "countdown", "running")
                else []),
            "expelled": [
                {"id": s.id,
                 "name": s.typed_name or names.get(s.student_id) or "—",
                 "note": s.note}
                for s in subs if s.status == "expelled"
            ],
        }
    return {"online": online, "group_level": lvl,
            "can_manage": user.role in RESULT_ROLES,
            "can_publish": user.role in PUBLISH_ROLES,
            "hidden": not can_see,
            "templates": templates,
            "submissions": [
                _sub_out(s, names, qmap, _cefr_info(o_parts, s))
                for s in subs]}


@router.post("/api/exams/{exam_id}/online")
def create_online(exam_id: int, payload: OnlineIn,
                  db: Session = Depends(get_db),
                  user=Depends(require_role(*RESULT_ROLES))):
    exam = _exams._exam_in_scope(db, exam_id, user)
    if exam.kind not in ("unit", "mid", "end", "mock"):
        raise HTTPException(400, "Online link faqat Unit, Mid-course, "
                                 "End of course va Mock testlari uchun")
    if not _exam_open_for_results(exam):
        raise HTTPException(400, "Test hali tasdiqlanmagan — avval Examiner "
                                 "tasdiqlashi kerak")
    if _online_of(db, exam.id):
        raise HTTPException(409, "Bu testning linki allaqachon bor")
    t = db.query(models.ExamTemplate).get(payload.template_id)
    if not t or not t.is_active:
        raise HTTPException(404, "Test bazada topilmadi")
    # VARIANTLAR ARALASH (2026-09-26): odatiy rejimda har bo'lim shu
    # daraja/tur/unit'ning tasodifiy variantidan olinadi — ustoz
    # savollarni oldindan bilolmaydi. "single" — faqat tanlangan shablon.
    if (payload.mode or "mix") == "single":
        parts, variants = _load(t.parts), (t.variant or "A")
    else:
        parts, variants = mix_parts(t, _family(db, t))
    # Essay (Writing) savollari avtomat tekshirilmaydi — maksimal
    # ballga kirmaydi (2026-09-26).
    online_max = float(sum(1 for q in _questions(parts)
                           if q.get("type") != "essay"))
    if payload.paper_max is not None:
        paper_max = float(payload.paper_max)
    elif t.kind in ("mid", "end") and _subj(t) == "english":
        # 100 ballik testda qog'oz qismi qolgan ballni oladi
        paper_max = float(t.paper_max or 0) or max(
            0.0, MID_END_TOTAL - online_max)
    else:
        paper_max = float(t.paper_max or 0)
    if paper_max < 0:
        raise HTTPException(400, "Writing/Speaking bali noto'g'ri")
    # Mock Writing/Speaking — butun natija qog'oz balida. 0 bo'lsa
    # tasdiqlashda hammaga band 0 yozilardi va keyin tuzatib bo'lmasdi
    # (2026-09-28 ko'rigi) — shablon shkalasi (9 / 75) qo'yiladi.
    if (exam.kind or "") == "mock" and online_max == 0 and paper_max <= 0:
        paper_max = float(t.paper_max or 0) or 9.0
    total = online_max + paper_max
    scored = [r for r in exam.results if not r.absent and r.score is not None]
    if scored and abs((exam.max_score or 0) - total) > 1e-6:
        raise HTTPException(
            400, f"Testga natija kiritilgan va maksimal ball "
                 f"{exam.max_score:g}. Online {online_max:g} + qog'oz "
                 f"{paper_max:g} = {total:g} — mos emas")
    old_max = exam.max_score
    if (exam.kind or "") != "mock":
        # Mock natijasi BAND (0-9) — maksimal ball yozilmaydi, aks holda
        # gradebook mockni ballik testdek ko'rsatib qo'yadi.
        exam.max_score = total
    o = models.ExamOnline(exam_id=exam.id, template_id=t.id,
                          token=secrets.token_urlsafe(9), is_open=1,
                          parts=json.dumps(parts, ensure_ascii=False),
                          online_max=online_max,
                          paper_max=paper_max, created_by=user.full_name,
                          variants=variants)
    db.add(o)
    db.commit()
    audit.log(db, user, entity="exam", action="update", entity_id=exam.id,
              entity_label=exam.title or roles.exam_title(exam.kind, exam.unit_no),
              field="online_link", old_value=old_max,
              new_value=f"{t.title}: online {online_max:g} + qog'oz "
                        f"{paper_max:g}, variantlar {variants}",
              commit=True)
    _push_exam(db, exam, o, started=False)
    return get_online(exam_id, db, user)


@router.put("/api/exams/{exam_id}/online")
def toggle_online(exam_id: int, payload: OnlineToggle,
                  db: Session = Depends(get_db),
                  user=Depends(require_role(*RESULT_ROLES))):
    exam = _exams._exam_in_scope(db, exam_id, user)
    o = _online_of(db, exam.id)
    if not o:
        raise HTTPException(404, "Link yo'q")
    o.is_open = 1 if payload.is_open else 0
    db.commit()
    return get_online(exam_id, db, user)


def _push_exam(db: Session, exam, o, started: bool) -> None:
    """Jony Student ilovasidagi o'quvchilarga telefon bildirishnomasi
    (2026-10-03). push moduli entry.py orqali yuklanadi; bo'lmasa jim."""
    import sys as _sys
    P = _sys.modules.get("push")
    if P is not None and not is_strict(exam):
        P.notify_exam(db, exam, o, started)


class StartIn(BaseModel):
    minutes: int
    countdown: Optional[int] = None
    away_limit: Optional[int] = None


@router.post("/api/exams/{exam_id}/online/start")
def start_online(exam_id: int, payload: StartIn, db: Session = Depends(get_db),
                 user=Depends(require_role(*RESULT_ROLES))):
    """Examiner vaqt belgilab testni boshlaydi: teskari sanoqdan keyin
    savollar ochiladi, belgilangan vaqt tugagach hammasi avtomatik
    topshiriladi."""
    exam = _exams._exam_in_scope(db, exam_id, user)
    o = _online_of(db, exam.id)
    if not o:
        raise HTTPException(404, "Link yo'q")
    if not _exam_open_for_results(exam):
        raise HTTPException(400, "Test tasdiqlanmagan yoki bekor qilingan")
    if timer_state(o) in ("countdown", "running"):
        raise HTTPException(400, "Test allaqachon boshlangan")
    if not (1 <= payload.minutes <= 300):
        raise HTTPException(400, "Vaqt 1 dan 300 daqiqagacha bo'lishi kerak")
    cd = COUNTDOWN_SEC if payload.countdown is None else max(0, min(60, payload.countdown))
    now = datetime.utcnow()
    o.duration_min = payload.minutes
    if payload.away_limit is not None:
        o.away_limit = max(0, min(50, payload.away_limit))
    elif o.away_limit is None:
        # Mockda qat'iy: 2 marta (2026-09-27)
        o.away_limit = MOCK_AWAY_LIMIT if is_strict(exam) else AWAY_LIMIT_DEFAULT
    o.started_at = now + timedelta(seconds=cd)
    o.ends_at = o.started_at + timedelta(minutes=payload.minutes)
    o.is_open = 1
    db.commit()
    audit.log(db, user, entity="exam", action="update", entity_id=exam.id,
              entity_label=exam.title or roles.exam_title(exam.kind, exam.unit_no),
              field="online_start", new_value=f"{payload.minutes} daqiqa",
              commit=True)
    _push_exam(db, exam, o, started=True)
    return get_online(exam_id, db, user)


@router.post("/api/exams/{exam_id}/online/stop")
def stop_online(exam_id: int, db: Session = Depends(get_db),
                user=Depends(require_role(*RESULT_ROLES))):
    """Testni muddatidan oldin tugatish — hamma o'quvchida vaqt tugaydi
    va javoblari avtomatik topshiriladi."""
    exam = _exams._exam_in_scope(db, exam_id, user)
    o = _online_of(db, exam.id)
    if not o or timer_state(o) not in ("countdown", "running"):
        raise HTTPException(400, "Test hozir ketmayapti")
    o.ends_at = datetime.utcnow()
    db.commit()
    return get_online(exam_id, db, user)


@router.delete("/api/exams/{exam_id}/online")
def delete_online(exam_id: int, db: Session = Depends(get_db),
                  user=Depends(require_role(*RESULT_ROLES))):
    exam = _exams._exam_in_scope(db, exam_id, user)
    o = _online_of(db, exam.id)
    if not o:
        raise HTTPException(404, "Link yo'q")
    if db.query(models.ExamSubmission).filter(
            models.ExamSubmission.exam_id == exam.id).count():
        raise HTTPException(400, "Bu link orqali topshirganlar bor — "
                                 "o'chirib bo'lmaydi, faqat yopish mumkin")
    db.delete(o)
    db.commit()
    return get_online(exam_id, db, user)


def _sub_in_scope(db: Session, sid: int, user):
    s = db.query(models.ExamSubmission).get(sid)
    if not s:
        raise HTTPException(404, "Topshiriq topilmadi")
    exam = _exams._exam_in_scope(db, s.exam_id, user)
    o = _online_of(db, exam.id)
    return s, exam, o


@router.post("/api/exam-submissions/{sid}/assign")
def assign_submission(sid: int, payload: AssignIn,
                      db: Session = Depends(get_db),
                      user=Depends(require_role(*RESULT_ROLES))):
    """Qizil chiziqdan pastdagi natijani guruhdagi o'quvchiga
    biriktirish (ismi xato yozilgan yoki qayta topshirgan)."""
    s, exam, o = _sub_in_scope(db, sid, user)
    if s.status not in ("pending", "duplicate", "replaced"):
        raise HTTPException(400, "Bu natija allaqachon joyida")
    if payload.student_id not in {st.id for st in
                                  _group_students(db, exam.group_id)}:
        raise HTTPException(400, "Bu o'quvchi guruhda yo'q — avval guruhga "
                                 "qo'shing")
    _place(db, exam, o, s, payload.student_id, user)
    audit.log(db, user, entity="exam", action="update", entity_id=exam.id,
              entity_label=exam.title or roles.exam_title(exam.kind, exam.unit_no),
              field="online_assign",
              old_value=s.typed_name or "", new_value=payload.student_id,
              commit=True)
    return get_online(exam.id, db, user)


@router.post("/api/exam-submissions/{sid}/expel")
def expel_submission(sid: int, db: Session = Depends(get_db),
                     user=Depends(require_role(*RESULT_ROLES))):
    """Examiner o'quvchini testdan chetlatadi — test o'sha zahoti
    yopiladi, natijasi hisobga olinmaydi."""
    s, exam, o = _sub_in_scope(db, sid, user)
    if s.status == "expelled":
        raise HTTPException(400, "Allaqachon chetlatilgan")
    expel(db, exam, s, f"Examiner chetlatdi ({user.full_name})")
    audit.log(db, user, entity="exam", action="update", entity_id=exam.id,
              entity_label=exam.title or roles.exam_title(exam.kind, exam.unit_no),
              field="online_expel",
              new_value=s.typed_name or s.student_id, commit=True)
    return get_online(exam.id, db, user)


@router.post("/api/exam-submissions/{sid}/reject")
def reject_submission(sid: int, db: Session = Depends(get_db),
                      user=Depends(require_role(*RESULT_ROLES))):
    s, exam, o = _sub_in_scope(db, sid, user)
    if s.status == "placed":
        raise HTTPException(400, "Joylashgan natijani rad etib bo'lmaydi — "
                                 "o'rniga boshqasini biriktiring")
    s.status = "rejected"
    db.commit()
    return get_online(exam.id, db, user)


@router.put("/api/exams/{exam_id}/paper")
def save_paper(exam_id: int, payload: PaperBulk,
               db: Session = Depends(get_db),
               user=Depends(require_role(*RESULT_ROLES))):
    """Writing + Speaking (qog'oz) ballari. Jami = online + qog'oz —
    shu jami natijaga yoziladi (foiz, coin shundan)."""
    exam = _exams._exam_in_scope(db, exam_id, user)
    o = _online_of(db, exam.id)
    if not o or not (o.paper_max or 0) > 0:
        raise HTTPException(400, "Bu testda qog'oz qismi yo'q")
    placed = {s.student_id: s for s in db.query(models.ExamSubmission)
              .filter(models.ExamSubmission.exam_id == exam.id,
                      models.ExamSubmission.status == "placed").all()}
    marks = []
    for m in payload.marks:
        s = placed.get(m.student_id)
        if not s:
            continue
        if m.paper is not None and not (0 <= m.paper <= o.paper_max):
            raise HTTPException(
                400, f"Writing/Speaking bali 0 va {o.paper_max:g} oralig'ida")
        if s.paper_score == m.paper:
            continue
        if m.paper is None and s.paper_by == "ai":
            # Bo'sh katak AI qo'ygan balni o'chirmaydi (eski sahifadan
            # "Saqlash" bosilsa ham) — examiner o'zi boshqa ball yozadi
            continue
        s.paper_score = m.paper
        # Examiner o'zgartirdi — endi AI bu balni hech qachon yozmaydi
        s.paper_by = user.full_name if m.paper is not None else None
        if m.paper is not None:
            # Mockda ball emas, band yoziladi (_mark_for)
            mk = _mark_for(exam, o, s)
            if mk is not None:
                marks.append(mk)
    db.commit()
    if marks and o.published_at:
        _exams._apply_exam_marks(db, exam, schemas.ExamScoreBulk(marks=marks),
                                 user)
    return get_online(exam_id, db, user)


@router.post("/api/exams/{exam_id}/online/publish")
def publish_online(exam_id: int, db: Session = Depends(get_db),
                   user=Depends(require_role(*PUBLISH_ROLES))):
    """Examiner natijalarni TASDIQLAYDI: joyidagi barcha topshiriqlar
    guruh testiga yoziladi — shundan keyin ustoz, o'quvchi va ota-ona
    ko'radi, coin beriladi, Telegram xabari ketadi. Qog'oz qismi bor
    bo'lsa, bali kiritilganlargina yoziladi (qolgani kiritilganda)."""
    exam = _exams._exam_in_scope(db, exam_id, user)
    o = _online_of(db, exam.id)
    if not o:
        raise HTTPException(404, "Link yo'q")
    if o.published_at:
        raise HTTPException(400, "Natijalar allaqachon tasdiqlangan")
    if not _exam_open_for_results(exam):
        raise HTTPException(400, "Test tasdiqlanmagan yoki bekor qilingan")
    placed = (db.query(models.ExamSubmission)
              .filter(models.ExamSubmission.exam_id == exam.id,
                      models.ExamSubmission.status == "placed",
                      models.ExamSubmission.student_id.isnot(None)).all())
    marks = []
    for s in placed:
        if (o.paper_max or 0) > 0 and s.paper_score is None:
            continue
        m = _mark_for(exam, o, s)
        if m is not None:
            marks.append(m)
    # UMUMAN KIRMAGANLAR — "KELMADI" (2026-10-03, Jahongir: "imtihonga
    # umuman kirmagan o'quvchi kelmadi deb avtomat belgilansin").
    # Faqat faol o'quvchilar; linkni ochgan (har qanday holatda) yoki
    # natijasi allaqachon bor o'quvchiga tegilmaydi. Examiner keyin
    # jadvalda o'zgartira oladi.
    touched = {sid for (sid,) in db.query(models.ExamSubmission.student_id)
               .filter(models.ExamSubmission.exam_id == exam.id,
                       models.ExamSubmission.student_id.isnot(None)).all()}
    has_row = {r.student_id for r in exam.results}
    marked = {m.student_id for m in marks}
    absent_ids = [st.id for st in _group_students(db, exam.group_id)
                  if (st.status or "active") == "active"
                  and st.id not in touched and st.id not in has_row
                  and st.id not in marked]
    for sid in absent_ids:
        marks.append(schemas.ExamScoreMark(student_id=sid, absent=True,
                                           note="Online testga kirmadi"))
    o.published_at = datetime.utcnow()
    o.published_by = user.full_name
    db.commit()
    if marks:
        _exams._apply_exam_marks(db, exam, schemas.ExamScoreBulk(marks=marks),
                                 user)
    audit.log(db, user, entity="exam", action="update", entity_id=exam.id,
              entity_label=exam.title or roles.exam_title(exam.kind, exam.unit_no),
              field="online_publish",
              new_value=f"{len(marks) - len(absent_ids)} ta natija"
                        + (f", {len(absent_ids)} ta kelmadi" if absent_ids else ""),
              commit=True)
    return get_online(exam_id, db, user)


# -------------------------------------------------------- ochiq (loginsiz)
def _rate_ok(ip: str) -> bool:
    now = time.time()
    hits = [t for t in _HITS.get(ip, []) if now - t < 3600]
    if len(hits) >= _MAX_PER_HOUR:
        _HITS[ip] = hits
        return False
    hits.append(now)
    _HITS[ip] = hits
    return True


def _public(db: Session, token: str):
    if not token or len(token) < 8:
        raise HTTPException(404, "Test topilmadi")
    o = db.query(models.ExamOnline).filter(
        models.ExamOnline.token == token).first()
    if not o:
        raise HTTPException(404, "Test topilmadi")
    exam = db.query(models.Exam).get(o.exam_id)
    if not exam or exam.status == "cancelled":
        raise HTTPException(404, "Test topilmadi")
    return o, exam


def _parts_for(exam, parts: list, key: str | None) -> list:
    """O'quvchiga savollar — mockdan tashqari har o'quvchiga aralash."""
    pub = public_parts(parts)
    if is_strict(exam) or not key:
        return pub
    return shuffle_for(pub, parts, key)


@router.get("/api/public/exam/{token}")
def public_exam(token: str, key: str | None = None,
                db: Session = Depends(get_db)):
    """Ochiq sahifa holati. Savollar faqat test ketayotganda beriladi —
    examiner "Start" bosmaguncha o'quvchi kutib turadi (2026-09-18)."""
    o, exam = _public(db, token)
    finalize_expired(db, o, exam)
    group = db.query(models.Group).get(exam.group_id)
    is_open = bool(o.is_open) and _exam_open_for_results(exam)
    state = timer_state(o)
    parts = _load(o.parts)
    strict = is_strict(exam)
    return {
        "title": exam.title or roles.exam_title(exam.kind, exam.unit_no),
        "group": group.name if group else "",
        "date": exam.date.isoformat() if exam.date else None,
        # Qat'iy tartib (faqat mock, 2026-09-27): kompyuterda, to'liq
        # ekranda; chiqish chegarasi sahifadagi qoidalarda ko'rinadi
        "strict": strict,
        "away_limit": away_limit_of(o, exam) if strict else None,
        "is_open": is_open,
        "state": state if is_open else "closed",
        "server_now": _iso(datetime.utcnow()),
        "starts_at": _iso(o.started_at),
        "ends_at": _iso(o.ends_at),
        "duration_min": o.duration_min,
        "q_count": int(o.online_max or 0),
        "paper_max": o.paper_max or 0,
        "students": [{"id": s.id, "name": s.full_name}
                     for s in _roster(db, exam.group_id)]
        if is_open and state != "finished" else [],
        "parts": (_parts_for(exam, parts, key)
                  if is_open and state == "running" else []),
    }


class BeginIn(BaseModel):
    student_id: Optional[int] = None
    name: Optional[str] = None
    photo: str


class SaveIn(BaseModel):
    key: str
    answers: dict


class AwayIn(BaseModel):
    key: str
    seconds: int = 0
    # tab | blur | fullscreen | extension | printscreen | devtools
    # (mockning qat'iy tartibi yuboradi, 2026-09-27; boshqalarida yo'q)
    reason: Optional[str] = None
    # Quyidagilar ham faqat mockda (2026-09-27):
    # eid — hodisa kodi: internet uzilib sahifa qayta yuborsa, ikki
    #   marta sanalmaydi;
    # extend — o'sha chiqishning davomi (qaytgach qolgan soniyalar):
    #   away_sec ga qo'shiladi, soni oshmaydi;
    # flag="nofs" — brauzer to'liq ekranga ruxsat bermadi: sanalmaydi,
    #   examiner jonli ro'yxatda ko'radi.
    eid: Optional[str] = None
    extend: bool = False
    flag: Optional[str] = None


class SubmitIn(BaseModel):
    # Yangi tartib: begin'dan olingan kalit bilan
    key: Optional[str] = None
    answers: dict
    # Eski tartib (kalitsiz) — keshlangan eski sahifalar uchun
    student_id: Optional[int] = None
    name: Optional[str] = None
    photo: Optional[str] = None


def _client_ip(request: Request) -> str:
    return ((request.headers.get("x-forwarded-for") or "").split(",")[0].strip()
            or (request.client.host if request.client else ""))


def is_strict(exam) -> bool:
    """Qat'iy tartib (kompyuterda, to'liq ekran, 2 marta chiqish) — faqat
    MOCK testlarda (2026-09-27)."""
    return (getattr(exam, "kind", None) or "") == "mock"


def is_mobile_ua(request: Request) -> bool:
    return bool(MOBILE_UA_RE.search(request.headers.get("user-agent") or ""))


def deny_mobile(request: Request) -> None:
    """Telefon / planshetdan mock boshlanmaydi. Asosiy tekshiruv sahifada
    (iPad o'zini Mac deb tanitadi — uni faqat brauzer ajratadi), bu —
    ikkinchi qavat."""
    if is_mobile_ua(request):
        raise HTTPException(403, MOBILE_MSG)


def away_limit_of(o, exam) -> Optional[int]:
    """Amaldagi chiqish chegarasi: examiner belgilagani, belgilamagan
    bo'lsa mockda MOCK_AWAY_LIMIT, boshqalarida chegara yo'q."""
    if o.away_limit is not None:
        return o.away_limit
    return MOCK_AWAY_LIMIT if is_strict(exam) else None


def deny_retake(db: Session, exam, student_id) -> None:
    """MOCK: ro'yxatdagi o'quvchi ikkinchi marta kira olmaydi (2026-09-27).

    Aks holda chetlatilgan (yoki 2 marta qoidabuzarlik qilgan) o'quvchi
    maxfiy oyna / boshqa brauzerda havolani qayta ochib, ismini yana
    tanlab, toza hisob bilan davom etardi — "3-qoidabuzarlikda
    chetlatiladi" hech narsani anglatmasdi. Ro'yxatdan istalgan ismni
    tanlash mumkinligi uchun davom etayotgan topshiriqning kaliti ham
    berilmaydi: o'sha kompyuterda davom etadi yoki examiner eski
    yozuvni rad etadi ("Rad etish") — shunda qayta kira oladi.
    Ro'yxatda yo'q (yozilgan) ism — student_id yo'q, examiner o'zi
    biriktiradi, bu yerda tekshirilmaydi."""
    if student_id is None:
        return
    subs = (db.query(models.ExamSubmission)
            .filter(models.ExamSubmission.exam_id == exam.id,
                    models.ExamSubmission.student_id == student_id).all())
    st = {s.status for s in subs}
    if "expelled" in st:
        raise HTTPException(403, "Siz bu testdan chetlatilgansiz")
    if st & {"placed", "duplicate"}:
        raise HTTPException(409, "Siz bu testni allaqachon topshirgansiz")
    if "in_progress" in st:
        raise HTTPException(409, "Siz bu testni boshqa kompyuter yoki "
                                 "brauzerda boshlagansiz — o'sha yerda davom "
                                 "eting yoki examinerga murojaat qiling")


def _identify(db: Session, exam, student_id, name, photo):
    """Ro'yxatdan tanlangan yoki yozilgan ism + kamera rasmi."""
    photo = photo or ""
    if not photo.startswith("data:image/") or len(photo) > PHOTO_MAX_CHARS:
        raise HTTPException(400, "Kameradan rasm oling")
    roster = {s.id: s for s in _roster(db, exam.group_id)}
    typed = (name or "").strip()[:120] or None
    if student_id is not None and student_id not in roster:
        raise HTTPException(400, "Ro'yxatdan o'zingizni tanlang")
    if student_id is None:
        if not typed or len(typed) < 3:
            raise HTTPException(400, "Ism va familiyangizni yozing")
        # Yozilgan ism ro'yxatdagi bilan AYNAN mos kelsa — o'sha o'quvchi
        want = _norm(typed)
        same = [s.id for s in roster.values() if _norm(s.full_name) == want]
        if len(same) == 1:
            student_id = same[0]
    if not typed and student_id in roster:
        typed = roster[student_id].full_name
    return student_id, typed, photo


def _finalize(db: Session, o, exam, sub, answers: dict, by: str = "Online test"):
    """Topshiriqni baholab joylashtiradi (qo'lda topshirish ham, vaqt
    tugab avtomatik topshirish ham shu yerdan)."""
    answers = {str(k): v for k, v in (answers or {}).items()}
    score, total, detail = grade(_load(o.parts), answers)
    status = "pending"
    if sub.student_id is not None:
        already = db.query(models.ExamSubmission).filter(
            models.ExamSubmission.exam_id == exam.id,
            models.ExamSubmission.student_id == sub.student_id,
            models.ExamSubmission.status == "placed",
            models.ExamSubmission.id != sub.id).first()
        status = "duplicate" if already else "placed"
    sub.answers = _answers_json(answers)
    sub.detail = json.dumps(detail, ensure_ascii=False)
    sub.online_score = score
    sub.online_max = total
    sub.status = status
    sub.submitted_at = datetime.utcnow()
    # WRITING AI (2026-09-28): bu yerda faqat belgi. Baholash alohida
    # so'rovda (/ai-grade) — _finalize finalize_expired ichida GET
    # so'rovlarida tsiklda chaqiriladi, AI esa 20 s gacha ketadi.
    if sub.ai_status is None and _is_ai_writing(_load(o.parts)):
        sub.ai_status = "pending"
    if status != "placed" and status != "duplicate":
        sub.student_id = None
    if status == "placed":
        sub.placed_by = by
        sub.placed_at = datetime.utcnow()
    db.commit()
    if status == "placed":
        try:
            _write_result(db, exam, o, sub, _system_user())
        except HTTPException:
            # Masalan, maksimal ball keyin o'zgartirilgan — javob baribir
            # saqlangan, examiner ExamSheet'da ko'radi
            db.rollback()
    return status


def finalize_expired(db: Session, o, exam) -> int:
    """Vaqt tugab (va kechikib keluvchilar uchun muhlat o'tib) hali
    topshirilmagan ishlar SAQLANGAN javoblari bilan topshiriladi — kim
    qancha belgilagan bo'lsa (Jahongir). Sahifa yopilib qolgan
    o'quvchi ham natijasiz qolmaydi."""
    if not o.ends_at or datetime.utcnow() < o.ends_at + timedelta(seconds=GRACE_SEC):
        return 0
    subs = (db.query(models.ExamSubmission)
            .filter(models.ExamSubmission.exam_id == exam.id,
                    models.ExamSubmission.status == "in_progress").all())
    for s in subs:
        _finalize(db, o, exam, s, _load_dict(s.answers), by="Vaqt tugadi (avtomat)")
    return len(subs)


def _answered_count(answers_json) -> int:
    """Nechta savolga javob berilgan (bo'sh matn/ro'yxat sanalmaydi)."""
    n = 0
    for v in _load_dict(answers_json).values():
        if isinstance(v, (int, float)) and not isinstance(v, bool):
            n += 1
        elif isinstance(v, list) and v:
            n += 1
        elif isinstance(v, str) and v.strip():
            n += 1
    return n


def _merge_answers(old_json, new: dict | None) -> dict:
    """Saqlangan javoblar USTIGA yangilari (2026-10-03). Kalit hech
    qachon o'chmaydi: o'quvchi boshqa telefonga o'tsa, yangi telefon
    bo'sh {} yuborib serverdagi javoblarni o'chirib yubormasin."""
    d = _load_dict(old_json)
    for k, v in (new or {}).items():
        d[str(k)] = v
    return d


def _answers_json(answers: dict) -> str:
    """Javoblar JSON'i. Ilgari butun matn 20 000 belgida kesilardi —
    uzun inshoda JSON buzilib, javoblar {} bo'lib qolardi (AI ularni
    bo'sh deb 0 qo'yardi). Endi har javob o'zi cheklanadi."""
    safe = {k: (v[:ESSAY_MAX_CHARS] if isinstance(v, str) else v)
            for k, v in (answers or {}).items()}
    out = json.dumps(safe, ensure_ascii=False)
    if len(out) <= 100000:
        return out
    # Juda ko'p / juda uzun (g'ayrioddiy) — har matn qisqartiriladi,
    # JSON baribir to'g'ri qoladi
    return json.dumps({k: (v[:3000] if isinstance(v, str) else v)
                       for k, v in list(safe.items())[:300]}, ensure_ascii=False)


# ------------------------------------------------------- WRITING AI
# 2026-09-28, Jahongir: "Writingni ham avtobaholaydigan qilib qoysak
# yaxshi bo'lardi. Hech qanday muammolarsiz bo'lishi yaxshi bolardi".
# writing_ai.py baholaydi; bu yerda — qachon, kim va natija qayerga:
#   - _finalize faqat ai_status="pending" qo'yadi;
#   - o'quvchi brauzeri topshirgach /api/public/exam/{token}/ai-grade ni,
#     examiner sahifasi esa kutilayotganlarni bittadan chaqiradi
#     (bitta so'rov = bitta topshiruv, Vercel 30 s);
#   - natija e'lon qilinmagan va examiner o'zi ball qo'ymagan bo'lsa
#     qog'oz baliga yoziladi (paper_by="ai"); examiner istalgan payt
#     o'zgartiradi — keyin AI unga tegmaydi;
#   - e'londan keyin kelgan AI bahosi faqat taklif (guruh jadvaliga,
#     coin va Telegramga o'zi yozilmaydi — examiner saqlaydi).
AI_RUNNING_SEC = 75     # "baholanmoqda" shundan uzoq tursa — osilgan
AI_MAX_TRIES = 3        # xato bo'lsa o'zi shuncha marta qayta uriniladi


def _is_ai_writing(parts) -> bool:
    import writing_ai
    return writing_ai.skill_of(parts) is not None


def _parse_iso(s) -> Optional[datetime]:
    try:
        return datetime.fromisoformat(str(s))
    except (TypeError, ValueError):
        return None


def _ai_grade_sub(db: Session, sub, o, *, force: bool = False) -> str:
    """Bitta topshiruvni AI bilan baholaydi. Holatni qaytaradi:
    done | running | error | no_key | skipped."""
    import writing_ai
    M = models.ExamSubmission
    parts = _load(o.parts)
    if not writing_ai.skill_of(parts):
        return "skipped"
    if sub.status not in ("placed", "pending", "duplicate", "replaced"):
        return "skipped"          # hali topshirilmagan / chetlatilgan
    meta = _load_dict(sub.ai_review)
    now = datetime.utcnow()
    if sub.ai_status == "done" and not force:
        return "done"
    if sub.ai_status == "running":
        st = _parse_iso(meta.get("started"))
        if st and (now - st).total_seconds() < AI_RUNNING_SEC:
            return "running"
    tries = int(meta.get("tries") or 0)
    if not force and sub.ai_status in ("error", "no_key") and tries >= AI_MAX_TRIES:
        return sub.ai_status
    answers = _load_dict(sub.answers)
    if not answers and (sub.answers or "").strip() not in ("", "{}"):
        # Javoblar saqlanishida buzilgan (eski 20 000 belgi kesimi) —
        # bo'sh deb 0 qo'yilmasin, examiner qo'lda baholaydi
        sub.ai_status = "error"
        sub.ai_review = json.dumps({"error": "bad_answers", "tries": tries,
                                    "at": now.isoformat(timespec="seconds")})
        db.commit()
        return "error"

    # Band qilish (optimistik): shu paytgacha holat o'zgarmagan bo'lsa
    # "running" — parallel so'rov ikkinchi marta AI chaqirmasin
    old_status, old_review = sub.ai_status, sub.ai_review
    claim = {"tries": tries, "started": now.isoformat(timespec="seconds")}
    if old_status == "done":
        claim["prev"] = old_review        # qayta baholash xato bo'lsa qaytadi
    q = db.query(M).filter(M.id == sub.id)
    q = q.filter(M.ai_status.is_(None) if old_status is None else M.ai_status == old_status)
    q = q.filter(M.ai_review.is_(None) if old_review is None else M.ai_review == old_review)
    got = q.update({M.ai_status: "running", M.ai_review: json.dumps(claim)},
                   synchronize_session=False)
    db.commit()
    db.refresh(sub)
    if got != 1:
        return sub.ai_status or "running"

    try:
        res = writing_ai.grade(parts, answers)
    except writing_ai.WritingAIError as e:
        db.refresh(sub)
        if old_status == "done":
            sub.ai_status, sub.ai_review = "done", old_review
            db.commit()
            return "error"
        sub.ai_status = "no_key" if e.code == "no_key" else "error"
        sub.ai_review = json.dumps({"error": e.code, "tries": tries + 1,
                                    "at": now.isoformat(timespec="seconds")})
        db.commit()
        return sub.ai_status

    db.refresh(sub)
    res["tries"] = tries + 1
    sub.ai_status = "done"
    sub.ai_score = float(res["score"])
    sub.ai_review = json.dumps(res, ensure_ascii=False)
    expected = 9.0 if res["skill"] == "ielts_writing" else 75.0
    if (not o.published_at
            and abs(float(o.paper_max or 0) - expected) < 1e-6
            and (sub.paper_score is None or sub.paper_by == "ai")):
        sub.paper_score = float(res["score"])
        sub.paper_by = "ai"
    db.commit()
    return "done"


class AiGradeIn(BaseModel):
    key: Optional[str] = None


@router.post("/api/exam-submissions/{sid}/ai-grade")
def ai_grade_submission(sid: int, force: bool = False,
                        db: Session = Depends(get_db),
                        user=Depends(require_role(*RESULT_ROLES))):
    """Examiner: shu topshiruvni AI bilan baholash (force — qayta)."""
    s, exam, o = _sub_in_scope(db, sid, user)
    if not o:
        raise HTTPException(404, "Link yo'q")
    st = _ai_grade_sub(db, s, o, force=force)
    db.refresh(s)
    return {"status": st, "ai_status": s.ai_status, "ai_score": s.ai_score,
            "paper_score": s.paper_score, "paper_by": s.paper_by,
            "ai_review": _ai_public(s.ai_review)}


@router.post("/api/public/exam/{token}/ai-grade")
def public_ai_grade(token: str, payload: AiGradeIn,
                    db: Session = Depends(get_db)):
    """O'quvchi brauzeri topshirgach chaqiradi — natija o'quvchiga
    ko'rsatilmaydi (examiner e'lon qilgach ko'radi)."""
    o, exam = _public(db, token)
    s = _sub_by_key(db, exam, payload.key or "")
    st = _ai_grade_sub(db, s, o)
    return {"ok": True, "status": st}


def _load_dict(txt) -> dict:
    try:
        v = json.loads(txt or "{}")
        return v if isinstance(v, dict) else {}
    except Exception:
        return {}


def expel(db: Session, exam, sub, why: str):
    """O'quvchini testdan chetlatish: uning testi yopiladi va natijasi
    umuman hisobga olinmaydi (2026-09-23, Jahongir)."""
    if sub.status == "placed" and sub.student_id:
        # Allaqachon yozilgan natija olib tashlanadi (coin ham qaytadi)
        for r in (db.query(models.ExamResult)
                  .filter(models.ExamResult.exam_id == exam.id,
                          models.ExamResult.student_id == sub.student_id).all()):
            _drop_coin_entry(db, "exam", r.id)
            db.delete(r)
    sub.status = "expelled"
    sub.note = why
    db.commit()


def _sub_by_key(db: Session, exam, key: str):
    if not key or len(key) < 10:
        raise HTTPException(400, "Qaytadan kiring")
    s = (db.query(models.ExamSubmission)
         .filter(models.ExamSubmission.exam_id == exam.id,
                 models.ExamSubmission.sub_key == key).first())
    if not s:
        raise HTTPException(400, "Qaytadan kiring")
    return s


def _can_answer(o) -> bool:
    """Javob qabul qilinadimi: test ketyapti yoki tugaganiga hali
    muhlat (GRACE_SEC) o'tmagan — avtomatik topshirish yetib kelsin."""
    if not o.is_open or not o.started_at or not o.ends_at:
        return False
    now = datetime.utcnow()
    return o.started_at <= now + timedelta(seconds=2) and \
        now <= o.ends_at + timedelta(seconds=GRACE_SEC)


@router.post("/api/public/exam/{token}/begin")
def public_begin(token: str, payload: BeginIn, request: Request,
                 db: Session = Depends(get_db)):
    """O'quvchi o'zini tanitadi (ism + rasm) — test boshlanishini
    kutib turadi. Kalit brauzerda saqlanadi."""
    ip = _client_ip(request)
    if not _rate_ok(ip or "?"):
        raise HTTPException(429, "Juda ko'p urinish — birozdan keyin qayta "
                                 "urinib ko'ring")
    o, exam = _public(db, token)
    if is_strict(exam):
        deny_mobile(request)       # mock faqat kompyuterda (2026-09-27)
    if not o.is_open or not _exam_open_for_results(exam) or \
            timer_state(o) == "finished":
        raise HTTPException(410, "Test yopilgan")
    student_id, typed, photo = _identify(db, exam, payload.student_id,
                                         payload.name, payload.photo)
    if is_strict(exam):
        deny_retake(db, exam, student_id)
    sub = models.ExamSubmission(
        exam_id=exam.id, student_id=student_id, typed_name=typed,
        photo=photo, answers="{}", status="in_progress", ip=ip[:64],
        online_max=o.online_max or 0, sub_key=secrets.token_urlsafe(16))
    db.add(sub)
    db.commit()
    # Ism suv belgisi uchun ham qaytariladi (2026-09-23, Jahongir:
    # "ismiga suv belgi qo'shchi") — skrinshot tarqalsa, kimniki
    # ekani ko'rinib tursin
    return {"ok": True, "key": sub.sub_key, "name": typed or ""}


@router.post("/api/public/exam/{token}/save")
def public_save(token: str, payload: SaveIn, db: Session = Depends(get_db)):
    """Javoblarni oraliqda saqlash — telefon o'chib qolsa ham yo'qolmasin."""
    o, exam = _public(db, token)
    s = _sub_by_key(db, exam, payload.key)
    if s.status == "expelled":
        return {"ok": False, "expelled": True}
    if s.status != "in_progress":
        return {"ok": True, "submitted": True}
    if not _can_answer(o):
        return {"ok": False}
    # Butun JSON kesilmaydi — har javob o'zi cheklanadi (uzun insho
    # vaqt tugab avtomat topshirilganda JSON buzilib, AI 0 qo'ymasin)
    s.answers = _answers_json(_merge_answers(s.answers, payload.answers))
    db.commit()
    return {"ok": True}


@router.post("/api/public/exam/{token}/away")
def public_away(token: str, payload: AwayIn, db: Session = Depends(get_db)):
    """O'quvchi test sahifasidan chiqib qaytdi — qayd qilinadi.
    (2026-09-23, Jahongir: skrinshotning o'zini sezib bo'lmaydi, lekin
    savolni boshqa ilovaga olib chiqish shu yerda ko'rinadi.)"""
    o, exam = _public(db, token)
    s = _sub_by_key(db, exam, payload.key)
    if s.status != "in_progress" or not _can_answer(o):
        return {"ok": True}
    # Mockda examiner chegara qo'ymagan bo'lsa ham 2 (2026-09-27)
    limit = away_limit_of(o, exam)

    def state(**extra):
        return {"ok": True, "away_count": s.away_count or 0,
                "away_limit": limit,
                "left": (limit - (s.away_count or 0)) if limit else None,
                **extra}

    # Qayta yuborilgan hodisa (internet uzilgan edi) — ikkinchi marta
    # sanalmaydi (2026-09-27)
    eid = (payload.eid or "").strip()[:40]
    if eid:
        try:
            seen = json.loads(s.away_eids or "[]")
            seen = seen if isinstance(seen, list) else []
        except Exception:
            seen = []
        if eid in seen:
            return state(duplicate=True)
        s.away_eids = json.dumps((seen + [eid])[-AWAY_EIDS_KEEP:])
    if (payload.flag or "") == "nofs":
        # Sanalmaydi — examiner jonli ro'yxatda ko'radi
        if not s.note:
            s.note = NOFS_NOTE
        db.commit()
        return state()
    secs = max(0, min(3600, int(payload.seconds or 0)))
    if payload.extend:
        # O'sha chiqishning davomi: vaqti qo'shiladi, soni oshmaydi
        s.away_sec = (s.away_sec or 0) + secs
        db.commit()
        return state()
    s.away_count = (s.away_count or 0) + 1
    s.away_sec = (s.away_sec or 0) + secs
    db.commit()
    if limit and s.away_count > limit:
        why = f"Sahifadan {s.away_count} marta chiqdi (ruxsat: {limit})"
        # Chetlatishga olib kelgan chiqish sababi — examiner ko'rsin
        reason = AWAY_REASONS.get((payload.reason or "").strip().lower())
        if reason:
            why += f" — oxirgisi: {reason}"
        expel(db, exam, s, why)
        return {"ok": True, "away_count": s.away_count, "expelled": True}
    return {"ok": True, "away_count": s.away_count,
            "away_limit": limit, "left": (limit - s.away_count) if limit else None}


@router.post("/api/public/exam/{token}/submit")
def public_submit(token: str, payload: SubmitIn, request: Request,
                  db: Session = Depends(get_db)):
    o, exam = _public(db, token)
    if not _exam_open_for_results(exam):
        raise HTTPException(410, "Test yopilgan")
    if payload.key:
        s = _sub_by_key(db, exam, payload.key)
        if s.status == "expelled":
            return {"ok": False, "expelled": True}
        if s.status == "in_progress":
            if not _can_answer(o):
                # Muhlat o'tib ketgan — saqlangan javoblar bilan yakunlanadi
                answers = _load_dict(s.answers)
            else:
                answers = _merge_answers(s.answers, payload.answers)
            _finalize(db, o, exam, s, answers)
        return {"ok": True, "paper_max": o.paper_max or 0,
                "pending": s.status not in ("placed",),
                # Writing mocki — sahifa /ai-grade ni chaqiradi (2026-09-28)
                "ai_writing": s.ai_status == "pending"}
    # Eski tartib (kalitsiz): faqat test ketayotganda. Mock telefondan
    # bu yo'l bilan ham topshirilmaydi (2026-09-27)
    if is_strict(exam):
        deny_mobile(request)
    ip = _client_ip(request)
    if not _rate_ok(ip or "?"):
        raise HTTPException(429, "Juda ko'p urinish — birozdan keyin qayta "
                                 "urinib ko'ring")
    if not _can_answer(o):
        raise HTTPException(410, "Test yopilgan")
    student_id, typed, photo = _identify(db, exam, payload.student_id,
                                         payload.name, payload.photo)
    if is_strict(exam):
        deny_retake(db, exam, student_id)   # kalitsiz yo'l ham (2026-09-27)
    sub = models.ExamSubmission(
        exam_id=exam.id, student_id=student_id, typed_name=typed, photo=photo,
        status="in_progress", ip=ip[:64], online_max=o.online_max or 0,
        sub_key=secrets.token_urlsafe(16))
    db.add(sub)
    db.commit()
    status = _finalize(db, o, exam, sub, payload.answers)
    # Ball o'quvchiga ko'rsatilmaydi — examiner tasdiqlagach e'lon
    # qilinadi (2026-09-18)
    return {"ok": True, "paper_max": o.paper_max or 0,
            "pending": status != "placed"}


# ================================================== JONY STUDENT ILOVASI ICHIDA
# 2026-09-25, Jahongir: "cherer Student app qiladigan qilish kerak link
# ham shu Student appga keladigan qilaylik".
#
# Farqi (link orqali loginsiz tartibdan):
#   - o'quvchi ILOVAGA KIRGAN — ro'yxatdan tanlash yo'q, kim ekani
#     login'dan aniq; rasm bilan tasdiqlash QOLADI ("baribir ozini
#     tasdiqlashi kerak rasm bilan chunki birovni nomidan boshqasi
#     ishlashi ham mumkin");
#   - imtihon o'z guruhi uchun ochilgan bo'lsa bosh sahifada va
#     bildirishnomada o'zi ko'rinadi — link shart emas; link kelsa ham
#     /t/<token> ilovaga yo'naltiradi;
#   - natija to'g'ridan-to'g'ri o'z qatoriga tushadi ("pending" yo'q).
# Javob saqlash/chiqish/topshirish — avvalgi public yo'llar (kalit
# bilan), ikki xil mantiq bo'lib ketmasin.

def _student_gids(db: Session, s) -> set:
    """O'quvchining guruhlari: asosiy + ko'p-guruh bog'lanishlari."""
    gids = {s.group_id} if s.group_id else set()
    try:
        for (gid,) in (db.query(models.StudentGroupLink.group_id)
                       .filter(models.StudentGroupLink.student_id == s.id,
                               models.StudentGroupLink.active == 1).all()):
            gids.add(gid)
    except Exception:
        db.rollback()
    return {g for g in gids if g}


def _my_sub(db: Session, exam_id: int, student_id: int):
    """O'quvchining shu imtihondagi eng so'nggi topshirig'i
    (in_progress > placed > qolganlar)."""
    subs = (db.query(models.ExamSubmission)
            .filter(models.ExamSubmission.exam_id == exam_id,
                    models.ExamSubmission.student_id == student_id)
            .order_by(models.ExamSubmission.id.desc()).all())
    for want in ("in_progress", "placed"):
        for x in subs:
            if x.status == want:
                return x
    return subs[0] if subs else None


def _student_exam_item(db: Session, o, exam, s, group=None) -> dict:
    finalize_expired(db, o, exam)
    group = group or db.query(models.Group).get(exam.group_id)
    is_open = bool(o.is_open) and _exam_open_for_results(exam)
    state = timer_state(o) if is_open else "closed"
    my = _my_sub(db, exam.id, s.id)
    my_status = my.status if my else "none"
    item = {
        "token": o.token, "exam_id": exam.id,
        "title": exam.title or roles.exam_title(exam.kind, exam.unit_no),
        "group": group.name if group else "", "kind": exam.kind,
        "unit_no": exam.unit_no,
        "date": exam.date.isoformat() if exam.date else None,
        "state": state, "starts_at": _iso(o.started_at),
        "ends_at": _iso(o.ends_at), "duration_min": o.duration_min,
        "q_count": int(o.online_max or 0), "paper_max": o.paper_max or 0,
        "my_status": my_status,
        "submitted_at": (my.submitted_at.isoformat()
                         if my and my.submitted_at else None),
        "published": bool(o.published_at),
    }
    # Natija faqat examiner e'lon qilgandan keyin (2026-09-18 qoidasi)
    if my and my.status == "placed" and o.published_at:
        total = (my.online_score or 0) + (my.paper_score or 0)
        mx = (my.online_max or 0) + (o.paper_max or 0)
        item["score"] = total
        item["max_score"] = mx
        item["percent"] = round(total * 100 / mx) if mx else None
    return item


def active_exams_for_student(db: Session, s) -> list:
    """Bosh sahifa va bildirishnoma uchun: hozir ochiq va hali
    topshirilmagan (yoki davom etayotgan) imtihonlar."""
    gids = _student_gids(db, s)
    if not gids:
        return []
    rows = (db.query(models.ExamOnline, models.Exam)
            .join(models.Exam, models.Exam.id == models.ExamOnline.exam_id)
            .filter(models.Exam.group_id.in_(list(gids)),
                    models.ExamOnline.is_open == 1)
            .all())
    out = []
    for o, exam in rows:
        if exam.status == "cancelled" or not _exam_open_for_results(exam):
            continue
        item = _student_exam_item(db, o, exam, s)
        if item["state"] in ("waiting", "countdown", "running") and \
                item["my_status"] in ("none", "in_progress"):
            out.append(item)
    out.sort(key=lambda x: (x["state"] != "running", x["title"]))
    return out


def _student_me(db: Session, user):
    from student_app import _me
    return _me(db, user)


@router.get("/api/student/exams/online")
def student_online_exams(db: Session = Depends(get_db),
                         user=Depends(require_role(roles.STUDENT))):
    """O'quvchining ONLINE imtihonlari: hozir ochiqlari + tarixi.
    (/api/student/exams — tasdiqlangan natijalar tarixi — student_app'da
    avvaldan bor, unga tegilmadi.)"""
    s = _student_me(db, user)
    gids = _student_gids(db, s)
    active, history = [], []
    if gids:
        rows = (db.query(models.ExamOnline, models.Exam)
                .join(models.Exam, models.Exam.id == models.ExamOnline.exam_id)
                .filter(models.Exam.group_id.in_(list(gids)))
                .order_by(models.Exam.date.desc(), models.Exam.id.desc())
                .all())
        for o, exam in rows:
            if exam.status == "cancelled":
                continue
            item = _student_exam_item(db, o, exam, s)
            if item["state"] in ("waiting", "countdown", "running") and \
                    item["my_status"] in ("none", "in_progress"):
                active.append(item)
            elif item["my_status"] != "none":
                history.append(item)
    active.sort(key=lambda x: (x["state"] != "running", x["title"]))
    return {"active": active, "history": history[:20]}


def _student_online(db: Session, token: str, s):
    o, exam = _public(db, token)
    if exam.group_id not in _student_gids(db, s):
        raise HTTPException(403, "Bu imtihon sizning guruhingiz uchun emas")
    return o, exam


@router.get("/api/student/exam/{token}")
def student_exam_state(token: str, db: Session = Depends(get_db),
                       user=Depends(require_role(roles.STUDENT))):
    """Ilovadagi imtihon sahifasi holati — public sahifa bilan bir xil
    tuzilma, lekin ro'yxat o'rniga "me" va o'zining topshirig'i
    (davom etayotgan bo'lsa kaliti bilan — telefon o'chib qolsa
    ham qayta kirib davom etadi)."""
    s = _student_me(db, user)
    o, exam = _student_online(db, token, s)
    finalize_expired(db, o, exam)
    group = db.query(models.Group).get(exam.group_id)
    is_open = bool(o.is_open) and _exam_open_for_results(exam)
    state = timer_state(o) if is_open else "closed"
    my = _my_sub(db, exam.id, s.id)
    mine = None
    if my:
        mine = {"status": my.status,
                "key": my.sub_key if my.status == "in_progress" else None,
                # Boshqa telefondan kirsa — javoblari qaytib keladi
                "answers": (_load_dict(my.answers)
                            if my.status == "in_progress" else None),
                "submitted_at": (my.submitted_at.isoformat()
                                 if my.submitted_at else None),
                "pending": my.status not in ("placed",),
                "paper_max": o.paper_max or 0}
    strict = is_strict(exam)
    return {
        "title": exam.title or roles.exam_title(exam.kind, exam.unit_no),
        "group": group.name if group else "",
        "date": exam.date.isoformat() if exam.date else None,
        "strict": strict,                      # faqat mock (2026-09-27)
        "away_limit": away_limit_of(o, exam) if strict else None,
        "is_open": is_open, "state": state,
        "server_now": _iso(datetime.utcnow()),
        "starts_at": _iso(o.started_at), "ends_at": _iso(o.ends_at),
        "duration_min": o.duration_min,
        "q_count": int(o.online_max or 0), "paper_max": o.paper_max or 0,
        "students": [],
        "parts": (_parts_for(exam, _load(o.parts),
                             my.sub_key if my else None)
                  if is_open and state == "running" else []),
        "me": {"id": s.id, "name": s.full_name},
        "my": mine,
    }


class AppBeginIn(BaseModel):
    photo: str


@router.post("/api/student/exam/{token}/begin")
def student_exam_begin(token: str, payload: AppBeginIn, request: Request,
                       db: Session = Depends(get_db),
                       user=Depends(require_role(roles.STUDENT))):
    """Ilovadan kirish: kim ekani login'dan, rasm — tasdiq uchun.
    Davom etayotgan topshirig'i bo'lsa o'sha kalit qaytadi (ikkinchi
    yozuv ochilmaydi)."""
    s = _student_me(db, user)
    o, exam = _student_online(db, token, s)
    if is_strict(exam):
        deny_mobile(request)       # mock faqat kompyuterda (2026-09-27)
    ip = _client_ip(request)
    if not _rate_ok(ip or "?"):
        raise HTTPException(429, "Juda ko'p urinish — birozdan keyin qayta "
                                 "urinib ko'ring")
    if not o.is_open or not _exam_open_for_results(exam) or \
            timer_state(o) == "finished":
        raise HTTPException(410, "Test yopilgan")
    cur = _my_sub(db, exam.id, s.id)
    if cur and cur.status == "in_progress":
        return {"ok": True, "key": cur.sub_key, "name": s.full_name,
                "resumed": True}
    if cur and cur.status in ("placed", "duplicate", "pending"):
        raise HTTPException(409, "Siz bu testni allaqachon topshirgansiz")
    if cur and cur.status == "expelled":
        raise HTTPException(403, "Siz bu testdan chetlatilgansiz")
    photo = payload.photo or ""
    if not photo.startswith("data:image/") or len(photo) > PHOTO_MAX_CHARS:
        raise HTTPException(400, "Kameradan rasm oling")
    sub = models.ExamSubmission(
        exam_id=exam.id, student_id=s.id, typed_name=s.full_name,
        photo=photo, answers="{}", status="in_progress", ip=ip[:64],
        online_max=o.online_max or 0, sub_key=secrets.token_urlsafe(16))
    db.add(sub)
    db.commit()
    return {"ok": True, "key": sub.sub_key, "name": s.full_name,
            "resumed": False}


# ------------------------------------------------ savol MAVZULARI (#177)
# 2026-09-26. @jonybazabaza kanalidagi test bazasi (Step 1/2/3 unit,
# mid, end — 1 585 savol) 42 ta shablonga to'liq mos ekani javob
# kalitlari bilan tekshirildi; har savolga mavzu belgilandi:
# "Listening · Short replies", "Vocabulary · Food and drink",
# "Grammar · Present simple" … (exam_topics.json — shablon kaliti ->
# bo'limlar -> savollar tartibida). Keyin o'quvchi/guruh/ustoz
# kesimida qaysi mavzuda ko'p xato qilinishi shu orqali chiqadi.
_TOPICS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "exam_topics.json")
_TOPICS_CACHE: Optional[dict] = None


def _bank_topics() -> dict:
    """{shablon kaliti: [[mavzu, ...] har bo'lim uchun]}"""
    global _TOPICS_CACHE
    if _TOPICS_CACHE is None:
        try:
            with open(_TOPICS_FILE, encoding="utf-8") as f:
                _TOPICS_CACHE = json.load(f)
        except Exception:
            _TOPICS_CACHE = {}
    return _TOPICS_CACHE


def _bank_topic_names() -> list:
    names = set()
    for parts in _bank_topics().values():
        for arr in parts:
            names.update(x for x in arr if x)
    return sorted(names)


def _apply_topics_by_position(parts: list, topics: list) -> int:
    """Seed'dan yaratilayotgan shablon: mavzular tartib bo'yicha."""
    n = 0
    for p, arr in zip(parts, topics or []):
        for q, t in zip(p.get("questions") or [], arr or []):
            if t and not q.get("topic"):
                q["topic"] = t
                n += 1
    return n


def _qsig(q: dict) -> str:
    """Savolni tanib olish imzosi — matn + variantlar (tartib va
    raqamdan qat'i nazar)."""
    return _norm(q.get("q") or "") + "|" + "|".join(
        _norm(o) for o in (q.get("options") or []))


def _seed_topic_index() -> dict:
    """{(level, kind, unit_no): {imzo: mavzu}} — jonli bazadagi
    (allaqachon yaratilgan, ehtimol tahrirlangan) shablonlarga mavzu
    qo'yish uchun savol matni bo'yicha moslashtiriladi."""
    import exam_bank_seed
    topics = _bank_topics()
    out = {}
    for key, tpl in exam_bank_seed.TEMPLATES:
        tp = topics.get(key)
        if not tp:
            continue
        idx = {}
        for p, arr in zip(tpl["parts"], tp):
            for q, t in zip(p.get("questions") or [], arr):
                if t:
                    idx.setdefault(_qsig(q), t)
        out[(tpl["level"], tpl["kind"], tpl.get("unit_no"))] = idx
    return out


def _fill_topics_in_parts(parts: list, idx: dict) -> int:
    n = 0
    for q in _questions(parts):
        if q.get("topic"):
            continue
        t = idx.get(_qsig(q))
        if t:
            q["topic"] = t
            n += 1
    return n


def fill_topics_from_bank(db: Session, key: str = "exam_topics_v1") -> int:
    """BIR MARTALIK: jonli bazadagi shablonlarga va ochilgan linklar
    nusxasiga (o'tgan imtihonlar tahlili uchun) mavzu qo'yadi. Faqat
    mavzusi bo'sh savollarga, matni seed bilan aynan mos kelsa —
    examiner tahrirlagan savol tegilmaydi (hech narsa o'chirilmaydi)."""
    if _seed_done(db, key):
        return 0
    filled = 0
    try:
        index = _seed_topic_index()
        if not index:
            # exam_topics.json o'qilmadi (deployda yo'q?) — belgi
            # qo'yilmaydi, keyingi startda qayta uriniladi
            print("[exam-bank] mavzular fayli topilmadi — o'tkazib yuborildi",
                  flush=True)
            return 0
        for t in db.query(models.ExamTemplate).all():
            idx = index.get((t.level, t.kind, t.unit_no))
            if not idx:
                continue
            parts = _load(t.parts)
            n = _fill_topics_in_parts(parts, idx)
            if n:
                t.parts = json.dumps(parts, ensure_ascii=False)
                filled += n
        for o in db.query(models.ExamOnline).all():
            exam = db.query(models.Exam).get(o.exam_id)
            group = db.query(models.Group).get(exam.group_id) if exam else None
            if not exam or not group:
                continue
            idx = index.get((group.level, exam.kind, exam.unit_no))
            if not idx:
                continue
            parts = _load(o.parts)
            n = _fill_topics_in_parts(parts, idx)
            if n:
                o.parts = json.dumps(parts, ensure_ascii=False)
                filled += n
        db.commit()
        _seed_mark(db, key)
        print(f"[exam-bank] mavzular qo'yildi: {filled} ta savol", flush=True)
    except Exception as e:  # noqa: BLE001
        db.rollback()
        print(f"[exam-bank] mavzular qo'yilmadi: {e}", flush=True)
    return filled


# ------------------------------------------------ VARIANTLAR (B, C, D, E)
# 2026-09-26, Jahongir: "shu savollarni 4-5 xil variantini tayyorlab
# qoyish kerak chunki ustozlar aynan testga tayyorlash holatlari
# kuzatilyabdi". exam_bank_variants.json: {shablon kaliti: {"B": parts,
# "C": parts, ...}} — asl (A) bilan bir xil tuzilish (bo'lim/savol soni,
# tur, mavzu), lekin boshqa savollar; listening bo'limida examiner
# o'qib beradigan `script`. Fayl bosqichma-bosqich to'ladi — har
# (kalit, harf) alohida belgi bilan bir marta yoziladi.
_VARIANTS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                              "exam_bank_variants.json")


def _bank_variants() -> dict:
    try:
        with open(_VARIANTS_FILE, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def seed_variants(db: Session) -> int:
    """Faylga qo'shilgan yangi variantlarni bazaga yozadi (idempotent).
    Asl shablon (A) tegilmaydi; mavjud (level, kind, unit, variant)
    qayta yaratilmaydi — examiner tahrirlagan bo'lsa shu qoladi."""
    import exam_bank_seed
    data = _bank_variants()
    if not data:
        return 0
    # Parallel sovuq startlar (Vercel 2–4 instansiya) bir vaqtda yozib
    # dublikat qilmasin — Postgres sessiya qulfi (commit'lar orasida ham
    # turadi; oxirida bo'shatiladi)
    locked = False
    try:
        from sqlalchemy import text as _sql
        if db.bind.dialect.name == "postgresql":
            locked = bool(db.execute(_sql("SELECT pg_try_advisory_lock(:k)"),
                                     {"k": 20260926}).scalar())
            if not locked:
                return 0
    except Exception:
        db.rollback()
    try:
        return _seed_variants_locked(db, data, exam_bank_seed)
    finally:
        if locked:
            try:
                db.execute(_sql("SELECT pg_advisory_unlock(:k)"), {"k": 20260926})
                db.commit()
            except Exception:
                db.rollback()


def _dup_key(t: models.ExamTemplate) -> tuple:
    """Qaysi shablonlar bir-birining DUBLIKATI hisoblanadi.

    Unit / Mid / End: bitta (daraja, tur, unit, variant) = bitta test.

    MOCK (2026-09-27 tuzatildi). Mockda unit yo'q, variant harfi esa
    BO'LIM ichida: IELTS Listening A, Reading A, Writing A, Speaking A —
    to'rtta boshqa-boshqa test. Eski kalit ularni bitta deb hisoblab,
    eng eskisidan (Listening) boshqasini har startda yashirardi.
    Jahongir: "nega bu yerda IELTS da faqat listening turibdi, qolgani
    qani". Endi mock faqat sarlavhasi VA variant harfi ham bir xil
    bo'lsa dublikat (parallel sovuq startlar bir shablonni ikki marta
    yozgan holat). Variant kalitda qoladi: examiner bitta nom bilan
    A, B, C parallel variant yaratadi (tahrirlagich shunday ishlaydi)
    va ular linkda aralashadi — ular dublikat emas.
    """
    if (t.kind or "") == "mock":
        import mock_seed
        return (t.level, t.kind, mock_seed.canon_title(t.title), t.variant)
    return (t.level, t.kind, t.unit_no, t.variant)


def dedupe_templates(db: Session) -> int:
    """Avvalgi startlarda dublikat tushib qolgan bo'lsa — keyingilarini
    yashiradi (o'chirilmaydi: o'tkazilgan imtihonlar shablonga FK bilan
    bog'langan). Eng eski yozuv (kichik id) qoladi."""
    seen, n = {}, 0
    for t in (db.query(models.ExamTemplate)
              .filter(models.ExamTemplate.variant.isnot(None),
                      models.ExamTemplate.is_active == 1)
              .order_by(models.ExamTemplate.id).all()):
        k = _dup_key(t)
        if k in seen:
            t.is_active = 0
            t.title = (t.title or "") + " (dublikat)"
            n += 1
            print(f"[exam-bank] dublikat variant yashirildi: {t.title}",
                  flush=True)
        else:
            seen[k] = t.id
    db.commit()
    return n


def _seed_variants_locked(db: Session, data: dict, exam_bank_seed) -> int:
    meta = {key: tpl for key, tpl in exam_bank_seed.TEMPLATES}
    made = 0
    dedupe_templates(db)
    for key, letters in data.items():
        tpl = meta.get(key)
        if not tpl:
            continue
        for letter, parts in sorted(letters.items()):
            mark = f"{key}:var{letter}"
            if _seed_done(db, mark):
                continue
            exists = db.query(models.ExamTemplate).filter(
                models.ExamTemplate.level == tpl["level"],
                models.ExamTemplate.kind == tpl["kind"],
                models.ExamTemplate.unit_no == tpl.get("unit_no"),
                models.ExamTemplate.variant == letter).first()
            if not exists:
                try:
                    clean = clean_parts(parts)
                except HTTPException as e:
                    print(f"[exam-bank] variant {key} {letter} xato: {e.detail}",
                          flush=True)
                    continue
                db.add(models.ExamTemplate(
                    level=tpl["level"], kind=tpl["kind"],
                    unit_no=tpl.get("unit_no"),
                    title=f"{tpl['title']} — {letter} varianti",
                    parts=json.dumps(clean, ensure_ascii=False),
                    paper_max=tpl.get("paper_max", 0), variant=letter,
                    created_by="JonyOS"))
                db.commit()
                made += 1
            _seed_mark(db, mark)
    if made:
        print(f"[exam-bank] variantlar yozildi: {made} ta shablon", flush=True)
    return made


# ------------------------------------------------ boshlang'ich test bazasi
def seed_templates(db: Session) -> None:
    """Jahongir yuborgan testlar (Step 1 Unit 1 …) bazaga bir marta
    yoziladi. Keyin examinerlar boshlig'i o'zi tahrirlaydi."""
    import exam_bank_seed
    # Tasdiqlash qo'shilishidan OLDINGI linklar natijalari allaqachon
    # guruh testida — ular tasdiqlangan hisoblanadi (bir martalik)
    if not _seed_done(db, "exam_online_publish_legacy_v1"):
        try:
            (db.query(models.ExamOnline)
             .filter(models.ExamOnline.published_at.is_(None))
             .update({models.ExamOnline.published_at: datetime.utcnow(),
                      models.ExamOnline.published_by: "avvalgi tartib"},
                     synchronize_session=False))
            db.commit()
            _seed_mark(db, "exam_online_publish_legacy_v1")
        except Exception:
            db.rollback()
    for key, tpl in exam_bank_seed.TEMPLATES:
        if _seed_done(db, key):
            continue
        exists = db.query(models.ExamTemplate).filter(
            models.ExamTemplate.level == tpl["level"],
            models.ExamTemplate.kind == tpl["kind"],
            models.ExamTemplate.unit_no == tpl.get("unit_no")).first()
        if not exists:
            parts = clean_parts(tpl["parts"])
            _apply_topics_by_position(parts, _bank_topics().get(key))
            db.add(models.ExamTemplate(
                level=tpl["level"], kind=tpl["kind"],
                unit_no=tpl.get("unit_no"), title=tpl["title"],
                parts=json.dumps(parts, ensure_ascii=False),
                paper_max=tpl.get("paper_max", 0), variant="A",
                created_by="JonyOS"))
            db.commit()
        _seed_mark(db, key)
    fill_exam_max_from_bank(db)
    fill_mid_end_100(db)
    fill_topics_from_bank(db)
    try:
        seed_variants(db)
    except Exception as e:  # noqa: BLE001
        db.rollback()
        print(f"[exam-bank] variantlar yozilmadi: {e}", flush=True)
    try:
        seed_math(db)
    except Exception as e:  # noqa: BLE001
        db.rollback()
        print(f"[exam-bank] matematika yozilmadi: {e}", flush=True)


def seed_math(db: Session) -> int:
    """MATEMATIKA bazasi (2026-09-26, Jahongir: "endi matematikanini
    ozing tuzib qoy baza qildib bo'l tez"): 3 daraja × (12 unit + mid +
    end) × 5 variant = 210 shablon, protsedura bilan (math_bank.py).
    Har shablon uchun alohida belgi — bir marta yoziladi; examiner
    keyin tahrirlasa tegilmaydi. Parallel startlar uchun qulf."""
    import math_bank
    locked = False
    try:
        from sqlalchemy import text as _sql
        if db.bind.dialect.name == "postgresql":
            locked = bool(db.execute(_sql("SELECT pg_try_advisory_lock(:k)"),
                                     {"k": 20260927}).scalar())
            if not locked:
                return 0
    except Exception:
        db.rollback()
    made = 0
    started = time.time()
    try:
        # Mavjudlarini bitta so'rovda olamiz (210 ta alohida so'rov emas)
        have = {(t.level, t.kind, t.unit_no, t.variant or "A")
                for t in db.query(models.ExamTemplate)
                .filter(models.ExamTemplate.subject == math_bank.SUBJECT).all()}
        pending = 0
        for level, kind, unit_no in math_bank.all_keys():
            for letter in math_bank.VARIANTS:
                mark = f"math:{level}:{kind}:{unit_no or 0}:{letter}"
                if _seed_done(db, mark):
                    continue
                if (level, kind, unit_no, letter) not in have:
                    t = math_bank.build(level, kind, unit_no, letter)
                    db.add(models.ExamTemplate(
                        level=level, kind=kind, unit_no=unit_no,
                        title=t["title"],
                        parts=json.dumps(clean_parts(t["parts"]),
                                         ensure_ascii=False),
                        paper_max=0, variant=letter,
                        subject=math_bank.SUBJECT, created_by="JonyOS"))
                    made += 1
                db.add(models.SeedMark(key=mark))
                # Jarayon xotirasidagi belgilar keshini ham yangilaymiz —
                # aks holda shu jarayonda ikkinchi chaqiruv dublikat
                # belgi yozmoqchi bo'lib UNIQUE xatosiga uchraydi
                if _common._SEED_KEYS is not None:
                    _common._SEED_KEYS.add(mark)
                pending += 1
                if pending >= 15:
                    db.commit()
                    pending = 0
                    # Sovuq startni cho'zmaslik: byudjet tugasa keyingi
                    # startda davom etadi (belgilar yozilgan)
                    if time.time() - started > 8:
                        print(f"[exam-bank] matematika: {made} ta yozildi, "
                              f"davomi keyingi startda", flush=True)
                        return made
        db.commit()
        if made:
            print(f"[exam-bank] matematika yozildi: {made} ta shablon", flush=True)
    finally:
        if locked:
            try:
                db.execute(_sql("SELECT pg_advisory_unlock(:k)"), {"k": 20260927})
                db.commit()
            except Exception:
                db.rollback()
    return made


def fill_mid_end_100(db: Session, key: str = "exam_mid_end_100_v1"):
    """BIR MARTALIK (2026-09-25): o'tish va yakuniy testlarning
    maksimal balini 100 ga tenglaydi.

    Faqat natijasi KIRITILMAGAN, linki ochilmagan va bekor
    qilinmagan testlar — natijasi borlarining foizi va coini
    o'zgarib ketmasin. Shablonlarda qog'oz qismi ham to'ldiriladi:
    online savollar soni + qog'oz = 100."""
    if _seed_done(db, key):
        return 0
    changed = 0
    try:
        for t in (db.query(models.ExamTemplate)
                  .filter(models.ExamTemplate.kind.in_(("mid", "end")))
                  .all()):
            if _subj(t) != "english":
                continue        # matematikada qog'oz qismi yo'q
            n = float(sum(1 for _ in _questions(_load(t.parts))))
            want = max(0.0, MID_END_TOTAL - n)
            if not (t.paper_max or 0) and want > 0:
                t.paper_max = want
        linked = {o.exam_id for o in db.query(models.ExamOnline).all()}
        for ex in (db.query(models.Exam)
                   .filter(models.Exam.kind.in_(("mid", "end"))).all()):
            if ex.status == "cancelled" or ex.id in linked:
                continue
            if any(not r.absent and (r.score is not None
                                     or r.band is not None)
                   for r in ex.results):
                continue
            if (ex.max_score or 0) != MID_END_TOTAL:
                ex.max_score = MID_END_TOTAL
                changed += 1
        db.commit()
        _seed_mark(db, key)
        print(f"[exam-bank] mid/end 100 ballik: {changed} ta imtihon")
    except Exception as e:  # noqa: BLE001
        db.rollback()
        print(f"[exam-bank] mid/end 100 ballik yangilanmadi: {e}")
    return changed


def fill_exam_max_from_bank(db: Session, key: str = "exam_max_from_bank_v1"):
    """BIR MARTALIK: mavjud imtihonlarning maksimal balini test bazasidagi
    savollar soniga tenglaydi. Faqat natija kiritilmagan, link ochilmagan
    va bekor qilinmagan Unit / Mid / End testlar — natijasi borlarining
    foizi va coini o'zgarib ketmasin."""
    if _seed_done(db, key):
        return 0
    changed = 0
    try:
        linked = {o.exam_id for o in db.query(models.ExamOnline).all()}
        groups = {}
        for ex in (db.query(models.Exam)
                   .filter(models.Exam.kind.in_(("unit", "mid", "end")))
                   .all()):
            if ex.status == "cancelled" or ex.id in linked:
                continue
            if any(not r.absent and (r.score is not None or r.band is not None)
                   for r in ex.results):
                continue
            if ex.group_id not in groups:
                groups[ex.group_id] = db.query(models.Group).get(ex.group_id)
            mx = bank_max(db, groups[ex.group_id], ex.kind, ex.unit_no)
            if mx and ex.max_score != mx:
                ex.max_score = mx
                changed += 1
        db.commit()
        _seed_mark(db, key)
        print(f"[exam-bank] maksimal ball yangilandi: {changed} ta imtihon")
    except Exception as e:  # noqa: BLE001
        db.rollback()
        print(f"[exam-bank] maksimal ball yangilanmadi: {e}")
    return changed
