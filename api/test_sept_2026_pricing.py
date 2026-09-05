"""SENTABR 2026 NARX QOIDASI (2026-09-05).

Jahongir: "Avgustda o'qiganlar ... 480 ming tolaganlar uchun narxlar
o'zgarishsiz ketadi, sentabrdan yozilganlar uchun esa 540,000dan
bo'lishi kerak stretinko filialdan tashqari, IT filialdan tashqari,
stretinkoda esa barchasi 420,000 so'm ... xato ketganlar bo'lsa
togrlab chiqish kerak".

Jonli bazadagi holat aynan qayta yasaladi va qoida qo'llanadi:
  - eski o'quvchi 480 000 da QOLADI (qulf) va keyingi oyda ham 480 000;
  - sentabrda kelgan 540 000 ga tuzatiladi; keyingi yangi ham 540 000;
  - Stretinko: hamma 420 000; 480 000 bilan hisoblangani tuzatiladi;
  - Stetch (IT hamkor) ga tegilmaydi;
  - chegirmali, qisman, boshqa narxdagi guruhlarga tegilmaydi;
  - hech narsa o'chirilmaydi, ikkinchi marta hech nima qilmaydi.
"""
import os, sys
from datetime import date, datetime, timedelta

os.environ["DATABASE_URL"] = "sqlite:////tmp/sept_price_test.db"
if os.path.exists("/tmp/sept_price_test.db"):
    os.remove("/tmp/sept_price_test.db")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
import main, models, roles, billing, courses
import entry  # noqa: F401
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


db = SessionLocal()
B = {}
for nm, partner in [("Zafar", 0), ("Bekobod 1", 0), ("Stretinko", 0),
                    ("Stetch", 1)]:
    b = models.Branch(name=nm, is_partner=partner)
    db.add(b)
    db.commit()
    B[nm] = b.id
db.add(models.User(username="asos", password_hash=hash_password("x"),
                   full_name="Asoschi", role="founder"))
db.commit()
t = models.Teacher(full_name="Ustoz", branch_id=B["Zafar"], is_active=1,
                   grade="middle", hired_date=date(2026, 1, 1))
db.add(t)
db.commit()


def mk_group(nm, br, price):
    g = models.Group(name=nm, teacher_id=t.id, branch_id=B[br],
                     subject="english", lesson_days="mon,wed,fri",
                     lesson_time="09:00", start_date=date(2026, 7, 1),
                     lesson_price=price, monthly_fee=price * 12,
                     standard_lessons_per_month=12)
    db.add(g)
    db.commit()
    return g


G = {
    "ielts": mk_group("IELTS intro", "Zafar", 40000),
    "bek": mk_group("Cambridge", "Bekobod 1", 40000),
    "z45": mk_group("Yangi 45", "Zafar", 45000),        # allaqachon 540k
    "odd": mk_group("Alohida narx", "Zafar", 30000),    # g'alati — tegilmasin
    "stariki": mk_group("Stariki", "Stretinko", 40000), # xato 480k
    "nevada_ok": mk_group("Nevada OK", "Stretinko", 35000),
    "it": mk_group("IT Python", "Stetch", 40000),        # hamkor — tegilmasin
}


def mk_student(nm, g, enrolled, sep_amount=None, aug=False, disc=None,
               status="active", locked=None):
    s = models.Student(full_name=nm, branch_id=g.branch_id, group_id=g.id,
                       status=status, enrolled_date=enrolled,
                       locked_lesson_price=locked)
    db.add(s)
    db.commit()
    if aug:
        db.add(models.Payment(student_id=s.id, amount=-480000,
                              kind="charge", period="2026-08",
                              note="avgust", created_by="avtomat",
                              created_at=datetime(2026, 8, 1, 3)))
    if sep_amount is not None:
        db.add(models.Payment(student_id=s.id, amount=-sep_amount,
                              kind="charge", period="2026-09",
                              note=f"{g.name} — 2026-09: 12 dars (standart oy, avtomat)",
                              created_by="avtomat",
                              created_at=datetime(2026, 9, 1, 3)))
    if disc:
        db.add(models.Discount(student_id=s.id, percent=disc,
                               kind="individual", status="active",
                               reason="test"))
    db.commit()
    return s.id


S = {}
S["eski_avg"] = mk_student("Eski Avgustli", G["ielts"], date(2026, 8, 6),
                           480000, aug=True)
S["eski_lcup"] = mk_student("Eski LCUP", G["bek"], date(2026, 8, 6),
                            480000)              # avgust hisobi LC UP da
S["eski_mart"] = mk_student("Eski Martli", G["ielts"], date(2026, 3, 1),
                            480000)
S["yangi"] = mk_student("Ubaydullaev Elmurod", G["ielts"],
                        date(2026, 9, 4), 480000)   # XATO: 540k bo'lishi kerak
S["yangi_ok"] = mk_student("Yangi To'g'ri", G["z45"], date(2026, 9, 2),
                           540000)
S["yangi_hisobsiz"] = mk_student("Yangi Hisobsiz", G["bek"],
                                 date(2026, 9, 3))   # hali hisoblanmagan
S["str_xato"] = mk_student("Komilova Farangiz", G["stariki"],
                           date(2026, 8, 6), 480000)   # XATO: 420k
S["str_ok"] = mk_student("Stretinko To'g'ri", G["nevada_ok"],
                         date(2026, 8, 6), 420000)
S["it"] = mk_student("IT Bola", G["it"], date(2026, 9, 2), 480000)
S["chegirma"] = mk_student("Chegirmali Yangi", G["ielts"],
                           date(2026, 9, 2), 480000, disc=10)
S["muz"] = mk_student("Muzlatilgan Eski", G["ielts"], date(2026, 8, 6),
                      None, aug=True, status="frozen")
S["odd"] = mk_student("Alohida Narxli", G["odd"], date(2026, 8, 6),
                      360000, aug=True)
GID = {k: g.id for k, g in G.items()}
db.close()


def charge(sid, period="2026-09"):
    db = SessionLocal()
    rows = db.query(models.Payment).filter(
        models.Payment.student_id == sid, models.Payment.kind == "charge",
        models.Payment.period == period).all()
    out = (len(rows), round(sum(-r.amount for r in rows)))
    db.close()
    return out


def lock(sid):
    db = SessionLocal()
    v = db.query(models.Student).get(sid).locked_lesson_price
    db.close()
    return v


def gprice(key):
    db = SessionLocal()
    v = db.query(models.Group).get(GID[key]).lesson_price
    db.close()
    return v


print("=== 1. QO'LLASH ===")
db = SessionLocal()
res = courses.apply_sept_2026_pricing(db, today=date(2026, 9, 5))
db.close()
print("   natija:", res)
ck("eskilar qulflandi (3 ta)", res["locked"], 3)
ck("asosiy guruhlar 45 000 ga (2 ta)", res["groups_up"], 2)
ck("Stretinko guruhi 35 000 ga (1 ta)", res["groups_stretinko"], 1)
ck("yangi o'quvchi tuzatildi (1 ta)", res["fixed_new"], 1)
ck("Stretinko o'quvchisi tuzatildi (1 ta)", res["fixed_stretinko"], 1)

print("\n=== 2. GURUH NARXLARI ===")
ck("IELTS intro 45 000", gprice("ielts"), 45000)
ck("Cambridge 45 000", gprice("bek"), 45000)
ck("Stariki 35 000", gprice("stariki"), 35000)
ck("Nevada OK 35 000 (edi)", gprice("nevada_ok"), 35000)
ck("allaqachon 45 000 — tegilmadi", gprice("z45"), 45000)
ck("g'alati 30 000 — tegilmadi", gprice("odd"), 30000)
ck("IT (Stetch) — tegilmadi", gprice("it"), 40000)
db = SessionLocal()
ck("oylik summa ham yangilandi",
   db.query(models.Group).get(GID["ielts"]).monthly_fee, 540000)
db.close()

print("\n=== 3. ESKILAR 480 000 DA QOLDI ===")
ck("avgustli: qulf 40 000", lock(S["eski_avg"]), 40000)
ck("LC UP li (avgust hisobi yo'q, lekin avgustda kelgan): qulf 40 000",
   lock(S["eski_lcup"]), 40000)
ck("martli: qulf 40 000", lock(S["eski_mart"]), 40000)
ck("eskining sentabr hisobi 480 000 ligicha", charge(S["eski_avg"]),
   (1, 480000))
ck("muzlatilganga qulf QO'YILMADI", lock(S["muz"]), None)
ck("g'alati narxli guruh o'quvchisiga qulf qo'yilmadi",
   lock(S["odd"]), None)
db = SessionLocal()
g_ = db.query(models.Group).get(GID["ielts"])
s_ = db.query(models.Student).get(S["eski_avg"])
ck("eskining keyingi oy narxi ham 40 000",
   billing.student_lesson_price(s_, g_), 40000)
db.close()

print("\n=== 4. YANGILAR 540 000 ===")
ck("Ubaydullaev: 480 000 -> 540 000 (bitta qator)",
   charge(S["yangi"]), (1, 540000))
ck("yangiga qulf yo'q", lock(S["yangi"]), None)
ck("to'g'ri hisoblangan yangi o'zgarmadi", charge(S["yangi_ok"]),
   (1, 540000))
db = SessionLocal()
g_ = db.query(models.Group).get(GID["bek"])
s_ = db.query(models.Student).get(S["yangi_hisobsiz"])
ck("hali hisoblanmagan yangi endi 45 000 dan hisoblanadi",
   billing.student_lesson_price(s_, g_), 45000)
db.close()

print("\n=== 5. STRETINKO 420 000 ===")
ck("Komilova: 480 000 -> 420 000", charge(S["str_xato"]), (1, 420000))
ck("to'g'ri Stretinko o'zgarmadi", charge(S["str_ok"]), (1, 420000))
ck("Stretinko eskisiga qulf qo'yilmadi (hamma 420k)",
   lock(S["str_xato"]), None)

print("\n=== 6. TEGILMASLIGI KERAKLAR ===")
ck("IT (Stetch) hisobi o'zgarmadi", charge(S["it"]), (1, 480000))
ck("chegirmali yangi — qo'lda ko'riladi, tegilmadi",
   charge(S["chegirma"]), (1, 480000))
ck("g'alati narxli guruh hisobi o'zgarmadi", charge(S["odd"]),
   (1, 360000))

print("\n=== 7. AUDIT VA TARIX ===")
db = SessionLocal()
a = db.query(models.AuditLog).filter(
    models.AuditLog.entity == "payment",
    models.AuditLog.note.like("Sentabr 2026 narx qoidasi%")).all()
ck("2 ta tuzatish auditda", len(a), 2)
p = db.query(models.Payment).filter(
    models.Payment.student_id == S["yangi"],
    models.Payment.kind == "charge").first()
ck("izohda tuzatish sababi", "narx tuzatish" in (p.note or ""), True)
ck("izohda eski summa ham", "480 000" in (p.note or ""), True)
db.close()

print("\n=== 8. IKKINCHI MARTA HECH NIMA QILMAYDI ===")
db = SessionLocal()
res2 = courses.apply_sept_2026_pricing(db, today=date(2026, 9, 5))
db.close()
ck("idempotent", sum(v for k, v in res2.items()
                     if k != "skipped_groups"), 0)
ck("Ubaydullaev hamon 540 000", charge(S["yangi"]), (1, 540000))

print("\n=== 9. HAQIQIY YO'L: FAOLLASHTIRISH ENDI 540 000 ===")
H = tok("asos")
db = SessionLocal()
s_new = models.Student(full_name="Bugun Kelgan", branch_id=B["Zafar"],
                       group_id=GID["ielts"], status="trial",
                       enrolled_date=date(2026, 9, 5))
db.add(s_new)
db.commit()
NID = s_new.id
db.close()
r = client.post(f"/api/students/{NID}/activate", headers=H,
                json={"on": "2026-09-01"})
ck("faollashtirildi", r.status_code, 200)
ck("sentabr hisobi 540 000", charge(NID), (1, 540000))

print("\n" + ("BARCHASI OK" if not fails else f"XATOLAR: {fails}"))
sys.exit(1 if fails else 0)
