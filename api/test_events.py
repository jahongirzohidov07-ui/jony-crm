"""EVENT MENEJER: lavozim, tug'ilgan kunlar va tadbirlar (2026-09-14).

Jahongir: "event manager degan lavozim qoshib qoygin eventlarni tashkil
qilish tugilgan kunlar avtomat korinib turishi kerak".

Tekshiriladi:
  1. Lavozim ikki tomonda (roles.py va roles.ts) bir xil e'lon qilingan;
  2. Tug'ilgan kunlar AVTOMAT chiqadi: o'quvchi va xodim, eng yaqini
     birinchi, arxivdagi va juda uzoqdagi chiqmaydi;
  3. Filial chegarasi: filial rahbari boshqa filial o'quvchisini ko'rmaydi;
  4. Ruxsatlar: ustoz kirolmaydi, HR ko'radi-yu yaratolmaydi;
  5. Tadbir yaratish, tahrirlash, o'chirish va noto'g'ri ma'lumot.
"""
import os
import sys
import tempfile
from datetime import date, timedelta

_DIR = os.path.join(tempfile.gettempdir(), "events_test")
os.makedirs(_DIR, exist_ok=True)
_DB = os.path.join(_DIR, "db.sqlite")
os.environ["DATABASE_URL"] = "sqlite:///" + _DB.replace(chr(92), "/")
if os.path.exists(_DB):
    os.remove(_DB)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient          # noqa: E402
import main, models, roles                         # noqa: E402
from database import SessionLocal                  # noqa: E402
from auth import hash_password                     # noqa: E402

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


def born(days_ahead, years):
    """Tug'ilgan kuni bugundan `days_ahead` kun keyin keladigan sana."""
    d = date.today() + timedelta(days=days_ahead)
    try:
        return d.replace(year=d.year - years)
    except ValueError:                      # 29-fevral
        return d.replace(year=d.year - years, day=28)


print("=== 1. LAVOZIM IKKI TOMONDA BIR XIL ===")
ck("roles.py da bor", roles.EVENT_MANAGER in roles.ALL_ROLES, True)
ck("nomi o'zbekcha", roles.UZ_LABELS.get("event_manager"), "Event menejer (tadbirlar)")
ck("HR tayinlay oladi", roles.EVENT_MANAGER in roles.HR_ASSIGNABLE_ROLES, True)
ck("butun tashkilotni ko'radi", roles.EVENT_MANAGER in roles.ORG_WIDE_ROLES, True)
ts = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src", "lib", "roles.ts"),
          encoding="utf-8").read()
ck("roles.ts da e'lon qilingan", 'export const EVENT_MANAGER = "event_manager";' in ts, True)
ck("roles.ts ALL_ROLES ichida", "FACILITY_MANAGER, EVENT_MANAGER," in ts, True)
ck("ruxsatlar matritsasida bo'lim bor", "events" in roles.RESOURCE_KEYS, True)

db = SessionLocal()
b1 = models.Branch(name="Markaz"); db.add(b1)
b2 = models.Branch(name="Zafar"); db.add(b2)
db.commit()
B1, B2 = b1.id, b2.id

for u, role, br, bd in [("asos", "founder", None, None),
                        ("event", "event_manager", None, born(3, 27)),
                        ("hr", "hr_manager", None, None),
                        ("rahbar", "branch_manager", B1, None),
                        ("ustoz", "teacher", B1, None)]:
    db.add(models.User(username=u, password_hash=hash_password("x"), full_name=u.capitalize(),
                       role=role, branch_id=br, phone="998900000000", birth_date=bd))
db.commit()

for name, br, status, bd in [("Bugun Tugilgan", B1, "active", born(0, 12)),
                             ("Onkun Keyin", B2, "active", born(10, 15)),
                             ("Arxivdagi", B1, "archived", born(0, 14)),
                             ("Sanasiz", B1, "active", None),
                             ("Uzoqdagi", B1, "active", born(100, 16))]:
    db.add(models.Student(full_name=name, branch_id=br, status=status, birth_date=bd))
db.commit()
db.close()

H, EV, HR, BM, T = tok("asos"), tok("event"), tok("hr"), tok("rahbar"), tok("ustoz")

print("\n=== 2. TUG'ILGAN KUNLAR AVTOMAT ===")
r = client.get("/api/events/birthdays?days=30", headers=EV)
ck("event menejer ochadi", r.status_code, 200)
d = r.json()
names = [x["full_name"] for x in d["rows"]]
ck("bugungi o'quvchi birinchi", names[:1], ["Bugun Tugilgan"])
ck("bugun belgisi", d["rows"][0]["today"], True)
ck("yoshi to'g'ri", d["rows"][0]["age"], 12)
ck("10 kundan keyingi o'quvchi bor", "Onkun Keyin" in names, True)
ck("xodimning tug'ilgan kuni ham chiqadi", "Event" in names, True)
ck("arxivdagi chiqmaydi", "Arxivdagi" in names, False)
ck("30 kundan uzoq chiqmaydi", "Uzoqdagi" in names, False)
ck("bugun soni", d["today"], 1)
ck("sanasi yo'q o'quvchi sanaladi", d["missing_students"], 1)
r = client.get("/api/events/birthdays?days=120", headers=EV)
ck("120 kunda uzoqdagi ham chiqadi", "Uzoqdagi" in [x["full_name"] for x in r.json()["rows"]], True)

print("\n=== 3. FILIAL CHEGARASI ===")
r = client.get("/api/events/birthdays?days=30", headers=BM)
ck("filial rahbari ochadi", r.status_code, 200)
bm_names = [x["full_name"] for x in r.json()["rows"]]
ck("o'z filiali ko'rinadi", "Bugun Tugilgan" in bm_names, True)
ck("boshqa filial ko'rinmaydi", "Onkun Keyin" in bm_names, False)

print("\n=== 4. RUXSATLAR ===")
ck("ustoz tug'ilgan kunlarni ocholmaydi", client.get("/api/events/birthdays", headers=T).status_code, 403)
ck("ustoz tadbirlarni ocholmaydi", client.get("/api/events", headers=T).status_code, 403)
ck("HR ko'radi", client.get("/api/events", headers=HR).status_code, 200)
ck("HR boshqara olmaydi (can_manage)", client.get("/api/events", headers=HR).json()["can_manage"], False)
good = {"title": "Mustaqillik kuni", "kind": "holiday",
        "event_date": (date.today() + timedelta(days=14)).isoformat(),
        "start_time": "17:00", "place": "Markaz zal", "budget": 1500000, "status": "planned"}
ck("HR yaratolmaydi", client.post("/api/events", headers=HR, json=good).status_code, 403)
ck("event menejer boshqaradi (can_manage)", client.get("/api/events", headers=EV).json()["can_manage"], True)
r = client.get("/api/permissions", headers=H)
ck("matritsada lavozim chiqadi", "event_manager" in [x["key"] for x in r.json()["roles"]], True)

print("\n=== 5. TADBIRLAR ===")
r = client.post("/api/events", headers=EV, json=good)
ck("yaratildi", r.status_code, 200)
eid = r.json().get("id")
ck("holat nomi", r.json().get("status_label"), "Rejada")
ck("tur nomi", r.json().get("kind_label"), "Bayram")
ck("nomsiz — rad", client.post("/api/events", headers=EV, json={**good, "title": " "}).status_code, 400)
ck("noto'g'ri sana — rad", client.post("/api/events", headers=EV, json={**good, "event_date": "20-sentabr"}).status_code, 400)
ck("noto'g'ri vaqt — rad", client.post("/api/events", headers=EV, json={**good, "start_time": "25:00"}).status_code, 400)
ck("manfiy byudjet — rad", client.post("/api/events", headers=EV, json={**good, "budget": -5}).status_code, 400)
r = client.put(f"/api/events/{eid}", headers=EV, json={**good, "status": "done"})
ck("tahrirlandi", r.status_code, 200)
ck("holat yangilandi", r.json().get("status"), "done")
ck("ustoz tahrirlay olmaydi", client.put(f"/api/events/{eid}", headers=T, json=good).status_code, 403)
ck("ro'yxatda 1 ta", len(client.get("/api/events", headers=EV).json()["rows"]), 1)
ck("o'chirildi", client.delete(f"/api/events/{eid}", headers=EV).status_code, 200)
ck("ro'yxat bo'sh", len(client.get("/api/events", headers=EV).json()["rows"]), 0)
ck("yo'q tadbir — 404", client.delete(f"/api/events/{eid}", headers=EV).status_code, 404)

print()
if fails:
    print(f"XATOLAR ({len(fails)}): " + ", ".join(fails))
    sys.exit(1)
print("HAMMASI O'TDI")
