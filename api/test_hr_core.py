"""HR Faza 2A: bo'limlar, lavozimlar, shtat rejasi, xodim so'rovi,
vakansiya."""
import os, sys
from datetime import date, timedelta

os.environ["DATABASE_URL"] = "sqlite:////tmp/hrcore_test.db"
if os.path.exists("/tmp/hrcore_test.db"):
    os.remove("/tmp/hrcore_test.db")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
import main, models, roles
from database import SessionLocal
from auth import hash_password

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


TODAY = date.today()
db = SessionLocal()
b1 = models.Branch(name="Zafar"); db.add(b1)
b2 = models.Branch(name="Markaz"); db.add(b2)
db.commit()
B1, B2 = b1.id, b2.id

for u, role, br in [("asos", "founder", None), ("hr", "hr_manager", None),
                    ("buxgalter", "accountant", None),
                    ("rahbar", "branch_manager", B1),
                    ("rahbar2", "branch_manager", B2),
                    ("ustoz", "teacher", B1)]:
    db.add(models.User(username=u, password_hash=hash_password("x"),
                       full_name=u.capitalize(), role=role, branch_id=br))
db.commit(); db.close()

H = tok("asos")
HR = tok("hr")
FIN = tok("buxgalter")
BM = tok("rahbar")
BM2 = tok("rahbar2")
HT = tok("ustoz")

print("=== 1. BO'LIM VA LAVOZIM SEED ===")

d = client.get("/api/hr/structure", headers=HR).json()
ck("8 bo'lim", len(d["departments"]), 8)
ck("15 lavozim", len(d["positions"]), 15)

teacher = next(p for p in d["positions"] if p["key"] == "teacher")
ck("ustoz lavozimi rolga bog'landi", teacher["system_role"], "teacher")
ck("sinov darsi majburiy", teacher["trial_required"], True)
ck("sinov muddati", teacher["probation_months"], 2)

buxgalter = next(p for p in d["positions"] if p["key"] == "accountant")
ck("buxgalterga sinov darsi kerak emas",
   buxgalter["trial_required"], False)
ck("bo'limi moliya", buxgalter["department"], "Moliya")

# Seed qayta yozmaydi
r = client.put(f"/api/hr/positions/{teacher['id']}", headers=H,
               json={"probation_months": 3})
ck("lavozim tahrirlandi", r.json()["probation_months"], 3)
dbx = SessionLocal(); main._seed_hr_structure(dbx); dbx.close()
d2 = client.get("/api/hr/structure", headers=HR).json()
t2 = next(p for p in d2["positions"] if p["key"] == "teacher")
ck("qayta seed tahrirni buzmadi", t2["probation_months"], 3)

ck("ustoz tuzilmani ko'rmaydi",
   client.get("/api/hr/structure", headers=HT).status_code, 403)
ck("noma'lum rol rad etildi",
   client.post("/api/hr/positions", headers=H,
               json={"name": "Test", "system_role": "yolgon"}).status_code,
   400)

print("\n=== 2. SHTAT REJASI VA BO'SHLIQ ===")

pos_id = teacher["id"]
r = client.post("/api/hr/workforce", headers=HR, json={
    "year": TODAY.year, "branch_id": B1, "position_id": pos_id,
    "approved_headcount": 5, "planned_hires": 2,
    "budgeted_salary": 15000000})
ck("reja yaratildi", r.status_code, 200)
P1 = r.json()["id"]
ck("hozircha xodim yo'q", r.json()["current_headcount"], 0)
ck("bo'shliq 5", r.json()["gap"], 5)

# Ikkita ustoz qo'shamiz
db = SessionLocal()
for i in range(2):
    db.add(models.User(username=f"u{i}", password_hash=hash_password("x"),
                       full_name=f"Ustoz {i}", role="teacher",
                       branch_id=B1, position="teacher"))
db.commit(); db.close()

d = client.get(f"/api/hr/workforce?year={TODAY.year}", headers=HR).json()
row = next(x for x in d["rows"] if x["id"] == P1)
ck("hozirgi xodim 2", row["current_headcount"], 2)
ck("bo'shliq 3 ga tushdi", row["gap"], 3)
ck("ortiqcha emas", row["over_staffed"], False)

# Shtatdan ko'p bo'lsa
client.put(f"/api/hr/workforce/{P1}", headers=HR,
           json={"approved_headcount": 1})
d = client.get(f"/api/hr/workforce?year={TODAY.year}", headers=HR).json()
row = next(x for x in d["rows"] if x["id"] == P1)
ck("ortiqcha xodim aniqlandi", row["over_staffed"], True)
ck("bo'shliq manfiy", row["gap"], -1)
client.put(f"/api/hr/workforce/{P1}", headers=HR,
           json={"approved_headcount": 5})

ck("HR rejani tasdiqlay olmaydi",
   client.put(f"/api/hr/workforce/{P1}", headers=HR,
              json={"status": "approved"}).status_code, 403)
r = client.put(f"/api/hr/workforce/{P1}", headers=H,
               json={"status": "approved"})
ck("asoschi tasdiqladi", r.json()["status"], "approved")
ck("tasdiq sanasi yozildi", r.json()["approved_at"] is not None, True)

print("\n=== 3. USTOZ YUKLAMASI ===")

db = SessionLocal()
t = models.Teacher(full_name="Yuklangan", branch_id=B1, is_active=1,
                   grade="senior", max_groups=5)
db.add(t); db.commit()
TID = t.id
for i in range(4):
    db.add(models.Group(name=f"G{i}", teacher_id=TID, branch_id=B1))
t2 = models.Teacher(full_name="Bo'sh", branch_id=B1, is_active=1,
                    grade="junior", max_groups=5)
db.add(t2); db.commit()
db.add(models.Group(name="Bitta", teacher_id=t2.id, branch_id=B1))
db.commit(); db.close()

d = client.get("/api/hr/workforce", headers=HR).json()
load = {x["name"]: x for x in d["teacher_load"]}
ck("yuklangan ustoz 4/5", load["Yuklangan"]["groups"], 4)
ck("foizi 80", load["Yuklangan"]["percent"], 80.0)
ck("bandligi", load["Yuklangan"]["band"], "high")
ck("bo'sh ustoz 20%", load["Bo'sh"]["percent"], 20.0)
ck("bo'sh deb belgilandi", load["Bo'sh"]["band"], "low")
ck("bo'sh joylar", d["free_group_slots"], 1 + 4)
ck("darajalar hisoblandi", len(d["load_summary"]), 4)

print("\n=== 4. XODIM SO'ROVI ===")

r = client.post("/api/hr/staff-requests", headers=BM, json={
    "position_id": pos_id, "headcount": 2, "reason": "new_group",
    "priority": "high", "salary_from": 3000000, "salary_to": 5000000,
    "needed_from": (TODAY + timedelta(days=20)).isoformat(),
    "duties": "Ingliz tili darslari"})
ck("so'rov yaratildi", r.status_code, 200)
R1 = r.json()["id"]
ck("raqam berildi", r.json()["public_id"].startswith("REQ-"), True)
ck("filial avtomat qo'yildi", r.json()["branch"], "Zafar")
ck("holati qoralama", r.json()["status"], "draft")
ck("20 kun qoldi", r.json()["days_left"], 20)

# O'rinbosar sabab: kim o'rniga ekani majburiy
r = client.post("/api/hr/staff-requests", headers=BM, json={
    "position_id": pos_id, "reason": "resigned"})
ck("o'rinbosar sababda kim o'rniga so'raladi", r.status_code, 400)
ck("sabab tushuntirildi", "o'rniga" in r.json()["detail"], True)

db = SessionLocal()
leaver = db.query(models.User).filter(models.User.username == "u0").first()
LEAVER = leaver.id
db.close()
r = client.post("/api/hr/staff-requests", headers=BM, json={
    "position_id": pos_id, "reason": "resigned",
    "replacing_user_id": LEAVER})
ck("kim o'rniga ko'rsatilsa o'tdi", r.status_code, 200)
ck("o'rinbosar ko'rinadi", r.json()["replacing"], "Ustoz 0")

print("\n=== 5. TASDIQLASH ZANJIRI ===")

r = client.post(f"/api/hr/staff-requests/{R1}/submit", headers=BM)
ck("yuborildi", r.json()["status"], "submitted")
ck("kim kutayotgani aytildi", len(r.json()["waiting_for"]) > 0, True)

# Buxgalter hali navbatda emas
ck("byudjet navbati kelmadi",
   client.post(f"/api/hr/staff-requests/{R1}/approve", headers=FIN,
               json={}).status_code, 403)

r = client.post(f"/api/hr/staff-requests/{R1}/approve", headers=HR,
                json={"note": "Guruh haqiqatan ochilyapti"})
ck("HR tasdiqladi", r.json()["status"], "hr_review")

r = client.post(f"/api/hr/staff-requests/{R1}/approve", headers=FIN,
                json={"note": "Byudjetda bor"})
ck("byudjet tasdiqladi", r.json()["status"], "budget_review")

ck("HR rahbar bosqichini bosib o'tolmaydi",
   client.post(f"/api/hr/staff-requests/{R1}/approve", headers=HR,
               json={}).status_code, 403)

r = client.post(f"/api/hr/staff-requests/{R1}/approve", headers=H, json={})
ck("rahbar tasdiqladi", r.json()["status"], "approved")
ck("3 qadam tarixda", len(r.json()["approvals"]), 3)
ck("birinchi qadam HR", r.json()["approvals"][0]["step"], "submitted")
ck("izoh saqlandi", r.json()["approvals"][0]["note"],
   "Guruh haqiqatan ochilyapti")
ck("qulflandi", r.json()["locked"], True)

r = client.put(f"/api/hr/staff-requests/{R1}", headers=BM,
               json={"headcount": 9})
ck("tasdiqlangandan keyin tahrirlanmaydi", r.status_code, 400)

print("\n=== 6. RAD ETISH ===")

r = client.post("/api/hr/staff-requests", headers=BM, json={
    "position_id": pos_id, "reason": "workload"})
R2 = r.json()["id"]
client.post(f"/api/hr/staff-requests/{R2}/submit", headers=BM)

r = client.post(f"/api/hr/staff-requests/{R2}/reject", headers=HR,
                json={"reason": ""})
ck("sababsiz rad etilmaydi", r.status_code, 400)

r = client.post(f"/api/hr/staff-requests/{R2}/reject", headers=HR,
                json={"reason": "Hozircha yuklama yetarli"})
ck("rad etildi", r.json()["status"], "rejected")
ck("sabab saqlandi", r.json()["reject_reason"],
   "Hozircha yuklama yetarli")

print("\n=== 7. SO'ROVDAN VAKANSIYA ===")

r = client.post(f"/api/hr/staff-requests/{R2}/convert", headers=HR)
ck("tasdiqlanmagandan vakansiya ochilmaydi", r.status_code, 400)
ck("sabab aytildi", "tasdiqlanmagan" in r.json()["detail"], True)

r = client.post(f"/api/hr/staff-requests/{R1}/convert", headers=HR)
ck("vakansiya ochildi", r.status_code, 200)
V1 = r.json()["id"]
ck("raqam berildi", r.json()["public_id"].startswith("VAC-"), True)
ck("lavozim ko'chdi", r.json()["position"], "O'qituvchi")
ck("nechta odam ko'chdi", r.json()["headcount"], 2)
ck("maosh ko'chdi", r.json()["salary_from"], 3000000)
ck("muhimlik ko'chdi", r.json()["priority"], "high")
ck("sinov darsi kerakligi ko'rindi", r.json()["trial_required"], True)
ck("holati ochiq", r.json()["status"], "open")
ck("so'rovga bog'landi", r.json()["request_id"], R1)

r = client.post(f"/api/hr/staff-requests/{R1}/convert", headers=HR)
ck("ikki marta ochilmaydi", r.status_code, 400)

d = client.get("/api/hr/staff-requests", headers=HR).json()
req = next(x for x in d["rows"] if x["id"] == R1)
ck("so'rov holati yangilandi", req["status"], "converted")

print("\n=== 8. VAKANSIYA MUDDATI ===")

d = client.get("/api/hr/vacancies", headers=HR).json()
v = next(x for x in d["rows"] if x["id"] == V1)
ck("yangi vakansiya kechikmagan", v["overdue"], False)
ck("yuqori muhimlikda 14 kun", v["sla_days"], 14)

db = SessionLocal()
vv = db.query(models.Vacancy).get(V1)
vv.opened_on = TODAY - timedelta(days=20)
db.commit(); db.close()

d = client.get("/api/hr/vacancies", headers=HR).json()
v = next(x for x in d["rows"] if x["id"] == V1)
ck("20 kun ochiq", v["days_open"], 20)
ck("kechikkan deb belgilandi", v["overdue"], True)
ck("umumiy kechikkanlar", d["summary"]["overdue"], 1)
ck("ochiq o'rinlar", d["summary"]["seats"], 2)

print("\n=== 9. VAKANSIYA VORONKASI ===")

db = SessionLocal()
for i, st in enumerate(["applied", "applied", "screening", "interview",
                        "offer", "hired", "rejected"]):
    db.add(models.Candidate(full_name=f"Nomzod {i}", vacancy_id=V1,
                            stage=st, branch_id=B1))
db.commit(); db.close()

r = client.get(f"/api/hr/vacancies/{V1}", headers=HR).json()
ck("7 ta nomzod", r["applications"], 7)
ck("ishga olindi", r["hired"], 1)
ck("rad etildi", r["rejected"], 1)
ck("jarayonda", r["in_progress"], 5)
ck("suhbatga yetganlar", r["interviewed"], 3)
ck("ishga olish foizi", r["hire_rate"], 14.3)

print("\n=== 10. VAKANSIYANI YOPISH ===")

r = client.post(f"/api/hr/vacancies/{V1}/status", headers=HR,
                json={"status": "closed"})
ck("sababsiz yopilmaydi", r.status_code, 400)

r = client.post(f"/api/hr/vacancies/{V1}/status", headers=HR,
                json={"status": "closed", "close_reason": "no_need"})
ck("yopildi", r.json()["status"], "closed")
ck("sabab yozildi", r.json()["close_reason_label"], "Ehtiyoj qolmadi")
ck("yopilgan sana", r.json()["closed_at"], TODAY.isoformat())
ck("endi ochiq emas", r.json()["is_open"], False)
ck("yopilgan vakansiya kechikmaydi", r.json()["overdue"], False)

r = client.post(f"/api/hr/vacancies/{V1}/status", headers=HR,
                json={"status": "open"})
ck("qayta ochildi", r.json()["is_open"], True)
ck("yopilish belgisi tozalandi", r.json()["closed_at"], None)

ck("noma'lum holat rad etildi",
   client.post(f"/api/hr/vacancies/{V1}/status", headers=HR,
               json={"status": "yolgon"}).status_code, 400)

print("\n=== 11. FILIAL CHEGARASI ===")

d = client.get("/api/hr/staff-requests", headers=BM2).json()
ck("boshqa filial so'rovlarini ko'rmaydi", len(d["rows"]), 0)

ck("boshqa filial vakansiyasini ocholmaydi",
   client.get(f"/api/hr/vacancies/{V1}", headers=BM2).status_code, 403)

d = client.get("/api/hr/vacancies", headers=BM).json()
ck("o'z filialini ko'radi", len(d["rows"]) >= 1, True)

ck("ustoz so'rov yubora olmaydi",
   client.post("/api/hr/staff-requests", headers=HT,
               json={"position_id": pos_id}).status_code, 403)
ck("ustoz vakansiya ko'rmaydi",
   client.get("/api/hr/vacancies", headers=HT).status_code, 403)

print("\n=== 12. VAZIFA VA AUDIT ===")

db = SessionLocal()
tasks = db.query(models.Task).filter(
    models.Task.title.like("%REQ-%")).all()
ck("so'rov vazifa yaratdi", len(tasks) >= 1, True)
logs = db.query(models.AuditLog).filter(
    models.AuditLog.entity == "staff_request").all()
ck("audit yozildi", len(logs) >= 4, True)
kinds = {l.action for l in logs}
ck("tasdiq audit qilindi", "approve" in kinds, True)
ck("rad etish audit qilindi", "reject" in kinds, True)
db.close()

print("\n=== 13. MAVJUD TIZIM BUZILMADI ===")

ck("eski vakansiya endpointi ishlaydi",
   client.get("/api/vacancies", headers=H).status_code, 200)
ck("eski nomzodlar ishlaydi",
   client.get("/api/candidates", headers=H).status_code, 200)
ck("HR voronka ishlaydi",
   client.get("/api/hr/dates", headers=HR).status_code, 200)
ck("xodimlar ishlaydi",
   client.get("/api/users", headers=H).status_code, 200)
ck("ustozlar ishlaydi",
   client.get("/api/teachers", headers=H).status_code, 200)

print()
if fails:
    print(f"XATOLAR ({len(fails)}): " + ", ".join(fails))
    sys.exit(1)
print("HAMMASI O'TDI")
