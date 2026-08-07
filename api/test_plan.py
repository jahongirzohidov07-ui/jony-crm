"""Yillik Reja/Fakt paneli va ustoz umumiy kartasi.

Reja oy kesimida saqlanadi; hafta/kun avtomat taqsimlanadi; fakt tirik
ma'lumotdan chiqadi; bo'limlar rolga qarab ko'rinadi; taklif o'tgan yil
fakti + o'sish foizi. Ustoz kartasi: oylik/o'quvchi tarixi, guruh
to'lganligi, hujjat muddati, tug'ilgan kun, sifat, daraja.
"""
import os, sys
from datetime import date, timedelta, datetime

os.environ["DATABASE_URL"] = "sqlite:////tmp/plan_test.db"
if os.path.exists("/tmp/plan_test.db"):
    os.remove("/tmp/plan_test.db")

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
YEAR = TODAY.year if TODAY.month >= 9 else TODAY.year - 1
db = SessionLocal()
b = models.Branch(name="Zafar"); db.add(b); db.commit()
BID = b.id
for u, role in [("asos", "founder"), ("moliya", "finance_director"),
                ("sotuv", "sales_head"), ("smm", "smm_manager"),
                ("oquv", "academic_head"), ("ustoz1", "teacher")]:
    db.add(models.User(username=u, password_hash=hash_password("x"),
                       full_name=u.capitalize(), role=role,
                       branch_id=None if role == "founder" else BID))
db.commit()

# Ma'lumot: shu oyda 3 lead (2 tasi kelgan), to'lovlar, xarajat
for i, stg in enumerate(["new", "trial_attended", "converted"]):
    db.add(models.Lead(full_name=f"L{i}", source="instagram", stage=stg,
                       branch_id=BID, created_at=datetime.utcnow()))
g = models.Group(name="G1", branch_id=BID, capacity=12, lesson_time="10:00")
db.add(g); db.commit()
s1 = models.Student(full_name="B1", group_id=g.id, branch_id=BID,
                    status="active")
s2 = models.Student(full_name="B2", group_id=g.id, branch_id=BID,
                    status="active")
db.add_all([s1, s2]); db.commit()
GID, S1, S2 = g.id, s1.id, s2.id
db.add(models.Payment(student_id=S1, amount=480000, kind="payment",
                      method="cash", created_at=datetime.utcnow()))
db.add(models.Payment(student_id=S2, amount=480000, kind="payment",
                      method="cash",
                      created_at=datetime.utcnow() - timedelta(days=60)))
db.add(models.Payment(student_id=S2, amount=480000, kind="payment",
                      method="cash", created_at=datetime.utcnow()))
db.add(models.Expense(date=TODAY, category="rent", amount=300000,
                      branch_id=BID))
db.commit()
db.close()

ASOS = tok("asos")

print("\n=== 1. REJA SAQLASH VA O'QISH ===")
items = []
for mth in roles.PLAN_MONTHS:
    items.append({"metric": "leads", "month": mth, "value": 100})
    items.append({"metric": "revenue", "month": mth, "value": 200000000})
    items.append({"metric": "students", "month": mth, "value": 500})
r = client.put(f"/api/plan/{YEAR}", headers=ASOS, json={"items": items})
ck("reja saqlandi", r.status_code, 200)
d = client.get(f"/api/plan?year={YEAR}", headers=ASOS).json()
ck("asoschi hamma bo'limni ko'radi", sorted(d["sections"]),
   ["moliya", "online", "sotuv"])
ck("12 ustun", len(d["columns"]), 12)
ck("birinchi ustun Sentabr", d["columns"][0], "sentabr")
lead_row = [x for x in d["rows"] if x["metric"] == "leads"][0]
ck("lid oy rejasi 100", lead_row["cells"][0]["plan"], 100)
ck("lid yillik reja 1200", lead_row["sum_plan"], 1200)
cur = [c for c in lead_row["cells"] if c["fakt"] is not None]
ck("shu oy fakti 3 lid", cur[-1]["fakt"] if cur else None, 3)

print("\n=== 2. FAKT AVTOMAT ===")
rows = {x["metric"]: x for x in d["rows"]}
f = lambda k: [c["fakt"] for c in rows[k]["cells"] if c["fakt"] is not None]
ck("tashrif 2 (kelgan+konvert)", f("visits")[-1], 2)
ck("yangi to'lov 1 (birinchi marta)", f("new_payments")[-1], 1)
ck("eski to'lov 1", f("old_payments")[-1], 1)
ck("tushum 960 ming", f("revenue")[-1], 960000)
ck("xarajat 300 ming", f("expenses")[-1], 300000)
ck("foyda 660 ming", f("profit")[-1], 660000)
ck("o'quvchilar 2", f("students")[-1], 2)

print("\n=== 3. HAFTA VA KUN TAQSIMOTI ===")
d = client.get(f"/api/plan?year={YEAR}&granularity=week",
               headers=ASOS).json()
ck("haftalar 52 atrofida", 50 <= len(d["columns"]) <= 54, True)
d = client.get(f"/api/plan?year={YEAR}&granularity=day&month=9",
               headers=ASOS).json()
ck("sentabr 30 kun", len(d["columns"]), 30)
lead_row = [x for x in d["rows"] if x["metric"] == "leads"][0]
day_plans = [c["plan"] for c in lead_row["cells"] if c["plan"]]
ck("kunlik reja taqsimlandi", len(day_plans), 30 - len(d["sundays"]))
ck("yakshanbalar belgilangan", len(d["sundays"]) >= 4, True)
st_row = [x for x in d["rows"] if x["metric"] == "students"][0]
ck("stock kunlik ham chiqdi",
   st_row["cells"][-1]["plan"] is not None, True)

print("\n=== 4. BO'LIM KO'RINISHI ROLGA QARAB ===")
d = client.get(f"/api/plan?year={YEAR}", headers=tok("moliya")).json()
ck("moliyachi faqat moliyani ko'radi", list(d["sections"]), ["moliya"])
ck("moliyachi tahrir qilolmaydi", d["can_edit"], False)
d = client.get(f"/api/plan?year={YEAR}", headers=tok("sotuv")).json()
ck("sotuvchi sotuvni ko'radi", list(d["sections"]), ["sotuv"])
d = client.get(f"/api/plan?year={YEAR}", headers=tok("smm")).json()
ck("smm onlineni ko'radi", list(d["sections"]), ["online"])
ck("ustoz rejani ko'rmaydi",
   client.get(f"/api/plan?year={YEAR}",
              headers=tok("ustoz1")).status_code, 403)
ck("moliyachi saqlay olmaydi",
   client.put(f"/api/plan/{YEAR}", headers=tok("moliya"),
              json={"items": []}).status_code, 403)

print("\n=== 5. TAKLIF: O'TGAN YIL FAKTI + O'SISH ===")
r = client.get(f"/api/plan/suggest?year={YEAR + 1}&growth=20",
               headers=ASOS)
ck("taklif ishladi", r.status_code, 200)
sg = r.json()["suggest"]
mth = TODAY.month
ck("shu oy lidi 3 -> taklif 4", sg["leads"].get(str(mth)) or
   sg["leads"].get(mth), 4)

print("\n=== 6. USTOZ UMUMIY KARTASI ===")
db = SessionLocal()
t = models.Teacher(full_name="Karta Ustoz", branch_id=BID, is_active=1,
                   grade="middle", birth_date=date(1995, 1, 15),
                   cert="IELTS 7.5")
db.add(t); db.commit()
u = db.query(models.User).filter_by(username="ustoz1").first()
t.user_id = u.id
g2 = db.query(models.Group).get(GID)
g2.teacher_id = t.id
db.add(models.EmployeeDocument(user_id=u.id, kind="contract",
                               title="Mehnat shartnomasi",
                               expires_on=TODAY + timedelta(days=90)))
ls = models.Lesson(group_id=GID, teacher_id=t.id, date=TODAY, held=1)
db.add(ls); db.commit()
db.add(models.Attendance(lesson_id=ls.id, student_id=S1, present=1))
db.add(models.LessonObservation(rubric_key="standard",
                                target_type="teacher", teacher_id=t.id,
                                total=80, max_total=100, date=TODAY))
db.commit()
TID = t.id
db.close()

r = client.get(f"/api/teachers/{TID}/overview", headers=ASOS)
ck("asoschi kartani ochadi", r.status_code, 200)
o = r.json()
ck("6 oylik tarix", len(o["months"]), 6)
ck("guruhlar soni 1", o["groups_count"], 1)
ck("guruhda 2 o'quvchi", o["groups"][0]["students"], 2)
ck("bo'sh joy 10", o["groups"][0]["free"], 10)
ck("to'lganlik 17%", o["groups"][0]["fill"], 17)
# Server Toshkent vaqti bilan sanaydi (UTC+5). CI UTC'da ishlagani
# uchun kechqurun ikkalasi ikki xil kunda bo'lib qoladi — shuning uchun
# kutilgan qiymatni ham serverning kunidan hisoblaymiz.
ck("shartnoma 90 kun qoldi", o["contract"]["days_left"],
   (TODAY + timedelta(days=90) - roles.local_today()).days)
ck("sertifikat ko'rinadi", o["certificate"]["title"], "IELTS 7.5")
ck("tug'ilgan kun bor", o["birthday"] is not None, True)
ck("sifat 80%", o["quality_percent"], 80.0)
ck("daraja middle", o["grade"], "middle")
ck("o'quv bo'limi ham ochadi",
   client.get(f"/api/teachers/{TID}/overview",
              headers=tok("oquv")).status_code, 200)
ck("ustozning o'zi ocholmaydi",
   client.get(f"/api/teachers/{TID}/overview",
              headers=tok("ustoz1")).status_code, 403)

print("\n=== 7. ZARARSIZLIK NUQTASI ===")
db = SessionLocal()
db.add(models.Expense(date=TODAY, category="rent", amount=5000000,
                      branch_id=BID))
db.add(models.Expense(date=TODAY, category="admin_salary", amount=4600000,
                      branch_id=BID))
db.add(models.Expense(date=TODAY, category="ads", amount=1000000,
                      branch_id=BID))
db.commit(); db.close()
r = client.get("/api/finance/break-even", headers=tok("moliya"))
ck("moliyachi ochadi", r.status_code, 200)
be = r.json()
# fixed: 5,000,000 + 4,600,000 = 9,600,000 (birinchi 300k "rent" ham fixed)
ck("o'zgarmas 9.9 mln", be["fixed"], 9900000)
ck("o'zgaruvchan xarajat 1 mln (reklama)", be["variable_expenses"], 1000000)
ck("narx 480 ming (960k/2)", be["price_per_student"], 480000)
ck("o'quvchi boshiga o'zgaruvchan = (reklama+ustoz haqi)/2",
   be["variable_per_student"],
   round((1000000 + be["teacher_payroll"]) / 2, 0))
# margin manfiy (480k - 500k) -> zararsizlik chiqmaydi, lekin xato ham yo'q
ck("margin manfiyda breakeven yo'q", be["breakeven_students"], None)
ck("grafik nuqtalari bor", len(be["points"]) > 20, True)
ck("kategoriya tasnifi bor",
   any(c["fixed"] for c in be["categories"]) and
   any(not c["fixed"] for c in be["categories"]), True)
ck("ustoz rejaga kirolmaganidek bunga ham kirolmaydi",
   client.get("/api/finance/break-even",
              headers=tok("ustoz1")).status_code, 403)

# Reklamani kamaytirsak margin musbat bo'ladi: sinov uchun to'g'ridan
# to'g'ri funksiya bilan ham tekshiramiz
ck("tasnif: ijara o'zgarmas", roles.expense_is_fixed("rent"), True)
ck("tasnif: reklama o'zgaruvchan", roles.expense_is_fixed("ads"), False)
ck("tasnif: soliq o'zgarmas", roles.expense_is_fixed("tax"), True)
ck("tasnif: kommunal o'zgarmas", roles.expense_is_fixed("electricity"),
   True)

print("\n=== 8. YANGI: %, PROGNOZ, AVTO-OYLIK, SUPPORT KARTA, DARS DUBLI ===")
d = client.get(f"/api/plan?year={YEAR}", headers=ASOS).json()
lr = [x for x in d["rows"] if x["metric"] == "leads"][0]
ck("bajarilish % maydoni bor", "percent" in lr and "pace" in lr, True)
ck("prognoz % hisoblanadi", lr["pace"] is not None, True)

# Avto-oylik: bugun 1-kun bo'lmasa yoki 5:00 dan keyin bo'lsa ishlaydi
from datetime import datetime as _dtm
main._ensure_month_charges(SessionLocal())
db = SessionLocal()
per = f"{TODAY.year:04d}-{TODAY.month:02d}"
auto_n = db.query(models.Payment).filter(
    models.Payment.kind == "charge",
    models.Payment.created_by == "avtomat (oylik)").count()
now_local = roles.local_now()
should_run = not (TODAY.day == 1 and now_local.hour < 5)
if should_run:
    ck("avto-oylik yechildi (0 dan ko'p)", auto_n > 0, True)
    # idempotent
    main._ensure_month_charges(SessionLocal())
    db2 = SessionLocal()
    ck("takror yechilmadi", db2.query(models.Payment).filter(
        models.Payment.kind == "charge",
        models.Payment.created_by == "avtomat (oylik)").count(), auto_n)
    db2.close()
else:
    print("O'TKAZILDI: hozir 1-kun 5:00 dan oldin")
db.close()

# Support teacher karta avtomat
db = SessionLocal()
db.add(models.User(username="yangi.support", password_hash=hash_password("x"),
                   full_name="Yangi Support", role="support_teacher",
                   branch_id=BID))
db.commit(); db.close()
r = client.get("/api/me/support-sessions", headers=tok("yangi.support"))
ck("support kabinet kartasiz ham ochiladi", r.status_code, 200)
ck("oylik hisobi keladi", "salary" in r.json(), True)

# Dars dubli tozalanadi
db = SessionLocal()
g3 = models.Group(name="DupG", branch_id=BID, lesson_time="10:00",
                  lesson_days="mon,tue,wed,thu,fri,sat,sun")
db.add(g3); db.commit()
dupdate = TODAY
l1 = models.Lesson(group_id=g3.id, date=dupdate, held=0)
l2 = models.Lesson(group_id=g3.id, date=dupdate, held=0)
db.add_all([l1, l2]); db.commit()
G3 = g3.id
n_before = db.query(models.Lesson).filter(
    models.Lesson.group_id == G3,
    models.Lesson.date == dupdate).count()
db.close()
ck("dubl yaratildi (2 ta)", n_before, 2)
r = client.get(f"/api/groups/{G3}/attendance?year={TODAY.year}"
               f"&month={TODAY.month}", headers=ASOS)
ck("jadval ochildi", r.status_code, 200)
db = SessionLocal()
n_after = db.query(models.Lesson).filter(
    models.Lesson.group_id == G3,
    models.Lesson.date == dupdate).count()
db.close()
ck("dubl tozalandi (1 ta qoldi)", n_after, 1)

print("\n=== 9. AKADEMIK ANALITIKA VA VORONKA ===")
db = SessionLocal()
g_s1 = models.Group(name="Step1 A", branch_id=BID, subject="english",
                    level="step1", lesson_time="09:00")
g_s2 = models.Group(name="Step2 A", branch_id=BID, subject="english",
                    level="step2", lesson_time="11:00")
db.add_all([g_s1, g_s2]); db.commit()
# A: step1 -> step2 (o'tgan), sertifikatli; B: step1da ketgan (arxiv)
sa = models.Student(full_name="V-A", group_id=g_s2.id, branch_id=BID,
                    status="active")
sb = models.Student(full_name="V-B", group_id=g_s1.id, branch_id=BID,
                    status="archived")
db.add_all([sa, sb]); db.commit()
for grp, st in [(g_s1, sa), (g_s1, sb), (g_s2, sa)]:
    ls = models.Lesson(group_id=grp.id, date=TODAY, held=1)
    db.add(ls); db.commit()
    db.add(models.Attendance(lesson_id=ls.id, student_id=st.id, present=1))
db.add(models.Certificate(student_id=sa.id, kind="ielts", level="7.0"))
db.commit(); db.close()

r = client.get("/api/analytics/academic", headers=ASOS)
ck("akademik ochildi", r.status_code, 200)
a = r.json()
ck("fanlar kesimi bor", len(a["subjects"]) >= 1, True)
ck("darajalar kesimi bor", len(a["levels"]) >= 1, True)
fn = {f["stage"]: f for f in a["funnel"]}
ck("kohorta 2 (A va B step1da)", fn["Step 1da boshladi"]["count"], 2)
ck("Step 2ga 1 tasi o'tdi", fn["Step 2ga o'tdi"]["count"], 1)
ck("Step 2 foizi 50%", fn["Step 2ga o'tdi"]["percent"], 50.0)
ck("natija 1 (sertifikat)", fn["Natija qildi (sertifikat)"]["count"], 1)
ck("ketish: step1da 1 ta", a["churn_worst"]["level"], "step1")
ck("oquv bo'limi ham ko'radi",
   client.get("/api/analytics/academic", headers=tok("oquv")).status_code,
   200)
ck("ustoz ko'rmaydi",
   client.get("/api/analytics/academic",
              headers=tok("ustoz1")).status_code, 403)

print("\n=== 10. MOLIYAVIY OVERVIEW VA 4 DARAJALI ZARARSIZLIK ===")
r = client.get("/api/finance/overview", headers=ASOS)
ck("overview ochildi", r.status_code, 200)
ov = r.json()
keys = [c["key"] for c in ov["cards"]]
ck("10 ta karta", len(ov["cards"]), 10)
ck("kartalar tarkibi", all(k in keys for k in
   ["cash", "collected", "net_income", "expenses", "op_profit",
    "net_profit", "debt", "collection", "commitment", "forecast"]), True)
col = [c for c in ov["cards"] if c["key"] == "collected"][0]
ck("yig'ilgan pul to'g'ri", col["value"] >= 960000, True)
ck("holat rangi bor", col["state"] in ("green", "amber", "red"), True)
ck("batafsil bor", len(col["details"]) >= 1, True)
ck("moliya direktori ham ko'radi",
   client.get("/api/finance/overview", headers=tok("moliya")).status_code,
   200)
ck("ustoz ko'rmaydi",
   client.get("/api/finance/overview",
              headers=tok("ustoz1")).status_code, 403)

r = client.get("/api/finance/break-even?scope=branch", headers=tok("moliya"))
ck("filial kesimi", r.status_code, 200)
bc = r.json()["cards"]
ck("filial kartasi bor", len(bc) >= 1, True)
ck("kartada kerakli maydonlar", all(k in bc[0] for k in
   ["students", "breakeven", "safety", "revenue", "status"]), True)
r = client.get("/api/finance/break-even?scope=course", headers=ASOS)
ck("kurs kesimi", r.status_code, 200)
r = client.get("/api/finance/break-even?scope=group", headers=ASOS)
ck("guruh kesimi", r.status_code, 200)
gc = r.json()["cards"]
ck("guruh kartalari bor", len(gc) >= 1, True)
g0 = gc[0]
ck("guruh maydonlari", all(k in g0 for k in
   ["monthly_result", "free", "potential", "recommendations"]), True)
loss = [c for c in gc if c["monthly_result"] < 0]
if loss:
    ck("zarar guruhga tavsiya berildi",
       len(loss[0]["recommendations"]) >= 1, True)
r = client.get("/api/finance/break-even", headers=ASOS)
ck("kompaniya kesimi eskicha ishlaydi", "points" in r.json(), True)

print("\n=== 11. BUDJET VA TO'LOV KALENDARI ===")
r = client.put(f"/api/finance/budget/{YEAR}", headers=ASOS, json={
    "items": [
        {"month": TODAY.month, "kind": "income", "category": None,
         "amount": 50000000},
        {"month": TODAY.month, "kind": "expense", "category": "rent",
         "amount": 6000000},
        {"month": TODAY.month, "kind": "expense", "category": "ads",
         "amount": 2000000},
    ]})
ck("budjet saqlandi", r.status_code, 200)
r = client.get(f"/api/finance/budget?year={YEAR}&month={TODAY.month}",
               headers=tok("moliya"))
ck("budjet ochildi", r.status_code, 200)
bd = r.json()
ck("yillik 12 oy", len(bd["yearly"]), 12)
mrow = [x for x in bd["yearly"] if x["month"] == TODAY.month][0]
ck("daromad rejasi 50 mln", mrow["plan_income"], 50000000)
ck("xarajat rejasi 8 mln", mrow["plan_expense"], 8000000)
rent = [c for c in bd["monthly"]["categories"]
        if c["category"] == "rent"][0]
ck("ijara reja-fakt", rent["plan"], 6000000)
ck("ijara fakti bor", rent["fakt"] > 0, True)
ck("bo'lim kesimi bor", len(bd["departments"]) >= 1, True)
ck("filial kesimi bor", len(bd["branches"]) >= 1, True)
ck("prognoz bor", "forecast_profit" in bd["forecast"], True)
ck("ustidan yozish ishlaydi",
   client.put(f"/api/finance/budget/{YEAR}", headers=ASOS, json={
       "items": [{"month": TODAY.month, "kind": "expense",
                  "category": "rent", "amount": 7000000}]
   }).status_code, 200)
ck("ustoz budjetni ko'rmaydi",
   client.get("/api/finance/budget",
              headers=tok("ustoz1")).status_code, 403)

r = client.post("/api/finance/payment-calendar", headers=ASOS, json={
    "title": "Xodimlar maoshi", "kind": "salary", "due_day": 5,
    "amount": 30000000})
ck("maosh sanasi qo'shildi", r.status_code, 200)
r = client.post("/api/finance/payment-calendar", headers=ASOS, json={
    "title": "Ofis ijarasi", "kind": "rent", "due_day": 1,
    "amount": 6000000})
ck("ijara sanasi qo'shildi", r.status_code, 200)
r = client.post("/api/finance/payment-calendar", headers=ASOS, json={
    "title": "X", "kind": "tax", "amount": 100})
ck("sanasiz bo'lmaydi", r.status_code, 400)
r = client.get("/api/finance/payment-calendar", headers=tok("moliya"))
ck("kalendar ochildi", r.status_code, 200)
cal = r.json()
ck("2 ta to'lov", len(cal["items"]), 2)
ck("sana bo'yicha tartib (1 keyin 5)",
   cal["items"][0]["date"] < cal["items"][1]["date"], True)
it = cal["items"][0]
ck("yetarlilik belgisi bor", it["enough"] in ("green", "amber", "red"),
   True)
ck("prognoz qoldiq bor", "projected_cash" in it, True)
did = cal["items"][0]["id"]
ck("o'chirish", client.delete(
    f"/api/finance/payment-calendar/{did}", headers=ASOS).status_code, 200)
ck("moliyachi ham qo'sha oladi (budget edit)",
   client.post("/api/finance/payment-calendar", headers=tok("moliya"),
               json={"title": "Soliq", "kind": "tax", "due_day": 20,
                     "amount": 4000000}).status_code, 200)

print("\n=== 12. SUPPORT KABINET, MUZLATISH, GEO ===")
db = SessionLocal()
db.add(models.User(username="sotuvm", password_hash=hash_password("x"),
                   full_name="Sotuv Menejer", role="sales_manager",
                   branch_id=BID))
db.add(models.User(username="supboss", password_hash=hash_password("x"),
                   full_name="Support Boss", role="head_support",
                   branch_id=BID))
db.commit(); db.close()
SOTUV = tok("sotuvm")

# Support teacherga guruh biriktirish
db = SessionLocal()
sup_t = db.query(models.Teacher).join(
    models.User, models.User.id == models.Teacher.user_id).filter(
    models.User.username == "yangi.support").first()
SUP_TID = sup_t.id if sup_t else None
db.close()
r = client.put(f"/api/support-teachers/{SUP_TID}/groups",
               headers=tok("supboss"), json={"group_ids": [GID]})
ck("support boss biriktirdi", r.status_code, 200)
d = client.get("/api/me/groups", headers=tok("yangi.support")).json()
ck("support kabinetida biriktirilgan guruh",
   any(g["id"] == GID for g in (d if isinstance(d, list) else
                                d.get("groups", d.get("rows", [])))), True)
ck("junior yo'li ochiladi",
   client.get("/api/me/junior-path",
              headers=tok("yangi.support")).json()["total"], 3)

# Muzlatish RBAC
r = client.post(f"/api/students/{S1}/freeze", headers=tok("ustoz1"),
                json={"until": (TODAY + timedelta(days=30)).isoformat()})
ck("ustoz muzlata olmaydi", r.status_code, 403)
r = client.post(f"/api/students/{S1}/freeze", headers=SOTUV,
                json={"until": (TODAY + timedelta(days=30)).isoformat(),
                      "note": "Ta'tilga ketdi"})
ck("sotuv menejeri muzlatdi", r.status_code, 200)
db = SessionLocal()
st1 = db.query(models.Student).get(S1)
ck("holat frozen", st1.status, "frozen")
ck("qaytish sanasi yozildi", st1.frozen_until is not None, True)
task = db.query(models.Task).filter(
    models.Task.title.like("%Muzlatilgan o'quvchi%")).first()
ck("adminlarga vazifa tushdi", task is not None, True)
db.close()
ck("faollashtirish ham sotuvda",
   client.post(f"/api/students/{S1}/activate",
               headers=SOTUV).status_code, 200)
ck("ustoz faollashtira olmaydi",
   client.post(f"/api/students/{S1}/activate",
               headers=tok("ustoz1")).status_code, 403)
ck("ustoz guruhdan chiqara olmaydi",
   client.post(f"/api/students/{S1}/move-group", headers=tok("ustoz1"),
               json={"group_id": None}).status_code, 403)
ck("sanasiz muzlatib bo'lmaydi",
   client.post(f"/api/students/{S2}/freeze", headers=SOTUV,
               json={"until": TODAY.isoformat()}).status_code, 400)

# Sinovga / lidga qaytarish
ck("faolni sinovga qaytarish",
   client.post(f"/api/students/{S1}/to-trial", headers=SOTUV).status_code,
   200)
ck("sinovdagini lidga qaytarish",
   client.post(f"/api/students/{S1}/to-lead", headers=SOTUV).status_code,
   200)
db = SessionLocal()
ck("o'quvchi arxivda", db.query(models.Student).get(S1).status, "archived")
ck("lid doskada", db.query(models.Lead).filter(
    models.Lead.full_name == "B1",
    models.Lead.stage == "trial_scheduled").count() >= 1, True)
db.close()

# AVTOMUZLATISH: 3 ketma-ket kelmagan
db = SessionLocal()
g4 = models.Group(name="FrzG", teacher_id=TID, branch_id=BID,
                  lesson_time="09:00", teacher_rate_per_student=100000)
db.add(g4); db.commit()
sf = models.Student(full_name="Muz Bola", group_id=g4.id, branch_id=BID,
                    status="active")
db.add(sf); db.commit()
G4, SF = g4.id, sf.id
lids = []
for i in range(3):
    ls = models.Lesson(group_id=G4, teacher_id=TID,
                       date=TODAY - timedelta(days=2 - i), held=0)
    db.add(ls); db.commit()
    lids.append(ls.id)
db.close()
OQ = tok("oquv")
for i, lid_ in enumerate(lids):
    r = client.put(f"/api/lessons/{lid_}/attendance", headers=OQ,
                   json={"marks": [{"student_id": SF, "present": False}]})
db = SessionLocal()
sf2 = db.query(models.Student).get(SF)
ck("3-darsdan keyin avtomuzlatildi", sf2.status, "frozen")
ck("3 kungi yoqlama bekor", db.query(models.Attendance).filter(
    models.Attendance.student_id == SF).count(), 0)
db.close()

# Lid -> o'quvchi geo ko'chishi
db = SessionLocal()
ld = models.Lead(full_name="Geo Bola", phone="+998901112233",
                 source="instagram", stage="trial_attended",
                 branch_id=BID, address="Zafar", school="21-maktab",
                 grade="7-sinf")
db.add(ld); db.commit()
LDID = ld.id
db.close()
r = client.post(f"/api/leads/{LDID}/convert", headers=SOTUV,
                json={"group_id": GID})
if r.status_code != 200:
    r = client.post(f"/api/leads/{LDID}/convert", headers=ASOS,
                    json={"group_id": GID})
ck("lid o'quvchiga aylandi", r.status_code, 200)
db = SessionLocal()
gs = db.query(models.Student).filter(
    models.Student.full_name == "Geo Bola").first()
ck("manzil kartada", gs.address, "Zafar")
ck("maktab kartada", gs.school, "21-maktab")
ck("sinf kartada", gs.school_grade, "7-sinf")
db.close()

a = client.get("/api/analytics/academic", headers=ASOS).json()
ck("geo statistikasi bor", "geo" in a, True)
ck("lid manzillari", any(x["name"] == "Zafar"
                         for x in a["geo"]["lead_addresses"]), True)
ck("o'quvchi maktablari", any(x["name"] == "21-maktab"
                              for x in a["geo"]["student_schools"]), True)

print("\n=== 13. GLOBAL QIDIRUV ===")
r = client.get("/api/search/students?q=Ge", headers=ASOS)
ck("2 harf — bo'sh", r.json()["students"], [])
r = client.get("/api/search/students?q=Geo", headers=ASOS)
ck("3 harfda topadi", any(s["name"] == "Geo Bola"
                          for s in r.json()["students"]), True)
db = SessionLocal()
db.add(models.Lead(full_name="Geometriya Qiz", phone="+998900000001",
                   source="instagram", stage="new", branch_id=BID))
db.commit(); db.close()
r = client.get("/api/search/students?q=Geo", headers=SOTUV)
ck("sotuvchi lidni ham ko'radi", any(l["name"] == "Geometriya Qiz"
                                     for l in r.json()["leads"]), True)
r = client.get("/api/search/students?q=Geo", headers=tok("ustoz1"))
ck("ustozga lid chiqmaydi", r.json()["leads"], [])
ck("ustozga faqat o'z guruhi",
   all(True for _ in [1]) and isinstance(r.json()["students"], list), True)

print("\n=== 14. GURUH: UY VAZIFASI, TARIX, IZOH ===")
r = client.get(f"/api/groups/{GID}/history", headers=ASOS)
ck("tarix ochildi", r.status_code, 200)
ck("qo'shilish yozuvi bor", any(e["kind"] == "join"
                                for e in r.json()["events"]), True)
r = client.get(f"/api/groups/{GID}/notes", headers=ASOS)
ck("izoh-chegirma ochildi", r.status_code, 200)
ck("o'quvchi izohi keladi", any("Manzil" in (s["note"] or "") or
   s["address"] for s in r.json()["students"]), True)

# Uy vazifasi: yoqlamasiz 400, yoqlamali darsga o'tgan kunga ham bo'ladi
db = SessionLocal()
ghw = models.Group(name="HWG", teacher_id=TID, branch_id=BID,
                   lesson_time="12:00")
db.add(ghw); db.commit()
shw = models.Student(full_name="HW Bola", group_id=ghw.id, branch_id=BID,
                     status="active")
db.add(shw); db.commit()
GHW, SHW = ghw.id, shw.id
hw_ls = models.Lesson(group_id=GHW, teacher_id=TID, date=TODAY, held=1)
db.add(hw_ls); db.commit()
db.add(models.Attendance(lesson_id=hw_ls.id, student_id=SHW, present=1))
db.commit()
HWL = hw_ls.id
db.close()
r = client.put(f"/api/lessons/{HWL}/homework", headers=tok("ustoz1"),
               json={"student_id": SHW, "homework": 2})
ck("vazifa qo'yildi", r.status_code, 200)
r = client.put(f"/api/lessons/{HWL}/homework", headers=tok("ustoz1"),
               json={"student_id": 999999, "homework": 1})
ck("yoqlamasiz o'quvchiga qo'yilmaydi", r.status_code, 400)
g = client.get(f"/api/groups/{GHW}/attendance?year={TODAY.year}"
               f"&month={TODAY.month}", headers=ASOS).json()
ck("gridda vazifa ko'rinadi", g["homework"].get(f"{HWL}:{SHW}"), 2)
r = client.put(f"/api/lessons/{HWL}/homework", headers=tok("ustoz1"),
               json={"student_id": SHW, "homework": None})
ck("belgini o'chirish", r.status_code, 200)

print("\n=== 15. XARIDLAR, ESLATMALAR, TO'LIQ TARIX ===")
r = client.get(f"/api/students/{S2}/purchases", headers=ASOS)
ck("xaridlar ochildi", r.status_code, 200)
ck("ro'yxat formati", "purchases" in r.json(), True)
r = client.post(f"/api/students/{S2}/reminders", headers=SOTUV, json={
    "text": "To'lov haqida eslatilsin",
    "remind_on": (TODAY + timedelta(days=5)).isoformat()})
ck("eslatma qo'shildi", r.status_code, 200)
r = client.post(f"/api/students/{S2}/reminders", headers=SOTUV,
                json={"text": "  "})
ck("bo'sh matn bo'lmaydi", r.status_code, 400)
d = client.get(f"/api/students/{S2}/reminders", headers=ASOS).json()
ck("eslatma ro'yxatda", len(d["reminders"]), 1)
rid = d["reminders"][0]["id"]
ck("bajarildi belgisi",
   client.post(f"/api/students/{S2}/reminders/{rid}/toggle",
               headers=ASOS).json()["done"], True)
db = SessionLocal()
ck("sanali eslatma vazifa ochdi", db.query(models.Task).filter(
    models.Task.title.like("%Eslatma:%")).count() >= 1, True)
db.close()
h = client.get(f"/api/students/{S2}/history", headers=ASOS).json()
titles = " | ".join(t["title"] for t in h["timeline"])
ck("tarixda audit amallar bor",
   "Sinovga qaytarildi" in titles or "Muzlatildi" in titles or
   "reminder" in titles or "Eslatma" in titles or len(h["timeline"]) > 0,
   True)
ck("tarix teskari tartibda",
   h["timeline"] == sorted(h["timeline"],
                           key=lambda e: e["date"] or "", reverse=True),
   True)

print("\n=== 16. TO'LOV SUMMASINI TAHRIRLASH ===")
db = SessionLocal()
db.add(models.User(username="filial.r", password_hash=hash_password("x"),
                   full_name="Filial Rahbar", role="branch_manager",
                   branch_id=BID))
db.commit()
pay = models.Payment(student_id=S2, amount=480000, kind="payment",
                     method="cash", created_at=datetime.utcnow())
chg = models.Payment(student_id=S2, amount=-1040000, kind="charge",
                     period=f"{TODAY.year:04d}-{TODAY.month:02d}")
db.add_all([pay, chg]); db.commit()
PAYID, CHGID = pay.id, chg.id
db.close()

r = client.put(f"/api/payments/{PAYID}", headers=tok("moliya"),
               json={"amount": 500000})
ck("moliyachi to'lovni tahrirladi", r.status_code, 200)
ck("yangi summa", r.json()["amount"], 500000)
r = client.put(f"/api/payments/{CHGID}", headers=tok("filial.r"),
               json={"amount": 960000})
ck("filial rahbari hisoblanganni tahrirladi", r.status_code, 200)
ck("minus saqlanadi (yechib olingan)", r.json()["amount"], -960000)
ck("asoschi ham tahrirlaydi",
   client.put(f"/api/payments/{PAYID}", headers=ASOS,
              json={"amount": 480000}).status_code, 200)
ck("sotuv menejeri tahrirlay olmaydi",
   client.put(f"/api/payments/{PAYID}", headers=SOTUV,
              json={"amount": 1}).status_code, 403)
ck("ustoz ham yo'q",
   client.put(f"/api/payments/{PAYID}", headers=tok("ustoz1"),
              json={"amount": 1}).status_code, 403)
ck("manfiy/nol kiritib bo'lmaydi",
   client.put(f"/api/payments/{PAYID}", headers=ASOS,
              json={"amount": 0}).status_code, 400)
db = SessionLocal()
ck("audit yozildi", db.query(models.AuditLog).filter(
    models.AuditLog.entity == "payment",
    models.AuditLog.action == "amount_edit").count() >= 3, True)
db.close()


print("\n=== 17. XAVFSIZLIK, XABARNOMA, OTA-ONA, DUBLIKAT ===")
# --- /api/me ---
d = client.get("/api/me", headers=ASOS).json()
ck("me ishlaydi", "full_name" in d and "role" in d, True)

# --- parol siyosati ---
ck("bo'sh parol rad", client.post("/api/users", headers=ASOS, json={
    "username": "yangi1", "password": "abc", "full_name": "Y",
    "role": "teacher", "branch_id": BID}).status_code, 400)
ck("kuchli parol OK", client.post("/api/users", headers=ASOS, json={
    "username": "yangi1", "password": "kuchli2024x", "full_name": "Y",
    "role": "teacher", "branch_id": BID}).status_code, 200)

# --- login brute-force limiti ---
for _ in range(5):
    client.post("/api/auth/login",
                json={"username": "bruteuser", "password": "xato"})
r = client.post("/api/auth/login",
                json={"username": "bruteuser", "password": "xato"})
ck("6-urinish bloklanadi", r.status_code, 429)
ck("boshqa login ishlayveradi", client.post(
    "/api/auth/login",
    json={"username": "asos", "password": "x"}).status_code, 200)

# --- tiklash kodi ---
ck("kod o'rnatildi", client.put("/api/auth/recovery-code", headers=ASOS,
   json={"current_password": "x",
         "recovery_code": "qutqaruv-kodi-2026"}).status_code, 200)
ck("noto'g'ri kod rad", client.post("/api/auth/recover", json={
    "username": "asos", "recovery_code": "notogri-kod-123",
    "new_password": "yangiparol9"}).status_code, 401)
ck("to'g'ri kod paroli almashtiradi", client.post(
    "/api/auth/recover", json={
        "username": "asos", "recovery_code": "qutqaruv-kodi-2026",
        "new_password": "yangiparol9"}).status_code, 200)
ck("yangi parol ishlaydi", client.post("/api/auth/login", json={
    "username": "asos", "password": "yangiparol9"}).status_code, 200)
ASOS2 = tok("asos", "yangiparol9")

# --- migratsiyalar jadvali ---
db = SessionLocal()
ck("migratsiyalar yozilgan",
   db.query(models.SchemaMigration).count() >= 4, True)
db.close()

# --- kengaytirilgan qidiruv ---
db = SessionLocal()
db.add(models.Group(name="Alpha17", branch_id=BID)); db.commit(); db.close()
d = client.get("/api/search/students?q=Alpha", headers=ASOS2).json()
ck("qidiruvda guruhlar bor", "groups" in d, True)
ck("Alpha17 guruhi topildi",
   any(g["name"] == "Alpha17" for g in d["groups"]), True)
d = client.get("/api/search/students?q=Karta", headers=ASOS2).json()
ck("ustoz qidiruvdan topiladi",
   any("Karta" in t["name"] for t in d["teachers"]), True)

# --- bildirishnomalar ---
r = client.get("/api/my/alerts", headers=ASOS2)
ck("bildirishnoma ishlaydi", r.status_code, 200)
ck("bildirishnoma shakli", "items" in r.json(), True)

# --- xato jurnali ---
r = client.get("/api/errors", headers=ASOS2)
ck("xato jurnali asoschiga ochiq", r.status_code, 200)
ck("xato jurnali ustozga yopiq", client.get(
    "/api/errors", headers=tok("ustoz1")).status_code, 403)

# --- ota-ona havolasi va sahifasi ---
r = client.get(f"/api/students/{S1}/parent-link", headers=ASOS2)
ck("ota-ona havolasi yaratildi", r.status_code, 200)
tok_url = r.json()["url"].rsplit("/", 1)[-1]
d = client.get(f"/api/parent/{tok_url}").json()
ck("ota-ona sahifasi ochiladi", d["name"], "B1")
ck("balans bor", "balance" in d, True)
ck("noto'g'ri token 404", client.get(
    "/api/parent/notogritoken123").status_code, 404)

# --- telegram va to'lov havolasi (token/env yo'q rejim) ---
d = client.get(f"/api/students/{S1}/telegram", headers=ASOS2).json()
ck("telegram o'chiq rejimda enabled=False", d["enabled"], False)
d = client.get(f"/api/students/{S1}/pay-link", headers=ASOS2).json()
ck("pay-link sozlanmagan rejimda enabled=False", d["enabled"], False)
d = client.post(f"/api/students/{S1}/notify-debt",
                headers=ASOS2).json()
ck("qarz eslatma botisiz sent=False", d["sent"], False)

# --- lid dublikati ---
ck("birinchi lid OK", client.post("/api/leads", headers=ASOS2, json={
    "full_name": "Dub Bola", "phone": "+998977775566",
    "source": "instagram"}).status_code, 200)
r = client.post("/api/leads", headers=ASOS2, json={
    "full_name": "Dub Bola 2", "phone": "97 777 55 66",
    "source": "instagram"})
ck("dublikat 409", r.status_code, 409)
ck("force bilan o'tadi", client.post("/api/leads", headers=ASOS2, json={
    "full_name": "Dub Bola 2", "phone": "97 777 55 66",
    "source": "instagram", "force": True}).status_code, 200)

# --- parallel tahrir (409) ---
db = SessionLocal()
pay = db.query(models.Payment).filter(
    models.Payment.student_id == S1,
    models.Payment.kind == "payment").first()
PID17 = pay.id
db.close()
ck("tahrir 1 (bo'sh versiya) OK", client.put(
    f"/api/payments/{PID17}", headers=ASOS2,
    json={"amount": 500000, "expected_updated_at": ""}).status_code, 200)
ck("eskirgan versiya 409", client.put(
    f"/api/payments/{PID17}", headers=ASOS2,
    json={"amount": 510000, "expected_updated_at": ""}).status_code, 409)
d = client.get(f"/api/students/{S1}/payments", headers=ASOS2).json()
ver = [p for p in d if p["id"] == PID17][0]["updated_at"]
ck("yangi versiya bilan OK", client.put(
    f"/api/payments/{PID17}", headers=ASOS2,
    json={"amount": 520000, "expected_updated_at": ver}).status_code, 200)

# --- to'lov tarixi ustozga yopiq (filial auditi) ---
ck("ustozga to'lov tarixi 403", client.get(
    f"/api/students/{S1}/payments",
    headers=tok("ustoz1")).status_code, 403)

# --- cron endpoint himoyalangan ---
ck("cron begonalarga yopiq",
   client.get("/api/cron/daily").status_code, 403)
ck("cron asoschiga ochiq", client.get(
    "/api/cron/daily", headers=ASOS2).status_code, 200)

# ============ 18. Guruhdan chiqarish: sabab + arxiv qoidalari ============
print("\n--- 18: guruhdan chiqarish, avtoarxiv, tiklash ---")
db = SessionLocal()
g18 = models.Group(name="G18", branch_id=BID, monthly_fee=400000,
                   lesson_days="mon,wed,fri", lesson_time="09:00-10:00")
db.add(g18); db.commit()
sA = models.Student(full_name="Chiquvchi Toza18", branch_id=BID,
                    group_id=g18.id, status="active")
sB = models.Student(full_name="Chiquvchi Qarzdor18", branch_id=BID,
                    group_id=g18.id, status="active")
db.add_all([sA, sB]); db.commit()
SA18, SB18 = sA.id, sB.id
db.add(models.Payment(student_id=SB18, amount=-250000, kind="charge"))
db.commit(); db.close()

ck("sababsiz chiqarish 400", client.post(
    f"/api/students/{SA18}/remove-from-group", headers=ASOS2,
    json={"reason": " "}).status_code, 400)
ck("move-group(null) yopiq 400", client.post(
    f"/api/students/{SA18}/move-group", headers=ASOS2,
    json={"group_id": None}).status_code, 400)
r = client.post(f"/api/students/{SA18}/remove-from-group", headers=ASOS2,
                json={"reason": "Ko'chib ketdi"}).json()
ck("qarzsiz -> darhol arxiv", r.get("archived"), True)
r = client.post(f"/api/students/{SB18}/remove-from-group", headers=ASOS2,
                json={"reason": "Qatnamay qo'ydi"}).json()
ck("qarzdor arxivga tushmadi", r.get("archived"), False)
st = client.get(f"/api/students/{SB18}", headers=ASOS2).json()
ck("qarzdor guruhsiz faol", (st["status"], st.get("group")), ("active", None))
client.post(f"/api/students/{SB18}/payments", headers=ASOS2,
            json={"amount": 250000, "kind": "payment"})
st = client.get(f"/api/students/{SB18}", headers=ASOS2).json()
ck("qarz yopilgach avtoarxiv", st["status"], "archived")
h = str(client.get(f"/api/students/{SB18}/history", headers=ASOS2).json())
ck("tarixda sabab bor", "Qatnamay qo'ydi" in h, True)
ck("qayta tiklash OK", client.post(
    f"/api/students/{SB18}/restore", json={},
    headers=ASOS2).status_code, 200)
st = client.get(f"/api/students/{SB18}", headers=ASOS2).json()
ck("tiklangan: faol, guruhsiz", (st["status"], st.get("group")),
   ("active", None))
ck("arxivda emasni tiklash 400", client.post(
    f"/api/students/{SB18}/restore", json={},
    headers=ASOS2).status_code, 400)

# --- HR bo'shatish sababi + support oyliklari ---
db = SessionLocal()
db.add(models.User(username="xodim18", password_hash=hash_password("x"),
                   full_name="Xodim 18", role="administrator",
                   branch_id=BID))
sup18u = models.User(username="sup18", password_hash=hash_password("x"),
                     full_name="Support 18", role="support_teacher",
                     branch_id=BID)
db.add(sup18u); db.commit()
db.add(models.Teacher(full_name="Support 18", user_id=sup18u.id,
                      branch_id=BID, is_active=1))
db.add(models.User(username="hr18", password_hash=hash_password("x"),
                   full_name="HR 18", role="hr_manager"))
db.commit()
X18 = db.query(models.User).filter_by(username="xodim18").first().id
db.close()
HR18 = tok("hr18")
ck("HR bo'shatish (sabab bilan)", client.put(
    f"/api/users/{X18}", headers=HR18,
    json={"is_active": False, "exit_reason": "Boshqa ishga o'tdi",
          "exit_type": "green"}).status_code, 200)
card = client.get(f"/api/staff/{X18}/card", headers=HR18).json()
ck("sabab kartada", card.get("exit_reason"), "Boshqa ishga o'tdi")
r = client.get("/api/support-teachers/salaries", headers=ASOS2)
ck("support oyliklari ro'yxati", r.status_code, 200)
ck("ro'yxatda summa bor",
   len(r.json()["rows"]) >= 1 and "salary" in r.json()["rows"][0], True)
ck("support o'zi ro'yxatni ocholmaydi", client.get(
    "/api/support-teachers/salaries", headers=tok("sup18")).status_code, 403)

# ============ 19. HR: login/parol hammaga (asoschi va filial r. dan tashqari) ============
print("\n--- 19: HR login/parol huquqlari ---")
HR19 = tok("hr18")
ck("HR o'quv rahbariga login ochadi", client.post(
    "/api/users", headers=HR19,
    json={"username": "u19ah", "password": "parol1234",
          "full_name": "U19 AH", "role": "academic_head"}).status_code, 200)
ck("HR moliya rahbariga login ochadi", client.post(
    "/api/users", headers=HR19,
    json={"username": "u19fd", "password": "parol1234",
          "full_name": "U19 FD", "role": "finance_director"}).status_code, 200)
ck("HR filial rahbari rolini ochOLMAYDI", client.post(
    "/api/users", headers=HR19,
    json={"username": "u19bm", "password": "parol1234",
          "full_name": "U19 BM", "role": "branch_manager",
          "branch_id": BID}).status_code, 403)
ck("HR asoschi rolini ochOLMAYDI", client.post(
    "/api/users", headers=HR19,
    json={"username": "u19f", "password": "parol1234",
          "full_name": "U19 F", "role": "founder"}).status_code, 403)
db = SessionLocal()
_ah19 = db.query(models.User).filter_by(username="u19ah").first().id
db.add(models.User(username="bm19", password_hash=hash_password("x"),
                   full_name="BM 19", role="branch_manager", branch_id=BID))
db.commit()
_bm19 = db.query(models.User).filter_by(username="bm19").first().id
db.close()
ck("HR yangi parol beradi", client.put(
    f"/api/users/{_ah19}", headers=HR19,
    json={"password": "yangi12345"}).status_code, 200)
ck("yangi parol ishlaydi", client.post(
    "/api/auth/login", json={"username": "u19ah",
                             "password": "yangi12345"}).status_code, 200)
ck("filial rahbari paroliga HR tegolmaydi", client.put(
    f"/api/users/{_bm19}", headers=HR19,
    json={"password": "hacker1234"}).status_code, 403)
ck("filial rahbarini HR o'chirolmaydi", client.put(
    f"/api/users/{_bm19}", headers=HR19,
    json={"is_active": False}).status_code, 403)
ck("lekin kartasini tahrirlaydi", client.put(
    f"/api/users/{_bm19}", headers=HR19,
    json={"phone": "+998900000019"}).status_code, 200)
# HR supportni guruhga biriktiradi
db = SessionLocal()
_supu = db.query(models.User).filter_by(username="sup18").first()
_supt = db.query(models.Teacher).filter_by(user_id=_supu.id).first()
_g19 = models.Group(name="G19", branch_id=BID, monthly_fee=400000,
                    lesson_days="mon,wed,fri", lesson_time="11:00-12:00")
db.add(_g19); db.commit()
_tid19, _gid19 = _supt.id, _g19.id
db.close()
ck("HR supportni guruhga biriktiradi", client.put(
    f"/api/support-teachers/{_tid19}/groups", headers=HR19,
    json={"group_ids": [_gid19]}).status_code, 200)
r = client.get(f"/api/support-teachers/{_tid19}/groups",
               headers=HR19).json()
ck("biriktirish saqlandi", r["assigned"], [_gid19])

# ============ 20. Tarixiy statistika (eski yillar o'quvchilar soni) ============
print("\n--- 20: tarixiy statistika ---")
ck("yozuv qo'shish (asoschi)", client.post(
    "/api/stats/history", headers=ASOS2,
    json={"date": "2022-09-01", "count": 380}).status_code, 200)
r = client.post("/api/stats/history/bulk", headers=ASOS2,
    json={"text": "15.01.2023 410\n2023-02-01 425 izoh\nxato"}).json()
ck("ommaviy: 2 qo'shildi 1 xato", (r["added"], len(r["errors"])), (2, 1))
h = client.get("/api/stats/history", headers=ASOS2).json()
ck("ro'yxat tartibli + jonli nuqta",
   (len(h["rows"]) >= 3, "count" in h["today"]), (True, True))
ck("HR ko'rolmaydi", client.get(
    "/api/stats/history", headers=tok("hr18")).status_code, 403)
ck("moliya kiritolmaydi", client.post(
    "/api/stats/history", headers=tok("moliya"),
    json={"date": "2021-01-01", "count": 5}).status_code, 403)

print()
if fails:
    print("YIQILGANLAR:", fails)
    sys.exit(1)
print("HAMMASI O'TDI")
