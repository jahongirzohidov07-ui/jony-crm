"""ZAXIRA VA TIKLASH (2026-08-15).

Jahongir: "hammasini ozing qil hamma ruxsatni beraman" — bazaning
parolini hech qayerga ko'chirmasdan ishlaydigan zaxira.

Bu test eng muhim savolga javob beradi: ZAXIRA HAQIQATAN TIKLANADIMI.
Sinov bazasi to'ldiriladi, zaxira olinadi, BO'SH bazaga qaytariladi va
qator sonlari solishtiriladi. Sinalmagan zaxira - zaxira emas.
"""
import io
import json
import os
import subprocess
import sys
import tempfile
import zipfile
from datetime import date

os.environ["DATABASE_URL"] = "sqlite:////tmp/bkp_src.db"
for _f in ("/tmp/bkp_src.db", "/tmp/bkp_dst.db"):
    if os.path.exists(_f):
        os.remove(_f)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient          # noqa: E402
import main, models                                # noqa: E402
import entry                                       # noqa: E402
import backup as B                                 # noqa: E402
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


# ---------------- Sinov ma'lumoti ----------------
db = SessionLocal()
b = models.Branch(name="Bekobod 1"); db.add(b); db.commit(); BID = b.id
t = models.Teacher(full_name="Ustoz Aliyev", branch_id=BID)
db.add(t); db.commit(); TID = t.id
g = models.Group(name="B1-01", teacher_id=TID, branch_id=BID,
                 monthly_fee=400000, lesson_price=50000,
                 lesson_days="mon,wed", lesson_time="10:00 - 12:00")
db.add(g); db.commit(); GID = g.id
for i in range(25):
    db.add(models.Student(full_name=f"O'quvchi {i:02d}", branch_id=BID,
                          status="active", group_id=GID,
                          phone=f"+9989012345{i:02d}",
                          enrolled_date=date(2026, 8, 1)))
db.commit()
sids = [s.id for s in db.query(models.Student).all()]
for sid in sids:
    db.add(models.Payment(student_id=sid, amount=400000, kind="payment",
                          method="cash", created_by="Admin"))
    db.add(models.Payment(student_id=sid, amount=-400000, kind="charge",
                          period="2026-08", created_by="avtomat (oylik)"))
db.commit()
db.add_all([
    models.User(username="asos", full_name="Asoschi", role="founder",
                password_hash=hash_password("x"), is_active=1),
    models.User(username="adm", full_name="Admin", role="administrator",
                branch_id=BID, password_hash=hash_password("x"),
                is_active=1),
])
db.commit()

src_counts = {}
for name in B._table_names():
    try:
        from sqlalchemy import text as _t
        src_counts[name] = db.execute(
            _t(f'SELECT COUNT(*) FROM "{name}"')).scalar() or 0
    except Exception:
        src_counts[name] = 0
db.close()


def tok(u):
    return {"Authorization": "Bearer " + c.post(
        "/api/auth/login", json={"username": u, "password": "x"})
        .json()["access_token"]}


F, A = tok("asos"), tok("adm")

print("=== 1. Faqat asoschi zaxira ola oladi ===")
r = c.get("/api/backup/download", headers=A)
ck("administratorga 403", r.status_code, 403)
r = c.get("/api/backup/download", headers=F)
ck("asoschiga 200", r.status_code, 200)
ck("zip qaytdi", r.headers.get("content-type"), "application/zip")
ck("fayl nomi bor",
   "jonyos_" in (r.headers.get("content-disposition") or ""), True)

blob = r.content
ck("fayl bo'sh emas (>5 KB)", len(blob) > 5000, True)

print("\n=== 2. Zip ichida hamma narsa bormi ===")
z = zipfile.ZipFile(io.BytesIO(blob))
names = set(z.namelist())
for need in ("README.txt", "restore.py", "manifest.json", "schema.sql"):
    ck(f"{need} bor", need in names, True)
man = json.loads(z.read("manifest.json"))
ck("jadvallar ro'yxati bor", len(man["tables"]) > 50, True)
ck("qatorlar soni bor", man["total_rows"] > 100, True)
ck("o'quvchilar fayli bor", "data/students.jsonl" in names, True)
ck("to'lovlar fayli bor", "data/payments.jsonl" in names, True)
readme = z.read("README.txt").decode()
ck("README o'zbekcha", "QANDAY TIKLANADI" in readme, True)

print("\n=== 3. Maxfiylik: parol HASH holida, ochiq emas ===")
users = [json.loads(x) for x in
         z.read("data/users.jsonl").decode().splitlines() if x.strip()]
ck("foydalanuvchilar bor", len(users) >= 2, True)
ck("ochiq parol yo'q", any(u.get("password_hash") == "x" for u in users),
   False)
ck("hash bcrypt formatida",
   all(str(u.get("password_hash", "")).startswith("$2")
       for u in users), True)

print("\n=== 4. Jurnal jadvallari zaxiraga tushmaydi ===")
ck("login_attempts yo'q", "data/login_attempts.jsonl" in names, False)
ck("error_logs yo'q", "data/error_logs.jsonl" in names, False)

print("\n=== 5. ENG MUHIMI: BO'SH BAZAGA TIKLANADIMI ===")
work = tempfile.mkdtemp(prefix="jonyos_restore_")
z.extractall(work)

# Bo'sh bazada sxemani yaratamiz (ilova qanday qilsa, shunday)
code = (
    "import os,sys;"
    "os.environ['DATABASE_URL']='sqlite:////tmp/bkp_dst.db';"
    f"sys.path.insert(0,{os.path.dirname(os.path.abspath(__file__))!r});"
    "import main, entry; print('SXEMA_OK')"
)
p = subprocess.run([sys.executable, "-c", code], capture_output=True,
                   text=True, timeout=300)
ck("bo'sh bazada sxema yaratildi", "SXEMA_OK" in p.stdout, True)

# Tiklash skriptini ISHGA TUSHIRAMIZ
p = subprocess.run(
    [sys.executable, os.path.join(work, "restore.py"),
     "sqlite:////tmp/bkp_dst.db"],
    capture_output=True, text=True, timeout=600)
tail = (p.stdout or "")[-400:] + (p.stderr or "")[-300:]
ck("restore.py xatosiz tugadi", p.returncode, 0)
ck("TAYYOR xabari chiqdi", "TAYYOR:" in (p.stdout or ""), True)
if "TAYYOR:" not in (p.stdout or ""):
    print("  --- chiqish ---\n" + tail)

print("\n=== 6. Qator sonlari mos keldimi ===")
from sqlalchemy import create_engine, text as _t2       # noqa: E402
dst = create_engine("sqlite:////tmp/bkp_dst.db")
bad = []
checked = 0
with dst.begin() as cx:
    for tbl in man["tables"]:
        name, want = tbl["name"], tbl["rows"]
        if want == 0:
            continue
        try:
            got = cx.execute(_t2(f'SELECT COUNT(*) FROM "{name}"')).scalar()
        except Exception:
            got = -1
        checked += 1
        if got != want:
            bad.append(f"{name}: {got}/{want}")
ck(f"{checked} ta to'ldirilgan jadval tekshirildi", checked > 5, True)
ck("hamma jadval to'liq tiklandi", bad or "hammasi mos", "hammasi mos")

print("\n=== 7. Muhim ma'lumot joyidami ===")
with dst.begin() as cx:
    n_st = cx.execute(_t2("SELECT COUNT(*) FROM students")).scalar()
    n_pay = cx.execute(_t2("SELECT COUNT(*) FROM payments")).scalar()
    bal = cx.execute(_t2("SELECT COALESCE(SUM(amount),0) FROM payments")
                     ).scalar()
    nm = cx.execute(_t2("SELECT full_name FROM students WHERE id=:i"),
                    {"i": sids[0]}).scalar()
ck("o'quvchilar soni", n_st, src_counts.get("students"))
ck("to'lov yozuvlari soni", n_pay, src_counts.get("payments"))
ck("umumiy balans 0 (to'lov = hisob)", float(bal), 0.0)
ck("ism to'g'ri ko'chdi", nm, "O'quvchi 00")

print("\n=== 8. Zaxira holati sahifasi ===")
r = c.get("/api/backup/status", headers=F)
ck("200", r.status_code, 200)
d = r.json()
ck("jadvallar soni ko'rsatilgan", d["tables"] > 50, True)
ck("oxirgi zaxira qayd etilgan", bool(d.get("last")), True)
ck("kim olgani yozilgan", (d["last"] or {}).get("by"), "Asoschi")

print("\n=== 9. Telegram: bot yo'q bo'lsa jimgina o'tadi ===")
db = SessionLocal()
res = B.daily_backup_to_telegram(db)
ck("yiqilmadi, sabab qaytardi", "skipped" in res, True)

print("\n=== 10. Baza Telegram uchun juda katta — zip umuman yasalmaydi ===")
# Jonli bazada zip 50 MB dan oshadi va Telegram rad etadi. U holda
# butun bazani har kuni o'qish — bekor sarf. Hajm oldindan tekshiriladi.
_orig_size, _orig_build = B._db_size_bytes, B.build_backup
_built = []
B._db_size_bytes = lambda _db: 600 * 1024 * 1024
B.build_backup = lambda *a, **k: _built.append(1) or _orig_build(*a, **k)
try:
    res = B.daily_backup_to_telegram(db)
finally:
    B._db_size_bytes, B.build_backup = _orig_size, _orig_build
ck("katta baza — o'tkazib yuborildi", "katta" in str(res.get("skipped")), True)
ck("zip yasalmadi (resurs sarflanmadi)", len(_built), 0)
ck("hajm javobda ko'rinadi", res.get("db_mb"), 600)
ck("SQLite'da hajm cheklovi yo'q", B._db_size_bytes(db), 0)
db.close()

print("\n" + ("HAMMASI OK" if not fails
              else f"{len(fails)} ta XATO: {fails}"))
sys.exit(1 if fails else 0)
