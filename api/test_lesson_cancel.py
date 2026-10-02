"""DARSNI BEKOR QILISH + DAM KUNLARI (2026-08-19).

Jahongir: "darsni bekor qilish funsiyasini ham qoshib ber... buni faqat
men qila olaman... Dam kunlari darslar bo'lmaydi va bu darslar umuman
hisoblanmaydi... agar 12tadan kamayib ketsa bu darsni bekor qilib
bolmaydi... dam kunlar belgilanganda 12tadan kamaysa ogohlantirib
bunday qilish mumkin emas degan yozuv chiqsin".
"""
import os, sys
from datetime import date, timedelta
os.environ["DATABASE_URL"] = "sqlite:////tmp/lescancel.db"
if os.path.exists("/tmp/lescancel.db"):
    os.remove("/tmp/lescancel.db")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fastapi.testclient import TestClient          # noqa: E402
import main, models, roles, billing                # noqa: E402
import entry                                       # noqa: E402
from database import SessionLocal                  # noqa: E402
import common as _cm_stub                           # noqa: E402
# Login oylik yechimni ishga tushiradi (auth_users -> common, 2026-10-02
# dan beri to'g'ri ulangan). Bu test unga bog'liq emas — o'chiramiz.
_cm_stub._ensure_month_charges = lambda db, **kw: None
from auth import hash_password                     # noqa: E402
import groups_lessons                              # noqa: E402

# Testda guruh jadval kunlari yo'q — sinxronlash rejani buzmasin
groups_lessons._sync_scheduled_lessons = lambda *a, **k: None

c = TestClient(main.app)
fails = []


def ck(n, g, w):
    ok = g == w
    print(("OK  " if ok else "MUAMMO ") + n + f": {g}"
          + ("" if ok else f" (kutilgan {w})"))
    if not ok:
        fails.append(n)


T = date.today()
Y, M = T.year, T.month

db = SessionLocal()
b = models.Branch(name="Zafar"); db.add(b); db.commit()
t = models.Teacher(full_name="Nodira", branch_id=b.id, is_active=1)
db.add(t); db.commit()
g13 = models.Group(name="NEW LEARNERS", branch_id=b.id, teacher_id=t.id,
                   monthly_fee=480000, lesson_price=40000,
                   standard_lessons_per_month=12,
                   rate_manual=1, teacher_rate_per_student=160000)
g12 = models.Group(name="TIG'IZ", branch_id=b.id, teacher_id=t.id,
                   monthly_fee=480000, lesson_price=40000,
                   standard_lessons_per_month=12,
                   rate_manual=1, teacher_rate_per_student=160000)
db.add_all([g13, g12]); db.commit()
s1 = models.Student(full_name="Bola", branch_id=b.id, group_id=g13.id,
                    status="active")
db.add(s1); db.commit()

# Bugungacha bo'lmagan REJA darslar kerak (dam kuni faqat kelajakka).
# Oy oxiriga sig'masa ham dars sanalari bir oy ichida bo'lishi shart
# emas — cancel uchun. 13 ta dars: 1 tasi O'TILGAN (belgi bilan).
fut = []
first = models.Lesson(group_id=g13.id, teacher_id=t.id,
                      date=T - timedelta(days=1), held=1)
db.add(first); db.flush()
db.add(models.Attendance(lesson_id=first.id, student_id=s1.id, present=1))
for i in range(12):
    L = models.Lesson(group_id=g13.id, teacher_id=t.id,
                      date=T + timedelta(days=i + 1), held=0)
    db.add(L); db.flush()
    fut.append(L.id)
# Hammasi shu oyda bo'lmasa test noto'g'ri — oy chegarasini tekshirish
same_month = all((T + timedelta(days=i + 1)).month == M for i in range(12)) \
    and (T - timedelta(days=1)).month == M
# 12 darslik guruh — bitta ham ortiqcha emas
g12_les = []
for i in range(12):
    L = models.Lesson(group_id=g12.id, teacher_id=t.id,
                      date=T + timedelta(days=i + 1), held=0)
    db.add(L); db.flush()
    g12_les.append(L.id)
db.add(models.User(username="asos", full_name="Asoschi",
                   password_hash=hash_password("x"), role=roles.FOUNDER,
                   branch_id=b.id))
db.add(models.User(username="adm", full_name="Admin",
                   password_hash=hash_password("x"),
                   role=roles.ADMINISTRATOR, branch_id=b.id))
db.commit()
G13, G12, HELD = g13.id, g12.id, first.id
db.close()

if not same_month:
    # Oy chegarasida test ma'nosiz bo'lib qoladi — soddalashtiramiz:
    # bu holda faqat huquq/tartib tekshiruvlari o'tkaziladi.
    print("OGOHLANTIRISH: oy chegarasi — reja-soni tekshiruvi taxminiy")


def tok(u):
    return c.post("/api/auth/login",
                  json={"username": u, "password": "x"}).json()["access_token"]


AS = {"Authorization": f"Bearer {tok('asos')}"}
AD = {"Authorization": f"Bearer {tok('adm')}"}

print("\n=== 1. Admin bekor qila olmaydi (403) ===")
r = c.post(f"/api/lessons/{fut[0]}/cancel", json={}, headers=AD)
ck("403", r.status_code, 403)

print("\n=== 2. O'tilgan darsni bekor qilib bo'lmaydi ===")
r = c.post(f"/api/lessons/{HELD}/cancel", json={}, headers=AS)
ck("400", r.status_code, 400)
ck("sababi tushunarli", "ish haqi" in r.json()["detail"], True)

if same_month:
    print("\n=== 3. 13-dars bekor qilinadi (12 qoladi) ===")
    r = c.post(f"/api/lessons/{fut[0]}/cancel",
               json={"note": "sinov"}, headers=AS)
    ck("ok", r.status_code, 200)
    db = SessionLocal()
    L = db.query(models.Lesson).get(fut[0])
    ck("belgilandi, o'chirilmadi", L.cancelled, 1)
    ck("bo'luvchi endi 12",
       billing.month_divisor(db, db.query(models.Group).get(G13), T), 12)
    a = (db.query(models.AuditLog)
         .filter(models.AuditLog.entity == "lesson",
                 models.AuditLog.action == "cancel").count())
    ck("auditda iz", a, 1)
    db.close()

    print("\n=== 4. Yana bekor qilsa — 12 dan kamayadi, TAQIQ ===")
    r = c.post(f"/api/lessons/{fut[1]}/cancel", json={}, headers=AS)
    ck("400", r.status_code, 400)
    ck("'mumkin emas' yozuvi",
       "mumkin emas" in r.json()["detail"], True)

    print("\n=== 5. Davomat jadvalida bekor qilingan ko'rinmaydi ===")
    r = c.get(f"/api/groups/{G13}/attendance?year={Y}&month={M}",
              headers=AS).json()
    ids = [x["id"] for x in r["lessons"]]
    ck("bekor qilingani jadvalda yo'q", fut[0] in ids, False)

    print("\n=== 6. Qaytarish ===")
    r = c.post(f"/api/lessons/{fut[0]}/uncancel", headers=AS)
    ck("qaytdi", r.status_code, 200)
    db = SessionLocal()
    ck("bo'luvchi yana 13",
       billing.month_divisor(db, db.query(models.Group).get(G13), T), 13)
    db.close()

    print("\n=== 7. Dam kuni: 12 darslik guruh to'sadi ===")
    dd = (T + timedelta(days=1)).isoformat()
    r = c.post("/api/holidays", json={"date": dd, "name": "Sinov bayram"},
               headers=AS)
    ck("to'sildi (TIG'IZ 12 ta)", r.status_code, 400)
    ck("'mumkin emas'", "mumkin emas" in r.json()["detail"], True)
    ck("guruh nomi aytildi", "TIG'IZ" in r.json()["detail"], True)

    print("\n=== 8. TIG'IZ guruhga zapas dars qo'shilsa — dam kuni o'tadi ===")
    db = SessionLocal()
    db.add(models.Lesson(group_id=G12, teacher_id=1,
                         date=T + timedelta(days=2), held=0))
    db.commit(); db.close()
    r = c.post("/api/holidays", json={"date": dd, "name": "Sinov bayram"},
               headers=AS)
    ck("endi o'tdi", r.status_code, 200)
    n = r.json()["cancelled_lessons"]
    ck("2 ta dars bekor bo'ldi (ikkala guruhda)", n, 2)
    db = SessionLocal()
    ck("g13 bo'luvchisi 12",
       billing.month_divisor(db, db.query(models.Group).get(G13), T), 12)
    hid = db.query(models.Holiday).first().id
    db.close()

    print("\n=== 9. Dam kuni olib tashlansa darslar qaytadi ===")
    r = c.delete(f"/api/holidays/{hid}", headers=AS)
    ck("o'chirildi", r.status_code, 200)
    ck("2 ta dars qaytdi", r.json()["restored_lessons"], 2)

print("\n" + ("HAMMASI JOYIDA" if not fails
              else f"MUAMMO: {len(fails)} ta -> {fails}"))
sys.exit(1 if fails else 0)
