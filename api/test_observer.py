"""Kuzatuvchi (observer) qo'riqchi testi — 2026-10-19.

Jahongir: "kuzatuvchi rolidan barcha agentlar kirib o'ziga kerakli
ma'lumotlarni olishi mumkin bo'lsin". Maslahat kengashi agentlari shu
hisob bilan kiradi, shuning uchun eng muhim kafolat: kuzatuvchi HECH
QANDAY yozish so'rovini o'tkaza olmaydi.

Tekshiriladi:
  1) login: asoschi ekranlari (role=founder) + read_only belgisi;
  2) ko'rish: BI analitika ochiladi, butun baza zaxirasi yopiq;
  3) TIZIMDAGI BARCHA yozish yo'llari (POST/PUT/PATCH/DELETE) —
     tizimga kirishni talab qiladigan har biri 403 qaytaradi va
     bazada hech bir jadval o'zgarmaydi;
  4) o'z parolini almashtira oladi (standart parol majburiyati);
  5) kuzatuvchi QO'SHIMCHA lavozim sifatida ishlamaydi;
  6) asoschi kuzatuvchi hisobini ocha oladi.

Ishga tushirish:  python test_observer.py
"""
import os
import re
import sys

DB = "/tmp/observer_test.db"
os.environ["DATABASE_URL"] = "sqlite:///" + DB
if os.path.exists(DB):
    os.remove(DB)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.routing import APIRoute               # noqa: E402
from fastapi.testclient import TestClient          # noqa: E402
from sqlalchemy import inspect, text               # noqa: E402

import auth                                        # noqa: E402
import entry                                       # noqa: E402
import models                                      # noqa: E402
import roles                                       # noqa: E402
from database import SessionLocal, engine          # noqa: E402

app = entry.app
c = TestClient(app, raise_server_exceptions=False)
fails = []


def ck(name, cond, extra=""):
    print(("  OK   " if cond else "  XATO ") + name
          + (f"  ({extra})" if extra and not cond else ""))
    if not cond:
        fails.append(name)


db = SessionLocal()
b = models.Branch(name="Bekobod 1")
db.add(b)
db.commit()
PW = "Kuzat-2026!x"
founder = models.User(username="t_founder", full_name="Asoschi",
                      role=roles.FOUNDER, is_active=1,
                      password_hash=auth.hash_password(PW))
obs = models.User(username="t_kuzatuvchi", full_name="Ma'lumotchi",
                  role=roles.OBSERVER, is_active=1, branch_id=b.id,
                  password_hash=auth.hash_password(PW))
teacher = models.User(username="t_teacher", full_name="Ustoz",
                      role=roles.TEACHER, is_active=1, branch_id=b.id,
                      password_hash=auth.hash_password(PW))
db.add_all([founder, obs, teacher])
db.commit()
db.add(models.UserRole(user_id=teacher.id, role=roles.OBSERVER))
db.commit()
OBS_ID = obs.id
db.close()


def login(username):
    r = c.post("/api/auth/login", json={"username": username,
                                        "password": PW})
    assert r.status_code == 200, r.text
    return r.json()


print("=== 1. Login ===")
lj = login("t_kuzatuvchi")
ck("login role=founder (asoschi ekranlari)", lj.get("role") == "founder",
   lj.get("role"))
ck("login read_only=true", lj.get("read_only") is True)
H = {"Authorization": "Bearer " + lj["access_token"]}
me = c.get("/api/me", headers=H).json()
ck("/api/me read_only=true", me.get("read_only") is True)
ck("/api/me role=founder", me.get("role") == "founder", me.get("role"))
fj = login("t_founder")
ck("asoschi read_only=false", fj.get("read_only") is False)
HF = {"Authorization": "Bearer " + fj["access_token"]}

print("=== 2. Ko'rish ===")
r = c.get("/api/analytics/bi", headers=H)
ck("BI analitika ochiladi", r.status_code == 200, r.status_code)
r = c.get("/api/users", headers=H)
ck("xodimlar ro'yxati ochiladi", r.status_code == 200, r.status_code)
for p in ("/api/backup/download", "/api/hr/documents", "/api/errors"):
    r = c.get(p, headers=H)
    ck(f"{p} yopiq (403)", r.status_code == 403, r.status_code)


# ---- 3. Barcha yozish yo'llari -----------------------------------------
def walk(routes, prefix=""):
    """(to'liq yo'l, route) — ichma-ich ulangan routerlar prefiksi bilan."""
    for r in routes:
        if isinstance(r, APIRoute):
            yield prefix + r.path, r
            continue
        ic = getattr(r, "include_context", None)
        nested = getattr(ic, "included_router", None) if ic else None
        if nested is not None and hasattr(nested, "routes"):
            yield from walk(nested.routes,
                            prefix + (getattr(ic, "prefix", "") or ""))


def needs_login(dep, seen=None):
    seen = seen if seen is not None else set()
    if id(dep) in seen:
        return False
    seen.add(id(dep))
    if dep.call is auth.get_current_user:
        return True
    return any(needs_login(d, seen) for d in dep.dependencies)


def counts():
    insp = inspect(engine)
    out = {}
    with engine.connect() as cn:
        for t in insp.get_table_names():
            out[t] = cn.execute(text(f'SELECT COUNT(*) FROM "{t}"')).scalar()
    return out


IGNORE_TABLES = {"login_attempts", "audit_logs", "error_logs"}
WRITE = {"POST", "PUT", "PATCH", "DELETE"}

print("=== 3. Barcha yozish yo'llari ===")
before = counts()
checked, leaked, seen_keys = 0, [], set()
for full, rt in walk(app.router.routes):
    methods = (rt.methods or set()) & WRITE
    if not methods or not needs_login(rt.dependant):
        continue
    path = re.sub(r"\{[^}]+\}", "1", full)
    for m in sorted(methods):
        key = (m, full)
        if key in seen_keys:
            continue
        seen_keys.add(key)
        if full in roles.OBSERVER_WRITE_ALLOW:
            continue
        r = c.request(m, path, headers=H, json={})
        checked += 1
        if r.status_code != 403:
            leaked.append(f"{m} {full} -> {r.status_code}")
after = counts()
changed = [t for t in before
           if t not in IGNORE_TABLES and before[t] != after.get(t)]
ck(f"{checked} ta yozish yo'li — hammasi 403", not leaked,
   "; ".join(leaked[:10]))
ck("hech bir jadval o'zgarmadi", not changed, ", ".join(changed))
ck("yozish yo'llari topildi (test ishlayapti)", checked > 200, checked)

print("=== 4. O'z paroli ===")
r = c.put("/api/auth/me/password", headers=H,
          json={"current_password": PW, "new_password": PW + "Y"})
ck("kuzatuvchi o'z parolini almashtira oladi", r.status_code == 200,
   r.status_code)
db = SessionLocal()
ck("parol almashgandan keyin ham rol=observer",
   db.get(models.User, OBS_ID).role == roles.OBSERVER)
db.close()

print("=== 5. Qo'shimcha lavozim sifatida ishlamaydi ===")
tj = login("t_teacher")
HT = {"Authorization": "Bearer " + tj["access_token"],
      "X-Active-Role": roles.OBSERVER}
me_t = c.get("/api/me", headers=HT).json()
ck("ustoz kuzatuvchiga o'ta olmaydi", me_t.get("role") == roles.TEACHER,
   me_t.get("role"))
r = c.get("/api/analytics/bi", headers=HT)
ck("ustozga BI yopiqligicha qoladi", r.status_code == 403, r.status_code)

print("=== 6. Asoschi kuzatuvchi ochadi ===")
r = c.post("/api/users", headers=HF, json={
    "username": "agent2", "password": PW, "full_name": "Agent 2",
    "role": roles.OBSERVER, "phone": "901112233"})
ck("asoschi kuzatuvchi hisobini ochadi", r.status_code == 200,
   f"{r.status_code} {r.text[:200]}")
r = c.post("/api/users", headers=H, json={
    "username": "agent3", "password": PW, "full_name": "Agent 3",
    "role": roles.OBSERVER, "phone": "901112244"})
ck("kuzatuvchi o'zi hisob ocha olmaydi", r.status_code == 403,
   r.status_code)

print()
if fails:
    print(f"XATO: {len(fails)} ta tekshiruv o'tmadi")
    sys.exit(1)
print("Hammasi OK")
