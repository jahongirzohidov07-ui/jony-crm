"""BOSHQA FILIALDAGI GURUHGA O'TKAZISH (2026-09-23).

Jahongir: "boshqa guruhga otkiza olish kerak boshqa filialdagi,
tolovlari ham togri bolib o'tkizilishi kerak".

Tekshiriladi:
  1) o'tkazish ro'yxatida boshqa filial guruhlari ham chiqadi;
  2) administrator o'z filialidagi o'quvchini o'tkaza oladi;
  3) shu oyning hisobi eski/yangi guruh darslariga bo'linib QAYTA
     hisoblanadi (bitta hisob qatori qoladi);
  4) o'quvchi eski guruh ro'yxatida QOLMAYDI, yangisida asosiy bo'ladi;
  5) filial almashadi va qabul qiluvchi filial adminiga vazifa tushadi;
  6) boshqa filial admini begona o'quvchini o'tkaza olmaydi (403);
  7) ustoz umuman o'tkaza olmaydi (403).
"""
import os
import sys
import tempfile
from datetime import timedelta

_DB = os.path.join(tempfile.gettempdir(), "cross_branch_move.db")
os.environ["DATABASE_URL"] = "sqlite:///" + _DB.replace(chr(92), "/")
if os.path.exists(_DB):
    os.remove(_DB)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient          # noqa: E402
import main, models, roles, billing                # noqa: E402
import entry                                       # noqa: E402,F401
from database import SessionLocal                  # noqa: E402
from auth import hash_password                     # noqa: E402

c = TestClient(main.app)
fails = []


def ck(name, got, want):
    ok = got == want
    print(("OK  " if ok else "XATO ") + name + f": {got}"
          + ("" if ok else f"   (kutilgan {want})"))
    if not ok:
        fails.append(name)


TODAY = roles.local_today()
START, END = billing.month_bounds(TODAY.year, TODAY.month)
PERIOD = f"{TODAY.year:04d}-{TODAY.month:02d}"

db = SessionLocal()
b1 = models.Branch(name="Bekobod 1")
b2 = models.Branch(name="Bekobod 2")
# Hamkor markaz — boshqa biznes: o'tkazish ro'yxatida ko'rinmasligi
# va o'tkazib bo'lmasligi kerak (2026-09-23 ko'rigi).
b3 = models.Branch(name="Stech hamkor", is_partner=1)
db.add_all([b1, b2, b3]); db.commit()
B1, B2, B3 = b1.id, b2.id, b3.id

t1 = models.Teacher(full_name="Ustoz Bir", branch_id=B1, is_active=1)
t2 = models.Teacher(full_name="Ustoz Ikki", branch_id=B2, is_active=1)
db.add_all([t1, t2]); db.commit()
T1, T2 = t1.id, t2.id

# Eski guruh 40 000, yangi (boshqa filialda) 30 000
g1 = models.Group(name="Eski guruh", branch_id=B1, teacher_id=t1.id,
                  lesson_price=40000, standard_lessons_per_month=12,
                  capacity=20)
g2 = models.Group(name="Yangi guruh", branch_id=B2, teacher_id=t2.id,
                  lesson_price=30000, standard_lessons_per_month=12,
                  capacity=20)
# Ikkinchi guruh SHU filialda: filial almashganda u ham yopilishi kerak
g1b = models.Group(name="Eski guruh 2", branch_id=B1, teacher_id=t1.id,
                   lesson_price=40000, standard_lessons_per_month=12,
                   capacity=20)
gp = models.Group(name="Hamkor guruh", branch_id=B3, teacher_id=t2.id,
                  lesson_price=55000, standard_lessons_per_month=12,
                  capacity=20)
db.add_all([g1, g2, g1b, gp]); db.commit()
G1, G2, G1B, GP = g1.id, g2.id, g1b.id, gp.id

# Xodimlar: 1-filial administratori, 2-filial administratori, ustoz
db.add_all([
    models.User(username="adm1", full_name="Admin Bir",
                role=roles.ADMINISTRATOR, branch_id=B1,
                password_hash=hash_password("x"), is_active=1),
    models.User(username="adm2", full_name="Admin Ikki",
                role=roles.ADMINISTRATOR, branch_id=B2,
                password_hash=hash_password("x"), is_active=1),
    models.User(username="ustoz1", full_name="Ustoz Bir",
                role=roles.TEACHER, branch_id=B1,
                password_hash=hash_password("x"), is_active=1),
])
db.commit()

st = models.Student(full_name="Ko'chuvchi Bola", branch_id=B1, group_id=G1,
                    status="active", enrolled_date=START)
db.add(st); db.commit()
SID = st.id
db.add(models.StudentGroupLink(student_id=SID, group_id=G1, is_primary=1,
                               active=1, joined_date=START))
db.add(models.StudentGroupLink(student_id=SID, group_id=G1B, is_primary=0,
                               active=1, joined_date=START))

# Oy boshidan bugungacha eski guruhda 4 dars, bugundan keyin yangi
# guruhda 6 dars (reja).
old_days = [d for d in (TODAY - timedelta(days=x) for x in (7, 5, 3, 1))
            if d >= START]
new_days = [d for d in (TODAY + timedelta(days=x) for x in (0, 2, 4, 6, 8, 10))
            if d <= END]
for d in old_days:
    db.add(models.Lesson(group_id=G1, teacher_id=t1.id, date=d, held=1))
for d in new_days:
    db.add(models.Lesson(group_id=G2, teacher_id=t2.id, date=d, held=0))

# Shu oy uchun hisob allaqachon yozilgan: 12 x 40 000
db.add(models.Payment(student_id=SID, amount=-480000, kind="charge",
                      period=PERIOD, note="Eski guruh — 12 dars",
                      created_by="Avtomat"))
db.commit(); db.close()


def tok(u):
    return {"Authorization": "Bearer " + c.post(
        "/api/auth/login", json={"username": u, "password": "x"}
    ).json()["access_token"]}


H1, H2, HT = tok("adm1"), tok("adm2"), tok("ustoz1")
KUTILGAN = len(old_days) * 40000 + len(new_days) * 30000

print(f"=== Eski guruhda {len(old_days)} dars (40 000), yangi filial "
      f"guruhida {len(new_days)} dars (30 000) ===")

print("\n=== 1. O'tkazish ro'yxatida boshqa filial guruhi bor ===")
r = c.get(f"/api/students/{SID}/transfer-groups", headers=H1)
ck("ro'yxat keldi", r.status_code, 200)
rows = r.json().get("rows", []) if r.status_code == 200 else []
other = [x for x in rows if x["id"] == G2]
ck("boshqa filial guruhi ko'rinadi", len(other), 1)
ck("filial nomi bilan", other[0]["branch"] if other else None, "Bekobod 2")
ck("o'z filiali emas deb belgilangan",
   other[0]["same_branch"] if other else None, False)
ck("o'zi turgan guruh ro'yxatda yo'q",
   [x for x in rows if x["id"] == G1], [])
ck("hamkor markaz guruhi ro'yxatda yo'q",
   [x for x in rows if x["id"] == GP], [])

print("\n=== 1b. Hamkor markazga o'tkazib bo'lmaydi ===")
ck("hamkor markazga 403",
   c.post(f"/api/students/{SID}/move-group?force=true", headers=H1,
          json={"group_id": GP}).status_code, 403)

print("\n=== 2. Ustoz o'tkaza olmaydi ===")
ck("ustozga ruxsat yo'q",
   c.post(f"/api/students/{SID}/move-group", headers=HT,
          json={"group_id": G2}).status_code, 403)

print("\n=== 3. Begona filial admini o'tkaza olmaydi ===")
ck("boshqa filial admini 403",
   c.post(f"/api/students/{SID}/move-group", headers=H2,
          json={"group_id": G2}).status_code, 403)

print("\n=== 4. O'z filiali admini o'tkazadi ===")
r = c.post(f"/api/students/{SID}/move-group?force=true", headers=H1,
           json={"group_id": G2, "note": "Oila ko'chib o'tdi"})
ck("o'tkazildi", r.status_code, 200)
d = r.json() if r.status_code == 200 else {}
ck("filial almashdi", d.get("branch"), "Bekobod 2")
ck("filial o'zgargani belgilandi", d.get("branch_changed"), True)
rc = d.get("recharge") or {}
ck("hisob qayta hisoblandi", bool(rc), True)
ck("eski guruh darslari", rc.get("old_lessons"), len(old_days))
ck("yangi guruh darslari", rc.get("new_lessons"), len(new_days))
ck("yangi summa", rc.get("new"), KUTILGAN)
ck("eski summa saqlandi", rc.get("old"), 480000)
ck("vazifa qabul qiluvchi adminga", d.get("task_for"), "Admin Ikki")

print("\n=== 5. Bazada: guruh, filial, bog'lanish, hisob ===")
db = SessionLocal()
s2 = db.query(models.Student).get(SID)
ck("o'quvchi yangi guruhda", s2.group_id, G2)
ck("o'quvchi yangi filialda", s2.branch_id, B2)
links = {l.group_id: l for l in db.query(models.StudentGroupLink)
         .filter(models.StudentGroupLink.student_id == SID).all()}
ck("eski bog'lanish yopildi", links[G1].active, 0)
ck("eski bog'lanishda chiqqan sana bor", links[G1].left_date is not None, True)
ck("yangi bog'lanish faol", links[G2].active, 1)
ck("yangi bog'lanish asosiy", links[G2].is_primary, 1)
ck("eski filialdagi IKKINCHI guruh ham yopildi", links[G1B].active, 0)
charges = (db.query(models.Payment)
           .filter(models.Payment.student_id == SID,
                   models.Payment.kind == "charge",
                   models.Payment.period == PERIOD).all())
ck("bitta hisob qatori", len(charges), 1)
ck("summa qayta yozildi", abs(charges[0].amount) if charges else 0, KUTILGAN)
db.close()
ck("balans yangi summaga teng",
   c.get(f"/api/students/{SID}", headers=H2).json()["balance"], -KUTILGAN)

print("\n=== 6. Qabul qiluvchi filialga vazifa ===")
db = SessionLocal()
tasks = (db.query(models.Task)
         .filter(models.Task.branch_id == B2).all())
ck("vazifa yaratildi", len(tasks), 1)
if tasks:
    ck("vazifada o'quvchi ismi", "Ko'chuvchi Bola" in (tasks[0].title or ""),
       True)
    ck("vazifada izoh", "Oila ko'chib o'tdi" in (tasks[0].description or ""),
       True)
    ck("vazifada qayta hisob",
       "qayta hisoblandi" in (tasks[0].description or ""), True)

print("\n=== 7. Auditda filial o'zgarishi ===")
al = [a for a in db.query(models.AuditLog).all() if a.field == "branch"]
ck("audit yozuvi bor", len(al) >= 1, True)
if al:
    ck("eski filial auditda", al[0].old_value, "Bekobod 1")
    ck("yangi filial auditda", al[0].new_value, "Bekobod 2")

print("\n=== 8. Shu filial ichidagi ko'chirish avvalgidek ===")
g3 = models.Group(name="Ikkinchi filial guruhi 2", branch_id=B2,
                  teacher_id=T2, lesson_price=30000,
                  standard_lessons_per_month=12, capacity=20)
db.add(g3); db.commit()
G3 = g3.id
db.close()
r8 = c.post(f"/api/students/{SID}/move-group?force=true", headers=H2,
            json={"group_id": G3})
ck("shu filial ichida ko'chirildi", r8.status_code, 200)
ck("filial o'zgarmadi", (r8.json() or {}).get("branch_changed"), None)

print("\n=== 9. Guruhsiz filialga o'tkazish ===")
# Ikki guruhli o'quvchi guruhsiz o'tkazilsa, ikkala bog'lanish ham
# yopilishi va group_id BO'SH qolishi kerak: ilgari detach_group()
# ichidagi sync_primary_group() uni eski filial guruhiga qaytarib
# qo'yardi (2026-09-23 ko'rigi).
db = SessionLocal()
st2 = models.Student(full_name="Guruhsiz Bola", branch_id=B1, group_id=G1,
                     status="active", enrolled_date=START)
db.add(st2); db.commit()
SID2 = st2.id
db.add_all([
    models.StudentGroupLink(student_id=SID2, group_id=G1, is_primary=1,
                            active=1, joined_date=START),
    models.StudentGroupLink(student_id=SID2, group_id=G1B, is_primary=0,
                            active=1, joined_date=START),
])
db.commit(); db.close()
r9 = c.post(f"/api/students/{SID2}/move-branch", headers=H1,
            json={"branch_id": B2, "note": "Guruh keyin tanlanadi"})
ck("guruhsiz o'tkazildi", r9.status_code, 200)
ck("javobda guruh yo'q", (r9.json() or {}).get("group_id"), None)
db = SessionLocal()
s9 = db.query(models.Student).get(SID2)
lk9 = {l.group_id: l.active for l in db.query(models.StudentGroupLink)
       .filter(models.StudentGroupLink.student_id == SID2).all()}
ck("bazada ham guruh yo'q", s9.group_id, None)
ck("filial yangisi", s9.branch_id, B2)
ck("eski guruhlar yopildi", [lk9.get(G1), lk9.get(G1B)], [0, 0])
db.close()

print("\nJAMI XATO:", len(fails), fails)
sys.exit(1 if fails else 0)
