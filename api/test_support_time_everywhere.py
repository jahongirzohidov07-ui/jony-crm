"""SUPPORT SOATI — HAMMA EKRANDA (2026-09-10, ikkinchi bosqich).

Birinchi urinishda faqat "Guruhlarim" (/api/me/groups) tuzatilgan edi.
Jahongir qaytib aytdi: "supportlar yoqlamasi boshqa aytgan muammolar
togrlanmagan deyabdi, haliyam supportlarni oz darsi vaqti emas asosiy
dars vaqti korinyabdi".

SABAB: support kunlik ishini JONY TEACHER ilovasida qiladi —
/api/teacher/today, /week, /home, /lesson/{id}, /support-options.
O'sha ekranlarning HAMMASI vaqtni guruhning asosiy dars vaqtidan
olardi. Endi qoida bitta joyda (common.support_slot_map /
group_time_for) va hamma ekran shundan o'qiydi.

Shu test AYNAN shuni qo'riqlaydi: yangi ekran qo'shilib, yana bir
joyda guruh vaqti sizib chiqmasin.

Tekshiriladi (support uchun):
  A. /api/me/groups            -> o'z vaqti
  B. /api/teacher/today        -> o'z vaqti
  C. /api/teacher/week         -> o'z vaqti
  D. /api/teacher/home         -> o'z vaqti
  E. /api/teacher/lesson/{id}  -> o'z vaqti
  F. /api/teacher/support-options -> o'z vaqti
  G. Ikki guruh — ikki xil vaqt (Apex 12:30, Limitless 16:00)
  H. Guruhning 14:00 i HECH QAYERDA chiqmaydi
  I. Vaqt biriktirilmagan guruhda guruh vaqtiga tushib ketmaydi
  J. ODDIY USTOZDA hammasi avvalgidek — guruh vaqti
"""
import os
import sys
import tempfile
from datetime import timedelta

_DB = os.path.join(tempfile.gettempdir(), "support_time_all_test.db")
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
GROUP_TIME = "14:00"        # ikkala guruhning asosiy dars vaqti
APEX_T = "12:30–13:30"      # support: 2 dan OLDIN
LIM_T = "16:00–17:00"       # support: 2 dan KEYIN

db = SessionLocal()
b = models.Branch(name="Zafar")
db.add(b)
db.commit()
BID = b.id

u_sup = models.User(username="sup", password_hash=hash_password("x"),
                    full_name="Support Ustoz",
                    role=roles.SUPPORT_TEACHER, branch_id=BID)
u_tea = models.User(username="tea", password_hash=hash_password("x"),
                    full_name="Asosiy Ustoz", role=roles.TEACHER,
                    branch_id=BID)
db.add_all([u_sup, u_tea])
db.commit()
t_sup = models.Teacher(full_name="Support Ustoz", branch_id=BID,
                       user_id=u_sup.id)
t_tea = models.Teacher(full_name="Asosiy Ustoz", branch_id=BID,
                       user_id=u_tea.id)
db.add_all([t_sup, t_tea])
db.commit()

apex = models.Group(name="Apex", branch_id=BID, teacher_id=t_tea.id,
                    lesson_days="Du,Cho,Ju", lesson_time=GROUP_TIME)
lim = models.Group(name="Limitless", branch_id=BID, teacher_id=t_tea.id,
                   lesson_days="Du,Cho,Ju", lesson_time=GROUP_TIME)
noslot = models.Group(name="Vaqtsiz", branch_id=BID, teacher_id=t_tea.id,
                      lesson_days="Se,Pa", lesson_time="18:00")
db.add_all([apex, lim, noslot])
db.commit()
APEX, LIM, NOSLOT = apex.id, lim.id, noslot.id

db.add_all([
    models.SupportAssignment(user_id=u_sup.id, group_id=APEX,
                             days="Se,Pa", start="12:30", end="13:30"),
    models.SupportAssignment(user_id=u_sup.id, group_id=LIM,
                             days="Se,Pa", start="16:00", end="17:00"),
    models.SupportAssignment(user_id=u_sup.id, group_id=NOSLOT),
])
db.commit()

for nm, gid in [("Aliyev", APEX), ("Boboyev", LIM), ("Valiyev", NOSLOT)]:
    db.add(models.Student(full_name=nm, branch_id=BID, group_id=gid,
                          status="active",
                          enrolled_date=TODAY - timedelta(days=60)))
db.commit()

# Bugungi darslar — Jony Teacher ilovasining "Bugun" ekrani uchun
LES = {}
for gid in (APEX, LIM, NOSLOT):
    ls = models.Lesson(group_id=gid, date=TODAY, held=0)
    db.add(ls)
    db.commit()
    LES[gid] = ls.id
db.close()

Hs = tok("sup")
Ht = tok("tea")


def times_in(obj):
    """Javobdagi HAMMA "time" qiymatini yig'adi (ichma-ich qidiradi)."""
    out = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k in ("time", "lesson_time") and isinstance(v, str):
                out.append(v)
            else:
                out += times_in(v)
    elif isinstance(obj, list):
        for x in obj:
            out += times_in(x)
    return out


print("=== A. /api/me/groups (Guruhlarim) ===")
d = client.get("/api/me/groups", headers=Hs).json()
rows = {r["name"]: r for r in d["rows"]}
ck("Apex", rows["Apex"]["time"], APEX_T)
ck("Limitless", rows["Limitless"]["time"], LIM_T)

print("\n=== B. /api/teacher/today (Jony Teacher — Bugun) ===")
d = client.get("/api/teacher/today", headers=Hs).json()
by_g = {l["group"]: l for l in d["lessons"]}
ck("Apex darsi", by_g["Apex"]["time"], APEX_T)
ck("Limitless darsi", by_g["Limitless"]["time"], LIM_T)
ck("manba support", by_g["Apex"]["time_source"], "support")
ck("guruh vaqti sizmadi", GROUP_TIME in times_in(d), False)

print("\n=== C. /api/teacher/week (Jadval) ===")
d = client.get("/api/teacher/week", headers=Hs).json()
week_times = set(times_in(d))
ck("o'z vaqtlari bor", {APEX_T, LIM_T} <= week_times, True)
ck("guruh vaqti sizmadi", GROUP_TIME in week_times, False)

print("\n=== D. /api/teacher/home (Bosh ekran) ===")
d = client.get("/api/teacher/home", headers=Hs).json()
home_times = set(times_in(d))
ck("o'z vaqtlari bor", {APEX_T, LIM_T} <= home_times, True)
ck("guruh vaqti sizmadi", GROUP_TIME in home_times, False)

print("\n=== E. /api/teacher/lesson/{id} (Yo'qlama ekrani) ===")
d = client.get(f"/api/teacher/lesson/{LES[APEX]}", headers=Hs).json()
ck("Apex yo'qlama ekrani", d["time"], APEX_T)
d2 = client.get(f"/api/teacher/lesson/{LES[LIM]}", headers=Hs).json()
ck("Limitless yo'qlama ekrani", d2["time"], LIM_T)

print("\n=== F. /api/teacher/support-options (Seans qo'shish) ===")
d = client.get("/api/teacher/support-options", headers=Hs).json()
so = {g["name"]: g["lesson_time"] for g in d["groups"]}
ck("Apex", so["Apex"], APEX_T)
ck("Limitless", so["Limitless"], LIM_T)
ck("guruh vaqti sizmadi", GROUP_TIME in times_in(d), False)

print("\n=== G. IKKI GURUH — IKKI XIL VAQT ===")
ck("bir xil emas", APEX_T == LIM_T, False)
ck("biri 2dan oldin", APEX_T < GROUP_TIME, True)
ck("ikkinchisi 2dan keyin", LIM_T > GROUP_TIME, True)

print("\n=== I. VAQT BIRIKTIRILMAGAN GURUH ===")
d = client.get("/api/me/groups", headers=Hs).json()
vs = {r["name"]: r for r in d["rows"]}["Vaqtsiz"]
ck("guruh vaqti (18:00) tushib ketmadi", vs["time"], None)
ck("izoh chiqadi", bool(vs["time_note"]), True)
d = client.get("/api/teacher/today", headers=Hs).json()
vl = {l["group"]: l for l in d["lessons"]}["Vaqtsiz"]
ck("ilovada ham bo'sh", vl["time"], None)
ck("ilovada ham izoh", bool(vl["time_note"]), True)

print("\n=== J. ODDIY USTOZDA HECH NARSA O'ZGARMADI ===")
d = client.get("/api/me/groups", headers=Ht).json()
tr = {r["name"]: r for r in d["rows"]}
ck("Apex — guruh vaqti", tr["Apex"]["time"], GROUP_TIME)
ck("manba group", tr["Apex"]["time_source"], "group")
d = client.get("/api/teacher/today", headers=Ht).json()
tl = {l["group"]: l for l in d["lessons"]}
ck("ilovada ham guruh vaqti", tl["Apex"]["time"], GROUP_TIME)
ck("ustozda izoh yo'q", tl["Apex"]["time_note"], None)
d = client.get(f"/api/teacher/lesson/{LES[APEX]}", headers=Ht).json()
ck("yo'qlama ekranida guruh vaqti", d["time"], GROUP_TIME)
d = client.get("/api/teacher/support-options", headers=Ht).json()
ck("seans tanlovida guruh vaqti",
   {g["name"]: g["lesson_time"] for g in d["groups"]}["Apex"], GROUP_TIME)

print("\n=== K. QOIDA BITTA JOYDA (yangi ekran unutilmasin) ===")
common = open(os.path.join(HERE, "common.py"), encoding="utf-8").read()
ck("support_slot_map common.py da", "def support_slot_map" in common, True)
ck("group_time_for common.py da", "def group_time_for" in common, True)
ta = open(os.path.join(HERE, "teacher_app.py"), encoding="utf-8").read()
ck("teacher_app g.lesson_time ni to'g'ridan-to'g'ri ishlatmaydi",
   "g.lesson_time" in ta.replace("models.Group.lesson_time", ""), False)

print("\n" + ("BARCHASI OK" if not fails else f"XATOLAR: {fails}"))
sys.exit(1 if fails else 0)
