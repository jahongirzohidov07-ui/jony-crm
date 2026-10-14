"""XARAJATLAR -> OYLIK va USTOZLAR OYLIGI BITTA MANBADAN (2026-10-12).

Jahongir: "men oylikni to'lagan bo'lsa ham xarajatlar bo'limida oylikni
tanlab shu joyda to'lanmagan bo'lib turibdi" (Hisobotlar -> Oyliklar ->
Ustozlar oyligi, Sentabr 2026, Bekobod 2 — hamma ustoz "TO'LANMAGAN").

Tekshiriladi:
  1. Xarajatlar -> Oylik (5-oktabrda, "Qaysi oy uchun" = sentabr) —
     sentabr hisobotida ustoz va uning HAR GURUHI "to'landi"; Moliya ->
     Oyliklar va ustozning o'z ko'rinishi ham shunday; foyda-zararga
     yangi qator tushmaydi;
  2. qisman to'lov va avans — "qisman", qoldig'i to'g'ri; oktabr uchun
     berilgani sentabrga qo'shilmaydi;
  3. hisobotdagi guruh "To'landi" — Xarajatlar orqali berilganini taniydi
     (ikkinchi to'lov yozilmaydi), berilmagan guruhga faqat QOLGANINI
     yozadi; foyda-zarar ikkala holda ham o'zgarmaydi;
  4. akkaunti kartaga bog'lanmagan ustoz — ro'yxatda bitta qator, pul
     ustoz kartasiga (xarajatga emas);
  5. ma'muriy xodim oyligi avvalgidek xarajat (foyda-zararda bir marta);
  6. examiner / support — Xarajatlar orqali berilgani ularning oylik
     ro'yxatida "berilgan"; ustozning guruh oyligi ikki marta sanalmaydi;
  7. bir martalik tuzatish: xarajat bo'lib yozilgan ustoz oyligi kartaga
     ko'chadi (ish haqidan oshib ketadigan — joriy oyda ham — va eski
     oyniki tegilmaydi), audit yoziladi, ikkinchi yurishda hech narsa
     qilmaydi; kassa o'zgarmaydi, foyda-zarardan faqat ikki marta
     sanalgan qism chiqadi;
  9. ko'rib chiqish topilmalari (2026-10-12): boshqa filialdan to'liq
     berilgan ustoz va filialsiz guruh — "To'landi" ikkinchi marta pul
     yozmaydi; "Administrator + ustoz/examiner" ning fiks oyligi
     xarajat bo'lib qoladi va examinerlik puli bo'lib ko'rinmaydi;
     nofaol karta tanlanmaydi; examiner boshlig'i boshqalarning
     Xarajatlardagi oyligini ko'rmaydi; tuzatish rahbar oyligiga va
     filialsiz to'lovga tegmaydi.
"""
import os
import sys
import tempfile
from datetime import date

_DIR = os.path.join(tempfile.gettempdir(), "teacher_salary_expense_sync_test")
os.makedirs(_DIR, exist_ok=True)
_DB = os.path.join(_DIR, "db.sqlite")
os.environ["DATABASE_URL"] = "sqlite:///" + _DB.replace(chr(92), "/")
if os.path.exists(_DB):
    os.remove(_DB)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient          # noqa: E402
import main, models, roles, billing                # noqa: E402
import entry                                       # noqa: E402
import common                                      # noqa: E402
import finance                                     # noqa: E402
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


Y, M = 2026, 9
SEP, OCT = "2026-09", "2026-10"
db = SessionLocal()
b1 = models.Branch(name="Bekobod 1"); b2 = models.Branch(name="Bekobod 2")
db.add_all([b1, b2]); db.commit()
B1, B2 = b1.id, b2.id


def mk_user(username, name, role, branch=B2, **kw):
    u = models.User(username=username, password_hash=hash_password("x"),
                    full_name=name, role=role, branch_id=branch, **kw)
    db.add(u); db.commit()
    return u


mk_user("asos", "Jahongir", roles.FOUNDER, branch=None)
mk_user("adm1", "Admin Bir", roles.ADMINISTRATOR, branch=B1)
u_sar = mk_user("sardor", "Sardor Mirfozilov", roles.TEACHER)
u_asl = mk_user("asliddin", "Asliddin Nabiyev", roles.TEACHER)
u_mal = mk_user("malika", "Malika Karimova", roles.TEACHER)
u_iro = mk_user("iroda", "Iroda Admin", roles.ADMINISTRATOR,
                fix_salary=2_000_000)
u_ex = mk_user("exam", "Examiner Ali", roles.EXAMINER)
u_sup = mk_user("sup", "Support Vali", roles.SUPPORT_TEACHER)


def mk_teacher(name, user=None):
    t = models.Teacher(full_name=name, is_active=1, branch_id=B2,
                       grade="middle", user_id=user.id if user else None)
    db.add(t); db.commit()
    return t


t_sar = mk_teacher("Sardor Mirfozilov", u_sar)
t_asl = mk_teacher("Asliddin Nabiyev")          # akkaunti bog'lanmagan
t_mal = mk_teacher("Malika Karimova", u_mal)
t_sup = mk_teacher("Support Vali", u_sup)       # guruh darsi yo'q


def group(name, t, n, branch=B2):
    g = models.Group(name=name, branch_id=branch, teacher_id=t.id,
                     lesson_price=40_000, standard_lessons_per_month=12,
                     monthly_fee=480_000, rate_manual=1,
                     teacher_rate_per_student=120_000)
    db.add(g); db.commit()
    kids = []
    for i in range(n):
        s = models.Student(full_name=f"{name} bola {i}", branch_id=branch,
                           status="active", group_id=g.id,
                           enrolled_date=date(Y, M, 1))
        db.add(s); db.commit()
        db.add(models.StudentGroupLink(student_id=s.id, group_id=g.id,
                                       is_primary=1, active=1))
        kids.append(s)
    db.commit()
    for d in range(12):
        les = models.Lesson(group_id=g.id, date=date(Y, M, d + 2),
                            teacher_id=t.id, held=1)
        db.add(les); db.commit()
        for s in kids:
            db.add(models.Attendance(student_id=s.id, lesson_id=les.id,
                                     present=1))
    db.commit()
    return g.id


# 1 yo'qlama = 120 000 / 12 = 10 000; o'quvchi oyiga 120 000
G_S1 = group("S-1", t_sar, 3)        # 360 000
G_S2 = group("S-2", t_sar, 2)        # 240 000
G_A1 = group("A-1", t_asl, 4)        # 480 000
G_M1 = group("M-1", t_mal, 5)        # 600 000
TS, TA, TM, TSUP = t_sar.id, t_asl.id, t_mal.id, t_sup.id
US, UA, UM, UI, UEX, USUP = (u_sar.id, u_asl.id, u_mal.id, u_iro.id,
                             u_ex.id, u_sup.id)
db.close()

H = tok("asos")


def report(h=None, month=M, branch=B2):
    q = f"/api/reports/teacher-payroll?year={Y}&month={month}"
    if branch:
        q += f"&branch_id={branch}"
    r = client.get(q, headers=h or H)
    assert r.status_code == 200, r.text
    return r.json()


def trow(rep, tid):
    return next((r for r in rep["rows"] if r["teacher_id"] == tid), None)


def grow(rep, tid, gid):
    return next(g for g in trow(rep, tid)["groups"] if g["group_id"] == gid)


def pnl(month, branch=B2):
    r = client.get(f"/api/reports/pnl?year={Y}&month={month}"
                   f"&branch_id={branch}", headers=H).json()
    return r["outflow_total"], r["payroll_total"], {
        l["category"]: l["amount"] for l in r["expense_lines"]}


def kassa_chiqim(month):
    r = client.get(f"/api/reports/cashflow-ledger?year={Y}&month={month}"
                   f"&branch_id={B2}", headers=H)
    assert r.status_code == 200, r.text
    return r.json()["chiqim"]


def counts():
    s = SessionLocal()
    out = (s.query(models.Expense).count(),
           s.query(models.TeacherPayment).count())
    s.close()
    return out


def xarajat_oylik(amount, *, teacher_id=None, staff_user_id=None,
                  period=SEP, on="2026-10-05", branch=B2, h=None):
    """Moliya.tsx ExpenseModal "Oylik" rejimi yuboradigan so'rov."""
    return client.post("/api/expenses", headers=h or H, json={
        "date": on, "category": "admin_salary", "amount": amount,
        "note": None, "method": "cash", "channel": None,
        "branch_id": branch, "teacher_id": teacher_id,
        "staff_user_id": staff_user_id, "period": period,
        "qty": None, "consumable_id": None, "new_item_name": None})


PNL9_0, PAY9, _ = pnl(9)
PNL10_0, _, _ = pnl(10)
ck("boshlang'ich: sentabr ish haqi yo'qlamadan", PAY9, 1_680_000.0)
rep = report()
ck("boshlang'ich: hamma to'lanmagan", (rep["paid"], rep["unpaid"]),
   (0.0, 1_680_000.0))

print("\n=== 1. Xarajatlar -> Oylik: sentabr oyligi 5-oktabrda ===")
r = xarajat_oylik(600_000, teacher_id=TS)
ck("qabul qilindi — ustoz oyligi", (r.status_code, r.json()["category"]),
   (200, "teacher_salary"))
ck("xarajat jadvaliga tushmadi, ustoz kartasiga tushdi", counts(), (0, 1))
rep = report()
s_row = trow(rep, TS)
ck("Sardor sentabrda to'langan", (s_row["paid_amount"], s_row["status"]),
   (600_000.0, "paid"))
ck("S-1 guruhi to'landi", (grow(rep, TS, G_S1)["paid"],
                           grow(rep, TS, G_S1)["paid_amount"]),
   (True, 360_000.0))
ck("S-2 guruhi to'landi", (grow(rep, TS, G_S2)["paid"],
                           grow(rep, TS, G_S2)["paid_amount"]),
   (True, 240_000.0))
ck("tepadagi jamlar", (rep["paid"], rep["unpaid"]), (600_000.0, 1_080_000.0))
rep_all = report(branch=None)
ck("barcha filiallarda ham to'langan", trow(rep_all, TS)["paid_amount"],
   600_000.0)
pr = client.get(f"/api/payroll?year={Y}&month={M}&branch_id={B2}",
                headers=H).json()
ck("Moliya -> Oyliklar (/api/payroll) ham to'langan",
   next(x["paid"] for x in pr["rows"] if x["teacher_id"] == TS), 600_000.0)
own = report(h=tok("sardor"), branch=None)
ck("ustozning o'z ko'rinishi: to'langan, guruhlari ham",
   (own["rows"][0]["paid_amount"],
    [g["paid"] for g in own["rows"][0]["groups"]]),
   (600_000.0, [True, True]))
card = client.get(f"/api/teachers/{TS}/finance", headers=H)
ck("ustoz kartasi (oylar daftari) ochiladi", card.status_code, 200)
s = SessionLocal()
led = common._month_ledger(s, s.query(models.Teacher).get(TS))
ck("ustoz kartasida sentabr oyligi berilgan",
   (led["by_period_map"][SEP]["paid_for"], led["by_period_map"][SEP]["left"]),
   (600_000.0, 0.0))
s.close()
ck("oktabrga yozilmadi (to'lov oyi emas, QAYSI OY UCHUN)",
   common._teacher_paid(SessionLocal(), TS, period=OCT,
                        since=date(2026, 10, 1), until=date(2026, 10, 31)),
   0.0)
ck("foyda-zarar sentabr o'zgarmadi", pnl(9)[0], PNL9_0)
ck("foyda-zarar oktabr — yangi xarajat qatori yo'q", pnl(10)[0], PNL10_0)

print("\n=== 2. Qisman to'lov, avans, keyingi oy uchun to'lov ===")
r = xarajat_oylik(250_000, teacher_id=TM)
ck("qisman berildi", r.status_code, 200)
rep = report()
m_row = trow(rep, TM)
ck("Malika — qisman", (m_row["paid_amount"], m_row["left"],
                       m_row["status"]), (250_000.0, 350_000.0, "partial"))
mg = grow(rep, TM, G_M1)
ck("M-1 guruhi — qisman", (mg["paid"], mg["status"], mg["paid_amount"],
                           mg["left"]), (False, "partial", 250_000.0,
                                         350_000.0))
r = client.post(f"/api/teachers/{TM}/payments", headers=H, json={
    "amount": 100_000, "kind": "advance", "date": "2026-09-20",
    "period": SEP, "method": "cash", "branch_id": B2})
ck("avans (ustoz kartasidan, sentabr ichida)", r.status_code, 200)
r = xarajat_oylik(70_000, teacher_id=TM, period=OCT, on="2026-10-10")
ck("oktabr UCHUN berilgan pul", r.status_code, 200)
rep = report()
ck("sentabrga faqat sentabr uchun berilganlar (250k + 100k avans)",
   (trow(rep, TM)["paid_amount"], trow(rep, TM)["status"]),
   (350_000.0, "partial"))

print("\n=== 3. Hisobotdagi guruh \"To'landi\" ===")
n_exp, n_tp = counts()
P9, P10 = pnl(9)[0], pnl(10)[0]
K10 = kassa_chiqim(10)
r = client.post("/api/reports/teacher-payroll/pay", headers=H, json={
    "teacher_id": TS, "group_id": G_S1, "year": Y, "month": M})
ck("Xarajatlar orqali to'langan guruh — yangi to'lov YO'Q",
   (r.status_code, r.json()["created"], r.json()["already_paid"]),
   (200, False, True))
ck("to'lovlar soni o'zgarmadi", counts(), (n_exp, n_tp))
ck("kassa o'zgarmadi", kassa_chiqim(10), K10)
r = client.post("/api/reports/teacher-payroll/pay", headers=H, json={
    "teacher_id": TM, "group_id": G_M1, "year": Y, "month": M})
ck("qisman guruh — faqat QOLGANI yoziladi",
   (r.status_code, r.json()["created"], r.json()["amount"]),
   (200, True, 250_000.0))
ck("bitta yangi to'lov, xarajat emas", counts(), (n_exp, n_tp + 1))
s = SessionLocal()
tp = s.query(models.TeacherPayment).order_by(
    models.TeacherPayment.id.desc()).first()
ck("to'lov: sentabr uchun, guruhga va filialga bog'langan",
   (tp.teacher_id, tp.period, tp.group_id, tp.branch_id, tp.amount),
   (TM, SEP, G_M1, B2, 250_000.0))
s.close()
rep = report()
ck("Malika endi to'liq to'langan", (trow(rep, TM)["paid_amount"],
                                    grow(rep, TM, G_M1)["paid"]),
   (600_000.0, True))
r = client.post("/api/reports/teacher-payroll/pay", headers=H, json={
    "teacher_id": TM, "group_id": G_M1, "year": Y, "month": M})
ck("qayta bosilsa — hech narsa yozilmaydi", r.json()["created"], False)
ck("foyda-zarar sentabr — hisoblangan ish haqi, o'zgarmadi", pnl(9)[0], P9)
ck("foyda-zarar oktabr — ikki marta tushmadi", pnl(10)[0], P10)
k10 = kassa_chiqim(10)
ck("kassada faqat haqiqiy berilgan 250 000 qo'shildi",
   round(k10["cash"] - K10["cash"], 2), 250_000.0)
r = client.post("/api/reports/teacher-payroll/pay", headers=tok("adm1"),
                json={"teacher_id": TA, "group_id": G_A1, "year": Y,
                      "month": M})
ck("boshqa filial administratori bosolmaydi", r.status_code, 403)
ck("ustozning ish haqi yo'q guruh — 400",
   client.post("/api/reports/teacher-payroll/pay", headers=H, json={
       "teacher_id": TS, "group_id": G_A1, "year": Y,
       "month": M}).status_code, 400)
ck("hisobot \"can_pay\" belgisi", report()["can_pay"], True)

print("\n=== 4. Akkaunti kartaga bog'lanmagan ustoz ===")
rows = client.get(f"/api/expenses/staff?branch_id={B2}", headers=H).json()["rows"]
asl = [x for x in rows if x["name"] == "Asliddin Nabiyev"]
ck("ro'yxatda BITTA qator, ustoz kartasi bilan",
   [(x["teacher_id"], x["user_id"], x["to_salary_card"]) for x in asl],
   [(TA, UA, True)])
n_exp, n_tp = counts()
r = xarajat_oylik(480_000, staff_user_id=UA)      # eski UI: akkaunt tanlandi
ck("akkaunt tanlansa ham — ustoz oyligi", r.json()["category"],
   "teacher_salary")
ck("xarajatga emas, ustoz kartasiga", counts(), (n_exp, n_tp + 1))
s = SessionLocal()
ck("karta akkauntga bog'landi", s.query(models.Teacher).get(TA).user_id, UA)
s.close()
ck("Asliddin to'langan", trow(report(), TA)["status"], "paid")
ck("foyda-zarar oktabr o'zgarmadi", pnl(10)[0], P10)

print("\n=== 5. Ma'muriy xodim oyligi — avvalgidek xarajat ===")
P10 = pnl(10)[0]
r = xarajat_oylik(627_000, staff_user_id=UI)
ck("xarajat bo'ldi", (r.json()["category"], r.json()["id"] > 0),
   ("admin_salary", True))
ck("foyda-zararda BIR marta", round(pnl(10)[0] - P10, 2), 627_000.0)
ss = client.get("/api/expenses/staff-salaries?year=2026&month=10",
                headers=H).json()
ck("xodimlar oyliklari ro'yxatida", [x["amount"] for x in ss["rows"]],
   [627_000.0])

print("\n=== 6. Examiner va support ===")
s = SessionLocal()
ck("avval: examinerga berilgan 0", entry._staff_paid(s, UEX, SEP), 0.0)
s.close()
r = xarajat_oylik(300_000, staff_user_id=UEX)
ck("examiner — xarajat (ustoz kartasi yo'q)", r.json()["category"],
   "admin_salary")
r = client.post("/api/staff-salary", headers=H, json={
    "user_id": UEX, "amount": 50_000, "kind": "advance", "period": SEP})
ck("examiner oylik oynasidan avans", r.status_code, 200)
s = SessionLocal()
ck("examiner: Xarajatlar + oylik oynasi = 350 000",
   entry._staff_paid(s, UEX, SEP), 350_000.0)
ck("examiner: oktabr uchun hech narsa", entry._staff_paid(s, UEX, OCT), 0.0)
s.close()
hist = client.get(f"/api/staff-salary?user_id={UEX}&period={SEP}",
                  headers=H).json()
ck("tarixda ikkala yo'l ham, jami",
   (sorted(x["source"] for x in hist["rows"]), hist["total"]),
   (["expense", "staff"], 350_000.0))
rows = client.get(f"/api/expenses/staff?branch_id={B2}", headers=H).json()["rows"]
sup = next(x for x in rows if x["name"] == "Support Vali")
ck("support — ustoz kartasi bilan", (sup["teacher_id"], sup["to_salary_card"]),
   (TSUP, True))
r = xarajat_oylik(200_000, teacher_id=TSUP)
ck("support oyligi kartaga", r.json()["category"], "teacher_salary")
s = SessionLocal()
ck("support: berilgan 200 000 (guruh darsi yo'q — hammasi supportniki)",
   entry._staff_paid(s, USUP, SEP), 200_000.0)
ck("Sardor: ustoz kartasidagi pul guruh oyligiga to'liq ketgan — "
   "examiner/support ro'yxatiga qayta tushmaydi",
   entry._staff_paid(s, US, SEP), 0.0)
s.close()
ck("support Ustozlar oyligida chiqmaydi (guruh darsi yo'q)",
   trow(report(), TSUP), None)

print("\n=== 7. Bir martalik tuzatish: eski xarajat yozuvlari ===")
s = SessionLocal()
u_nod = models.User(username="nodira", password_hash=hash_password("x"),
                    full_name="Nodira Usmonova", role=roles.TEACHER,
                    branch_id=B2)
s.add(u_nod); s.commit()
t_nod = models.Teacher(full_name="Nodira Usmonova", is_active=1,
                       branch_id=B2, grade="middle")
s.add(t_nod); s.commit()
UN, TN = u_nod.id, t_nod.id
s.close()
db = SessionLocal()
G_N1 = group("N-1", db.query(models.Teacher).get(TN), 2)       # 240 000
# Oktabrda ham 3 dars (2 bola x 3 x 10 000 = 60 000 — oy hali tugamagan)
for d in (1, 2, 5):
    _les = models.Lesson(group_id=G_N1, date=date(2026, 10, d),
                         teacher_id=TN, held=1)
    db.add(_les); db.commit()
    for _s in db.query(models.Student).filter(
            models.Student.group_id == G_N1).all():
        db.add(models.Attendance(student_id=_s.id, lesson_id=_les.id,
                                 present=1))
    db.commit()
db.close()
# "Bugun" oktabr: sentabr tugagan, oktabr joriy oy (test sanaga bog'liq
# bo'lmasin — finance o'z nusxasini ishlatadi, shuni almashtiramiz)
finance._period_closed = lambda p: str(p) < OCT
s = SessionLocal()
old = [
    # 1) ko'chadi: sentabr oyligi, 6-oktabrda, Bekobod 2 kassasidan
    models.Expense(date=date(2026, 10, 6), category="admin_salary",
                   amount=240_000, note="Nodira Usmonova — oylik",
                   branch_id=B2, method="card", staff_user_id=UN,
                   period=SEP, created_by="Admin"),
    # 2) ish haqidan oshadi — tegilmaydi (qo'lda ko'rish uchun auditda)
    models.Expense(date=date(2026, 10, 7), category="admin_salary",
                   amount=100_000, branch_id=B2, method="cash",
                   staff_user_id=UN, period=SEP, created_by="Admin"),
    # 3) 5-sentabr, oyi yozilmagan — avgust oyligi; eski oy, tegilmaydi
    models.Expense(date=date(2026, 9, 5), category="admin_salary",
                   amount=50_000, branch_id=B2, method="cash",
                   staff_user_id=UN, period=None, created_by="Admin"),
    # 4) JORIY oy (oktabr) avansi — hozircha ishlagani 60 000 dan
    #    katta: noaniq, tegilmaydi (qo'lda ko'rish uchun auditda)
    models.Expense(date=date(2026, 10, 3), category="admin_salary",
                   amount=300_000, branch_id=B2, method="cash",
                   staff_user_id=UN, period=OCT, created_by="Admin"),
]
s.add_all(old); s.commit()
E1, E2, E3, E4 = (e.id for e in old)
s.close()
rep = report()
ck("avval: Nodira to'lanmagan", trow(rep, TN)["paid_amount"], 0.0)
P9, P10 = pnl(9)[0], pnl(10)[0]
K9, K10 = kassa_chiqim(9), kassa_chiqim(10)
n_exp, n_tp = counts()

KEY = "teacher_salary_expense_sync_2026-10"
s = SessionLocal()
AU0 = s.query(models.AuditLog).filter(
    models.AuditLog.action == "expense_to_teacher_payment").count()
ck("kalit login paytida belgilangan (bo'sh bazada)",
   common._seed_done(s, KEY), True)
# Deploydan keyingi birinchi yurishni takrorlaymiz
s.query(models.SeedMark).filter(models.SeedMark.key == KEY).delete()
s.commit()
common._seed_keys(s).discard(KEY)
entry._mc_ensure(s)
ck("tuzatish yurdi, kalit belgilandi", common._seed_done(s, KEY), True)
s.close()
s = SessionLocal()
left = sorted(e.id for e in s.query(models.Expense)
              .filter(models.Expense.staff_user_id == UN).all())
ck("faqat 1-yozuv ko'chdi, qolganlari joyida", left, sorted([E2, E3, E4]))
tp = sorted(s.query(models.TeacherPayment)
            .filter(models.TeacherPayment.teacher_id == TN).all(),
            key=lambda p: p.period)
ck("ustoz kartasida bitta to'lov — sana, usul, filial, oy saqlangan",
   [(p.amount, p.period, str(p.paid_on), p.method, p.branch_id)
    for p in tp], [(240_000.0, SEP, "2026-10-06", "card", B2)])
ck("izohda manba xarajat", f"Xarajat #{E1} dan" in (tp[0].note or ""),
   True)
led = common._month_ledger(s, s.query(models.Teacher).get(TN))
ck("Nodira kartasida sentabr berilgan", led["by_period_map"][SEP]["paid_for"],
   240_000.0)
au = (s.query(models.AuditLog)
      .filter(models.AuditLog.action == "expense_to_teacher_payment")
      .order_by(models.AuditLog.id.desc()).all())
ck("auditda shu yurish uchun bitta umumiy yozuv", len(au), AU0 + 1)
ck("auditda ko'chgani va tegilmagani",
   (f"xarajat #{E1} ->" in (au[0].note or ""),
    "TEGILMADI: " in (au[0].note or "")
    and f"xarajat #{E2}: " in (au[0].note or "").split("TEGILMADI: ")[1],
    f"xarajat #{E4}: Nodira Usmonova 300000 ({OCT}) — joriy oy"
    in (au[0].note or ""),
    f"#{E3}" in (au[0].note or "")), (True, True, True, False))
s.close()
ck("jadval: -1 xarajat, +1 ustoz to'lovi", counts(), (n_exp - 1, n_tp + 1))
rep = report()
ck("Nodira endi to'langan, guruhi ham",
   (trow(rep, TN)["paid_amount"], grow(rep, TN, G_N1)["paid"]),
   (240_000.0, True))
ck("oktabr avansi xarajatda qoldi (kartaga tushmadi)",
   trow(report(month=10), TN)["paid_amount"], 0.0)
ck("foyda-zarar sentabr o'zgarmadi", pnl(9)[0], P9)
ck("foyda-zarar oktabr: faqat ikki marta sanalgan 240 000 chiqdi",
   round(P10 - pnl(10)[0], 2), 240_000.0)
ck("kassa (sentabr) o'zgarmadi", kassa_chiqim(9), K9)
k10 = kassa_chiqim(10)
ck("kassa (oktabr) jami o'zgarmadi",
   {k: round(v, 2) for k, v in k10.items()},
   {k: round(v, 2) for k, v in K10.items()})

print("\n=== 7b. Ikkinchi yurish — idempotent ===")
s = SessionLocal()
res = finance._teacher_salary_expense_sync(s)
ck("hech narsa ko'chmadi", res["moved"], [])
ck("oshadiganlar hamon tegilmagan",
   sorted(x["expense_id"] for x in res["skipped"]), sorted([E2, E4]))
s.close()
ck("jadval o'zgarmadi", counts(), (n_exp - 1, n_tp + 1))
ck("foyda-zarar o'zgarmadi", pnl(10)[0], P10 - 240_000)
s = SessionLocal()
entry._mc_ensure(s)        # kalit bor — qayta yurmaydi
ck("audit yozuvi ko'paymadi", s.query(models.AuditLog).filter(
    models.AuditLog.action == "expense_to_teacher_payment").count(),
   AU0 + 1)
s.close()

print("\n=== 8. Taqsimot va filial jamlari bir xil (bitta manba) ===")
s = SessionLocal()
ctx = billing.PayrollContext(s)
ctx.prefetch([TS, TM, TA, TN])
S9, E9 = billing.month_bounds(Y, M)
for tid in (TS, TM, TA, TN):
    e = common._teacher_earned(s, tid, since=S9, until=E9, ctx=ctx)
    al = common._teacher_pay_alloc(
        e, ctx.groups, common._teacher_pays_for(s, tid, SEP, ctx=ctx))
    worked = {ctx.groups[g["group_id"]].branch_id for g in e["by_group"]}
    scoped = common._teacher_paid_scoped(
        s, tid, since=S9, until=E9, ctx=ctx, period=SEP, branches={B2},
        part=e["amount"], whole=e["amount"], worked=worked)
    ck(f"ustoz #{tid}: guruhlar + ortiqcha = filial jami",
       round(sum(al["by_group"].values()) + al["over"].get(B2, 0.0), 2),
       scoped)
s.close()

print("\n=== 9. Ko'rib chiqish topilmalari (2026-10-12) ===")
db = SessionLocal()
u_hex = mk_user("hex", "Bosh Examiner", roles.HEAD_EXAMINER)
# Ustozlik qo'shimcha lavozimi bor administrator, kartasi bog'lanmagan
u_nr = mk_user("nodir", "Nodir Rahbar", roles.ADMINISTRATOR,
               fix_salary=2_000_000)
db.add(models.UserRole(user_id=u_nr.id, role=roles.TEACHER)); db.commit()
# Administrator + examiner
u_ae = mk_user("dilnoza", "Dilnoza AdminExam", roles.ADMINISTRATOR,
               fix_salary=2_000_000)
db.add(models.UserRole(user_id=u_ae.id, role=roles.EXAMINER)); db.commit()
# Ustoz, karta faqat NOFAOL
u_ic = mk_user("rahimova", "Dilnoza Rahimova", roles.TEACHER)
t_ic = models.Teacher(full_name="Dilnoza Rahimova", is_active=0,
                      branch_id=B2, grade="middle")
t_nr = models.Teacher(full_name="Nodir Rahbar", is_active=1, branch_id=B2,
                      grade="middle")
# Asosiy filiali Bekobod 1, Bekobod 2 da ham dars beradi
t_el = models.Teacher(full_name="Elena Petrova", is_active=1, branch_id=B1,
                      grade="middle")
# Filialsiz guruhi bor ustoz
t_kh = models.Teacher(full_name="Kamol Hasanov", is_active=1, branch_id=B2,
                      grade="middle")
db.add_all([t_ic, t_nr, t_el, t_kh]); db.commit()
TIC, TNR, TEL, TKH = t_ic.id, t_nr.id, t_el.id, t_kh.id
UNR, UAE, UIC = u_nr.id, u_ae.id, u_ic.id
G_E1 = group("E-1", t_el, 3, branch=B1)       # 360 000
G_E2 = group("E-2", t_el, 2)                  # 240 000 (Bekobod 2)
G_K1 = group("K-1", t_kh, 3)                  # 360 000
G_K0 = group("K-0", t_kh, 2, branch=None)     # 240 000, filialsiz
db.close()


def tick(tid, gid, h=None):
    r = client.post("/api/reports/teacher-payroll/pay", headers=h or H,
                    json={"teacher_id": tid, "group_id": gid, "year": Y,
                          "month": M})
    assert r.status_code == 200, r.text
    return r.json()


def tp_sum(tid, per=SEP):
    s = SessionLocal()
    v = sum(float(p.amount or 0) for p in s.query(models.TeacherPayment)
            .filter(models.TeacherPayment.teacher_id == tid,
                    models.TeacherPayment.period == per).all())
    s.close()
    return round(v, 2)


# 9a. Oylik Bekobod 1 dan to'liq berilgan — Bekobod 2 guruhi qayta
#     to'lanmaydi, barcha filiallarda guruhlar ham "to'landi"
r = xarajat_oylik(600_000, teacher_id=TEL, branch=B1)
ck("Elena: oylik Bekobod 1 dan", r.status_code, 200)
ra = report(branch=None)
ck("barcha filiallar: Elena va ikkala guruhi to'langan",
   (trow(ra, TEL)["status"], grow(ra, TEL, G_E1)["paid"],
    grow(ra, TEL, G_E2)["paid"]), ("paid", True, True))
n_exp, n_tp = counts()
res = tick(TEL, G_E2)
ck("Bekobod 2 guruhiga \"To'landi\" — ikkinchi marta yozilmaydi",
   (res["created"], res["already_paid"]), (False, True))
ck("to'lovlar o'zgarmadi, jami = ish haqi", (counts(), tp_sum(TEL)),
   ((n_exp, n_tp), 600_000.0))

# 9b. Filialsiz guruh: bir bosish — to'landi, keyingilari hech narsa
ck("K-0 birinchi bosish", tick(TKH, G_K0)["created"], True)
ck("K-0 qayta bosish", (tick(TKH, G_K0)["created"],
                        tick(TKH, G_K0)["created"]), (False, False))
ra = report(branch=None)
ck("K-0 to'landi, jami faqat 240 000",
   (grow(ra, TKH, G_K0)["status"], grow(ra, TKH, G_K1)["status"],
    tp_sum(TKH)), ("paid", "unpaid", 240_000.0))
r = xarajat_oylik(360_000, teacher_id=TKH)
ck("qolgani Xarajatlardan — ustoz to'liq to'langan",
   (trow(report(branch=None), TKH)["status"], tp_sum(TKH)),
   ("paid", 600_000.0))

# 9c. "Administrator + ustoz": alohida xodim qatori, fiks oyligi xarajat
rows = client.get(f"/api/expenses/staff?branch_id={B2}",
                  headers=H).json()["rows"]
ck("Nodir: xodim qatori va ustoz kartasi alohida",
   sorted((x["key"], x["to_salary_card"]) for x in rows
          if x["name"] == "Nodir Rahbar"),
   sorted([(f"t{TNR}", True), (f"u{UNR}", False)]))
P10 = pnl(10)[0]
r = xarajat_oylik(2_000_000, staff_user_id=UNR, period=OCT)
ck("Nodir oyligi — ma'muriy xarajat, foyda-zararda",
   (r.json()["category"], round(pnl(10)[0] - P10, 2)),
   ("admin_salary", 2_000_000.0))
s = SessionLocal()
ck("Nodir kartasi akkauntga bog'lanmadi",
   s.query(models.Teacher).get(TNR).user_id, None)
s.close()

# 9d. Nofaol karta — pul unga jim ketmaydi
r = xarajat_oylik(1_000_000, staff_user_id=UIC, period=OCT)
s = SessionLocal()
ck("nofaol karta tanlanmadi, bog'lanmadi",
   (r.json()["category"], s.query(models.Teacher).get(TIC).user_id),
   ("admin_salary", None))
s.close()

# 9e. "Administrator + Examiner" — fiks oyligi examinerlik puli emas
r = xarajat_oylik(2_000_000, staff_user_id=UAE)
ck("Dilnoza fiks oyligi xarajat", r.json()["category"], "admin_salary")
s = SessionLocal()
ck("examiner ro'yxatida berilgan 0", entry._staff_paid(s, UAE, SEP), 0.0)
s.close()
hist = client.get(f"/api/staff-salary?user_id={UAE}&period={SEP}",
                  headers=H).json()
ck("examiner tarixida ham yo'q", (hist["rows"], hist["total"]), ([], 0.0))

# 9f. Examiner boshlig'i boshqalarning Xarajatlardagi oyligini ko'rmaydi
HX = tok("hex")
hx = client.get(f"/api/staff-salary?user_id={UEX}&period={SEP}",
                headers=HX).json()
ck("examiner boshlig'i: faqat oylik oynasidagi yozuv",
   ([x["source"] for x in hx["rows"]], hx["total"]), (["staff"], 50_000.0))
hx = client.get(f"/api/staff-salary?user_id={US}&period={SEP}",
                headers=HX).json()
ck("examiner boshlig'i: ustoz kartasi ko'rinmaydi",
   (hx["rows"], hx["total"]), ([], 0.0))

# 9g. Bir martalik tuzatish: rahbar (karta bog'langan) va filialsiz xarajat
db = SessionLocal()
u_bh = mk_user("rahbar", "Bek Rahbar", roles.ADMINISTRATOR)
u_bf = mk_user("bobur", "Bobur Filialsiz", roles.TEACHER, branch=None)
t_bh = models.Teacher(full_name="Bek Rahbar", is_active=1, branch_id=B2,
                      grade="middle", user_id=u_bh.id)
t_bf = models.Teacher(full_name="Bobur Filialsiz", is_active=1,
                      branch_id=None, grade="middle")
db.add_all([t_bh, t_bf]); db.commit()
TBH, TBF = t_bh.id, t_bf.id
group("BH-1", t_bh, 3)                         # 360 000
group("BF-1", t_bf, 2)                         # 240 000 (Bekobod 2)
x1 = models.Expense(date=date(2026, 10, 6), category="admin_salary",
                    amount=300_000, branch_id=B2, method="cash",
                    staff_user_id=u_bh.id, period=SEP, created_by="Admin")
x2 = models.Expense(date=date(2026, 9, 25), category="admin_salary",
                    amount=240_000, branch_id=None, method="cash",
                    staff_user_id=u_bf.id, period=SEP, created_by="Admin")
db.add_all([x1, x2]); db.commit()
X1, X2 = x1.id, x2.id
db.close()
s = SessionLocal()
res = finance._teacher_salary_expense_sync(s)
s.close()
ck("rahbar xarajati tegilmadi (asosiy lavozimi ustoz emas)",
   [(x["expense_id"], x["reason"]) for x in res["skipped"]
    if x["expense_id"] == X1], [(X1, "asosiy lavozimi ustoz emas")])
ck("filialsiz xarajat ko'chdi — dars o'tgan filialga",
   [(x["expense_id"], x["branch_id"]) for x in res["moved"]], [(X2, B2)])
ck("Bobur endi to'langan", trow(report(), TBF)["status"], "paid")

print()
if fails:
    print(f"XATOLAR ({len(fails)}): " + ", ".join(fails))
    sys.exit(1)
print("HAMMASI O'TDI")
