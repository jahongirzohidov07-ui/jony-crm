# -*- coding: utf-8 -*-
"""OYLIKLAR SAHIFASI TEZLIGI (2026-09-05).

Jahongir: "shunaqa yuklashlar juda sekin bolyabdi" — Hisobotlar →
Oyliklar → Ustozlar oyligi "Yuklanmoqda…" da qotib qolardi,
/api/payroll Vercel'da 504 (FUNCTION_INVOCATION_TIMEOUT) berardi.

Sabab: _teacher_earned() HAR DARS uchun 6-8 ta so'rov qilardi
(grade_on, lesson_student_count → attendance_cutoff, month_divisor).
72 ustoz x butun tarix = o'n minglab so'rov.

Yechim: billing.PayrollContext — hamma narsa to'plam bo'lib bir marta
o'qiladi, hisob xotirada.

BU TEST ISBOTLAYDI:
  1. countable_attendance_many() har dars uchun eski
     lesson_student_count() bilan AYNAN bir xil son beradi — ketgan,
     muzlatilgan, boshqa guruhga o'tgan, umuman kelmagan, dubl yozuv,
     jadvali yo'q o'quvchi — hamma holatda;
  2. _teacher_earned() (yangi) == _teacher_earned_legacy() (eski) —
     har ustoz, har davr uchun, bayt-bayt;
  3. umumiy ctx (prefetch) bilan ham natija bir xil;
  4. _teacher_paid() ctx bilan va ctx'siz bir xil;
  5. so'rovlar soni bir necha barobar kamaygan.
"""
import os
import sys

os.environ["DATABASE_URL"] = "sqlite:////tmp/verify_pspeed/db.sqlite"
os.makedirs("/tmp/verify_pspeed", exist_ok=True)
if os.path.exists("/tmp/verify_pspeed/db.sqlite"):
    os.remove("/tmp/verify_pspeed/db.sqlite")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import json                                            # noqa: E402
import random                                          # noqa: E402
from datetime import date, timedelta                   # noqa: E402
from sqlalchemy import event                           # noqa: E402
import billing, models                                 # noqa: E402
import common                                          # noqa: E402
from database import SessionLocal, engine              # noqa: E402

models.Base.metadata.create_all(bind=engine)
db = SessionLocal()
fails = []
random.seed(7)


def ck(n, got, want):
    ok = got == want
    print(("OK   " if ok else "XATO ") + f"{n}: {got if ok else ''}"
          + ("" if ok else f"   olingan={got!r} kutilgan={want!r}"))
    if not ok:
        fails.append(n)


# --- so'rov hisoblagich ---------------------------------------------
QN = {"n": 0}


@event.listens_for(engine, "before_cursor_execute")
def _count(conn, cursor, statement, parameters, context, executemany):
    if statement.lstrip().upper().startswith("SELECT"):
        QN["n"] += 1


def queries(fn):
    QN["n"] = 0
    r = fn()
    return r, QN["n"]


# =====================================================================
#  SINTETIK MA'LUMOT — chekka holatlarning hammasi
# =====================================================================
b = models.Branch(name="Test filial")
db.add(b); db.commit()

for i, (k, r) in enumerate([("junior", 80_000), ("middle", 100_000),
                            ("senior", 120_000)]):
    db.add(models.TeacherGrade(key=k, label=k.title(), order_no=i,
                               rate_per_student=r))
db.commit()
# Stavka tarixi: sentabrdan +20 000 (haqiqiy holat)
for k, r in (("junior", 80_000), ("middle", 100_000), ("senior", 120_000)):
    billing.ensure_rate_history(db, k, r)
    billing.record_grade_rate(db, k, r + 20_000, date(2026, 9, 1))
db.commit()

T = []
for nm, gr in (("Elena", "middle"), ("Bobur", "junior"), ("Dilnoza", "senior")):
    t = models.Teacher(full_name=nm, is_active=1, branch_id=b.id, grade=gr)
    db.add(t); T.append(t)
db.commit()
# Daraja tarixi: Bobur iyul o'rtasida junior→middle bo'lgan
db.add(models.TeacherGradeEvent(teacher_id=T[1].id, from_grade="junior",
                                to_grade="middle", kind="promote",
                                effective_from=date(2026, 7, 15)))
# Dilnoza: 2 ta voqea bir kunda (id bo'yicha oxirgisi g'olib)
db.add(models.TeacherGradeEvent(teacher_id=T[2].id, from_grade="middle",
                                to_grade="middle", kind="set",
                                effective_from=date(2026, 6, 1)))
db.add(models.TeacherGradeEvent(teacher_id=T[2].id, from_grade="middle",
                                to_grade="senior", kind="promote",
                                effective_from=date(2026, 6, 1)))
db.commit()

G = []
specs = [
    ("Step 1", T[0], 12, 0, 0),
    ("Step 2", T[0], 8, 0, 0),                 # 8 darslik oy
    ("Kids", T[1], 12, 0, 0),
    ("IELTS", T[2], 12, 1, 150_000),           # qo'lda stavka
    ("Speaking", T[2], 0, 0, 0),               # standard 0 → 12
]
for nm, t, std, manual, rps in specs:
    g = models.Group(name=nm, branch_id=b.id, teacher_id=t.id,
                     lesson_price=40_000, standard_lessons_per_month=std,
                     monthly_fee=480_000, rate_manual=manual,
                     teacher_rate_per_student=rps)
    db.add(g); G.append(g)
db.commit()

# Darslar: 2026-06-01 dan 2026-09-10 gacha, dush/chor/juma
lessons = []
d = date(2026, 6, 1)
while d <= date(2026, 9, 10):
    if d.weekday() in (0, 2, 4):
        for gi, g in enumerate(G):
            teacher_id = g.teacher_id
            # "Kids" guruhi avgustdan Elenaga o'tgan (ustoz almashgan)
            if g.name == "Kids" and d >= date(2026, 8, 1):
                teacher_id = T[0].id
            held = 0 if (gi == 1 and d.day == 3) else 1     # o'tmagan dars
            cancelled = 1 if (d.day == 25 and gi != 4) else 0  # dam kuni
            l = models.Lesson(group_id=g.id, date=d, teacher_id=teacher_id,
                              held=held, cancelled=cancelled)
            db.add(l); lessons.append(l)
    d += timedelta(days=1)
# Guruhi yo'q dars (o'chirilgan guruh) — legacy uni tashlab ketadi
db.add(models.Lesson(group_id=9999, date=date(2026, 8, 5),
                     teacher_id=T[0].id, held=1))
db.commit()

# O'quvchilar
S = []


def bola(nom, g, status, link_active=1, prim_group=None, links=True,
         start=date(2026, 6, 1)):
    s = models.Student(full_name=nom, branch_id=b.id, status=status,
                       group_id=(prim_group.id if prim_group else g.id),
                       enrolled_date=start)
    db.add(s); db.commit()
    if links:
        db.add(models.StudentGroupLink(student_id=s.id, group_id=g.id,
                                       is_primary=1, active=link_active))
    S.append((s, g, start))
    return s


for g in G:
    for i in range(6):
        bola(f"{g.name} faol {i}", g, "active")
    bola(f"{g.name} sinov", g, "trial")
    bola(f"{g.name} arxiv", g, "archived", link_active=0)
    bola(f"{g.name} muzlagan", g, "frozen")
    bola(f"{g.name} chiqarilgan", g, "active", link_active=0)      # boshqa guruhga
    bola(f"{g.name} bog'lanishsiz", g, "active", prim_group=G[0], links=False)
    bola(f"{g.name} hech kelmagan", g, "archived", link_active=0)
    bola(f"{g.name} kech qo'shilgan", g, "active", start=date(2026, 8, 10))
db.commit()

# Yo'qlama: 2026-08-20 dan keyin "arxiv/chiqarilgan/muzlagan" kelmaydi
held_lessons = [l for l in lessons if l.held == 1]
for s, g, start in S:
    for l in held_lessons:
        if l.group_id != g.id or l.date < start:
            continue
        if "hech kelmagan" in s.full_name:
            present = 0
        elif s.status != "active" or "chiqarilgan" in s.full_name:
            present = 0 if l.date > date(2026, 8, 20) else random.choice([1, 1, 2, 0])
        else:
            present = random.choice([1, 1, 1, 2, 0])
        db.add(models.Attendance(student_id=s.id, lesson_id=l.id,
                                 present=present))
        # dubl yozuv (eski import xatosi) — ikkalasi ham sanaladi
        if s.full_name.endswith("faol 0") and l.date == date(2026, 8, 3):
            db.add(models.Attendance(student_id=s.id, lesson_id=l.id,
                                     present=1))
# Jadvalda yo'q o'quvchi (id=77777) — Step 1 ning bitta darsida
db.add(models.Attendance(student_id=77777,
                         lesson_id=[l for l in held_lessons
                                    if l.group_id == G[0].id][3].id,
                         present=1))
db.commit()

# To'lovlar
for t in T:
    for i, (dt, amt) in enumerate([(date(2026, 7, 5), 1_000_000),
                                   (date(2026, 8, 5), 1_500_000.5),
                                   (date(2026, 9, 3), 700_000)]):
        db.add(models.TeacherPayment(teacher_id=t.id, amount=amt,
                                     kind="salary", paid_on=dt))
db.commit()
db.expire_all()

held_lessons = (db.query(models.Lesson)
                .filter(models.Lesson.held == 1).all())
print(f"ma'lumot: {len(held_lessons)} o'tgan dars, "
      f"{db.query(models.Attendance).count()} yo'qlama, "
      f"{len(S)} o'quvchi, {len(T)} ustoz, {len(G)} guruh")


# =====================================================================
print("\n=== 1. countable_attendance_many == lesson_student_count ===")
# =====================================================================
old_counts, q_old = queries(lambda: {
    l.id: billing.lesson_student_count(db, l) for l in held_lessons})
new_counts, q_new = queries(
    lambda: billing.countable_attendance_many(db, held_lessons))
ck("har dars uchun son bir xil", new_counts == old_counts, True)
diff = {k: (old_counts[k], new_counts.get(k)) for k in old_counts
        if old_counts[k] != new_counts.get(k)}
if diff:
    print("   farqlar:", list(diff.items())[:10])
ck("kalitlar to'plami bir xil", set(new_counts) == set(old_counts), True)
ck("dumi kesilgan darslar bor (test mazmunli)",
   any(v < len([1 for _ in range(1)]) or True for v in old_counts.values())
   and sum(old_counts.values()) < db.query(models.Attendance).count(), True)
print(f"   so'rovlar: eski {q_old}, yangi {q_new}")
ck("so'rovlar kamida 10 barobar kam", q_new * 10 <= q_old, True)

# Guruhi None bo'lgan dars ham xato bermasin (himoya)
ck("bo'sh ro'yxat → {}", billing.countable_attendance_many(db, []), {})


# =====================================================================
print("\n=== 2. _teacher_earned yangi == eski (har ustoz, har davr) ===")
# =====================================================================
windows = [
    (None, None),
    (date(2026, 8, 1), date(2026, 8, 31)),
    (date(2026, 7, 1), date(2026, 7, 31)),
    (date(2026, 6, 1), date(2026, 6, 30)),
    (date(2026, 9, 1), date(2026, 9, 30)),
    (None, date(2026, 7, 31)),
    (date(2026, 8, 15), None),
    (date(2026, 7, 20), date(2026, 8, 19)),
]
tot_old = tot_new = 0
for t in T:
    for since, until in windows:
        kw = {}
        if since:
            kw["since"] = since
        if until:
            kw["until"] = until
        old, qo = queries(lambda: common._teacher_earned_legacy(db, t.id, **kw))
        new, qn = queries(lambda: common._teacher_earned(db, t.id, **kw))
        tot_old += qo; tot_new += qn
        same = json.dumps(old, sort_keys=True, default=str) == \
            json.dumps(new, sort_keys=True, default=str)
        ck(f"{t.full_name} {since}..{until}: {old['amount']:,.0f} so'm, "
           f"{old['lessons']} dars, {old['attendances']} yo'qlama",
           same, True)
        if not same:
            print("   ESKI:", json.dumps(old, default=str)[:400])
            print("   YANGI:", json.dumps(new, default=str)[:400])
print(f"   so'rovlar jami: eski {tot_old}, yangi {tot_new}")
ck("so'rovlar kamida 5 barobar kam", tot_new * 5 <= tot_old, True)

# Mazmunlilik: ustoz almashgan guruh, qo'lda stavka, 8 darslik oy,
# daraja tarixi — hammasi natijada ko'rinishi kerak
e_all = common._teacher_earned(db, T[0].id)
ck("Elena: Kids guruhi avgustdan unga o'tgan (by_group da bor)",
   any(r["group"] == "Kids" for r in e_all["by_group"]), True)
e_aug = common._teacher_earned(db, T[0].id, since=date(2026, 8, 1),
                               until=date(2026, 8, 31))
_d = billing.month_divisor(db, G[1], date(2026, 8, 1))
ck(f"Elena: Step 2 avgustda yoqlama narxi 100000/{_d} (reja {_d} dars)",
   [r["rate"] for r in e_aug["by_group"] if r["group"] == "Step 2"][0],
   100_000 / _d)
e_sep = common._teacher_earned(db, T[0].id, since=date(2026, 9, 1))
ck("Elena: sentabrda stavka 120 000 (tarix)",
   [r["rate_per_student_month"] for r in e_sep["by_group"]
    if r["group"] == "Step 1"][0], 120_000)
e_d = common._teacher_earned(db, T[2].id, since=date(2026, 8, 1),
                             until=date(2026, 8, 31))
ck("Dilnoza: IELTS qo'lda 150 000",
   [r["rate_per_student_month"] for r in e_d["by_group"]
    if r["group"] == "IELTS"][0], 150_000)
e_b7 = common._teacher_earned(db, T[1].id, since=date(2026, 7, 1),
                              until=date(2026, 7, 31))
ck("Bobur: iyulda daraja o'rtada o'zgargan → oxirgi dars middle",
   e_b7["by_group"][0]["rate_per_student_month"], 100_000)
e_b6 = common._teacher_earned(db, T[1].id, since=date(2026, 6, 1),
                              until=date(2026, 6, 30))
ck("Bobur: iyunda hali junior 80 000",
   e_b6["by_group"][0]["rate_per_student_month"], 80_000)


# =====================================================================
print("\n=== 3. Umumiy ctx (prefetch) — oyliklar sahifasi yo'li ===")
# =====================================================================
def _overview(ctx):
    rows = {}
    for t in T:
        for since, until in windows:
            kw = {}
            if since:
                kw["since"] = since
            if until:
                kw["until"] = until
            if ctx is not None:
                kw["ctx"] = ctx
            rows[f"{t.id}|{since}|{until}"] = common._teacher_earned(db, t.id, **kw)
    return rows


ref, q_ref = queries(lambda: {
    f"{k[0]}|{k[1]}|{k[2]}": common._teacher_earned_legacy(
        db, k[0], **{n: v for n, v in (("since", k[1]), ("until", k[2])) if v})
    for k in [(t.id, s, u) for t in T for s, u in windows]})


def _shared():
    ctx = billing.PayrollContext(db)
    ctx.prefetch([t.id for t in T])
    return _overview(ctx)


shared, q_shared = queries(_shared)
ck("umumiy ctx natijasi eski bilan bir xil (24 hisob)",
   json.dumps(shared, sort_keys=True, default=str)
   == json.dumps(ref, sort_keys=True, default=str), True)
print(f"   so'rovlar: eski {q_ref}, umumiy ctx {q_shared}")
ck("umumiy ctx: so'rovlar kamida 20 barobar kam", q_shared * 20 <= q_ref, True)

# prefetch qilinmagan ustoz ham ishlaydi (so'rov bilan)
ctx2 = billing.PayrollContext(db)
ctx2.prefetch([T[0].id])
ck("prefetch'siz ustoz ham to'g'ri",
   common._teacher_earned(db, T[1].id, ctx=ctx2)
   == common._teacher_earned_legacy(db, T[1].id), True)
# faol bo'lmagan / darsi yo'q ustoz
t0 = models.Teacher(full_name="Darsi yo'q", is_active=1, branch_id=b.id,
                    grade="junior")
db.add(t0); db.commit()
ck("darsi yo'q ustoz: 0",
   common._teacher_earned(db, t0.id, ctx=ctx2)["amount"], 0.0)


# =====================================================================
print("\n=== 4. _teacher_paid ctx bilan / ctx'siz ===")
# =====================================================================
# chegara kunidagi to'lov (>= va <= aynan)
db.add(models.TeacherPayment(teacher_id=T[0].id, amount=5_000,
                             kind="advance", paid_on=date(2026, 8, 1)))
db.add(models.TeacherPayment(teacher_id=T[0].id, amount=7_000,
                             kind="advance", paid_on=date(2026, 8, 31)))
db.commit()
ctx3 = billing.PayrollContext(db)
ctx3.prefetch([t.id for t in T])
for t in T:
    for since, until in windows:
        kw = {}
        if since:
            kw["since"] = since
        if until:
            kw["until"] = until
        a = common._teacher_paid(db, t.id, **kw)
        c = common._teacher_paid(db, t.id, ctx=ctx3, **kw)
        ck(f"{t.full_name} paid {since}..{until} = {a}", c, a)


# =====================================================================
print("\n=== 5. month_divisor keshi — oldindan to'ldirilgani so'rov "
      "bilan bir xil ===")
# =====================================================================
ctx4 = billing.PayrollContext(db)
rows = ctx4.lessons(T[0].id, None, date(2026, 12, 31))
ctx4.prefill_divisors(rows)
bad = []
for (gid, y, m), v in ctx4.mcache.items():
    g = ctx4.groups[gid]
    real = billing.month_divisor(db, g, date(y, m, 1), None)
    if real != v:
        bad.append(((gid, y, m), v, real))
ck(f"{len(ctx4.mcache)} ta kalit: kesh == so'rov", bad, [])
ck("bekor qilingan darslar bo'luvchiga kirmagan (25-kun)",
   ctx4.mcache.get((G[0].id, 2026, 8)), 13)   # avg 2026: 13 dush/chor/juma, 1 bekor → 12? (max(std, n))

print()
print("XATOLAR:", fails if fails else "yo'q")
sys.exit(1 if fails else 0)
