"""SUPPORT: O'Z SOATI VA TOZA YO'QLAMA (2026-09-10).

Jahongir (skrinshot bilan):
  1) "Supportlarga asosiy dars vaqti korinyabdi men belgilagan support
     soati emas, yani o'zlari otadigan soat emas";
  2) "Birinchi ikkinchi guruh bir vaqtdrk ko'rinyabdi aslida bittasi
     2dan avval 2dan keyin ikkinchisi";
  3) "Ustoz supportlarda muzlatilgan arxiv o'quvchilaram yo'qlamada
     chiqib turibdi filtrlanmayabdi".
Aniqlashtirdi: "support darslarni menejer biriktirgan shundan tortvol
malumot" — ya'ni manba SupportAssignment (days/start/end).

Tekshiriladi:
  A. Support kabinetida guruh kartasi GURUH dars vaqtini emas,
     BIRIKTIRUVDAGI vaqtni ko'rsatadi;
  B. Ikki guruh — ikki xil vaqt (ikkalasi ham 14:00 bo'lib qolmaydi);
  C. Biriktiruvda vaqt yo'q bo'lsa — guruh vaqtiga "tushib ketmaydi",
     ochiq izoh chiqadi;
  D. Oddiy USTOZ uchun hech narsa o'zgarmagan — guruh vaqti o'z joyida;
  E. Support yo'qlamasida muzlatilgan, arxiv va ketgan o'quvchi
     ro'yxatda turmaydi — faol o'quvchilar qoladi;
  F. Ular bazadan O'CHIRILMAGAN (hech narsa o'chirilmaydi qoidasi);
  G. Frontend haqiqatda shu maydonlarni ishlatyapti.
"""
import os
import sys
import tempfile
from datetime import date, timedelta

_DB = os.path.join(tempfile.gettempdir(), "support_slot_test.db")
os.environ["DATABASE_URL"] = "sqlite:///" + _DB.replace("\\", "/")
if os.path.exists(_DB):
    os.remove(_DB)
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

from fastapi.testclient import TestClient          # noqa: E402
import main, models, roles                          # noqa: E402
import entry  # noqa: F401,E402
from database import SessionLocal                   # noqa: E402
from auth import hash_password                      # noqa: E402

client = TestClient(main.app)
fails = []


def ck(name, got, want):
    ok = got == want
    print(("OK  " if ok else "XATO ") + name + f": {got}"
          + ("" if ok else f"   (kutilgan {want})"))
    if not ok:
        fails.append(name)


def tok(u, p="x"):
    return {"Authorization": "Bearer " + client.post(
        "/api/auth/login", json={"username": u, "password": p}
    ).json()["access_token"]}


TODAY = roles.local_today()

# ---------------------------------------------------------------
#  MA'LUMOT
# ---------------------------------------------------------------
db = SessionLocal()
b = models.Branch(name="Zafar")
db.add(b)
db.commit()

u_sup = models.User(username="sup", password_hash=hash_password("x"),
                    full_name="Support Ustoz",
                    role=roles.SUPPORT_TEACHER, branch_id=b.id)
u_tea = models.User(username="tea", password_hash=hash_password("x"),
                    full_name="Asosiy Ustoz", role=roles.TEACHER,
                    branch_id=b.id)
db.add_all([u_sup, u_tea])
db.commit()

t_sup = models.Teacher(full_name="Support Ustoz", branch_id=b.id,
                       user_id=u_sup.id)
t_tea = models.Teacher(full_name="Asosiy Ustoz", branch_id=b.id,
                       user_id=u_tea.id)
db.add_all([t_sup, t_tea])
db.commit()

# Ikkala guruh ham asosiy darsni 14:00 da o'tadi — skrinshotdagi holat
apex = models.Group(name="Apex", branch_id=b.id, teacher_id=t_tea.id,
                    lesson_days="Du,Cho,Ju", lesson_time="14:00")
limitless = models.Group(name="Limitless", branch_id=b.id,
                         teacher_id=t_tea.id,
                         lesson_days="Du,Cho,Ju", lesson_time="14:00")
noslot = models.Group(name="Vaqtsiz", branch_id=b.id,
                      teacher_id=t_tea.id,
                      lesson_days="Se,Pa", lesson_time="18:00")
db.add_all([apex, limitless, noslot])
db.commit()
APEX_ID = apex.id      # sessiya yopilgach ham ishlatamiz

# Support menejer biriktirdi: biri 2 dan OLDIN, biri 2 dan KEYIN
db.add_all([
    models.SupportAssignment(user_id=u_sup.id, group_id=apex.id,
                             days="Se,Pa", start="12:30", end="13:30",
                             created_by="Support Menejer"),
    models.SupportAssignment(user_id=u_sup.id, group_id=limitless.id,
                             days="Se,Pa", start="16:00", end="17:00",
                             created_by="Support Menejer"),
    # Vaqti hali qo'yilmagan biriktiruv
    models.SupportAssignment(user_id=u_sup.id, group_id=noslot.id,
                             created_by="Support Menejer"),
])
db.commit()

# O'quvchilar: 2 faol + muzlatilgan + arxiv + ketgan
S = {}
for nm, st in [("Faol Birinchi", "active"), ("Faol Ikkinchi", "active"),
               ("Muzlatilgan Aliyev", "frozen"),
               ("Arxiv Boboyev", "archived"),
               ("Ketgan Valiyev", "left")]:
    s = models.Student(full_name=nm, branch_id=b.id, group_id=APEX_ID,
                       status=st, enrolled_date=TODAY - timedelta(days=60))
    db.add(s)
    db.commit()
    S[nm] = s.id
db.close()

Hs = tok("sup")
Ht = tok("tea")

# ---------------------------------------------------------------
print("=== 1. SUPPORT KARTASIDA — BIRIKTIRUVDAGI VAQT ===")
d = client.get("/api/me/groups", headers=Hs).json()
rows = {r["name"]: r for r in d["rows"]}
ck("3 ta guruh biriktirilgan", sorted(rows), ["Apex", "Limitless", "Vaqtsiz"])
ck("Apex vaqti — supportniki", rows["Apex"]["time"], "12:30–13:30")
ck("Apex kunlari — supportniki", rows["Apex"]["days"], "Se,Pa")
ck("Apex GURUH vaqti EMAS", rows["Apex"]["time"] == "14:00", False)
ck("manba support deb belgilangan", rows["Apex"]["time_source"], "support")

print("\n=== 2. IKKI GURUH — IKKI XIL VAQT ===")
ck("Limitless vaqti", rows["Limitless"]["time"], "16:00–17:00")
ck("bir xil ko'rinmaydi",
   rows["Apex"]["time"] == rows["Limitless"]["time"], False)
ck("biri 2dan oldin", rows["Apex"]["time"] < "14:00", True)
ck("ikkinchisi 2dan keyin", rows["Limitless"]["time"] > "14:00", True)

print("\n=== 3. VAQT BIRIKTIRILMAGAN BO'LSA ===")
ck("guruh vaqtiga tushib ketmaydi", rows["Vaqtsiz"]["time"], None)
ck("kuni ham guruhnikini olmaydi", rows["Vaqtsiz"]["days"], None)
ck("izoh chiqadi", bool(rows["Vaqtsiz"]["time_note"]), True)

print("\n=== 4. ODDIY USTOZDA HECH NARSA O'ZGARMADI ===")
dt = client.get("/api/me/groups", headers=Ht).json()
rt = {r["name"]: r for r in dt["rows"]}
ck("Apex — guruh vaqti", rt["Apex"]["time"], "14:00")
ck("Apex — guruh kunlari", rt["Apex"]["days"], "Du,Cho,Ju")
ck("manba group", rt["Apex"]["time_source"], "group")
ck("izoh yo'q", rt["Apex"]["time_note"], None)

print("\n=== 5. SUPPORT YO'QLAMASI — FAQAT FAOLLAR ===")
gr = client.get(f"/api/groups/{APEX_ID}/support-attendance"
                f"?year={TODAY.year}&month={TODAY.month}",
                headers=Hs).json()
names = sorted(x["full_name"] for x in gr["students"])
ck("faqat 2 ta faol", names, ["Faol Birinchi", "Faol Ikkinchi"])
ck("muzlatilgan yo'q", any("Muzlatilgan" in n for n in names), False)
ck("arxiv yo'q", any("Arxiv" in n for n in names), False)
ck("ketgan yo'q", any("Ketgan" in n for n in names), False)

print("\n=== 6. RAHBARIYATGA HAM SHUNDAY (yo'qlama = ish haqi hujjati) ===")
db = SessionLocal()
db.add(models.User(username="asos", password_hash=hash_password("x"),
                   full_name="Asoschi", role="founder"))
db.commit()
db.close()
Ha = tok("asos")
gr2 = client.get(f"/api/groups/{APEX_ID}/support-attendance"
                 f"?year={TODAY.year}&month={TODAY.month}",
                 headers=Ha).json()
ck("asoschida ham faqat faollar",
   sorted(x["full_name"] for x in gr2["students"]),
   ["Faol Birinchi", "Faol Ikkinchi"])

print("\n=== 7. HECH NARSA O'CHIRILMADI ===")
db = SessionLocal()
ck("5 ta o'quvchi bazada turibdi",
   db.query(models.Student).filter(
       models.Student.group_id == APEX_ID).count(), 5)
ck("muzlatilgan holati saqlangan",
   db.query(models.Student).get(S["Muzlatilgan Aliyev"]).status, "frozen")
ck("arxiv holati saqlangan",
   db.query(models.Student).get(S["Arxiv Boboyev"]).status, "archived")
ck("biriktiruvlar joyida",
   db.query(models.SupportAssignment).count(), 3)
db.close()

print("\n=== 8. FRONTEND SHU MAYDONLARNI ISHLATYAPTIMI ===")
tsx = open(os.path.join(ROOT, "src", "pages", "MyGroups.tsx"),
           encoding="utf-8").read()
ck("time_note ko'rsatiladi", "g.time_note" in tsx, True)
ck("time_source tekshiriladi", 'g.time_source === "support"' in tsx, True)
api_ts = open(os.path.join(ROOT, "src", "lib", "api.ts"),
              encoding="utf-8").read()
ck("MyGroup tipida time_source bor", "time_source?:" in api_ts, True)
ck("MyGroup tipida time_note bor", "time_note?:" in api_ts, True)

print("\n" + ("BARCHASI OK" if not fails else f"XATOLAR: {fails}"))
sys.exit(1 if fails else 0)
