# -*- coding: utf-8 -*-
"""Multilevel Speaking — HTTP darajasida uchidan-uchiga tekshiruv.

test_speaking_cefr.py FORMAT va KONTENTni tekshiradi. Bu esa
boshqa savolga javob beradi: o'quvchi diktafonni bosib javob
yuborganda tizim ROSTDAN ball chiqaradimi?

Tekshiriladi:
  - bosh ekran, qo'llanma, vazifa
  - javob yuborilganda tahlil va ball qaytishi
  - AI ishlamaganda ham baho berilishi (eng muhim holat)
  - AI ball qaytarsa, uning bahosi ustun turishi
  - Free Mock: 10 savol -> 0-75 ball va CEFR darajasi
  - natija bazaga yozilib, bosh ekranda ko'rinishi
"""
import os
import sys

os.environ["DATABASE_URL"] = "sqlite:////tmp/verify_sp/db.sqlite"
os.makedirs("/tmp/verify_sp", exist_ok=True)
if os.path.exists("/tmp/verify_sp/db.sqlite"):
    os.remove("/tmp/verify_sp/db.sqlite")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient          # noqa: E402
import main, models                                # noqa: E402
import entry                                       # noqa: F401,E402
import student_app                                 # noqa: E402
from database import SessionLocal                  # noqa: E402
from auth import hash_password                     # noqa: E402
import speaking_cefr_guide as G                    # noqa: E402
import speaking_cefr_seed as S                     # noqa: E402
import speaking_cefr_format as F                   # noqa: E402

c = TestClient(main.app)
db = SessionLocal()
fails = []


def ck(n, got, want):
    ok = got == want
    print(("OK   " if ok else "XATO ") + f"{n}: {got}"
          + ("" if ok else f"   (kutilgan {want})"))
    if not ok:
        fails.append(n)


b = models.Branch(name="Zafar")
db.add(b); db.commit()
s = models.Student(full_name="Speaking Test", branch_id=b.id,
                   status="active", phone="998901110077",
                   public_id="STU-SP-1")
db.add(s); db.commit()
u = models.User(username="998901110077",
                password_hash=hash_password("jonyjony"),
                role="student", full_name="Speaking Test",
                branch_id=b.id)
db.add(u); db.commit()
s.user_id = u.id; db.commit()
H = {"Authorization": "Bearer " + c.post(
    "/api/auth/login",
    json={"username": "998901110077", "password": "jonyjony"}
).json()["access_token"]}

# --- AI ni o'chiramiz: eng yomon holatni sinaymiz ---------------
def _ai_off(system, messages):
    raise RuntimeError("AI kaliti yo'q (test)")


student_app._ai_reply = _ai_off

print("=== BOSH EKRAN ===")
d = c.get("/api/student/cefr/speaking/home", headers=H).json()
ck("4 qism", len(d["parts"]), 4)
ck("0-75 shkala", d["score_max"], 75)
ck("xom ball 21", d["raw_max"], 21)
ck("5 daraja bandi", len(d["levels"]), 5)
ck("C1 chegarasi 65-75",
   [(l["from"], l["to"]) for l in d["levels"] if l["level"] == "C1"],
   [(65, 75)])
ck("B2 chegarasi 51-64",
   [(l["from"], l["to"]) for l in d["levels"] if l["level"] == "B2"],
   [(51, 64)])
ck("B1 chegarasi 30-50",
   [(l["from"], l["to"]) for l in d["levels"] if l["level"] == "B1"],
   [(30, 50)])
ck("boshida mock yo'q", d["best"], 0)

print("\n=== QO'LLANMA ===")
g = c.get("/api/student/cefr/speaking/guide/p3", headers=H).json()
ck("shablon bor", len(g["template"]) >= 4, True)
ck("namuna bor", bool(g["sample"]), True)
ck("rasmiy shkala 0-6", g["band"]["max"], 6)
ck("shkalada 7 daraja", len(g["band"]["scale"]), 7)
ck("yo'q qismga 404",
   c.get("/api/student/cefr/speaking/guide/p9", headers=H).status_code, 404)

print("\n=== VAZIFA ===")
t = c.get("/api/student/cefr/speaking/task?part=p11&idx=0", headers=H).json()
ck("3 savol", len(t["questions"]), 3)
ck("30 soniyadan", t["seconds"], [30, 30, 30])
ck("tayyorgarlik yo'q", t["prep"], 0)
t3 = c.get("/api/student/cefr/speaking/task?part=p3&idx=0", headers=H).json()
ck("FOR/AGAINST keldi", len(t3["for"]) >= 3 and len(t3["against"]) >= 3, True)
ck("120 soniya", t3["seconds"], [120])
ck("60s tayyorgarlik", t3["prep"], 60)
t2 = c.get("/api/student/cefr/speaking/task?part=p12&idx=0", headers=H).json()
ck("ikki rasm tavsifi", bool(t2["scene_a"] and t2["scene_b"]), True)
ck("45/30/30", t2["seconds"], [45, 30, 30])

print("\n=== JAVOB (AI O'CHIQ) ===")
r = c.post("/api/student/cefr/speaking/answer", headers=H,
           json={"part": "p11", "idx": 0, "qi": 0, "seconds": 30,
                 "transcript": G.GUIDE["p11"]["sample"]}).json()
ck("ball keldi", 0 <= r["point"] <= 5, True)
ck("AI'siz ham baho", r["from_ai"], False)
ck("namunaviy javob 4 ball", r["point"], 4)
ck("tahlil ro'yxati", len(r["tips"]) >= 3, True)
ck("daraja yorlig'i", bool(r["band_label"]), True)
ck("XP berildi", r["xp"] > 0, True)

r = c.post("/api/student/cefr/speaking/answer", headers=H,
           json={"part": "p11", "idx": 0, "qi": 0, "seconds": 30,
                 "transcript": "I like him. He is good."}).json()
ck("qisqa javob past ball", r["point"] <= 2, True)
lab = {x["label"] for x in r["tips"] if x["ok"] is False}
ck("hajm kamligi aytildi", "Nutq hajmi" in lab, True)

print("\n=== 3-QISM MUVOZANATI ===")
r = c.post("/api/student/cefr/speaking/answer", headers=H,
           json={"part": "p3", "idx": 0, "qi": 0, "seconds": 120,
                 "transcript": G.GUIDE["p3"]["sample"]}).json()
ck("muvozanatli javob 4+", r["point"] >= 4, True)
bal = r["analysis"]["balance"]
ck("ikkala ro'yxat ham ishlatilgan",
   bal["for"] >= 1 and bal["against"] >= 1, True)

print("\n=== BO'SH JAVOB RAD ETILADI ===")
rr = c.post("/api/student/cefr/speaking/answer", headers=H,
            json={"part": "p11", "idx": 0, "qi": 0, "seconds": 30,
                  "transcript": ""})
ck("matnsiz javob 400", rr.status_code, 400)

print("\n=== FREE MOCK ===")
m = c.get("/api/student/cefr/speaking/mock", headers=H).json()
ck("4 vazifa", len(m["tasks"]), 4)
ck("qismlar tartibi", [x["part"] for x in m["tasks"]],
   ["p11", "p12", "p2", "p3"])
ck("jami 10 savol",
   sum(len(x["questions"]) if x["part"] in ("p11", "p12", "p2") else 1
       for x in m["tasks"]), 10)

# a'lo darajadagi javoblar bilan mock
items = []
for t in m["tasks"]:
    key = t["part"]
    n = len(t["questions"]) if key in ("p11", "p12") else 1
    for qi in range(n):
        items.append({"part": key, "idx": t["idx"], "qi": qi,
                      "seconds": t["seconds"][qi] if qi < len(t["seconds"])
                      else t["seconds"][0],
                      "transcript": G.GUIDE[key]["sample"]})
res = c.post("/api/student/cefr/speaking/mock/score", headers=H,
             json={"items": items}).json()
ck("0-75 oralig'ida", 0 <= res["score"] <= 75, True)
ck("4 blok baholandi", len(res["blocks"]), 4)
ck("daraja chiqdi", res["level"] in ("A1", "A2", "B1", "B2", "C1"), True)
ck("xom ball 21 dan", res["raw_max"], 21)
# Namuna javoblar tasodifiy tanlangan mavzuga to'liq mos
# kelmasligi mumkin (masalan do'st haqidagi namuna "kundalik
# tartib" savoliga tushib qolishi), shuning uchun ANIQ darajaga
# emas, NISBIY farqqa qaraymiz — bu ancha ishonchli tekshiruv.
ck("daraja jadvalga mos", F.level_of(res["score"])[0], res["level"])
ck("blok ballari yig'indisi xom ballga teng",
   sum(bl["point"] for bl in res["blocks"]), res["raw"])
ck("xom ball 75 shkalasiga to'g'ri o'girildi",
   res["score"], F.to_scale(res["raw"]))
ck("har blokda izoh", all(bl["why"] for bl in res["blocks"]), True)
ck("tahlil tafsiloti", len(res["detail"]) >= 3, True)

# bo'sh javoblar bilan mock
bosh = [{"part": i["part"], "idx": i["idx"], "qi": i["qi"],
         "seconds": i["seconds"], "transcript": ""} for i in items]
res0 = c.post("/api/student/cefr/speaking/mock/score", headers=H,
              json={"items": bosh}).json()
ck("bo'sh mock 0 ball", res0["score"], 0)
ck("bo'sh mock A1", res0["level"], "A1")

print("\n=== AI ISHLAGANDA UNING BAHOSI USTUN ===")
def _ai_on(system, messages):
    return ("BALL: 5\nKUCHLI: Fikringiz aniq.\n"
            "1) Talaffuzni yaxshilang.\n2) Ko'proq misol keltiring.\n"
            "3) Bog'lovchilarni xilma-xil qiling.\n"
            "YAXSHIROQ: I would argue that ...")


student_app._ai_reply = _ai_on
r = c.post("/api/student/cefr/speaking/answer", headers=H,
           json={"part": "p11", "idx": 1, "qi": 0, "seconds": 30,
                 "transcript": "I like him. He is good."}).json()
ck("AI bahosi olindi", r["from_ai"], True)
ck("AI 5 ball qo'ydi", r["point"], 5)
ck("avtomat baho ham saqlandi", r["auto_point"] <= 2, True)
ck("AI izohi keldi", "KUCHLI" in (r["ai"] or ""), True)

print("\n=== NATIJA BAZADA ===")
n = (db.query(models.SkillAttempt)
     .filter(models.SkillAttempt.skill == "speaking",
             models.SkillAttempt.ref.like("cspmock:%")).count())
ck("mock yozuvlari", n >= 2, True)
d = c.get("/api/student/cefr/speaking/home", headers=H).json()
ck("bosh ekranda mock ro'yxati", len(d["mocks"]) >= 2, True)
ck("eng yaxshi natija = mocklarning eng kattasi",
   d["best"], max(m["score"] for m in d["mocks"]))
ck("to'liq javob bo'sh javobdan yuqori", res["score"] > res0["score"], True)
ck("javoblar sanaldi",
   sum(p["answered"] for p in d["parts"]) >= 3, True)

print("\n" + ("HAMMASI O'TDI" if not fails else "XATO: " + ", ".join(fails)))
sys.exit(1 if fails else 0)
