# -*- coding: utf-8 -*-
"""DIAGNOSTIKA: "BILMAYMAN" VA "JUDA TEZ" (2026-10-22).

Jahongir: "diagnostik testda hech narsani bilmay taxminan bosib
tashlaydiganlarning darajasi baland chiqyapti — variantlar sonini 5 taga
ko'tarib, 6-variantga 'Bilmayman' qo'shish kerak; savolni o'qimay bosib
tashlaydiganlarni to'g'ri bossa ham noto'g'ri ko'rsatishi kerak".

Tekshiriladi (ingliz adaptiv testi, nemis va rus kirish testlari):
  1. 5 variantli savol (banklar placement_options_v2.json va nemis/rus
     bank JSON laridan) — 5 ta haqiqiy variant va "idk": true beriladi,
     "Bilmayman" variantlar ichida emas, javob kaliti hech qayerda yo'q.
  2. "Bilmayman" (-1) adaptiv zinani XATO javobdek pastga tushiradi.
  3. min_ms dan tez kelgan TO'G'RI javob — xato va "juda tez";
     min_ms dan keyin — to'g'ri. Tez-to'g'ri javobda zina joyida qoladi
     (held): kuchli o'quvchi oson savollarni tez bosib A1 ga sirg'almaydi,
     tasodifiy taxminchi esa baribir A1 (3b).
  4. Reading: matnli ekrandagi 1-javob matn minimumini kutadi,
     keyingisi ketma-ket qo'shiladi.
  5. Listening: yozuvning kamida yarmi (yoki bankdagi davomiylik).
  6. Lug'at: ekran minimumi (ta'riflar yig'indisi, 10 s gacha).
  Minimumlar roles.PLACEMENT_MIN_* dan olinadi (2026-10-22 yumshatilgan:
  grammatika savoli ~1.5 s, 5 s dan oshmaydi).
  7. Eski sessiya (savol berilgan vaqt saqlanmagan) — xatosiz tugaydi,
     "juda tez" belgisi qo'yilmaydi, eski javoblar o'zgarmaydi.
  8. Natija, eksport, lid izohi — idk / fast / guess_warning; test
     topshiruvchiga ketadigan natijada "juda tez" haqida hech narsa yo'q.
  9. Nemis va rus testi: savollar bittadan, shifrlangan state, eski
     (answers bilan) yuborish ham ishlaydi.

Server soati soxta soat bilan almashtiriladi: ingliz testida _pt_now
(entry.py boshqa nom bilan ham yuklangan bo'lishi mumkin — sys.modules
bo'ylab hamma nusxada), nemis/rus testida placement_guard.now_ms.
"""
import base64
import datetime
import json
import os
import sys
import tempfile
import uuid
from datetime import timedelta

_DB = os.path.join(tempfile.gettempdir(), "pt_antiguess_test.db")
os.environ["DATABASE_URL"] = "sqlite:///" + _DB.replace("\\", "/")
if os.path.exists(_DB):
    os.remove(_DB)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient          # noqa: E402
import main, models, roles                          # noqa: F401,E402
import entry as E                                   # noqa: E402
import placement_guard as PG                        # noqa: E402
import german_placement as G                        # noqa: E402
import russian_placement as R                       # noqa: E402
from database import SessionLocal                   # noqa: E402
from auth import hash_password                      # noqa: E402

client = TestClient(E.app)
fails = []
# State'siz (eski sahifa) yuborish faqat PLACEMENT_LEGACY_SUBMIT_UNTIL gacha
# ochiq. Test sanadan qat'i nazar ishlasin: muddat ataylab uzaytiriladi,
# yopilishi alohida (haqiqiy sana bilan) tekshiriladi.
REAL_LEGACY_UNTIL = PG.roles.PLACEMENT_LEGACY_SUBMIT_UNTIL
PG.roles.PLACEMENT_LEGACY_SUBMIT_UNTIL = "2099-12-31"


def ck(n, got, want):
    ok = got == want
    print(("OK   " if ok else "XATO ") + f"{n}: {got}"
          + ("" if ok else f"   (kutilgan {want})"))
    if not ok:
        fails.append(n)


# ---- Soxta soatlar ----------------------------------------------------
CLOCK = {"t": E._pt_now()}
MS = {"t": 1_800_000_000_000}


def fake_now():
    return CLOCK["t"]


def fake_ms():
    return MS["t"]


def tick(ms):
    CLOCK["t"] += timedelta(milliseconds=ms)
    MS["t"] += int(ms)


_patched = 0
for _m in list(sys.modules.values()):
    try:
        if getattr(_m, "_PTS", None) is not None and callable(
                getattr(_m, "_pt_now", None)):
            _m._pt_now = fake_now
            _patched += 1
        if hasattr(_m, "SeqTest") and callable(getattr(_m, "seal", None)) \
                and callable(getattr(_m, "now_ms", None)):
            _m.now_ms = fake_ms
            _patched += 1
    except Exception:
        pass
ck("soxta soat o'rnatildi (ingliz + guard)", _patched >= 2, True)

# ---- 5 variantli banklar (placement_options_v2.json va JSON banklar) ---
ck("hamma bankda 5 ta variant",
   {len(q["opts"]) for q in E.PT_BANK}
   | {len(q["opts"]) for it in E.READ_BY_ID.values() for q in it["qs"]}
   | {len(it["opts"]) for it in E.LISTEN_BY_ID.values()}
   | {len(q["options"]) for q in G.BANK + R.BANK}, {5})

SERVED = []                     # mijozga ketgan hamma savol (kalit tekshiruvi)
KEY_NAMES = {"a", "answer", "correct", "target", "key"}


def keys_deep(o):
    if isinstance(o, dict):
        out = set(o)
        for v in o.values():
            out |= keys_deep(v)
        return out
    if isinstance(o, list):
        out = set()
        for v in o:
            out |= keys_deep(v)
        return out
    return set()


def remember(d):
    if isinstance(d, dict) and d.get("question"):
        SERVED.append(d["question"])
    return d


# ---- Xodim, filial, lid -------------------------------------------------
db = SessionLocal()
db.add(models.User(username="ag_admin", full_name="AG Admin",
                   password_hash=hash_password("x"), role=roles.FOUNDER,
                   is_active=True))
_br = models.Branch(name="Chilonzor")
_lead = models.Lead(full_name="Taxmin Lid", phone="+998901111111")
db.add_all([_br, _lead])
db.commit()
BRANCH_ID, LEAD_ID = _br.id, _lead.id
db.close()
_tok = client.post("/api/auth/login", json={"username": "ag_admin", "password": "x"})
HDR = {"Authorization": "Bearer " + _tok.json()["access_token"]}


# ---- Ingliz testi yordamchilari ---------------------------------------
def new_session(name, lead_id=None):
    r = client.post("/api/placement/sessions", headers=HDR,
                    json={"name": name, "lead_id": lead_id, "mode": "office"})
    return r.json()["session"]["token"]


def P(tok):
    return "/api/public/placement/" + tok


def start(tok):
    return remember(client.post(P(tok) + "/start", json={}).json())


def answer(tok, body):
    return remember(client.post(P(tok) + "/answer", json=body).json())


def row(tok):
    s = SessionLocal()
    r = s.query(E._PTS).filter(E._PTS.token == tok).first()
    out = {"cur_qid": r.cur_qid, "cur_d": r.cur_d, "step": r.step,
           "shuffle": r.cur_shuffle, "answers": json.loads(r.answers or "[]"),
           "st": E._pt_sec_state(r), "id": r.id, "status": r.status, "sec": r.sec}
    s.close()
    return out


def g_choice(tok, correct=True):
    r = row(tok)
    q = E._PT_BY_ID[r["cur_qid"]]
    order = [int(x) for x in r["shuffle"].split(",")]
    if correct:
        return order.index(q["a"])
    return next(i for i, k in enumerate(order) if k != q["a"])


def g_min(tok):
    r = row(tok)
    q = E._PT_BY_ID[r["cur_qid"]]
    order = [int(x) for x in r["shuffle"].split(",")]
    return PG.cap(PG.single_min_ms(q["q"], [q["opts"][i] for i in order]), E._PT_SECS)


def section_session(name, sec, level="B1", lead_id=None):
    tok = new_session(name, lead_id)
    s = SessionLocal()
    r = s.query(E._PTS).filter(E._PTS.token == tok).first()
    r.status, r.sec, r.level, r.unit = "running", sec, level, 1
    r.started_at = E._pt_now()
    s.commit()
    s.close()
    return tok


def cur_of(tok, sec):
    return row(tok)["st"][sec]["cur"]


def correct_picks(tok, sec):
    cur = cur_of(tok, sec)
    if sec == "vocab":
        it = E.VOCAB_BY_ID[cur["id"]]
        return [cur["w"].index(it["defs"][j][1]) for j in cur["d"]]
    if sec == "reading":
        it = E.READ_BY_ID[cur["id"]]
        return [cur["o"][i].index(q["a"]) for i, q in enumerate(it["qs"])]
    it = E.LISTEN_BY_ID[cur["id"]]
    return cur["o"].index(it["a"])


print("=== 1. 5 TA VARIANT + 'BILMAYMAN' BELGISI ===")
T1 = new_session("Birinchi lid")
d = start(T1)
q = d["question"]
ck("grammatika: 5 ta haqiqiy variant", len(q["opts"]), 5)
ck("idk: true", q.get("idk"), True)
ck("'Bilmayman' variantlar ichida emas", "Bilmayman" in q["opts"], False)
ck("kalit yo'q", keys_deep(q) & KEY_NAMES, set())
st = client.get(P(T1)).json()
ck("holatda ham 5 variant + idk",
   (len(st["question"]["opts"]), st["question"].get("idk")), (5, True))
ck("tartib 5 variantni aralashtiradi", sorted(int(x) for x in row(T1)["shuffle"].split(",")),
   [0, 1, 2, 3, 4])

print("\n=== 2. 'BILMAYMAN' ZINANI XATODEK TUSHIRADI ===")
ck("boshlang'ich qiyinlik", row(T1)["cur_d"], E._PT_START_D)
tick(10000)
d = answer(T1, {"qid": q["qid"], "choice": -1})
r1 = row(T1)
a1 = r1["answers"][-1]
ck("bilmayman: xato, idk, tez emas", (a1["ok"], a1["idk"], a1["fast"]), (False, True, False))
ck("javobda baho yo'q (last_ok yo'q)", "last_ok" in d, False)

T2 = new_session("Ikkinchi lid")
d2 = start(T2)
tick(10000)
answer(T2, {"qid": d2["question"]["qid"], "choice": g_choice(T2, correct=False)})
r2 = row(T2)
ck("xato javob: ok=false, idk=false", (r2["answers"][-1]["ok"], r2["answers"][-1]["idk"]),
   (False, False))
ck("bilmayman va xato — bir xil pog'ona", r1["cur_d"], r2["cur_d"])
ck("pog'ona pastga tushdi", r1["cur_d"] < E._PT_START_D, True)
ck("qadam ham bir xil", r1["step"], r2["step"])

print("\n=== 3. JUDA TEZ TO'G'RI JAVOB — XATO ===")
T3 = new_session("Uchinchi lid")
d = start(T3)
mn = g_min(T3)
ck("minimum pol..shift oralig'ida (1.5..5 s)",
   roles.PLACEMENT_MIN_SINGLE_FLOOR_MS <= mn <= roles.PLACEMENT_MIN_SINGLE_CEIL_MS, True)
# 2026-10-22: qisqa grammatika savoli (60–120 belgi, 5 variant bilan) ~1.5 s
_short = [q for q in E.PT_BANK if 60 <= PG.chars(q["q"], q["opts"]) <= 120]
ck("60–120 belgilik savol minimumi 1.4..1.7 s",
   (len(_short) > 100, {1400 <= PG.single_min_ms(q["q"], q["opts"]) <= 1700 for q in _short}),
   (True, {True}))
ck("eng uzun matnda ham bitta savol 5 s dan oshmaydi",
   PG.single_min_ms("x" * 5000, []), roles.PLACEMENT_MIN_SINGLE_CEIL_MS)
tick(mn - 300)
d = answer(T3, {"qid": d["question"]["qid"], "choice": g_choice(T3)})
r3 = row(T3)
a3 = r3["answers"][-1]
ck("tez to'g'ri: ok=false, fast=true", (a3["ok"], a3["fast"], a3["idk"]), (False, True, False))
# 2026-10-22 (ko'rib chiqish): tez, lekin kalitga mos javob — ballda xato,
# zina esa joyida qoladi (held). Aks holda kuchli o'quvchi oson savollarni
# tez bosib A1 gacha "sirg'alib" tushardi.
ck("tez to'g'ri: zina joyida (held), qadam o'zgarmadi",
   (r3["cur_d"], r3["step"], a3.get("held")), (E._PT_START_D, 6, True))
ck("javobda tezlik haqida hech narsa yo'q",
   keys_deep(d) & {"fast", "last_ok", "guess_warning", "held"}, set())
d_before = r3["cur_d"]
mn = g_min(T3)
tick(mn + 50)
d = answer(T3, {"qid": d["question"]["qid"], "choice": g_choice(T3)})
r3 = row(T3)
a3 = r3["answers"][-1]
ck("minimumdan keyin to'g'ri: ok=true, fast=false", (a3["ok"], a3["fast"]), (True, False))
ck("to'g'ri: zina tepaga", r3["cur_d"] > d_before, True)
# vaqt tugagandan keyin — eskicha "vaqt tugadi" (t), tez emas
tick((E._PT_SECS + E._PT_GRACE + 2) * 1000)
d = answer(T3, {"qid": d["question"]["qid"], "choice": g_choice(T3)})
a3 = row(T3)["answers"][-1]
ck("vaqt tugadi: t=true, ok=false, fast=false", (a3["t"], a3["ok"], a3["fast"]),
   (True, False, False))
# tez va XATO javob — oddiy xatodek pastga tushadi (held emas)
T3b = new_session("Tez xato lid")
d = start(T3b)
tick(300)
answer(T3b, {"qid": d["question"]["qid"], "choice": g_choice(T3b, correct=False)})
a3b = row(T3b)
ck("tez xato: pastga, held yo'q",
   (a3b["cur_d"] < E._PT_START_D, a3b["answers"][-1].get("held"), a3b["answers"][-1]["fast"]),
   (True, None, True))

print("\n=== 3b. KUCHLI O'QUVCHI OSON SAVOLNI TEZ BOSADI — SIRG'ALISH YO'Q ===")


def strong_run(name, fast_on_easy):
    """C1 o'quvchi: hamma javob to'g'ri. B2 va undan past savollarda
    fast_on_easy(n) True bo'lsa minimumdan tez bosadi, aks holda
    minimumdan sal keyin; C1 savollarida o'ylab javob beradi."""
    tok = new_session(name)
    dd = start(tok)
    n = 0
    while dd.get("status") == "running" and dd["question"]["kind"] == "grammar":
        n += 1
        rr = row(tok)
        mn = g_min(tok)
        easy = rr["cur_d"] <= 48
        tick(mn - 300 if easy and fast_on_easy(n) else mn + (100 if easy else 3000))
        dd = answer(tok, {"qid": dd["question"]["qid"], "choice": g_choice(tok)})
    s_ = SessionLocal()
    r_ = s_.query(E._PTS).filter(E._PTS.token == tok).first()
    out = (r_.level, [a["d"] for a in json.loads(r_.answers)],
           sum(1 for a in json.loads(r_.answers) if a.get("fast")))
    s_.close()
    return out


lv_all, ds_all, nf_all = strong_run("Kuchli tez", lambda n: True)
ck("hamma oson savol tez: zina boshlang'ichdan pastga tushmaydi",
   min(ds_all) >= E._PT_START_D, True)
ck("hamma oson savol tez: hammasi juda tez (ogohlantirish uchun)", nf_all, E._PT_N)
ck("hamma oson savol tez: A1 ga sirg'alib tushmaydi", lv_all != "A1", True)
lv_mix, ds_mix, nf_mix = strong_run("Kuchli aralash", lambda n: n % 2 == 0)
ck("oson savollarning yarmi tez: zina pastga tushmaydi", min(ds_mix) >= E._PT_START_D, True)
ck("oson savollarning yarmi tez: C1 ga yetadi", lv_mix, "C1")
# taxminchi (tez, tasodifiy variant) baribir eng pastga tushadi
import random as _rnd                                   # noqa: E402
_rg = _rnd.Random(7)
TG = new_session("Tasodifiy taxminchi")
d = start(TG)
while d.get("status") == "running" and d["question"]["kind"] == "grammar":
    tick(400)
    d = answer(TG, {"qid": d["question"]["qid"],
                    "choice": _rg.randrange(len(d["question"]["opts"]))})
s = SessionLocal()
ck("tasodifiy taxminchi: A1", s.query(E._PTS).filter(E._PTS.token == TG).first().level, "A1")
s.close()

print("\n=== 4. READING: MATNLI EKRAN MINIMUMI ===")
T4 = section_session("Reading lid", "reading")
d = start(T4)
ck("reading savoli", d["question"]["kind"], "reading")
ck("reading: 5 variant", [len(x["opts"]) for x in d["question"]["qs"]], [5, 5])
ck("reading idk", d["question"].get("idk"), True)


def reading_needs(tok):
    cur = cur_of(tok, "reading")
    it = E.READ_BY_ID[cur["id"]]
    sh = [[q["opts"][k] for k in cur["o"][i]] for i, q in enumerate(it["qs"])]
    n1 = PG.passage_min_ms(it["qs"][0]["q"], sh[0], it["text"])
    n2 = n1 + PG.single_min_ms(it["qs"][1]["q"], sh[1])
    full = int(it.get("secs") or 90)
    return PG.cap(n1, full), PG.cap(n2, full), it, sh


n1, n2, it, sh = reading_needs(T4)
ck("1-javob matnni ham hisoblaydi (matnli pol va bitta savoldan ko'p)",
   n1 >= roles.PLACEMENT_MIN_PASSAGE_FLOOR_MS
   and n1 > PG.single_min_ms(it["qs"][0]["q"], sh[0]), True)
ck("matn minimumi matn uzunligiga proporsional",
   PG.passage_min_ms("q", [], "x" * 900) - PG.passage_min_ms("q", [], "x" * 600),
   300 * roles.PLACEMENT_MIN_PASSAGE_PER_CHAR_MS)
tick(n1 - 200)
d = answer(T4, {"qid": d["question"]["qid"], "picks": correct_picks(T4, "reading")})
n1, n2, it, sh = reading_needs(T4)
tick(n1 + 100)                       # 1-savolga yetadi, 2-siga yetmaydi
d = answer(T4, {"qid": d["question"]["qid"], "picks": correct_picks(T4, "reading")})
n1, n2, it, sh = reading_needs(T4)
tick(n2 + 100)
d = answer(T4, {"qid": d["question"]["qid"], "picks": correct_picks(T4, "reading")})
n1, n2, it, sh = reading_needs(T4)
tick(n2 + 100)
d = answer(T4, {"qid": d["question"]["qid"], "picks": [-1, -1]})
done = row(T4)["st"]["reading"]["done"]
ck("reading (ball, juda tez, bilmayman) ketma-ket",
   [(x["score"], x["fast"], x["idk"]) for x in done],
   [(0, 2, 0), (1, 1, 0), (2, 0, 0), (0, 0, 2)])

print("\n=== 5. LISTENING: YOZUVNING KAMIDA YARMI ===")
T5 = section_session("Listening lid", "listening")
d = start(T5)
ck("listening savoli", d["question"]["kind"], "listening")
ck("listening: 5 variant + idk", (len(d["question"]["opts"]), d["question"].get("idk")),
   (5, True))


def listen_need(tok):
    cur = cur_of(tok, "listening")
    it = E.LISTEN_BY_ID[cur["id"]]
    shown = [it["opts"][k] for k in cur["o"]]
    single = PG.single_min_ms(it["q"], shown)
    words = len(it["script"].split())
    rate = max(0.5, min(2.0, float(it.get("rate") or 1.0)))
    clip = int(words / (roles.PLACEMENT_MIN_SPEECH_WPS * rate) * 1000)
    want = max(single, int(clip * roles.PLACEMENT_MIN_CLIP_SHARE))
    return single, want, it, shown


single, want, it, shown = listen_need(T5)
ck("listening minimumi = max(bitta savol, yozuvning ulushi)",
   PG.listening_min_ms(it, shown), want)
ck("yozuv minimumi bitta savoldan uzun", want > single, True)
tick(single + 100)                   # savolni o'qishga yetadi, tinglashga yo'q
d = answer(T5, {"qid": d["question"]["qid"], "choice": correct_picks(T5, "listening")})
single, want, it, shown = listen_need(T5)
tick(PG.cap(want, 90) + 100)
d = answer(T5, {"qid": d["question"]["qid"], "choice": correct_picks(T5, "listening")})
single, want, it, shown = listen_need(T5)
tick(1000)
d = answer(T5, {"qid": d["question"]["qid"], "choice": -1})
done = row(T5)["st"]["listening"]["done"]
ck("listening (ball, juda tez, bilmayman)",
   [(x["score"], x["fast"], x["idk"]) for x in done], [(0, 1, 0), (1, 0, 0), (0, 0, 1)])
_lx = dict(E.LISTEN_BY_ID[next(iter(E.LISTEN_BY_ID))], duration_ms=20000)
ck("bankda davomiylik bo'lsa — o'sha (20 s -> ulushi)",
   PG.listening_min_ms(_lx, _lx["opts"]), int(20000 * roles.PLACEMENT_MIN_CLIP_SHARE))
_lx = {"q": "Where?", "opts": ["a", "b"]}
ck("yozuv ham, matn ham yo'q — bitta savol qoidasi",
   PG.listening_min_ms(_lx, _lx["opts"]), PG.single_min_ms("Where?", ["a", "b"]))

print("\n=== 6. LUG'AT: EKRAN MINIMUMI ===")
T6 = section_session("Lug'at lid", "vocab")
d = start(T6)
ck("lug'at savoli + idk", (d["question"]["kind"], d["question"].get("idk")), ("vocab", True))


def vocab_need(tok):
    cur = cur_of(tok, "vocab")
    it = E.VOCAB_BY_ID[cur["id"]]
    words = [it["words"][i] for i in cur["w"]]
    defs = [it["defs"][j][0] for j in cur["d"]]
    return PG.cap(min(roles.PLACEMENT_MIN_SCREEN_CEIL_MS,
                      sum(PG.single_min_ms(x, words) for x in defs)), 60)


need = vocab_need(T6)
ck("ekran minimumi shiftdan (10 s) oshmaydi",
   0 < need <= roles.PLACEMENT_MIN_SCREEN_CEIL_MS, True)
tick(need - 100)
d = answer(T6, {"qid": d["question"]["qid"], "picks": correct_picks(T6, "vocab")})
need = vocab_need(T6)
tick(need + 100)
d = answer(T6, {"qid": d["question"]["qid"], "picks": correct_picks(T6, "vocab")})
need = vocab_need(T6)
tick(need + 100)
_p = correct_picks(T6, "vocab")
d = answer(T6, {"qid": d["question"]["qid"], "picks": [-1, -1, _p[2]]})
tick(500)
_p = correct_picks(T6, "vocab")
d = answer(T6, {"qid": d["question"]["qid"], "picks": [-1, _p[1], _p[2]]})
done = row(T6)["st"]["vocab"]["done"]
ck("lug'at (ball, juda tez, bilmayman)",
   [(x["score"], x["fast"], x["idk"]) for x in done],
   [(0, 3, 0), (3, 0, 0), (1, 0, 2), (0, 2, 1)])
# zina: tez-to'g'ri ekranlar pog'onani tushirmaydi (1- va 4-ekran),
# sekin 3/3 — tepaga, 1/3 — pastga
_L = E.PT_LEVELS.index("B1")
ck("lug'at zinasi: tezlik pastga tushirmaydi",
   ([x["li"] for x in done], row(T6)["st"]["vocab"]["li"]),
   ([_L, _L, _L + 1, _L], _L))

print("\n=== 7. ESKI SESSIYA (SAVOL VAQTI SAQLANMAGAN) ===")
_old_q = next(x for x in E.PT_BANK if E.PT_LEVELS.index(x["level"]) * 12 + x["unit"] - 1
              == E._PT_START_D)
_old_ans = [{"qid": 999999, "d": 24, "ok": True, "secs": 5}]
s = SessionLocal()
s.add(E._PTS(token="old_running", name="Eski yarim lid", status="running", sec="grammar",
             cur_d=E._PT_START_D, step=6, cur_qid=_old_q["id"], cur_sent_at=None,
             cur_shuffle="3,1,0,2", asked=json.dumps([_old_q["id"]]),
             answers=json.dumps(_old_ans), expires_at=E._pt_now() + timedelta(hours=40)))
s.commit()
s.close()
st = client.get(P("old_running")).json()
ck("eski savol 4 variant bilan qaytadi", len(st["question"]["opts"]), 4)
d = answer("old_running", {"qid": _old_q["id"], "choice": [3, 1, 0, 2].index(_old_q["a"])})
ro = row("old_running")
ck("vaqtsiz eski savol: darrov to'g'ri — to'g'ri qoladi",
   (ro["answers"][-1]["ok"], ro["answers"][-1]["fast"]), (True, False))
ck("eski javob o'zgarmadi", ro["answers"][0], _old_ans[0])
guard = 0
while d.get("status") == "running" and guard < E._PT_N + 10:
    guard += 1
    tick(8000)
    d = answer("old_running", {"qid": d["question"]["qid"], "choice": 0})
ck("eski sessiya grammatikasi xatosiz tugadi", d.get("status"), "break")
ro = row("old_running")
ck("eski sessiyada juda tez yo'q", sum(1 for a in ro["answers"] if a.get("fast")), 0)
# bo'limdagi eski savol: cur["sent"] yo'q
_vb = E.VOCAB_BY_ID[next(iter(E.VOCAB_BY_ID))]
s = SessionLocal()
r = s.query(E._PTS).filter(E._PTS.token == "old_running").first()
r.sec = "vocab"
r.sec_state = json.dumps({"vocab": {"li": 2, "done": [
    {"id": 0, "li": 2, "score": 2, "max": 3, "t": False}],
    "cur": {"id": _vb["id"], "li": 2, "w": [0, 1, 2, 3, 4, 5], "d": [0, 1, 2]}}})
s.commit()
s.close()
d = answer("old_running", {"qid": _vb["id"], "picks": [x[1] for x in _vb["defs"]]})
done = row("old_running")["st"]["vocab"]["done"]
ck("vaqtsiz lug'at savoli: darrov to'g'ri — 3 ball, tez emas",
   (done[-1]["score"], done[-1]["fast"]), (3, 0))
ck("eski bo'lim yozuvi o'zgarmadi", done[0], {"id": 0, "li": 2, "score": 2, "max": 3, "t": False})
_res = client.get("/api/placement/sessions", headers=HDR).json()
_or = next(x for x in _res["rows"] if x["token"] == "old_running")
ck("eski sessiya ro'yxatda xatosiz", _or["status"], "running")
# Deploydan OLDIN tugagan sessiya: javoblarda idk/fast kalitlari yo'q —
# hisoblar "0" emas, "o'lchanmagan" (null, timed=false) bo'lishi kerak.
s = SessionLocal()
s.add(E._PTS(token="old_done", name="Eski tugagan lid", status="done", sec="done",
             level="B1", unit=3, score=12, ability=26.0, cur_d=26, step=2,
             answers=json.dumps([{"qid": E.PT_BANK[i]["id"], "d": 26, "ok": i % 2 == 0,
                                  "secs": 9} for i in range(30)]),
             sec_state=json.dumps({"vocab": {"li": 2, "level": "B1", "done": [
                 {"id": 1, "li": 2, "score": 2, "max": 3, "t": False}]}}),
             started_at=E._pt_now(), finished_at=E._pt_now(),
             expires_at=E._pt_now() + timedelta(hours=40)))
s.commit()
s.close()
_res = client.get("/api/placement/sessions", headers=HDR).json()
_od = next(x for x in _res["rows"] if x["token"] == "old_done")["result"]
ck("eski tugagan sessiya: idk/fast null, timed=false, ogohlantirish yo'q",
   (_od["idk"], _od["fast"], _od["timed"], _od["guess_warning"]), (None, None, False, False))
ck("eski tugagan sessiya: guard_text '—'", _od["guard_text"], "Bilmayman: — · Juda tez: —")
ck("eski tugagan sessiya: bo'limlarda ham null",
   [(x["key"], x["idk"], x["fast"]) for x in _od["skills"]][:2],
   [("grammar", None, None), ("vocab", None, None)])
_ex = client.get("/api/placement/export?days=30", headers=HDR).json()
_oe = next(x for x in _ex["rows"] if x["name"] == "Eski tugagan lid")
ck("eksport: eski sessiyada idk/fast null, timed=false",
   (_oe["idk"], _oe["fast"], _oe["timed"]), (None, None, False))
ck("ochiq holatda timed/guard_text yo'q",
   keys_deep(client.get(P("old_done")).json().get("result") or {}) & set(PG.PRIVATE_KEYS), set())

print("\n=== 8. TAXMINAN BOSGAN LID: NATIJA, EKSPORT, LID IZOHI ===")
T7 = new_session("Taxmin Lid", LEAD_ID)
d = start(T7)
guard = 0
while d.get("status") in ("running", "break") and guard < 80:
    guard += 1
    if d.get("status") == "break":
        d = start(T7)
        continue
    q = d["question"]
    tick(300)                            # o'qimay bosadi
    if q["kind"] == "grammar":
        d = answer(T7, {"qid": q["qid"], "choice": g_choice(T7)})
    elif q["kind"] == "listening":
        d = answer(T7, {"qid": q["qid"], "choice": correct_picks(T7, "listening")})
    else:
        d = answer(T7, {"qid": q["qid"], "picks": correct_picks(T7, q["kind"])})
ck("taxmin lid testi tugadi", d.get("status"), "done")
pub = d["result"]
ck("ochiq natijada 'juda tez' kalitlari yo'q",
   keys_deep(pub) & set(PG.PRIVATE_KEYS), set())
ck("ochiq natijada idk bor", "idk" in pub, True)
pub2 = client.get(P(T7)).json()["result"]
ck("ochiq holatda ham yo'q", keys_deep(pub2) & set(PG.PRIVATE_KEYS), set())
rows = client.get("/api/placement/sessions", headers=HDR).json()["rows"]
sr = next(x for x in rows if x["token"] == T7)["result"]
# 2026-10-22: savollar soni dvijok konstantalaridan (test 100 savolga
# o'tdi — grammatika 50, tinglash 10; qattiq yozilgan son eskirardi).
_SN = E._PT_SEC_N
sec_units = [("grammar", E._PT_N), ("vocab", _SN["vocab"] * 3),
             ("reading", _SN["reading"] * 2), ("listening", _SN["listening"])]
units = sum(n for _k, n in sec_units)
ck("xodim natijasi: hammasi juda tez", (sr["fast"], sr["idk"]), (units, 0))
ck("guess_warning", sr["guess_warning"], True)
ck("ogohlantirish matni", sr["guess_label"], roles.PLACEMENT_GUESS_LABEL)
ck("bo'limlar kesimida fast",
   [(x["key"], x["fast"]) for x in sr["skills"]], sec_units)
ck("hammasi juda tez — ball 0", sr["score"], 0)
ck("guard_text", sr["guard_text"].startswith(f"Bilmayman: 0 · Juda tez: {units}"), True)
sid = next(x for x in rows if x["token"] == T7)["id"]
det = client.get(f"/api/placement/sessions/{sid}", headers=HDR).json()
ck("javoblar tafsilotida fast", all(a["fast"] for a in det["answers"]), True)
ex = client.get("/api/placement/export?days=30", headers=HDR).json()
er = next(x for x in ex["rows"] if x["session_id"] == sid)
ck("eksport: idk/fast/guess_warning", (er["idk"], er["fast"], er["guess_warning"]),
   (0, units, True))
ck("eksport: bo'limlarda idk/fast",
   all({"idk", "fast"} <= set(x) for x in er["skills"]), True)
s = SessionLocal()
_note = s.query(models.Lead).get(LEAD_ID).note or ""
s.close()
ck("lid izohida 'Juda tez' va ogohlantirish",
   (f"Juda tez: {units}" in _note, roles.PLACEMENT_GUESS_LABEL in _note), (True, True))
ld = client.get("/api/leads", headers=HDR).json()
_lp = next(x for x in ld if x["id"] == LEAD_ID)["placement"]
ck("lidlar ro'yxatida guess_warning", _lp["guess_warning"], True)

# Halol lid: o'ylab javob beradi, bilmaganiga "Bilmayman"
T8 = new_session("Halol lid")
d = start(T8)
n = 0
while d.get("status") == "running" and d["question"]["kind"] == "grammar":
    n += 1
    tick(9000)
    d = answer(T8, {"qid": d["question"]["qid"], "choice": -1 if n % 3 == 0 else g_choice(T8)})
rows = client.get("/api/placement/sessions", headers=HDR).json()["rows"]
d = client.post(P(T8) + "/answer", json={"skip_section": True})  # vocabni o'tkazib bo'lmaydi
ck("lug'at bo'limini o'tkazib bo'lmaydi", d.status_code, 400)
s = SessionLocal()
r = s.query(E._PTS).filter(E._PTS.token == T8).first()
E._pt_all_done(r)
s.commit()
s.close()
rows = client.get("/api/placement/sessions", headers=HDR).json()["rows"]
hr = next(x for x in rows if x["token"] == T8)["result"]
_idk = E._PT_N // 3                     # har 3-savolga "Bilmayman"
ck("halol lid: har 3-savolga Bilmayman, fast 0, ogohlantirish yo'q",
   (hr["idk"], hr["fast"], hr["guess_warning"]), (_idk, 0, False))
ck("guard_text halol", hr["guard_text"], f"Bilmayman: {_idk} · Juda tez: 0")

print("\n=== 9. NEMIS VA RUS TESTI ===")


def run_seq(prefix, mod, label, phone):
    base = "/api/public/" + prefix
    bank = mod.BANK
    aid = str(uuid.uuid4())
    d = remember(client.post(base + "/start", json={"attempt_id": aid}).json())
    q = d["question"]
    ck(f"{label}: 1-savol, 5 variant, idk",
       (q["id"], len(q["options"]), q["idk"], d["total"]), (bank[0]["id"], 5, True, 48))
    ck(f"{label}: kalit yo'q", keys_deep(q) & KEY_NAMES, set())
    tokb = d["state"]
    raw = base64.urlsafe_b64decode(tokb + "=" * (-len(tokb) % 4))
    try:
        json.loads(raw)
        opaque = False
    except ValueError:
        opaque = True
    ck(f"{label}: state o'qib bo'lmaydi (shifrlangan)", opaque and b'"c"' not in raw, True)
    # matnli savol: nemis/rus — BITTA SAVOL qoidasi (2..7 s), 1-si qisqa
    # matn ham o'qiladigan belgilarga qo'shiladi; keyingisi (o'sha matn) —
    # faqat savol va variantlar. Ingliz readingidagi 4 s pol yo'q.
    ti = next(i for i, x in enumerate(bank) if x.get("text"))
    ck(f"{label}: matnli 1-savol minimumi",
       mod.SEQ.min_ms(ti), PG.single_min_ms([bank[ti]["text"], bank[ti]["prompt"]],
                                             bank[ti]["options"]))
    ck(f"{label}: hamma savol minimumi pol..shift (1.5..5 s)",
       all(roles.PLACEMENT_MIN_SINGLE_FLOOR_MS <= mod.SEQ.min_ms(i)
           <= roles.PLACEMENT_MIN_SINGLE_CEIL_MS for i in range(len(bank))), True)
    if bank[ti + 1].get("text") == bank[ti]["text"]:
        ck(f"{label}: o'sha matndagi keyingi savol — bitta savol qoidasi",
           mod.SEQ.min_ms(ti + 1),
           PG.single_min_ms(bank[ti + 1]["prompt"], bank[ti + 1]["options"]))
    # tampered / boshqa test tokeni
    bad = client.post(base + "/answer", json={"attempt_id": aid, "state": tokb[:-3] + "AAA",
                                              "qid": q["id"], "choice": 0})
    ck(f"{label}: buzilgan state — 400", bad.status_code, 400)
    other = "ru-placement" if prefix.startswith("german") else "de-placement"
    forged = PG.seal(other, {"a": aid, "i": 47, "s": 0, "c": [0] * 47, "f": []})
    bad = client.post(base + "/answer", json={"attempt_id": aid, "state": forged,
                                              "qid": bank[47]["id"], "choice": 0})
    ck(f"{label}: boshqa test state'i — 400", bad.status_code, 400)
    bad = client.post(base + "/answer", json={"attempt_id": aid, "state": tokb,
                                              "qid": q["id"], "choice": 5})
    ck(f"{label}: chegaradan tashqari variant — 422", bad.status_code, 422)
    st_ = client.post(base + "/answer", json={"attempt_id": aid, "state": tokb,
                                              "qid": bank[3]["id"], "choice": 0}).json()
    ck(f"{label}: eski savol — o'zgarishsiz", (st_["stale"], st_["question"]["id"]),
       (True, bank[0]["id"]))
    cur = client.post(base + "/current", json={"attempt_id": aid, "state": tokb}).json()
    ck(f"{label}: /current joriy savol", (cur["question"]["id"], cur["answered"]),
       (bank[0]["id"], 0))
    # 15 ta tez to'g'ri, 4 ta bilmayman, qolgani o'ylab to'g'ri
    for i in range(48):
        if i < 15:
            tick(300)
            ch = bank[i]["answer"]
        elif i < 19:
            tick(300)
            ch = -1
        else:
            tick(mod.SEQ.min_ms(i) + 50)
            ch = bank[i]["answer"]
        d = remember(client.post(base + "/answer", json={
            "attempt_id": aid, "state": d["state"], "qid": bank[i]["id"],
            "choice": ch}).json())
        if keys_deep(d) & {"fast", "last_ok", "guess_warning", "correct"}:
            ck(f"{label}: javobda baho ko'rinmasin ({i})", True, False)
    ck(f"{label}: tugadi", (d["done"], d["question"], d["answered"]), (True, None, 48))
    early = client.post(base, json={"attempt_id": aid, "full_name": "Erta Yuboruvchi",
                                    "phone": "+998 90 000 00 01", "branch_id": BRANCH_ID,
                                    "state": tokb})
    ck(f"{label}: tugallanmagan state — 422", early.status_code, 422)
    wrong_aid = client.post(base, json={"attempt_id": str(uuid.uuid4()), "full_name": "Begona",
                                        "phone": "+998 90 000 00 02", "branch_id": BRANCH_ID,
                                        "state": d["state"]})
    ck(f"{label}: boshqa attempt_id — 409", wrong_aid.status_code, 409)
    sub = client.post(base, json={"attempt_id": aid, "full_name": f"{label} Taxminchi",
                                  "phone": phone, "branch_id": BRANCH_ID,
                                  "answers": {x["id"]: x["answer"] for x in bank},
                                  "state": d["state"]})
    ck(f"{label}: saqlandi", sub.status_code, 200)
    pres = sub.json()["result"]
    ck(f"{label}: ochiq natijada 'juda tez' yo'q", keys_deep(pres) & set(PG.PRIVATE_KEYS), set())
    ck(f"{label}: ball (mijoz answers e'tiborsiz, state'dan)", pres["score"], 48 - 15 - 4)
    ck(f"{label}: ochiq natijada idk", pres["idk"], 4)
    again = client.post(base, json={"attempt_id": aid, "full_name": f"{label} Taxminchi",
                                    "phone": phone, "branch_id": BRANCH_ID,
                                    "state": d["state"]})
    ck(f"{label}: qayta yuborish (retry) — o'sha natija",
       (again.status_code, again.json()["result"]["score"]), (200, 48 - 15 - 4))
    ck(f"{label}: retry javobida ham 'juda tez' yo'q",
       keys_deep(again.json()["result"]) & set(PG.PRIVATE_KEYS), set())
    # eski sahifa: answers bilan, state'siz — 5-variant (4) ham qabul
    legacy = {x["id"]: x["answer"] for x in bank}
    legacy[bank[0]["id"]] = 4
    legacy[bank[1]["id"]] = -1
    legacy_body = {"attempt_id": str(uuid.uuid4()), "full_name": f"{label} Eski",
                   "phone": phone[:-1] + "9", "branch_id": BRANCH_ID, "answers": legacy}
    lsub = client.post(base, json=legacy_body)
    ck(f"{label}: eski usulda yuborish ishlaydi", lsub.status_code, 200)
    ck(f"{label}: eski usul bahosi", lsub.json()["result"]["score"], 46)
    bad5 = dict(legacy)
    bad5[bank[2]["id"]] = 5
    lbad = client.post(base, json={"attempt_id": str(uuid.uuid4()), "full_name": f"{label} Yomon",
                                   "phone": phone[:-1] + "8", "branch_id": BRANCH_ID,
                                   "answers": bad5})
    ck(f"{label}: 6-indeks — 422", lbad.status_code, 422)
    # eski yo'l muddati (roles.PLACEMENT_LEGACY_SUBMIT_UNTIL) o'tgach: yangi
    # state'siz yuborish — 409 "Sahifani yangilang"; avval saqlangan urinishni
    # qayta yuborish (retry) esa o'sha natijani qaytaradi.
    _until = PG.roles.PLACEMENT_LEGACY_SUBMIT_UNTIL
    try:
        PG.roles.PLACEMENT_LEGACY_SUBMIT_UNTIL = REAL_LEGACY_UNTIL
        _last = datetime.date.fromisoformat(REAL_LEGACY_UNTIL)
        ck(f"{label}: eski yo'l deploy kuni va oxirgi kuni ochiq",
           (PG.legacy_submit_open(datetime.date(2026, 10, 22)), PG.legacy_submit_open(_last)),
           (True, True))
        ck(f"{label}: eski yo'l muddati o'tgach yopiq",
           PG.legacy_submit_open(_last + datetime.timedelta(days=1)), False)
        PG.roles.PLACEMENT_LEGACY_SUBMIT_UNTIL = "2026-01-01"
        late = client.post(base, json={"attempt_id": str(uuid.uuid4()), "full_name": f"{label} Kech",
                                       "phone": phone[:-1] + "7", "branch_id": BRANCH_ID,
                                       "answers": legacy})
        ck(f"{label}: muddat o'tgach state'siz — 409",
           (late.status_code, late.json().get("detail")), (409, PG.LEGACY_CLOSED_TEXT))
        again_l = client.post(base, json=legacy_body)
        ck(f"{label}: muddat o'tgach saqlangan eski urinish retry — 200",
           (again_l.status_code, again_l.json()["result"]["score"]), (200, 46))
    finally:
        PG.roles.PLACEMENT_LEGACY_SUBMIT_UNTIL = _until
    # token uzunligi "juda tez" belgisini oshkor qilmasin: bir xil tanlov,
    # biri tez, biri sekin — har qadamda token uzunligi bir xil
    sa = client.post(base + "/start", json={"attempt_id": str(uuid.uuid4())}).json()
    sb = client.post(base + "/start", json={"attempt_id": str(uuid.uuid4())}).json()
    la, lb = [], []
    for i in range(12):
        tick(200)
        sa = client.post(base + "/answer", json={"state": sa["state"], "qid": bank[i]["id"],
                                                 "choice": 0}).json()
        tick(mod.SEQ.min_ms(i) + 500)
        sb = client.post(base + "/answer", json={"state": sb["state"], "qid": bank[i]["id"],
                                                 "choice": 0}).json()
        la.append(len(sa["state"]))
        lb.append(len(sb["state"]))
    ck(f"{label}: token uzunligi tez/sekin javobda bir xil", la, lb)
    # matn qat'iy o'lchamga to'ldiriladi — uzunlik test davomida o'zgarmaydi
    ck(f"{label}: token uzunligi butun test davomida bir xil",
       len(set(la + lb + [len(sa["state"])])), 1)
    return aid


run_seq("german-placement", G, "Nemis", "+998 90 123 45 61")
run_seq("russian-placement", R, "Rus", "+998 90 123 45 71")

for path, label in (("/api/german-placement/results", "Nemis"),
                    ("/api/russian-placement/results", "Rus")):
    rs = client.get(path, headers=HDR).json()["rows"]
    t = next(x for x in rs if x["name"] == f"{label} Taxminchi")["result"]
    ck(f"{label} xodim natijasi: idk/fast/guess_warning/timed",
       (t["idk"], t["fast"], t["guess_warning"], t["timed"]), (4, 15, True, True))
    ck(f"{label}: bloklar kesimida fast/idk",
       (sum(b["fast"] for b in t["blocks"]), sum(b["idk"] for b in t["blocks"])), (15, 4))
    ck(f"{label}: ko'nikmalar kesimida fast",
       sum(x["fast"] for x in t["skills"]), 15)
    lg = next(x for x in rs if x["name"] == f"{label} Eski")["result"]
    # vaqt o'lchanmagan: "juda tez" 0 emas, noma'lum (None) — "toza" ko'rinmaydi
    ck(f"{label} eski usul: timed=false, fast=None, idk=1",
       (lg["timed"], lg["fast"], lg["idk"], lg["guess_warning"]), (False, None, 1, False))
    ck(f"{label} eski usul: bo'limlarda ham fast=None, satrda '—'",
       ({b["fast"] for b in lg["blocks"] + lg["skills"]}, lg["guard_text"].endswith("Juda tez: —")),
       ({None}, True))

# 2026-10-22 dan oldin saqlangan yozuv (hisoblarsiz) — xatosiz o'qiladi
s = SessionLocal()
_l = models.Lead(full_name="Eski Nemis", phone="+998901234500", branch_id=BRANCH_ID)
s.add(_l)
s.flush()
_ans = {x["id"]: x["answer"] for x in G.BANK}
_ans[G.BANK[0]["id"]] = -1
_old_res = {k: v for k, v in G.assess(_ans).items()
            if k not in ("idk", "fast", "guess_warning", "guess_label", "guard_text",
                         "timed", "fast_ids", "skills", "allPassed")}
for _b in _old_res["blocks"]:
    _b.pop("idk", None)
    _b.pop("fast", None)
s.add(models.GermanPlacementResult(attempt_id=str(uuid.uuid4()), payload_hash="x", lead_id=_l.id,
                                   branch_id=BRANCH_ID, full_name="Eski Nemis",
                                   phone="998901234500", result_json=json.dumps(_old_res),
                                   answers_json=json.dumps(_ans)))
s.commit()
s.close()
rs = client.get("/api/german-placement/results", headers=HDR).json()["rows"]
t = next(x for x in rs if x["name"] == "Eski Nemis")["result"]
ck("eski nemis yozuvi: idk javoblardan, fast None, timed false",
   (t["idk"], t["fast"], t["timed"], t["blocks"][0]["idk"], t["blocks"][0]["fast"], t["score"]),
   (1, None, False, 1, None, 47))

print("\n=== 10. JAVOB KALITI HECH QAYERDA YO'Q ===")
ck("berilgan savollar soni", len(SERVED) > 150, True)
ck("hamma berilgan savolda kalit yo'q",
   [i for i, x in enumerate(SERVED) if keys_deep(x) & KEY_NAMES], [])
ck("hamma berilgan savolda idk: true", all(x.get("idk") is True for x in SERVED), True)

print("\n" + ("HAMMASI O'TDI" if not fails else "XATO: " + ", ".join(fails)))
sys.exit(1 if fails else 0)
