"""KURSLAR + HAMKOR FILIAL (2026-08-15).

Jahongir: "hamkorlikda ochgan Stech o'quv markazimi ham bor ... uni
men umuman boshqarmayman, faqat asoschi sifatida 40% ulushim bor,
shogirdim Husayn 60% ulushi bor va ozi boshqaradi ... alohida filial
qilib ochib to'lovlarini o'zlari beglialyidan qilsa bolarkan masalan
sozlamalar ichida kurslar bolimini ochib u yerda kurslarni yozadi
dars vaqti narxini bitta darsga narxini yozadi, shu narxlar hamma
joyga ulanadi ... bizda ham sentabrdan narxlar oshadi".
"""
import os, sys
from datetime import date, timedelta
os.environ["DATABASE_URL"] = "sqlite:////tmp/courses.db"
if os.path.exists("/tmp/courses.db"):
    os.remove("/tmp/courses.db")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fastapi.testclient import TestClient          # noqa: E402
import main, models, roles                         # noqa: E402
import entry                                       # noqa: E402
from database import SessionLocal                  # noqa: E402
from auth import hash_password                     # noqa: E402
import common                                      # noqa: E402

c = TestClient(main.app)
fails = []


def ck(n, g, w):
    ok = g == w
    print(("OK  " if ok else "XATO ") + n + f": {g}"
          + ("" if ok else f" (kutilgan {w})"))
    if not ok:
        fails.append(n)


db = SessionLocal()
b1 = models.Branch(name="Bekobod 1")
b2 = models.Branch(name="Stech", is_partner=1,
                   partner_note="Husayn boshqaradi", owner_percent=40)
db.add_all([b1, b2]); db.commit()
B1, STECH = b1.id, b2.id
common.reset_partner_cache()
# Jony guruhi va o'quvchisi
g1 = models.Group(name="Jony G1", branch_id=B1, lesson_price=50000,
                  standard_lessons_per_month=8, monthly_fee=400000)
db.add(g1); db.commit()
s1 = models.Student(full_name="Jony O'quvchi", branch_id=B1,
                    status="active", group_id=g1.id)
db.add(s1); db.commit(); SID1 = s1.id
db.add(models.Payment(student_id=s1.id, amount=400000, kind="payment",
                      method="cash", created_by="Admin"))
# Stech guruhi va o'quvchisi
g2 = models.Group(name="Stech G1", branch_id=STECH, lesson_price=30000,
                  standard_lessons_per_month=12, monthly_fee=360000)
db.add(g2); db.commit()
s2 = models.Student(full_name="Stech O'quvchi", branch_id=STECH,
                    status="active", group_id=g2.id)
db.add(s2); db.commit()
db.add(models.Payment(student_id=s2.id, amount=1000000, kind="payment",
                      method="cash", created_by="Husayn"))
db.commit()
G1, G2 = g1.id, g2.id      # id larni sessiya yopilmasdan olamiz
db.add_all([
    models.User(username="asos", full_name="Asoschi", role="founder",
                password_hash=hash_password("x"), is_active=1),
    models.User(username="husayn", full_name="Husayn",
                role="branch_manager", branch_id=STECH,
                password_hash=hash_password("x"), is_active=1),
    models.User(username="rahbar", full_name="Bekobod rahbari",
                role="branch_manager", branch_id=B1,
                password_hash=hash_password("x"), is_active=1),
])
db.commit(); db.close()


def tok(u):
    return {"Authorization": "Bearer " + c.post(
        "/api/auth/login", json={"username": u, "password": "x"})
        .json()["access_token"]}


F, H, R = tok("asos"), tok("husayn"), tok("rahbar")

print("=== 1. HAMKOR filial umumiy ro'yxatga KIRMAYDI ===")
r = c.get("/api/students", headers=F)
names = [x["full_name"] for x in r.json()]
ck("Jony o'quvchisi bor", "Jony O'quvchi" in names, True)
ck("Stech o'quvchisi YO'Q", "Stech O'quvchi" in names, False)
r = c.get("/api/groups", headers=F)
gn = [x["name"] for x in r.json()]
ck("Stech guruhi ham yo'q", "Stech G1" in gn, False)

print("\n=== 2. Lekin FILIALNI TANLAB ko'rish mumkin ===")
r = c.get(f"/api/students?branch_id={STECH}", headers=F)
ck("tanlanganda ko'rinadi",
   [x["full_name"] for x in r.json()], ["Stech O'quvchi"])

print("\n=== 3. Umumiy MOLIYA raqamlariga ham qo'shilmaydi ===")
r = c.get("/api/dashboard", headers=F)
d = r.json()
ck("faqat Jony o'quvchisi sanaldi", d["active_students"], 1)
ck("Stech puli tushumga kirmadi", d["month_income"], 400000)
r = c.get(f"/api/dashboard?branch_id={STECH}", headers=F)
ck("Stech tanlansa o'z puli", r.json()["month_income"], 1000000)

print("\n=== 4. Husayn FAQAT Stech'ni ko'radi ===")
r = c.get("/api/students", headers=H)
ck("faqat o'z o'quvchisi",
   [x["full_name"] for x in r.json()], ["Stech O'quvchi"])
r = c.get(f"/api/students?branch_id={B1}", headers=H)
ck("Jony filialini so'rasa ham ko'rmaydi",
   any(x["full_name"] == "Jony O'quvchi" for x in r.json()), False)

print("\n=== 5. Husayn O'Z KURSINI yaratadi ===")
r = c.post("/api/courses", headers=H, json={
    "name": "Ingliz tili — Beginner", "subject": "english",
    "lesson_minutes": 60, "lesson_price": 30000,
    "lessons_per_month": 12})
ck("kurs yaratildi", r.status_code, 200)
CID = r.json()["id"]
ck("filial o'zi qo'yildi", r.json()["branch_id"], STECH)
ck("oylik narx hisoblandi", r.json()["monthly_fee"], 360000)
ck("dars vaqti saqlandi", r.json()["lesson_minutes"], 60)

print("\n=== 6. Boshqa filialga kurs qo'sha olmaydi ===")
r = c.post("/api/courses", headers=H, json={
    "name": "Chet kurs", "lesson_price": 10000, "branch_id": B1})
ck("403", r.status_code, 403)

print("\n=== 7. Kurs ro'yxati filialga bo'linadi ===")
r = c.get("/api/courses", headers=H)
ck("Husaynda 1 ta", len(r.json()), 1)
r = c.get("/api/courses", headers=R)
ck("Bekobod rahbarida 0 ta", len(r.json()), 0)

print("\n=== 8. Guruh kursni tanlasa NARX kursdan olinadi ===")
r = c.put(f"/api/groups/{G2}", headers=H, json={"course_id": CID})
ck("guruh yangilandi", r.status_code, 200)
db = SessionLocal()
gg = db.query(models.Group).get(G2)
ck("dars narxi kursdan", gg.lesson_price, 30000)
ck("oyiga dars soni kursdan", gg.standard_lessons_per_month, 12)
ck("oylik narx", gg.monthly_fee, 360000)
db.close()

print("\n=== 9. Kurs narxi o'zgarsa GURUHGA ko'chadi ===")
r = c.put(f"/api/courses/{CID}", headers=H, json={"lesson_price": 35000})
ck("kurs yangilandi", r.status_code, 200)
ck("1 ta guruhga ko'chdi", r.json()["groups_updated"], 1)
db = SessionLocal()
ck("guruh narxi yangilandi",
   db.query(models.Group).get(G2).lesson_price, 35000)
ck("oylik ham", db.query(models.Group).get(G2).monthly_fee, 420000)
db.close()

print("\n=== 10. \"O'z narxi\" belgilangan guruhga TEGMAYDI ===")
c.put(f"/api/groups/{G2}", headers=H, json={"price_manual": True})
db = SessionLocal()
gg = db.query(models.Group).get(G2); gg.lesson_price = 99000
db.commit(); db.close()
r = c.put(f"/api/courses/{CID}", headers=H, json={"lesson_price": 40000})
ck("hech qaysi guruhga ko'chmadi", r.json()["groups_updated"], 0)
db = SessionLocal()
ck("guruh narxi saqlanib qoldi",
   db.query(models.Group).get(G2).lesson_price, 99000)
gg = db.query(models.Group).get(G2); gg.price_manual = 0
gg.lesson_price = 40000
db.commit(); db.close()

print("\n=== 11. SENTABRDAN narx oshishi (Jony uchun) ===")
r = c.post("/api/courses", headers=F, json={
    "name": "Multilevel", "subject": "english", "lesson_price": 50000,
    "lessons_per_month": 8, "branch_id": B1})
JC = r.json()["id"]
c.put(f"/api/groups/{G1}", headers=F, json={"course_id": JC})
sep = date(roles.local_today().year, 9, 1)
if sep <= roles.local_today():
    sep = date(roles.local_today().year + 1, 9, 1)
r = c.post(f"/api/courses/{JC}/price-change", headers=F, json={
    "from_date": sep.isoformat(), "lesson_price": 60000,
    "note": "Sentabrdan narx oshdi"})
ck("reja qabul qilindi", r.status_code, 200)
ck("hozir qo'llanmadi", r.json()["applied_now"], False)
db = SessionLocal()
ck("guruh narxi HOZIRCHA eski",
   db.query(models.Group).get(G1).lesson_price, 50000)
db.close()
r = c.get("/api/courses", headers=F)
jc = [x for x in r.json() if x["id"] == JC][0]
ck("kutayotgan o'zgarish ko'rinadi",
   jc["next_change"]["lesson_price"], 60000)

print("\n=== 12. Sana kelganda AVTOMAT qo'llanadi ===")
db = SessionLocal()
ch = (db.query(models.CoursePriceChange)
      .filter(models.CoursePriceChange.course_id == JC).first())
ch.from_date = roles.local_today()          # sana keldi deb qo'yamiz
db.commit(); db.close()
import courses as CRS                              # noqa: E402
db = SessionLocal()
n = CRS.apply_due_price_changes(db)
ck("qo'llandi", n, 1)
ck("kurs narxi yangilandi",
   db.query(models.Course).get(JC).lesson_price, 60000)
ck("guruh narxi ham",
   db.query(models.Group).get(G1).lesson_price, 60000)
n2 = CRS.apply_due_price_changes(db)
ck("ikkinchi marta qo'llanmaydi", n2, 0)
db.close()

print("\n=== 13. O'TGAN OYLAR hisobi TEGILMAYDI ===")
db = SessionLocal()
ck("eski to'lov o'zgarmadi",
   db.query(models.Payment).filter(
       models.Payment.student_id == SID1).first().amount, 400000)
db.close()

print("\n=== 14. Guruhi bor kurs o'chirilmaydi ===")
r = c.delete(f"/api/courses/{JC}", headers=F)
ck("400 va tushuntirish", r.status_code, 400)
ck("sabab aytilgan", "guruh bor" in str(r.json()), True)

print("\n=== 15. Husayn Jony kursini tahrirlay olmaydi ===")
r = c.put(f"/api/courses/{JC}", headers=H, json={"lesson_price": 1})
ck("403", r.status_code, 403)

print("\n=== 16. ESKI NARX HIMOYASI (sentabrdan narx oshadi) ===")
# Jony guruhiga uch xil o'quvchi: faol, muzlatilgan va keyin qo'shiladigan
db = SessionLocal()
gj = db.query(models.Group).get(G1)
gj.lesson_price = 50000; gj.standard_lessons_per_month = 8
db.commit()
old_st = models.Student(full_name="Eski O'quvchi", branch_id=B1,
                        status="active", group_id=G1)
frz = models.Student(full_name="Muzlatilgan", branch_id=B1,
                     status="frozen", group_id=G1)
db.add_all([old_st, frz]); db.commit()
OLD_ID, FRZ_ID = old_st.id, frz.id
db.close()

r = c.post(f"/api/courses/{JC}/price-change", headers=F, json={
    "from_date": roles.local_today().isoformat(),
    "lesson_price": 70000,
    "keep_old_for_active": True,
    "note": "Sentabrdan narx oshdi"})
ck("qo'llandi", r.json()["applied_now"], True)
# 12-bandda ham qulflangan edi (o'sha o'zgarishda ham himoya yoqilgan),
# shuning uchun bu safar YANGI qo'shilgan faol o'quvchi qulflanadi
ck("eski o'quvchilar qulflandi", r.json()["locked_students"] >= 1, True)

db = SessionLocal()
ck("FAOL o'quvchida eski narx qulflandi",
   db.query(models.Student).get(OLD_ID).locked_lesson_price, 50000)
ck("MUZLATILGANDA qulf yo'q",
   db.query(models.Student).get(FRZ_ID).locked_lesson_price, None)
ck("guruh narxi yangi", db.query(models.Group).get(G1).lesson_price, 70000)
db.close()

print("\n=== 17. Hisob-kitob har kimga o'z narxida ===")
import billing as _B                                # noqa: E402
db = SessionLocal()
g = db.query(models.Group).get(G1)
ck("eski o'quvchiga 50 000",
   _B.student_lesson_price(db.query(models.Student).get(OLD_ID), g), 50000)
# Yangi kelgan o'quvchi
new_st = models.Student(full_name="Yangi O'quvchi", branch_id=B1,
                        status="active", group_id=G1)
db.add(new_st); db.commit(); NEW_ID = new_st.id
ck("yangi kelganga 70 000",
   _B.student_lesson_price(new_st, g), 70000)
db.close()

print("\n=== 18. Muzlatib qaytgan YANGI narxda ===")
db = SessionLocal()
st = db.query(models.Student).get(OLD_ID)
st.status = "frozen"        # avgustda muzlatdi
db.commit()
ck("muzlatilganda qulf O'ZI ochildi", st.locked_lesson_price, None)
st.status = "active"        # qaytib keldi
db.commit()
ck("qaytgach yangi narx",
   _B.student_lesson_price(st, db.query(models.Group).get(G1)), 70000)
db.close()

print("\n=== 19. Qulfni qo'lda ochish/qo'yish ===")
r = c.post(f"/api/students/{NEW_ID}/price-lock", headers=F,
           json={"price": 55000, "note": "Kelishuv bo'yicha"})
ck("qulf qo'yildi", r.json()["locked_lesson_price"], 55000)
r = c.post(f"/api/students/{NEW_ID}/price-lock", headers=F, json={})
ck("qulf ochildi", r.json()["locked_lesson_price"], None)

print("\n=== 20. Narx kartasida ko'rinadi ===")
db = SessionLocal()
st = db.query(models.Student).get(NEW_ID)
st.locked_lesson_price = 50000
db.commit(); db.close()
r = c.get(f"/api/students/{NEW_ID}/pricing", headers=F)
d = r.json()
ck("qulflangan narx ko'rsatilgan", d["locked_lesson_price"], 50000)
ck("oylik eski narxdan hisoblandi", d["base_fee"], 400000)
ck("joriy narx ham ko'rinadi", d["current_lesson_price"], 70000)

print("\n=== 21. Himoyasiz o'zgartirish — hamma yangi narxda ===")
r = c.post(f"/api/courses/{JC}/price-change", headers=F, json={
    "from_date": roles.local_today().isoformat(),
    "lesson_price": 80000, "keep_old_for_active": False})
ck("qo'llandi", r.json()["applied_now"], True)
ck("hech kim qulflanmadi", r.json()["locked_students"], 0)

print("\n" + ("HAMMASI OK" if not fails
              else f"{len(fails)} ta XATO: {fails}"))
sys.exit(1 if fails else 0)
