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
import hashlib
import json
import math
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import date, datetime, timedelta

from fastapi import APIRouter, Body, Depends, HTTPException, Request, Response
from sqlalchemy import case, func, or_, select, update as sa_update
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


def confirmed_badges(db: Session, student_ids=None) -> dict:
    """{student_id: [badge_out, ...]} — eng oxirgisi birinchi. FAQAT
    tasdiqlanganlar: pending / rejected / withdrawn / revoked natijasi
    bu yerdan HECH QACHON chiqmaydi. student_ids=None — hammasi."""
    rows = []
    if student_ids is None:
        rows = db.query(CU).filter(CU.status == CONFIRMED).all()
    else:
        ids = _ids(student_ids)
        for i in range(0, len(ids), _IN_CHUNK):
            rows += (db.query(CU)
                     .filter(CU.student_id.in_(ids[i:i + _IN_CHUNK]),
                             CU.status == CONFIRMED).all())
    out: dict = {}
    for u in sorted(rows, key=_sort_key, reverse=True):
        out.setdefault(int(u.student_id), []).append(badge_out(u))
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
    begona yozuv haqida hech narsa bilinmasin)."""
    try:
        return int(str(raw))
    except (TypeError, ValueError):
        raise HTTPException(404, "Sertifikat topilmadi")


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
