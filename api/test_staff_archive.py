"""KETGANLAR ARXIVI HR DA (2026-09-24).

Jahongir: "hr ga xodimlar arxivini ochib ber, ishdan ketgan nega
ketgan hammasi bo'lsin".

Tekshiriladi:
  A. HR ro'yxatni ko'radi: hisobi yopilgan xodimlar ham, hisobsiz
     ustoz kartalari ham. Ishlayotganlar ro'yxatda yo'q;
  B. Har qatorda NEGA ketgani bor — ketish jarayonidagi sabab,
     chiqish suhbati, qancha ishlagani;
  C. Sababi yozilmaganlar sanaladi va HR uni to'ldira oladi;
  D. To'ldirilgan sabab HR hisobotiga ham tushadi (bitta manba);
  E. Begona rol (sotuv menejeri) arxivni ocha olmaydi.
"""
import os
import sys
import tempfile
from datetime import timedelta

_DB = os.path.join(tempfile.gettempdir(), "staff_archive_test.db")
os.environ["DATABASE_URL"] = "sqlite:///" + _DB.replace("\\", "/")
if os.path.exists(_DB):
    os.remove(_DB)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient          # noqa: E402
import main, models, roles                         # noqa: E402
import entry  # noqa: F401,E402
from database import SessionLocal                  # noqa: E402
from auth import hash_password                     # noqa: E402

client = TestClient(main.app)
fails = []


def ck(name, got, want):
    ok = got == want
    print(("OK  " if ok else "XATO ") + f"{name}: {got}"
          + ("" if ok else f"   (kutilgan {want})"))
    if not ok:
        fails.append(name)


def tok(u):
    return {"Authorization": "Bearer " + client.post(
        "/api/auth/login",
        json={"username": u, "password": "Parol123!"}
    ).json()["access_token"]}


TODAY = roles.local_today()

db = SessionLocal()
b = models.Branch(name="Zafar")
db.add(b)
db.commit()
BID = b.id
ids = {}
for un, nm, role, active in [
        ("asos", "Asoschi", roles.FOUNDER, 1),
        ("hr", "HR Nodira", roles.HR_MANAGER, 1),
        ("sot", "Sotuvchi Sardor", roles.SALES_MANAGER, 1),
        ("ketgan1", "Ketgan Anvar", roles.TEACHER, 0),
        ("ketgan2", "Ketgan Bobur", roles.SUPPORT_TEACHER, 0),
        ("ishlaydi", "Ishlayotgan Dilnoza", roles.TEACHER, 1)]:
    u = models.User(username=un, full_name=nm,
                    password_hash=hash_password("Parol123!"),
                    role=role, branch_id=BID, is_active=active,
                    hired_date=TODAY - timedelta(days=700),
                    position="O'qituvchi" if role == roles.TEACHER else None)
    if not active:
        u.exit_date = TODAY - timedelta(days=30)
        u.exit_type = "neutral"
    db.add(u)
    db.commit()
    ids[un] = u.id

# Ketgan Anvar ketish jarayonidan o'tgan: sababi yozilgan
db.add(models.Offboarding(
    user_id=ids["ketgan1"], branch_id=BID,
    last_day=TODAY - timedelta(days=30), reason="salary",
    steps="{}", completed=1,
    exit_notes="Oylik kam deb ketdi, boshqa markaz ko'proq taklif qildi",
    would_return=1))
# Hisobsiz ustoz kartasi — u ham arxivda ko'rinishi kerak
db.add(models.Teacher(full_name="Kartasi qolgan Gulnora", branch_id=BID,
                      is_active=0, hired_date=TODAY - timedelta(days=400),
                      left_date=TODAY - timedelta(days=60)))
db.commit()
db.close()

H = tok("asos")
HH = tok("hr")
HX = tok("sot")

print("\n=== A. HR RO'YXATNI KO'RADI ===")
r = client.get("/api/archive/staff", headers=HH)
ck("HR ocha oladi", r.status_code, 200)
d = r.json()
names = sorted(x["full_name"] for x in d["rows"])
ck("uchala ketgan ham bor", names,
   ["Kartasi qolgan Gulnora", "Ketgan Anvar", "Ketgan Bobur"])
ck("ishlayotgan odam ro'yxatda yo'q",
   any(x["full_name"] == "Ishlayotgan Dilnoza" for x in d["rows"]), False)
ck("shu yil ketganlar sanaldi", d["this_year"], 3)

print("\n=== B. NEGA KETGANI KO'RINADI ===")
by = {x["full_name"]: x for x in d["rows"]}
a = by["Ketgan Anvar"]
ck("sabab yozuvi", a["reason_label"], "Ish haqidan norozi")
ck("bizga bog'liq deb belgilandi", a["ours"], True)
ck("chiqish suhbati ko'rinadi",
   a["exit_notes"].startswith("Oylik kam"), True)
ck("qaytib kelarmidi", a["would_return"], True)
ck("qancha ishlagani", a["months"] > 20, True)
ck("lavozimi", a["position"], "O'qituvchi")

print("\n=== C. SABABI YOZILMAGANLAR ===")
ck("ikkitasining sababi yo'q", d["no_reason"], 2)
ck("Boburda sabab yo'q", by["Ketgan Bobur"]["has_reason"], False)
r = client.put(f"/api/archive/staff/{ids['ketgan2']}", headers=HH, json={
    "exit_type": "red", "reason_key": "dismissed",
    "exit_notes": "Kechikishlar va yo'qlamani soxtalashtirish",
    "would_return": False})
ck("HR to'ldira oladi", r.status_code, 200)
ck("noto'g'ri sabab rad etiladi",
   client.put(f"/api/archive/staff/{ids['ketgan2']}", headers=HH,
              json={"exit_type": "red", "reason_key": "yolgon"}).status_code,
   400)
d2 = client.get("/api/archive/staff", headers=HH).json()
b2 = {x["full_name"]: x for x in d2["rows"]}["Ketgan Bobur"]
ck("sabab yozildi", b2["reason_label"], "Ishdan bo'shatildi")
ck("qizil yo'lak", b2["exit_type"], "red")
ck("qaytarib olinmaydi", b2["would_return"], False)
ck("sababsizlar kamaydi", d2["no_reason"], 1)

print("\n=== D. HISOBOTGA HAM TUSHADI ===")
off = client.get("/api/hr/offboarding", headers=HH).json()
ck("ketish hisobotida ikkalasi ham bor",
   sorted(x["user"] for x in off["rows"]),
   ["Ketgan Anvar", "Ketgan Bobur"])
ck("arxivda sabab statistikasi bor",
   sorted(x["key"] for x in d2["by_reason"]), ["dismissed", "salary"])
ck("bizga bog'liq ulushi hisoblandi", d2["ours_percent"], 50.0)

print("\n=== E. BEGONA ROL ===")
ck("sotuvchi ocha olmaydi",
   client.get("/api/archive/staff", headers=HX).status_code, 403)
ck("sotuvchi to'ldira olmaydi",
   client.put(f"/api/archive/staff/{ids['ketgan2']}", headers=HX,
              json={"exit_type": "green"}).status_code, 403)
ck("asoschi ham ko'radi",
   client.get("/api/archive/staff", headers=H).status_code, 200)

print()
if fails:
    print("XATOLAR:", ", ".join(fails))
    sys.exit(1)
print("HAMMASI O'TDI")
