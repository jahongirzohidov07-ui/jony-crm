# -*- coding: utf-8 -*-
"""PLACEMENT TEST — YANGI BO'LIMLAR (2026-09-11).

Jahongir: "faqat ichiga reading va listening lar ham qosha
olmaysanmi" + "grammar 30ta qolsin uzogi bilan grammar savoli".

Tekshiriladi:
  1. Banklar to'g'ri yozilganmi (ta'rif faqat BITTA so'zga mos
     kelishi, javob indeksi chegarada bo'lishi) — bank xatosi
     lidga noto'g'ri daraja qo'yadi, shuning uchun eng muhimi.
  2. Grammatika 30 ta savoldan keyin tugab, TANAFFUS qaytarishi.
  3. Tanaffusda savol BERILMASLIGI — aks holda lid o'ylab
     o'tirganda soati ketardi.
  4. To'g'ri javob mijozga HECH QACHON yuborilmasligi.
  5. To'liq o'tish: grammar -> vocab -> reading -> listening -> done,
     va natijada har ko'nikma darajasi chiqishi.
  6. Listeningni o'tkazib yuborish (ovoz ishlamasa) — jazosiz.
  7. Grammatika tugashi bilanoq natija LIDGA yozilishi (lid qolgan
     bo'limlarni tashlab ketsa ham joylashtirish mumkin bo'lsin).
  8. Eski, yarim qolgan sessiya buzilmasligi.
"""
import os
import sys
import tempfile

_DB = os.path.join(tempfile.gettempdir(), "pt_sections_test.db")
os.environ["DATABASE_URL"] = "sqlite:///" + _DB.replace("\\", "/")
if os.path.exists(_DB):
    os.remove(_DB)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient          # noqa: E402
import main, models, roles                          # noqa: F401,E402
import entry as E                                   # noqa: E402
from database import SessionLocal                   # noqa: E402
from auth import hash_password                      # noqa: E402
from pt_vocab_bank import VOCAB_BLOCKS              # noqa: E402
from pt_read_bank import READ_ITEMS                 # noqa: E402
from pt_listen_bank import LISTEN_ITEMS             # noqa: E402

client = TestClient(E.app)
fails = []


def ck(n, got, want):
    ok = got == want
    print(("OK   " if ok else "XATO ") + f"{n}: {got}"
          + ("" if ok else f"   (kutilgan {want})"))
    if not ok:
        fails.append(n)


print("=== 1. BANKLAR TO'G'RI YOZILGANMI ===")
bad_ids, bad_idx, dup_def, short = [], [], [], []
seen = set()
for b in VOCAB_BLOCKS:
    if b["id"] in seen:
        bad_ids.append(b["id"])
    seen.add(b["id"])
    if len(b["words"]) != 6 or len(b["defs"]) != 3:
        short.append(b["id"])
    tgt = [t for _, t in b["defs"]]
    if any(not (0 <= t < len(b["words"])) for t in tgt):
        bad_idx.append(b["id"])
    if len(set(tgt)) != len(tgt):
        dup_def.append(b["id"])          # ikki ta'rif bitta so'zga
ck("lug'at bloklari soni", len(VOCAB_BLOCKS), 30)
ck("takror id", bad_ids, [])
ck("6 so'z / 3 ta'rif emas", short, [])
ck("javob indeksi chegaradan tashqarida", bad_idx, [])
ck("ikki ta'rif bir so'zga", dup_def, [])
ck("har darajada blok bor",
   sorted({b["level"] for b in VOCAB_BLOCKS}),
   sorted(E.PT_LEVELS))

r_bad, r_short = [], []
for it in READ_ITEMS:
    if len(it["qs"]) != 2:
        r_short.append(it["id"])
    for q in it["qs"]:
        if len(q["opts"]) != 4 or not (0 <= q["a"] < 4):
            r_bad.append(it["id"])
        if len(set(q["opts"])) != len(q["opts"]):
            r_bad.append(it["id"])       # bir xil variant ikki marta
ck("reading matnlari soni", len(READ_ITEMS), 18)
ck("har matnda 2 savol emas", r_short, [])
ck("reading variantlari xato", r_bad, [])
ck("reading har darajada bor",
   sorted({x["level"] for x in READ_ITEMS}), sorted(E.PT_LEVELS))

l_bad = [x["id"] for x in LISTEN_ITEMS
         if len(x["opts"]) != 4 or not (0 <= x["a"] < 4)
         or len(set(x["opts"])) != 4 or not x["script"].strip()]
ck("listening yozuvlari soni", len(LISTEN_ITEMS), 30)
ck("listening variantlari xato", l_bad, [])
ck("listening har darajada bor",
   sorted({x["level"] for x in LISTEN_ITEMS}), sorted(E.PT_LEVELS))

print("\n=== 2. SESSIYA OCHISH ===")
db = SessionLocal()
u = models.User(username="pt_admin", full_name="PT Admin",
                password_hash=hash_password("x"), role=roles.FOUNDER,
                is_active=True)
db.add(u)
lead = models.Lead(full_name="Test Lid", phone="+998900000000")
db.add(lead)
db.commit()
LEAD_ID = lead.id
db.close()

tok = client.post("/api/auth/login",
                  json={"username": "pt_admin", "password": "x"})
HDR = {"Authorization": "Bearer " + tok.json()["access_token"]}
res = client.post("/api/placement/sessions", headers=HDR,
                  json={"lead_id": LEAD_ID, "mode": "office"})
ck("sessiya ochildi", res.status_code, 200)
TOKEN = res.json()["session"]["token"]
P = "/api/public/placement/" + TOKEN


def state():
    return client.get(P).json()


def start():
    return client.post(P + "/start", json={}).json()


def answer(body):
    return client.post(P + "/answer", json=body).json()


print("\n=== 3. GRAMMATIKA 30 TA, KEYIN TANAFFUS ===")
d = start()
ck("birinchi savol grammatika", d["question"]["kind"], "grammar")
ck("jami 30", d["question"]["total"], 30)
ck("to'g'ri javob yuborilmaydi",
   any(k in d["question"] for k in ("a", "answer", "correct")), False)

n = 0
while d.get("status") == "running" and d.get("question", {}).get(
        "kind") == "grammar":
    n += 1
    d = answer({"qid": d["question"]["qid"], "choice": 0})
    if n > 40:
        break
ck("grammatika savollari soni", n, 30)
ck("keyin tanaffus", d.get("status"), "break")
ck("tanaffusda savol YO'Q", "question" in d, False)
ck("grammatika natijasi bor", bool(d["section_done"].get("level")), True)
ck("keyingisi lug'at", d.get("next"), "vocab")

print("\n=== 4. GRAMMATIKA TUGASHI BILAN LID YANGILANDI ===")
db = SessionLocal()
_ld = db.query(models.Lead).get(LEAD_ID)
ck("lid izohida diagnostika bor", "[Diagnostika]" in (_ld.note or ""), True)
db.close()

print("\n=== 5. LUG'AT BLOKI ===")
d = start()                       # "Davom etish"
q = d["question"]
ck("kind = vocab", q["kind"], "vocab")
ck("6 ta so'z", len(q["words"]), 6)
ck("3 ta ta'rif", len(q["defs"]), 3)
ck("bloklar soni 10", q["total"], 10)
ck("javob yo'q", any(k in q for k in ("a", "answer", "target")), False)


def solve_vocab(q):
    """To'g'ri javobni SERVER ma'lumotidan topamiz (test uchun)."""
    sess = SessionLocal()
    s = sess.query(E._PTS).filter(E._PTS.token == TOKEN).first()
    cur = E._pt_sec_state(s)["vocab"]["cur"]
    sess.close()
    item = E.VOCAB_BY_ID[cur["id"]]
    picks = []
    for j in cur["d"]:
        tgt = item["defs"][j][1]
        picks.append(cur["w"].index(tgt))
    return picks


vn = 0
while d.get("status") == "running" and d["question"]["kind"] == "vocab":
    vn += 1
    d = answer({"qid": d["question"]["qid"], "picks": solve_vocab(d)})
    if vn > 15:
        break
ck("lug'at bloklari soni", vn, 10)
ck("lug'atdan keyin tanaffus", d.get("status"), "break")
ck("lug'at darajasi hisoblandi", bool(d["section_done"].get("level")), True)
ck("hammasi to'g'ri -> eng yuqori daraja",
   d["section_done"]["level"], "C1")

print("\n=== 6. READING ===")
d = start()
q = d["question"]
ck("kind = reading", q["kind"], "reading")
ck("matn bor", len(q["text"]) > 40, True)
ck("2 ta savol", len(q["qs"]), 2)
ck("matnlar soni 5", q["total"], 5)

rn = 0
while d.get("status") == "running" and d["question"]["kind"] == "reading":
    rn += 1
    d = answer({"qid": d["question"]["qid"], "picks": [0, 0]})
    if rn > 8:
        break
ck("reading savollari soni", rn, 5)
ck("readingdan keyin tanaffus", d.get("status"), "break")

print("\n=== 7. LISTENING + O'TKAZIB YUBORISH ===")
d = start()
q = d["question"]
ck("kind = listening", q["kind"], "listening")
ck("ovoz matni bor", len(q["script"]) > 10, True)
ck("2 marta eshitish", q["plays"], 2)
ck("javob yuborilmaydi", "a" in q, False)

d = answer({"skip_section": True})
ck("o'tkazib yuborilgach test tugadi", d.get("status"), "done")
r = d["result"]
ck("listening 'tekshirilmadi'",
   [x["skipped"] for x in r["skills"] if x["key"] == "listening"], [True])
ck("listening darajasi yo'q",
   [x["level"] for x in r["skills"] if x["key"] == "listening"], [None])
ck("lug'at darajasi natijada", 
   [x["level"] for x in r["skills"] if x["key"] == "vocab"], ["C1"])
ck("4 ta ko'nikma", len(r["skills"]), 4)
ck("umumiy daraja bor", r["overall"] in E.PT_LEVELS, True)
ck("grammatika soni 30", r["total"], 30)

print("\n=== 8. TUGAGACH QAYTA JAVOB BERIB BO'LMAYDI ===")
rr = client.post(P + "/answer", json={"choice": 0})
ck("javob 409", rr.status_code, 409)
rr = client.post(P + "/start", json={})
ck("start 409", rr.status_code, 409)
ck("holat done", state()["status"], "done")

print("\n=== 9. LISTENINGNI TO'LIQ ISHLASH ===")
res2 = client.post("/api/placement/sessions", headers=HDR,
                   json={"name": "Ikkinchi lid", "mode": "office"})
T2 = res2.json()["session"]["token"]
P2 = "/api/public/placement/" + T2


def a2(body):
    return client.post(P2 + "/answer", json=body).json()


d = client.post(P2 + "/start", json={}).json()
guard = 0
while d.get("status") in ("running", "break") and guard < 120:
    guard += 1
    if d.get("status") == "break":
        d = client.post(P2 + "/start", json={}).json()
        continue
    q = d["question"]
    if q["kind"] == "vocab":
        d = a2({"qid": q["qid"], "picks": [0, 1, 2]})
    elif q["kind"] == "reading":
        d = a2({"qid": q["qid"], "picks": [0, 0]})
    else:
        d = a2({"qid": q["qid"], "choice": 0})
ck("to'liq o'tish tugadi", d.get("status"), "done")
r2 = d["result"]
ck("hamma ko'nikmada daraja bor",
   all(x["level"] in E.PT_LEVELS for x in r2["skills"]), True)
ck("listening o'tkazib yuborilmagan",
   [x["skipped"] for x in r2["skills"] if x["key"] == "listening"], [False])
ck("jami savol 30+10+5+6 = 51 qadam", guard, 51 + 3)

print("\n=== 10. ESKI SESSIYA BUZILMAYDI ===")
db = SessionLocal()
old = E._PTS(token="legacy_tok", name="Eski lid", status="done",
            level="B1", unit=4, score=41, ability=27.0,
            answers='[{"qid":1,"d":24,"ok":true,"secs":5}]',
            asked="[1]", per_level='{"B1": {"ok": 1, "n": 1}}')
db.add(old)
db.commit()
db.close()
o = client.get("/api/public/placement/legacy_tok").json()
ck("eski sessiya ochiladi", o["status"], "done")
ck("eski daraja saqlandi", o["result"]["level"], "B1")
ck("eski sessiyada ko'nikmalar bo'sh",
   [x["level"] for x in o["result"]["skills"] if x["key"] != "grammar"],
   [None, None, None])

print("\n=== 11. JONY SCHOOL'GA EKSPORT (2026-09-26) ===")
# Jahongir: "11-sinflarga lid qilib korgizdim ularni natijalarini ham
# qoshib qo'y ozing endi topib Jony 360ga" — tugallanganlar JSON bo'lib
# chiqadi, Jony School shu faylni o'qiydi.
ex = client.get("/api/placement/export?days=30", headers=HDR)
ck("eksport 200", ex.status_code, 200)
exd = ex.json()
ck("manba jonyos/placement", (exd["source"], exd["kind"]), ("jonyos", "placement"))
ck("faqat tugallanganlar (finished_at bilan)",
   all(r["finished_at"] for r in exd["rows"]), True)
names = [r["name"] for r in exd["rows"]]
ck("to'liq o'tgan lid ro'yxatda", any(n and n.startswith("Test Lid") for n in names), True)
row = next((r for r in exd["rows"] if r["name"] == "Eski lid"), None)
ck("eski sessiya (finished_at yo'q) chiqmaydi", row, None)
row = next(r for r in exd["rows"] if (r["name"] or "").startswith("Test Lid"))
ck("4 ko'nikma", [s["key"] for s in row["skills"]],
   ["grammar", "vocab", "reading", "listening"])
ck("grammatika mavzulari bor", len(row["topics"]) > 0, True)
ck("mavzuda ok/n/pct", all({"topic", "ok", "n", "pct"} <= set(t) for t in row["topics"]), True)
ck("daraja va unit", (row["level"] in E.PT_LEVELS, 1 <= row["unit"] <= 12), (True, True))
ck("javoblar eksportga kirmaydi", "answers" in row, False)
noauth = client.get("/api/placement/export")
ck("ruxsatsiz — 401", noauth.status_code, 401)

print("\n" + ("HAMMASI O'TDI" if not fails else "XATO: " + ", ".join(fails)))
sys.exit(1 if fails else 0)
