"""GURUHDAN CHIQARISH (2026-08-15).

Jahongir: "birorta oquvchi guruhsiz lekin faol bola olmaydi guruhdan
chiqarildimi u faol emas endi" + "guruhdan chiqqanda avtomat shu
kungacha qatnashgan darslarini hisoblanib hisobi ham togrlanishi
kerak, va guruhsiz bolishi kerak talab qarzi bolsa qarzdorlarda,
qarzi yoq bolsa arxivga tushsin".
"""
import os, sys
from datetime import date, timedelta
os.environ["DATABASE_URL"] = "sqlite:////tmp/leavegrp.db"
if os.path.exists("/tmp/leavegrp.db"):
    os.remove("/tmp/leavegrp.db")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fastapi.testclient import TestClient          # noqa: E402
import main, models, roles                         # noqa: E402
import entry                                       # noqa: E402
from database import SessionLocal                  # noqa: E402
from auth import hash_password                     # noqa: E402
from common import student_balance                 # noqa: E402

c = TestClient(main.app)
fails = []


def ck(n, g, w):
    ok = g == w
    print(("OK  " if ok else "XATO ") + n + f": {g}"
          + ("" if ok else f" (kutilgan {w})"))
    if not ok:
        fails.append(n)


today = roles.local_today()
first = today.replace(day=1)
db = SessionLocal()
b = models.Branch(name="Bekobod 1"); db.add(b); db.commit(); BID = b.id
g = models.Group(name="G1", branch_id=BID, lesson_price=50000,
                 standard_lessons_per_month=8, monthly_fee=400000)
db.add(g); db.commit(); GID = g.id
# 8 dars: 4 tasi O'TILGAN (bugungacha), 4 tasi hali yo'q
for i in range(4):
    db.add(models.Lesson(group_id=GID, date=first + timedelta(days=i),
                         held=1))
for i in range(4):
    db.add(models.Lesson(group_id=GID, date=today + timedelta(days=i + 1),
                         held=0))
db.commit()


def mk(name, paid):
    st = models.Student(full_name=name, branch_id=BID, status="active",
                        group_id=GID, enrolled_date=first)
    db.add(st); db.commit()
    # Oy boshida BUTUN oy uchun yechilgan: 8 dars x 50 000
    db.add(models.Payment(student_id=st.id, amount=-400000, kind="charge",
                          period=f"{today.year:04d}-{today.month:02d}",
                          created_by="avtomat (oylik)"))
    if paid:
        db.add(models.Payment(student_id=st.id, amount=paid,
                              kind="payment", method="cash",
                              created_by="Admin"))
    db.commit()
    return st.id


TOLAGAN = mk("To'lagan Bola", 400000)      # to'liq to'lagan
QARZDOR = mk("Qarzdor Bola", 0)            # umuman to'lamagan
db.add(models.User(username="asos", full_name="Asoschi", role="founder",
                   password_hash=hash_password("x"), is_active=1))
db.commit(); db.close()

H = {"Authorization": "Bearer " + c.post(
    "/api/auth/login", json={"username": "asos", "password": "x"})
    .json()["access_token"]}

print("=== 1. Sababsiz chiqarib bo'lmaydi ===")
# 2026-08-24: endi KATEGORIYA ham majburiy (Jahongir: "ketish
# sababini majburiy qil") — ikkalasi ham tekshiriladi.
r = c.post(f"/api/students/{TOLAGAN}/remove-from-group", headers=H,
           json={"reason": "", "reason_code": "unknown"})
ck("400", r.status_code, 400)

print("\n=== 2. To'lagan o'quvchi: ortiqcha pul QAYTADI, arxivga ===")
db = SessionLocal()
ck("chiqishdan oldin balans 0", student_balance(db, TOLAGAN), 0)
db.close()
r = c.post(f"/api/students/{TOLAGAN}/remove-from-group", headers=H,
           json={"reason": "Boshqa shaharga ko'chib ketdi",
                 "reason_code": "moved"})
ck("200", r.status_code, 200)
d = r.json()
ck("arxivga tushdi", d["archived"], True)
ck("holati arxiv", d["status"], "archived")
ck("4 ta o'tilgan dars hisoblandi", d["recalc"]["lessons"], 4)
ck("200 000 qaytarildi", d["recalc"]["returned"], 200000)
db = SessionLocal()
ck("balans +200 000 bo'ldi", student_balance(db, TOLAGAN), 200000)
st = db.query(models.Student).get(TOLAGAN)
ck("guruhsiz qoldi", st.group_id, None)
ck("FAOL emas", st.status != "active", True)
row = (db.query(models.Payment)
       .filter(models.Payment.student_id == TOLAGAN,
               models.Payment.kind == "charge").first())
ck("hisob qatori 200 000 ga tushdi", row.amount, -200000)
ck("izohda tushuntirish bor", "guruhdan chiqdi" in (row.note or ""), True)
db.close()

print("\n=== 3. Qarzdor: arxivga TUSHMAYDI, 'Chiqib ketgan' bo'ladi ===")
r = c.post(f"/api/students/{QARZDOR}/remove-from-group", headers=H,
           json={"reason": "To'lamadi, aloqaga chiqmadi",
                 "reason_code": "price"})
ck("200", r.status_code, 200)
d = r.json()
ck("arxivga tushmadi", d["archived"], False)
ck("holati 'left'", d["status"], "left")
ck("qarzi hisoblangan", d["debt"], 200000)
db = SessionLocal()
st = db.query(models.Student).get(QARZDOR)
ck("guruhsiz", st.group_id, None)
ck("FAOL emas", st.status != "active", True)
ck("qarz ham to'g'rilandi (400k emas, 200k)",
   student_balance(db, QARZDOR), -200000)
db.close()

print("\n=== 4. Qarzdor QARZDORLAR ro'yxatida qoladi ===")
r = c.get("/api/debtors", headers=H)
names = [x.get("full_name") or x.get("student") for x in
         (r.json().get("rows") if isinstance(r.json(), dict) else r.json())]
ck("ro'yxatda bor", any("Qarzdor Bola" in str(n) for n in names), True)

print("\n=== 5. Guruhsiz o'quvchini FAOL qilib bo'lmaydi ===")
r = c.put(f"/api/students/{QARZDOR}", headers=H, json={"status": "active"})
ck("400 qaytadi", r.status_code, 400)
ck("sabab tushunarli", "Guruhsiz" in str(r.json()), True)

print("\n=== 6. Qarzni to'lasa AVTOMAT arxivga ===")
r = c.post(f"/api/students/{QARZDOR}/payments", headers=H,
           json={"amount": 200000, "kind": "payment", "method": "cash",
                 "client_key": "leave-1"})
ck("to'lov qabul qilindi", r.status_code, 200)
db = SessionLocal()
st = db.query(models.Student).get(QARZDOR)
ck("avtomat arxivga o'tdi", st.status, "archived")
ck("balans 0", student_balance(db, QARZDOR), 0)
db.close()

print("\n=== 7. Chiqib ketganni qayta tiklash mumkin ===")
r = c.post(f"/api/students/{TOLAGAN}/restore", headers=H)
ck("tiklandi", r.status_code, 200)
ck("faol bo'ldi", r.json()["status"], "active")

print("\n=== 8. Hisob yozuvi yo'q bo'lsa yiqilmaydi ===")
db = SessionLocal()
st2 = models.Student(full_name="Yangi Bola", branch_id=BID,
                     status="active", group_id=GID, enrolled_date=first)
db.add(st2); db.commit(); NID = st2.id
db.close()
r = c.post(f"/api/students/{NID}/remove-from-group", headers=H,
           json={"reason": "Sinov uchun", "reason_code": "unknown"})
ck("200", r.status_code, 200)
ck("hisob to'g'rilanmadi (yozuv yo'q edi)", r.json()["recalc"], None)
ck("arxivga tushdi", r.json()["archived"], True)

print("\n=== 9. SANA TANLAB chiqarish (2026-08-20) ===")
# Jahongir: "guruhdan talabani chiqarishda, sana tanlaydigan bo'lsin
# va masalan tanlangan sanagacha hisoblanib hisobi o'zgarsin va
# guruhdan chiqarilsin".
db = SessionLocal()
st3 = models.Student(full_name="Sanali Bola", branch_id=BID,
                     status="active", group_id=GID, enrolled_date=first)
db.add(st3); db.commit(); SANA = st3.id
db.add(models.Payment(student_id=SANA, amount=-400000, kind="charge",
                      period=f"{today.year:04d}-{today.month:02d}",
                      created_by="avtomat (oylik)"))
db.add(models.Payment(student_id=SANA, amount=400000, kind="payment",
                      method="cash", created_by="Admin"))
db.commit(); db.close()

# Oldindan ko'rish: 2-dars kunigacha (first+1) faqat 2 dars o'tilgan
d2 = (first + timedelta(days=1)).isoformat()
r = c.get(f"/api/students/{SANA}/leave-preview?on_date={d2}", headers=H)
ck("preview 200", r.status_code, 200)
pv = r.json()
ck("2 ta dars hisoblanadi", pv["lessons"], 2)
ck("300 000 qaytadi", pv["returned"], 300000)
ck("balans 300 000 bo'ladi", pv["target"], 300000)

# Bugungi kun bo'yicha esa 4 dars
r = c.get(f"/api/students/{SANA}/leave-preview", headers=H)
ck("bugungi kunda 4 dars", r.json()["lessons"], 4)

# Kelajak sana rad etiladi
r = c.post(f"/api/students/{SANA}/remove-from-group", headers=H,
           json={"reason": "Sana sinovi",
                 "on_date": (today + timedelta(days=3)).isoformat()})
ck("kelajak sana 400", r.status_code, 400)

# Qo'shilgan kunidan oldin ham bo'lmaydi
r = c.post(f"/api/students/{SANA}/remove-from-group", headers=H,
           json={"reason": "Sana sinovi",
                 "on_date": (first - timedelta(days=1)).isoformat()})
ck("erta sana 400", r.status_code, 400)

# Tanlangan sana bilan chiqaramiz
r = c.post(f"/api/students/{SANA}/remove-from-group", headers=H,
           json={"reason": "Oyning boshida ketgan edi", "reason_code": "unknown", "on_date": d2})
ck("200", r.status_code, 200)
d = r.json()
ck("preview bilan bir xil: 2 dars", d["recalc"]["lessons"], 2)
ck("300 000 qaytdi", d["recalc"]["returned"], 300000)
ck("sana javobda", d["on_date"], d2)
db = SessionLocal()
ck("balans 300 000", student_balance(db, SANA), 300000)
st3 = db.query(models.Student).get(SANA)
ck("ketgan sana tanlangan kun", st3.left_date.isoformat(), d2)
ck("guruhsiz", st3.group_id, None)
db.close()

print("\n" + ("HAMMASI OK" if not fails
              else f"{len(fails)} ta XATO: {fails}"))
sys.exit(1 if fails else 0)
