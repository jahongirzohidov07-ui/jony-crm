"""JONY SHOP — SOVG'A SO'ROVI ADMINGA VAZIFA BO'LIB BORADI (2026-08-16).

Jahongir: "ichida Do'konni qoshmabmiz nega coin yigyabdi nimadur
sotib olishi kerakku, sotib olgandan keyin masalan skidka sotib olsa
avtomat hisobiga ishlasin oldin men aytgan usulda senga. sovga yutib
olsa adminlarga vazifa bolib borsin falonchi coinga shu narsa
olmoqchi deb".

Bu test SOVG'A yo'lini tekshiradi (chegirma yo'li test_coin_shop.py
da). Asosiy savol: o'quvchi tugma bosgandan keyin xodim buni
KO'RADIMI va ish tugagach vazifa YOPILADIMI.
"""
import os, sys
os.environ["DATABASE_URL"] = "sqlite:////tmp/shopgift.db"
if os.path.exists("/tmp/shopgift.db"):
    os.remove("/tmp/shopgift.db")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fastapi.testclient import TestClient          # noqa: E402
import main, models, roles                         # noqa: E402
import entry                                       # noqa: E402
from database import SessionLocal                  # noqa: E402
from auth import hash_password                     # noqa: E402
from common import _student_coin_balance           # noqa: E402

c = TestClient(main.app)
fails = []


def ck(n, g, w):
    ok = g == w
    print(("OK  " if ok else "MUAMMO ") + n + f": {g}"
          + ("" if ok else f" (kutilgan {w})"))
    if not ok:
        fails.append(n)


db = SessionLocal()
b = models.Branch(name="Bekobod 1"); db.add(b); db.commit(); BID = b.id
b2 = models.Branch(name="Chinoz"); db.add(b2); db.commit(); BID2 = b2.id
g = models.Group(name="G1", branch_id=BID, monthly_fee=400000,
                 lesson_price=50000, standard_lessons_per_month=8)
db.add(g); db.commit(); GID = g.id
st = models.Student(full_name="Nazarov Doniyor", branch_id=BID,
                    status="active", group_id=GID, phone="+998901112233")
db.add(st); db.commit(); SID = st.id
db.add(models.CoinEntry(student_id=SID, amount=500, source="manual",
                        note="boshlang'ich", created_by="Admin"))
u = models.User(username="oquvchi", full_name="Nazarov Doniyor",
                role="student", branch_id=BID,
                password_hash=hash_password("x"), is_active=1)
db.add(u); db.commit()
st.user_id = u.id
db.add_all([
    models.User(username="asos", full_name="Asoschi", role="founder",
                password_hash=hash_password("x"), is_active=1),
    # ATAYLAB boshqa filialda ham administrator bor: vazifa O'Z
    # filialidagi odamga tushishi kerak.
    models.User(username="adm2", full_name="Chinoz Admin",
                role="administrator", branch_id=BID2,
                password_hash=hash_password("x"), is_active=1),
    models.User(username="adm", full_name="Bekobod Admin",
                role="administrator", branch_id=BID,
                password_hash=hash_password("x"), is_active=1),
])
db.commit()
ADM_ID = db.query(models.User).filter(
    models.User.username == "adm").first().id
db.close()


def tok(u_):
    return {"Authorization": "Bearer " + c.post(
        "/api/auth/login", json={"username": u_, "password": "x"})
        .json()["access_token"]}


F, A, S = tok("asos"), tok("adm"), tok("oquvchi")

print("=== 1. Do'kon o'quvchiga ko'rinadi ===")
r = c.post("/api/rewards", headers=F, json={
    "name": "Quloqchin", "cost": 300, "category": "tech",
    "branch_id": BID})
ck("sovg'a yaratildi", r.status_code, 200)
GIFT = r.json()["id"]
r = c.get("/api/me/coins", headers=S)
ck("do'kon ochildi", r.status_code, 200)
d = r.json()
ck("balans 500", d["balance"], 500)
ck("band coin yo'q", d["held"], 0)
ck("sovg'a ro'yxatda", any(x["name"] == "Quloqchin" for x in d["rewards"]),
   True)
item = [x for x in d["rewards"] if x["id"] == GIFT][0]
ck("yetadi deb belgilangan", item["affordable"], True)
ck("turi sovg'a", item["kind"], "gift")

print("\n=== 2. O'quvchi sovg'ani so'raydi ===")
r = c.post(f"/api/me/rewards/{GIFT}", headers=S)
ck("so'rov qabul qilindi", r.status_code, 200)
RED = r.json()["id"]
ck("holati so'raldi", r.json()["status"], "requested")
db = SessionLocal()
ck("coin HALI yechilmadi", _student_coin_balance(db, SID), 500)
db.close()
r = c.get("/api/me/coins", headers=S)
ck("300 coin band bo'ldi", r.json()["held"], 300)
ck("ishlatsa bo'ladigani 200", r.json()["available"], 200)

print("\n=== 3. Adminga VAZIFA tushdi ===")
db = SessionLocal()
t = (db.query(models.Task)
     .filter(models.Task.title == f"Sovg'a so'rovi #R{RED}").first())
ck("vazifa yaratildi", t is not None, True)
ck("o'quvchi ismi bor", "Nazarov Doniyor" in (t.description or ""), True)
ck("sovg'a nomi bor", "Quloqchin" in (t.description or ""), True)
ck("coin soni bor", "300 coin" in (t.description or ""), True)
ck("O'Z filialidagi adminga tushdi", t.assignee_id, ADM_ID)
ck("filial to'g'ri", t.branch_id, BID)
ck("ochiq holatda", t.status, "new")
db.close()

print("\n=== 4. Coin yetmasa so'rab bo'lmaydi ===")
r = c.post("/api/rewards", headers=F, json={
    "name": "Noutbuk", "cost": 5000, "branch_id": BID})
BIG = r.json()["id"]
r = c.post(f"/api/me/rewards/{BIG}", headers=S)
ck("400 qaytadi", r.status_code, 400)
ck("sababi tushunarli", "Coin yetarli emas" in str(r.json()), True)
r = c.post(f"/api/me/rewards/{GIFT}", headers=S)
ck("band coin hisobga olinadi (200 < 300)", r.status_code, 400)

print("\n=== 5. Admin ro'yxatda ko'radi ===")
r = c.get("/api/rewards/requests?status_filter=requested", headers=A)
ck("ro'yxat ochildi", r.status_code, 200)
rows = r.json()["rows"]
ck("bitta so'rov", len(rows), 1)
ck("o'zi so'ragani belgilangan", rows[0]["by_student"], True)
ck("o'quvchi ismi", rows[0]["student"], "Nazarov Doniyor")

print("\n=== 6. Sovg'a berildi — coin yechiladi, vazifa yopiladi ===")
r = c.post(f"/api/rewards/requests/{RED}/give", headers=A,
           json={"give": True})
ck("berildi", r.status_code, 200)
ck("holati", r.json()["status"], "given")
db = SessionLocal()
ck("coin endi yechildi", _student_coin_balance(db, SID), 200)
t = (db.query(models.Task)
     .filter(models.Task.title == f"Sovg'a so'rovi #R{RED}").first())
ck("vazifa yopildi", t.status, "done")
ck("natija yozildi", "berildi" in (t.result or "").lower(), True)
ck("yopilgan vaqt bor", t.done_at is not None, True)
db.close()
r = c.get("/api/me/coins", headers=S)
ck("band coin qolmadi", r.json()["held"], 0)
ck("balans 200", r.json()["balance"], 200)

print("\n=== 7. O'quvchining bildirishnomasida chiqadi ===")
r = c.get("/api/student/notifications", headers=S)
ck("bildirishnoma ochildi", r.status_code, 200)
items = r.json()["items"]
gift_n = [x for x in items if x["kind"] == "reward"]
ck("sovg'a xabari bor", len(gift_n), 1)
ck("sarlavhada nomi bor", "Quloqchin" in gift_n[0]["title"], True)

print("\n=== 8. Rad etilganda coin qaytadi ===")
db = SessionLocal()
db.add(models.CoinEntry(student_id=SID, amount=300, source="manual",
                        note="qo'shimcha", created_by="Admin"))
db.commit(); db.close()
r = c.post(f"/api/me/rewards/{GIFT}", headers=S)
RED2 = r.json()["id"]
ck("ikkinchi so'rov ochildi", r.status_code, 200)
db = SessionLocal()
t2 = (db.query(models.Task)
      .filter(models.Task.title == f"Sovg'a so'rovi #R{RED2}").first())
ck("yangi vazifa ham ochildi", t2 is not None, True)
db.close()
r = c.post(f"/api/rewards/requests/{RED2}/give", headers=A,
           json={"give": False, "note": "Omborda tugagan"})
ck("rad etildi", r.json()["status"], "rejected")
db = SessionLocal()
ck("coin YECHILMADI", _student_coin_balance(db, SID), 500)
t2 = (db.query(models.Task)
      .filter(models.Task.title == f"Sovg'a so'rovi #R{RED2}").first())
ck("vazifa yopildi", t2.status, "done")
ck("natijada rad etilgani ko'rinadi",
   "rad etildi" in (t2.result or "").lower(), True)
db.close()
r = c.get("/api/me/coins", headers=S)
ck("band coin bo'shadi", r.json()["held"], 0)
ck("ishlatsa bo'ladigani 500", r.json()["available"], 500)

print("\n=== 9. O'quvchi o'zi bekor qilsa ham coin qaytadi ===")
r = c.post(f"/api/me/rewards/{GIFT}", headers=S)
RED3 = r.json()["id"]
ck("uchinchi so'rov", r.status_code, 200)
ck("band bo'ldi", c.get("/api/me/coins", headers=S).json()["held"], 300)
r = c.delete(f"/api/me/rewards/{RED3}", headers=S)
ck("bekor qilindi", r.status_code, 200)
ck("band bo'shadi", c.get("/api/me/coins", headers=S).json()["held"], 0)
db = SessionLocal()
ck("coin o'zgarmadi", _student_coin_balance(db, SID), 500)
db.close()

print("\n=== 10. Ikki marta berib bo'lmaydi ===")
r = c.post(f"/api/rewards/requests/{RED}/give", headers=A,
           json={"give": True})
ck("takroriy berish rad etiladi", r.status_code, 400)

print("\n" + ("HAMMASI OK" if not fails
              else f"{len(fails)} ta muammo: {fails}"))
sys.exit(1 if fails else 0)
