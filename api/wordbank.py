"""LUG'AT BANKI — "So'z bilish" API (2026-10-16, 2-qadam).

Sabab (Jahongir, OWNER_DECISIONS D1–D5): o'quvchi nechta inglizcha
so'zni HAQIQATAN bilishi turli kunlarda tekshirilib, tasdiqlangan holda
sanalsin; Common N000 darajasi to'liq tugasa N coin (bir marta).

YASHIRIN ISHGA TUSHIRISH: IntegrationSetting["wordbank_branches"]
ro'yxatidagi filial o'quvchilari uchungina ochiq. Ro'yxat bo'sh
(standart) — /api/wordbank/* yo'llari HAMMAGA 404 qaytaradi, bo'lim
tashqaridan umuman ko'rinmaydi. Sabab: 20 000 so'z tarjimasi hali
tayyor emas, avval bitta pilot filialda sinaladi.

Qoidalar wordbank_core.py da (sof mantiq, testlangan) — bu yerda FAQAT
baza va HTTP; hech bir qoida qayta yozilmagan.

Xavfsizlik:
  * o'quvchi har doim tokendan topiladi, payload'dan emas;
  * savolni server beradi; to'g'ri javob va variantlar tartibi faqat
    serverda saqlanadi, mijozga "answer" yuborilmaydi;
  * har savolga BIR marta va faqat egasi javob beradi (shartli UPDATE —
    ikki bosishda ham ikkinchisi 409);
  * yozib topish (P) 1200 ms dan tez bo'lsa — shubhali va hech narsani
    o'zgartirmaydi; vaqt = mijoz ms va server oralig'ining KICHIGI
    (mijoz katta ms yozib tez javobini yashira olmaydi).
  * 2026-10-16 (review): shubhali javobga to'g'ri so'z ham, "to'g'ri/
    xato" bahosi ham QAYTARILMAYDI — aks holda ms=0 yuborib lemmani
    bepul bilib olib, o'sha kuni qayta berilgan savolga yozib, so'zni
    tasdiqlatish mumkin edi (DESIGN §2: taxmin bilan tasdiqlash ≈ 0).
  * 2026-10-16 (review): tanlash (R) variantlari bir o'quvchi + so'z +
    so'z holati uchun BARQAROR (har sessiyada bir xil to'plam) — avval
    har sessiya yangi tasodifiy variant berardi, 2–3 sessiya kesishmasi
    javob bermasdan to'g'ri variantni ochib qo'yardi. Server oralig'i
    esa o'quvchining barcha ochiq mashq sessiyalari bo'yicha o'lchanadi.
Coin (D1): UNIQUE(student_id, band) bir vaqtdagi ikki so'rovda ham
ikkinchi to'lovni to'xtatadi.
Hajm testi: natija faqat "taxminiy", so'z holatiga UMUMAN tegmaydi.
"""
import hashlib
import json
import os
import random
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import date, datetime, timedelta

from fastapi import APIRouter, Body, Depends, HTTPException
from sqlalchemy import and_, case, func, select, update as sa_update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

import audit
import auth
import models
import roles
import wordbank_core as WC
from auth import get_current_user
from database import get_db
from common import _student_of_user

router = APIRouter()

FLAG_KEY = "wordbank_branches"
SESSION_MAX = 20                      # bitta mashqda eng ko'p savol
SUSPECT_MS = 1200                     # yozib topish: bundan tez — shubhali
PRACTICE_TTL = timedelta(minutes=45)  # mashq sessiyasi muddati
TEST_TTL = timedelta(minutes=90)      # hajm testi (13 blok x 10 savol)
COIN_SOURCE = "vocab_band"
_NOT_FOUND = "Not Found"              # FastAPI'ning "yo'l yo'q" javobi bilan bir xil

_rng = random.SystemRandom()

W = models.WordbankWord
SW = models.WordbankStudentWord
SS = models.WordbankSession
SI = models.WordbankSessionItem
BA = models.WordbankBandAward
ST = models.WordbankSizeTest

# Mashqqa chiqa oladigan so'z: faol va o'zbekcha tarjimasi bor
_HAS_UZ = (W.status == "active", W.uz_primary.isnot(None), W.uz_primary != "")


# ------------------------------------------------------------- vaqt ---
# Testlar soatni shu ikki funksiya orqali suradi (kunlar, ms oralig'i).
def _now() -> datetime:
    return datetime.utcnow()


def _today() -> date:
    """Toshkent kuni (roles.local_today bilan bir xil, lekin _now dan)."""
    return roles.to_local(_now()).date()


# --------------------------------------------------------- bayroq/kirish ---
def enabled_branches(db: Session) -> set:
    """Yoqilgan filiallar. Qiymat: JSON ro'yxat ("[3, 5]") yoki "3,5".
    Bo'sh yoki yo'q — hech qayerda yoqilmagan."""
    try:
        row = db.query(models.IntegrationSetting).get(FLAG_KEY)
    except Exception:
        return set()
    raw = ((row.value if row is not None else "") or "").strip()
    if not raw:
        return set()
    try:
        v = json.loads(raw)
        items = v if isinstance(v, list) else [v]
    except ValueError:
        items = re.split(r"[,;\s]+", raw)
    out = set()
    for x in items:
        try:
            out.add(int(str(x).strip()))
        except (TypeError, ValueError):
            continue
    return out


def _student(db: Session, user) -> models.Student:
    """Kirgan o'quvchi. Bayroq o'chiq, o'quvchi emas yoki filiali
    yoqilmagan bo'lsa — 404 (bo'lim yo'qdek)."""
    on = enabled_branches(db)
    if not on:
        raise HTTPException(404, _NOT_FOUND)
    if getattr(user, "role", None) != roles.STUDENT:
        raise HTTPException(404, _NOT_FOUND)
    s = _student_of_user(db, user)
    if s is None or s.branch_id not in on:
        raise HTTPException(404, _NOT_FOUND)
    why = roles.student_app_block_reason(s.status)
    if why:
        raise HTTPException(403, why)
    return s


# ------------------------------------------------------ holat <-> qator ---
def _state(sw) -> WC.WordState:
    return WC.WordState(stage=int(sw.stage or 0), due=sw.due,
                        has_prod=bool(sw.has_prod), known=bool(sw.known),
                        lapses=int(sw.lapses or 0), last_move=sw.last_move)


def _put(sw, st: WC.WordState, now: datetime) -> None:
    was = bool(sw.known)
    sw.stage = st.stage
    sw.due = st.due
    sw.has_prod = 1 if st.has_prod else 0
    sw.known = 1 if st.known else 0
    sw.lapses = st.lapses
    sw.last_move = st.last_move
    if st.known and not was:
        sw.known_at = now
    elif not st.known:
        sw.known_at = None


# ----------------------------------------------------- savol yasash ---
def _norm(text) -> str:
    s = str(text or "").replace("’", "'").replace("‘", "'") \
        .replace("`", "'")
    s = re.sub(r"\s+", " ", s).strip().lower()
    return s.strip(".,!?;:\"' ")


def _alts(word) -> set:
    try:
        v = json.loads(word.uz_alt or "[]")
    except (TypeError, ValueError):
        v = []
    if isinstance(v, str):
        v = [v]
    return {_norm(x) for x in v if isinstance(x, str) and x.strip()}


def _pool(db: Session, band, cache: dict) -> list:
    """Chalg'ituvchi nomzodlar (id, uz) — QAT'IY tartibda.
    2026-10-16 (review): avval har chaqiriqda func.random() bilan 40 ta
    olinardi — bir so'z har sessiyada yangi variantlar bilan chiqardi va
    2–3 sessiya variantlarining kesishmasi (javob bermasdan) to'g'ri
    tarjimani ochib qo'yardi. Endi ro'yxat qat'iy, tasodif esa _opt_rng
    urug'idan (o'quvchi + so'z + holat) olinadi."""
    if band not in cache:
        q = db.query(W.id, W.uz_primary).filter(*_HAS_UZ)
        if band is not None:
            q = q.filter(W.band == band).order_by(W.id)
        else:
            q = q.order_by(W.rank).limit(200)
        cache[band] = q.all()
    return cache[band]


def _opt_states(db: Session, s, word_ids) -> dict:
    """{so'z: holat izi}. Iz faqat javob holatni o'zgartirganda (pog'ona
    yoki last_move) o'zgaradi — shu paytgacha variantlar to'plami bir xil."""
    ids = list(word_ids)
    if not ids:
        return {}
    return {wid: f"{stage}:{lm.isoformat() if lm else '-'}"
            for wid, stage, lm in
            db.query(SW.word_id, SW.stage, SW.last_move)
            .filter(SW.student_id == s.id, SW.word_id.in_(ids))}


def _opt_rng(student_id: int, word_id: int, fp: str) -> random.Random:
    """2026-10-16 (review): variantlar uchun barqaror tasodif. Urug' =
    server siri + o'quvchi + so'z + holat izi: o'quvchi uni hisoblay
    olmaydi, lekin qayta-qayta sessiya ochsa ham (yoki hajm testida)
    o'sha so'z uchun AYNAN o'sha 4 variantni ko'radi — kesishma hech
    narsa bermaydi. Javobdan keyin holat o'zgarsa — yangi to'plam."""
    key = f"{auth.SECRET_KEY}|wordbank-opts|{student_id}|{word_id}|{fp}"
    seed = int.from_bytes(hashlib.sha256(key.encode("utf-8")).digest()[:8],
                          "big")
    return random.Random(seed)


def _build_options(db: Session, word, cache: dict, rng: random.Random):
    """4 ta o'zbekcha variant (to'g'risi + 3 ta shu darajadan, yetmasa
    qo'shni darajadan). To'g'risining indeksi FAQAT serverda qoladi.
    Chalg'ituvchilar rng (barqaror urug') bilan tanlanadi; ekrandagi
    tartib esa har safar tasodifiy — to'plam bir xil bo'lgani uchun
    tartib hech narsa oshkor qilmaydi."""
    target = (word.uz_primary or "").strip()
    need = WC.K_CHOICES - 1
    seen = {_norm(target)} | _alts(word)
    picked: list = []
    for b in (word.band, word.band - 1, word.band + 1, None):
        if len(picked) >= need:
            break
        if b is not None and not 1 <= b <= WC.BANDS:
            continue
        pool = list(_pool(db, b, cache))
        rng.shuffle(pool)
        for wid, uz in pool:
            if len(picked) >= need:
                break
            key = _norm(uz)
            if wid == word.id or not key or key in seen:
                continue
            seen.add(key)
            picked.append(uz.strip())
    opts = picked + [target]
    _rng.shuffle(opts)
    return opts, opts.index(target)


def _gap(word):
    """Misoldagi so'z o'rniga "____" (yozib topish uchun). Topilmasa —
    misol ko'rsatilmaydi (javobni oshkor qilmaslik uchun)."""
    ex = (word.example_en or "").strip()
    lemma = (word.lemma or "").strip()
    if not ex or not lemma:
        return None
    rx = re.compile(r"(?<![A-Za-z])" + re.escape(lemma) + r"[A-Za-z]*", re.I)
    if not rx.search(ex):
        return None
    return rx.sub("____", ex)


def _mode_for(sw, word_id: int, day: date) -> str:
    """R — tanlash, P — yozib topish (DESIGN §4): 2-pog'onada hali P
    muvaffaqiyati yo'q so'z — P; tasdiqlanganlarda har 3 takrordan biri P."""
    if sw is None or (sw.stage or 0) <= 1:
        return "R"
    if sw.stage == 2:
        return "R" if sw.has_prod else "P"
    return "P" if (word_id + day.toordinal()) % 3 == 0 else "R"


def _item_out(item, word, options) -> dict:
    if item.mode == "R":
        return {"item_id": item.id, "mode": "R", "word": word.lemma,
                "options": options, "tts": True}
    return {"item_id": item.id, "mode": "P", "uz": word.uz_primary,
            "example": _gap(word), "example_uz": word.example_uz,
            "hint": (word.lemma or "")[:1]}


def _issue(db: Session, s, sess, picks: list, now: datetime) -> list:
    """picks: [(so'z, rejim)] -> sessiya savollari (javobsiz chiqadi)."""
    cache: dict = {}
    made = []
    fps = _opt_states(db, s, {w.id for w, m in picks if m == "R"})
    for i, (word, mode) in enumerate(picks):
        opts = None
        if mode == "R":
            rng = _opt_rng(s.id, word.id, fps.get(word.id, "new"))
            opts, idx = _build_options(db, word, cache, rng)
            expected = str(idx)
        else:
            expected = word.lemma
        it = SI(session_id=sess.id, student_id=s.id, word_id=word.id, seq=i,
                band=word.band, mode=mode, expected=expected, asked_at=now,
                options=(json.dumps(opts, ensure_ascii=False)
                         if opts is not None else None))
        db.add(it)
        made.append((it, word, opts))
    db.flush()
    return [_item_out(it, w, o) for it, w, o in made]


# ------------------------------------------------------- javob berish ---
def _body(payload) -> dict:
    """So'rov tanasi. Bayroq tekshiruvidan KEYIN chaqiriladi: tana yo'q
    yoki noto'g'ri bo'lsa ham o'chiq bo'limga 422 emas, 404 qaytadi."""
    if payload is None:
        return {}
    if not isinstance(payload, dict):
        raise HTTPException(400, "So'rov tanasi obyekt bo'lsin")
    return payload


def _load_session(db: Session, s, payload: dict, kind: str):
    try:
        sid = int(payload.get("session_id"))
    except (TypeError, ValueError):
        raise HTTPException(400, "session_id kerak")
    sess = db.query(SS).get(sid)
    if sess is None or sess.student_id != s.id or sess.kind != kind:
        raise HTTPException(404, "Sessiya topilmadi")
    return sess


def _load_item(db: Session, sess, item_id):
    try:
        iid = int(item_id)
    except (TypeError, ValueError):
        raise HTTPException(400, "item_id kerak")
    item = db.query(SI).get(iid)
    if item is None or item.session_id != sess.id:
        raise HTTPException(404, "Savol topilmadi")
    return item


def _check_open(sess, now: datetime) -> None:
    if sess.closed_at is not None:
        raise HTTPException(409, "Sessiya yopilgan")
    if sess.expires_at is not None and now > sess.expires_at:
        raise HTTPException(410, "Sessiya muddati tugagan — yangisini boshlang")


def _grade(item, given):
    """(to'g'rimi, saqlanadigan javob). R: variant indeksi; P: yozilgan
    so'z (katta-kichik harf va chetdagi bo'shliq/tinish farq qilmaydi,
    lemma qabul qilinadi). Bo'sh / "Bilmayman" — (False, None)."""
    if item.mode == "R":
        if given is None or isinstance(given, bool):
            return False, None
        try:
            idx = int(given)
        except (TypeError, ValueError):
            return False, None
        try:
            n = len(json.loads(item.options or "[]"))
        except (TypeError, ValueError):
            n = 0
        if not 0 <= idx < n:
            return False, None
        return idx == int(item.expected), str(idx)
    text = _norm(given) if isinstance(given, str) else ""
    if not text:
        return False, None
    return text == _norm(item.expected), given.strip()[:64]


def _reveal(item) -> str:
    if item.mode == "R":
        try:
            return json.loads(item.options or "[]")[int(item.expected)]
        except (TypeError, ValueError, IndexError):
            return ""
    return item.expected


def _elapsed_ms(db: Session, sess, item, now: datetime, client_ms,
                since_prev: bool = True) -> int:
    """Javobga ketgan vaqt: server oralig'i (o'quvchining oldingi
    javobidan yoki savol berilgandan beri) va mijoz ms ning KICHIGI.

    2026-10-16 (review): "oldingi javob" endi faqat shu sessiyadan emas,
    o'quvchining so'nggi PRACTICE_TTL ichida ochilgan BARCHA shu turdagi
    sessiyalaridan olinadi. Sabab: bir necha bitta-savollik sessiyani
    oldindan ochib, hammasiga millisekundlar ichida javob bersa, har biri
    o'z sessiyasida "birinchi javob" bo'lib 1200 ms tekshiruvidan o'tib
    ketardi. Javob berish mumkin bo'lgan har sessiya shu oynada (aks holda
    _check_open 410 qaytaradi)."""
    prev = None
    if since_prev:
        recent = select(SS.id).where(
            SS.student_id == sess.student_id, SS.kind == sess.kind,
            SS.created_at >= now - PRACTICE_TTL)
        prev = (db.query(func.max(SI.answered_at))
                .filter(SI.session_id.in_(recent), SI.id != item.id)
                .scalar())
    marks = [x for x in (prev, item.asked_at, sess.created_at)
             if x is not None]
    base = min(max(marks), now) if marks else now
    gap = int((now - base).total_seconds() * 1000)
    try:
        c = int(client_ms) if client_ms is not None else None
    except (TypeError, ValueError):
        c = None
    if c is not None and c >= 0:
        return min(gap, c)
    return gap


def _mark(db: Session, item, given_s, correct: bool, suspect: bool,
          ms, now: datetime) -> None:
    """Savolni javob berilgan deb belgilaydi — FAQAT hali javobsiz
    bo'lsa (shartli UPDATE). Ikki bosish / ikki qurilma: ikkinchisi 409."""
    r = db.execute(
        sa_update(SI)
        .where(SI.id == item.id, SI.answered_at.is_(None))
        .values(given=given_s, correct=1 if correct else 0,
                suspect=1 if suspect else 0, answered_at=now, ms=ms)
        .execution_options(synchronize_session=False))
    if r.rowcount != 1:
        db.rollback()
        raise HTTPException(409, "Bu savolga allaqachon javob berilgan")
    db.expire(item)


# -------------------------------------------------------------- coin ---
def _pay_band(db: Session, s, band: int, coins: int):
    """Bitta daraja uchun to'lov (D1). Avval UNIQUE qator (savepoint):
    u allaqachon bo'lsa — hech narsa qilinmaydi. Keyin mavjud coin
    yozuvi tekshiriladi (birlashtirilgan o'quvchida eski hisobning coini
    ko'chib kelgan bo'lishi mumkin) va faqat yo'q bo'lsa yangisi yoziladi.
    common._sync_coin_entry ISHLATILMAYDI: u faqat (source, ref_id) bo'yicha
    qidiradi — ref_id = daraja raqami barcha o'quvchilarda bir xil,
    ya'ni boshqa bolaning coinini "yangilab" yuborardi."""
    aw = BA(student_id=s.id, band=band, coins=coins, awarded_at=_now())
    try:
        with db.begin_nested():
            db.add(aw)
            db.flush()
    except IntegrityError:
        return None
    prev = (db.query(models.CoinEntry)
            .filter(models.CoinEntry.student_id == s.id,
                    models.CoinEntry.source == COIN_SOURCE,
                    models.CoinEntry.ref_id == band).first())
    if prev is not None:
        aw.coin_entry_id = prev.id
        db.flush()
        return {"band": band, "coins": 0, "already_paid": True}
    ce = models.CoinEntry(
        student_id=s.id, amount=coins, source=COIN_SOURCE, ref_id=band,
        note=f"So'z bilish: Common {band}000 tugatildi (+{coins} coin)",
        created_by="Tizim")
    db.add(ce)
    db.flush()
    aw.coin_entry_id = ce.id
    # AUDIT — coin pulga aylanadi, iz qolishi shart (qo'lda coin
    # berishdagi bilan bir xil uslub: students.add_manual_coins).
    audit.log(db, None, entity="student", action=COIN_SOURCE,
              entity_id=s.id, entity_label=s.full_name, field=COIN_SOURCE,
              new_value=f"Common {band}000: +{coins} coin",
              note="So'z bilish: daraja tugatildi", branch_id=s.branch_id)
    db.flush()
    return {"band": band, "coins": coins}


def _award_bands(db: Session, s, bands) -> list:
    """Berilgan darajalardan qaysilari to'liq tasdiqlangan bo'lsa
    (wordbank_core.bands_completed) — yangilari uchun coin."""
    bands = {int(b) for b in bands if b}
    if not bands:
        return []
    band_ids = {b: set() for b in bands}
    for wid, b in (db.query(W.id, W.band)
                   .filter(W.band.in_(bands), W.status == "active")):
        band_ids[b].add(wid)
    known = {b: set() for b in bands}
    for wid, b in (db.query(SW.word_id, W.band)
                   .join(W, W.id == SW.word_id)
                   .filter(SW.student_id == s.id, SW.known == 1,
                           W.band.in_(bands), W.status == "active")):
        known[b].add(wid)
    done = WC.bands_completed(known, band_ids)
    if not done:
        return []
    already = {b for (b,) in db.query(BA.band).filter(BA.student_id == s.id)}
    out = []
    for band, coins in WC.new_band_awards(done, already):
        r = _pay_band(db, s, band, coins)
        if r:
            out.append(r)
    return out


# ------------------------------------------------------------ yo'llar ---
@router.get("/api/wordbank/me")
def wordbank_me(db: Session = Depends(get_db),
                user=Depends(get_current_user)):
    """Tasdiqlangan so'zlar (wordbank_core.known_count), darajalar
    bo'yicha, va oxirgi hajm testi ALOHIDA — "taxminiy" (hech qachon
    qo'shilmaydi)."""
    s = _student(db, user)
    day = _today()
    by_band: dict = {}
    due_today = 0
    for sw, b in (db.query(SW, W.band).join(W, W.id == SW.word_id)
                  .filter(SW.student_id == s.id, W.status == "active")):
        st = _state(sw)
        by_band.setdefault(b, []).append(st)
        if st.due is not None and st.due <= day:
            due_today += 1
    totals = {b: int(n) for b, n in
              db.query(W.band, func.count(W.id))
              .filter(W.status == "active").group_by(W.band)}
    awards = {a.band: a for a in
              db.query(BA).filter(BA.student_id == s.id)}
    # O'z-o'zini tiklash: daraja to'liq, lekin coin yozilmagan (masalan
    # so'z o'chirilib daraja kichraydi) — shu yerda bir marta to'lanadi.
    heal = [b for b, n in totals.items()
            if n and b not in awards
            and WC.known_count(by_band.get(b, [])) >= n]
    if heal and _award_bands(db, s, heal):
        db.commit()
        awards = {a.band: a for a in
                  db.query(BA).filter(BA.student_id == s.id)}
    known = WC.known_count(st for sts in by_band.values() for st in sts)
    bands = []
    for b in range(1, WC.BANDS + 1):
        sts = by_band.get(b, [])
        k = WC.known_count(sts)
        a = awards.get(b)
        bands.append({
            "band": b, "label": f"Common {b}000",
            "total": totals.get(b, 0), "known": k,
            "learning": len(sts) - k, "ready": totals.get(b, 0) > 0,
            "coins": WC.coins_for_band(b), "done": a is not None,
            "awarded_at": (a.awarded_at.isoformat()
                           if a is not None and a.awarded_at else None),
        })
    last = (db.query(ST).filter(ST.student_id == s.id)
            .order_by(ST.created_at.desc(), ST.id.desc()).first())
    return {
        "known": known,
        "known_label": "Tasdiqlangan so'zlar",
        "due_today": due_today,
        "bands": bands,
        "coins_earned": sum(int(a.coins or 0) for a in awards.values()),
        "size_test": _test_out(last) if last is not None else None,
    }


@router.post("/api/wordbank/session")
def wordbank_session(payload=Body(default=None),
                     db: Session = Depends(get_db),
                     user=Depends(get_current_user)):
    """Bugungi mashq: avval vaqti kelgan so'zlar (unutilgan va 2-pog'ona
    oldinda), keyin yangi so'zlar rank tartibida. Tarjimasiz so'z chiqmaydi."""
    s = _student(db, user)
    raw = _body(payload).get("size")
    try:
        size = SESSION_MAX if raw is None else int(raw)
    except (TypeError, ValueError):
        raise HTTPException(400, "size noto'g'ri")
    if not 1 <= size <= SESSION_MAX:
        raise HTTPException(400, f"size 1 dan {SESSION_MAX} gacha bo'lsin")
    now, day = _now(), _today()
    prio = case((and_(SW.stage == 2, SW.lapses > 0), 0),
                (SW.stage == 2, 1), else_=2)
    due = (db.query(SW, W).join(W, W.id == SW.word_id)
           .filter(SW.student_id == s.id, SW.due.isnot(None),
                   SW.due <= day, *_HAS_UZ)
           .order_by(prio, SW.due, W.rank).limit(size).all())
    picks = [(w, _mode_for(sw, w.id, day)) for sw, w in due]
    left = size - len(picks)
    if left > 0:
        tracked = (db.query(SW.id)
                   .filter(SW.student_id == s.id, SW.word_id == W.id)
                   .exists())
        for w in (db.query(W).filter(*_HAS_UZ).filter(~tracked)
                  .order_by(W.rank).limit(left)):
            picks.append((w, "R"))      # birinchi ko'rish — tanlash
    if not picks:
        return {"session_id": None, "kind": "practice", "items": [],
                "message": "Bugun uchun savol qolmadi"}
    sess = SS(student_id=s.id, kind="practice", created_at=now,
              expires_at=now + PRACTICE_TTL)
    db.add(sess)
    db.flush()
    items = _issue(db, s, sess, picks, now)
    db.commit()
    return {"session_id": sess.id, "kind": "practice",
            "expires_at": sess.expires_at.isoformat(), "items": items}


@router.post("/api/wordbank/answer")
def wordbank_answer(payload=Body(default=None),
                    db: Session = Depends(get_db),
                    user=Depends(get_current_user)):
    """Mashq savoliga javob — server baholaydi va wordbank_core qoidasini
    qo'llaydi. Kuzatilmagan so'zga birinchi to'g'ri javob — fast track."""
    s = _student(db, user)
    payload = _body(payload)
    sess = _load_session(db, s, payload, "practice")
    item = _load_item(db, sess, payload.get("item_id"))
    if item.answered_at is not None:
        raise HTTPException(409, "Bu savolga allaqachon javob berilgan")
    now = _now()
    _check_open(sess, now)
    correct, given_s = _grade(item, payload.get("given"))
    mode = item.mode
    ms = _elapsed_ms(db, sess, item, now, payload.get("ms"))
    suspect = mode == "P" and ms < SUSPECT_MS
    _mark(db, item, given_s, correct, suspect, ms, now)

    day = roles.to_local(now).date()
    sw = (db.query(SW).filter(SW.student_id == s.id,
                              SW.word_id == item.word_id).first())
    before_known = False
    if sw is None:
        if correct and not suspect:
            st = WC.fast_track(day)
        else:
            st = WC.apply_answer(WC.new_word(day), day, mode, False)
        sw = SW(student_id=s.id, word_id=item.word_id, created_at=now)
        _put(sw, st, now)
        try:
            with db.begin_nested():
                db.add(sw)
                db.flush()
        except IntegrityError:
            # Boshqa qurilmadagi javob shu so'zni hozirgina yaratdi —
            # oddiy yo'l bilan uning ustiga qo'llaymiz.
            sw = (db.query(SW).filter(SW.student_id == s.id,
                                      SW.word_id == item.word_id).first())
            before = _state(sw)
            before_known = before.known
            st = WC.apply_answer(before, day, mode, correct, suspect=suspect)
            _put(sw, st, now)
    else:
        before = _state(sw)
        before_known = before.known
        st = WC.apply_answer(before, day, mode, correct, suspect=suspect)
        _put(sw, st, now)
    db.flush()

    awards = []
    if st.known and not before_known:
        band = db.query(W.band).filter(W.id == item.word_id).scalar()
        awards = _award_bands(db, s, {band})
    db.commit()
    db.refresh(item)
    out = {"correct": correct, "expected": _reveal(item),
           "suspect": suspect, "stage": st.stage, "known": st.known,
           "due": st.due.isoformat() if st.due else None,
           "awards": awards}
    if suspect:
        # 2026-10-16 (review): shubhali javob holatni o'zgartirmaydi va so'z
        # bugun yana beriladi. Shu sababli bu yerda to'g'ri so'z (lemma)
        # ham, "to'g'ri/xato" bahosi ham QAYTARILMAYDI: aks holda ms=0
        # bilan istalgan matn yuborib javobni bepul ko'rib (yoki taxminni
        # bepul tekshirib), qayta berilgan savolga 1,2 s dan keyin yozib
        # so'zni o'sha kuni tasdiqlatish mumkin edi. Haqiqiy baho bazada
        # (SI.correct) qoladi — keyingi anti-cheat hisobi uchun.
        out.update(correct=None, expected=None,
                   message="Juda tez yozildi — javob hisobga olinmadi. "
                           "So'z keyinroq yana beriladi.")
    return out


# --------------------------------------------------------- hajm testi ---
def _results(db: Session, sess) -> dict:
    """Sessiyadagi javoblar: {daraja: (R, W, n)}. "Bilmayman" (given
    bo'sh) — na R, na W."""
    agg: dict = {}
    for band, given, correct in (db.query(SI.band, SI.given, SI.correct)
                                 .filter(SI.session_id == sess.id,
                                         SI.answered_at.isnot(None))):
        r, w, n = agg.get(band, (0, 0, 0))
        n += 1
        if correct:
            r += 1
        elif given is not None:
            w += 1
        agg[band] = (r, w, n)
    return agg


def _for_core(agg: dict) -> dict:
    """wordbank_core 10 savollik blokni kutadi; darajada 10 tadan kam so'z
    bo'lsa (kontent to'liq emas) ulush 10 ga moslab beriladi."""
    out = {}
    for b, (r, w, n) in agg.items():
        if b is None or n <= 0:
            continue
        f = WC.TEST_N / float(n)
        out[int(b)] = (r * f, w * f)
    return out


def _eligible_ids(db: Session, band: int) -> list:
    return [wid for (wid,) in db.query(W.id).filter(W.band == band, *_HAS_UZ)
            .order_by(W.rank)]


def _pick_band(db: Session, res: dict):
    """wordbank_core.next_test_band; tarjimasi yo'q (hali tayyor emas)
    daraja sinalmaydi — 0 deb o'tib ketiladi."""
    res = dict(res)
    while True:
        band = WC.next_test_band(res)
        if band is None:
            return None, []
        ids = _eligible_ids(db, band)
        if ids:
            return band, ids
        res[band] = (0.0, 0.0)


def _test_block(db: Session, s, sess, ids: list, now: datetime) -> list:
    """Daraja 10 qatlamga bo'linadi, har qatlamdan bitta tasodifiy so'z."""
    n = min(WC.TEST_N, len(ids))
    picks = []
    for k in range(n):
        lo, hi = k * len(ids) // n, (k + 1) * len(ids) // n
        picks.append(ids[_rng.randrange(lo, hi)])
    words = db.query(W).filter(W.id.in_(picks)).all()
    _rng.shuffle(words)
    return _issue(db, s, sess, [(w, "R") for w in words], now)


def _close_unanswered(db: Session, sess, now: datetime, band=None) -> None:
    q = sa_update(SI).where(SI.session_id == sess.id,
                            SI.answered_at.is_(None))
    if band is not None:
        q = q.where(SI.band == band)
    db.execute(q.values(answered_at=now, given=None, correct=0)
               .execution_options(synchronize_session=False))


def _test_out(row) -> dict:
    try:
        bands = json.loads(row.results or "{}")
    except (TypeError, ValueError):
        bands = {}
    return {"taxminiy": True, "label": "Taxminiy lug'at hajmi",
            "test_id": row.id, "estimate": row.estimate, "low": row.low,
            "high": row.high, "bands": bands,
            "date": row.created_at.date().isoformat() if row.created_at
            else None}


def _finish(db: Session, s, sess, now: datetime) -> dict:
    """Natija (wordbank_core.size_estimate) saqlanadi. So'z holatiga
    TEGMAYDI. Ikkinchi chaqiruv saqlangan natijani qaytaradi."""
    old = db.query(ST).filter(ST.session_id == sess.id).first()
    if old is not None:
        return _test_out(old)
    _close_unanswered(db, sess, now)
    agg = _results(db, sess)
    est = WC.size_estimate(_for_core(agg)) or \
        {"estimate": 0, "low": 0, "high": 0}
    row = ST(student_id=s.id, session_id=sess.id, created_at=now,
             results=json.dumps({str(b): [r, w, n]
                                 for b, (r, w, n) in sorted(agg.items())
                                 if b is not None}),
             estimate=int(est["estimate"]), low=int(est["low"]),
             high=int(est["high"]))
    try:
        with db.begin_nested():
            db.add(row)
            db.flush()
    except IntegrityError:
        return _test_out(db.query(ST).filter(ST.session_id == sess.id)
                         .first())
    sess.closed_at = now
    db.flush()
    return _test_out(row)


@router.post("/api/wordbank/size-test/start")
def size_test_start(db: Session = Depends(get_db),
                    user=Depends(get_current_user)):
    """Lug'at hajmi testi: 1-darajadan boshlab 10 talik bloklar."""
    s = _student(db, user)
    now = _now()
    band, ids = _pick_band(db, {})
    if band is None:
        raise HTTPException(409, "Test uchun so'zlar hali tayyor emas")
    sess = SS(student_id=s.id, kind="size_test", band=band, created_at=now,
              expires_at=now + TEST_TTL)
    db.add(sess)
    db.flush()
    items = _test_block(db, s, sess, ids, now)
    db.commit()
    return {"session_id": sess.id, "band": band, "items": items,
            "expires_at": sess.expires_at.isoformat()}


@router.post("/api/wordbank/size-test/next")
def size_test_next(payload=Body(default=None),
                   db: Session = Depends(get_db),
                   user=Depends(get_current_user)):
    """Joriy blok javoblari: {session_id, band, answers: [{item_id,
    given}]} (given — variant indeksi yoki null = "Bilmayman"). Javobsiz
    qolganlar "Bilmayman". Keyingi blok yoki tugagan bo'lsa natija."""
    s = _student(db, user)
    payload = _body(payload)
    sess = _load_session(db, s, payload, "size_test")
    now = _now()
    _check_open(sess, now)
    cur = sess.band
    if payload.get("band") is not None:
        try:
            claimed = int(payload.get("band"))
        except (TypeError, ValueError):
            raise HTTPException(400, "band noto'g'ri")
        if claimed != cur:
            raise HTTPException(409, "Bu blok allaqachon yopilgan")
    answers = payload.get("answers") or []
    if not isinstance(answers, list):
        raise HTTPException(400, "answers ro'yxat bo'lsin")
    for a in answers:
        if not isinstance(a, dict):
            raise HTTPException(400, "answers ro'yxat bo'lsin")
        item = _load_item(db, sess, a.get("item_id"))
        if item.band != cur:
            raise HTTPException(409, "Bu blok allaqachon yopilgan")
        if item.answered_at is not None:
            raise HTTPException(409, "Bu savolga allaqachon javob berilgan")
        correct, given_s = _grade(item, a.get("given"))
        ms = _elapsed_ms(db, sess, item, now, a.get("ms"),
                         since_prev=False)
        _mark(db, item, given_s, correct, False, ms, now)
    _close_unanswered(db, sess, now, band=cur)

    band, ids = _pick_band(db, _for_core(_results(db, sess)))
    if band is None:
        result = _finish(db, s, sess, now)
        db.commit()
        return {"done": True, "result": result}
    # Ikki bosish: blokni faqat BIR so'rov oldinga sura oladi.
    r = db.execute(sa_update(SS).where(SS.id == sess.id, SS.band == cur)
                   .values(band=band)
                   .execution_options(synchronize_session=False))
    if r.rowcount != 1:
        db.rollback()
        raise HTTPException(409, "Bu blok allaqachon yopilgan")
    items = _test_block(db, s, sess, ids, now)
    db.commit()
    return {"done": False, "band": band, "items": items}


@router.post("/api/wordbank/size-test/finish")
def size_test_finish(payload=Body(default=None),
                     db: Session = Depends(get_db),
                     user=Depends(get_current_user)):
    """Testni tugatish (javobsizlar — "Bilmayman"). Natija "taxminiy",
    tasdiqlangan son, coin va so'z holatiga ta'sir qilmaydi."""
    s = _student(db, user)
    sess = _load_session(db, s, _body(payload), "size_test")
    result = _finish(db, s, sess, _now())
    db.commit()
    return {"done": True, "result": result}
