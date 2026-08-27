# -*- coding: utf-8 -*-
"""REFERAL DASTURI — to'liq tekshiruv (2026-08-28).

Jahongirning qoidalari SO'ZMA-SO'Z shu yerda tekshiriladi:

  "bitta olib kelsa shu 10% bo'ladi, 2-do'stiga esa 30% bo'ladi
   QO'SHILMAYDI 10+30=40% bo'lmaydi"
  "faqat 1 oy bepul, TO'LAGANLARGINA hisobga olinadi, 2 oy emas
   SHU OY ichida qilaylik"
  "oilaviy chegirmasi bo'lsa o'sha TO'LAYDIGAN SUMMADAN 10% foiz
   hisoblanib ketaveradi"

Eng muhim qism — PUL. Shuning uchun har bir daraja uchun oxirgi
to'lanadigan summa alohida hisoblanadi va solishtiriladi: foiz
to'g'ri, lekin so'm noto'g'ri bo'lishi ham mumkin.
"""
import os
import sys

os.environ["DATABASE_URL"] = "sqlite:////tmp/verify_ref/db.sqlite"
os.makedirs("/tmp/verify_ref", exist_ok=True)
if os.path.exists("/tmp/verify_ref/db.sqlite"):
    os.remove("/tmp/verify_ref/db.sqlite")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import date, datetime, timedelta                # noqa: E402
from fastapi.testclient import TestClient           # noqa: E402
import main, models, roles, referral                # noqa: E402
import entry                                        # noqa: F401,E402
import common                                       # noqa: E402
from database import SessionLocal                   # noqa: E402
from auth import hash_password                      # noqa: E402

c = TestClient(main.app)
db = SessionLocal()
fails = []
FEE = 500_000.0


def ck(n, got, want):
    ok = got == want
    print(("OK   " if ok else "XATO ") + f"{n}: {got}"
          + ("" if ok else f"   (kutilgan {want})"))
    if not ok:
        fails.append(n)


def money(s, on=None):
    """O'quvchi chegirma tegishli oyda HAQIQATDA qancha to'laydi.

    DIQQAT — sana muhim. Chegirma "shu oyga" emas, o'quvchining
    balansiga qarab beriladi (2026-08-20 qoidasi: qarzli bo'lsa shu
    oyga, to'lab bo'lgan bo'lsa keyingi oyga). Shuning uchun
    o'lchashda ham O'SHA oyning ichidagi kun olinadi — aks holda
    chegirma "hali boshlanmagan" bo'lib ko'rinadi."""
    if on is None:
        d = (db.query(models.Discount)
             .filter(models.Discount.student_id == s.id,
                     models.Discount.kind == "app_referral",
                     models.Discount.status == "active")
             .order_by(models.Discount.id.desc()).first())
        on = d.start_date if d is not None else date.today()
    pct = _percent_on(s, on)
    return round(FEE * (100.0 - pct) / 100.0, 0)


def _percent_on(s, on):
    """common._student_discount_percent, lekin BERILGAN sanada."""
    total = common._family_discount_percent(db, s)
    rows = (db.query(models.Discount)
            .filter(models.Discount.student_id == s.id,
                    models.Discount.status == "active").all())
    for d in rows:
        if d.kind == "family" or not common._discount_alive(d, on):
            continue
        if d.percent:
            total += d.percent
        elif d.amount:
            total += d.amount / FEE * 100
    return min(roles.DISCOUNT_ABSOLUTE_CAP, round(total, 2))


b = models.Branch(name="Zafar")
db.add(b); db.commit()
common.reset_partner_cache()

g = models.Group(name="B1-1", branch_id=b.id, monthly_fee=FEE)
db.add(g); db.commit()

aziz = models.Student(full_name="Aziz Karimov", phone="+998901112233",
                      group_id=g.id, branch_id=b.id, status="active",
                      subject="Ingliz tili", first_name="Aziz")
db.add(aziz); db.commit()

admin = models.User(username="admin1", password_hash=hash_password("jonyjony"),
                    role=roles.ADMINISTRATOR, full_name="Admin",
                    branch_id=b.id, is_active=1)
db.add(admin); db.commit()
H = {"Authorization": "Bearer " + c.post(
    "/api/auth/login",
    json={"username": "admin1", "password": "jonyjony"}
).json()["access_token"]}


# =====================================================================
print("=== 1. HAVOLA KODI ===")
# =====================================================================
code = referral.ensure_code(db, aziz)
ck("kod berildi", bool(code and code.startswith("JONY-")), True)
ck("kod o'zgarmaydi", referral.ensure_code(db, aziz), code)
ck("chalkash belgi yo'q (0/O/1/I)",
   any(ch in code[5:] for ch in "01OI"), False)
codes = {referral.make_code() for _ in range(500)}
ck("500 kod — takror yo'q", len(codes), 500)
ck("kod bo'yicha topiladi", referral.by_code(db, code).id, aziz.id)
ck("kichik harfda ham topiladi", referral.by_code(db, code.lower()).id,
   aziz.id)
ck("prefikssiz ham topiladi", referral.by_code(db, code[5:]).id, aziz.id)
ck("yo'q kod — None", referral.by_code(db, "JONY-ZZZZZ"), None)


# =====================================================================
print("\n=== 2. OCHIQ SAHIFA (do'st ko'radi) ===")
# =====================================================================
r = c.get(f"/api/public/ref/{code}").json()
ck("sahifa ochiladi", r["ok"], True)
ck("taklif qiluvchining ISMI chiqadi", r["inviter"], "Aziz")
ck("familiya CHIQMAYDI", "Karimov" in str(r), False)
ck("telefon CHIQMAYDI", "901112233" in str(r), False)
ck("kursi chiqadi", r["course"], "Ingliz tili")
r0 = c.get("/api/public/ref/JONY-ZZZZZ").json()
ck("noto'g'ri kodda ham sahifa ochiladi", r0["ok"], False)
ck("  lekin ma'lumot bermaydi", r0["inviter"], None)

txt = referral.share_text(aziz, "https://jonyos.uz/r/" + code)
for word in ("Jony Academy", "Jony Student", "Ingliz tili", "BEPUL", code):
    ck(f"tavsiya matnida '{word}'", word in txt, True)


# =====================================================================
print("\n=== 3. DO'ST ARIZA QOLDIRDI -> LID ===")
# =====================================================================
r = c.post(f"/api/public/ref/{code}/lead", json={
    "full_name": "Diyor Sobirov", "phone": "+998901112201",
    "course": "Ingliz tili"}).json()
ck("ariza qabul qilindi", r["ok"], True)
lead = db.query(models.Lead).get(r["lead_id"])
ck("manba 'do'st taklifi'", lead.source, "app_referral")
ck("kim olib kelgani yozildi", lead.referrer_student_id, aziz.id)
ck("filial taklif qiluvchinikidan olindi", lead.branch_id, b.id)
ck("izohda ism bor", "Aziz Karimov" in (lead.note or ""), True)
task = (db.query(models.Task)
        .filter(models.Task.title.like("Do'st taklifi:%")).first())
ck("adminlarga vazifa ochildi", task is not None, True)

r2 = c.post(f"/api/public/ref/{code}/lead", json={
    "full_name": "Diyor Sobirov", "phone": "+998901112201"}).json()
ck("24 soatda takror lid ochilmaydi", r2.get("duplicate"), True)

r3 = c.post(f"/api/public/ref/{code}/lead", json={
    "full_name": "Aziz Karimov", "phone": "+998901112233"})
ck("o'zini o'zi taklif qila olmaydi", r3.status_code, 400)

r4 = c.post(f"/api/public/ref/{code}/lead", json={
    "full_name": "Bot", "phone": "+998901119999", "hp": "spam"}).json()
ck("honeypot: bot yozuvi bazaga tushmaydi",
   db.query(models.Lead).filter(models.Lead.full_name == "Bot").count(), 0)
ck("  lekin botga 'ok' deyiladi", r4["ok"], True)

ck("ismsiz ariza rad etiladi", c.post(
    f"/api/public/ref/{code}/lead",
    json={"full_name": "A", "phone": "+998901112299"}).status_code, 400)
ck("telefonsiz ariza rad etiladi", c.post(
    f"/api/public/ref/{code}/lead",
    json={"full_name": "Ali Valiyev", "phone": "12"}).status_code, 400)


# =====================================================================
print("\n=== 4. LID -> O'QUVCHI: bog'lanish ko'chadi ===")
# =====================================================================
conv = c.post(f"/api/leads/{lead.id}/convert",
              json={"group_id": g.id}, headers=H)
ck("lid o'quvchiga aylandi", conv.status_code, 200)
diyor = db.query(models.Student).get(conv.json()["id"])
ck("o'quvchida 'kim olib keldi' saqlandi",
   diyor.referred_by_student_id, aziz.id)


# =====================================================================
print("\n=== 5. TO'LAMAGUNCHA CHEGIRMA YO'Q ===")
# =====================================================================
st = referral.state(db, aziz)
ck("do'st ro'yxatda bor", st["total_invited"] >= 1, True)
ck("to'lamagan — daraja 0", st["level"], 0)
ck("to'lamagan — foiz 0", st["percent"], 0.0)
ck("kutayotganlar bor", st["waiting"] >= 1, True)
ck("chegirma qatori yaratilmadi",
   db.query(models.Discount).filter(
       models.Discount.kind == "app_referral").count(), 0)


# =====================================================================
print("\n=== 6. PILLAPOYA: 10 / 30 / 50 / 75 / 100 (QO'SHILMAYDI) ===")
# =====================================================================
def add_friend(i):
    """Yangi do'st: havoladan kelib, guruhga qo'shilib, TO'LOV qiladi."""
    s = models.Student(full_name=f"Dost{i} Testov", phone=f"+99890111{i:04d}",
                       group_id=g.id, branch_id=b.id, status="active",
                       referred_by_student_id=aziz.id)
    db.add(s); db.commit()
    db.add(models.Payment(student_id=s.id, amount=FEE, kind="payment",
                          created_at=datetime.now(),
                          period=referral.month_key(), created_by="test"))
    db.commit()
    referral.on_payment(db, s)
    return s


# 1-do'st: Diyor to'lov qildi
db.add(models.Payment(student_id=diyor.id, amount=FEE, kind="payment",
                      created_at=datetime.now(), period=referral.month_key(),
                      created_by="test"))
db.commit()
referral.on_payment(db, diyor)

want = {1: 10.0, 2: 30.0, 3: 50.0, 4: 75.0, 5: 100.0, 6: 100.0}
for n in range(1, 7):
    if n > 1:
        add_friend(n)
    res = referral.recompute(db, aziz)
    rows = (db.query(models.Discount)
            .filter(models.Discount.student_id == aziz.id,
                    models.Discount.kind == "app_referral").all())
    to_pay = money(aziz)
    ck(f"{n} ta do'st -> {want[n]:.0f}%", res["percent"], want[n])
    ck(f"  chegirma qatori BITTA (qo'shilmaydi)", len(rows), 1)
    ck(f"  to'laydigan summa", to_pay,
       round(FEE * (100 - want[n]) / 100, 0))

ck("2 ta do'stda 40% BO'LMADI (10+30)",
   roles.referral_percent(1) + roles.referral_percent(2) == 40.0
   and roles.referral_percent(2) == 30.0, True)
ck("5 ta do'stda BEPUL", money(aziz), 0.0)


# =====================================================================
print("\n=== 7. OILAVIY CHEGIRMA BILAN QO'SHILISHI ===")
# =====================================================================
# Jahongir: "oilaviy chegirmasi bo'lsa o'sha TO'LAYDIGAN SUMMADAN
# 10% foiz hisoblanib ketaveradi". 500 000 -> oilaviy 20% ->
# 400 000 -> referal 10% -> 40 000 -> 360 000 to'laydi (28%, 30% emas).
par = models.Parent(full_name="Ota Ona", phone="+998907770000")
db.add(par); db.commit()
oila = []
for i in range(roles.FAMILY_DISCOUNT_MIN_CHILDREN):
    s = models.Student(full_name=f"Aka{i} Oilaviy", group_id=g.id,
                       branch_id=b.id, status="active", parent_id=par.id,
                       first_name=f"Aka{i}")
    db.add(s); oila.append(s)
db.commit()
uka = oila[0]
ck("oilaviy chegirma bor", common._family_discount_percent(db, uka),
   roles.FAMILY_DISCOUNT_PERCENT)
fam = roles.FAMILY_DISCOUNT_PERCENT
baza = round(FEE * (100 - fam) / 100, 2)
ck("referal bazasi = oiladan keyingi summa",
   referral.payable_base(db, uka), baza)

d1 = models.Student(full_name="Ukaning Dosti", group_id=g.id, branch_id=b.id,
                    status="active", referred_by_student_id=uka.id)
db.add(d1); db.commit()
db.add(models.Payment(student_id=d1.id, amount=FEE, kind="payment",
                      created_at=datetime.now(), period=referral.month_key(),
                      created_by="test"))
db.commit()
res = referral.on_payment(db, d1)   # TO'LAGAN odam beriladi
ck("uka 10% oldi", res["percent"], 10.0)
ck("  chegirma summasi = bazadan 10%", res["amount"], round(baza * 0.10, 0))
ck("  oxirgi to'lov = baza - 10%", money(uka), round(baza * 0.90, 0))
d_uka = (db.query(models.Discount)
         .filter(models.Discount.student_id == uka.id,
                 models.Discount.kind == "app_referral").first())
ck("  jami foiz oilaviy+referal (qo'shib emas, ketma-ket)",
   _percent_on(uka, d_uka.start_date),
   round(100 - 90 * (100 - fam) / 100, 2))


# =====================================================================
print("\n=== 8. FAQAT SHU OY ===")
# =====================================================================
eski = models.Student(full_name="Eski Dost", group_id=g.id, branch_id=b.id,
                      status="active", referred_by_student_id=uka.id)
db.add(eski); db.commit()
o_oy = date.today().replace(day=1) - timedelta(days=15)
db.add(models.Payment(student_id=eski.id, amount=FEE, kind="payment",
                      created_at=datetime.combine(o_oy, datetime.min.time()),
                      period=referral.month_key(o_oy),
                      created_by="test"))
db.commit()
n_now = referral.paid_count(db, uka.id, referral.month_key())
n_old = referral.paid_count(db, uka.id, referral.month_key(o_oy))
ck("o'tgan oydagi do'st SHU OYGA sanalmaydi", n_now, 1)
ck("  o'tgan oyda esa sanaladi", n_old, 1)
ck("daraja hali ham 10% (30% emas)",
   referral.recompute(db, uka)["percent"], 10.0)


# =====================================================================
print("\n=== 9. CHEGIRMA FAQAT 1 OYGA ===")
# =====================================================================
d = (db.query(models.Discount)
     .filter(models.Discount.student_id == uka.id,
             models.Discount.kind == "app_referral").first())
first, last = referral.month_bounds(d.period)
ck("boshlanish — oyning 1-kuni", d.start_date, first)
ck("tugash — oyning oxirgi kuni", d.end_date, last)
ck("bir oydan uzun emas", (d.end_date - d.start_date).days <= 31, True)
ck("keyingi oyda amal qilmaydi",
   common._discount_alive(d, last + timedelta(days=1)), False)


# =====================================================================
print("\n=== 10. QAYTA HISOB: DUBL CHIQMAYDI (idempotent) ===")
# =====================================================================
before = money(aziz)
n_before = db.query(models.Discount).filter(
    models.Discount.kind == "app_referral").count()
for _ in range(10):
    referral.recompute(db, aziz)
    referral.recompute(db, uka)
ck("10 marta qayta hisob — qator soni o'zgarmadi",
   db.query(models.Discount).filter(
       models.Discount.kind == "app_referral").count(), n_before)
ck("  summa ham o'zgarmadi", money(aziz), before)

rr = c.post("/api/referral-program/recompute", headers={
    "Authorization": "Bearer " + c.post(
        "/api/auth/login",
        json={"username": "founder_ref", "password": "jonyjony"}).json()
    .get("access_token", "")})
# asoschi hali yo'q — quyida yaratamiz


# =====================================================================
print("\n=== 11. HOLAT EKRANI (o'quvchi ko'radi) ===")
# =====================================================================
st = referral.state(db, aziz, "https://jonyos.uz")
ck("havola to'liq", st["link"], f"https://jonyos.uz/r/{code}")
ck("daraja 5", st["level"], 5)
ck("foiz 100", st["percent"], 100.0)
ck("pillapoya 5 bosqich", len(st["ladder"]), 5)
ck("qoidalar yozilgan", len(st["rules"]) >= 5, True)
ck("keyingi qadam maslahati bor", bool(st["next_hint"]), True)
ck("do'stlar ro'yxati bor", len(st["friends"]) >= 5, True)
ck("familiya qisqartirilgan",
   all("." in f["name"] or " " not in f["name"] for f in st["friends"]), True)
ck("tarix bor", len(st["history"]) >= 1, True)
st2 = referral.state(db, uka)
ck("2-do'stda maslahat 30% deydi", "30%" in st2["next_hint"], True)


# =====================================================================
print("\n=== 12. XODIM HISOBOTI ===")
# =====================================================================
rep = c.get("/api/referral-program", headers=H).json()
ck("hisobot ochildi", "rows" in rep, True)
ck("taklif qiluvchilar bor", rep["totals"]["inviters"] >= 2, True)
ck("to'lovlar sanaldi", rep["totals"]["paid"] >= 5, True)
ck("shu oyda ishlab topilgan summa", rep["totals"]["earned_sum"] > 0, True)
ck("kelasi oyga tushadigani ham ko'rinadi",
   c.get("/api/referral-program?period=%s" % referral.month_key(
       date.today().replace(day=28) + timedelta(days=7)),
       headers=H).json()["totals"]["discount_sum"] > 0, True)
top = rep["rows"][0]
ck("eng ko'p olib kelgan birinchi", top["name"], "Aziz Karimov")
ck("  darajasi 5", top["level"], 5)


# =====================================================================
print("\n=== 13. XAVFSIZLIK ===")
# =====================================================================
ck("loginsiz hisobot ochilmaydi", c.get("/api/referral-program").status_code
   in (401, 403), True)
ck("loginsiz qayta hisob ishlamaydi",
   c.post("/api/referral-program/recompute").status_code in (401, 403), True)
ck("adminга qayta hisob yopiq",
   c.post("/api/referral-program/recompute", headers=H).status_code, 403)

fo = models.User(username="asoschi_ref",
                 password_hash=hash_password("jonyjony"),
                 role=roles.FOUNDER, full_name="Asoschi", is_active=1)
db.add(fo); db.commit()
HF = {"Authorization": "Bearer " + c.post(
    "/api/auth/login",
    json={"username": "asoschi_ref", "password": "jonyjony"}
).json()["access_token"]}
rr = c.post("/api/referral-program/recompute", headers=HF)
ck("asoschiga ochiq", rr.status_code, 200)
ck("  hech narsa buzilmadi", money(aziz), before)


# =====================================================================
print("\n=== 14. TO'LOV YIQILMAYDI ===")
# =====================================================================
class _Yolgon:
    id = -1
    referred_by_student_id = 999999
res = referral.on_payment(db, _Yolgon())
ck("yo'q o'quvchida ham xato tashlamaydi", res["ok"], False)
res = referral.on_payment(db, models.Student(full_name="x"))
ck("bog'lanmagan o'quvchida ham tinch", res["ok"], False)


# =====================================================================
print("\n=== 15. HECH NARSA O'CHIRILMAYDI ===")
# =====================================================================
n_disc = db.query(models.Discount).count()
n_pay = db.query(models.Payment).count()
n_lead = db.query(models.Lead).count()
d_old = (db.query(models.Discount)
         .filter(models.Discount.kind == "app_referral",
                 models.Discount.student_id == uka.id).first())
d_old.applied_at = None
db.commit()
# do'stlarni "to'lamagan" qilib ko'ramiz: chegirma O'CHMASIN, bekor bo'lsin
for p in db.query(models.Payment).filter(
        models.Payment.student_id.in_(
            [s.id for s in db.query(models.Student).filter(
                models.Student.referred_by_student_id == uka.id).all()])).all():
    p.kind = "charge"
db.commit()
referral.recompute(db, uka)
ck("chegirma qatori O'CHIRILMADI",
   db.query(models.Discount).count(), n_disc)
ck("to'lovlar joyida", db.query(models.Payment).count(), n_pay)
ck("lidlar joyida", db.query(models.Lead).count(), n_lead)
d2 = db.query(models.Discount).get(d_old.id)
ck("  faqat 'bekor qilindi' bo'ldi", d2.status, "cancelled")
ck("  sababi yozilgan", "bekor" in (d2.reason or ""), True)


print("\n" + "=" * 60)
if fails:
    print("YIQILGAN TEKSHIRUVLAR:", len(fails))
    for f in fails:
        print("  -", f)
else:
    print("HAMMASI O'TDI")
sys.exit(1 if fails else 0)
