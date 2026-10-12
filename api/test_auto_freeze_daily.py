"""AVTOMUZLATISH ERTASI KUNI ERTALAB (2026-10-12, Jahongir).

Tekshiriladi:
  1. 3-chi "kelmadi" saqlanganda darhol muzlamaydi; ustoz o'sha kuni
     "keldi"ga to'g'rilasa — ertalab ham muzlamaydi.
  2. Ertalab ham ketma-ket 3 ta "kelmadi" tursa — muzlaydi, yo'qlama
     arxivga, audit sanalar bilan.
  3. Bugungi dars hisobga kirmaydi; bugun "keldi" bo'lsa muzlamaydi.
  4. Oy chegarasi: 30-sentabr darsi, 1-oktabr ertalab muzlatildi —
     SENTABR hisobi qayta hisoblanadi (avvalgi qoida bilan bir xil),
     oktabrga tegilmaydi.
  5. Eski zanjir (oxirgi "kelmadi" 14 kundan oldin) birdaniga
     muzlatilmaydi.
  6. Kuniga bir marta — ikkinchi chaqiruv hech narsa qilmaydi.
"""
import os, sys
from datetime import date, timedelta
os.environ["DATABASE_URL"] = "sqlite:////tmp/af_daily_test.db"
if os.path.exists("/tmp/af_daily_test.db"):
    os.remove("/tmp/af_daily_test.db")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fastapi.testclient import TestClient  # noqa: E402
import main, models, roles, entry, common  # noqa: E402,F401
import groups_lessons as GL  # noqa: E402
from database import SessionLocal  # noqa: E402
from auth import hash_password  # noqa: E402

common._ensure_month_charges = lambda db, **kw: None
c = TestClient(main.app)
fails = []


def ck(n, got, want):
    ok = got == want
    print(("OK  " if ok else "XATO ") + n + f": {got}" + ("" if ok else f" (kutilgan {want})"))
    if not ok:
        fails.append(n)


TODAY = roles.local_today()
db = SessionLocal()
b = models.Branch(name="Zafar"); db.add(b); db.commit()
db.add(models.User(username="asos", password_hash=hash_password("x"),
                   full_name="Asoschi", role=roles.FOUNDER, is_active=1))
t = models.Teacher(full_name="Ustoz", branch_id=b.id, is_active=1)
db.add(t); db.commit()


def group(name):
    g = models.Group(name=name, teacher_id=t.id, branch_id=b.id,
                     lesson_price=40_000, monthly_fee=480_000,
                     standard_lessons_per_month=12)
    db.add(g); db.commit()
    return g


def student(name, g):
    s = models.Student(full_name=name, branch_id=b.id, group_id=g.id,
                       status="active", enrolled_date=date(2026, 8, 1))
    db.add(s); db.commit()
    db.add(models.StudentGroupLink(student_id=s.id, group_id=g.id,
                                   is_primary=1, active=1))
    db.commit()
    return s.id


def lessons(g, days):
    out = []
    for d in days:
        ls = models.Lesson(group_id=g.id, teacher_id=t.id, date=d, held=1)
        db.add(ls); db.commit()
        out.append(ls.id)
    return out


def mark(lid, sid, present):
    db.add(models.Attendance(lesson_id=lid, student_id=sid,
                             present=present))
    db.commit()


def status(sid):
    s2 = SessionLocal()
    v = s2.query(models.Student).get(sid).status
    s2.close()
    return v


H = {"Authorization": "Bearer " + c.post("/api/auth/login", json={
    "username": "asos", "password": "x"}).json()["access_token"]}

print("=== 1. Saqlashda muzlamaydi; o'sha kuni to'g'rilansa ham ===")
g1 = group("G1")
A = student("Kechikkan Ali", g1)
L1 = lessons(g1, [TODAY - timedelta(days=3), TODAY - timedelta(days=2),
                  TODAY - timedelta(days=1)])
for lid in L1:
    r = c.put(f"/api/lessons/{lid}/attendance", headers=H,
              json={"marks": [{"student_id": A, "present": False}]})
    ck("saqlandi", r.status_code, 200)
ck("3-chi kelmadidan keyin ham faol", status(A), "active")
r = c.put(f"/api/lessons/{L1[-1]}/attendance", headers=H,
          json={"marks": [{"student_id": A, "present": True}]})
ck("ustoz keldi ga to'g'riladi", r.status_code, 200)
s2 = SessionLocal(); GL.run_auto_freeze(s2, TODAY); s2.close()
ck("ertalab ham muzlamadi", status(A), "active")

print("\n=== 2. 3 ta kelmadi qolsa — ertalab muzlaydi ===")
g2 = group("G2")
B = student("Kelmagan Vali", g2)
L2 = lessons(g2, [TODAY - timedelta(days=5), TODAY - timedelta(days=3),
                  TODAY - timedelta(days=1)])
for lid in L2:
    c.put(f"/api/lessons/{lid}/attendance", headers=H,
          json={"marks": [{"student_id": B, "present": False}]})
s2 = SessionLocal(); got = GL.run_auto_freeze(s2, TODAY); s2.close()
ck("muzlatildi", status(B), "frozen")
ck("faqat shu o'quvchi", got, [B])
s2 = SessionLocal()
ck("yo'qlama arxivda", s2.query(models.AttendanceArchive).filter(
    models.AttendanceArchive.student_id == B).count(), 3)
ev = s2.query(models.AuditLog).filter(models.AuditLog.action == "auto_freeze",
                                      models.AuditLog.entity_id == B).first()
ck("auditda sanalar", (TODAY - timedelta(days=1)).isoformat() in (ev.note or ""), True)
s2.close()

print("\n=== 3. Bugungi dars kirmaydi ===")
g3 = group("G3")
C = student("Bugun keldi", g3)
D = student("Bugun ham kelmadi", g3)
L3 = lessons(g3, [TODAY - timedelta(days=4), TODAY - timedelta(days=2), TODAY])
for lid in L3[:2]:
    mark(lid, C, 0); mark(lid, D, 0)
mark(L3[2], C, 1); mark(L3[2], D, 0)
s2 = SessionLocal(); GL.run_auto_freeze(s2, TODAY); s2.close()
ck("bugun kelgan — faol", status(C), "active")
ck("2 ta oldingi + bugungi kelmadi — hali faol", status(D), "active")
s2 = SessionLocal(); GL.run_auto_freeze(s2, TODAY + timedelta(days=1)); s2.close()
ck("ertasi kuni 3 ta bo'ldi — muzladi", status(D), "frozen")
ck("bugun kelgan hali ham faol", status(C), "active")

print("\n=== 4. Oy chegarasi: sentabr hisobi qayta hisoblanadi ===")
g4 = group("G4")
E = student("Sentabr Bola", g4)
L4 = lessons(g4, [date(2026, 9, d) for d in (2, 4, 7, 28, 29, 30)])
for lid in L4[:3]:
    mark(lid, E, 1)
for lid in L4[3:]:
    mark(lid, E, 0)
db.add(models.Payment(student_id=E, amount=-480_000, kind="charge",
                      period="2026-09", note="Guruh — 12 dars"))
db.commit()
s2 = SessionLocal(); GL.run_auto_freeze(s2, date(2026, 10, 1)); s2.close()
ck("1-oktabr ertalab muzladi", status(E), "frozen")
s2 = SessionLocal()
sep = s2.query(models.Payment).filter(models.Payment.student_id == E,
                                      models.Payment.kind == "charge",
                                      models.Payment.period == "2026-09").all()
okt = s2.query(models.Payment).filter(models.Payment.student_id == E,
                                      models.Payment.kind == "charge",
                                      models.Payment.period == "2026-10").count()
ck("sentabr hisobi kamaydi (3 dars)", sorted(int(abs(p.amount)) for p in sep), [120_000])
ck("oktabrga hech narsa yozilmadi", okt, 0)
s2.close()

print("\n=== 5. Eski zanjir birdaniga muzlatilmaydi ===")
g5 = group("G5")
F = student("Eski tarix", g5)
L5 = lessons(g5, [TODAY - timedelta(days=d) for d in (40, 38, 36)])
for lid in L5:
    mark(lid, F, 0)
s2 = SessionLocal(); GL.run_auto_freeze(s2, TODAY); s2.close()
ck("eski zanjir — faol qoldi", status(F), "active")

print("\n=== 6. _mc_ensure kuniga bir marta ===")
g6 = group("G6")
G = student("Kunlik", g6)
L6 = lessons(g6, [TODAY - timedelta(days=d) for d in (6, 4, 2)])
for lid in L6:
    mark(lid, G, 0)
s2 = SessionLocal()
key = f"autofreeze_{TODAY.isoformat()}"
s2.query(models.SeedMark).filter(models.SeedMark.key == key).delete()
s2.commit()
common._SEED_KEYS = None if hasattr(common, "_SEED_KEYS") else None
entry._mc_ensure(s2, budget_s=10.0)
s2.close()
ck("kunlik chaqiruvda muzladi", status(G), "frozen")

print()
if fails:
    print(f"{len(fails)} ta XATO: {fails}"); sys.exit(1)
print("HAMMASI OK")
