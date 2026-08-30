# -*- coding: utf-8 -*-
"""SABABLAR + OYLIK STATISTIKA (2026-08-30).

Jahongir: "har oy qaysi filial nechi foiz eski to'lov rejasi bajardi
statistika ketishi kerak ... men senga keyin ESKI YILLARNIKINI
tashlayman shundan ham eski davrnikini ham statistikaga qo'shib
olaverasan, keyin har bir admin yangi to'lov bo'yicha ham
statistikasi ketishi kerak, O'ZIDA HAM bu statistikalar ko'rinishi
kerak. Keyin o'quv markazdan ketish sababi ichiga JONY SCHOOL
MAKTABIGA O'TDI va BOSHQA XUSUSIY MAKTABGA O'TDI sabablarini ham
qo'shish kerak ... ketish sabablari statistikasi ham bo'lsa ...
muzlatish sabablari statistikasi ham kerak"
"""
import os
import sys

os.environ["DATABASE_URL"] = "sqlite:////tmp/verify_rsn/db.sqlite"
os.makedirs("/tmp/verify_rsn", exist_ok=True)
if os.path.exists("/tmp/verify_rsn/db.sqlite"):
    os.remove("/tmp/verify_rsn/db.sqlite")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import date, datetime, timedelta       # noqa: E402
from fastapi.testclient import TestClient            # noqa: E402
import main, models, roles                           # noqa: E402
import entry                                         # noqa: F401,E402
import common                                        # noqa: E402
from database import SessionLocal                    # noqa: E402
from auth import hash_password                       # noqa: E402

c = TestClient(main.app)
db = SessionLocal()
fails = []


def ck(n, got, want):
    ok = got == want
    print(("OK   " if ok else "XATO ") + f"{n}: {got}"
          + ("" if ok else f"   (kutilgan {want})"))
    if not ok:
        fails.append(n)


BUGUN = roles.local_today()
b1 = models.Branch(name="Zafar")
b2 = models.Branch(name="Bekobod 1")
db.add_all([b1, b2]); db.commit()
common.reset_partner_cache()
g = models.Group(name="G1", branch_id=b1.id, lesson_price=40_000,
                 monthly_fee=480_000)
db.add(g); db.commit()

fo = models.User(username="asoschi_r", password_hash=hash_password("jonyjony"),
                 role=roles.FOUNDER, full_name="Jahongir", is_active=1)
adm = models.User(username="shaxlo_r", password_hash=hash_password("jonyjony"),
                  role=roles.SALES_MANAGER, full_name="Zohidova Shaxlo",
                  branch_id=b1.id, is_active=1)
db.add_all([fo, adm]); db.commit()
HF = {"Authorization": "Bearer " + c.post("/api/auth/login", json={
    "username": "asoschi_r", "password": "jonyjony"}).json()["access_token"]}
HA = {"Authorization": "Bearer " + c.post("/api/auth/login", json={
    "username": "shaxlo_r", "password": "jonyjony"}).json()["access_token"]}


# =====================================================================
print("=== 1. YANGI SABABLAR RO'YXATDA ===")
# =====================================================================
m = c.get("/api/meta/reasons", headers=HF).json()
lv = {x["key"]: x for x in m["leave"]}
ck("Jony School sababi bor", lv["jony_school"]["label"],
   "Jony School maktabimizga o'tdi")
ck("Boshqa xususiy maktab sababi bor", lv["private_school"]["label"],
   "Boshqa xususiy maktabga o'tdi")
ck("Jony School YO'QOTISH emas", lv["jony_school"]["churn"], False)
ck("  chunki bizning maktabimiz", lv["jony_school"]["group"], "internal")
ck("boshqa maktab esa yo'qotish", lv["private_school"]["churn"], True)
ck("kursni tugatgan ham yo'qotish emas", lv["finished"]["churn"], False)
ck("narx qimmat — yo'qotish", lv["price"]["churn"], True)
ck("muzlatish sabablari ham keladi", len(m["freeze"]) >= 9, True)
ck("  pul qiyinchiligi XAVF deb belgilangan",
   [x["risk"] for x in m["freeze"] if x["key"] == "money"], [True])


# =====================================================================
print("\n=== 2. KETISH SABABLARI STATISTIKASI ===")
# =====================================================================
def ketdi(nom, sabab, kun_oldin=5, br=None):
    s = models.Student(full_name=nom, branch_id=(br or b1).id,
                       status="archived",
                       left_date=BUGUN - timedelta(days=kun_oldin),
                       enrolled_date=date(2026, 1, 1))
    db.add(s); db.commit()
    db.add(models.LeaveReason(student_id=s.id, reason=sabab,
                              created_by="test"))
    db.commit()
    return s


ketdi("Narxdan Ketgan", "price")
ketdi("Ustozdan Ketgan", "teacher")
ketdi("Ustozdan Ketgan 2", "teacher")
ketdi("Maktabga Ketgan", "jony_school")
ketdi("Maktabga Ketgan 2", "jony_school")
ketdi("Xususiyga Ketgan", "private_school")
ketdi("Tugatgan", "finished")
ketdi("Boshqa Filial", "price", br=b2)
db.commit()

r = c.get("/api/analytics/reason-stats?months=12", headers=HF).json()
lvv = r["leave"]
ck("jami ketganlar", lvv["total"], 8)
ck("HAQIQIY yo'qotish 5 ta", lvv["real"], 5)
ck("  (Jony School 2 + tugatgan 1 = 3 tasi yo'qotish emas)",
   lvv["not_churn"], 3)
ck("bizga bog'liq sabablar 2 ta", lvv["controllable"], 2)
top = {x["key"]: x["count"] for x in lvv["rows"]}
ck("ustozdan norozilik 2 ta", top["teacher"], 2)
ck("Jony School 2 ta", top["jony_school"], 2)
ck("  guruh nomi tushunarli",
   [x["group_label"] for x in lvv["rows"] if x["key"] == "jony_school"],
   ["Ichki ko'chish (yo'qotish emas)"])
ck("oylar kesimi bor", len(lvv["by_month"]) >= 1, True)
ck("filial kesimi bor", len(lvv["by_branch"]), 2)
zaf = [x for x in lvv["by_branch"] if x["branch"] == "Zafar"][0]
ck("  Zafarda 7 ta ketgan, 4 tasi haqiqiy",
   [zaf["total"], zaf["real"]], [7, 4])


# =====================================================================
print("\n=== 3. MUZLATISH SABABLARI STATISTIKASI ===")
# =====================================================================
for nom, sab in (("Muz Pul", "money"), ("Muz Pul 2", "money"),
                 ("Muz Kasal", "illness"), ("Muz Tatil", "vacation")):
    s = models.Student(full_name=nom, branch_id=b1.id, status="frozen",
                       frozen_reason=sab, enrolled_date=date(2026, 1, 1))
    db.add(s)
db.commit()
r = c.get("/api/analytics/reason-stats?months=12", headers=HF).json()
fz = r["freeze"]
ck("muzlatilganlar 4 ta", fz["total"], 4)
ck("XAVFLI muzlatish 2 ta (pul)", fz["risk"], 2)
ck("sabablar ajratilgan",
   {x["key"]: x["count"] for x in fz["rows"]},
   {"money": 2, "illness": 1, "vacation": 1})

# Muzlatishda sabab MAJBURIY ro'yxatdan
st = db.query(models.Student).filter(
    models.Student.full_name == "Muz Tatil").first()
bad = c.post(f"/api/students/{st.id}/freeze", headers=HF, json={
    "until": (BUGUN + timedelta(days=30)).isoformat(),
    "reason": "qandaydir-yoq-sabab"})
ck("yo'q sabab qabul qilinmaydi", bad.status_code, 400)
ok = c.post(f"/api/students/{st.id}/freeze", headers=HF, json={
    "until": (BUGUN + timedelta(days=30)).isoformat(),
    "reason": "illness", "note": "gripp"})
ck("to'g'ri sabab saqlanadi", ok.status_code, 200)
db.expire_all()
st = db.query(models.Student).get(st.id)
ck("  kod yozildi", st.frozen_reason, "illness")
ck("  izohda nomi ham bor", st.frozen_note, "Kasallik — gripp")


# =====================================================================
print("\n=== 4. YIG'ISH STATISTIKASI — OYLAR KESIMIDA ===")
# =====================================================================
def eski_oquvchi(nom, br, oylar, tolov_foiz, birinchi=None):
    """oylar — [(yil, oy), ...]. Har oyda hisob va tolov_foiz to'lov.

    birinchi — BIRINCHI to'lov sanasi. U eng eski oydan ham OLDIN
    bo'lishi shart: shundagina o'quvchi o'sha oylarda "eski mijoz"
    hisoblanadi va yig'ish foiziga kiradi. (Birinchi to'lov o'sha
    oyning o'zida bo'lsa — bu YANGI mijoz, foizga kirmaydi.)"""
    s = models.Student(full_name=nom, branch_id=br.id, group_id=g.id,
                       status="active", enrolled_date=date(2025, 1, 1))
    db.add(s); db.commit()
    db.add(models.Payment(student_id=s.id, amount=480_000, kind="payment",
                          created_at=(birinchi or datetime(2025, 1, 5)),
                          created_by="Eski"))
    for (y, mth) in oylar:
        db.add(models.Payment(student_id=s.id, amount=-480_000,
                              kind="charge", created_at=datetime(y, mth, 1)))
        if tolov_foiz:
            db.add(models.Payment(
                student_id=s.id, amount=480_000 * tolov_foiz,
                kind="payment", created_at=datetime(y, mth, 15),
                created_by="Zohidova Shaxlo"))
    db.commit()
    return s


Y, M = BUGUN.year, BUGUN.month
oldingi = (Y, M - 1) if M > 1 else (Y - 1, 12)
eski_oquvchi("Zafar Toliq", b1, [(Y, M), oldingi], 1.0)
eski_oquvchi("Zafar Yarim", b1, [(Y, M), oldingi], 0.5)
eski_oquvchi("Bekobod Toliq", b2, [(Y, M)], 1.0)
# ESKI DAVR: 2024-yil ma'lumoti ham qo'shilsa statistikaga tushishi kerak
eski_oquvchi("Eski Davr", b1, [(2024, 5)], 1.0,
             birinchi=datetime(2024, 1, 5))
db.commit()

r = c.get("/api/analytics/collection-history?months=6", headers=HF).json()
oy = {x["month"]: x for x in r["months"]}
key = f"{Y:04d}-{M:02d}"
ck("joriy oy bor", key in oy, True)
zf = [x for x in oy[key]["branches"] if x["branch"] == "Zafar"][0]
ck("Zafar rejasi 960 ming (2 ta o'quvchi)", zf["plan"], 960_000)
ck("  fakti 720 ming (biri to'liq, biri yarim)", zf["fact"], 720_000)
ck("  foizi 75%", zf["percent"], 75.0)
bk = [x for x in oy[key]["branches"] if x["branch"] == "Bekobod 1"][0]
ck("Bekobod 100%", bk["percent"], 100.0)
ck("oy jami foizi", oy[key]["percent"],
   round((720_000 + 480_000) / (960_000 + 480_000) * 100, 1))
ck("filial yig'indisi ham bor", len(r["summary"]) >= 2, True)

# Eski davr — 24 oy so'ralsa chiqishi kerak
oy_uzoq = (BUGUN.year - 2024) * 12 + BUGUN.month - 5 + 1
r2 = c.get(f"/api/analytics/collection-history?months={oy_uzoq}",
           headers=HF).json()
ck("ESKI DAVR (2024-05) ham statistikada",
   "2024-05" in [x["month"] for x in r2["months"]], True)
k24 = [x for x in r2["months"] if x["month"] == "2024-05"][0]
ck("  o'sha oyda ham foiz hisoblangan", k24["percent"], 100.0)


# =====================================================================
print("\n=== 5. ADMIN YANGI TO'LOV STATISTIKASI ===")
# =====================================================================
def yangi_mijoz(nom, y, mth, kim):
    s = models.Student(full_name=nom, branch_id=b1.id, group_id=g.id,
                       status="active", enrolled_date=date(y, mth, 1))
    db.add(s); db.commit()
    db.add(models.Payment(student_id=s.id, amount=480_000, kind="payment",
                          created_at=datetime(y, mth, 10), created_by=kim))
    db.commit()


for i in range(3):
    yangi_mijoz(f"YM Joriy {i}", Y, M, "Zohidova Shaxlo")
yangi_mijoz("YM Oldingi", oldingi[0], oldingi[1], "Zohidova Shaxlo")
yangi_mijoz("YM Boshqa", Y, M, "Kimdir Boshqa")
db.commit()

r = c.get("/api/analytics/admin-history?months=6", headers=HF).json()
sh = [x for x in r["rows"] if x["full_name"] == "Zohidova Shaxlo"][0]
cells = {x["month"]: x for x in sh["cells"]}
ck("joriy oyda 3 ta yangi mijoz", cells[key]["clients"], 3)
ck("  tushumi ham", cells[key]["revenue"], 3 * 480_000)
ck("o'tgan oyda 1 ta",
   cells[f"{oldingi[0]:04d}-{oldingi[1]:02d}"]["clients"], 1)
ck("jami 4 ta", sh["total_clients"], 4)
ck("boshqa odam qabul qilgani unga yozilmadi", sh["total_clients"] != 5, True)
ck("eng yaxshi oyi 3 ta", sh["best_month"], 3)


# =====================================================================
print("\n=== 6. ADMIN O'ZINIKINI KO'RADI ===")
# =====================================================================
r = c.get("/api/analytics/admin-history?months=6", headers=HA).json()
ck("admin uchun ham ochiq", len(r["rows"]), 1)
ck("  faqat o'zi", r["rows"][0]["full_name"], "Zohidova Shaxlo")
ck("  'faqat o'zim' belgisi bor", r["mine"], True)
ck("  raqami bir xil", r["rows"][0]["total_clients"], 4)
ck("asoschida esa 'faqat o'zim' emas",
   c.get("/api/analytics/admin-history?months=6",
         headers=HF).json()["mine"], False)


print("\n" + "=" * 60)
if fails:
    print("YIQILGAN TEKSHIRUVLAR:", len(fails))
    for f in fails:
        print("  -", f)
else:
    print("HAMMASI O'TDI")
sys.exit(1 if fails else 0)
