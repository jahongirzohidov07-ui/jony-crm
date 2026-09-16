"""JARIMA BALLARI (2026-09-16, Jahongir: "examinerlar boshlig'i uchun
examinerlardan ayirish, HR uchun ham examiner ham supportlardan ayirish
uchun jarima ball bo'limi").

Tekshiriladi:
  - HR supportdan ball ayiradi, ball oylikka aylanishidan OLDIN chegiriladi;
  - examinerlar boshlig'i supportga tegolmaydi, examinerdan ayiradi;
  - filial rahbari umuman ayirolmaydi;
  - sababsiz / kelajak sanaga / supportga tegishli bo'lmagan jarima yo'q;
  - xato jarimani bekor qilsa, ball qaytadi."""
import os, sys, tempfile
from datetime import timedelta

_tmp = tempfile.mkdtemp(prefix="jony_penalty_")
os.environ["DATABASE_URL"] = "sqlite:///" + os.path.join(
    _tmp, "db.sqlite").replace("\\", "/")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
import main, models, roles
import entry  # noqa
from database import SessionLocal
from auth import hash_password

c = TestClient(main.app)
db = SessionLocal()
fails = []


def ck(n, g, w):
    ok = g == w
    print(("OK  " if ok else "XATO ") + f"{n}: {g}"
          + ("" if ok else f"  (kutilgan {w})"))
    if not ok:
        fails.append(n)


b = models.Branch(name="Zafar"); db.add(b); db.commit()


def mk(username, role):
    u = models.User(username=username, full_name=username.title(),
                    password_hash=hash_password("Parol123!"),
                    role=role, branch_id=b.id, is_active=1)
    db.add(u); db.commit()
    return u


def login(username):
    r = c.post("/api/auth/login",
               json={"username": username, "password": "Parol123!"})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


hr = mk("hr", roles.HR_MANAGER)
hx = mk("boshliq", roles.HEAD_EXAMINER)
bm = mk("rahbar", roles.BRANCH_MANAGER)
ex = mk("examiner", roles.EXAMINER)
su = mk("support", roles.SUPPORT_TEACHER)
t = models.Teacher(full_name="Support", branch_id=b.id, user_id=su.id,
                   is_active=1)
db.add(t); db.commit()

# 20 seans x 3 soat x 8 o'quvchi: 18 + 32 + 0.25 = 50.25 ball
today = roles.local_today()
start = today.replace(day=1)
for i in range(20):
    db.add(models.SupportSession(
        teacher_id=t.id, branch_id=b.id, date=start,
        start_time="10:00", end_time="13:00", minutes=180,
        students_count=8))
db.commit()

H_HR, H_HX, H_BM = login("hr"), login("boshliq"), login("rahbar")


def su_row(h):
    r = c.get("/api/support/salary", headers=h)
    ck("support ro'yxati 200", r.status_code, 200)
    return r.json(), next(x for x in r.json()["rows"]
                          if x["user_id"] == su.id)


print("=== JARIMASIZ ===")
d, row = su_row(H_HR)
ck("sof ball", row["points"], 50.25)
ck("HR ayira oladi (bayroq)", d["can_penalize"], True)
ck("oylik (darajagacha)", row["salary_base"], 502500)

print("\n=== HR SUPPORTDAN AYIRADI ===")
r = c.post("/api/support-adjustments", headers=H_HR,
           json={"user_id": su.id, "points": 5, "reason": "Darsga kechikdi"})
ck("qo'shildi", r.status_code, 200)
adj_id = r.json()["id"]
d, row = su_row(H_HR)
ck("yig'ilgan ball o'zgarmadi", row["gross_points"], 50.25)
ck("jarima", row["adjustment_points"], 5)
ck("sof ball kamaydi", row["points"], 45.25)
ck("oylik kamaydi", row["salary_base"], 452500)
ck("jarima ro'yxatda", [a["reason"] for a in row["adjustments"]],
   ["Darsga kechikdi"])

print("\n=== TEKSHIRUVLAR ===")
r = c.post("/api/support-adjustments", headers=H_HR,
           json={"user_id": su.id, "points": 5, "reason": "  "})
ck("sababsiz rad", r.status_code, 400)
r = c.post("/api/support-adjustments", headers=H_HR,
           json={"user_id": su.id, "points": 5, "reason": "x",
                 "date": (today + timedelta(days=1)).isoformat()})
ck("kelajak sana rad", r.status_code, 400)
r = c.post("/api/support-adjustments", headers=H_HR,
           json={"user_id": ex.id, "points": 5, "reason": "x"})
ck("examinerga support jarimasi yo'q", r.status_code, 404)
r = c.post("/api/support-adjustments", headers=H_HX,
           json={"user_id": su.id, "points": 5, "reason": "x"})
ck("examinerlar boshlig'i supportga tegolmaydi", r.status_code, 403)
r = c.post("/api/support-adjustments", headers=H_BM,
           json={"user_id": su.id, "points": 5, "reason": "x"})
ck("filial rahbari ayirolmaydi", r.status_code, 403)

print("\n=== SUPPORT O'Z OYLIGIDA KO'RADI ===")
r = c.get("/api/me/support-sessions", headers=login("support"))
ck("o'z sahifasi 200", r.status_code, 200)
ck("jarima ko'rinadi", r.json()["adjustment_points"], 5)
ck("formulada jarima", "− 5.0 jarima" in r.json()["formula"], True)

print("\n=== BEKOR QILISH ===")
r = c.delete(f"/api/support-adjustments/{adj_id}", headers=H_BM)
ck("filial rahbari bekor qilolmaydi", r.status_code, 403)
r = c.delete(f"/api/support-adjustments/{adj_id}", headers=H_HR)
ck("HR bekor qildi", r.status_code, 200)
d, row = su_row(H_HR)
ck("ball qaytdi", row["points"], 50.25)

print("\n=== EXAMINERLAR BOSHLIG'I EXAMINERDAN AYIRADI ===")
r = c.post("/api/examiner-adjustments", headers=H_HX,
           json={"user_id": ex.id, "points": 3, "reason": "Hisobot kech"})
ck("qo'shildi", r.status_code, 200)
ex_adj = r.json()["id"]
r = c.get("/api/examiners/salary", headers=H_HX)
ck("ro'yxat 200", r.status_code, 200)
erow = next(x for x in r.json()["rows"] if x["user_id"] == ex.id)
ck("jarima", erow["adjustment_points"], 3)
r = c.post("/api/examiner-adjustments", headers=H_HR,
           json={"user_id": ex.id, "points": 2, "reason": "HR ham"})
ck("HR ham examinerdan ayiradi", r.status_code, 200)
r = c.delete(f"/api/examiner-adjustments/{ex_adj}", headers=H_BM)
ck("filial rahbari bekor qilolmaydi", r.status_code, 403)
r = c.delete(f"/api/examiner-adjustments/{ex_adj}", headers=H_HX)
ck("boshliq bekor qildi", r.status_code, 200)
r = c.get("/api/examiners/salary", headers=H_HX)
erow = next(x for x in r.json()["rows"] if x["user_id"] == ex.id)
ck("faqat HR jarimasi qoldi", erow["adjustment_points"], 2)

print()
if fails:
    print("XATOLAR:", fails)
    sys.exit(1)
print("HAMMASI O'TDI")
