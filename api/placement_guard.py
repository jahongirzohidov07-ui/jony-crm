# -*- coding: utf-8 -*-
"""Diagnostika testlari: "Bilmayman" va "juda tez" himoyasi (2026-10-22).

Jahongir: "diagnostik testda hech narsani bilmay taxminan bosib
tashlaydiganlarning darajasi baland chiqyapti — variantlar sonini 5 taga
ko'tarib, 6-variantga 'Bilmayman' qo'shish kerak; savolni o'qimay bosib
tashlaydiganlarni to'g'ri bossa ham noto'g'ri ko'rsatishi kerak".

Uchala test shu bitta modulni ishlatadi: ingliz adaptiv diagnostikasi
(entry.py, _PT_*), nemis (german_placement.py) va rus
(russian_placement.py) kirish testlari.

QOIDALAR
  * "Bilmayman" — javob sifatida choice = -1 keladi. Har qanday hisobda
    XATO (adaptiv zina ham xatodagidek pastga tushadi), lekin alohida
    sanaladi. Tez bosilgan "Bilmayman" "juda tez" emas: bilmasligini
    halol aytgan odamni jazolamaymiz — biz aynan shuni istaymiz.
  * "Juda tez" — savol berilgandan min_ms o'tmasdan kelgan haqiqiy
    variant. Kalitga mos bo'lsa ham XATO. Vaqtni FAQAT server o'lchaydi:
    savol berilgan payt serverda (yoki server imzolagan tokenda)
    saqlanadi, javob kelgan payt — server soati. Mijoz yuborgan vaqtga
    hech qachon ishonilmaydi.
  * min_ms odam o'qishi kerak bo'lgan matn hajmidan chiqadi; sonlar
    roles.PLACEMENT_MIN_* da.
  * Test topshiruvchiga "tez bosdingiz" degan hech narsa aytilmaydi:
    public() natijadan "juda tez" bilan bog'liq hamma narsani olib
    tashlaydi. Bu ma'lumot faqat xodimlar uchun.
  * Savol berilgan vaqt saqlanmagan eski sessiyalarda (deploydan oldin
    boshlangan) "juda tez" qoidasi qo'llanmaydi.

NEMIS/RUS TESTI HOLATI
  Bu ikki testda alohida sessiya jadvali yo'q (natija faqat oxirida
  yoziladi). Shuning uchun holat — joriy savol, u berilgan server vaqti,
  shu paytgacha javoblar va "juda tez" belgilari — SHIFRLANGAN va
  IMZOLANGAN "state" token ichida mijozda yuradi (SeqTest). Mijoz uni
  o'qiy olmaydi ham, o'zgartira olmaydi ham; yangi jadval yoki ustun
  kerak emas.
"""
import base64
import hashlib
import hmac
import json
import os
import time

from fastapi import HTTPException

import roles

IDK = -1                                   # "Bilmayman" javobi
IDK_LABEL = roles.PLACEMENT_IDK_LABEL
GUESS_LABEL = roles.PLACEMENT_GUESS_LABEL

# Test topshiruvchiga ko'rsatilmaydigan kalitlar (faqat xodimlar uchun).
PRIVATE_KEYS = frozenset({"fast", "fast_ids", "fast_pct", "guess_warning",
                          "guess_label", "guard_text", "timed"})


def now_ms() -> int:
    """Server soati, millisekundda. Testlar shu funksiyani almashtiradi."""
    return int(time.time() * 1000)


# ---- min_ms hisoblari ----------------------------------------------
def _clamp(lo, hi, v) -> int:
    return int(max(lo, min(hi, v)))


def chars(*parts) -> int:
    """Matn bo'laklarining umumiy uzunligi (ro'yxatlar ichiga ham kiradi)."""
    n = 0
    for p in parts:
        if p is None:
            continue
        if isinstance(p, (list, tuple)):
            n += chars(*p)
        else:
            n += len(str(p))
    return n


def single_min_ms(text, options) -> int:
    """Bitta savol: clamp(700 + 7 * belgilar, 1500, 5000) — sonlar
    roles.PLACEMENT_MIN_* da (2026-10-22 yumshatilgan, sababi o'sha yerda).
    Belgilar = savol matni + ko'rsatilgan HAMMA haqiqiy variant."""
    return _clamp(roles.PLACEMENT_MIN_SINGLE_FLOOR_MS,
                  roles.PLACEMENT_MIN_SINGLE_CEIL_MS,
                  roles.PLACEMENT_MIN_BASE_MS
                  + roles.PLACEMENT_MIN_PER_CHAR_MS * chars(text, options))


def passage_min_ms(text, options, passage) -> int:
    """Matnli ekrandagi BIRINCHI javob: matnni ham o'qish kerak.
    clamp(700 + 7 * savol_va_variantlar + 12 * matn, 3000, 20000)."""
    return _clamp(roles.PLACEMENT_MIN_PASSAGE_FLOOR_MS,
                  roles.PLACEMENT_MIN_PASSAGE_CEIL_MS,
                  roles.PLACEMENT_MIN_BASE_MS
                  + roles.PLACEMENT_MIN_PER_CHAR_MS * chars(text, options)
                  + roles.PLACEMENT_MIN_PASSAGE_PER_CHAR_MS * chars(passage))


def clip_ms(item):
    """Listening yozuvining davomiyligi (ms). Bankda bo'lsa — o'sha
    (duration_ms / clip_ms ms da, duration / audio_secs soniyada).
    Bo'lmasa — matndan taxmin: 2.5 so'z/soniya, ovoz tezligi (rate)
    hisobga olinadi. Hech biri bo'lmasa — None."""
    for key, mul in (("duration_ms", 1), ("clip_ms", 1),
                     ("duration", 1000), ("audio_secs", 1000)):
        try:
            v = float(item.get(key))
        except (TypeError, ValueError):
            continue
        if v > 0:
            return int(v * mul)
    words = len(str(item.get("script") or "").split())
    if not words:
        return None
    try:
        rate = float(item.get("rate") or 1.0)
    except (TypeError, ValueError):
        rate = 1.0
    rate = max(0.5, min(2.0, rate))
    return int(words / (roles.PLACEMENT_MIN_SPEECH_WPS * rate) * 1000)


def listening_min_ms(item, options) -> int:
    """Listening: bitta savol qoidasi VA yozuvning kamida yarmi
    (roles.PLACEMENT_MIN_CLIP_SHARE)."""
    base = single_min_ms(item.get("q"), options)
    clip = clip_ms(item)
    if clip:
        return max(base, int(clip * roles.PLACEMENT_MIN_CLIP_SHARE))
    return base


def vocab_screen_min_ms(def_texts, words) -> int:
    """Lug'at ekrani (bir nechta ta'rif BIRDAN yuboriladi): har ta'rifga
    bitta savol qoidasi (ta'rif + so'zlar ro'yxati), yig'indisi, 10 s dan
    oshmaydi (roles.PLACEMENT_MIN_SCREEN_CEIL_MS)."""
    total = sum(single_min_ms(d, words) for d in def_texts)
    return min(roles.PLACEMENT_MIN_SCREEN_CEIL_MS, total)


def cap(min_ms, limit_secs) -> int:
    """Minimum savolga berilgan vaqtning 60 foizidan oshmasin."""
    try:
        limit = float(limit_secs or 0)
    except (TypeError, ValueError):
        limit = 0
    if limit > 0:
        return int(min(min_ms, limit * 1000 * roles.PLACEMENT_MIN_LIMIT_SHARE))
    return int(min_ms)


def is_idk(choice) -> bool:
    return type(choice) is int and choice == IDK


def is_real_choice(choice, n) -> bool:
    """Haqiqiy variant tanlanganmi (bool emas, butun son, chegarada)."""
    return type(choice) is int and 0 <= choice < int(n)


def is_fast(elapsed_ms, min_ms) -> bool:
    """Server vaqti yo'q (eski sessiya) — hech qachon tez emas."""
    return elapsed_ms is not None and elapsed_ms < min_ms


# ---- Hisobot --------------------------------------------------------
def guess_warning(fast, total) -> bool:
    """Javoblarning kamida 30 foizi juda tez — taxminan bosilgan."""
    fast, total = int(fast or 0), int(total or 0)
    return total > 0 and fast > 0 and fast * 100 >= roles.PLACEMENT_GUESS_WARN_PCT * total


def guard_text(idk, fast, warning=False) -> str:
    """Xodimlar uchun qisqa satr: "Bilmayman: 3 · Juda tez: 7".
    None — o'lchanmagan (deploydan oldingi sessiya): "—"."""
    def n(v):
        return "—" if v is None else int(v or 0)
    s = f"{IDK_LABEL}: {n(idk)} · Juda tez: {n(fast)}"
    return s + (f" · {GUESS_LABEL}" if warning else "")


def summary(idk, fast, total) -> dict:
    """Natijaga qo'shiladigan umumiy hisob (xodimlar uchun)."""
    warn = guess_warning(fast, total)
    return {"idk": int(idk or 0), "fast": int(fast or 0),
            "guess_warning": warn,
            "guess_label": GUESS_LABEL if warn else None,
            "guard_text": guard_text(idk, fast, warn)}


def untimed(result: dict) -> dict:
    """Vaqt o'lchanmagan natija (nemis/rus eski sahifasidan state'siz
    yuborilgan yoki deploydan oldingi yozuv): "juda tez" soni 0 emas,
    NOMA'LUM — None ("—"), ogohlantirish yo'q, timed=false. 0 desak
    natija "toza" (tez javob yo'q) bo'lib ko'rinardi (2026-10-22)."""
    result.update(timed=False, fast=None, guess_warning=False,
                  guess_label=None, guard_text=guard_text(result.get("idk"), None))
    for key in ("blocks", "skills"):
        for b in result.get(key) or []:
            if isinstance(b, dict):
                b["fast"] = None
    return result


LEGACY_CLOSED_TEXT = ("Test sahifasi eskirgan. Sahifani yangilab, testni "
                      "qaytadan boshlang.")


def legacy_submit_open(today=None) -> bool:
    """Nemis/rus: state'siz (eski sahifa) yuborish hali qabul qilinadimi.
    roles.PLACEMENT_LEGACY_SUBMIT_UNTIL kuni ham ochiq (UTC sana)."""
    import datetime as _dt
    try:
        until = _dt.date.fromisoformat(str(roles.PLACEMENT_LEGACY_SUBMIT_UNTIL))
    except (TypeError, ValueError):
        return False
    return (today or _dt.datetime.utcnow().date()) <= until


def public(obj):
    """Test topshiruvchiga ketadigan nusxa: "juda tez" bilan bog'liq
    hamma kalit olib tashlanadi (ichma-ich lug'at va ro'yxatlarda ham)."""
    if isinstance(obj, dict):
        return {k: public(v) for k, v in obj.items() if k not in PRIVATE_KEYS}
    if isinstance(obj, list):
        return [public(v) for v in obj]
    return obj


# ---- Shifrlangan va imzolangan holat --------------------------------
_VER = 1
_NONCE = 12
_TAG = 16
# 2026-10-22: shifrlanadigan matn shu o'lchamga (uzunroq bo'lsa — uning
# karralisiga) bo'sh joy bilan to'ldiriladi. Shunda token uzunligi butun
# test davomida bir xil va ichidagi hech narsani (masalan, "juda tez"
# belgilari yoki javoblar sonini) oshkor qilmaydi. 48 savollik holat
# ~300 bayt — 512 ga sig'adi. json.loads oxiridagi bo'sh joyni o'qiydi.
_PAD = 512


def _keys():
    import auth  # kalit — JWT bilan bir xil manba (JONY_CRM_SECRET)
    sec = str(getattr(auth, "SECRET_KEY", "") or "").encode("utf-8")
    return (hashlib.sha256(b"placement-guard/enc|" + sec).digest(),
            hashlib.sha256(b"placement-guard/mac|" + sec).digest())


def _stream(key: bytes, nonce: bytes, n: int) -> bytes:
    out = bytearray()
    ctr = 0
    while len(out) < n:
        out += hmac.new(key, nonce + ctr.to_bytes(4, "big"),
                        hashlib.sha256).digest()
        ctr += 1
    return bytes(out[:n])


def _xor(a: bytes, b: bytes) -> bytes:
    return bytes(x ^ y for x, y in zip(a, b))


def seal(kind: str, data: dict) -> str:
    """Holatni shifrlaydi (HMAC-SHA256 oqimi) va imzolaydi."""
    ek, mk = _keys()
    raw = json.dumps(dict(data, v=_VER), separators=(",", ":")).encode("utf-8")
    raw += b" " * (-len(raw) % _PAD)          # qat'iy uzunlik (yuqorida)
    nonce = os.urandom(_NONCE)
    ct = _xor(raw, _stream(ek, nonce, len(raw)))
    tag = hmac.new(mk, kind.encode() + b"|" + nonce + ct,
                   hashlib.sha256).digest()[:_TAG]
    return base64.urlsafe_b64encode(nonce + ct + tag).decode().rstrip("=")


def unseal(kind: str, token):
    """Imzo to'g'ri bo'lsa holat (dict), aks holda None."""
    try:
        t = str(token or "")
        blob = base64.urlsafe_b64decode(t + "=" * (-len(t) % 4))
    except (ValueError, TypeError):
        return None
    if len(blob) < _NONCE + _TAG + 2:
        return None
    nonce, ct, tag = blob[:_NONCE], blob[_NONCE:-_TAG], blob[-_TAG:]
    ek, mk = _keys()
    want = hmac.new(mk, kind.encode() + b"|" + nonce + ct,
                    hashlib.sha256).digest()[:_TAG]
    if not hmac.compare_digest(tag, want):
        return None
    try:
        data = json.loads(_xor(ct, _stream(ek, nonce, len(ct))).decode("utf-8"))
    except (ValueError, UnicodeDecodeError):
        return None
    return data if isinstance(data, dict) and data.get("v") == _VER else None


# =====================================================================
#  KETMA-KET TEST (nemis va rus kirish testlari)
#
#  Savollar bankdagi tartibda BITTADAN beriladi va faqat oldinga
#  yuriladi ("Oldingi" yo'q): har savolning vaqti server bergan paytdan
#  o'lchanadi. Variantlar aralashtirilmaydi (bugungidek), "Bilmayman"ni
#  sahifa o'zi oxirgi tugma qilib qo'shadi ("idk": true).
#
#  /start    {attempt_id}                    -> 1-savol + state
#  /answer   {attempt_id, state, qid, choice} -> keyingi savol + yangi state
#  /current  {attempt_id, state}              -> joriy savol (vaqt qayta
#                                               boshlanmaydi)
#  Yakuniy yuborishda state beriladi — javoblar va "juda tez" belgilari
#  shu tokendan olinadi, mijoz yuborgan javoblardan emas.
# =====================================================================
class SeqTest:
    def __init__(self, kind: str, bank: list):
        self.kind = kind
        self.bank = bank

    # -- savol va uning minimumi --
    def min_ms(self, i: int) -> int:
        """Nemis/rus — BITTA SAVOL qoidasi (clamp 1500..5000). Qisqa matn
        (60–120 belgi) savol bilan birinchi marta ko'rsatilsa, u ham
        o'qiladigan matnga qo'shiladi; o'sha matndagi keyingi savolda —
        faqat savol va variantlar. Ingliz readingidagi matnli ekran
        qoidasi (kamida 3 s) bu yerda ishlatilmaydi: rp-7 kabi 62
        belgilik matnga 4 s talab qilish ortiqcha edi va bilimdon
        o'quvchini 1-blokda yiqitardi (2026-10-22, ko'rib chiqish)."""
        q = self.bank[i]
        prev = self.bank[i - 1] if i > 0 else None
        text = q.get("text")
        if text and not (prev is not None and prev.get("text") == text):
            # matn bu savol bilan birinchi marta ko'rsatilyapti
            return single_min_ms([text, q.get("prompt")], q.get("options"))
        return single_min_ms(q.get("prompt"), q.get("options"))

    def question(self, i: int):
        if i >= len(self.bank):
            return None
        q = self.bank[i]
        out = {k: v for k, v in q.items() if k != "answer"}
        out["options"] = list(q.get("options") or [])
        out.update(index=i, no=i + 1, total=len(self.bank), idk=True)
        return out

    def _out(self, st: dict, token: str, **extra) -> dict:
        i = int(st.get("i") or 0)
        out = {"state": token, "question": self.question(i),
               "done": i >= len(self.bank),
               "answered": len(st.get("c") or []), "total": len(self.bank)}
        out.update(extra)
        return out

    def _load(self, token, attempt_id=None) -> dict:
        st = unseal(self.kind, token)
        if st is None:
            raise HTTPException(400, "Test holati buzilgan. Sahifani yangilab, "
                                     "testni qaytadan boshlang.")
        if attempt_id is not None and str(attempt_id) != str(st.get("a")):
            raise HTTPException(409, "Bu holat boshqa testga tegishli. "
                                     "Sahifani yangilang.")
        return st

    # -- "juda tez" belgilari --
    # f — bank uzunligidagi "0"/"1" qatori. Ro'yxat bo'lsa ("juda tez"
    # indekslari) token har tez javobda uzunroq bo'lib, shifrlangan
    # bo'lsa ham UZUNLIGI qaysi javob tez deb belgilanganini aytib
    # qo'yardi. Qat'iy uzunlikdagi qator buni yashiradi.
    def _fbits(self, f) -> str:
        n = len(self.bank)
        if isinstance(f, str) and len(f) == n and set(f) <= {"0", "1"}:
            return f
        bits = ["0"] * n
        for k in (f if isinstance(f, list) else []):
            if isinstance(k, int) and 0 <= k < n:
                bits[k] = "1"
        return "".join(bits)

    # -- endpointlar mantiqi --
    def start(self, attempt_id) -> dict:
        t = now_ms()
        st = {"a": str(attempt_id), "i": 0, "s": t, "t0": t, "c": [],
              "f": self._fbits(None)}
        return self._out(st, seal(self.kind, st))

    def current(self, token, attempt_id=None) -> dict:
        st = self._load(token, attempt_id)
        return self._out(st, token)

    def answer(self, token, qid, choice, attempt_id=None) -> dict:
        st = self._load(token, attempt_id)
        i = int(st.get("i") or 0)
        if i >= len(self.bank):
            return self._out(st, token)
        q = self.bank[i]
        if str(qid) != str(q["id"]):
            # eski savolga javob — joriy savolni o'zgarishsiz qaytaramiz
            return self._out(st, token, stale=True)
        n = len(q.get("options") or [])
        if not (is_idk(choice) or is_real_choice(choice, n)):
            raise HTTPException(422, "Javobni tanlang")
        served = st.get("s")
        elapsed = (now_ms() - int(served)) if isinstance(served, int) else None
        fast = is_real_choice(choice, n) and is_fast(elapsed, self.min_ms(i))
        c = list(st.get("c") or [])
        f = self._fbits(st.get("f"))
        c.append(int(choice))
        if fast:
            f = f[:i] + "1" + f[i + 1:]
        nst = dict(st, i=i + 1, s=now_ms(), c=c, f=f)
        return self._out(nst, seal(self.kind, nst))

    def final(self, token, attempt_id):
        """(javoblar {qid: choice}, juda tez qid lar to'plami)."""
        st = self._load(token, attempt_id)
        c = list(st.get("c") or [])
        if int(st.get("i") or 0) < len(self.bank) or len(c) < len(self.bank):
            raise HTTPException(422, f"{len(self.bank)} ta savolga javob bering")
        answers = {q["id"]: int(c[k]) for k, q in enumerate(self.bank)}
        f = self._fbits(st.get("f"))
        fast = {q["id"] for k, q in enumerate(self.bank) if f[k] == "1"}
        return answers, fast
