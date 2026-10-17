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

2026-10-16 (3-qadam):
  * bayroq qiymati "all" ham bo'lishi mumkin — BARCHA filiallar (keyin
    ochilgan filial ham avtomat kiradi). Jahongir: "barcha filiallar".
  * GET/PUT /api/wordbank/admin — faqat ASOSCHI; filiallarni yoqish /
    o'chirish, har o'zgarish auditda. Bir martalik "hammaga ochish"
    seedi shu yerdan qaytariladi (masalan [] — hamma joyda yopiq).
  * so'zlar api/wordbank_data/words.json dan yuklanadi (load_words):
    lemma bo'yicha upsert, HECH NARSA O'CHIRILMAYDI; fayl yo'q bo'lsa
    jim o'tadi. Startda seed_startup chaqiriladi (main.py).

2026-10-16 (review, 2-davra):
  * daraja faqat TO'LIQ yuklangan bo'lsa (kamida BAND_SIZE so'z o'rni)
    "tayyor": yangi so'z beradi, tugasa coin to'laydi, "hammaga ochish"
    1-daraja to'liq bo'lmaguncha kutadi (D1: "1000 tasining hammasi");
  * vaqt tugashi (timeout) — "o'tkazib yuborildi" deb yoziladi, so'z
    holatiga TEGMAYDI va javob ochilmaydi (DESIGN §2);
  * hajm testini erta tugatish joriy blok javoblarini /finish ga beradi —
    ko'rilmagan yangi blok natijaga qo'shilmaydi;
  * asoschining birinchi PUT [] i ham saqlanadi ("hammaga ochish" uni
    bosib ketmaydi); rank to'qnashuvlari chiziqli hal qilinadi.

2026-10-17 (2–3-bosqich, D2–D4): reyting, tarix va sertifikatlar
alohida modullarda (wordbank_social.py, wordbank_certs.py). Bu yerda
faqat ikki ulanish: /me javobiga ranks / best_known / certs /
certs_pending (wordbank_social.me_extras) va daraja to'langanda tarix
qatori (wordbank_social.refresh_hall).
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
from sqlalchemy import and_, case, func, insert as sa_insert, select, \
    text as sa_text, update as sa_update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

import audit
import auth
import models
import roles
import wordbank_core as WC
from auth import get_current_user, require_role
from database import get_db
from common import _student_of_user

router = APIRouter()

FLAG_KEY = "wordbank_branches"
ALL = "all"                           # bayroq: barcha filiallar (2026-10-16)
SESSION_MAX = 20                      # bitta mashqda eng ko'p savol
SUSPECT_MS = 1200                     # yozib topish: bundan tez — shubhali
PRACTICE_TTL = timedelta(minutes=45)  # mashq sessiyasi muddati
TEST_TTL = timedelta(minutes=90)      # hajm testi (13 blok x 10 savol)
COIN_SOURCE = "vocab_band"
_NOT_FOUND = "Not Found"              # FastAPI'ning "yo'l yo'q" javobi bilan bir xil
# 2026-10-16 (review): daraja shuncha so'z o'rniga ega bo'lgandagina to'liq
# (mashq, coin, "ready"). Testlar kichik to'plam uchun kamaytiradi.
BAND_SIZE = WC.WORDS_PER_BAND
# 2026-10-16 (review): savol vaqti (DESIGN §2) — "vaqt tugadi" da'vosi
# server oralig'i bilan tekshiriladi (tez yuborilgan "timeout" — oddiy
# "Bilmayman"); SLACK — tarmoq/soat farqi uchun.
LIMIT_MS = {"R": 15000, "P": 30000}
TIMEOUT_SLACK_MS = 1000

_rng = random.SystemRandom()

W = models.WordbankWord
SW = models.WordbankStudentWord
SS = models.WordbankSession
SI = models.WordbankSessionItem
BA = models.WordbankBandAward
ST = models.WordbankSizeTest

# Mashqqa chiqa oladigan so'z: faol va o'zbekcha tarjimasi bor
_HAS_UZ = (W.status == "active", W.uz_primary.isnot(None), W.uz_primary != "")


def _ready_bands(db: Session) -> set:
    """2026-10-16 (review): kontenti TO'LIQ yuklangan darajalar.

    Sabab: words.json dan skip=true / tarjimasiz qatorlar tushmaydi, budjet
    bilan esa daraja bir necha startda to'ladi. Avval "daraja tugadi" faqat
    bazadagi faol so'zlar bo'yicha hisoblanardi — 2 ta so'zi yuklangan
    1-daraja ham tugab, coin to'lardi va keyin qolgan so'zlar kelsa ham coin
    qaytmasdi (D1: "1000 tasining hammasi tasdiqlangan").

    Endi daraja kamida BAND_SIZE so'z o'rniga ega bo'lsagina "tayyor": unda
    yangi so'z beriladi, tugasa coin to'lanadi. O'rin = har qanday holatdagi
    qator: keyin o'chirilgan (disabled) so'z ham o'rin bo'lib qoladi — DESIGN
    §9: o'chirilgan so'z darajani yopmaydi, faqat band_total ni kamaytiradi.
    Yuklovchi qator o'chirmaydi, ya'ni tayyor daraja tayyorligicha qoladi."""
    return {int(b) for b, n in
            db.query(W.band, func.count(W.id)).group_by(W.band)
            if b is not None and int(n) >= BAND_SIZE}


# ------------------------------------------------------------- vaqt ---
# Testlar soatni shu ikki funksiya orqali suradi (kunlar, ms oralig'i).
def _now() -> datetime:
    return datetime.utcnow()


def _today() -> date:
    """Toshkent kuni (roles.local_today bilan bir xil, lekin _now dan)."""
    return roles.to_local(_now()).date()


# --------------------------------------------------------- bayroq/kirish ---
def _flag_raw(db: Session) -> str:
    try:
        row = db.query(models.IntegrationSetting).get(FLAG_KEY)
    except Exception:
        return ""
    return ((row.value if row is not None else "") or "").strip()


def _is_all(x) -> bool:
    return isinstance(x, str) and x.strip().lower() == ALL


def parse_flag(raw):
    """Bayroq qiymati -> ALL yoki filial id'lari to'plami.
    Qiymat: "all" (2026-10-16 — barcha filiallar, keyin ochilgani ham),
    JSON ro'yxat ("[3, 5]") yoki "3,5". Bo'sh / "[]" — hech qayerda."""
    raw = (raw or "").strip()
    if not raw:
        return set()
    if _is_all(raw):
        return ALL
    try:
        v = json.loads(raw)
        items = v if isinstance(v, list) else [v]
    except ValueError:
        items = re.split(r"[,;\s]+", raw)
    if any(_is_all(x) for x in items):
        return ALL
    out = set()
    for x in items:
        if isinstance(x, bool):
            continue
        try:
            out.add(int(str(x).strip()))
        except (TypeError, ValueError):
            continue
    return out


def flag_value(db: Session):
    """ALL yoki yoqilgan filial id'lari (bo'sh to'plam — hamma joyda yopiq)."""
    return parse_flag(_flag_raw(db))


def enabled_branches(db: Session) -> set:
    """Yoqilgan filiallar to'plami. "all" bo'lsa — bazadagi BARCHA
    filiallar (eski chaqiruvchilar uchun bir xil ko'rinish)."""
    v = flag_value(db)
    if v == ALL:
        try:
            return {bid for (bid,) in db.query(models.Branch.id)}
        except Exception:
            return set()
    return v


def branch_enabled(db: Session, branch_id) -> bool:
    v = flag_value(db)
    return v == ALL or (branch_id is not None and branch_id in v)


def _student(db: Session, user) -> models.Student:
    """Kirgan o'quvchi. Bayroq o'chiq, o'quvchi emas yoki filiali
    yoqilmagan bo'lsa — 404 (bo'lim yo'qdek). "all" — hamma filial."""
    on = flag_value(db)
    if not on:
        raise HTTPException(404, _NOT_FOUND)
    if getattr(user, "role", None) != roles.STUDENT:
        raise HTTPException(404, _NOT_FOUND)
    s = _student_of_user(db, user)
    if s is None or (on != ALL and s.branch_id not in on):
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
    misol ko'rsatilmaydi (javobni oshkor qilmaslik uchun).
    2026-10-16 (review): faqat lemma va uning muntazam shakli bo'shliqqa
    aylanadi (wordbank_core.gap_regex) — avval lemma bilan BOSHLANGAN har
    so'z ham ("volt" -> "voltage") ikkinchi bo'shliq bo'lib qolardi."""
    ex = (word.example_en or "").strip()
    lemma = (word.lemma or "").strip()
    if not ex or not lemma:
        return None
    rx = WC.gap_regex(lemma)
    if not rx.search(ex):
        return None
    return rx.sub("____", ex)


def _gap_forms(word) -> set:
    """Bo'shliqqa aylangan shakllar — yozib topishda ular ham to'g'ri
    (DESIGN §2: "the exact form in the gapped example"). 2026-10-16."""
    return {_norm(f) for f in WC.gap_forms((word.lemma or "").strip(),
                                           (word.example_en or "").strip())}


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


def _grade(item, given, forms=None):
    """(to'g'rimi, saqlanadigan javob). R: variant indeksi; P: yozilgan
    so'z (katta-kichik harf va chetdagi bo'shliq/tinish farq qilmaydi,
    lemma va — 2026-10-16 — misoldagi bo'shliq shakli `forms` qabul
    qilinadi). Bo'sh / "Bilmayman" — (False, None)."""
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
    ok = text == _norm(item.expected) or text in (forms or ())
    return ok, given.strip()[:64]


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
    (wordbank_core.bands_completed) — yangilari uchun coin.
    2026-10-16 (review): faqat kontenti to'liq darajalar (_ready_bands) —
    qisman yuklangan daraja coin to'lamaydi (coin keyin qaytarilmaydi)."""
    bands = {int(b) for b in bands if b}
    if bands:
        bands &= _ready_bands(db)
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
    if out:
        # 2026-10-17 (D4, tarix): tugatilgan daraja darhol "Tarix" ga
        # yoziladi (wordbank_social.refresh_hall, commit — chaqiruvchida).
        # Savepoint ichida: tarix yozuvidagi xato coin to'lovini
        # bekor qilmasin — qator keyingi /me da baribir yangilanadi.
        try:
            import wordbank_social as WSOC
            with db.begin_nested():
                WSOC.refresh_hall(db, s.id)
        except Exception as e:                  # noqa: BLE001
            print(f"[wordbank-hall] award {s.id}: {e!r}")
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
    ready = _ready_bands(db)
    # O'z-o'zini tiklash: daraja to'liq, lekin coin yozilmagan (masalan
    # so'z o'chirilib daraja kichraydi) — shu yerda bir marta to'lanadi.
    # 2026-10-16 (review): faqat kontenti to'liq daraja (ready).
    heal = [b for b, n in totals.items()
            if n and b in ready and b not in awards
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
            "learning": len(sts) - k,
            "ready": b in ready and totals.get(b, 0) > 0,
            "coins": WC.coins_for_band(b), "done": a is not None,
            "awarded_at": (a.awarded_at.isoformat()
                           if a is not None and a.awarded_at else None),
        })
    last = (db.query(ST).filter(ST.student_id == s.id)
            .order_by(ST.created_at.desc(), ST.id.desc()).first())
    out = {
        "known": known,
        "known_label": "Tasdiqlangan so'zlar",
        "due_today": due_today,
        "bands": bands,
        "coins_earned": sum(int(a.coins or 0) for a in awards.values()),
        "size_test": _test_out(last) if last is not None else None,
    }
    # 2026-10-17 (D2–D4): reytingdagi o'rin (guruh / filial / markaz),
    # eng yaxshi natija (tarix), FAQAT tasdiqlangan sertifikatlar va
    # tekshirilayotganlar SONI (ball yo'q). Arzon tarix yangilanishi ham
    # shu yerda (wordbank_social.me_extras).
    import wordbank_social as WSOC
    out.update(WSOC.me_extras(db, s, known))
    return out


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
    # 2026-10-16 (review): yangi so'z faqat kontenti to'liq darajadan
    # (_ready_bands) — qisman yuklangan daraja mashqqa ochilmaydi.
    ready = _ready_bands(db) if left > 0 else set()
    if left > 0 and ready:
        tracked = (db.query(SW.id)
                   .filter(SW.student_id == s.id, SW.word_id == W.id)
                   .exists())
        for w in (db.query(W).filter(*_HAS_UZ)
                  .filter(W.band.in_(sorted(ready)), ~tracked)
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


def _timeout(db: Session, s, sess, item, now: datetime, client_ms):
    """2026-10-16 (review): "vaqt tugadi" (DESIGN §2: o'tkazib yuborilgan
    deb yoziladi, pog'ona o'zgarmaydi, so'z vaqti kelganicha qoladi).

    Avval mijoz vaqt tugaganda given=null yuborardi va server uni oddiy
    xato deb hisoblardi: tasdiqlangan so'z unutilgan bo'lib qolardi, ochiq
    qoldirilgan mashq esa 20 ta savolni ketma-ket "xato" qilardi.

    Da'vo server oralig'i bilan tekshiriladi: savol vaqtidan (LIMIT_MS)
    tezroq kelgan "timeout" — None qaytadi va oddiy "Bilmayman" sifatida
    baholanadi (xatodan qochish uchun ishlatib bo'lmaydi). To'g'ri javob
    QAYTARILMAYDI: aks holda vaqtni o'tkazib javobni ko'rib, keyingi
    sessiyada (so'z hali vaqti kelgan) yozib, unutish o'rniga pog'ona olish
    mumkin edi."""
    gap = _elapsed_ms(db, sess, item, now, None)
    if gap < LIMIT_MS.get(item.mode, LIMIT_MS["R"]) - TIMEOUT_SLACK_MS:
        return None
    ms = _elapsed_ms(db, sess, item, now, client_ms)
    _mark(db, item, None, False, False, ms, now)
    sw = (db.query(SW).filter(SW.student_id == s.id,
                              SW.word_id == item.word_id).first())
    st = _state(sw) if sw is not None else None
    db.commit()
    return {"correct": None, "expected": None, "suspect": False,
            "timeout": True,
            "stage": st.stage if st is not None else 0,
            "known": bool(st is not None and st.known),
            "due": (st.due.isoformat()
                    if st is not None and st.due else None),
            "awards": [],
            "message": "Vaqt tugadi — so'z holati o'zgarmadi, "
                       "u keyinroq yana beriladi."}


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
    mode = item.mode
    if payload.get("timeout") is True:
        out = _timeout(db, s, sess, item, now, payload.get("ms"))
        if out is not None:
            return out
    forms = None
    if mode == "P":
        word = db.query(W).get(item.word_id)
        forms = _gap_forms(word) if word is not None else None
    correct, given_s = _grade(item, payload.get("given"), forms)
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


def _apply_block(db: Session, sess, payload: dict, now: datetime) -> int:
    """Joriy blok javoblarini yozadi ({band?, answers: [{item_id, given,
    ms}]}), javobsiz qolganlari — "Bilmayman". Joriy daraja qaytadi.
    2026-10-16 (review): /next va /finish uchun umumiy."""
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
    return cur


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
    cur = _apply_block(db, sess, payload, now)

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
    tasdiqlangan son, coin va so'z holatiga ta'sir qilmaydi.

    2026-10-16 (review): joriy blokning berilgan javoblari shu yerga
    {session_id, band, answers} bilan keladi va YANGI blok ochilmaydi.
    Avval mijoz erta tugatishda avval /next ga yuborardi — u keyingi
    darajaning 10 ta savolini ochib qo'yar, /finish esa o'quvchi ko'rmagan
    o'sha blokni "Bilmayman" (0%) deb natijaga qo'shardi."""
    s = _student(db, user)
    payload = _body(payload)
    sess = _load_session(db, s, payload, "size_test")
    now = _now()
    old = db.query(ST).filter(ST.session_id == sess.id).first()
    if old is not None:
        return {"done": True, "result": _test_out(old)}
    if payload.get("answers"):
        _check_open(sess, now)
        _apply_block(db, sess, payload, now)
    result = _finish(db, s, sess, now)
    db.commit()
    return {"done": True, "result": result}


# ============================================================ ADMIN ===
# 2026-10-16: asoschi "So'z bilish" bo'limini qaysi filiallarda ochiq
# bo'lishini o'zi boshqaradi ("all" — hammasi, [id...] — tanlanganlar,
# [] — hamma joyda yopiq). Boshqa rollarga 403. Bayroq o'chiq bo'lsa
# ham bu yo'l ishlaydi — aks holda asoschi uni yoqa olmasdi.
def _admin_out(db: Session) -> dict:
    v = flag_value(db)
    words = db.query(func.count(W.id)).filter(*_HAS_UZ).scalar() or 0
    rows = (db.query(models.Branch.id, models.Branch.name)
            .order_by(models.Branch.id).all())
    return {
        "enabled": ALL if v == ALL else sorted(v),
        "branches": [{"id": bid, "name": name,
                      "enabled": v == ALL or bid in v}
                     for bid, name in rows],
        "words": int(words),        # mashqqa tayyor (faol, tarjimali) so'zlar
    }


def _want_flag(db: Session, payload) -> str:
    """So'rovdagi {enabled: "all" | [id...]} -> saqlanadigan qiymat.
    Noma'lum filial, son bo'lmagan qiymat — 400 (jim yutib yuborilmaydi)."""
    hint = "enabled kerak: \"all\" yoki filial id'lari ro'yxati"
    if not isinstance(payload, dict) or "enabled" not in payload:
        raise HTTPException(400, hint)
    want = payload.get("enabled")
    if _is_all(want):
        return ALL
    if not isinstance(want, list):
        raise HTTPException(400, hint)
    ids = set()
    for x in want:
        if isinstance(x, bool):
            raise HTTPException(400, f"Filial id noto'g'ri: {x}")
        if isinstance(x, int):
            ids.add(x)
        elif isinstance(x, str) and x.strip().isdigit():
            ids.add(int(x.strip()))
        else:
            raise HTTPException(400, f"Filial id noto'g'ri: {x}")
    known = {bid for (bid,) in db.query(models.Branch.id)
             .filter(models.Branch.id.in_(ids))} if ids else set()
    bad = sorted(ids - known)
    if bad:
        raise HTTPException(400, f"Filial topilmadi: {bad}")
    return json.dumps(sorted(ids))


def _set_flag(db: Session, value: str, who) -> None:
    row = db.query(models.IntegrationSetting).get(FLAG_KEY)
    if row is None:
        row = models.IntegrationSetting(key=FLAG_KEY)
        db.add(row)
    row.value = value
    row.updated_by = who
    row.updated_at = _now()


@router.get("/api/wordbank/admin")
def wordbank_admin_get(db: Session = Depends(get_db),
                       user=Depends(require_role(roles.FOUNDER))):
    """Qaysi filiallarda ochiq + mashqqa tayyor so'zlar soni."""
    return _admin_out(db)


@router.put("/api/wordbank/admin")
def wordbank_admin_put(payload=Body(default=None),
                       db: Session = Depends(get_db),
                       user=Depends(require_role(roles.FOUNDER))):
    """{enabled: "all" | [filial id]} — bayroqni o'zgartiradi. Har
    o'zgarish auditda (kim, eski va yangi qiymat)."""
    new = _want_flag(db, payload)
    old = _flag_raw(db)
    # 2026-10-16 (review): bayroq hali qo'yilmagan bo'lsa ("" va "[]" bir
    # xil — hamma joyda yopiq) asoschining PUT [] i ham YOZILADI: aks holda
    # qator yo'qligicha qolib, keyingi startda seed_enable_all uni "all" ga
    # aylantirib, asoschining "hamma joyda yopiq" qarorini bosib ketardi.
    changed = not old or parse_flag(old) != parse_flag(new)
    if changed:
        _set_flag(db, new, getattr(user, "full_name", None)
                  or getattr(user, "username", None))
        audit.log(db, user, entity="settings", action="update",
                  entity_id=0, field=FLAG_KEY,
                  old_value=old or "(bo'sh)", new_value=new,
                  note="So'z bilish: yoqilgan filiallar")
        db.commit()
    out = _admin_out(db)
    out["changed"] = changed
    return out


# ================================================= SO'ZLAR FAYLI (SEED) ===
# 2026-10-16: 20 000 so'z (Common 1000 … 20000) api/wordbank_data/
# words.json da — uni scripts/wordbank_merge.py yozadi (tarjima
# partiyalari + mavjud lug'at birlashtiriladi). Qoidalar:
#   * lemma bo'yicha UPSERT; bazadagi so'z HECH QACHON o'chirilmaydi
#     (o'quvchi holati unga bog'langan) va holati (active/disabled)
#     o'zgartirilmaydi — yangi so'z "active" bo'lib kiradi;
#   * skip=true yoki o'zbekcha tarjimasi bo'sh qator yuklanmaydi;
#   * fayl yo'q bo'lsa — jim o'tadi (belgi qo'yilmaydi);
#   * belgi kaliti FAYL MAZMUNIDAN (sha256): fayl yangilansa seed o'zi
#     qayta ishlaydi (vocab_extra_seed saboqi), o'zgarmasa — bir marta;
#   * bir sovuq startda WORDS_BUDGET tagacha yangi qator, qolgani
#     keyingi startda (Vercel 30 s chegarasi); belgi faqat oxirida.
_HERE = os.path.dirname(os.path.abspath(__file__))
WORDS_FILE = os.path.join(_HERE, "wordbank_data", "words.json")
SEED_WORDS = "wordbank_words_v1"
SEED_ENABLE_ALL = "wordbank_enable_all_v1"
WORDS_BUDGET = 5000
_SEED_LOCK_ID = 20261016       # pg_advisory qulf kaliti (parallel startlar)
_WORD_FIELDS = ("rank", "band", "pos", "uz_primary", "uz_alt",
                "example_en", "example_uz")


def words_file() -> str:
    """words.json yo'li; WORDBANK_WORDS_FILE (testlar uchun) ustun."""
    return os.environ.get("WORDBANK_WORDS_FILE") or WORDS_FILE


def _read_file(path):
    try:
        with open(path, "rb") as f:
            return f.read()
    except OSError:
        return None


def _words_key(raw: bytes) -> str:
    return f"{SEED_WORDS}:{hashlib.sha256(raw).hexdigest()[:12]}"


def _try_lock(db: Session) -> bool:
    """Bir vaqtda uyg'ongan bir nechta instansiyadan faqat bittasi
    yozsin (vocab_extra_seed._try_lock bilan bir xil). Qulf tranzaksiya
    bilan o'zi bo'shaydi. SQLite'da shart emas."""
    try:
        if db.bind.dialect.name != "postgresql":
            return True
        return bool(db.execute(
            sa_text("SELECT pg_try_advisory_xact_lock(:k)"),
            {"k": _SEED_LOCK_ID}).scalar())
    except Exception:
        return True


def _txt(v):
    if isinstance(v, (list, tuple)):          # pos: ["NOUN", "VERB"] -> NOUN
        v = next((x for x in v if isinstance(x, str) and x.strip()), None)
    if v is None or isinstance(v, (dict, bool)):
        return None
    s = str(v).strip()
    return s or None


def _entries(data) -> list:
    """Fayl ko'rinishlari: {"words": [...]}, [...] yoki {lemma: {...}}."""
    if isinstance(data, dict) and isinstance(data.get("words"), list):
        return data["words"]
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        out = []
        for lemma, e in data.items():
            if isinstance(e, dict):
                e = dict(e)
                e.setdefault("lemma", lemma)
                out.append(e)
        return out
    return []


def parse_words(data) -> tuple:
    """(qatorlar rank tartibida, tashlab ketilganlar soni). Yuklanmaydi:
    skip=true, o'zbekcha tarjimasiz, rank/daraja/lemma noto'g'ri. Bir
    lemma ikki marta kelsa — oxirgisi."""
    rows: dict = {}
    skipped = 0
    for e in _entries(data):
        if not isinstance(e, dict) or e.get("skip"):
            skipped += 1
            continue
        lemma, uz = _txt(e.get("lemma")), _txt(e.get("uz_primary"))
        rk, bd = e.get("rank"), e.get("band")
        if isinstance(rk, bool) or isinstance(bd, bool):
            skipped += 1
            continue
        try:
            rank, band = int(rk), int(bd)
        except (TypeError, ValueError):
            skipped += 1
            continue
        if not lemma or not uz or rank <= 0 or not 1 <= band <= WC.BANDS:
            skipped += 1
            continue
        alt = e.get("uz_alt")
        if isinstance(alt, str):
            alt = [alt]
        alt = ([a.strip() for a in alt if isinstance(a, str) and a.strip()]
               if isinstance(alt, list) else [])
        rows[lemma] = {
            "lemma": lemma, "rank": rank, "band": band,
            "pos": _txt(e.get("pos")), "uz_primary": uz,
            "uz_alt": json.dumps(alt, ensure_ascii=False),
            "example_en": _txt(e.get("example_en")),
            "example_uz": _txt(e.get("example_uz")),
        }
    return sorted(rows.values(), key=lambda r: r["rank"]), skipped


def _plan(have: dict, rows: list) -> tuple:
    """Qaysi qatorlarni yozish mumkin (rank UNIQUE). Fayldan tashqari
    eski so'z egallagan rank'ga yangi so'z QO'YILMAYDI (eski so'z
    o'chirilmaydi) — fayldagi qator o'tkazib yuboriladi; agar u bazada
    bo'lsa, o'z eski joyida qoladi ("qotgan"). Fayl ichida bir rank ikki
    marta kelsa — birinchisi.

    2026-10-16 (review): CHIZIQLI ishchi navbat. Avval har yangi "qotgan"
    so'zda butun ro'yxat qaytadan aylanardi — rank'lar bittaga surilgan
    20 000 qatorli faylda bu ~1 daqiqa (O(n²)): Vercel 30 s chegarasidan
    oshib, belgi qo'yilmagani uchun har sovuq startda takrorlanardi. Endi
    qotgan so'z faqat o'zining bazadagi rank'ini xohlagan BITTA qatorni
    tekshiradi. Qoida o'sha; navbat tartibi natijaga ta'sir qilmaydi."""
    want = {}                      # rank -> fayl qatori
    lost = []                      # fayl ichida rank takrori (ikkinchisi)
    for r in rows:
        if r["rank"] in want:
            lost.append(r["lemma"])
        else:
            want[r["rank"]] = r
    file_rank = {r["lemma"]: r["rank"] for r in rows}
    queue = [lem for lem in have if lem not in file_rank]
    queue += [lem for lem in lost if lem in have]
    fixed = set()
    while queue:
        lem = queue.pop()
        if lem in fixed:
            continue
        fixed.add(lem)
        fr = file_rank.get(lem)
        if fr is not None and want.get(fr, {}).get("lemma") == lem:
            del want[fr]               # o'zi qotdi — fayldagi joyini olmaydi
        k = have[lem]["rank"]
        r = want.get(k)
        if r is not None and r["lemma"] != lem:
            del want[k]                # bazadagi egasi turibdi
            if r["lemma"] in have:
                queue.append(r["lemma"])
    accepted = [r for r in rows if want.get(r["rank"]) is r]
    ok = {r["lemma"] for r in accepted}
    return accepted, [r["lemma"] for r in rows if r["lemma"] not in ok]


def _upsert(db: Session, rows: list, budget) -> dict:
    cols = (W.id, W.lemma) + tuple(getattr(W, k) for k in _WORD_FIELDS)
    have = {}
    for t in db.query(*cols):
        have[t[1]] = dict(zip(("id",) + _WORD_FIELDS,
                              (t[0],) + tuple(t[2:])))
    accepted, conflicts = _plan(have, rows)
    inserts, updates = [], []
    for r in accepted:
        old = have.get(r["lemma"])
        if old is None:
            inserts.append(r)
        elif any(old[k] != r[k] for k in _WORD_FIELDS):
            updates.append(dict(r, id=old["id"]))
    # 2026-10-16 (review): rank'i qotib qolgan, lekin faylda bor so'z —
    # rank va daraja bazadagidek qoladi, tarjima va misollar esa fayldan
    # yangilanadi (avval bunday so'zning tuzatishlari umuman tushmasdi).
    ok = {r["lemma"] for r in accepted}
    for r in rows:
        old = have.get(r["lemma"])
        if old is None or r["lemma"] in ok:
            continue
        fr = dict(r, rank=old["rank"], band=old["band"])
        if any(old[k] != fr[k] for k in _WORD_FIELDS):
            updates.append(dict(fr, id=old["id"]))
    # rank almashadigan so'zlar avval vaqtincha manfiy rank'ga (-id)
    # o'tkaziladi — aks holda almashuvda UNIQUE(rank) yiqiladi.
    moving = [u for u in updates if have[u["lemma"]]["rank"] != u["rank"]]
    if moving:
        db.execute(sa_update(W), [{"id": u["id"], "rank": -u["id"]}
                                  for u in moving])
    if updates:
        db.execute(sa_update(W), [{k: u[k] for k in ("id",) + _WORD_FIELDS}
                                  for u in updates])
    batch = inserts if budget is None else inserts[:max(0, int(budget))]
    if batch:
        db.execute(sa_insert(W), [dict(r, status="active") for r in batch])
    return {"inserted": len(batch), "updated": len(updates),
            "left": len(inserts) - len(batch), "conflicts": len(conflicts),
            "conflict_sample": conflicts[:10],
            "finished": len(batch) == len(inserts)}


def load_words(db: Session, path=None, budget=WORDS_BUDGET):
    """words.json -> wordbank_words (idempotent). Qaytaradi:
    None — bu fayl allaqachon to'liq yuklangan; {"missing": True} —
    fayl yo'q (hech narsa qilinmadi); aks holda hisobot."""
    from common import _seed_done, _seed_mark
    path = path or words_file()
    raw = _read_file(path)
    if raw is None:
        return {"missing": True}
    key = _words_key(raw)
    if _seed_done(db, key):
        return None
    if not _try_lock(db):
        return {"locked": True, "finished": False}
    try:
        data = json.loads(raw.decode("utf-8-sig"))
    except ValueError as e:
        db.rollback()               # qulfni bo'shatamiz
        print(f"[wordbank] words.json o'qilmadi: {e}", flush=True)
        return {"error": "json", "finished": False}
    rows, skipped = parse_words(data)
    try:
        res = _upsert(db, rows, budget)
        db.commit()
    except IntegrityError as e:
        # parallel start boshqa instansiyada yozdi — keyingi startda davom
        db.rollback()
        print(f"[wordbank] so'zlar yozilmadi (to'qnashuv): {e}", flush=True)
        return {"error": "conflict", "finished": False}
    res["skipped"] = skipped
    res["key"] = key
    if res["finished"]:
        _seed_mark(db, key)
    print(f"[wordbank] so'zlar yuklandi: {res}", flush=True)
    return res


def words_pending(db: Session, path=None) -> bool:
    """words.json bor, lekin hali to'liq yuklanmagan."""
    from common import _seed_done
    raw = _read_file(path or words_file())
    return raw is not None and not _seed_done(db, _words_key(raw))


def seed_enable_all(db: Session, path=None):
    """BIR MARTALIK (Jahongir, 2026-10-16: "barcha filiallar"): bayroq
    hali qo'yilmagan bo'lsa (yo'q yoki bo'sh) — "all". Asoschi pilot
    ro'yxatini allaqachon qo'ygan bo'lsa — tegilmaydi. So'zlar to'liq
    yuklanmaguncha (yoki mashqqa tayyor so'z yo'q bo'lsa, yoki — 2026-10-16
    review — 1-daraja to'liq bo'lmasa) kutadi — bo'sh bo'limni hammaga
    ochib qo'ymaslik uchun; belgi qo'yilmaydi, keyingi startda qayta
    tekshiriladi. Asoschi PUT qilgan bo'lsa (hatto [] ham) bayroq qatori
    bor — tegilmaydi. Qaytarish: PUT /api/wordbank/admin."""
    from common import _seed_done, _seed_mark
    if _seed_done(db, SEED_ENABLE_ALL):
        return None
    if words_pending(db, path):
        return "pending"
    if db.query(W.id).filter(*_HAS_UZ).first() is None:
        return "no-words"
    # 2026-10-16 (review): 1-daraja to'liq bo'lmaguncha ochilmaydi — bitta
    # tarjimali so'z bilan ham "all" bo'lib, chala bo'lim hammaga ochilardi.
    if 1 not in _ready_bands(db):
        return "not-ready"
    old = _flag_raw(db)
    out = "kept"
    if not old:
        _set_flag(db, ALL, "Tizim")
        audit.log(db, None, entity="settings", action="update", entity_id=0,
                  field=FLAG_KEY, old_value="(bo'sh)", new_value=ALL,
                  note="So'z bilish: barcha filiallar uchun ochildi "
                       "(asoschi so'rovi, 2026-10-16)")
        try:
            db.commit()
        except IntegrityError:
            db.rollback()           # parallel start qo'ydi — keyingi startda
            return "conflict"
        out = "enabled"
    _seed_mark(db, SEED_ENABLE_ALL)
    return out


def seed_startup(db: Session, path=None) -> dict:
    """main.py startda chaqiradi: avval so'zlar, keyin bir martalik
    "hammaga ochish". Xato boshqa seedlarni to'xtatmaydi."""
    out = {}
    try:
        out["words"] = load_words(db, path)
    except Exception as e:  # noqa: BLE001
        db.rollback()
        out["words"] = {"error": str(e)[:200]}
    try:
        out["enable_all"] = seed_enable_all(db, path)
    except Exception as e:  # noqa: BLE001
        db.rollback()
        out["enable_all"] = f"error: {str(e)[:200]}"
    # 2026-10-17: Telegram kanalidagi natijalar -> CRM sertifikatlari
    # (wordbank_certs.seed_telegram; bir martalik, fayl mazmuni bo'yicha)
    try:
        import wordbank_certs as WCERT
        out["tg_certs"] = WCERT.seed_telegram(db)
    except Exception as e:  # noqa: BLE001
        db.rollback()
        out["tg_certs"] = {"error": str(e)[:200]}
    return out


# ---------------------------------------------------------------- holat ---
# 2026-10-17, Jahongir: "o'zing tekshir va yuklanmagan bo'lsa tugat".
# So'zlar faqat sovuq startda (WORDS_BUDGET tadan) yuklanardi, Vercel
# instansiyalari esa soatlab yashaydi — yuklash to'xtab qolishi mumkin,
# start loglari ham yo'qolishi mumkin (mock-strict-mode saboqi). Shu
# sababli ochiq holat yo'li:
#   * faqat sonlar — so'zlar, tayyor darajalar, bayroq turi; shaxsiy
#     ma'lumot ham, so'zlarning o'zi ham yo'q;
#   * so'zlar hali to'liq bo'lmasa, chaqiruv seed_startup bilan AYNAN bir
#     qadamni bajaradi (budjet, pg qulfi, idempotent upsert — jami yozuv
#     fayldagi qatorlar bilan cheklangan, qator o'chirilmaydi), keyin bir
#     martalik "hammaga ochish"ni tekshiradi (asoschi qarori bosilmaydi);
#   * ikkalasi tugagach jarayon xotirasida eslanadi — faylni qayta
#     o'qimaydi, faqat ikki COUNT so'rovi qoladi.
_STATUS_DONE = False


def _status_flag(db: Session) -> str:
    v = parse_flag(_flag_raw(db))
    if v == ALL:
        return ALL
    return f"{len(v)} filial" if v else "off"


@router.get("/api/wordbank/status")
def wordbank_status(db: Session = Depends(get_db)):
    global _STATUS_DONE
    from common import _seed_done
    step = None
    if not _STATUS_DONE:
        step = seed_startup(db)
        if (not words_pending(db)
                and _seed_done(db, SEED_ENABLE_ALL)):
            _STATUS_DONE = True
    words = db.query(func.count(W.id)).filter(*_HAS_UZ).scalar() or 0
    try:
        import wordbank_certs as WCERT
        tg = WCERT.tg_report(db)      # faqat sonlar va post raqamlari
    except Exception:  # noqa: BLE001
        tg = None
    return {
        "words": int(words),
        "bands_ready": len(_ready_bands(db)),
        "words_pending": not _STATUS_DONE and words_pending(db),
        "enabled": _status_flag(db),
        "done": _STATUS_DONE,
        "step": step,
        "tg_certs": tg,
    }
