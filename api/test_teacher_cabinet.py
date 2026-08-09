"""Ustoz kabineti: o'z guruhlari, o'z o'quvchilari (balanssiz),
dars ko'chirish kvotasi, o'rinbosar va kitob buyurtmasi."""
import os, sys, json
from datetime import date, timedelta

os.environ["DATABASE_URL"] = "sqlite:////tmp/tcab_test.db"
if os.path.exists("/tmp/tcab_test.db"):
    os.remove("/tmp/tcab_test.db")

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
b = models.Branch(name="Zafar"); db.add(b); db.commit()
BID = b.id

for u, role in [("asos", "founder"), ("rahbar", "branch_manager"),
                ("oquv", "academic_head")]:
    db.add(models.User(username=u, password_hash=hash_password("x"),
                       full_name=u.capitalize(), role=role,
                       branch_id=None if role == "founder" else BID))
db.commit()

# Ikkita ustoz
T = {}
for name in ["Mening Ustoz", "Boshqa Ustoz"]:
    t = models.Teacher(full_name=name, branch_id=BID, is_active=1,
                       grade="senior",
                       hired_date=TODAY - timedelta(days=1278))  # ~3.5 yil
    db.add(t); db.commit()
    T[name] = t.id
    u = models.User(username=roles.login_from_name(name),
                    password_hash=hash_password("x"), full_name=name,
                    role="teacher", branch_id=BID)
    db.add(u); db.commit()
    t.user_id = u.id; db.commit()
    T[name + "_login"] = u.username

# Guruhlar
for name, tid in [("Mening guruh", T["Mening Ustoz"]),
                  ("Begona guruh", T["Boshqa Ustoz"])]:
    g = models.Group(name=name, teacher_id=tid, branch_id=BID,
                     subject="english", lesson_days="mon,wed",
                     lesson_time="15:00")
    db.add(g); db.commit()
    T[name] = g.id

# O'quvchilar
for i in range(3):
    db.add(models.Student(full_name=f"Mening bola {i}", branch_id=BID,
                          group_id=T["Mening guruh"], status="active",
                          enrolled_date=TODAY - timedelta(days=200)))
db.add(models.Student(full_name="Begona bola", branch_id=BID,
                      group_id=T["Begona guruh"], status="active",
                      enrolled_date=TODAY - timedelta(days=100)))
db.commit()

# Davomat: bittasi kam qatnaydi
mine = db.query(models.Student).filter(
    models.Student.group_id == T["Mening guruh"]).all()
for i in range(10):
    ls = models.Lesson(group_id=T["Mening guruh"],
                       teacher_id=T["Mening Ustoz"],
                       date=TODAY - timedelta(days=60 - i * 5), held=1)
    db.add(ls); db.commit()
    for j, s in enumerate(mine):
        present = not (j == 0 and i % 2 == 0)     # 0-bola yarmini qoldirgan
        db.add(models.Attendance(lesson_id=ls.id, student_id=s.id,
                                 present=1 if present else 0))
        if present:
            db.add(models.DailyGrade(lesson_id=ls.id, student_id=s.id,
                                     score=8))
db.commit()

# Omborda kitob
db.add(models.Consumable(name="Solutions Elementary", kind="book",
                         branch_id=BID, qty=12, unit="dona"))
db.commit(); db.close()

H = tok("asos")
BM = tok("rahbar")
AC = tok("oquv")
ME = tok(T["Mening Ustoz_login"])
OTHER = tok(T["Boshqa Ustoz_login"])

print("=== 1. GURUHLARIM ===")

d = client.get("/api/me/groups", headers=ME).json()
ck("faqat o'z guruhi", len(d["rows"]), 1)
ck("guruh nomi", d["rows"][0]["name"], "Mening guruh")
ck("o'quvchilar soni", d["rows"][0]["students"], 3)
ck("jami o'quvchi", d["total_students"], 3)
ck("izoh berilgan", "Boshqa ustozlarning" in d["hint"], True)
raw = json.dumps(d, ensure_ascii=False)
ck("begona guruh ko'rinmaydi", "Begona guruh" in raw, False)

ck("asoschi bu oynani ochmaydi",
   client.get("/api/me/groups", headers=H).status_code, 403)

print("\n=== 2. O'QUVCHILARIM — BALANSSIZ ===")

d = client.get("/api/me/students", headers=ME).json()
ck("faqat o'z o'quvchilari", d["total"], 3)
raw = json.dumps(d, ensure_ascii=False)
ck("begona bola yo'q", "Begona bola" in raw, False)
# Eng muhimi: pul haqida hech narsa
ck("balans qaytarilmaydi", "balance" in raw, False)
ck("to'lov haqida hech narsa yo'q", "payment" in raw.lower(), False)
ck("izohda tushuntirilgan", "balans" in d["hint"].lower(), True)

r0 = next(r for r in d["rows"] if r["full_name"] == "Mening bola 0")
r1 = next(r for r in d["rows"] if r["full_name"] == "Mening bola 1")
ck("davomat foizi hisoblandi", r0["attendance_percent"], 50.0)
ck("boshqasi to'liq qatnagan", r1["attendance_percent"], 100.0)
ck("qoldirgan darslari", r0["missed"], 5)
ck("o'rtacha baho", r1["avg_grade"], 8.0)
ck("kam qatnaydigan belgilandi", r0["at_risk"], True)
ck("yaxshi qatnaydigan belgilanmadi", r1["at_risk"], False)
ck("xavfli o'quvchilar soni", d["at_risk"], 1)

d2 = client.get(f"/api/me/students?group_id={T['Begona guruh']}",
                headers=ME)
ck("begona guruh so'ralsa rad etiladi", d2.status_code, 403)

print("\n=== 3. TAJRIBA YILDA ===")

d = client.get("/api/me/career", headers=ME).json()
st = d["state"]
ck("oyda ham bor", st["months"] > 40, True)
ck("yilda hisoblandi", st["years"], 3.5)
ck("matn ko'rinishi", st["tenure_text"], "3.5 yil")

ck("bir yildan kam — oyda qoladi", roles.tenure_years_text(7), "7 oy")
ck("aniq ikki yil", roles.tenure_years_text(24), "2 yil")

print("\n=== 4. DARS KO'CHIRISH KVOTASI ===")

d = client.get("/api/me/reschedules", headers=ME).json()
ck("oyiga 2 marta", d["quota"]["per_month"], 2)
ck("6 oyda 12 marta", d["quota"]["per_window"], 12)
ck("hozircha ishlatilmagan", d["quota"]["used_month"], 0)
ck("avtomat ruxsat bor", d["quota"]["auto_ok"], True)
ck("keyingi oyga o'tmaydi", d["carry_over"], False)
ck("bekor qilib bo'lmasligi aytilgan",
   "bekor qilish mumkin emas" in d["cannot_cancel"].lower(), True)

GID = T["Mening guruh"]


def _next_month_start(d):
    return (date(d.year + 1, 1, 1) if d.month == 12
            else date(d.year, d.month + 1, 1))


# MUHIM: bu uchta ko'chirish ATAYLAB "kelasi oy"ning aniq kunlariga
# bog'langan (TODAY+3/+7/+11 kabi qattiq sonlarga emas). Kvota "DARS
# oyi" bo'yicha sanalgani uchun (pastda, 6-bandda tekshiriladi) test
# har doim - oyning qaysi kunida ishga tushirilishidan qat'i nazar -
# bir xil natija berishi kerak. Qattiq son ishlatilganda test faqat
# oyning oxirgi ~10-15 kunida to'g'ri natija berardi, boshqa kunlarda
# esa "kelasi oy" deb hisoblangan darslar aslida JORIY oyga tushib,
# 6-banddagi tekshiruv teskarisiga aylanardi.
_NMS = _next_month_start(TODAY)
D1 = (_NMS + timedelta(days=1) - TODAY).days
D2 = (_NMS + timedelta(days=5) - TODAY).days
D3 = (_NMS + timedelta(days=9) - TODAY).days


def move(from_days, to_days):
    return client.post("/api/me/reschedules", headers=ME, json={
        "group_id": GID,
        "from_date": (TODAY + timedelta(days=from_days)).isoformat(),
        "to_date": (TODAY + timedelta(days=to_days)).isoformat(),
        "reason": "sick"})


r = move(D1, D1 + 2)
ck("birinchi surish avtomat", r.json()["status"], "auto")
ck("avtomat deb belgilandi", r.json()["auto_approved"], True)
ck("kvota kamaydi", r.json()["quota"]["left_month"], 1)

r = move(D2, D2 + 2)
ck("ikkinchi surish ham avtomat", r.json()["status"], "auto")
ck("oylik kvota tugadi", r.json()["quota"]["left_month"], 0)

r = move(D3, D3 + 2)
ck("uchinchisi tasdiqqa ketdi", r.json()["status"], "pending")
ck("avtomat emas", r.json()["auto_approved"], False)
RID = r.json()["id"]

print("\n=== 5. KO'CHIRISH QOIDALARI ===")

r = client.post("/api/me/reschedules", headers=ME, json={
    "group_id": GID, "from_date": (TODAY + timedelta(days=20)).isoformat(),
    "to_date": (TODAY - timedelta(days=1)).isoformat()})
ck("o'tmishga surib bo'lmaydi", r.status_code, 400)

r = client.post("/api/me/reschedules", headers=ME, json={
    "group_id": GID, "from_date": (TODAY + timedelta(days=20)).isoformat(),
    "to_date": (TODAY + timedelta(days=20)).isoformat()})
ck("o'sha kunga surib bo'lmaydi", r.status_code, 400)

r = client.post("/api/me/reschedules", headers=ME, json={
    "group_id": GID, "from_date": TODAY.isoformat(),
    "to_date": (TODAY + timedelta(days=2)).isoformat()})
ck("bugungi darsni surib bo'lmaydi", r.status_code, 400)
ck("sabab: ogohlantirish vaqti", "kun oldin" in r.json()["detail"], True)

r = client.post("/api/me/reschedules", headers=ME, json={
    "group_id": GID, "from_date": (TODAY + timedelta(days=20)).isoformat(),
    "to_date": (TODAY + timedelta(days=60)).isoformat()})
ck("juda uzoqqa surib bo'lmaydi", r.status_code, 400)

r = move(D1, D1 + 3)
ck("bir dars ikki marta surilmaydi", r.status_code, 400)

r = client.post("/api/me/reschedules", headers=OTHER, json={
    "group_id": GID, "from_date": (TODAY + timedelta(days=20)).isoformat(),
    "to_date": (TODAY + timedelta(days=22)).isoformat()})
ck("begona guruhni surib bo'lmaydi", r.status_code, 403)

print("\n=== 6. TASDIQLASH ===")

d = client.get("/api/reschedules?status=pending", headers=AC).json()
ck("o'quv bo'limi ko'radi", d["pending"], 1)

r = client.post(f"/api/reschedules/{RID}/decide", headers=AC,
                json={"decision": "rejected"})
ck("sababsiz rad etilmaydi", r.status_code, 400)

r = client.post(f"/api/reschedules/{RID}/decide", headers=AC,
                json={"decision": "approved", "note": "Sabab jiddiy"})
ck("tasdiqlandi", r.json()["status"], "approved")
ck("kim tasdiqladi", r.json()["decided_by"], "Oquv")

r = client.post(f"/api/reschedules/{RID}/decide", headers=AC,
                json={"decision": "approved"})
ck("ikki marta qaror qabul qilinmaydi", r.status_code, 400)

ck("ustoz o'zi tasdiqlay olmaydi",
   client.get("/api/reschedules", headers=ME).status_code, 403)

# Kvota DARS oyi bo'yicha sanaladi. Surilgan darslar kelasi oyda
# bo'lgani uchun joriy oyda 0, kelasi oyda 3 chiqadi.
d = client.get("/api/me/reschedules", headers=ME).json()
ck("joriy oyda ishlatilmagan", d["quota"]["used_month"], 0)
ck("kelasi oyda 3 ta", d["quota_next"]["used_month"], 3)
ck("kelasi oyda kvota tugagan", d["quota_next"]["auto_ok"], False)
ck("tasdiqlangani ham sanaldi", d["quota"]["used_window"], 3)
ck("qoida izohlangan", "DARS qaysi oyda" in d["hint"], True)

print("\n=== 7. O'RINBOSAR USTOZ ===")

r = client.post("/api/me/substitutions", headers=ME, json={
    "group_id": GID,
    "lesson_date": (TODAY + timedelta(days=4)).isoformat(),
    "reason": "family"})
ck("ochiq taklif yaratildi", r.status_code, 200)
SID = r.json()["id"]
ck("holati taklif", r.json()["status"], "offered")
ck("hali o'rinbosar yo'q", r.json()["substitute_teacher"], None)

d = client.get("/api/me/substitutions", headers=OTHER).json()
ck("boshqa ustoz ochiq taklifni ko'radi", len(d["open_offers"]), 1)

d = client.get("/api/me/substitutions", headers=ME).json()
ck("o'z so'rovim ro'yxatda", len(d["my_requests"]), 1)
ck("o'zimga ochiq taklif ko'rinmaydi", len(d["open_offers"]), 0)

r = client.post(f"/api/me/substitutions/{SID}/decide", headers=ME,
                json={"decision": "accepted"})
ck("o'z so'rovini o'zi qabul qilolmaydi", r.status_code, 400)

r = client.post(f"/api/me/substitutions/{SID}/decide", headers=OTHER,
                json={"decision": "accepted"})
ck("boshqa ustoz qabul qildi", r.json()["status"], "accepted")
ck("o'rinbosar yozildi", r.json()["substitute_teacher"], "Boshqa Ustoz")

r = client.post("/api/me/substitutions", headers=ME, json={
    "group_id": GID,
    "lesson_date": (TODAY + timedelta(days=4)).isoformat()})
ck("bir darsga ikkinchi so'rov yo'q", r.status_code, 400)

r = client.post("/api/me/substitutions", headers=ME, json={
    "group_id": T["Begona guruh"],
    "lesson_date": (TODAY + timedelta(days=4)).isoformat()})
ck("begona guruhga so'ramaydi", r.status_code, 403)

print("\n=== 8. KITOB BUYURTMASI ===")

cat = client.get("/api/books/catalogue", headers=ME).json()
ck("katalogda kitob bor", len(cat["rows"]), 1)
ck("qoldiq ko'rinadi", cat["rows"][0]["qty"], 12)

r = client.post("/api/me/book-orders", headers=ME, json={
    "group_id": GID,
    "items": [{"title": "Solutions Elementary", "qty": 12,
               "level": "A1", "consumable_id": cat["rows"][0]["id"]},
              {"title": "Grammar in Use", "qty": 5}],
    "needed_by": (TODAY + timedelta(days=10)).isoformat(),
    "urgency": "soon", "note": "Yangi guruh uchun"})
ck("buyurtma yaratildi", r.status_code, 200)
OID = r.json()["id"]
ck("raqam berildi", r.json()["public_id"].startswith("BOOK-"), True)
ck("2 xil kitob", r.json()["titles"], 2)
ck("jami 17 dona", r.json()["total_qty"], 17)
ck("holati yangi", r.json()["status"], "new")
ck("vazifa yaratildi", r.json()["task_id"] is not None, True)

# Vazifa filial rahbariga tushdi
db = SessionLocal()
task = db.query(models.Task).get(r.json()["task_id"])
rahbar = db.query(models.User).filter(
    models.User.username == "rahbar").first()
ck("vazifa filial rahbariga", task.assignee_id, rahbar.id)
ck("vazifada kitob nomi bor", "Solutions Elementary" in task.description,
   True)
ck("vazifada soni bor", "12 dona" in task.description, True)
db.close()

r = client.post("/api/me/book-orders", headers=ME,
                json={"items": []})
ck("bo'sh buyurtma qabul qilinmaydi", r.status_code, 400)

r = client.post("/api/me/book-orders", headers=ME,
                json={"items": [{"title": "Test", "qty": 0}]})
ck("nol dona qabul qilinmaydi", r.status_code, 400)

print("\n=== 9. BUYURTMANI KO'RIB CHIQISH ===")

d = client.get("/api/book-orders", headers=BM).json()
ck("filial rahbari ko'radi", len(d["rows"]), 1)
ck("ochiq buyurtmalar", d["open"], 1)
ck("jami kitoblar", d["total_books"], 17)

ck("ustoz boshqalarnikini ko'rmaydi",
   client.get("/api/book-orders", headers=ME).status_code, 403)

r = client.post(f"/api/book-orders/{OID}/status", headers=BM,
                json={"status": "rejected"})
ck("sababsiz rad etilmaydi", r.status_code, 400)

r = client.post(f"/api/book-orders/{OID}/status", headers=BM,
                json={"status": "delivered"})
ck("yetkazildi deb belgilandi", r.json()["status"], "delivered")
ck("yetkazilgan sana", r.json()["delivered_at"], TODAY.isoformat())
ck("hamma kitob yetkazildi",
   all(i["delivered_qty"] == i["qty"] for i in r.json()["items"]), True)

db = SessionLocal()
task = db.query(models.Task).get(OID and r.json()["task_id"])
ck("vazifa ham yopildi", task.status, "done")
db.close()

print("\n=== 10. AUDIT ===")

db = SessionLocal()
kinds = {l.entity for l in db.query(models.AuditLog).all()}
ck("ko'chirish audit qilindi", "lesson_reschedule" in kinds, True)
ck("o'rinbosar audit qilindi", "substitution" in kinds, True)
ck("kitob audit qilindi", "book_order" in kinds, True)
db.close()

print()
if fails:
    print(f"XATOLAR ({len(fails)}): " + ", ".join(fails))
    sys.exit(1)
print("HAMMASI O'TDI")
