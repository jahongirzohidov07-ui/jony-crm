"""USTOZ OYLIGI PDF va FILIAL CHEGARASI (2026-09-25).

Jahongir: "ustozlarni har oygi oyliki qaysi oquvchidan qancha olishini
hisobotini pdf qilib yuklab olsa bolsin bu funksiya filial
rahbarlarida ham bolsin" + "faqat o'z filiali".

Tekshiriladi:
  1. Asoschi PDF yuklab oladi (haqiqiy PDF fayl);
  2. Ustoz o'zinikini TO'LIQ ko'radi (ikkala filial);
  3. Filial rahbariga hisobot faqat O'Z filiali bo'yicha kesiladi;
  4. Filial rahbari ham PDF yuklab oladi;
  5. Boshqa ustoz va administrator ko'ra olmaydi (403);
  6. Noto'g'ri oy — 400; yo'qlama bo'lmagan oy — 404.
"""
import os
import sys
import tempfile
from datetime import date

_DIR = os.path.join(tempfile.gettempdir(), "salary_pdf_test")
os.makedirs(_DIR, exist_ok=True)
_DB = os.path.join(_DIR, "db.sqlite")
os.environ["DATABASE_URL"] = "sqlite:///" + _DB.replace(chr(92), "/")
if os.path.exists(_DB):
    os.remove(_DB)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient          # noqa: E402
import main, models, roles                         # noqa: E402
import entry                                       # noqa: E402,F401
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


today = roles.local_today()
PY, PM = ((today.year, today.month - 1) if today.month > 1
          else (today.year - 1, 12))

db = SessionLocal()
b1 = models.Branch(name="Bekobod 1")
b2 = models.Branch(name="Bekobod 2")
db.add_all([b1, b2]); db.commit()
B1, B2 = b1.id, b2.id

u_e = models.User(username="elena", password_hash=hash_password("x"),
                  full_name="Elena", role=roles.TEACHER, branch_id=B1)
u_b = models.User(username="bobur", password_hash=hash_password("x"),
                  full_name="Bobur", role=roles.TEACHER, branch_id=B2)
u_f = models.User(username="asos", password_hash=hash_password("x"),
                  full_name="Asoschi", role=roles.FOUNDER)
u_r = models.User(username="rahbar1", password_hash=hash_password("x"),
                  full_name="Filial Rahbari", role=roles.BRANCH_MANAGER,
                  branch_id=B1)
u_a = models.User(username="admin1", password_hash=hash_password("x"),
                  full_name="Administrator", role=roles.ADMINISTRATOR,
                  branch_id=B1)
db.add_all([u_e, u_b, u_f, u_r, u_a]); db.commit()

elena = models.Teacher(full_name="Elena Karimova", is_active=1, branch_id=B1,
                       grade="middle", user_id=u_e.id)
bobur = models.Teacher(full_name="Bobur Rasulov", is_active=1, branch_id=B2,
                       grade="middle", user_id=u_b.id)
db.add_all([elena, bobur]); db.commit()
db.add(models.TeacherBranch(teacher_id=elena.id, branch_id=B2)); db.commit()
EID, BID = elena.id, bobur.id


def group(name, br):
    g = models.Group(name=name, branch_id=br, teacher_id=EID,
                     lesson_price=40_000, standard_lessons_per_month=12,
                     monthly_fee=480_000, rate_manual=1,
                     teacher_rate_per_student=120_000)
    db.add(g); db.commit()
    return g


def student(name, g, br):
    s = models.Student(full_name=name, branch_id=br, status="active",
                       group_id=g.id, enrolled_date=date(PY, PM, 1))
    db.add(s); db.commit()
    db.add(models.StudentGroupLink(student_id=s.id, group_id=g.id,
                                   is_primary=1, active=1))
    db.commit()
    return s


gA = group("Step 2 · ertalab", B1)
gB = group("Step 1 · kechki", B2)
ali = student("Ali Tursunov", gA, B1)
vali = student("Vali Qodirov", gA, B1)
sara = student("Sara Yusupova", gB, B2)
for d in range(1, 13):
    la = models.Lesson(group_id=gA.id, date=date(PY, PM, d),
                       teacher_id=EID, held=1)
    lb = models.Lesson(group_id=gB.id, date=date(PY, PM, d),
                       teacher_id=EID, held=1)
    db.add_all([la, lb]); db.commit()
    db.add(models.Attendance(student_id=ali.id, lesson_id=la.id,
                             present=1 if d != 3 else 0))
    db.add(models.Attendance(student_id=vali.id, lesson_id=la.id, present=1))
    db.add(models.Attendance(student_id=sara.id, lesson_id=lb.id, present=1))
db.commit()
db.close()

H, TE, TB, HR, HA = (tok("asos"), tok("elena"), tok("bobur"),
                     tok("rahbar1"), tok("admin1"))
PDF = f"/api/teachers/{EID}/salary.pdf?year={PY}&month={PM}"
JSON = f"/api/teachers/{EID}/salary-breakdown?year={PY}&month={PM}"

print("=== 1. Asoschi PDF yuklab oladi ===")
r = client.get(PDF, headers=H)
ck("status 200", r.status_code, 200)
ck("PDF turi", r.headers.get("content-type"), "application/pdf")
ck("haqiqiy PDF fayl", r.content[:4], b"%PDF")
ck("bo'sh emas", len(r.content) > 3000, True)
ck("fayl nomida ustoz",
   "Elena" in (r.headers.get("content-disposition") or ""), True)

print("\n=== 2. Ustoz o'zinikini TO'LIQ ko'radi ===")
d_full = client.get(JSON, headers=TE).json()
ck("ikki filial", d_full["multi_branch"], True)
ck("kesilmagan", d_full.get("scoped"), None)
TOTAL = d_full["amount"]
B1_SUM = [b for b in d_full["branches"]
          if b["branch"] == "Bekobod 1"][0]["amount"]
ck("B1 summasi umumiydan kam", B1_SUM < TOTAL, True)

print("\n=== 3. Filial rahbari: faqat o'z filiali ===")
r3 = client.get(JSON, headers=HR)
ck("status 200", r3.status_code, 200)
d3 = r3.json()
ck("kesilgan deb belgilandi", d3.get("scoped"), True)
ck("faqat bitta filial", [b["branch"] for b in d3["branches"]], ["Bekobod 1"])
ck("summa o'z filialiniki", d3["amount"], B1_SUM)
ck("boshqa filial o'quvchisi yo'q",
   [s for s in d3["students"] if s["student"] == "Sara Yusupova"], [])
ck("o'z filiali o'quvchilari bor",
   sorted(s["student"] for s in d3["students"]),
   ["Ali Tursunov", "Vali Qodirov"])
ck("muhr summasi ko'rsatilmaydi", d3.get("sealed_amount"), None)

print("\n=== 4. Filial rahbari PDF yuklab oladi ===")
r4 = client.get(PDF, headers=HR)
ck("status 200", r4.status_code, 200)
ck("haqiqiy PDF fayl", r4.content[:4], b"%PDF")


def pdf_text(data: bytes) -> str:
    """PDF ichidagi matn — ichida nima yozilgani tekshiriladi."""
    import io as _io
    try:
        from pypdf import PdfReader
    except ImportError:          # eski muhitda bo'lmasligi mumkin
        return ""
    return "\n".join(p.extract_text() or ""
                     for p in PdfReader(_io.BytesIO(data)).pages)


t_full, t_scoped = pdf_text(r.content), pdf_text(r4.content)
if t_full:
    ck("to'liq PDFda ikkala filial",
       ("Bekobod 1" in t_full, "Bekobod 2" in t_full), (True, True))
    ck("to'liq PDFda boshqa filial o'quvchisi bor",
       "Sara Yusupova" in t_full, True)
    ck("kesilgan PDFda boshqa filial o'quvchisi YO'Q",
       "Sara Yusupova" in t_scoped, False)
    ck("kesilgan PDFda o'z o'quvchisi bor",
       "Ali Tursunov" in t_scoped, True)
    ck("kesilgan PDFda filial yozilgan",
       "Bekobod 1 bo'yicha" in t_scoped, True)
    ck("summalar PDFda", ("360 000" in t_full, "240 000" in t_scoped),
       (True, True))
else:
    print("   (pypdf yo'q — PDF matni tekshirilmadi)")

print("\n=== 5. Ruxsatlar ===")
ck("boshqa ustoz ko'ra olmaydi", client.get(PDF, headers=TB).status_code, 403)
ck("administrator ko'ra olmaydi", client.get(PDF, headers=HA).status_code, 403)
ck("ustoz o'zinikini yuklaydi", client.get(PDF, headers=TE).status_code, 200)

print("\n=== 6. Chegaraviy holatlar ===")
ck("noto'g'ri oy", client.get(
    f"/api/teachers/{EID}/salary.pdf?year={PY}&month=13",
    headers=H).status_code, 400)
ck("yo'qlamasiz oy", client.get(
    f"/api/teachers/{BID}/salary.pdf?year={PY}&month={PM}",
    headers=H).status_code, 404)

print("\nJAMI XATO:", len(fails), fails)
sys.exit(1 if fails else 0)
