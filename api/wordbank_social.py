"""LUG'AT BANKI — "So'z bilish" reytingi va TARIX (2026-10-17, 2–3-bosqich).

Sabab (Jahongir, OWNER_DECISIONS):
  D2 — "so'z bilish bo'yicha jadval tursin": tasdiqlangan so'zlar soni
       bo'yicha reyting (guruh / filial / butun markaz), haftalik o'sish;
  D4 — "o'quvchilar ro'yxatidan chiqib ketsa ham natijasi tarixda
       qolaversin": wordbank_hall (student_ref, FK yo'q) — o'quvchi
       ketsa, arxivlansa yoki butunlay o'chirilsa ham eng yaxshi natija,
       tugatilgan darajalar va tasdiqlangan sertifikat qoladi;
  D5 — maksimal motivatsiya (keyingi o'ringa N ta so'z, birinchi bo'lib
       tugatganlar).

Shartnoma: scratchpad/vocab/PHASE23_CONTRACT.md (yo'llar, javob
shakllari, umumiy funksiyalar). Umumiy funksiyalar imzosi o'zgarmaydi —
ularni wordbank.py, wordbank_certs.py va students.py chaqiradi.

Yo'llar (2026-10-17):
  GET /api/wordbank/leaderboard        — o'quvchi: guruh / filial / markaz,
                                         Jami / Shu hafta / Tarix;
  GET /api/wordbank/teacher/students   — ustoz (o'z guruhi) va o'quv
                                         bo'limi: guruh bo'yicha so'zlar.
Yordamchilar: me_extras (/api/wordbank/me qo'shimchalari), parent_payload
(ota-ona sahifasi, entry.py: parent_view).

Qoidalar:
  * o'quvchi bo'limi bilan bir xil darvoza: wordbank._student (bayroq
    o'chiq / filial yoqilmagan — 404);
  * o'quvchiga ko'rinadigan ism — student_app._mask ("Aziz K."),
    Student.photo HECH QACHON tanlanmaydi (faqat aniq ustunlar);
  * tasdiqlanmagan sertifikat natijasi hech qayerda chiqmaydi — faqat
    wordbank_certs.latest_badges / confirmed_badges (status="confirmed");
  * reyting coin ham, XP ham bermaydi; sertifikat o'ringa ta'sir qilmaydi;
  * "tekshirilmoqda" belgisi — faqat ko'rsatish (coinni to'xtatmaydi).

Hisob: tasdiqlangan son — wordbank_student_words.known = 1 (faol so'zlar,
/me bilan bir xil), JONLI COUNT. Butun markaz bo'yicha bitta GROUP BY
jarayon ichida AGG_TTL soniya keshlanadi; o'quvchining O'Z qatori esa
har so'rovda jonli o'qiladi (yangi so'zi darhol ko'rinsin). Hafta —
Toshkent dushanbasi 00:00 dan (bazadagi vaqtlar naive UTC).

2026-10-17 (review, tezlik): /me va ota-ona sahifasi (ranks_for) faqat
"known" qismini oladi (darajalar va "tekshirilmoqda" hisobisiz), 0 so'zli
o'quvchida umumiy hisob umuman qilinmaydi; "tekshirilmoqda" belgisi
faqat ko'rinadigan qatorlar (TOP_N + o'zi) uchun hisoblanadi.
"""
import os
import sys
import threading
import time as _time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import date, datetime, time, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import case, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

import audit
import models
import roles
import wordbank as WB
import wordbank_core as WCORE
from auth import get_current_user, require_role
from common import _get_group_in_scope, in_group, student_group_ids
from database import get_db

router = APIRouter()

# Reyting sozlamalari (shartnoma §A). Testlar AGG_TTL = 0 qilib keshni
# o'chiradi yoki clear_cache() chaqiradi.
AGG_TTL = 60                 # s — jarayon ichidagi umumiy hisob keshi
TOP_N = 50                   # ro'yxatda nechta qator
FLAG_WEEK_GAIN = 550         # shu haftada bundan ko'p — "tekshirilmoqda"
FLAG_SUSPECT_SHARE = 0.30    # shu haftadagi P javoblarning shubhali ulushi
FLAG_MIN_P = 20              # ... kamida shuncha P javob bo'lsa
HALL_STEP = 10               # /me: eng yaxshi natija shuncha o'ssa yangilanadi

SCOPES = ("group", "branch", "school")
PERIODS = ("total", "week", "history")
LIVE = ("active", "trial")   # joriy reytingdagi holatlar (XP reytingi kabi)

S = models.Student
W = models.WordbankWord
SW = models.WordbankStudentWord
SI = models.WordbankSessionItem
BA = models.WordbankBandAward
ST = models.WordbankSizeTest
HALL = models.WordbankHall
SGL = models.StudentGroupLink
CE = models.CoinEntry

_CACHE: dict = {}
_CACHE_LOCK = threading.Lock()
_IN_CHUNK = 500


def clear_cache() -> None:
    """Reyting keshini tozalash (testlar va yozuvdan keyin)."""
    with _CACHE_LOCK:
        _CACHE.clear()


# ------------------------------------------------------- yordamchilar ---
def _dt(v):
    """SQLite MAX(CASE ...) ba'zan matn qaytaradi — datetime ga."""
    if v is None or isinstance(v, datetime):
        return v
    if isinstance(v, date):
        return datetime.combine(v, time())
    try:
        return datetime.fromisoformat(str(v).replace(" ", "T"))
    except ValueError:
        return None


def _mask(name) -> str:
    from student_app import _mask as _m        # sikl bo'lmasin — kech import
    return _m(name or "") or "O'quvchi"


def _initials(name) -> str:
    parts = (name or "").split()
    out = "".join(p[0] for p in parts[:2] if p).upper()
    return out or "?"


def _popcount(x) -> int:
    return bin(int(x or 0)).count("1")


def _chunks(ids):
    ids = sorted({int(i) for i in ids if i is not None})
    for i in range(0, len(ids), _IN_CHUNK):
        yield ids[i:i + _IN_CHUNK]


def week_bounds():
    """(Toshkent dushanbasi sanasi, o'sha 00:00 ning naive UTC vaqti).
    Soat wordbank._now orqali — testlar uni suradi."""
    local_today = roles.to_local(WB._now()).date()
    ws_local = local_today - timedelta(days=local_today.weekday())
    ws_utc = (datetime.combine(ws_local, time())
              - timedelta(hours=roles.TIMEZONE_OFFSET_HOURS))
    return ws_local, ws_utc


def _enabled(q, col, db: Session):
    """Faqat bo'lim yoqilgan filiallar ("all" — filtr yo'q)."""
    v = WB.flag_value(db)
    if v == WB.ALL:
        return q
    return q.filter(col.in_(sorted(v) or [-1]))


def _has_progress():
    return S.id.in_(select(SW.student_id).where(SW.known == 1))


# ------------------------------------------------------ umumiy hisob ---
def _known_rows(db: Session, ws_utc, sids=None):
    """{sid: (tasdiqlangan, oxirgi known_at, shu hafta, haftadagi oxirgi)}."""
    in_week = SW.known_at >= ws_utc
    q = (db.query(SW.student_id, func.count(SW.id), func.max(SW.known_at),
                  func.sum(case((in_week, 1), else_=0)),
                  func.max(case((in_week, SW.known_at), else_=None)))
         .join(W, W.id == SW.word_id)
         .filter(SW.known == 1, W.status == "active"))
    out = {}
    parts = [None] if sids is None else list(_chunks(sids))
    for part in parts:
        qq = q if part is None else q.filter(SW.student_id.in_(part))
        for sid, n, last, wk, wlast in qq.group_by(SW.student_id):
            out[int(sid)] = (int(n or 0), _dt(last), int(wk or 0),
                             _dt(wlast))
    return out


def _band_counts(db: Session, sids=None) -> dict:
    q = db.query(BA.student_id, func.count(BA.id))
    out = {}
    parts = [None] if sids is None else list(_chunks(sids))
    for part in parts:
        qq = q if part is None else q.filter(BA.student_id.in_(part))
        for sid, n in qq.group_by(BA.student_id):
            out[int(sid)] = int(n or 0)
    return out


def _p_answers(db: Session, ws_utc, sids=None) -> dict:
    """{sid: (shu haftadagi P javoblar, shubhalilari)} — "Bilmayman"
    (given bo'sh) sanalmaydi."""
    q = (db.query(SI.student_id, func.count(SI.id),
                  func.sum(SI.suspect))
         .filter(SI.mode == "P", SI.given.isnot(None),
                 SI.answered_at >= ws_utc))
    out = {}
    parts = [None] if sids is None else list(_chunks(sids))
    for part in parts:
        qq = q if part is None else q.filter(SI.student_id.in_(part))
        for sid, n, sus in qq.group_by(SI.student_id):
            out[int(sid)] = (int(n or 0), int(sus or 0))
    return out


class _Stats:
    """O'quvchilar bo'yicha hisob. Butun markaz — keshdan; own_sid — har
    so'rovda jonli (o'z yangi so'zi darhol ko'rinsin). "tekshirilmoqda"
    uchun P javoblar faqat load_flags bilan so'ralgan o'quvchilarga
    (2026-10-17, review: butun markaz bo'yicha emas)."""

    def __init__(self, known, bands, pans=None, own=None):
        self._known = known
        self._bands = bands
        self._pans = dict(pans or {})
        self._own = own or {}

    def known(self, sid):
        if sid in self._own:
            return self._own[sid]
        return self._known.get(sid, (0, None, 0, None))

    def bands(self, sid) -> int:
        return self._bands.get(sid, 0)

    def load_flags(self, db: Session, ws_utc, sids) -> None:
        """Shu o'quvchilarning shu haftadagi P javoblari (faqat
        ko'rinadigan qatorlar — TOP_N + o'zi)."""
        need = [int(s) for s in sids if s is not None
                and int(s) not in self._pans]
        if not need:
            return
        got = _p_answers(db, ws_utc, need)
        for sid in need:
            self._pans[sid] = got.get(sid, (0, 0))

    def flagged(self, sid) -> bool:
        """Faqat ko'rsatish: shu hafta > FLAG_WEEK_GAIN so'z yoki P
        javoblarning > 30% i shubhali (kamida FLAG_MIN_P ta)."""
        if self.known(sid)[2] > FLAG_WEEK_GAIN:
            return True
        n, sus = self._pans.get(sid, (0, 0))
        return n >= FLAG_MIN_P and sus / float(n) > FLAG_SUSPECT_SHARE


def _cached(db: Session, part: str, ws_utc, fn):
    """Butun markaz bo'yicha hisobning bir QISMI ("known" | "bands") —
    AGG_TTL soniya jarayon keshida (kalit: baza + qism + hafta boshi).
    2026-10-17 (review): qismlar alohida — ranks_for (/me, ota-ona)
    faqat "known" ni oladi, darajalar hisobi unga kerak emas."""
    try:
        url = str(db.get_bind().url)
    except Exception:
        url = "?"
    key = (url, part, ws_utc.isoformat())
    now_m = _time.monotonic()
    with _CACHE_LOCK:
        hit = _CACHE.get(key)
    if hit is not None and AGG_TTL > 0 and now_m - hit[0] < AGG_TTL:
        return hit[1]
    val = fn()
    with _CACHE_LOCK:
        # eski hafta / muddati o'tgan qiymatlar ketsin
        for k in [k for k, v in _CACHE.items()
                  if AGG_TTL <= 0 or now_m - v[0] >= AGG_TTL]:
            _CACHE.pop(k, None)
        if AGG_TTL > 0:
            _CACHE[key] = (now_m, val)
    return val


def _known_agg(db: Session, ws_utc) -> dict:
    return _cached(db, "known", ws_utc, lambda: _known_rows(db, ws_utc))


def _stats(db: Session, ws_utc, own_sid=None) -> _Stats:
    """Reyting uchun hisob: tasdiqlangan so'zlar va darajalar — keshdan;
    "tekshirilmoqda" — keyin load_flags bilan, faqat ko'rinadiganlarga."""
    known = _known_agg(db, ws_utc)
    bands = _cached(db, "bands", ws_utc, lambda: _band_counts(db))
    own = None
    if own_sid is not None:
        own = {int(own_sid): _known_rows(db, ws_utc, [own_sid]).get(
            int(own_sid), (0, None, 0, None))}
    return _Stats(known, bands, None, own)


def _live_known(db: Session, sid: int):
    """(tasdiqlangan son, oxirgi known_at) — /me bilan bir xil sanoq."""
    r = (db.query(func.count(SW.id), func.max(SW.known_at))
         .join(W, W.id == SW.word_id)
         .filter(SW.student_id == int(sid), SW.known == 1,
                 W.status == "active").first())
    return (int(r[0] or 0), _dt(r[1])) if r else (0, None)


def _primary_gid(db: Session, sid: int, group_id=None):
    """Asosiy guruh: Student.group_id, bo'lmasa birinchi faol bog'lanish."""
    if group_id:
        return int(group_id)
    r = (db.query(SGL.group_id)
         .filter(SGL.student_id == int(sid), SGL.active == 1)
         .order_by(SGL.is_primary.desc(), SGL.id).first())
    return int(r[0]) if r else None


def _last_gid(db: Session, sid: int):
    """Faol guruhi yo'q o'quvchi (ketgan / arxiv) — oxirgi guruhi:
    eng oxirgi yopilgan bog'lanish (left_date, keyin id), bo'lmasa
    oxirgi LeaveReason.group_id.

    2026-10-17 (review): arxivlash yo'llari (common.detach_group, avtomat
    arxiv) bog'lanishni yopib, Student.group_id ni bo'shatadi. Tarix
    qatori birinchi marta o'chirish oldidan (before_purge) yozilsa,
    guruh bo'sh qolib, o'quvchi guruhning "Tarix" idan tushib qolardi."""
    links = (db.query(SGL.group_id, SGL.left_date, SGL.id)
             .filter(SGL.student_id == int(sid)).all())
    if links:
        return int(max(links, key=lambda r: (r[1] or date.min, r[2]))[0])
    LR = models.LeaveReason
    r = (db.query(LR.group_id)
         .filter(LR.student_id == int(sid), LR.group_id.isnot(None))
         .order_by(LR.created_at.desc(), LR.id.desc()).first())
    return int(r[0]) if r else None


def _student_gids(db: Session, s) -> list:
    """O'quvchining guruhlari — asosiysi birinchi (tanlagich uchun)."""
    out = []
    first = _primary_gid(db, s.id, s.group_id)
    if first:
        out.append(first)
    for g in sorted(student_group_ids(db, s.id)):
        if g and g not in out:
            out.append(int(g))
    return out


def _group_names(db: Session, gids) -> dict:
    out = {}
    for part in _chunks(gids):
        for gid, name in (db.query(models.Group.id, models.Group.name)
                          .filter(models.Group.id.in_(part))):
            out[int(gid)] = name
    return out


def _branch_names(db: Session) -> dict:
    return {int(b): n for b, n in db.query(models.Branch.id,
                                           models.Branch.name)}


def _leave_labels(db: Session, sids) -> dict:
    """{sid: "bitirgan" | "ketgan"} — oxirgi LeaveReason (created_at,
    keyin id bo'yicha) "finished" bo'lsa bitirgan."""
    LR = models.LeaveReason
    latest = {}
    for part in _chunks(sids):
        for sid, reason in (db.query(LR.student_id, LR.reason)
                            .filter(LR.student_id.in_(part))
                            .order_by(LR.student_id, LR.created_at.desc(),
                                      LR.id.desc())):
            latest.setdefault(int(sid), reason)
    return {sid: ("bitirgan" if latest.get(sid) == "finished" else "ketgan")
            for sid in sids}


def _badges(db: Session, sids) -> dict:
    import wordbank_certs as WCERT             # faqat tasdiqlanganlar
    if not sids:
        return {}
    return WCERT.latest_badges(db, list(sids))


# -------------------------------------------------------- tarix (D4) ---
def _status_snap(db: Session, sid: int, status) -> str:
    if (status or "") in LIVE:
        return status
    if _leave_labels(db, [sid]).get(sid) == "bitirgan":
        return "finished"
    return status or ""


def refresh_hall(db: Session, student_id: int, hidden=None):
    """wordbank_hall qatorini yangilaydi (upsert, student_ref bo'yicha).

    best_known = max(eski, jonli tasdiqlangan son) — HECH QACHON
    pasaymaydi (best_at = o'sha paytdagi oxirgi known_at); bands_mask =
    eski | to'langan darajalar; bands_done = bitlar soni; cert_badge =
    wordbank_certs.cert_badge_for (joriy oxirgi tasdiqlangan, bekor
    qilinsa o'zgaradi); name/branch/group/status snapshot jonli
    o'quvchidan (o'quvchi yo'q bo'lsa — eski qiymatlar qoladi; guruh /
    filial bo'shab qolsa ham oxirgisi saqlanadi); hidden berilsa
    yoziladi. Commit QILMAYDI (chaqiruvchi qiladi). Qaytaradi:
    models.WordbankHall yoki None (yangi qatorga yozadigan narsa yo'q).

    Chaqiruvchilar: daraja coini (wordbank._award_bands), /me (o'sish
    >= HALL_STEP yoki 1000 chegarasi), sertifikat tasdiq/bekor
    (wordbank_certs), before_purge, on_merge."""
    import wordbank_certs as WCERT
    sid = int(student_id)
    # SessionLocal autoflush=False: chaqiruvchining hali yozilmagan
    # o'zgarishi (yangi tasdiq, daraja qatori) quyidagi so'rovlarga
    # ko'rinsin — aks holda cert_badge / bands_mask eski qiymatda qolardi.
    db.flush()
    st = (db.query(S.id, S.full_name, S.status, S.branch_id, S.group_id)
          .filter(S.id == sid).first())
    known, last = _live_known(db, sid)
    mask = 0
    for (b,) in db.query(BA.band).filter(BA.student_id == sid):
        if b and 1 <= int(b) <= 31:
            mask |= 1 << (int(b) - 1)
    badge = WCERT.cert_badge_for(db, sid)
    now = WB._now()
    row = db.query(HALL).filter(HALL.student_ref == sid).first()
    if row is None:
        if st is None or (known <= 0 and not mask and not badge):
            return None
        row = HALL(student_ref=sid, best_known=0, bands_mask=0,
                   bands_done=0, hidden=0, created_at=now, updated_at=now)
        try:
            with db.begin_nested():
                db.add(row)
                db.flush()
        except IntegrityError:
            # Parallel so'rov hozirgina yaratdi — o'shani yangilaymiz
            row = db.query(HALL).filter(HALL.student_ref == sid).first()
            if row is None:
                return None
    if known > int(row.best_known or 0):
        row.best_known = known
        row.best_at = last or now
    row.bands_mask = int(row.bands_mask or 0) | mask
    row.bands_done = _popcount(row.bands_mask)
    row.cert_badge = badge
    if st is not None:
        row.name_snap = st.full_name
        if st.branch_id is not None:
            row.branch_id = st.branch_id
            br = db.query(models.Branch.name).filter(
                models.Branch.id == st.branch_id).first()
            row.branch_name = br[0] if br else row.branch_name
        gid = _primary_gid(db, sid, st.group_id) or _last_gid(db, sid)
        if gid:
            row.group_id = gid
            row.group_name = _group_names(db, [gid]).get(gid, row.group_name)
        row.status_snap = _status_snap(db, sid, st.status)
    if hidden is not None:
        row.hidden = 1 if hidden else 0
    row.updated_at = now
    db.flush()
    return row


def before_purge(db: Session, student_id: int, hidden: int = 0) -> None:
    """Asoschi o'quvchini BUTUNLAY o'chirishidan oldin (students.
    delete_student — hidden=0; import-undo "delete" — hidden=1, chunki
    bular xato kiritilgan yozuvlar) natija snapshotini tarixga yozadi.
    _purge_student_children DAN OLDIN chaqiriladi. Hech qachon xato
    tashlamaydi (ichida savepoint) — o'chirish to'xtab qolmasin."""
    try:
        with db.begin_nested():
            refresh_hall(db, student_id, hidden=hidden)
    except Exception as e:                      # noqa: BLE001
        print(f"[wordbank-hall] before_purge {student_id}: {e!r}")
    clear_cache()


def _strength(r):
    return (int(r.known or 0), int(r.stage or 0), r.last_move or date.min)


def on_merge(db: Session, keep_id: int, drop_id: int) -> dict:
    """students.merge_students umumiy ko'chirishidan (3-qadam) OLDIN:
    so'z holatlarini so'z bo'yicha birlashtiradi (kuchlisi qoladi:
    known, keyin stage, keyin kechroq last_move; lapses qo'shiladi),
    sessiya / savol / hajm testlarini ko'chiradi, daraja coinlarini
    takrorsiz ko'chiradi (ikkala hisobda to'langan bo'lsa -N tuzatish
    CoinEntry, source="vocab_band", izohda [merge]), sertifikat
    yuklamalarini va tarix qatorini (maksimumlar) ko'chiradi.
    Qaytaradi: {"Jadval nomi": son} — merge javobidagi "moved" ga
    qo'shiladi.

    Nega alohida: wordbank_band_awards, wordbank_cert_uploads va
    wordbank_hall da FK yo'q (D4) — umumiy qoida ularni ko'rmaydi;
    wordbank_student_words esa UNIQUE(student_id, word_id) ga urilib,
    umumiy qadamda takror qator shunchaki o'chirilardi (kuchlisi emas)."""
    keep_id, drop_id = int(keep_id), int(drop_id)
    out: dict = {}
    db.flush()                       # autoflush=False — oldingi qadamlar yozilsin

    def put(label, n):
        if n:
            out[label] = out.get(label, 0) + int(n)

    # 1) So'z holatlari — so'z bo'yicha
    keep_rows = {r.word_id: r for r in
                 db.query(SW).filter(SW.student_id == keep_id)}
    moved = merged = 0
    for r in db.query(SW).filter(SW.student_id == drop_id).all():
        k = keep_rows.get(r.word_id)
        if k is None:
            r.student_id = keep_id
            moved += 1
            continue
        if _strength(r) > _strength(k):
            for f in ("stage", "due", "has_prod", "known", "last_move",
                      "known_at"):
                setattr(k, f, getattr(r, f))
        k.lapses = int(k.lapses or 0) + int(r.lapses or 0)
        db.delete(r)
        merged += 1
    db.flush()
    put("So'z holati", moved)
    put("So'z holati (birlashdi)", merged)

    # 2) Sessiyalar, savollar, hajm testlari — oddiy ko'chirish
    for M, label in ((models.WordbankSession, "So'z mashqi sessiyalari"),
                     (SI, None),
                     (ST, "Lug'at hajmi testi")):
        n = (db.query(M).filter(M.student_id == drop_id)
             .update({M.student_id: keep_id}, synchronize_session=False))
        if label:
            put(label, n)

    # 3) Daraja coinlari — har daraja bitta qator (erta yozilgani qoladi)
    keep_aw = {int(a.band): a for a in
               db.query(BA).filter(BA.student_id == keep_id)}
    n_move = n_dup = 0
    for a in (db.query(BA).filter(BA.student_id == drop_id)
              .order_by(BA.id).all()):
        band = int(a.band)
        k = keep_aw.get(band)
        if k is None:
            a.student_id = keep_id
            keep_aw[band] = a
            n_move += 1
            continue
        if (a.awarded_at or datetime.max) < (k.awarded_at or datetime.max):
            db.delete(k)
            db.flush()                  # UNIQUE(student_id, band) bo'shasin
            a.student_id = keep_id
            keep_aw[band] = a
        else:
            db.delete(a)
        n_dup += 1
    db.flush()
    put("So'z bilish darajasi", n_move)
    put("So'z bilish darajasi (takror)", n_dup)

    fixes = 0
    if keep_aw:
        net = {int(b): int(v or 0) for b, v in
               db.query(CE.ref_id, func.sum(CE.amount))
               .filter(CE.source == WB.COIN_SOURCE,
                       CE.student_id.in_((keep_id, drop_id)),
                       CE.ref_id.in_(sorted(keep_aw)))
               .group_by(CE.ref_id)}
        who = db.query(S.full_name, S.branch_id).filter(
            S.id == keep_id).first()
        for band, a in sorted(keep_aw.items()):
            coins = int(a.coins if a.coins is not None
                        else WCORE.coins_for_band(band))
            extra = net.get(band, 0) - coins
            if extra <= 0:
                continue
            db.add(CE(student_id=keep_id, amount=-extra,
                      source=WB.COIN_SOURCE, ref_id=band,
                      note=(f"[merge] So'z bilish: Common {band}000 ikki "
                            f"hisobda to'langan — takror qaytarildi"),
                      created_by="Tizim"))
            # AUDIT — coin pulga aylanadi (wordbank._pay_band uslubi)
            audit.log(db, None, entity="student", action=WB.COIN_SOURCE,
                      entity_id=keep_id,
                      entity_label=who[0] if who else None,
                      field=WB.COIN_SOURCE,
                      old_value=f"Common {band}000: {net.get(band, 0)} coin",
                      new_value=f"-{extra} coin (takror to'lov qaytarildi)",
                      note=f"[merge] #{drop_id} -> #{keep_id}",
                      branch_id=who[1] if who else None)
            fixes += 1
        db.flush()
    put("Daraja coini (takror)", fixes)

    # 4) Sertifikat yuklamalari
    CU = models.WordbankCertUpload
    put("Sertifikat yuklamasi",
        db.query(CU).filter(CU.student_id == drop_id)
        .update({CU.student_id: keep_id}, synchronize_session=False))

    # 5) Tarix qatori — maksimumlar
    hk = db.query(HALL).filter(HALL.student_ref == keep_id).first()
    hd = db.query(HALL).filter(HALL.student_ref == drop_id).first()
    if hd is not None:
        if hk is None:
            hd.student_ref = keep_id
        else:
            if int(hd.best_known or 0) > int(hk.best_known or 0):
                hk.best_known = hd.best_known
                hk.best_at = hd.best_at
            hk.bands_mask = int(hk.bands_mask or 0) | int(hd.bands_mask or 0)
            hk.bands_done = _popcount(hk.bands_mask)
            hk.hidden = min(int(hk.hidden or 0), int(hd.hidden or 0))
            db.delete(hd)
        db.flush()
        put("So'z bilish tarixi", 1)
    refresh_hall(db, keep_id)
    clear_cache()
    return out


# ------------------------------------------------------ reyting (D2) ---
class _E:
    """Reyting nomzodi. key — saralash: ko'p birinchi, keyin erta
    erishgan, keyin kichik id."""
    __slots__ = ("sid", "deleted", "metric", "tie", "known", "week",
                 "bands", "name", "branch_id", "group_id", "group_name",
                 "branch_name", "status", "label", "badge", "rank")

    def __init__(self, sid, metric, tie, **kw):
        self.sid = sid
        self.metric = int(metric or 0)
        self.tie = tie
        self.deleted = False
        self.known = self.week = self.bands = 0
        self.name = self.group_name = self.branch_name = None
        self.branch_id = self.group_id = None
        self.status = self.label = self.badge = None
        self.rank = None
        for k, v in kw.items():
            setattr(self, k, v)

    def key(self):
        return (-self.metric, self.tie or datetime.max, self.sid)


def _rank(entries) -> list:
    out = sorted((e for e in entries if e.metric > 0), key=_E.key)
    for i, e in enumerate(out, 1):
        e.rank = i
    return out


def _live_entries(db: Session, s, scope, gid, period, stats) -> list:
    q = (db.query(S.id, S.full_name, S.branch_id, S.group_id, S.status)
         .filter(S.status.in_(LIVE), _has_progress()))
    q = _enabled(q, S.branch_id, db)
    if scope == "group":
        q = q.filter(in_group(gid))
    elif scope == "branch":
        q = q.filter(S.branch_id == s.branch_id)
    out = []
    for sid, name, bid, pgid, status in q:
        n, last, wk, wlast = stats.known(sid)
        out.append(_E(sid, n if period == "total" else wk,
                      last if period == "total" else wlast,
                      known=n, week=wk, bands=stats.bands(sid), name=name,
                      branch_id=bid, group_id=pgid, status=status))
    return out


def _history_entries(db: Session, s, scope, gid, stats) -> list:
    """Tarix: BARCHA holatdagi o'quvchilar (eng yaxshi = max(hall, jonli))
    + o'chirilgan o'quvchilarning yashirilmagan tarix qatorlari."""
    q = (db.query(S.id, S.full_name, S.status, S.branch_id, S.group_id,
                  HALL.best_known, HALL.best_at, HALL.bands_done,
                  HALL.group_name)
         .outerjoin(HALL, HALL.student_ref == S.id)
         .filter(or_(_has_progress(), HALL.id.isnot(None),
                     S.id.in_(select(BA.student_id)))))
    q = _enabled(q, S.branch_id, db)
    hq = (db.query(HALL.student_ref, HALL.name_snap, HALL.branch_id,
                   HALL.branch_name, HALL.group_id, HALL.group_name,
                   HALL.best_known, HALL.best_at, HALL.bands_done,
                   HALL.cert_badge, HALL.status_snap)
          .outerjoin(S, S.id == HALL.student_ref)
          .filter(S.id.is_(None), HALL.hidden == 0))
    hq = _enabled(hq, HALL.branch_id, db)
    if scope == "group":
        q = q.filter(or_(S.group_id == gid,
                         S.id.in_(select(SGL.student_id)
                                  .where(SGL.group_id == gid)),
                         HALL.group_id == gid))
        hq = hq.filter(HALL.group_id == gid)
    elif scope == "branch":
        q = q.filter(S.branch_id == s.branch_id)
        hq = hq.filter(HALL.branch_id == s.branch_id)
    out = []
    for (sid, name, status, bid, pgid, hb, hb_at, hbands, hgname) in q:
        n, last = stats.known(sid)[:2]
        hb = int(hb or 0)
        best, tie = (n, last) if n > hb else (hb, hb_at or last)
        out.append(_E(sid, best, tie, known=best,
                      bands=max(stats.bands(sid), int(hbands or 0)),
                      name=name, branch_id=bid, group_id=pgid,
                      group_name=hgname, status=status))
    for (ref, name, bid, bname, hgid, hgname, hb, hb_at, hbands, badge,
         snap) in hq:
        e = _E(int(ref), hb, hb_at, known=int(hb or 0),
               bands=max(stats.bands(int(ref)), int(hbands or 0)),
               name=name, branch_id=bid, branch_name=bname, group_id=hgid,
               group_name=hgname, status=snap, badge=badge,
               label="bitirgan" if snap == "finished" else "ketgan")
        e.deleted = True
        out.append(e)
    return out


def _first_finishers(db: Session, entries, me_id) -> list:
    """Har daraja bo'yicha eng birinchi tugatgan (wordbank_band_awards.
    awarded_at) — qamrovdagi tarix nomzodlari orasidan."""
    by_id = {e.sid: e for e in entries}
    first: dict = {}
    for sid, band, at in (db.query(BA.student_id, BA.band, BA.awarded_at)
                          .order_by(BA.band, BA.awarded_at, BA.id)):
        band = int(band)
        if band in first or int(sid) not in by_id:
            continue
        first[band] = (int(sid), at)
    out = []
    for band in sorted(first):
        sid, at = first[band]
        e = by_id[sid]
        mine = (not e.deleted) and sid == me_id
        out.append({
            "band": band, "label": f"Common {band}000",
            "name": "Siz" if mine else _mask(e.name),
            "initials": _initials(e.name),
            "at": roles.to_local(at).date().isoformat() if at else None,
            "is_me": mine,
        })
    return out


def _rows_out(db: Session, shown, me_id, period, stats) -> list:
    """Ko'rinadigan qatorlar (TOP_N + o'z qatori) — barcha qo'shimcha
    ma'lumot shu kichik to'plam uchun bitta-bitta so'rov bilan."""
    live_ids = [e.sid for e in shown if not e.deleted]
    badges = _badges(db, live_ids)
    labels = {}
    if period == "history":
        gone = [e.sid for e in shown
                if not e.deleted and (e.status or "") not in LIVE]
        labels = _leave_labels(db, gone) if gone else {}
    gnames = _group_names(db, [e.group_id for e in shown
                               if e.group_id and not e.deleted])
    bnames = _branch_names(db)
    out = []
    for e in shown:
        mine = (not e.deleted) and e.sid == me_id
        if e.deleted:
            label, badge = e.label, e.badge
        else:
            label = labels.get(e.sid) if period == "history" else None
            badge = badges.get(e.sid)
        gname = e.group_name if e.deleted else \
            (gnames.get(e.group_id) or e.group_name)
        out.append({
            "rank": e.rank,
            "name": "Siz" if mine else _mask(e.name),
            "initials": _initials(e.name),
            "group": gname,
            "branch": e.branch_name if e.deleted else
            bnames.get(e.branch_id),
            "known": int(e.known or 0),
            "week_gain": 0 if period == "history" else int(e.week or 0),
            "bands_done": int(e.bands or 0),
            "cert_badge": badge,
            "label": label,
            "flagged": (False if period == "history" or e.deleted
                        else stats.flagged(e.sid)),
            "is_me": mine,
        })
    return out


def _me_entry(s, period, stats) -> "_E":
    n, last, wk, wlast = stats.known(s.id)
    metric = wk if period == "week" else n
    return _E(s.id, metric, wlast if period == "week" else last, known=n,
              week=wk, bands=stats.bands(s.id), name=s.full_name,
              branch_id=s.branch_id, group_id=s.group_id, status=s.status)


@router.get("/api/wordbank/leaderboard")
def wordbank_leaderboard(scope: str = "group", period: str = "total",
                         group_id: str = None,
                         db: Session = Depends(get_db),
                         user=Depends(get_current_user)):
    """"So'z bilish" reytingi (D2): tasdiqlangan so'zlar soni bo'yicha.

    scope:  group (Guruhim) | branch (Filialim) | school (Umumiy);
    period: total (Jami) | week (Shu hafta, dushanbadan) |
            history (Tarix — ketgan / bitirgan / o'chirilganlar ham).
    group_id — o'quvchining guruhlaridan biri (2+ guruh tanlagichi).
    Ro'yxat TOP_N ta; o'z qatori (me) HAR DOIM alohida. Ismlar
    yashiriladi ("Aziz K."), rasm yo'q — faqat bosh harflar.
    Reyting coin / XP bermaydi; sertifikat o'ringa ta'sir qilmaydi."""
    s = WB._student(db, user)                   # bayroq/filial — 404
    if scope not in SCOPES:
        raise HTTPException(400, "scope: group, branch yoki school")
    if period not in PERIODS:
        raise HTTPException(400, "period: total, week yoki history")
    my_gids = _student_gids(db, s)
    gid = None
    if group_id not in (None, ""):
        try:
            gid = int(group_id)
        except (TypeError, ValueError):
            raise HTTPException(400, "group_id noto'g'ri")
        if gid not in my_gids:
            raise HTTPException(403, "Bu guruh sizniki emas")
    if gid is None and my_gids:
        gid = my_gids[0]
    ws_local, ws_utc = week_bounds()
    names = _group_names(db, my_gids)
    base = {
        "scope": scope, "period": period,
        "group_id": gid if scope == "group" else None,
        "rows": [], "me": None, "gap_to_next": None, "total": 0,
        "groups": [{"id": g, "name": names.get(g) or f"Guruh #{g}"}
                   for g in my_gids],
        "first_finishers": [], "week_start": ws_local.isoformat(),
        "hint": None,
    }
    stats = _stats(db, ws_utc, own_sid=s.id)
    hint = None
    if scope == "group" and gid is None:
        hint = "Siz hali guruhga biriktirilmagansiz."
    elif scope == "branch" and s.branch_id is None:
        hint = "Filial biriktirilmagan."
    if hint:
        me = _me_entry(s, period, stats)
        if period != "history":
            stats.load_flags(db, ws_utc, [s.id])
        base["me"] = _rows_out(db, [me], s.id, period, stats)[0]
        base["hint"] = hint
        return base

    if period == "history":
        entries = _history_entries(db, s, scope, gid, stats)
    else:
        entries = _live_entries(db, s, scope, gid, period, stats)
    ranked = _rank(entries)
    me = next((e for e in entries if not e.deleted and e.sid == s.id), None)
    if me is None:
        me = _me_entry(s, period, stats)
        if period == "history":
            me.metric = me.known
    shown = ranked[:TOP_N]
    if me not in shown:
        shown = shown + [me]
    if period != "history":
        # "tekshirilmoqda" — faqat ko'rinadigan qatorlar uchun (2026-10-17)
        stats.load_flags(db, ws_utc, [e.sid for e in shown if not e.deleted])
    rows = _rows_out(db, shown, s.id, period, stats)
    base["rows"] = rows[:min(TOP_N, len(ranked))]
    base["me"] = rows[-1] if me.rank is None or me.rank > TOP_N else \
        rows[me.rank - 1]
    if me.rank == 1:
        gap = None
    elif me.rank:
        gap = ranked[me.rank - 2].metric - me.metric + 1
    else:
        gap = 1
    base["gap_to_next"] = gap
    base["total"] = len(ranked)
    if period == "history":
        base["first_finishers"] = _first_finishers(db, entries, s.id)
    return base


def ranks_for(db: Session, student, known=None) -> dict:
    """O'quvchining "Jami" reytingidagi o'rni: {"group", "branch",
    "school"} — har biri int yoki None (reytingda yo'q / 0 so'z).
    Guruh — asosiy guruh (Student.group_id, bo'lmasa birinchi faol
    bog'lanish). /api/wordbank/me va ota-ona sahifasi ishlatadi.

    Bitta so'rov: faol/sinovdagi, yoqilgan filial o'quvchilari (id,
    filial, "shu guruhda" belgisi) — o'rin Python'da sanaladi.

    2026-10-17 (review, tezlik): known — chaqiruvchi allaqachon sanagan
    tasdiqlangan son (ixtiyoriy); 0 bo'lsa umumiy hisob umuman
    qilinmaydi. Umumiy hisobdan faqat "known" qismi olinadi (keshdan),
    darajalar va "tekshirilmoqda" hisoblanmaydi."""
    out = {"group": None, "branch": None, "school": None}
    if student is None or (student.status or "") not in LIVE:
        return out
    if known is not None and int(known or 0) <= 0:
        return out
    n, last = _live_known(db, student.id)
    if n <= 0:
        return out
    _ws_local, ws_utc = week_bounds()
    agg = _known_agg(db, ws_utc)
    gid = _primary_gid(db, student.id, student.group_id)
    flag = case((in_group(gid), 1), else_=0) if gid else None
    cols = [S.id, S.branch_id] + ([flag] if flag is not None else [])
    # So'zi borlar keshdagi hisobdan aniqlanadi (pastda k <= 0 o'tkaziladi)
    q = db.query(*cols).filter(S.status.in_(LIVE))
    q = _enabled(q, S.branch_id, db)
    mine = (-n, last or datetime.max, student.id)
    school = branch = group = 0
    seen_self = self_in_group = False
    for row in q:
        sid, bid = int(row[0]), row[1]
        if sid == student.id:
            seen_self = True
            self_in_group = flag is not None and bool(row[2])
            continue
        k, kl = agg.get(sid, (0, None))[:2]
        if k <= 0 or (-k, kl or datetime.max, sid) >= mine:
            continue
        school += 1
        if student.branch_id is not None and bid == student.branch_id:
            branch += 1
        if flag is not None and row[2]:
            group += 1
    if not seen_self:
        return out
    out["school"] = school + 1
    if student.branch_id is not None:
        out["branch"] = branch + 1
    if self_in_group:
        out["group"] = group + 1
    return out


# ----------------------------------------------------- /me qo'shimcha ---
def me_extras(db: Session, s, known: int) -> dict:
    """/api/wordbank/me ga: ranks, best_known, certs (FAQAT tasdiqlangan),
    certs_pending (SON, natijasiz). Arzon tarix yangilanishi: qator yo'q
    va so'z bor, yoki HALL_STEP ga o'sdi, yoki 1000 chegarasidan o'tdi."""
    import wordbank_certs as WCERT
    known = int(known or 0)
    row = (db.query(HALL.best_known)
           .filter(HALL.student_ref == s.id).first())
    best = int(row[0] or 0) if row else 0
    if (row is None and known > 0) or known >= best + HALL_STEP \
            or known // 1000 > best // 1000:
        try:
            if refresh_hall(db, s.id) is not None:
                db.commit()
        except Exception as e:                  # noqa: BLE001
            db.rollback()
            print(f"[wordbank-hall] /me {s.id}: {e!r}")
    try:
        # Savepoint (2026-10-17, review): Postgres'da yiqilgan so'rov
        # butun tranzaksiyani to'xtatadi — keyingi so'rovlar ham
        # yiqilmasin, faqat shu qism bekor bo'lsin.
        with db.begin_nested():
            ranks = ranks_for(db, s, known=known)
    except Exception as e:                      # noqa: BLE001
        print(f"[wordbank-rank] /me {s.id}: {e!r}")
        ranks = {"group": None, "branch": None, "school": None}
    return {
        "ranks": ranks,
        "best_known": max(best, known),
        "certs": WCERT.confirmed_badges(db, [s.id]).get(int(s.id), []),
        "certs_pending": int(WCERT.pending_count(db, s.id)),
    }


# ----------------------------------------------------------- ota-ona ---
def parent_payload(db: Session, s):
    """Ota-ona sahifasi (entry.py: parent_view) uchun "wordbank" bo'limi
    yoki None (filialda bo'lim yoqilmagan). FAQAT shu bitta o'quvchi;
    sertifikatlar — faqat tasdiqlangan; boshqa bolalarning ma'lumoti
    yo'q (faqat o'rin raqami)."""
    import wordbank_certs as WCERT
    if s is None or not WB.branch_enabled(db, s.branch_id):
        return None
    known, _last = _live_known(db, s.id)
    row = (db.query(HALL.best_known, HALL.bands_done)
           .filter(HALL.student_ref == s.id).first())
    bands = db.query(func.count(BA.id)).filter(
        BA.student_id == s.id).scalar() or 0
    ranks = ranks_for(db, s, known=known)
    return {
        "known": known,
        "best": max(known, int(row[0] or 0) if row else 0),
        "bands_done": max(int(bands), int(row[1] or 0) if row else 0),
        "rank_group": ranks.get("group"),
        "rank_branch": ranks.get("branch"),
        "certs": WCERT.confirmed_badges(db, [s.id]).get(int(s.id), []),
    }


# ------------------------------------------------------------ ustoz ---
@router.get("/api/wordbank/teacher/students")
def teacher_word_students(group_id: str = None,
                          db: Session = Depends(get_db),
                          user=Depends(require_role(roles.TEACHER,
                                                    *roles.ACADEMIC_ACCESS))):
    """Ustoz (faqat O'Z guruhi) va o'quv bo'limi: guruh o'quvchilarining
    so'z bilishi — tasdiqlangan, eng yaxshi, shu hafta, darajalar,
    oxirgi hajm testi (TAXMINIY) va FAQAT tasdiqlangan sertifikatlar.
    Xodimga to'liq ism ko'rinadi. Bayroq butunlay o'chiq — 404."""
    import wordbank_certs as WCERT
    if not WB.flag_value(db):
        raise HTTPException(404, WB._NOT_FOUND)
    try:
        gid = int(group_id)
    except (TypeError, ValueError):
        raise HTTPException(400, "group_id kerak")
    g = _get_group_in_scope(db, gid, user)
    ws_local, ws_utc = week_bounds()
    enabled = WB.branch_enabled(db, g.branch_id)
    out = {"group": {"id": g.id, "name": g.name}, "enabled": enabled,
           "week_start": ws_local.isoformat(), "students": []}
    if not enabled:
        return out
    rows = (db.query(S.id, S.full_name)
            .filter(in_group(g.id), S.status.in_(LIVE)).all())
    sids = [int(r[0]) for r in rows]
    if not sids:
        return out
    stats = _Stats(_known_rows(db, ws_utc, sids), _band_counts(db, sids),
                   _p_answers(db, ws_utc, sids))
    best = {}
    tests = {}
    for part in _chunks(sids):
        for ref, b in (db.query(HALL.student_ref, HALL.best_known)
                       .filter(HALL.student_ref.in_(part))):
            best[int(ref)] = int(b or 0)
        for t in (db.query(ST.student_id, ST.estimate, ST.low, ST.high,
                           ST.created_at)
                  .filter(ST.student_id.in_(part))
                  .order_by(ST.created_at.desc(), ST.id.desc())):
            tests.setdefault(int(t[0]), t)
    certs = WCERT.confirmed_badges(db, sids)
    students = []
    for sid, name in rows:
        n, _l, wk, _wl = stats.known(sid)
        t = tests.get(sid)
        students.append({
            "id": sid, "name": name, "known": n,
            "best": max(n, best.get(sid, 0)), "week_gain": wk,
            "bands_done": stats.bands(sid),
            "size_test": ({"estimate": t[1], "low": t[2], "high": t[3],
                           "date": (roles.to_local(t[4]).date().isoformat()
                                    if t[4] else None)}
                          if t is not None else None),
            "certs": certs.get(sid, []),
            "flagged": stats.flagged(sid),
        })
    students.sort(key=lambda r: (-r["known"], r["name"] or "", r["id"]))
    out["students"] = students
    return out
