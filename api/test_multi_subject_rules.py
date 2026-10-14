"""IKKI FAN — egasining ikki qo'shimcha qoidasi (2026-10-14).

R3. Jahongir: "O'quvchi oilaviy 10% chegirma bo'lsa 2 fan chegirmasi
    ishlamaydi" — oilaviy bo'lsa 2-fan 10% = 0; ustma-ust yozilgan joriy
    oy qatorlari bir marta to'g'rilanadi (idempotent, audit bilan).
R4. Jahongir: "O'quvchiga kirib yangi guruh qo'shilsa pul yechmay faol
    bo'lib qolyabdi. Avval qo'shilganda sinovda bo'lishi kerak keyin
    faollashtirilsa pul yechsin" + "Sinovdan faolga o'tganda pul
    yechilishi dars sonidan kelib chiqsin".
"""
import os
import sys
import tempfile
from datetime import date, timedelta

_DIR = os.path.join(tempfile.gettempdir(), "multi_subject_rules_test")
os.makedirs(_DIR, exist_ok=True)
_DB = os.path.join(_DIR, "db.sqlite")
os.environ["DATABASE_URL"] = "sqlite:///" + _DB.replace(chr(92), "/")
if os.path.exists(_DB):
    os.remove(_DB)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient          # noqa: E402
import main, models, roles                         # noqa: E402
import entry as E                                  # noqa: E402
import multi_subject as MS                         # noqa: E402
import common as C                                 # noqa: E402
import groups_lessons as GL                        # noqa: E402
from database import SessionLocal                  # noqa: E402
from auth import hash_password                     # noqa: E402

c = TestClient(main.app)
fails = []


def ck(n, g, w):
    ok = g == w
    print(("OK  " if ok else "XATO ") + n + f": {g}"
          + ("" if ok else f" (kutilgan {w})"))
    if not ok:
        fails.append(n)


TODAY = roles.local_today()
PER = f"{TODAY.year:04d}-{TODAY.month:02d}"
M0 = TODAY.replace(day=1)

db = SessionLocal()
b = models.Branch(name="Bekobod 2"); db.add(b); db.commit(); BID = b.id
db.add(models.User(username="asos", full_name="Asoschi", role=roles.FOUNDER,
                   password_hash=hash_password("x"), is_active=1))
t = models.Teacher(full_name="Elena", branch_id=b.id, is_active=1,
                   grade="senior", hired_date=date(2025, 1, 1))
db.add(t); db.commit()


def mk_group(name):
    g = models.Group(name=name, teacher_id=t.id, branch_id=b.id,
                     subject="english", lesson_days="tue,thu,sat",
                     lesson_time="16:00", monthly_fee=540000,
                     lesson_price=45000, standard_lessons_per_month=12,
                     start_date=date(2026, 8, 1))
    db.add(g); db.commit()
    # joriy va o'tgan oy darslari (avtomuzlatish oynasi uchun)
    pm = (M0 - timedelta(days=1))
    for y, m in ((pm.year, pm.month), (TODAY.year, TODAY.month)):
        s, e = main.billing.month_bounds(y, m)
        main._sync_scheduled_lessons(db, g, s, e)
    db.commit()
    return g.id


G1, G2, G3 = mk_group("Rus tili"), mk_group("LOUISIANA 2"), mk_group("Nemis")


def mk_student(name, parent_id=None, groups=(G1,), mc=540000.0):
    s = models.Student(full_name=name, branch_id=BID, group_id=groups[0],
                       status="active", enrolled_date=date(2026, 9, 1),
                       parent_id=parent_id)
    db.add(s); db.commit()
    for gid in groups:
        C.attach_group(db, s, gid, None, joined=date(2026, 9, 1))
    if mc:
        db.add(models.Payment(
            student_id=s.id, amount=-mc, kind="charge", period=PER,
            created_by=E._MC_BY,
            note=f"Rus tili - {PER} oyi uchun 12 dars (avtomat)"))
    db.commit()
    return s.id


def rows(sid):
    d = SessionLocal()
    r = {p.period: round(abs(p.amount)) for p in d.query(models.Payment)
         .filter(models.Payment.student_id == sid,
                 models.Payment.kind == "charge").all()}
    d.close()
    return r


def pct(sid):
    d = SessionLocal()
    v = C._student_discount_percent(d, d.query(models.Student).get(sid))
    d.close()
    return v


def link(sid, gid):
    d = SessionLocal()
    ln = (d.query(models.StudentGroupLink)
          .filter(models.StudentGroupLink.student_id == sid,
                  models.StudentGroupLink.group_id == gid).first())
    out = None if ln is None else (ln.active, ln.status, ln.activated_on)
    d.close()
    return out


def billable(gid, since):
    d = SessionLocal()
    s, e = main.billing.month_bounds(since.year, since.month)
    n = E._billable_lessons(d, d.query(models.Group).get(gid), since, s, e)
    d.close()
    return n


H = {"Authorization": "Bearer " + c.post(
    "/api/auth/login", json={"username": "asos", "password": "x"}
).json()["access_token"]}

# ------------------------------------------------------------------ R3
print("=== R3: oilaviy bo'lsa 2-fan 10% yo'q ===")
par = models.Parent(full_name="Oila oilasi", branch_id=BID)
db.add(par); db.commit(); PID = par.id
FAM_A = mk_student("Oila Akbar", PID, groups=(G1, G3), mc=486000)
FAM_B = mk_student("Oila Barno", PID, groups=(G1,), mc=486000)
ck("oilaviy + 2 fan = faqat 10%", pct(FAM_A), 10.0)
d = SessionLocal()
ck("2-fan foizi 0", C._multi_subject_percent(
    d, d.query(models.Student).get(FAM_A)), 0.0)
d.close()
d = SessionLocal(); MS.daily(d, TODAY); d.commit(); d.close()
n3 = billable(G3, M0)
ck("oilaviy 2-fan qatori 10% bilan (20% emas)",
   rows(FAM_A).get(MS.key(PER, G3)), round(n3 * 45000 * 0.9))
ck("oilaviy asosiy qator o'zgarmadi", rows(FAM_A).get(PER), 486000)

print("=== R3: ustma-ust yozilgan qator bir marta tuzatiladi ===")
FAM_C = mk_student("Oila Cholpon", PID, groups=(G1,), mc=486000)


def _old_multi(db_, s, plus=0, fam=None):
    """91069473 dagi eski qoida: oilaviyga qaramay 10%."""
    n = (db_.query(models.StudentGroupLink)
         .filter(models.StudentGroupLink.student_id == s.id,
                 models.StudentGroupLink.active == 1).count())
    return C.MULTI_SUBJECT_PERCENT if n >= 2 else 0.0


JOIN = max(M0, TODAY - timedelta(days=7))
_new_multi = C._multi_subject_percent
C._multi_subject_percent = _old_multi
try:
    d = SessionLocal()
    s = d.query(models.Student).get(FAM_C)
    C.attach_group(d, s, G2, None, joined=JOIN)
    d.flush()
    MS.on_group_added(d, s, d.query(models.Group).get(G2), JOIN)
    d.commit(); d.close()
finally:
    C._multi_subject_percent = _new_multi
n2 = billable(G2, JOIN)
R = rows(FAM_C)
ck("(oldin) asosiy 20% ga tushgan", R.get(PER), 432000)
ck("(oldin) 2-fan qatori 20% bilan", R.get(MS.key(PER, G2)),
   round(n2 * 45000 * 0.8))
X_BEFORE = rows(FAM_A)
d = SessionLocal()
fx = MS.fix_family_stack(d, TODAY); d.commit(); d.close()
R = rows(FAM_C)
ck("tuzatildi: asosiy 486 000", R.get(PER), 486000)
ck("tuzatildi: 2-fan 10% bilan", R.get(MS.key(PER, G2)),
   round(n2 * 45000 * 0.9))
ck("tuzatilgan qatorlar soni", len(fx), 2)
ck("to'g'ri qatorlarga tegilmadi", rows(FAM_A), X_BEFORE)
ck("yakka farzand qatoriga tegilmadi", rows(FAM_B).get(PER), 486000)
d = SessionLocal()
au = (d.query(models.AuditLog)
      .filter(models.AuditLog.action == "ms2_family_fix").all())
ck("umumiy audit yozuvi", len(au), 1)
ck("auditda o'quvchi va summa",
   bool(au and "Oila Cholpon" in (au[0].note or "")
        and "432000 -> 486000" in (au[0].note or "")), True)
d.close()
d = SessionLocal()
fx2 = MS.fix_family_stack(d, TODAY); d.commit(); d.close()
ck("qayta yurgizilsa hech narsa o'zgarmaydi", (len(fx2), rows(FAM_C)),
   (0, R))
d = SessionLocal(); MS.daily(d, TODAY); d.commit(); d.close()
ck("kunlik jarayondan keyin ham to'g'ri", rows(FAM_C), R)

# ------------------------------------------------------------------ R4
print("=== R4: guruh qo'shildi — sinovda, pul yo'q, 10% yo'q ===")
TR = mk_student("Sinov Toxir")
r = c.post(f"/api/students/{TR}/groups", headers=H,
           json={"group_id": G2, "joined_date": JOIN.isoformat()})
ck("qo'shish 200", r.status_code, 200)
ck("javob: sinov", r.json().get("link_status"), "trial")
ck("javob: pul yo'q", r.json().get("charge"), None)
ck("bog'lanish sinovda", (link(TR, G2) or (None, None))[1], "trial")
ck("2-fan qatori yo'q", MS.key(PER, G2) in rows(TR), False)
ck("asosiy 10% olmadi", rows(TR).get(PER), 540000)
ck("chegirma 0%", pct(TR), 0.0)
d = SessionLocal(); MS.daily(d, TODAY); d.commit(); d.close()
ck("kunlik ham sinovni hisoblamaydi", rows(TR), {PER: 540000})
g = c.get(f"/api/students/{TR}/groups", headers=H).json()
st = {x["group_id"]: (x.get("link_status"), x.get("status_label"))
      for x in g["rows"] if x["active"]}
ck("GET: sinovdagi guruh", st.get(G2), ("trial", "Sinov"))
ck("GET: asosiy guruh faol", st.get(G1), ("active", "Faol"))

print("=== R4: asosiy guruhni olib tashlab sinovni pulsiz qoldirib bo'lmaydi ===")
r = c.delete(f"/api/students/{TR}/groups/{G1}", headers=H)
ck("asosiyni olish 400", r.status_code, 400)

print("=== R4: Faollashtirish — oldindan ko'rish va pul ===")
r = c.get(f"/api/students/{TR}/groups/{G2}/activate-preview"
          f"?on={(TODAY + timedelta(days=1)).isoformat()}", headers=H)
ck("kelajak sana — xato ko'rsatiladi", bool(r.json().get("error")), True)
r = c.post(f"/api/students/{TR}/groups/{G2}/activate", headers=H,
           json={"on": (TODAY + timedelta(days=1)).isoformat()})
ck("kelajak sana 400", r.status_code, 400)
if JOIN > M0:
    r = c.post(f"/api/students/{TR}/groups/{G2}/activate", headers=H,
               json={"on": (JOIN - timedelta(days=1)).isoformat()})
    ck("qo'shilgandan oldingi sana 400", r.status_code, 400)
ON = JOIN
pv = c.get(f"/api/students/{TR}/groups/{G2}/activate-preview"
           f"?on={ON.isoformat()}", headers=H)
ck("preview 200", pv.status_code, 200)
pv = pv.json()
nON = billable(G2, ON)
ck("preview: darslar", pv.get("lessons"), nON)
ck("preview: chegirma 10%", pv.get("discount"), 10.0)
ck("preview: summa", round(pv.get("amount") or 0), round(nON * 45000 * 0.9))
ck("preview hech narsa yozmadi", rows(TR), {PER: 540000})
r = c.post(f"/api/students/{TR}/groups/{G2}/activate", headers=H,
           json={"on": ON.isoformat()})
ck("faollashtirish 200", r.status_code, 200)
R = rows(TR)
ck("2-fan qatori = preview", R.get(MS.key(PER, G2)), round(pv["amount"]))
ck("asosiy guruhga 10%", R.get(PER), 486000)
ck("bog'lanish faol, sana bilan", link(TR, G2), (1, "active", ON))
ck("chegirma endi 10%", pct(TR), 10.0)
r = c.post(f"/api/students/{TR}/groups/{G2}/activate", headers=H,
           json={"on": ON.isoformat()})
ck("qayta faollashtirish 400", r.status_code, 400)
d = SessionLocal(); MS.daily(d, TODAY); d.commit(); d.close()
ck("kunlik takrorlamaydi", rows(TR), R)
g = c.get(f"/api/students/{TR}/groups", headers=H).json()
st = {x["group_id"]: x.get("status_label") for x in g["rows"] if x["active"]}
ck("GET: endi faol", st.get(G2), "Faol")

print("=== R4: shu guruhda 3 ta darsga kelsa — avtomat faol ===")
AU = mk_student("Avto Umid")
r = c.post(f"/api/students/{AU}/groups", headers=H,
           json={"group_id": G3, "joined_date": M0.isoformat()})
ck("qo'shildi (sinov)", r.json().get("link_status"), "trial")
d = SessionLocal()
past = (d.query(models.Lesson)
        .filter(models.Lesson.group_id == G3, models.Lesson.date >= M0,
                models.Lesson.date <= TODAY)
        .order_by(models.Lesson.date).all())
past = [(L.id, L.date) for L in past]
d.close()
if len(past) >= 3:
    # Boshqa guruhdagi (asosiy) kelishlar sanalmaydi
    d = SessionLocal()
    l1 = (d.query(models.Lesson)
          .filter(models.Lesson.group_id == G1, models.Lesson.date >= M0,
                  models.Lesson.date <= TODAY).first())
    if l1 is not None:
        d.add(models.Attendance(lesson_id=l1.id, student_id=AU, present=1))
        d.commit()
    d.close()
    for i, (lid, _d) in enumerate(past[:3]):
        r = c.put(f"/api/lessons/{lid}/attendance", headers=H,
                  json={"marks": [{"student_id": AU, "present": True}]})
        ck(f"yo'qlama {i + 1} 200", r.status_code, 200)
        if i < 2:
            ck(f"{i + 1}-darsdan keyin hali sinov",
               (link(AU, G3) or (0, None))[1], "trial")
    ck("3-darsda javobda faollashdi",
       any(a.get("group_id") == G3 for a in r.json().get("activated", [])),
       True)
    on = max(past[0][1], M0)
    ck("bog'lanish faol (birinchi kelgan kundan)", link(AU, G3),
       (1, "active", on))
    ck("pul darslar soni bo'yicha", rows(AU).get(MS.key(PER, G3)),
       round(billable(G3, on) * 45000 * 0.9))
    ck("asosiy guruhga 10%", rows(AU).get(PER), 486000)
else:
    print("  (oy boshida 3 ta o'tgan dars yo'q — endpoint yo'li o'tkazildi)")

print("=== R4: kunlik jarayon ham 3 ta kelishni ushlaydi ===")
AD = mk_student("Avto Dilnoza")
r = c.post(f"/api/students/{AD}/groups", headers=H,
           json={"group_id": G3, "joined_date": M0.isoformat()})
d = SessionLocal()
ls = (d.query(models.Lesson)
      .filter(models.Lesson.group_id == G3, models.Lesson.date >= M0)
      .order_by(models.Lesson.date).limit(3).all())
for L in ls:
    d.add(models.Attendance(lesson_id=L.id, student_id=AD, present=2))
first = ls[0].date
d.commit()
out = MS.daily(d, TODAY); d.commit(); d.close()
ck("kunlik: faollashdi", out.get("activated", 0) >= 1, True)
on = min(max(first, M0), TODAY)
ck("kunlik: bog'lanish faol", (link(AD, G3) or (0, None, None))[:2],
   (1, "active"))
ck("kunlik: pul yechildi", rows(AD).get(MS.key(PER, G3)),
   round(billable(G3, on) * 45000 * 0.9))

print("=== Sinovdagi guruh sababli FAOL o'quvchi arxivlanmaydi ===")
SF = mk_student("Sinov Farrux")
r = c.post(f"/api/students/{SF}/groups", headers=H,
           json={"group_id": G2, "joined_date": (TODAY - timedelta(
               days=20)).isoformat()})
d = SessionLocal()
ls = (d.query(models.Lesson)
      .filter(models.Lesson.group_id == G2,
              models.Lesson.date >= TODAY - timedelta(days=14),
              models.Lesson.date < TODAY)
      .order_by(models.Lesson.date.desc()).limit(3).all())
ids = [L.id for L in ls]
d.close()
if len(ids) >= 2:
    # 2 ta "kelmadi" — o'quvchi sinovidagi qoida faol o'quvchiga tegmaydi
    for lid in ids[:2]:
        c.put(f"/api/lessons/{lid}/attendance", headers=H,
              json={"marks": [{"student_id": SF, "present": False}]})
    d = SessionLocal()
    s = d.query(models.Student).get(SF)
    ck("2 ta kelmadi: holat faol", s.status, "active")
    ck("2 ta kelmadi: bog'lanish ochiq", (link(SF, G2) or (0,))[0], 1)
    ck("2 ta kelmadi: yo'qlama joyida",
       d.query(models.Attendance).filter(
           models.Attendance.student_id == SF).count(), 2)
    d.close()
if len(ids) >= 3:
    c.put(f"/api/lessons/{ids[2]}/attendance", headers=H,
          json={"marks": [{"student_id": SF, "present": False}]})
    d = SessionLocal()
    fz = GL.run_auto_freeze(d, TODAY)
    s = d.query(models.Student).get(SF)
    ck("avtomuzlatish sinov guruhi uchun muzlatmadi", (SF in fz, s.status),
       (False, "active"))
    ck("avtomuzlatish yo'qlamani arxivlamadi",
       d.query(models.Attendance).filter(
           models.Attendance.student_id == SF).count(), 3)
    d.close()

print("=== Bitta guruhli va mavjud faol 2-guruhlilar o'zgarmaydi ===")
ONE = mk_student("Yakka Olim")
d = SessionLocal(); MS.daily(d, TODAY); d.commit(); d.close()
ck("bitta guruh: qator o'zgarmadi", rows(ONE), {PER: 540000})
ck("bitta guruh: chegirma 0", pct(ONE), 0.0)
d = SessionLocal()
nogrp = models.Student(full_name="Guruhsiz Nodir", branch_id=BID,
                       status="active", enrolled_date=date(2026, 9, 1))
d.add(nogrp); d.commit(); NG = nogrp.id; d.close()
r = c.post(f"/api/students/{NG}/groups", headers=H,
           json={"group_id": G1, "joined_date": JOIN.isoformat()})
ck("guruhsizning birinchi guruhi faol", r.json().get("link_status"),
   "active")
ck("guruhsizning birinchi guruhi avvalgidek yechildi",
   bool(r.json().get("charge")), True)
OLD2 = mk_student("Eski Ikki", groups=(G1, G3))
ck("mavjud 2-guruh bog'lanishi faol", (link(OLD2, G3) or (0, None))[1],
   "active")
d = SessionLocal(); MS.daily(d, TODAY); d.commit(); d.close()
ck("mavjud 2-guruh: to'liq oy 10% bilan", rows(OLD2).get(MS.key(PER, G3)),
   486000)
ck("mavjud 2-guruh: asosiy 10%", rows(OLD2).get(PER), 486000)
# Eski yozuv (status bo'sh) ham faol sanaladi — migratsiyadan oldingi qator
d = SessionLocal()
d.query(models.StudentGroupLink).filter(
    models.StudentGroupLink.student_id == OLD2).update(
    {models.StudentGroupLink.status: None})
d.commit(); d.close()
ck("bo'sh status = faol (10%)", pct(OLD2), 10.0)

print("=== Sinovdagi guruhga ko'chirilsa — u asosiy va faol ===")
MV = mk_student("Kochish Malika")
c.post(f"/api/students/{MV}/groups", headers=H,
       json={"group_id": G2, "joined_date": JOIN.isoformat()})
r = c.post(f"/api/students/{MV}/move-group", headers=H,
           json={"group_id": G2})
ck("ko'chirish 200", r.status_code, 200)
ck("ko'chirilgan guruh faol", (link(MV, G2) or (0, None))[1], "active")

print("=== Faol bo'lmagan o'quvchining sinovdagi guruhi faollashmaydi ===")
# 2026-10-14 ko'rigi: muzlatilgan / o'zi sinovdagi o'quvchida
# faollashtirish pul yechmay activated_on yozardi, keyin kunlik jarayon
# "#g" ni shu sanadan (muzlagan kunlar bilan) yechardi.
for nm, stt in (("Muzlagan Zafar", "frozen"), ("Sinovdagi Sevara", "trial")):
    NA = mk_student(nm)
    c.post(f"/api/students/{NA}/groups", headers=H,
           json={"group_id": G2, "joined_date": M0.isoformat()})
    d = SessionLocal()
    s = d.query(models.Student).get(NA)
    s.status = stt
    if stt == "frozen":
        s.frozen_until = TODAY + timedelta(days=10)
    d.commit(); d.close()
    pv = c.get(f"/api/students/{NA}/groups/{G2}/activate-preview"
               f"?on={M0.isoformat()}", headers=H).json()
    ck(f"{stt}: preview xato", pv.get("error"), MS.NOT_ACTIVE_MSG)
    r = c.post(f"/api/students/{NA}/groups/{G2}/activate", headers=H,
               json={"on": M0.isoformat()})
    ck(f"{stt}: faollashtirish 400", r.status_code, 400)
    ck(f"{stt}: bog'lanish sinovda, sanasiz", link(NA, G2), (1, "trial", None))
    d = SessionLocal()
    s = d.query(models.Student).get(NA)
    s.status = "active"
    s.frozen_until = None
    d.commit()
    MS.daily(d, TODAY); d.commit(); d.close()
    ck(f"{stt}: faollashgach ham kunlik #g yozmaydi",
       MS.key(PER, G2) in rows(NA), False)
r = c.post(f"/api/students/{NA}/groups/{G2}/activate", headers=H,
           json={"on": TODAY.isoformat()})
ck("o'quvchi faol bo'lgach guruh faollashadi", r.status_code, 200)
ck("pul faollashgan kundan", rows(NA).get(MS.key(PER, G2), 0),
   round(billable(G2, TODAY) * 45000 * 0.9))

print("=== Shu oyda chiqib qayta qo'shilgan guruh: preview = yechilgan ===")
RA = mk_student("Qayta Rano", groups=(G1, G3))
d = SessionLocal(); MS.daily(d, TODAY); d.commit(); d.close()
ck("qayta: boshida #g3 to'liq oy", rows(RA).get(MS.key(PER, G3)), 486000)
r = c.delete(f"/api/students/{RA}/groups/{G3}", headers=H)
ck("qayta: chiqarish 200", r.status_code, 200)
CUT1 = rows(RA).get(MS.key(PER, G3))
r = c.post(f"/api/students/{RA}/groups", headers=H,
           json={"group_id": G3, "joined_date": TODAY.isoformat()})
ck("qayta: qo'shildi (sinov)", r.json().get("link_status"), "trial")
pv = c.get(f"/api/students/{RA}/groups/{G3}/activate-preview"
           f"?on={TODAY.isoformat()}", headers=H).json()
ck("qayta: preview avvalgi qatorni ko'rsatadi",
   bool(pv.get("existing")), True)
ex_n = (pv.get("existing") or {}).get("lessons", 0)
ck("qayta: preview darslar standartdan oshmaydi",
   pv.get("lessons"), max(0, min(billable(G3, TODAY), 12 - ex_n)))
r = c.post(f"/api/students/{RA}/groups/{G3}/activate", headers=H,
           json={"on": TODAY.isoformat()})
ck("qayta: faollashtirish 200", r.status_code, 200)
got = (r.json().get("charge") or {}).get("amount", 0)
ck("qayta: yechilgan = preview", round(got), round(pv.get("amount") or 0))
ck("qayta: qator preview qadar oshdi", rows(RA).get(MS.key(PER, G3)),
   round(CUT1 + (pv.get("amount") or 0)))
R_RA = rows(RA)
d = SessionLocal(); MS.daily(d, TODAY); d.commit(); d.close()
ck("qayta: kunlik takrorlamaydi", rows(RA), R_RA)
r = c.delete(f"/api/students/{RA}/groups/{G3}", headers=H)
ck("qayta: ikkinchi chiqishda oldingi darslar saqlandi",
   rows(RA).get(MS.key(PER, G3), 0) >= CUT1, True)

print("=== Faol 2-guruhga ko'chirish: yangi guruh ikki marta yechilmaydi ===")
MA = mk_student("Kochish Aziz", groups=(G1, G2))
d = SessionLocal(); MS.daily(d, TODAY); d.commit(); d.close()
ck("ko'chishdan oldin", rows(MA), {PER: 486000, MS.key(PER, G2): 486000})
r = c.post(f"/api/students/{MA}/move-group", headers=H,
           json={"group_id": G2})
ck("ko'chirish 200", r.status_code, 200)
R = rows(MA)
ck("#g2 qatori asosiyga aylandi", (MS.key(PER, G2) in R, R.get(PER)),
   (False, 486000))
ck("eski guruh qatori ko'chgan kungacha (oshmaydi)",
   R.get(MS.key(PER, G1), 0) <= 486000, True)
ck("jami: yangi guruh bir marta",
   sum(R.values()) == R.get(PER, 0) + R.get(MS.key(PER, G1), 0), True)
d = SessionLocal(); MS.daily(d, TODAY); d.commit(); d.close()
ck("ko'chirishdan keyin kunlik o'zgartirmaydi", rows(MA), R)

print("=== Migratsiya ro'yxatida ===")
import migrations as MG                             # noqa: E402
ck("0029 migratsiya", any(v == "0029_student_group_trial"
                          for v, _s in MG.MIGRATIONS), True)

print()
print("XATOLAR:", fails if fails else "yo'q")
sys.exit(1 if fails else 0)
