"""2026-09-10 auditidan keyingi qo'riqchi testlar.

Uchta narsani tekshiradi:
  1) X-Active-Role bilan lavozim almashtirish BAZAGA YOZILMASIN;
  2) JONY_SECRET_ENFORCE=1 bo'lsa token berilmasin HAM, qabul
     qilinmasin HAM;
  3) client_ip soxta x-forwarded-for ga ishonmasin.

Ishga tushirish:  python test_auth_guard.py
"""
import importlib
import os
import sys

os.environ.setdefault("DATABASE_URL", "sqlite:///./auth_guard_test.db")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from starlette.requests import Request as _Req

import auth
import database
import models


def _req(headers):
    raw = [(k.lower().encode(), v.encode()) for k, v in headers.items()]
    return _Req({"type": "http", "method": "GET", "path": "/",
                 "headers": raw, "client": ("10.0.0.1", 0)})


def _fresh_db():
    models.Base.metadata.create_all(bind=database.engine)
    db = database.SessionLocal()
    db.query(models.UserRole).delete()
    db.query(models.User).filter(models.User.username == "audit_nodir").delete()
    db.commit()
    u = models.User(username="audit_nodir", password_hash=auth.hash_password("x"),
                    full_name="Nodir", role="branch_manager", is_active=1)
    db.add(u)
    db.commit()
    db.add(models.UserRole(user_id=u.id, role="teacher"))
    db.commit()
    return db


ok = 0


def check(name, cond):
    global ok
    if cond:
        print("  OK   " + name)
        ok += 1
    else:
        print("  XATO " + name)
        raise SystemExit(1)


print("=== 1. Lavozim almashtirish bazaga yozilmasligi ===")
db = _fresh_db()
token = auth.create_access_token({"sub": "audit_nodir"})
user = auth.get_current_user(_req({"x-active-role": "teacher"}), token, db)
check("so'rov ichida lavozim almashdi", user.role == "teacher")
check("obyekt 'iflos' emas", user not in db.dirty)

db.commit()          # endpoint o'z ishini saqlaydi
db.close()

db2 = database.SessionLocal()
after = (db2.query(models.User)
         .filter(models.User.username == "audit_nodir").first().role)
check("BAZADA asosiy lavozim saqlanib qoldi", after == "branch_manager")
db2.close()

print("=== 2. Yolg'on lavozim qabul qilinmasligi ===")
db = database.SessionLocal()
u2 = auth.get_current_user(_req({"x-active-role": "administrator"}), token, db)
check("ro'yxatda yo'q lavozim rad etildi", u2.role == "branch_manager")
db.close()

print("=== 3. SECRET_ENFORCE ikkala tomonni yopishi ===")
os.environ["JONY_SECRET_ENFORCE"] = "1"
os.environ["VERCEL"] = "1"
os.environ.pop("JONY_CRM_SECRET", None)
a2 = importlib.reload(auth)
check("default kalit aniqlandi", a2.SECRET_IS_DEFAULT and a2.SECRET_ENFORCE)

try:
    a2.create_access_token({"sub": "x"})
    check("token BERISH to'sildi", False)
except Exception as e:
    check("token BERISH to'sildi", getattr(e, "status_code", None) == 503)

try:
    db = database.SessionLocal()
    a2.get_current_user(_req({}), token, db)
    check("token QABUL QILISH to'sildi", False)
except Exception as e:
    check("token QABUL QILISH to'sildi", getattr(e, "status_code", None) == 503)
finally:
    db.close()

os.environ.pop("JONY_SECRET_ENFORCE", None)
os.environ.pop("VERCEL", None)
a3 = importlib.reload(auth)

print("=== 4. client_ip soxta sarlavhaga ishonmasligi ===")
check("XFF: oxirgi (proksi qo'ygan) qiymat olinadi",
      a3.client_ip(_req({"x-forwarded-for": "6.6.6.6, 203.0.113.9"}))
      == "203.0.113.9")
check("Vercel sarlavhasi ustun turadi",
      a3.client_ip(_req({"x-forwarded-for": "6.6.6.6",
                         "x-vercel-forwarded-for": "203.0.113.9"}))
      == "203.0.113.9")
check("sarlavha yo'q bo'lsa ulanish IP'si",
      a3.client_ip(_req({})) == "10.0.0.1")

print()
print("HAMMASI O'TDI — %d ta tekshiruv" % ok)
