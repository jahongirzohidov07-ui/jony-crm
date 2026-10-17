"""LUG'AT BANKI — "So'z bilish" SERTIFIKATLARI (2026-10-17, 3-bosqich).

Sabab (Jahongir, OWNER_DECISIONS D3, "tasdiqlangandan keyin chiqsin"):
natijaga erishgan o'quvchi (IELTS, CEFR/Multilevel, SAT, Duolingo,
TOEFL, Cambridge, TOPIK, Goethe, TORFL, boshqa) sertifikatini PROFILDA
yuklaydi. Natija (profil — "So'z bilish: N" yonida, reyting, ota-ona)
FAQAT xodim tasdiqlagach "tasdiqlangan" belgisi bilan chiqadi. Undan
oldin o'quvchi o'zi faqat "Yuklandi — tekshirilmoqda" ni ko'radi (BALL
YO'Q), boshqalar hech narsani ko'rmaydi.

Shartnoma: scratchpad/vocab/PHASE23_CONTRACT.md §6. Bu yerda:
  * O'QISH yordamchilari (badge_out, confirmed_badges, latest_badges,
    cert_badge_for, pending_count) — boshqa modullar (wordbank_social,
    wordbank.py /me, ota-ona) natijani FAQAT shular orqali o'qiydi va
    ular faqat status="confirmed" qatorni beradi. Imzo va ma'no
    o'zgartirilmaydi.
  * o'quvchi yo'llari (/api/wordbank/certs/mine...) — darvoza
    wordbank._student (bo'lim o'chiq / filial yoqilmagan — 404) HAMMA
    tekshiruvdan oldin;
  * xodim navbati (/api/wordbank/certs...) — tasdiqlash / rad etish /
    bekor qilish, chegara: ustoz — FAQAT o'z guruhlari o'quvchisi,
    filial rahbari / administrator — o'z filiali, o'quv bo'limi rahbari
    va asoschi — butun markaz. Chegaradan tashqaridagi yozuv — 404
    (borligi ham bilinmasin).

Xavfsizlik va qoidalar:
  * fayl turi mijoz aytganidan EMAS, fayl boshidagi baytlardan
    aniqlanadi (JPEG / PNG / WEBP / PDF); boshqa hamma narsa — 415;
    hajm 3 MB gacha (MAX_BYTES + 1 baytdan ortiq o'qilmaydi);
  * fayl javobi: nosniff, inline, CSP sandbox, no-store — brauzer uni
    sahifa sifatida bajarmaydi;
  * bir o'quvchida bir xil fayl (sha256) kutilayotgan yoki tasdiqlangan
    holda ikki marta bo'lmaydi; rad etilgandan keyin qayta yuklash
    mumkin. Boshqa o'quvchida xuddi shu fayl bo'lsa — qabul qilinadi,
    lekin xodim navbatida qizil ogohlantirish chiqadi;
  * cheklovlar: bir vaqtda 3 ta kutilayotgan, 30 kunda 10 ta yuklama;
    test sanasi kelajakda emas va 5 yildan eski emas;
  * holat almashishi SHARTLI UPDATE bilan (WHERE status = ...): ikki
    xodim bir vaqtda bossa ham Certificate bitta yaratiladi, ikkinchisi
    409;
  * bildirishnomalarda tasdiqlanmagan ball HECH QACHON yo'q: ustozga
    faqat "Yangi sertifikat tekshiruvga yuklandi: {ism}".

Saqlash: Attachment(entity="vocab_cert", entity_id=upload.id, base64) —
R2 2-bosqichi hali yoqilmagan. Umumiy /api/attachments bu fayllarni
bermaydi (audit_admin._PRIVATE_ENTITIES). Jadval qatorlari va fayllar
hech qachon o'chirilmaydi (D4) — students._PURGE_KEEP_TABLES ga qarang.
"""
import base64
import functools
import hashlib
import itertools
import json
import math
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import date, datetime, timedelta
from types import SimpleNamespace

from fastapi import APIRouter, Body, Depends, HTTPException, Request, Response
from sqlalchemy import case, func, or_, select, update as sa_update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, aliased

import audit
import common
import models
import roles
import wordbank as WB
from auth import get_current_user, has_role
from database import get_db

router = APIRouter()

CU = models.WordbankCertUpload

ATTACH_ENTITY = "vocab_cert"         # Attachment.entity
MAX_BYTES = 3 * 1024 * 1024          # fayl chegarasi (3 MB)
MAX_PENDING = 3                      # bir vaqtda kutilayotgan yuklamalar
MAX_PER_30D = 10                     # 30 kunda jami yuklamalar
MAX_AGE_YEARS = 5                    # test sanasi 5 yildan eski bo'lmasin
CONFIRMED = "confirmed"
PENDING = "pending"
REJECTED = "rejected"
WITHDRAWN = "withdrawn"
REVOKED = "revoked"

_IN_CHUNK = 500                      # IN (...) ro'yxatini bo'lib so'rash
_ID_MAX = 2 ** 31 - 1                # id INTEGER ustuni chegarasi
LIST_LIMIT = 500                     # xodim navbatida bir so'rovda eng ko'p
NOTE_MAX = 500                       # izohlar uzunligi
TEACHER_URL = "/vocab-certs"         # ustoz bildirishnomasi ochadigan sahifa
STUDENT_URL = "/student/profile"

DUPLICATE_WARNING = "bu fayl boshqa o'quvchi tomonidan ham yuklangan"
STATUS_LABEL = {
    PENDING: "Yuklandi — tekshirilmoqda",
    CONFIRMED: "Tasdiqlangan",
    REJECTED: "Rad etildi",
    WITHDRAWN: "Qaytarib olindi",
    REVOKED: "Bekor qilindi",
}


def _ids(student_ids) -> list:
    out = []
    for x in student_ids or []:
        try:
            out.append(int(x))
        except (TypeError, ValueError):
            continue
    return sorted(set(out))


def _sort_key(u):
    """Eng oxirgisi birinchi: test sanasi, keyin tasdiqlangan vaqt, id.
    NULL sanalar Python'da tartiblanadi (SQLite va Postgres NULL'ni har
    xil joylashtiradi)."""
    return (u.test_date or date.min, u.reviewed_at or datetime.min, u.id)


def badge_out(u) -> dict:
    """Tasdiqlangan sertifikatning ommaviy ko'rinishi (o'quvchi, reyting,
    ota-ona, ustoz ro'yxati). FAQAT status="confirmed" qatorga ishlatiladi."""
    return {
        "id": u.id,
        "exam_type": u.exam_type,
        "exam_label": roles.VOCAB_CERT_EXAM_LABELS.get(u.exam_type,
                                                       u.exam_type),
        "label": u.result_label or roles.VOCAB_CERT_EXAM_LABELS.get(
            u.exam_type, u.exam_type),
        "test_date": u.test_date.isoformat() if u.test_date else None,
    }


# CRM SERTIFIKATLARI (2026-10-17, Jahongir: "Ha, chiqsin"): xodim o'quvchi
# kartasiga qo'shgan IELTS / CEFR sertifikati xodim kiritgani uchun
# tasdiqlangan hisoblanadi va So'z bilish'da ham chiqadi (profil, reyting,
# ota-ona). Ichki / kurs / olimpiada / boshqa turlari chiqmaydi. Yuklamani
# tasdiqlash ham Certificate yaratadi (certificate_id) — u yuklama orqali
# ko'rinadi, shuning uchun bu yerda ikkinchi marta olinmaydi.
CRM_KINDS = ("ielts", "cefr")


def crm_badge_out(c) -> dict:
    """CRM Certificate qatori -> badge_out bilan bir xil ko'rinish. id
    manfiy: yuklama id'lari bilan to'qnashmasin."""
    lvl = (c.level or "").strip()
    sc = c.score
    if c.kind == "ielts":
        val = lvl or (f"{sc:.1f}" if sc is not None else "")
        et, name, label = "ielts", "IELTS", f"IELTS {val}".strip()
    else:
        multi = "multilevel" in (c.note or "").lower()
        et = "multilevel" if multi else "cefr_other"
        name = "Multilevel" if multi else "CEFR"
        sc_s = f"{sc:g}" if sc is not None else ""
        label = f"{name} {lvl or sc_s}".strip()
        if lvl and sc_s and sc_s != lvl:
            label += f" ({sc_s})"
    return {"id": -int(c.id), "exam_type": et, "exam_label": name,
            "label": label,
            "test_date": c.date.isoformat() if c.date else None}


def _crm_rows(db: Session, ids) -> list:
    C = models.Certificate
    linked = select(CU.certificate_id).where(CU.certificate_id.isnot(None))
    q = db.query(C).filter(C.kind.in_(CRM_KINDS), ~C.id.in_(linked))
    if ids is None:
        return q.all()
    out = []
    for i in range(0, len(ids), _IN_CHUNK):
        out += q.filter(C.student_id.in_(ids[i:i + _IN_CHUNK])).all()
    return out


def confirmed_badges(db: Session, student_ids=None) -> dict:
    """{student_id: [badge_out, ...]} — eng oxirgisi birinchi. FAQAT
    tasdiqlanganlar: pending / rejected / withdrawn / revoked natijasi
    bu yerdan HECH QACHON chiqmaydi. student_ids=None — hammasi.
    2026-10-17: xodim kiritgan CRM IELTS/CEFR sertifikatlari ham (yuqorida)."""
    rows = []
    ids = None if student_ids is None else _ids(student_ids)
    if ids is None:
        rows = db.query(CU).filter(CU.status == CONFIRMED).all()
    else:
        for i in range(0, len(ids), _IN_CHUNK):
            rows += (db.query(CU)
                     .filter(CU.student_id.in_(ids[i:i + _IN_CHUNK]),
                             CU.status == CONFIRMED).all())
    items = [(_sort_key(u), int(u.student_id), badge_out(u)) for u in rows]
    for c in _crm_rows(db, ids):
        items.append(((c.date or date.min, c.created_at or datetime.min, 0),
                      int(c.student_id), crm_badge_out(c)))
    out: dict = {}
    for _k, sid, b in sorted(items, key=lambda x: x[0], reverse=True):
        out.setdefault(sid, []).append(b)
    return out


def latest_badges(db: Session, student_ids=None) -> dict:
    """{student_id: "IELTS 7.0"} — har o'quvchining oxirgi TASDIQLANGAN
    sertifikati yorlig'i (reyting qatori uchun)."""
    return {sid: b[0]["label"]
            for sid, b in confirmed_badges(db, student_ids).items() if b}


def cert_badge_for(db: Session, student_id: int):
    """Bitta o'quvchining oxirgi tasdiqlangan sertifikati yorlig'i yoki
    None (wordbank_hall.cert_badge shundan yoziladi)."""
    return latest_badges(db, [student_id]).get(int(student_id))


def pending_count(db: Session, student_id: int) -> int:
    """Kutilayotgan yuklamalar SONI (natijasiz) — /api/wordbank/me
    "certs_pending" uchun."""
    return int(db.query(CU.id)
               .filter(CU.student_id == int(student_id),
                       CU.status == PENDING).count())


# =================================================== NATIJA TEKSHIRUVI ===
# 2026-10-17: shartnoma §6.3 — imtihon turiga qarab qaysi maydon kerak,
# chegarasi va yorlig'i. UI (wordbankApi.ts CERT_RULES) aynan shu
# qoidani takrorlaydi; server baribir o'zi tekshiradi va result_label ni
# O'ZI yasaydi (mijoz yuborgan yorliq ishlatilmaydi).
_CEFR = ("A1", "A2", "B1", "B2", "C1", "C2")
_CAMBRIDGE = ("A2 Key", "B1 Preliminary", "B2 First", "C1 Advanced",
              "C2 Proficiency")
_TOPIK = ("1", "2", "3", "4", "5", "6")
_IELTS_SUBS = ("L", "R", "W", "S")
_CTRL = re.compile(r"[\x00-\x1f\x7f]")


def _bad(msg: str):
    raise HTTPException(400, msg)


def _txt(v, maxlen: int, msg: str):
    """Erkin matn: bo'shliqlar siqiladi, boshqaruv belgilari olinadi.
    Bo'sh — None; uzun — 400."""
    if v is None:
        return None
    if not isinstance(v, (str, int, float)) or isinstance(v, bool):
        _bad(msg)
    s = " ".join(_CTRL.sub(" ", str(v)).split())
    if not s:
        return None
    if len(s) > maxlen:
        _bad(msg)
    return s


def _num(v, msg: str):
    """Son: 7 / 7.5 / "7,5". Bo'sh — None; son emas, NaN, cheksiz — 400."""
    if v is None or isinstance(v, bool):
        if isinstance(v, bool):
            _bad(msg)
        return None
    if isinstance(v, (int, float)):
        x = float(v)
    elif isinstance(v, str):
        s = v.strip().replace(",", ".")
        if not s:
            return None
        try:
            x = float(s)
        except ValueError:
            _bad(msg)
    else:
        _bad(msg)
    if math.isnan(x) or math.isinf(x):
        _bad(msg)
    return x


def _on_step(x, lo, hi, step) -> bool:
    if x is None or x < lo - 1e-9 or x > hi + 1e-9:
        return False
    q = x / step
    return abs(q - round(q)) < 1e-6


def _need(x, lo, hi, step, msg):
    if not _on_step(x, lo, hi, step):
        _bad(msg)
    return round(x / step) * step


def _pick(v, options, msg, upper=False):
    """Ro'yxatdan tanlov (katta-kichik harf farqsiz) — kanonik yozuv."""
    s = _txt(v, 60, msg)
    if s is None:
        _bad(msg)
    key = s.upper() if upper else s.lower()
    for o in options:
        if (o.upper() if upper else o.lower()) == key:
            return o
    _bad(msg)


def _i(x) -> str:
    return str(int(round(x)))


def _subs_in(v):
    """IELTS bo'limlari: {"L": 7.5, ...} yoki shu ko'rinishdagi JSON
    matn. Har biri 0–9, 0.5 qadam. Bo'sh — None."""
    msg = "IELTS bo'limlari (L, R, W, S) 0 dan 9 gacha, 0.5 qadam bilan"
    if v is None:
        return None
    if isinstance(v, str):
        if not v.strip():
            return None
        try:
            v = json.loads(v)
        except ValueError:
            _bad(msg)
    if v is None:
        return None
    if not isinstance(v, dict):
        _bad(msg)
    out = {}
    for k, val in v.items():
        key = str(k).strip().upper()
        if key not in _IELTS_SUBS:
            _bad(msg)
        x = _num(val, msg)
        if x is None:
            continue
        out[key] = _need(x, 0, 9, 0.5, msg)
    if not out:
        return None
    return {k: out[k] for k in _IELTS_SUBS if k in out}


def validate_result(exam_type, exam_name=None, score=None, level=None,
                    sub_scores=None, cert_no=None) -> dict:
    """Imtihon natijasini tekshiradi va saqlanadigan qiymatlarni
    qaytaradi: exam_type, exam_name, score, level, sub_scores (JSON
    matn yoki None), result_label, cert_no. Turga kerak bo'lmagan
    maydonlar None bo'ladi. Xato — HTTPException(400)."""
    et = exam_type.strip().lower() if isinstance(exam_type, str) else None
    if et not in roles.VOCAB_CERT_EXAM_LABELS:
        _bad("Imtihon turini tanlang")
    cno = _txt(cert_no, 40, "Sertifikat raqami 40 belgidan oshmasin")
    name = lvl = sc = subs = None
    if et == "ielts":
        sc = _need(_num(score, "IELTS balini kiriting"), 1, 9, 0.5,
                   "IELTS bali 1.0 dan 9.0 gacha, 0.5 qadam bilan")
        subs = _subs_in(sub_scores)
        label = f"IELTS {sc:.1f}"
    elif et == "multilevel":
        lvl = _pick(level, _CEFR, "Darajani tanlang (A1–C2)", upper=True)
        sc = _need(_num(score, "Multilevel balini kiriting"), 0, 75, 1,
                   "Multilevel bali 0 dan 75 gacha butun son")
        label = f"Multilevel {lvl} ({_i(sc)})"
    elif et == "cefr_other":
        lvl = _pick(level, _CEFR, "Darajani tanlang (A1–C2)", upper=True)
        name = _txt(exam_name, 40, "Imtihon nomi 40 belgidan oshmasin")
        label = f"{name} {lvl}" if name else f"CEFR {lvl}"
    elif et == "sat":
        sc = _need(_num(score, "SAT balini kiriting"), 400, 1600, 10,
                   "SAT bali 400 dan 1600 gacha, 10 qadam bilan")
        label = f"SAT {_i(sc)}"
    elif et == "duolingo":
        sc = _need(_num(score, "Duolingo balini kiriting"), 10, 160, 5,
                   "Duolingo bali 10 dan 160 gacha, 5 qadam bilan")
        label = f"Duolingo {_i(sc)}"
    elif et == "toefl":
        sc = _need(_num(score, "TOEFL balini kiriting"), 0, 120, 1,
                   "TOEFL bali 0 dan 120 gacha butun son")
        label = f"TOEFL {_i(sc)}"
    elif et == "cambridge":
        name = _pick(exam_name, _CAMBRIDGE, "Cambridge imtihonini tanlang")
        sc = _need(_num(score, "Cambridge balini kiriting"), 80, 230, 1,
                   "Cambridge bali 80 dan 230 gacha butun son")
        label = f"Cambridge {name} ({_i(sc)})"
    elif et == "topik":
        lvl = _pick(level, _TOPIK, "TOPIK darajasini tanlang (1–6)")
        label = f"TOPIK {lvl}"
    elif et in ("goethe", "torfl"):
        lvl = _pick(level, _CEFR, "Darajani tanlang (A1–C2)", upper=True)
        label = f"{'Goethe' if et == 'goethe' else 'TORFL'} {lvl}"
    else:  # other
        name = _txt(exam_name, 40, "Imtihon nomini yozing (40 belgigacha)")
        lvl = _txt(level, 20, "Natijani yozing (20 belgigacha)")
        if not name:
            _bad("Imtihon nomini yozing (40 belgigacha)")
        if not lvl:
            _bad("Natijani yozing (20 belgigacha)")
        label = f"{name} {lvl}"
    return {
        "exam_type": et, "exam_name": name,
        "score": float(sc) if sc is not None else None, "level": lvl,
        "sub_scores": json.dumps(subs) if subs else None,
        "result_label": label, "cert_no": cno,
    }


def _parse_date(v) -> date:
    msg = "Test sanasini kiriting (YYYY-MM-DD)"
    if isinstance(v, date) and not isinstance(v, datetime):
        return v
    if not isinstance(v, str) or not v.strip():
        _bad(msg)
    try:
        return date.fromisoformat(v.strip()[:10])
    except ValueError:
        _bad(msg)


def _years_back(d: date, n: int) -> date:
    try:
        return d.replace(year=d.year - n)
    except ValueError:            # 29-fevral
        return d.replace(year=d.year - n, day=28)


def _check_date(d: date) -> None:
    """Test sanasi: kelajakda emas (Toshkent kuni), 5 yildan eski emas."""
    today = roles.to_local(WB._now()).date()
    if d > today:
        _bad("Test sanasi kelajakda bo'lishi mumkin emas")
    if d < _years_back(today, MAX_AGE_YEARS):
        _bad(f"Test sanasi {MAX_AGE_YEARS} yildan eski bo'lmasin")


# ================================================================ FAYL ===
# Fayl turi faqat sehrli baytlardan: mijoz yozgan Content-Type va fayl
# nomi ishonchsiz (.exe ni .png deb qayta nomlash mumkin).
_EXT = {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp",
        "application/pdf": "pdf"}


def sniff(head: bytes):
    """Fayl boshidan turi: mime yoki None (ruxsat etilmagan)."""
    if head[:3] == b"\xff\xd8\xff":
        return "image/jpeg"
    if head[:4] == b"\x89PNG":
        return "image/png"
    if len(head) >= 12 and head[:4] == b"RIFF" and head[8:12] == b"WEBP":
        return "image/webp"
    if head[:5] == b"%PDF-":
        return "application/pdf"
    return None


def _file_response(db: Session, u) -> Response:
    """Sertifikat fayli — xavfsiz sarlavhalar bilan (shartnoma §6.1):
    nosniff (brauzer turini o'zi taxmin qilmasin), inline, CSP sandbox
    (PDF/rasm ichidagi skript sahifa huquqi bilan ishlamasin),
    no-store (umumiy kompyuter keshida qolmasin)."""
    a = (db.query(models.Attachment).get(u.attachment_id)
         if u.attachment_id else None)
    if a is None or a.entity != ATTACH_ENTITY or int(a.entity_id) != u.id:
        raise HTTPException(404, "Fayl topilmadi")
    try:
        data = base64.b64decode(a.data or "")
    except (ValueError, TypeError):
        raise HTTPException(404, "Fayl topilmadi")
    mime = sniff(data[:16]) or "application/octet-stream"
    ext = _EXT.get(mime, "bin")
    return Response(content=data, media_type=mime, headers={
        "X-Content-Type-Options": "nosniff",
        "Content-Disposition": f'inline; filename="sertifikat-{u.id}.{ext}"',
        "Content-Security-Policy": "sandbox",
        "Cache-Control": "private, no-store",
    })


# ======================================================== BILDIRISHNOMA ===
def _push(db: Session, user_ids, title: str, body: str, url: str,
          tag: str) -> None:
    """Telefon bildirishnomasi. push modulini entry.py yuklaydi; bo'lmasa
    jim. push o'zi COMMIT qiladi — shuning uchun faqat o'z commitimizdan
    keyin chaqiriladi. Hech qachon xato tashlamaydi."""
    P = sys.modules.get("push")
    if P is None or not user_ids:
        return
    try:
        P.send_to_users(db, list(user_ids), title, body, url=url, tag=tag)
    except Exception as e:  # noqa: BLE001
        print(f"[vocab-cert] bildirishnoma yuborilmadi: {e}")


def _group_ids_of(db: Session, sid: int, primary_gid) -> set:
    """O'quvchining guruhlari: asosiy + ochiq qo'shimcha bog'lanishlar
    (ustoz chegarasi — common.in_any_group — bilan bir xil qoida)."""
    L = models.StudentGroupLink
    gids = {gid for (gid,) in db.query(L.group_id)
            .filter(L.student_id == sid, common._link_open())}
    if primary_gid:
        gids.add(primary_gid)
    return gids


def _teacher_user_ids(db: Session, s) -> list:
    gids = _group_ids_of(db, s.id, s.group_id)
    if not gids:
        return []
    rows = (db.query(models.Teacher.user_id)
            .join(models.Group, models.Group.teacher_id == models.Teacher.id)
            .filter(models.Group.id.in_(gids),
                    models.Group.archived_at.is_(None),
                    models.Teacher.user_id.isnot(None)).all())
    return sorted({uid for (uid,) in rows if uid})


def _student_user_id(db: Session, sid: int):
    row = (db.query(models.Student.user_id)
           .filter(models.Student.id == sid).first())
    return row[0] if row else None


# ============================================================ O'QUVCHI ===
def _subs_out(raw):
    if not raw:
        return None
    try:
        v = json.loads(raw)
    except ValueError:
        return None
    return v if isinstance(v, dict) and v else None


def _iso(x):
    return x.isoformat() if x else None


def _my_out(u) -> dict:
    """O'quvchining o'z yuklamasi (shartnoma §6.1 MyCert). Natija
    maydonlari (result_label, score, level, exam_name, sub_scores,
    cert_no) FAQAT tasdiqlanganda — aks holda None (D3)."""
    conf = u.status == CONFIRMED
    rej = u.status == REJECTED
    return {
        "id": u.id,
        "exam_type": u.exam_type,
        "exam_label": roles.VOCAB_CERT_EXAM_LABELS.get(u.exam_type,
                                                       u.exam_type),
        "status": u.status,
        "status_label": STATUS_LABEL.get(u.status, u.status),
        "created_at": _iso(u.created_at),
        "test_date": _iso(u.test_date),
        "result_label": u.result_label if conf else None,
        "score": u.score if conf else None,
        "level": u.level if conf else None,
        "exam_name": u.exam_name if conf else None,
        "sub_scores": _subs_out(u.sub_scores) if conf else None,
        "cert_no": u.cert_no if conf else None,
        "reject_reason": u.reject_reason if rej else None,
        "reject_note": u.reject_note if rej else None,
        "can_withdraw": u.status == PENDING,
        "can_reupload": rej,
        "mime": u.mime,
    }


def _limits(db: Session, sid: int, now: datetime) -> dict:
    pending = (db.query(func.count(CU.id))
               .filter(CU.student_id == sid, CU.status == PENDING)
               .scalar() or 0)
    used = (db.query(func.count(CU.id))
            .filter(CU.student_id == sid,
                    CU.created_at >= now - timedelta(days=30))
            .scalar() or 0)
    return {"max_pending": MAX_PENDING, "pending": int(pending),
            "max_30d": MAX_PER_30D, "used_30d": int(used),
            "max_bytes": MAX_BYTES}


def _cid(raw) -> int:
    """Yo'ldagi id. Son bo'lmasa — 404 (422 emas: o'chiq bo'lim yoki
    begona yozuv haqida hech narsa bilinmasin). 2026-10-17 (review):
    INTEGER chegarasidan tashqari son ham 404 (bazada OverflowError /
    DataError — 500 bo'lardi)."""
    try:
        v = int(str(raw))
    except (TypeError, ValueError):
        raise HTTPException(404, "Sertifikat topilmadi")
    if not 0 < v <= _ID_MAX:
        raise HTTPException(404, "Sertifikat topilmadi")
    return v


def _own(db: Session, s, raw_id):
    u = db.query(CU).get(_cid(raw_id))
    if u is None or int(u.student_id) != s.id:
        raise HTTPException(404, "Sertifikat topilmadi")
    return u


FORM_MARGIN = 256 * 1024             # multipart: fayldan tashqari maydonlar


def _gate(db: Session = Depends(get_db), user=Depends(get_current_user)):
    """O'quvchi darvozasi DEPENDENCY sifatida (2026-10-17, review): tana
    (_form) undan KEYIN o'qiladi — o'chiq bo'lim / begona foydalanuvchi
    noto'g'ri tana yuborsa ham 400 emas, 404 oladi (shartnoma §3).
    FastAPI natijani so'rov ichida keshlaydi — yo'l ham shu qiymatni
    oladi, darvoza ikki marta ishlamaydi."""
    return WB._student(db, user)


async def _form(request: Request, s=Depends(_gate)):
    """Multipart tana. Maydonlar Form()/File() sifatida e'lon qilinmagan —
    noto'g'ri tana 422 bermasin: darvoza (404) birinchi, maydonlar
    keyin qo'lda tekshiriladi (shartnoma §3). Fayl so'rov tugagach
    yopiladi. Yo'lda token (get_current_user) shundan OLDIN tekshiriladi
    — kirmagan odamning tanasi umuman o'qilmaydi.

    2026-10-17 (review): Content-Length 3 MB + zaxiradan katta bo'lsa —
    tana o'qilmasdan 413; tana buzuq bo'lsa (boundary yo'q, maydon /
    fayl ko'p) — o'zbekcha 400 (darvozadan keyin)."""
    cl = request.headers.get("content-length")
    if cl and cl.strip().isdigit() and int(cl) > MAX_BYTES + FORM_MARGIN:
        raise HTTPException(413, "Fayl juda katta — 3 MB dan oshmasin")
    try:
        form = await request.form(max_files=2, max_fields=20)
    except Exception:  # noqa: BLE001 - Starlette tahlil xatosi
        raise HTTPException(400, "Fayl yuborilmadi — so'rov noto'g'ri. "
                                 "Sahifani yangilab, qayta urinib ko'ring")
    try:
        yield form
    finally:
        await form.close()


def _field(form, key):
    v = form.get(key) if form is not None else None
    return v if isinstance(v, str) else None


@router.get("/api/wordbank/certs/mine")
def my_certs(db: Session = Depends(get_db),
             user=Depends(get_current_user)):
    """O'quvchining o'z yuklamalari (eng yangisi birinchi, qaytarib
    olinganlar ko'rsatilmaydi) va cheklovlar."""
    s = WB._student(db, user)
    rows = (db.query(CU)
            .filter(CU.student_id == s.id, CU.status != WITHDRAWN)
            .order_by(CU.created_at.desc(), CU.id.desc()).all())
    return {"items": [_my_out(u) for u in rows],
            "limits": _limits(db, s.id, WB._now())}


@router.post("/api/wordbank/certs/mine")
def upload_my_cert(db: Session = Depends(get_db), s=Depends(_gate),
                   form=Depends(_form)):
    """Sertifikat yuklash (multipart: file, exam_type, exam_name, score,
    level, sub_scores (JSON), test_date, cert_no). Tekshiruv tartibi
    shartnoma §6.1 da. Javobda FAQAT {id, status} — ball ham, yorliq
    ham yo'q (tasdiqlanmagan natija o'quvchiga ham qaytarilmaydi).
    Darvoza (s) — _gate, tana o'qilishidan OLDIN."""
    # 1) natija maydonlari
    res = validate_result(
        _field(form, "exam_type"), _field(form, "exam_name"),
        _field(form, "score"), _field(form, "level"),
        _field(form, "sub_scores"), _field(form, "cert_no"))
    tdate = _parse_date(_field(form, "test_date"))
    # 2) fayl
    f = form.get("file") if form is not None else None
    if f is None or isinstance(f, str) or not hasattr(f, "file"):
        raise HTTPException(400, "Sertifikat faylini tanlang")
    data = f.file.read(MAX_BYTES + 1)
    if not data:
        raise HTTPException(400, "Sertifikat faylini tanlang")
    if len(data) > MAX_BYTES:
        raise HTTPException(413, "Fayl juda katta — 3 MB dan oshmasin")
    mime = sniff(data[:16])
    if mime is None:
        raise HTTPException(415, "Faqat rasm (JPG, PNG, WEBP) yoki PDF "
                                 "yuklang")
    # 3) sana
    _check_date(tdate)
    # 4) cheklovlar. 2026-10-17 (review): bir o'quvchining PARALLEL
    # yuklamalari "sanab, keyin yozish" oralig'idan o'tib cheklovni
    # aylanib o'tardi (12 ta parallel so'rovdan 4 tasi o'tgan). O'quvchi
    # qatori qulflanadi (Postgres: FOR UPDATE — ikkinchi so'rov birinchisi
    # commit bo'lguncha kutadi); SQLite'da bu no-op, u yerda yozilgandan
    # keyingi qayta sanash (pastda) ushlaydi.
    db.query(models.Student.id).filter(
        models.Student.id == s.id).with_for_update().first()
    now = WB._now()
    lim = _limits(db, s.id, now)
    if lim["pending"] >= MAX_PENDING:
        raise HTTPException(429, "Tekshirilayotgan sertifikatlar 3 tadan "
                                 "oshmasin")
    if lim["used_30d"] >= MAX_PER_30D:
        raise HTTPException(429, "30 kunda 10 tadan ko'p yuklab bo'lmaydi")
    # 5) bir xil fayl (shu o'quvchida kutilayotgan yoki tasdiqlangan)
    digest = hashlib.sha256(data).hexdigest()

    def same_file():
        return (db.query(func.count(CU.id))
                .filter(CU.student_id == s.id, CU.sha256 == digest,
                        CU.status.in_([PENDING, CONFIRMED])).scalar() or 0)

    if same_file():
        raise HTTPException(409, "Bu fayl allaqachon yuklangan")
    u = CU(student_id=s.id, test_date=tdate, store="db", mime=mime,
           size=len(data), sha256=digest, status=PENDING,
           name_snap=s.full_name, branch_id_snap=s.branch_id,
           created_at=now, updated_at=now, **res)
    db.add(u)
    db.flush()
    # Qayta sanash — shu yozuv bilan birga chegaradan oshsa, bekor
    lim = _limits(db, s.id, now)
    if lim["pending"] > MAX_PENDING or lim["used_30d"] > MAX_PER_30D:
        db.rollback()
        raise HTTPException(429, "Tekshirilayotgan sertifikatlar 3 tadan "
                                 "oshmasin" if lim["pending"] > MAX_PENDING
                            else "30 kunda 10 tadan ko'p yuklab bo'lmaydi")
    if same_file() > 1:
        db.rollback()
        raise HTTPException(409, "Bu fayl allaqachon yuklangan")
    a = models.Attachment(
        entity=ATTACH_ENTITY, entity_id=u.id, kind="certificate",
        filename=f"sertifikat-{u.id}.{_EXT[mime]}", mime=mime,
        size=len(data), data=base64.b64encode(data).decode("ascii"),
        created_by=s.full_name)
    db.add(a)
    db.flush()
    u.attachment_id = a.id
    uid, name = u.id, s.full_name
    db.commit()
    # Ustozga — FAQAT ism (ball yo'q, D3)
    _push(db, _teacher_user_ids(db, s), "Yangi sertifikat",
          f"Yangi sertifikat tekshiruvga yuklandi: {name}",
          url=TEACHER_URL, tag="vocab-cert")
    return {"id": uid, "status": PENDING}


@router.delete("/api/wordbank/certs/mine/{cid}")
def withdraw_my_cert(cid: str, db: Session = Depends(get_db),
                     user=Depends(get_current_user)):
    """Kutilayotgan yuklamani qaytarib olish (qator va fayl qoladi)."""
    s = WB._student(db, user)
    u = _own(db, s, cid)
    if u.status != PENDING:
        raise HTTPException(409, "Faqat tekshirilayotgan sertifikatni "
                                 "qaytarib olish mumkin")
    now = WB._now()
    r = db.execute(sa_update(CU)
                   .where(CU.id == u.id, CU.status == PENDING)
                   .values(status=WITHDRAWN, updated_at=now)
                   .execution_options(synchronize_session=False))
    if r.rowcount != 1:
        db.rollback()
        raise HTTPException(409, "Faqat tekshirilayotgan sertifikatni "
                                 "qaytarib olish mumkin")
    uid = u.id
    db.commit()
    return {"id": uid, "status": WITHDRAWN}


@router.get("/api/wordbank/certs/mine/{cid}/file")
def my_cert_file(cid: str, db: Session = Depends(get_db),
                 user=Depends(get_current_user)):
    """O'z yuklamasining fayli (istalgan holatda)."""
    s = WB._student(db, user)
    return _file_response(db, _own(db, s, cid))


# =============================================================== XODIM ===
# Chegara (shartnoma §6.2): ustoz — o'z guruhlari (common._my_groups,
# o'quvchi common.in_any_group bilan); filial xodimi — o'z filiallari
# (jonli o'quvchi filiali, o'quvchi o'chirilgan bo'lsa branch_id_snap;
# filialsiz o'quvchi ham ko'rinadi — _in_user_branches(null_ok=True));
# ORG_WIDE (asoschi, o'quv bo'limi rahbari) — hammasi.
def _staff(db: Session, user) -> None:
    if not WB.flag_value(db):
        raise HTTPException(404, WB._NOT_FOUND)
    if not has_role(user, roles.VOCAB_CERT_CONFIRM):
        raise HTTPException(403, "Bu amal uchun ruxsatingiz yo'q")


def _scope(db: Session, user) -> tuple:
    """("all", None) | ("groups", [gid]) | ("branches", [bid])."""
    if user.role in tuple(roles.ORG_WIDE_ROLES):
        return ("all", None)
    if user.role in tuple(roles.OWN_GROUPS_ONLY):
        t = common._teacher_of_user(db, user)
        gids = [g.id for g in common._my_groups(db, t.id)] if t else []
        return ("groups", gids)
    if not user.branch_id:
        # filialga bog'lanmagan xodim — cheklov yo'q (_in_user_branches)
        return ("all", None)
    return ("branches", list(common._user_branch_ids(db, user)))


def _eff_branch(SA):
    """Jonli o'quvchi filiali; o'quvchi o'chirilgan bo'lsa — snapshot."""
    return case((SA.id.isnot(None), SA.branch_id), else_=CU.branch_id_snap)


def _in_groups_sql(gids):
    return CU.student_id.in_(
        select(models.Student.id).where(common.in_any_group(gids)))


def _apply_scope(q, sc, SA):
    kind, ids = sc
    if kind == "groups":
        return q.filter(_in_groups_sql(ids))
    if kind == "branches":
        eff = _eff_branch(SA)
        return q.filter(or_(eff.in_(ids or [-1]), eff.is_(None)))
    return q


def _in_scope(db: Session, sc, u) -> bool:
    kind, ids = sc
    if kind == "all":
        return True
    live = (db.query(models.Student.id, models.Student.branch_id)
            .filter(models.Student.id == u.student_id).first())
    if kind == "groups":
        return live is not None and db.query(models.Student.id).filter(
            models.Student.id == u.student_id,
            common.in_any_group(ids)).first() is not None
    eff = live.branch_id if live is not None else u.branch_id_snap
    return eff is None or eff in ids


def _load_scoped(db: Session, user, raw_id):
    u = db.query(CU).get(_cid(raw_id))
    if u is None or not _in_scope(db, _scope(db, user), u):
        raise HTTPException(404, "Sertifikat topilmadi")
    return u


def _opt_int(raw, msg):
    if raw is None or (isinstance(raw, str) and not raw.strip()):
        return None
    try:
        return int(str(raw).strip())
    except ValueError:
        raise HTTPException(400, msg)


def _filters(db: Session, user, sc, SA, branch_id, group_id,
             strict: bool = True) -> list:
    """branch_id / group_id — chaqiruvchi chegarasi ICHIDA filtr.
    strict: begona filial / guruh — 403 (ro'yxat); aks holda jim
    e'tiborsiz (menyu hisoblagichi — xato ko'rsatmasin).
    Ustoz chegarasi guruhlar bo'yicha: veb-mijoz har GET ga qo'shadigan
    global branch_id ustozda e'tiborga olinmaydi (guruh boshqa filialda
    bo'lsa o'z o'quvchilari yo'qolib qolardi — api.ts groupScoped
    izohiga qarang)."""
    out = []
    bid = _opt_int(branch_id, "branch_id noto'g'ri")
    if bid is not None and sc[0] != "groups":
        if common._in_user_branches(db, user, bid):
            out.append(_eff_branch(SA) == bid)
        elif strict:
            raise HTTPException(403, "Bu filial sizga tegishli emas")
    gid = _opt_int(group_id, "group_id noto'g'ri")
    if gid is not None:
        try:
            common._get_group_in_scope(db, gid, user)
            out.append(CU.student_id.in_(
                select(models.Student.id).where(common.in_group(gid))))
        except HTTPException:
            if strict:
                raise
    return out


# Xodim ko'radigan holatlar. 2026-10-17 (review): o'quvchi QAYTARIB
# OLGAN yuklama (masalan adashib yoki shaxsiy hujjat yuklagan) xodimga
# ko'rsatilmaydi — na ro'yxatda, na fayli (qator va fayl D4 bo'yicha
# bazada qoladi).
STAFF_STATUSES = [x for x in roles.VOCAB_CERT_STATUSES if x != WITHDRAWN]


def _parse_statuses(raw) -> list:
    if raw is None or not str(raw).strip():
        return [PENDING]
    out = []
    for p in str(raw).split(","):
        p = p.strip().lower()
        if not p:
            continue
        if p not in STAFF_STATUSES:
            raise HTTPException(400, "status: " + ", ".join(STAFF_STATUSES))
        if p not in out:
            out.append(p)
    return out or [PENDING]


def _staff_out(db: Session, rows: list) -> list:
    """Xodim navbati qatorlari (shartnoma §6.2 StaffCert). Hamma
    qo'shimcha ma'lumot to'plab so'raladi (har qatorga alohida so'rov
    yo'q); Student.photo TANLANMAYDI."""
    if not rows:
        return []
    now = WB._now()
    S = models.Student
    sids = sorted({int(u.student_id) for u in rows})
    live = {}
    for i in range(0, len(sids), _IN_CHUNK):
        for r in (db.query(S.id, S.full_name, S.public_id, S.branch_id,
                           S.group_id)
                  .filter(S.id.in_(sids[i:i + _IN_CHUNK]))):
            live[r.id] = r
    L = models.StudentGroupLink
    sgroups = {sid: ([r.group_id] if r.group_id else [])
               for sid, r in live.items()}
    lsids = sorted(live)
    for i in range(0, len(lsids), _IN_CHUNK):
        for sid, gid in (db.query(L.student_id, L.group_id)
                         .filter(L.student_id.in_(lsids[i:i + _IN_CHUNK]),
                                 L.active == 1)):
            if gid not in sgroups[sid]:
                sgroups[sid].append(gid)
    gids = sorted({g for v in sgroups.values() for g in v})
    gname = ({gid: name for gid, name in db.query(
        models.Group.id, models.Group.name)
        .filter(models.Group.id.in_(gids))} if gids else {})

    def eff_branch(u):
        r = live.get(int(u.student_id))
        return r.branch_id if r is not None else u.branch_id_snap

    bids = sorted({b for b in (eff_branch(u) for u in rows) if b})
    bname = ({bid: name for bid, name in db.query(
        models.Branch.id, models.Branch.name)
        .filter(models.Branch.id.in_(bids))} if bids else {})
    shas = sorted({u.sha256 for u in rows if u.sha256})
    owners: dict = {}
    for i in range(0, len(shas), _IN_CHUNK):
        for h, sid in (db.query(CU.sha256, CU.student_id)
                       .filter(CU.sha256.in_(shas[i:i + _IN_CHUNK]))
                       .distinct()):
            owners.setdefault(h, set()).add(int(sid))

    out = []
    for u in rows:
        sid = int(u.student_id)
        r = live.get(sid)
        b = eff_branch(u)
        dup = bool(u.sha256) and len(owners.get(u.sha256, set()) - {sid}) > 0
        out.append({
            "id": u.id,
            "student_id": sid,
            "student_name": (r.full_name if r is not None else u.name_snap)
            or "—",
            "student_public_id": r.public_id if r is not None else None,
            "student_exists": r is not None,
            "branch_id": b,
            "branch_name": bname.get(b) if b else None,
            "groups": [gname[g] for g in sgroups.get(sid, []) if g in gname],
            "exam_type": u.exam_type,
            "exam_label": roles.VOCAB_CERT_EXAM_LABELS.get(u.exam_type,
                                                           u.exam_type),
            "exam_name": u.exam_name,
            "score": u.score,
            "level": u.level,
            "sub_scores": _subs_out(u.sub_scores),
            "result_label": u.result_label,
            "test_date": _iso(u.test_date),
            "cert_no": u.cert_no,
            "mime": u.mime,
            "size": u.size,
            "status": u.status,
            "created_at": _iso(u.created_at),
            "days_waiting": (max(0, (now - u.created_at).days)
                             if u.status == PENDING and u.created_at
                             else None),
            "duplicate_warning": DUPLICATE_WARNING if dup else None,
            "verify_method": u.verify_method,
            "review_note": u.review_note,
            "reviewed_by_name": u.reviewed_by_name,
            "reviewed_at": _iso(u.reviewed_at),
            "reject_reason": u.reject_reason,
            "reject_note": u.reject_note,
            "revoked_by_name": u.revoked_by_name,
            "revoked_at": _iso(u.revoked_at),
            "revoke_note": u.revoke_note,
        })
    return out


def _one_out(db: Session, u) -> dict:
    db.refresh(u)
    return _staff_out(db, [u])[0]


def _pending_in_scope(db: Session, user, branch_id=None,
                      group_id=None) -> int:
    SA = aliased(models.Student)
    sc = _scope(db, user)
    q = (db.query(func.count(CU.id)).select_from(CU)
         .outerjoin(SA, SA.id == CU.student_id))
    q = _apply_scope(q, sc, SA).filter(CU.status == PENDING)
    for c in _filters(db, user, sc, SA, branch_id, group_id, strict=False):
        q = q.filter(c)
    return int(q.scalar() or 0)


@router.get("/api/wordbank/certs/count")
def certs_count(branch_id: str = None, group_id: str = None,
                db: Session = Depends(get_db),
                user=Depends(get_current_user)):
    """Chegaradagi kutilayotganlar soni (menyu belgisi uchun)."""
    _staff(db, user)
    return {"pending": _pending_in_scope(db, user, branch_id, group_id)}


def pending_alert(db: Session, user):
    """/api/my/alerts (paneldagi qo'ng'iroqcha va JonyOS "Bildirishnomalar")
    qatori yoki None.

    2026-10-17 (review): yangi yuklama haqida faqat telefon bildirishnomasi
    bor edi, xodimlar esa push'ga obuna emas (PushBanner faqat o'quvchida)
    — ustoz umuman bilmay, sertifikat kutib qolardi. Endi tasdiqlay
    oladigan xodim o'z chegarasidagi kutilayotganlar SONINI ko'radi
    (ism ham, ball ham yo'q)."""
    if not has_role(user, roles.VOCAB_CERT_CONFIRM) or not WB.flag_value(db):
        return None
    n = _pending_in_scope(db, user)
    if n <= 0:
        return None
    return {"icon": "task",
            "text": f"{n} ta sertifikat tekshiruvni kutmoqda",
            "link": TEACHER_URL, "tone": "amber"}


@router.get("/api/wordbank/certs")
def list_certs(status: str = None, branch_id: str = None,
               group_id: str = None, db: Session = Depends(get_db),
               user=Depends(get_current_user)):
    """Tekshiruv navbati. status — vergul bilan ro'yxat (standart
    pending; "Rad etilgan" yorlig'i rejected,revoked yuboradi).
    Kutilayotganlar — eng eskisi birinchi; qolganlari — oxirgi qaror
    birinchi. counts — yorliqlar uchun (rejected = rejected + revoked)."""
    _staff(db, user)
    wanted = _parse_statuses(status)
    SA = aliased(models.Student)
    sc = _scope(db, user)
    conds = _filters(db, user, sc, SA, branch_id, group_id, strict=True)

    def base(q):
        q = _apply_scope(q.select_from(CU)
                         .outerjoin(SA, SA.id == CU.student_id), sc, SA)
        for c in conds:
            q = q.filter(c)
        return q

    q = base(db.query(CU)).filter(CU.status.in_(wanted))
    if wanted == [PENDING]:
        q = q.order_by(CU.created_at.asc(), CU.id.asc())
    else:
        q = q.order_by(func.coalesce(CU.revoked_at, CU.reviewed_at,
                                     CU.created_at).desc(), CU.id.desc())
    rows = q.limit(LIST_LIMIT).all()
    counts = {PENDING: 0, CONFIRMED: 0, REJECTED: 0}
    for st, n in (base(db.query(CU.status, func.count(CU.id)))
                  .group_by(CU.status)):
        if st == PENDING:
            counts[PENDING] += int(n)
        elif st == CONFIRMED:
            counts[CONFIRMED] += int(n)
        elif st in (REJECTED, REVOKED):
            counts[REJECTED] += int(n)
    return {"items": _staff_out(db, rows),
            "counts": {"pending": counts[PENDING],
                       "confirmed": counts[CONFIRMED],
                       "rejected": counts[REJECTED]},
            "can_revoke": has_role(user, roles.VOCAB_CERT_REVOKE)}


@router.get("/api/wordbank/certs/{cid}/file")
def staff_cert_file(cid: str, db: Session = Depends(get_db),
                    user=Depends(get_current_user)):
    """Xodim uchun fayl (chegara ichida; qaytarib olingani — yo'q)."""
    _staff(db, user)
    u = _load_scoped(db, user, cid)
    if u.status == WITHDRAWN:
        raise HTTPException(404, "Fayl topilmadi")
    return _file_response(db, u)


def _note(v, required: bool, msg: str):
    s = _txt(v, NOTE_MAX, f"Izoh {NOTE_MAX} belgidan oshmasin")
    if required and not s:
        _bad(msg)
    return s


def _hall(db: Session, sid: int) -> None:
    """Tarix qatori (wordbank_social, shartnoma §2) — dangasa import."""
    import wordbank_social as WSOC
    WSOC.refresh_hall(db, sid)


def _board_cache_clear() -> None:
    try:
        import wordbank_social as WSOC
        WSOC.clear_cache()
    except Exception:  # noqa: BLE001 - kesh tozalanmasa 60 s da o'zi
        pass


_CERT_KIND = {"ielts": "ielts", "multilevel": "cefr", "cefr_other": "cefr"}


def _cert_level(r: dict) -> str:
    et = r["exam_type"]
    if et == "ielts":
        return f"{r['score']:.1f}"
    if et in ("multilevel", "cefr_other", "goethe", "torfl"):
        return r["level"]
    if et == "topik":
        return f"TOPIK {r['level']}"
    return r["result_label"]


@router.post("/api/wordbank/certs/{cid}/confirm")
def confirm_cert(cid: str, payload=Body(default=None),
                 db: Session = Depends(get_db),
                 user=Depends(get_current_user)):
    """Tasdiqlash. Xodim maydonlarni tuzatishi mumkin — ular qaytadan
    o'sha qoidalar bilan tekshiriladi va yorliq qayta yasaladi. Natija:
    students.add_certificate dagidek Certificate + SMM vazifasi, audit,
    tarix qatori, o'quvchiga bildirishnoma."""
    _staff(db, user)
    u = _load_scoped(db, user, cid)
    if u.status != PENDING:
        raise HTTPException(409, "Faqat kutilayotgan sertifikat "
                                 "tasdiqlanadi")
    st = db.query(models.Student).get(u.student_id)
    if st is None:
        raise HTTPException(409, "O'quvchi bazada yo'q — tasdiqlab "
                                 "bo'lmaydi")
    body = WB._body(payload)

    def val(k, cur):
        return body[k] if k in body else cur

    vm = body.get("verify_method")
    if vm not in roles.VOCAB_CERT_VERIFY_METHODS:
        _bad("Qanday tekshirilganini tanlang")
    res = validate_result(
        val("exam_type", u.exam_type), val("exam_name", u.exam_name),
        val("score", u.score), val("level", u.level),
        val("sub_scores", u.sub_scores), val("cert_no", u.cert_no))
    tdate = _parse_date(val("test_date", u.test_date))
    _check_date(tdate)
    note = _note(body.get("note"), False, "")
    now = WB._now()
    who = getattr(user, "full_name", None) or getattr(user, "username", None)
    r = db.execute(sa_update(CU)
                   .where(CU.id == u.id, CU.status == PENDING)
                   .values(status=CONFIRMED, test_date=tdate,
                           verify_method=vm, review_note=note,
                           reviewed_by=user.id, reviewed_by_name=who,
                           reviewed_at=now, updated_at=now, **res)
                   .execution_options(synchronize_session=False))
    if r.rowcount != 1:
        db.rollback()
        raise HTTPException(409, "Faqat kutilayotgan sertifikat "
                                 "tasdiqlanadi")
    # Shartli UPDATE identity map'dagi obyektni yangilamaydi — eskirgan
    # qiymat (masalan xodim tuzatgan ball o'rniga yuklamadagisi)
    # refresh_hall -> cert_badge_for orqali tarixga yozilmasin.
    db.expire(u)
    label = res["result_label"]
    c = models.Certificate(
        student_id=st.id, kind=_CERT_KIND.get(res["exam_type"], "other"),
        level=_cert_level(res), score=res["score"], date=tdate,
        note=f"So'z bilish: {label} (yuklama #{u.id}, {vm})",
        created_by=who)
    db.add(c)
    db.flush()
    u.certificate_id = c.id
    db.flush()
    # SMM: video olish vazifasi (add_certificate bilan bir xil). Vazifa
    # yaratilmasa ham tasdiq to'xtamasin — savepoint.
    try:
        with db.begin_nested():
            common._smm_achievement_task(
                db, st, what=label,
                detail=(f"Manba: So'z bilish — o'quvchi yukladi, "
                        f"tekshirildi: {vm}"))
    except Exception as e:  # noqa: BLE001
        print(f"[vocab-cert] SMM vazifasi yaratilmadi: {e}")
    audit.log(db, user, entity="student", action="update",
              entity_id=st.id, entity_label=st.full_name,
              field="vocab_cert", new_value=label,
              note=vm + (f": {note}" if note else ""),
              branch_id=st.branch_id)
    _hall(db, st.id)
    db.commit()
    _board_cache_clear()
    _push(db, [st.user_id] if st.user_id else [], "Sertifikat tasdiqlandi",
          f"Sertifikatingiz tasdiqlandi: {label}", url=STUDENT_URL,
          tag="vocab-cert")
    return _one_out(db, u)


@router.post("/api/wordbank/certs/{cid}/reject")
def reject_cert(cid: str, payload=Body(default=None),
                db: Session = Depends(get_db),
                user=Depends(get_current_user)):
    """Rad etish: sabab ro'yxatdan (majburiy), "boshqa" bo'lsa izoh ham.
    O'quvchiga sabab boradi (ball emas) — u qayta yuklay oladi."""
    _staff(db, user)
    u = _load_scoped(db, user, cid)
    if u.status != PENDING:
        raise HTTPException(409, "Faqat kutilayotgan sertifikat rad "
                                 "etiladi")
    body = WB._body(payload)
    reason = body.get("reason_code")
    if reason not in roles.VOCAB_CERT_REJECT_REASONS:
        _bad("Sababni tanlang")
    note = _note(body.get("note"), reason == "boshqa", "Sababini yozing")
    now = WB._now()
    who = getattr(user, "full_name", None) or getattr(user, "username", None)
    r = db.execute(sa_update(CU)
                   .where(CU.id == u.id, CU.status == PENDING)
                   .values(status=REJECTED, reject_reason=reason,
                           reject_note=note, reviewed_by=user.id,
                           reviewed_by_name=who, reviewed_at=now,
                           updated_at=now)
                   .execution_options(synchronize_session=False))
    if r.rowcount != 1:
        db.rollback()
        raise HTTPException(409, "Faqat kutilayotgan sertifikat rad "
                                 "etiladi")
    db.expire(u)
    st = db.query(models.Student).get(u.student_id)
    audit.log(db, user, entity="student", action="update",
              entity_id=u.student_id,
              entity_label=st.full_name if st is not None else u.name_snap,
              field="vocab_cert", new_value=f"rad etildi: {reason}",
              note=note, branch_id=(st.branch_id if st is not None
                                    else u.branch_id_snap))
    db.commit()
    uid = _student_user_id(db, u.student_id)
    _push(db, [uid] if uid else [], "Sertifikat rad etildi",
          f"Sertifikatingiz rad etildi: {reason}. Profil bo'limidan qayta "
          f"yuklashingiz mumkin.", url=STUDENT_URL, tag="vocab-cert")
    return _one_out(db, u)


@router.post("/api/wordbank/certs/{cid}/revoke")
def revoke_cert(cid: str, payload=Body(default=None),
                db: Session = Depends(get_db),
                user=Depends(get_current_user)):
    """Tasdiqlangan natijani bekor qilish (tor ro'yxat:
    VOCAB_CERT_REVOKE). Yaratilgan Certificate o'chiriladi (certificate_id
    iz uchun qoladi), belgi hamma joydan yo'qoladi; yuklama va fayl
    qoladi (D4)."""
    _staff(db, user)
    if not has_role(user, roles.VOCAB_CERT_REVOKE):
        raise HTTPException(403, "Bu amal uchun ruxsatingiz yo'q")
    u = _load_scoped(db, user, cid)
    if u.status != CONFIRMED:
        raise HTTPException(409, "Faqat tasdiqlangan sertifikat bekor "
                                 "qilinadi")
    body = WB._body(payload)
    note = _note(body.get("note"), True, "Bekor qilish sababini yozing")
    old_label, cert_id, sid = u.result_label, u.certificate_id,         int(u.student_id)
    now = WB._now()
    who = getattr(user, "full_name", None) or getattr(user, "username", None)
    r = db.execute(sa_update(CU)
                   .where(CU.id == u.id, CU.status == CONFIRMED)
                   .values(status=REVOKED, revoked_by_name=who,
                           revoked_at=now, revoke_note=note, updated_at=now)
                   .execution_options(synchronize_session=False))
    if r.rowcount != 1:
        db.rollback()
        raise HTTPException(409, "Faqat tasdiqlangan sertifikat bekor "
                                 "qilinadi")
    db.expire(u)
    if cert_id:
        c = db.query(models.Certificate).get(cert_id)
        if c is not None and int(c.student_id) == sid:
            db.delete(c)
            db.flush()
    st = db.query(models.Student).get(sid)
    audit.log(db, user, entity="student", action="update",
              entity_id=sid,
              entity_label=st.full_name if st is not None else u.name_snap,
              field="vocab_cert", old_value=old_label,
              new_value="bekor qilindi", note=note,
              branch_id=(st.branch_id if st is not None
                         else u.branch_id_snap))
    _hall(db, sid)
    db.commit()
    _board_cache_clear()
    uid = st.user_id if st is not None else None
    # Ball / yorliq yozilmaydi — faqat holat
    _push(db, [uid] if uid else [], "Sertifikat bekor qilindi",
          "Sertifikatingiz natijasi bekor qilindi. Savol bo'lsa, ustozingizga "
          "murojaat qiling.", url=STUDENT_URL, tag="vocab-cert")
    return _one_out(db, u)


# ======================================================= TELEGRAM IMPORT ===
# 2026-10-17, Jahongir: "JonyAcademy telegram sahifamizda natija qilgan
# o'quvchilar bor shularnikini olib avtomat sertifikatlarni yuklab qo'y",
# qarorlar: "Darhol tasdiqlangan", kanal https://t.me/JonyAcademy.
#   * Manba — kanaldagi natija postlaridan ajratilgan ro'yxat
#     (wordbank_data/telegram_results.json: post, sana, ism, imtihon,
#     daraja, ball). Faqat ingliz tili: IELTS va Multilevel/CEFR.
#   * Ism CRM o'quvchisiga FAQAT bitta aniq moslik bo'lsa bog'lanadi
#     (postdagi ism so'zlari o'quvchi to'liq ismida bo'lishi kerak; lotin/
#     kirill, x/h, tutuq belgisi farqi hisobga olinmaydi). Bir nechta
#     o'quvchi mos kelsa yoki hech kim — o'tkazib yuboriladi (hisobotda
#     faqat post raqami: ism hech qayerga yozilmaydi).
#   * Certificate qatori (CRM sertifikati) yaratiladi — u yuqoridagi
#     CRM_KINDS qoidasi bilan darhol "tasdiqlangan" belgi bo'ladi. SMM
#     vazifasi YARATILMAYDI (natija allaqachon kanalda e'lon qilingan).
#   * Takror yo'q: shu tur va darajadagi sertifikati bor o'quvchiga qayta
#     yozilmaydi. Belgi kaliti fayl mazmunidan — fayl yangilansa qayta
#     ishlaydi (idempotent).
#
# 2026-10-17 (v2): production'da v1 natijasi — yaratildi 0, bor 31, bir
# nechta mos 3, topilmadi ~140; 2026-10-03/05 dagi hozirgi o'quvchilar ham
# topilmadi ("Azamova Sevinch", "Pulatova Sarvinoz", "Otayeva Kamola"):
# CRM'da ism boshqacha yozilgan (-xon/-oy qo'shimchasi, o'/u, a/o, dj/j,
# iy/i, ruscha yozilish). Shuning uchun:
#   * EHTIYOTKOR o'xshashlik (_match): aniq moslik topilmasa, so'zlar
#     "qat'iy o'xshash" bo'lsa ham mos (_tok_eq: bosh qismi — qisqasi
#     >= 4 harf, uzuni ko'pi bilan 3 harf qo'shadi; yoki bitta harf farqi —
#     ikkalasi >= 5 harf). Postdagi har so'z o'quvchi ismining ALOHIDA
#     so'ziga mos kelishi shart; baribir faqat BITTA o'quvchi bo'lsa.
#   * TAKROR XATOSI tuzatildi: "bor" tekshiruvi OR(post havolasi, tur +
#     daraja) edi — bitta postda bir odamning ikki natijasi (4691: IELTS
#     7.0 va 7.5) bo'lsa, ikkinchisi "bor" bo'lib qolardi. Endi qoida
#     bitta: o'quvchida SHU TUR va SHU DARAJA sertifikati bor bo'lsa —
#     bor (havola ahamiyatsiz).
#   * TG_SEED v2 — production bir marta qayta yuradi; bor sertifikatlar
#     yuqoridagi qoida bilan o'tkaziladi, takror bo'lmaydi.
#   * Qolganini xodim o'zi bog'laydi / "bizniki emas" deb yashiradi
#     (/api/wordbank/telegram-results, faqat VOCAB_CERT_REVOKE). Holat
#     JONLI hisoblanadi (fayl + baza); ism faqat xodim yo'lida — ochiq
#     /api/wordbank/status da faqat sonlar va post raqamlari.
#
# 2026-10-17 (v2, review): yuqoridagi "qat'iy o'xshash" (bosh qismi +
# 3 harf, har qanday bitta harf farqi) aka-uka / opa-singil va adash
# ismlarni bitta odam qilib qo'yardi (Olimova Nozima -> Olimov Nozim,
# Otayeva Kamola -> Otayeva Kamila, Aliyev -> Valiyev, Xasan -> Husan) —
# boshqa odamga DARHOL tasdiqlangan sertifikat. Endi avtomat bog'lash
# (_tok_eq) faqat TOR ro'yxat bilan: aynan; ism oxiriga -xon/-oy/-bek/
# -jon/-oyim qo'shilishi; bitta o/u, a/o, p/b, k/q, d/t almashishi
# (oxirgi harf emas); bitta y yoki d qo'shilishi (iy/i, ye/e, dj/j;
# boshida va oxirida emas). Oxirgi harfi farq qiladigan juftlik (-ov/-ova,
# Diyor/Diyora) hech qachon teng emas. Otasining ismi (-ovna/-evna/
# -ovich/-evich, "... o'g'li/qizi") solishtirishga kirmaydi. Bo'sh
# o'xshashlik (_tok_cost) — faqat xodimga nomzod.
#   * Holat qoidasi BITTA (_TgCtx.state): seed ham, xodim ro'yxati ham
#     shuni ishlatadi — xodim qo'lda bog'lagan natijani keyingi seed
#     boshqa o'quvchiga qayta bermaydi. "Bog'langan" taxmini (havolasiz)
#     faqat AYNAN ism bilan.
#   * Seed Postgres'da tranzaksiya qulfi bilan (parallel nusxalar
#     takror sertifikat yaratmasin); sertifikatlar, hisobot va belgi —
#     bitta commit.
#   * Xodim qarorlari "wordbank_tg_links" da ({"post:ism:tur:daraja":
#     o'quvchi id}): qo'lda bog'lash va "natija unda allaqachon bor" deb
#     tasdiqlash shu yerga yoziladi.
TG_FILE =os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       "wordbank_data", "telegram_results.json")
TG_SEED = "wordbank_tg_certs_v2"
TG_REPORT_KEY = "wordbank_tg_import"   # IntegrationSetting: sonlar + post raqamlari
TG_DISMISSED_KEY = "wordbank_tg_dismissed"   # IntegrationSetting: ["post:ism", ...]
TG_LINKS_KEY = "wordbank_tg_links"   # IntegrationSetting: {"post:ism:tur:daraja": sid}
TG_SEED_LOCK = 20261017              # pg_advisory qulf kaliti (seed_telegram)
TG_CHANNEL = "https://t.me/JonyAcademy/"
TG_BY = "Telegram (avtomat)"
TG_STATUSES = ("unmatched", "ambiguous", "linked", "dismissed")
TG_MAX_CANDIDATES = 5
TG_DUP = "Bu o'quvchida bu natija allaqachon bor"
TG_TAKEN = "Bu natija allaqachon boshqa o'quvchiga bog'langan"
_TG_POST_RE = re.compile(r"t\.me/JonyAcademy/(\d+)")

_CYR = {"а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e",
        "ё": "yo", "ж": "j", "з": "z", "и": "i", "й": "y", "к": "k",
        "л": "l", "м": "m", "н": "n", "о": "o", "п": "p", "р": "r",
        "с": "s", "т": "t", "у": "u", "ф": "f", "х": "x", "ц": "ts",
        "ч": "ch", "ш": "sh", "щ": "sh", "ъ": "", "ы": "i", "ь": "",
        "э": "e", "ю": "yu", "я": "ya", "ў": "o", "қ": "q", "ғ": "g",
        "ҳ": "h"}


def _name_words(s) -> list:
    """Ism so'zlari TARTIB bilan: kichik harf, kirill -> lotin, tutuq
    belgisi tashlanadi, x/kh -> h, faqat harflar (2+ harf)."""
    s = (s or "").lower()
    s = "".join(_CYR.get(ch, ch) for ch in s)
    s = re.sub(r"[ʻʼ‘’`'´]", "", s)
    s = s.replace("kh", "h").replace("x", "h")
    return [t for t in re.findall(r"[a-z]+", s) if len(t) > 1]


def _name_tokens(s) -> frozenset:
    """Ismni solishtirish uchun so'zlar to'plami (_name_words)."""
    return frozenset(_name_words(s))


_PATRO_MARK = frozenset({"ogli", "ugli", "qizi", "kizi"})
_PATRO_END = ("ovna", "evna", "ovich", "evich")


def _own_tokens(s) -> frozenset:
    """CRM ismidan OTASINING ISMISIZ so'zlar (2026-10-17, review):
    "Akmal o'g'li" / "Anvar qizi" (belgi va undan oldingi so'z) va
    -ovna/-evna/-ovich/-evich so'zlari tashlanadi. Aks holda postdagi
    "Akmal Sobirov" (ota) "Sobirov Abdurahmon Akmal o'g'li" (bola) ga,
    "Anvarova Ziyoda" — "Karimova Ziyoda Anvarovna" ga bog'lanardi."""
    w = _name_words(s)
    drop = set()
    for i, t in enumerate(w):
        if t in _PATRO_MARK:
            drop.update((i, i - 1))
        elif t.endswith(_PATRO_END):
            drop.add(i)
    return frozenset(t for i, t in enumerate(w) if i not in drop)


# --------------------------------------------------- ism o'xshashligi ---
def _lev1(a: str, b: str) -> bool:
    """Levenshtein masofasi <= 1: bitta harf almashgan, qo'shilgan yoki
    tushib qolgan (sobirov/sabirov, adildjonova/adiljonova)."""
    if a == b:
        return True
    if len(a) > len(b):
        a, b = b, a
    if len(b) - len(a) > 1:
        return False
    i = 0
    while i < len(a) and a[i] == b[i]:
        i += 1
    if len(a) == len(b):
        return a[i + 1:] == b[i + 1:]
    return a[i:] == b[i + 1:]


def _lev_le(a: str, b: str, k: int) -> bool:
    """Levenshtein masofasi <= k (k kichik; satr bo'yi farqi k dan katta
    bo'lsa yoki qator minimumi k dan oshsa — darhol yo'q)."""
    if abs(len(a) - len(b)) > k:
        return False
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i] + [0] * len(b)
        low = i
        for j, cb in enumerate(b, 1):
            v = min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb))
            cur[j] = v
            if v < low:
                low = v
        if low > k:
            return False
        prev = cur
    return prev[-1] <= k


@functools.lru_cache(maxsize=1 << 16)
def _tok_cost(a: str, b: str):
    """Ikki so'z o'xshashligi "narxi" — FAQAT xodimga nomzod tanlash va
    tartiblash uchun (2026-10-17, review: avtomat bog'lash — _tok_eq):
      0 — aynan bir xil;
      1 — yaqin: _tok_eq, yoki bosh qismi (qisqasi >= 4 harf, uzuni
          ko'pi bilan 3 harf qo'shadi), yoki Levenshtein <= 1, ikkalasi
          >= 5 harf;
      2 — bo'sh o'xshash: Levenshtein <= 2, ikkalasi >= 4 harf;
      3 — bo'sh o'xshash: umumiy boshi >= 6 harf va qisqasining 70% i
          (abdumannabxonov/abdumannabov);
      None — o'xshamaydi.
    1–3 HECH QACHON avtomat bog'lamaydi (aka-uka, adash ismlar ham shu
    yerga tushadi) — xodim ko'rib tanlaydi."""
    if a == b:
        return 0
    if _tok_eq(a, b):
        return 1
    s, lng = (a, b) if len(a) <= len(b) else (b, a)
    d = len(lng) - len(s)
    if len(s) >= 4 and d <= 3 and lng.startswith(s):
        return 1
    if len(s) >= 5 and d <= 1 and _lev1(s, lng):
        return 1
    if len(s) >= 4 and d <= 2 and _lev_le(s, lng, 2):
        return 2
    if len(s) >= 6:
        n = 0
        while n < len(s) and s[n] == lng[n]:
            n += 1
        if n >= max(6, math.ceil(0.7 * len(s))):
            return 3
    return None


# Avtomat bog'lashga yaraydigan yozilish farqlari (2026-10-17, review).
# x -> h normallashtirilgan, shuning uchun -xon = "hon".
_TG_SUFFIX = ("hon", "oy", "bek", "jon", "oyim")
_TG_SWAP = frozenset(frozenset(p) for p in ("ou", "ao", "pb", "kq", "dt"))
_TG_INS = frozenset("yd")
_TG_SUFFIX_MAX = max(len(x) for x in _TG_SUFFIX)


@functools.lru_cache(maxsize=1 << 16)
def _tok_eq(a: str, b: str) -> bool:
    """AVTOMAT bog'lash qoidasi — tor ro'yxat, umumiy tahrir masofasi
    EMAS (aka-uka va adash ismlar teng bo'lib qolmasin):
      * aynan bir xil;
      * ism oxiriga qo'shimcha: qisqasi >= 4 harf, uzuni = qisqasi +
        -xon/-oy/-bek/-jon/-oyim (sevinch/sevinchxon);
      * ikkalasi >= 5 harf, OXIRGI harfi bir xil va: bitta o/u, a/o,
        p/b, k/q, d/t almashgan (yoldashev/yuldashev, gaibova/gaipova)
        yoki bitta y / d qo'shilgan, boshida va oxirida emas (otaeva/
        otayeva, adiljonova/adildjonova).
    Shuning uchun -ov/-ova, Diyor/Diyora, Kamola/Kamila, Xasan/Husan,
    Aliyev/Valiyev, Nazarova/Nazirova — teng EMAS."""
    if a == b:
        return True
    s, lng = (a, b) if len(a) <= len(b) else (b, a)
    if len(s) >= 4 and lng.startswith(s) and lng[len(s):] in _TG_SUFFIX:
        return True
    if len(s) < 5 or s[-1] != lng[-1]:
        return False
    if len(s) == len(lng):
        diff = [(x, y) for x, y in zip(s, lng) if x != y]
        return len(diff) == 1 and frozenset(diff[0]) in _TG_SWAP
    if len(lng) == len(s) + 1:
        for i in range(1, len(lng) - 1):
            if lng[:i] + lng[i + 1:] == s:
                return lng[i] in _TG_INS
    return False


def _dels(w: str) -> set:
    """So'zning o'zi va bitta harfi tashlangan hamma ko'rinishlari."""
    return {w} | {w[:i] + w[i + 1:] for i in range(len(w))}


class _TgIndex:
    """Bir chaqiruv uchun o'quvchilar ismi indeksi (2026-10-17): HAMMA
    o'quvchi (istalgan holat), faqat id, full_name, branch_id — photo
    o'qilmaydi. So'z -> o'quvchilar; yaqin so'zlarni tez topish uchun
    ikki yordamchi jadval (bitta harf tashlangan ko'rinishlar va 1–4 harf
    qisqargan boshlar) — har post uchun hamma o'quvchi aylanib
    chiqilmaydi. toks / by_tok — otasining ismisiz (_own_tokens, moslik
    shu bilan); full — hamma so'zlar (faqat nomzod bahosi uchun)."""

    def __init__(self, rows):
        self.name, self.branch, self.toks, self.by_tok = {}, {}, {}, {}
        self.full = {}
        for sid, full_name, branch_id in rows:
            sid = int(sid)
            words = _own_tokens(full_name)
            self.name[sid] = full_name
            self.branch[sid] = branch_id
            self.toks[sid] = tuple(sorted(words))
            self.full[sid] = tuple(sorted(_name_tokens(full_name)))
            for w in words:
                self.by_tok.setdefault(w, set()).add(sid)
        self._del, self._pre, self._near = {}, {}, {}
        for w in self.by_tok:
            if len(w) >= 5:
                for v in _dels(w):
                    self._del.setdefault(v, set()).add(w)
            for k in range(max(4, len(w) - _TG_SUFFIX_MAX), len(w)):
                self._pre.setdefault(w[:k], set()).add(w)

    def near(self, q: str) -> set:
        """Indeksdagi q ga yaqin so'zlar — _tok_eq (avtomat) va _tok_cost
        <= 1 (nomzod) bo'ladigan hamma so'zlar shu to'plam ichida; q ning
        o'zi ham. Aniq qoidani chaqiruvchi tekshiradi."""
        got = self._near.get(q)
        if got is not None:
            return got
        out = {q} if q in self.by_tok else set()
        if len(q) >= 4:
            out |= self._pre.get(q, set())          # q — qisqasi
            for k in range(max(4, len(q) - _TG_SUFFIX_MAX), len(q)):
                if q[:k] in self.by_tok:            # q — uzuni
                    out.add(q[:k])
        if len(q) >= 5:
            for v in _dels(q):
                for w in self._del.get(v, ()):
                    if _lev1(q, w):
                        out.add(w)
        self._near[q] = out
        return out

    def sids(self, words) -> set:
        out = set()
        for w in words:
            out |= self.by_tok.get(w, set())
        return out


def _tg_index(db: Session) -> _TgIndex:
    S = models.Student
    return _TgIndex(db.query(S.id, S.full_name, S.branch_id).all())


def _assign(ptoks, stoks, eq) -> bool:
    """Postdagi har so'z o'quvchi ismining ALOHIDA (boshqa-boshqa) so'ziga
    mos keladimi — kichik ikki tomonlama moslik (so'zlar 2–5 ta)."""
    def go(i, used):
        if i == len(ptoks):
            return True
        return any(j not in used and eq(ptoks[i], t) and go(i + 1, used | {j})
                   for j, t in enumerate(stoks))
    return len(ptoks) <= len(stoks) and go(0, frozenset())


def _match_how(ix: _TgIndex, name) -> tuple:
    """(holat, [o'quvchi id], usul). Holat: "match" (aynan bitta),
    "ambiguous" (bir nechta), "unmatched". Usul: "exact" | "fuzzy" | None.
    Tartib: aynan moslik (postdagi so'zlar o'quvchi ismida, otasining
    ismisiz) bitta bo'lsa — o'sha; bir nechta bo'lsa — ambiguous
    (o'xshashlikka o'tilmaydi); hech kim bo'lmasa — _tok_eq (tor ro'yxat):
    bitta — match, bir nechta — ambiguous, hech kim — unmatched. Ismda
    kamida 2 so'z bo'lishi shart."""
    toks = _name_tokens(name)
    if len(toks) < 2:
        return "unmatched", [], None
    exact = None
    for w in toks:
        s = ix.by_tok.get(w, set())
        exact = set(s) if exact is None else exact & s
        if not exact:
            break
    if exact:
        return ("match" if len(exact) == 1 else "ambiguous"), sorted(exact), \
            "exact"
    pool = None
    for w in toks:
        s = ix.sids(ix.near(w))
        pool = s if pool is None else pool & s
        if not pool:
            break
    ptoks = sorted(toks)
    fz = sorted(sid for sid in (pool or ())
                if _assign(ptoks, ix.toks[sid], _tok_eq))
    if fz:
        return ("match" if len(fz) == 1 else "ambiguous"), fz, "fuzzy"
    return "unmatched", [], None


def _match(ix: _TgIndex, name) -> tuple:
    """(holat, [o'quvchi id]) — _match_how ning qisqasi."""
    st, ids, _how = _match_how(ix, name)
    return st, ids


def _best_cost(ptoks, stoks):
    """Yaqin nomzod bahosi: postdagi har so'z o'quvchining ALOHIDA so'ziga
    bo'sh o'xshash (_tok_cost <= 3), kamida bittasi qat'iy (<= 1); eng
    kichik yig'indi yoki None."""
    k, m = len(ptoks), len(stoks)
    if k > m:
        return None
    cost = [[_tok_cost(p, s) for s in stoks] for p in ptoks]
    if any(all(c is None for c in row) for row in cost):
        return None
    best = None
    for perm in itertools.permutations(range(m), k):
        cs = [cost[i][j] for i, j in enumerate(perm)]
        if None in cs or min(cs) > 1:
            continue
        t = sum(cs)
        if best is None or t < best:
            best = t
    return best


def _suggest(ix: _TgIndex, toks, exclude=(), ok=None,
             limit: int = TG_MAX_CANDIDATES) -> list:
    """Xodimga taklif (yaqin nomzodlar, avtomat bog'lanmaydi): kamida bitta
    so'zi yaqin o'quvchilar ichidan _best_cost bo'yicha eng yaqinlari
    (baho — ismning hamma so'zlari bilan, otasining ismi ham). ok —
    chegara (filial rahbari faqat o'z filiali)."""
    if len(toks) < 2 or limit <= 0:
        return []
    ptoks = sorted(toks)
    pool = set()
    for w in ptoks:
        pool |= ix.sids(ix.near(w))
    scored = []
    for sid in pool:
        if sid in exclude or (ok is not None and not ok(sid)):
            continue
        c = _best_cost(ptoks, ix.full[sid])
        if c is not None:
            scored.append((c, (ix.name.get(sid) or "").lower(), sid))
    scored.sort()
    return [sid for _c, _n, sid in scored[:limit]]


# ------------------------------------------------------- fayl va natija ---
def _tg_path() -> str:
    return os.environ.get("WORDBANK_TG_FILE") or TG_FILE


def _tg_read(path=None):
    """(xom baytlar, [(tartib raqami, qator), ...]) yoki None (fayl yo'q).
    Tartib raqami — "results" ro'yxatidagi o'rni (xodim yo'llari qatorni
    shu bilan topadi); lug'at bo'lmagan yozuv tashlanadi, raqamlar
    siljimaydi."""
    try:
        with open(path or _tg_path(), "rb") as f:
            raw = f.read()
    except OSError:
        return None
    data = json.loads(raw.decode("utf-8-sig"))
    rows = data.get("results", []) if isinstance(data, dict) else data
    if not isinstance(rows, list):
        rows = []
    return raw, [(i, r) for i, r in enumerate(rows) if isinstance(r, dict)]


def _tg_post(r: dict) -> int:
    try:
        return int(r.get("post") or 0)
    except (TypeError, ValueError):
        return 0


def _tg_day(r: dict):
    try:
        return date.fromisoformat(str(r.get("date"))[:10])
    except ValueError:
        return None


def _tg_link(r: dict) -> str:
    return f"{TG_CHANNEL}{_tg_post(r)}"


def _tg_key(r: dict) -> str:
    """"Bizniki emas" ro'yxati kaliti: "post:ism"."""
    return f"{_tg_post(r)}:{str(r.get('name') or '').strip()}"


def _tg_cert(r: dict):
    """(kind, level, score, note_suffix) yoki None (noma'lum imtihon)."""
    ex = str(r.get("exam") or "").lower()
    score = r.get("score")
    try:
        score = float(score) if score not in (None, "") else None
    except (TypeError, ValueError):
        score = None
    if ex == "ielts":
        if score is None or not (1.0 <= score <= 9.0):
            return None
        return "ielts", f"{score:.1f}", score, ""
    if ex in ("multilevel", "cefr"):
        lvl = str(r.get("level") or "").strip().upper()
        if lvl not in _CEFR:
            return None
        return "cefr", lvl, score, " · Multilevel" if ex == "multilevel" else ""
    return None


_NUM_RE = re.compile(r"\d+(?:[.,]\d+)?")
_CEFR_RE = re.compile(r"\b([ABC][12])\b")


def _lvl_key(kind, level, score) -> str:
    """"Bir xil natija" kaliti (tur ichida). Xodim CRM'da darajani erkin
    yozadi ("7", "7.0", "IELTS 7", "b2", "B2 (61)") — solishtirish shu
    ko'rinishlarni bitta kalitga keltirib qilinadi (IELTS — "7.0",
    CEFR — "B2")."""
    lv = str(level or "").strip()
    if kind == "ielts":
        m = _NUM_RE.search(lv)
        x = None
        try:
            if m:
                x = float(m.group(0).replace(",", "."))
            elif score is not None:
                x = float(score)
        except (TypeError, ValueError):
            x = None
        return f"{x:.1f}" if x is not None else lv.upper()
    m = _CEFR_RE.search(lv.upper())
    return m.group(1) if m else lv.upper()


def _has_same(db: Session, sid: int, kind: str, level, score) -> int:
    """O'quvchida shu tur va shu darajadagi sertifikatlar SONI (takror
    qoidasi — post havolasi ahamiyatsiz)."""
    C = models.Certificate
    want = _lvl_key(kind, level, score)
    return sum(1 for lv, sc in db.query(C.level, C.score)
               .filter(C.student_id == sid, C.kind == kind)
               if _lvl_key(kind, lv, sc) == want)


def _tg_create(db: Session, sid: int, r: dict, cert, by: str, user,
               how: str, name=None, branch_id=None):
    """Telegram natijasidan Certificate. Avtomat import ham, xodimning
    qo'lda bog'lashi ham SHU funksiya orqali — tur, daraja, ball, sana va
    izoh ko'rinishi bir xil bo'lsin. Audit yoziladi; commit QILMAYDI."""
    kind, level, score, suffix = cert
    link = _tg_link(r)
    c = models.Certificate(student_id=sid, kind=kind, level=level,
                           score=score, date=_tg_day(r) or date.today(),
                           note=f"Telegram: {link}{suffix}", created_by=by)
    db.add(c)
    db.flush()
    audit.log(db, user, entity="student", action="update",
              entity_id=sid, entity_label=name, field="certificate",
              new_value=crm_badge_out(c)["label"], note=f"{how}: {link}",
              branch_id=branch_id)
    return c


def _tg_dismissed(db: Session) -> set:
    row = db.query(models.IntegrationSetting).get(TG_DISMISSED_KEY)
    try:
        v = json.loads(row.value) if row is not None and row.value else []
    except ValueError:
        v = []
    return {str(x) for x in v} if isinstance(v, list) else set()


def _tg_lk(cert) -> tuple:
    """(tur, daraja kaliti) — "bir xil natija"."""
    return cert[0], _lvl_key(cert[0], cert[1], cert[2])


def _tg_rkey(r: dict, cert) -> str:
    """Xodim qarori kaliti: "post:ism:tur:daraja" — bitta postda bir
    odamning ikki natijasi (4691: IELTS 7.0 va 7.5) alohida."""
    return "%s:%s:%s" % ((_tg_key(r),) + _tg_lk(cert))


def _tg_links(db: Session) -> dict:
    """{"post:ism:tur:daraja": sid} — xodim bog'lagan natijalar."""
    row = db.query(models.IntegrationSetting).get(TG_LINKS_KEY)
    try:
        v = json.loads(row.value) if row is not None and row.value else {}
    except ValueError:
        v = {}
    out = {}
    for k, sid in (v.items() if isinstance(v, dict) else ()):
        if isinstance(sid, int) and not isinstance(sid, bool):
            out[str(k)] = sid
    return out


def _tg_items(items) -> list:
    """[(tartib raqami, qator, natija)] — natijasi tanilganlari."""
    out = [(i, r, _tg_cert(r)) for i, r in items]
    return [x for x in out if x[2] is not None]


class _TgCtx:
    """Bir chaqiruv (seed yoki xodim ro'yxati) uchun umumiy ma'lumot va
    BITTA holat qoidasi (2026-10-17, review) — seed xodim ko'rgan holatdan
    boshqacha qaror qilmasin."""

    def __init__(self, db: Session, valid):
        self.ix = _tg_index(db)
        self.have, self.by_link = _tg_cert_maps(db)
        self.dismissed = _tg_dismissed(db)
        self.links = _tg_links(db)
        # Bitta postda bir xil natijali bir nechta ODAM bo'lsa, havola
        # kimniki ekanini xodim qarori yoki ism hal qiladi
        self.names = {}
        for _i, r, cert in valid:
            self.names.setdefault((_tg_post(r),) + _tg_lk(cert), set()).add(
                _name_tokens(r.get("name")))

    def state(self, r: dict, cert) -> tuple:
        """(holat, bog'langan sid, moslik holati, ids, usul).
        Tartib: 1) haqiqiy bog'lanish — xodim qarori (o'quvchida shu
        natija hali bor) yoki shu post havolali Certificate; 2) "bizniki
        emas"; 3) taxmin — AYNAN ism bitta o'quvchini topadi va unda shu
        tur/daraja bor (havolasiz; o'xshashlik bilan taxmin qilinmaydi);
        4) ambiguous / unmatched."""
        post, lk = _tg_post(r), _tg_lk(cert)
        st, ids, how = _match_how(self.ix, r.get("name"))
        linked = self.links.get(_tg_rkey(r, cert))
        if linked is not None and lk not in self.have.get(linked, ()):
            linked = None              # sertifikat o'chirilgan / o'quvchi yo'q
        if linked is None:
            sids = self.by_link.get((post,) + lk) or []
            if len(self.names.get((post,) + lk, ())) <= 1:
                linked = sids[0] if sids else None
            else:
                hit = [s for s in sids if s in ids]
                linked = hit[0] if hit else None
        if linked is not None:
            return "linked", linked, st, ids, how
        if _tg_key(r) in self.dismissed:
            return "dismissed", None, st, ids, how
        if st == "match" and how == "exact" and lk in self.have.get(ids[0], ()):
            return "linked", ids[0], st, ids, how
        return ("ambiguous" if st == "ambiguous" else "unmatched",
                None, st, ids, how)

    def add(self, sid: int, r: dict, cert) -> None:
        """Shu chaqiruvda yaratilgan Certificate xaritalarga."""
        lk = _tg_lk(cert)
        self.have.setdefault(sid, set()).add(lk)
        self.by_link.setdefault((_tg_post(r),) + lk, []).append(sid)


def _tg_seed_lock(db: Session) -> bool:
    """Postgres: tranzaksiya qulfi (commit/rollback bilan o'zi bo'shaydi,
    wordbank._try_lock bilan bir xil). Boshqa nusxa seed qilayotgan
    bo'lsa — False, kutilmaydi. SQLite'da shart emas."""
    try:
        if db.bind.dialect.name != "postgresql":
            return True
        from sqlalchemy import text as sa_text
        return bool(db.execute(
            sa_text("SELECT pg_try_advisory_xact_lock(:k)"),
            {"k": TG_SEED_LOCK}).scalar())
    except Exception:  # noqa: BLE001 - qulf olinmasa ham belgi tekshiriladi
        return True


def seed_telegram(db: Session, path=None):
    """Bir martalik (fayl mazmuni bo'yicha) import. Qaytaradi: None — bu
    fayl allaqachon import qilingan, boshqa nusxa hozir import qilyapti
    yoki fayl yo'q; aks holda hisobot (faqat sonlar va post raqamlari;
    fuzzy — o'xshashlik bilan yaratilganlar soni, dismissed — xodim
    "bizniki emas" deganlari). Holat — _TgCtx.state (xodim ro'yxati bilan
    bir xil): bog'langan natija (xodim bog'lagani ham) "bor" sanaladi."""
    from common import _seed_done, _seed_mark
    got = _tg_read(path)
    if got is None:
        return None
    raw, items = got
    key = f"{TG_SEED}:{hashlib.sha256(raw).hexdigest()[:12]}"
    if _seed_done(db, key):
        return None
    if not _tg_seed_lock(db):
        return None                    # boshqa nusxa ishlayapti
    # Belgilar keshi eskirgan bo'lishi mumkin — qulf ichida bazadan
    if db.query(models.SeedMark).get(key) is not None:
        db.rollback()
        _seed_mark(db, key)
        return None
    ctx = _TgCtx(db, _tg_items(items))
    rep = {"created": 0, "existing": 0, "fuzzy": 0, "unmatched": [],
           "ambiguous": [], "skipped": [], "dismissed": []}
    touched = set()
    S = models.Student
    for _i, r in items:
        post = _tg_post(r)
        cert = _tg_cert(r)
        if cert is None or len(_name_tokens(r.get("name"))) < 2:
            rep["skipped"].append(post)
            continue
        status, _sid, st, ids, how = ctx.state(r, cert)
        if status == "linked":
            rep["existing"] += 1
            continue
        if status == "dismissed":
            rep["dismissed"].append(post)
            continue
        if st != "match":
            rep[st].append(post)
            continue
        sid = ids[0]
        kind, level, score, _sfx = cert
        # Xodim shu o'quvchiga bir vaqtda bog'layotgan bo'lsa (tg_link
        # ham shu qatorni qulflaydi) — takror yaratilmasin
        db.query(S.id).filter(S.id == sid).with_for_update().first()
        if _has_same(db, sid, kind, level, score):
            rep["existing"] += 1
            continue
        _tg_create(db, sid, r, cert, TG_BY, None,
                   "Telegram kanalidan avtomat", ctx.ix.name.get(sid),
                   ctx.ix.branch.get(sid))
        ctx.add(sid, r, cert)
        rep["created"] += 1
        if how == "fuzzy":
            rep["fuzzy"] += 1
        touched.add(sid)
    rep["at"] = datetime.utcnow().isoformat(timespec="seconds")
    row = db.query(models.IntegrationSetting).get(TG_REPORT_KEY)
    if row is None:
        db.add(models.IntegrationSetting(key=TG_REPORT_KEY,
                                         value=json.dumps(rep)))
    else:
        row.value = json.dumps(rep)
    # Sertifikatlar, hisobot va belgi — BITTA commit (qulf shu bilan
    # bo'shaydi; keyingi nusxa belgini ko'radi). Qulfsiz (SQLite) yoki
    # qulf olinmagan holatda boshqa nusxa belgini oldinroq qo'ygan bo'lsa —
    # bu nusxaning hamma yozuvi bekor qilinadi (takror sertifikat yo'q).
    db.add(models.SeedMark(key=key))
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        _seed_mark(db, key)
        return None
    _seed_mark(db, key)                # faqat kesh (qator bor)
    for sid in sorted(touched):
        try:
            with db.begin_nested():
                _hall(db, sid)
        except Exception as e:  # noqa: BLE001 - tarix keyin ham yangilanadi
            print(f"[tg-certs] tarix {sid}: {e!r}", flush=True)
    db.commit()
    _board_cache_clear()
    return rep


def tg_report(db: Session):
    """Oxirgi import hisoboti (faqat sonlar va post raqamlari) yoki None."""
    row = db.query(models.IntegrationSetting).get(TG_REPORT_KEY)
    try:
        return json.loads(row.value) if row is not None and row.value else None
    except ValueError:
        return None


# ===================================================== XODIM: TELEGRAM ===
# 2026-10-17: avtomat import bog'lay olmagan natijalarni xodim o'zi
# bog'laydi yoki "bizniki emas" deb yashiradi. Faqat VOCAB_CERT_REVOKE
# (asoschi, filial rahbari, o'quv bo'limi rahbari); "So'z bilish" filial
# bayrog'iga BOG'LIQ EMAS. Filial rahbari faqat o'z filiali o'quvchisini
# ko'radi (nomzodlar) va bog'laydi — chegara tasdiqdagi bilan bir xil
# (_scope / _in_scope; filialsiz o'quvchi ham). Qaror: bog'langan natija
# DARHOL tasdiqlangan sertifikat (seed_telegram bilan bir xil Certificate).
# Holat JONLI: linked — shu post havolasi bilan shu tur/daraja Certificate
# bor yoki o'xshashlik aniq bitta o'quvchini topib, unda shu tur/daraja
# bor; dismissed — "wordbank_tg_dismissed" ro'yxatida; qolgani
# ambiguous / unmatched. O'xshashlik bitta o'quvchini topsa-yu, unda
# sertifikat bo'lmasa (masalan o'quvchi importdan keyin qo'shilgan) —
# unmatched, o'sha o'quvchi nomzodlar boshida (bitta bosish bilan).
#
# 2026-10-17 (review): holat — _TgCtx.state (seed bilan bir xil):
# xodim qarori ("wordbank_tg_links") va shu post havolali Certificate —
# bog'lanish; havolasiz taxmin faqat AYNAN ism bilan (o'xshash adashning
# sertifikati qatorni "bog'langan" qilib qo'ymasin). Bog'langan natijani
# boshqa o'quvchiga bog'lab bo'lmaydi (409, ikki xodim / eski ro'yxat;
# javobda egasining ismi — faqat xodim chegarasida bo'lsa). O'quvchida
# shu natija allaqachon bo'lsa (masalan ikki postda bir natija, yoki xodim
# CRM'ga o'zi kiritgan) — 409; {"existing": true} bilan qayta yuborilsa
# yangi sertifikat YARATILMAYDI, faqat "bog'langan" deb yoziladi. Filial
# rahbari boshqa filial o'quvchisining ismini ko'rmaydi (student_id /
# student_name — null).
def _tg_staff(user) -> None:
    if not has_role(user, roles.VOCAB_CERT_REVOKE):
        raise HTTPException(403, "Bu amal uchun ruxsatingiz yo'q")


def _tg_read_staff():
    """Xodim yo'llari uchun _tg_read: buzilgan fayl — tushunarli 500."""
    try:
        return _tg_read()
    except (ValueError, UnicodeDecodeError):
        raise HTTPException(500, "Telegram natijalari fayli buzilgan")


def _sid_ok(sc, branch_id) -> bool:
    """_in_scope bilan bir xil filial qoidasi (o'quvchi filiali bo'yicha;
    filialsiz o'quvchi ham)."""
    kind, ids = sc
    if kind == "all":
        return True
    if kind == "branches":
        return branch_id is None or branch_id in ids
    return False


def _tg_cert_maps(db: Session) -> tuple:
    """have: {sid: {(tur, daraja kaliti)}};
    by_link: {(post, tur, daraja kaliti): [sid, ...]} — izohdagi post
    raqami ANIQ solishtiriladi (".../101" ".../1012" ga mos kelmasin)."""
    C = models.Certificate
    have, by_link = {}, {}
    for sid, kind, level, score, note in (
            db.query(C.student_id, C.kind, C.level, C.score, C.note)
            .filter(C.kind.in_(CRM_KINDS)).order_by(C.id)):
        lk = (kind, _lvl_key(kind, level, score))
        have.setdefault(int(sid), set()).add(lk)
        m = _TG_POST_RE.search(note or "")
        if m:
            by_link.setdefault((int(m.group(1)),) + lk, []).append(int(sid))
    return have, by_link


def _tg_ctx(db: Session) -> tuple:
    """(natijasi tanilgan qatorlar, _TgCtx) yoki (None, None) — fayl yo'q."""
    got = _tg_read_staff()
    if got is None:
        return None, None
    valid = _tg_items(got[1])
    return valid, _TgCtx(db, valid)


def _tg_state_at(db: Session, idx: int) -> tuple:
    """Bitta qatorning jonli holati: (holat, bog'langan sid | None)."""
    valid, ctx = _tg_ctx(db)
    for i, r, cert in valid or ():
        if i == idx:
            return ctx.state(r, cert)[:2]
    raise HTTPException(404, "Natija topilmadi")


def _tg_view(db: Session, user, want: str = "all", only=None) -> tuple:
    """(qatorlar, sonlar). want — holat yoki "all"; only — faqat shu
    tartib raqamlari (sonlar baribir hamma qatordan)."""
    counts = {s: 0 for s in TG_STATUSES}
    valid, ctx = _tg_ctx(db)
    if valid is None:
        return [], counts
    ix = ctx.ix
    sc = _scope(db, user)
    bname = {bid: nm for bid, nm in db.query(models.Branch.id,
                                             models.Branch.name)}

    def ok(sid):
        return _sid_ok(sc, ix.branch.get(sid))

    out = []
    for i, r, cert in valid:
        post = _tg_post(r)
        status, linked, st, ids, _how = ctx.state(r, cert)
        counts[status] += 1
        if only is not None and i not in only:
            continue
        if want != "all" and status != want:
            continue
        pick = []
        if status != "linked":
            if st == "ambiguous":
                pick = sorted((s for s in ids if ok(s)),
                              key=lambda s: ((ix.name.get(s) or "").lower(), s))
            else:
                first = [ids[0]] if st == "match" and ok(ids[0]) else []
                pick = first + _suggest(
                    ix, _name_tokens(r.get("name")), exclude=set(first), ok=ok,
                    limit=TG_MAX_CANDIDATES - len(first))
        kind, level, score, suffix = cert
        link = _tg_link(r)
        day = _tg_day(r)
        # Boshqa filial o'quvchisi — holat "linked", ismi va id'si yo'q
        if linked is not None and not ok(linked):
            linked = None
        out.append({
            "row": i,
            "post": post,
            "date": day.isoformat() if day else str(r.get("date") or "")[:10],
            "name": str(r.get("name") or "").strip(),
            "exam": str(r.get("exam") or "").lower(),
            "label": crm_badge_out(SimpleNamespace(
                id=0, kind=kind, level=level, score=score, date=None,
                note=f"Telegram: {link}{suffix}"))["label"],
            "link": link,
            "status": status,
            "student_id": linked,
            "student_name": ix.name.get(linked) if linked is not None
            else None,
            "candidates": [{"id": s, "name": ix.name.get(s),
                            "branch": bname.get(ix.branch.get(s))}
                           for s in pick[:TG_MAX_CANDIDATES]],
        })
    out.sort(key=lambda x: (x["date"], x["post"], -x["row"]), reverse=True)
    return out, counts


def _tg_pick(raw_row) -> tuple:
    """(tartib raqami, qator, natija) yoki 404."""
    try:
        idx = int(str(raw_row))
    except (TypeError, ValueError):
        raise HTTPException(404, "Natija topilmadi")
    got = _tg_read_staff()
    for i, r in (got[1] if got else []):
        if i == idx:
            cert = _tg_cert(r)
            if cert is not None:
                return i, r, cert
            break
    raise HTTPException(404, "Natija topilmadi")


def _tg_one(db: Session, user, idx: int) -> dict:
    rows, _counts = _tg_view(db, user, "all", only={idx})
    return rows[0]


@router.get("/api/wordbank/telegram-results")
def tg_results(status: str = None, db: Session = Depends(get_db),
               user=Depends(get_current_user)):
    """Kanal natijalari ro'yxati (standart — unmatched; eng yangi post
    birinchi) va hamma holatlar soni."""
    _tg_staff(user)
    want = (status or "unmatched").strip().lower()
    if want not in TG_STATUSES + ("all",):
        raise HTTPException(400, "status: " + ", ".join(TG_STATUSES)
                            + " yoki all")
    rows, counts = _tg_view(db, user, want)
    return {"rows": rows, "counts": counts}


def _tg_links_put(db: Session, rkey: str, sid: int) -> None:
    """Xodim qarorini "wordbank_tg_links" ga yozadi (commit QILMAYDI).
    Qator FOR UPDATE bilan o'qiladi (ikki xodim bir vaqtda — biri
    yo'qolmasin); birinchi yaratishdagi to'qnashuv savepoint ichida."""
    IS = models.IntegrationSetting
    q = db.query(IS).filter(IS.key == TG_LINKS_KEY).with_for_update()
    srow = q.first()
    if srow is None:
        try:
            with db.begin_nested():
                db.add(IS(key=TG_LINKS_KEY, value="{}"))
        except IntegrityError:
            pass                       # boshqa xodim hozirgina yaratdi
        srow = q.first()
    try:
        cur = json.loads(srow.value) if srow.value else {}
    except ValueError:
        cur = {}
    if not isinstance(cur, dict):
        cur = {}
    cur[rkey] = int(sid)
    srow.value = json.dumps(cur, ensure_ascii=False)


@router.post("/api/wordbank/telegram-results/{row}/link")
def tg_link(row: str, payload=Body(default=None),
            db: Session = Depends(get_db), user=Depends(get_current_user)):
    """Natijani o'quvchiga bog'lash: seed_telegram bilan AYNAN bir xil
    Certificate (created_by — xodim), audit, tarix va reyting keshi;
    qaror "wordbank_tg_links" ga ham yoziladi. Natija boshqa o'quvchiga
    bog'langan bo'lsa — 409 (TG_TAKEN); o'quvchida shu tur/daraja bo'lsa —
    409 (TG_DUP), {"existing": true} bilan — sertifikat yaratilmaydi, qator
    shu o'quvchiga bog'langan deb yoziladi; begona filial — 404."""
    _tg_staff(user)
    idx, r, cert = _tg_pick(row)
    body = WB._body(payload)
    raw_sid = body.get("student_id")
    try:
        if isinstance(raw_sid, bool):
            raise ValueError
        sid = int(str(raw_sid).strip())
    except (TypeError, ValueError):
        _bad("O'quvchini tanlang")
    existing = body.get("existing", False)
    if not isinstance(existing, bool):
        _bad("existing: true yoki false")
    if not 0 < sid <= _ID_MAX:
        raise HTTPException(404, "O'quvchi topilmadi")
    S = models.Student
    sc = _scope(db, user)
    st = db.query(S.id, S.full_name, S.branch_id).filter(S.id == sid).first()
    if st is None or not _in_scope(db, sc, SimpleNamespace(
            student_id=sid, branch_id_snap=None)):
        raise HTTPException(404, "O'quvchi topilmadi")
    kind, level, score, _sfx = cert
    # Ikki xodim bir vaqtda bossa: Postgres'da o'quvchi qatori qulflanadi;
    # SQLite'da (no-op) yozilgandan keyingi qayta sanash ushlaydi.
    db.query(S.id).filter(S.id == sid).with_for_update().first()
    status, owner = _tg_state_at(db, idx)
    if status == "linked" and owner != sid:
        # Ikkinchi xodim / eski ro'yxat: boshqa o'quvchiga ham berilmasin.
        # Ism faqat xodim chegarasidagi o'quvchi bo'lsa aytiladi.
        o = db.query(S.full_name, S.branch_id).filter(S.id == owner).first()
        msg = TG_TAKEN
        if o is not None and _sid_ok(sc, o.branch_id) and o.full_name:
            msg = f"{TG_TAKEN}: {o.full_name}"
        raise HTTPException(409, msg)
    rkey = _tg_rkey(r, cert)
    link = _tg_link(r)
    if _has_same(db, sid, kind, level, score):
        if not existing:
            raise HTTPException(409, TG_DUP)
        # Natija o'quvchida allaqachon bor — yangi sertifikat yo'q, faqat
        # "bog'langan" qarori (qator ro'yxatda abadiy osilib qolmasin)
        _tg_links_put(db, rkey, sid)
        label = crm_badge_out(SimpleNamespace(
            id=0, kind=kind, level=level, score=score, date=None,
            note=f"Telegram: {link}{_sfx}"))["label"]
        audit.log(db, user, entity="settings", action="update",
                  entity_label=f"Telegram natijasi #{_tg_post(r)}",
                  field=TG_LINKS_KEY, new_value=st.full_name,
                  note=f"{str(r.get('name') or '').strip()} — {label} "
                       f"({link}): o'quvchida allaqachon bor",
                  branch_id=st.branch_id)
        db.commit()
        return _tg_one(db, user, idx)
    who = getattr(user, "full_name", None) or getattr(user, "username", None)
    _tg_create(db, sid, r, cert, who, user,
               "Telegram kanalidan qo'lda bog'landi", st.full_name,
               st.branch_id)
    if _has_same(db, sid, kind, level, score) > 1:
        db.rollback()
        raise HTTPException(409, TG_DUP)
    _tg_links_put(db, rkey, sid)
    try:
        with db.begin_nested():
            _hall(db, sid)
    except Exception as e:  # noqa: BLE001 - tarix keyin ham yangilanadi
        print(f"[tg-certs] tarix {sid}: {e!r}", flush=True)
    db.commit()
    _board_cache_clear()
    return _tg_one(db, user, idx)


@router.post("/api/wordbank/telegram-results/{row}/dismiss")
def tg_dismiss(row: str, payload=Body(default=None),
               db: Session = Depends(get_db), user=Depends(get_current_user)):
    """"Bizniki emas" — ro'yxatdan yashirish; {"undo": true} — qaytarish.
    O'quvchiga bog'langan natijani yashirib bo'lmaydi (409). Kalit
    "post:ism": shu postdagi shu odamning hamma natijasi birga yashiriladi
    ("bizniki emas" — natija emas, odam haqida)."""
    _tg_staff(user)
    idx, r, cert = _tg_pick(row)
    body = WB._body(payload)
    undo = body.get("undo", False)
    if not isinstance(undo, bool):
        _bad("undo: true yoki false")
    if not undo and _tg_state_at(db, idx)[0] == "linked":
        raise HTTPException(409, "Bu natija o'quvchiga bog'langan")
    key, post, link = _tg_key(r), _tg_post(r), _tg_link(r)
    label = crm_badge_out(SimpleNamespace(
        id=0, kind=cert[0], level=cert[1], score=cert[2], date=None,
        note=f"Telegram: {link}{cert[3]}"))["label"]
    IS = models.IntegrationSetting
    for attempt in range(2):
        srow = (db.query(IS).filter(IS.key == TG_DISMISSED_KEY)
                .with_for_update().first())
        try:
            cur = json.loads(srow.value) if srow is not None and srow.value \
                else []
        except ValueError:
            cur = []
        cur = [str(x) for x in cur] if isinstance(cur, list) else []
        if (key in cur) != undo:
            break                      # o'zgarish yo'q
        cur = [x for x in cur if x != key] if undo else cur + [key]
        if srow is None:
            db.add(IS(key=TG_DISMISSED_KEY, value=json.dumps(cur)))
        else:
            srow.value = json.dumps(cur)
        audit.log(db, user, entity="settings", action="update",
                  entity_label=f"Telegram natijasi #{post}",
                  field=TG_DISMISSED_KEY,
                  new_value="qaytarildi" if undo else "bizniki emas",
                  note=f"{str(r.get('name') or '').strip()} — {label} "
                       f"({link})")
        try:
            db.commit()
            break
        except IntegrityError:
            # Birinchi yozuvni ikki xodim bir vaqtda yaratdi — qayta o'qib,
            # bir marta takrorlanadi.
            db.rollback()
            if attempt:
                raise HTTPException(409, "Qayta urinib ko'ring")
    return _tg_one(db, user, idx)
