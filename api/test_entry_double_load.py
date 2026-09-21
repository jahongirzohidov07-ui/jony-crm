# -*- coding: utf-8 -*-
"""ENTRY.PY IKKI MARTA YUKLANMASIN (2026-09-21 avariya).

Jahongir skrinshot yubordi: guruh sahifasida "Serverda kutilmagan
xato", Davomat va Support davomati bo'limlari ochilmadi. Jonli
logdagi xato:

    File "/var/task/api/entry.py", in attendance_grid_v2
        data = result.model_dump()
    AttributeError: 'dict' object has no attribute 'model_dump'

SABAB. Vercel entry.py ni o'zi qo'ygan modul nomi bilan yuklaydi,
"entry" nomi bilan emas. Keyin so'rov paytida finance.py ichidagi
`import entry as _E` ishga tushganda Python uni sys.modules da
topolmay, BUTUN FAYLNI IKKINCHI marta bajardi. Natijada bitta
`app` ustiga hamma route qayta o'raldi va attendance_grid_v2
o'z-o'zini o'rab qoldi: tashqi qavat ichkisini chaqiradi, ichkisi
esa Pydantic model emas, oddiy dict qaytaradi.

Shu test ikkala himoyani ham qo'riqlaydi:
  1. entry.py o'zini sys.modules["entry"] ga yozib qo'yadimi —
     ya'ni keyingi `import entry` faylni qayta bajarmaydimi;
  2. attendance_grid_v2 ichki javob dict bo'lsa ham ishlaydimi
     (ikki qavat o'ralib qolgan holat).
"""
import os
import sys
import tempfile

_DB = os.path.join(tempfile.gettempdir(), "entry_double_test.db")
os.environ["DATABASE_URL"] = "sqlite:///" + _DB.replace("\\", "/")
if os.path.exists(_DB):
    os.remove(_DB)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import importlib                                    # noqa: E402
from datetime import date                           # noqa: E402

from fastapi.testclient import TestClient           # noqa: E402
import main, models, roles                          # noqa: F401,E402
import entry as E                                   # noqa: E402
from database import SessionLocal                   # noqa: E402
from auth import hash_password                      # noqa: E402

client = TestClient(E.app)
fails = []


def ck(n, got, want):
    ok = got == want
    print(("OK   " if ok else "XATO ") + f"{n}: {got}"
          + ("" if ok else f"   (kutilgan {want})"))
    if not ok:
        fails.append(n)


print("=== 1. ENTRY O'ZINI sys.modules GA YOZADIMI ===")
ck("sys.modules['entry'] bor", "entry" in sys.modules, True)
ck("o'sha modulning o'zi", sys.modules["entry"] is E, True)

print("\n=== 2. QAYTA IMPORT FAYLNI QAYTA BAJARMAYDI ===")
# Vercel'dagi holat: modul boshqa nom bilan yuklangan, keyin
# kimdir `import entry` qiladi. Agar himoya ishlamasa, fayl
# qaytadan bajarilib, route'lar ikki qavat o'raladi.
_before = len(E.app.routes)
_again = importlib.import_module("entry")
ck("qayta import bir xil modul", _again is E, True)
ck("route soni o'zgarmadi", len(E.app.routes), _before)

print("\n=== 3. MA'LUMOT TAYYORLASH ===")
db = SessionLocal()
u = models.User(username="att_boss", full_name="Att Boss",
                password_hash=hash_password("x"), role=roles.FOUNDER,
                is_active=True)
db.add(u)
br = models.Branch(name="Att filial")
db.add(br)
db.commit()
t = models.Teacher(full_name="Att Ustoz", branch_id=br.id)
db.add(t)
db.commit()
g = models.Group(name="Att Guruh", teacher_id=t.id, branch_id=br.id,
                 level="Step 1")
db.add(g)
db.commit()
GID = g.id
s1 = models.Student(full_name="Faol O'quvchi", group_id=GID,
                    branch_id=br.id, status="active")
s2 = models.Student(full_name="Muzlatilgan", group_id=GID,
                    branch_id=br.id, status="frozen")
db.add_all([s1, s2])
db.commit()
today = roles.local_today()
ls = models.Lesson(group_id=GID, date=date(today.year, today.month, 1),
                   held=1)
db.add(ls)
db.commit()
db.add(models.Attendance(lesson_id=ls.id, student_id=s1.id, present=1))
db.commit()
Y, M = today.year, today.month
db.close()

tok = client.post("/api/auth/login",
                  json={"username": "att_boss", "password": "x"})
HDR = {"Authorization": "Bearer " + tok.json()["access_token"]}

print("\n=== 4. YO'QLAMA JADVALI OCHILADI ===")
r = client.get(f"/api/groups/{GID}/attendance?year={Y}&month={M}",
               headers=HDR)
ck("javob 200", r.status_code, 200)
d = r.json()
ck("o'quvchilar bor", len(d.get("students") or []) >= 1, True)
ck("darslar bor", len(d.get("lessons") or []) >= 1, True)
ck("belgilar bor", len(d.get("marks") or {}) >= 1, True)
ck("faol o'quvchi ro'yxatda",
   any(x["full_name"] == "Faol O'quvchi" for x in d["students"]), True)

print("\n=== 5. IKKI QAVAT O'RALGAN HOLAT (bugungi xato) ===")
# Funksiyani ataylab o'z-o'ziga o'ratamiz: ichki chaqiruv endi
# Pydantic model emas, DICT qaytaradi — 21-sentabrdagi holatning
# aynan o'zi. Endpoint shunda ham ishlashi kerak.
_saved = E._orig_att_grid


def _inner_returns_dict(**kw):
    """Ikki qavat o'ralgandagi ICHKI qavat: u Pydantic model emas,
    oddiy dict qaytaradi — 21-sentabrdagi xatoning o'zagi shu."""
    res = _saved(**kw)
    return res.model_dump() if hasattr(res, "model_dump") else dict(res)


try:
    E._orig_att_grid = _inner_returns_dict
    r2 = client.get(f"/api/groups/{GID}/attendance?year={Y}&month={M}",
                    headers=HDR)
    ck("ichki javob dict bo'lsa ham 200", r2.status_code, 200)
    d2 = r2.json()
    ck("natija bir xil",
       [x["full_name"] for x in d2.get("students", [])],
       [x["full_name"] for x in d.get("students", [])])
    ck("belgilar yo'qolmadi", d2.get("marks"), d.get("marks"))
finally:
    E._orig_att_grid = _saved

print("\n=== 6. FINANCE ICHIDAGI IMPORT XAVFSIZ ===")
# finance.py so'rov paytida `import entry as _E` qiladi — aynan
# shu qator avariyani keltirib chiqargan edi.
import finance                                      # noqa: E402
_src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         "finance.py"), encoding="utf-8").read()
ck("finance hali ham entry import qiladi", "import entry" in _src, True)
_n_before = len(E.app.routes)
import entry as _E2                                 # noqa: E402
ck("o'sha modul qaytdi", _E2 is E, True)
ck("route soni yana o'zgarmadi", len(E.app.routes), _n_before)
r3 = client.get(f"/api/groups/{GID}/attendance?year={Y}&month={M}",
                headers=HDR)
ck("importdan keyin ham 200", r3.status_code, 200)

print("\n" + ("HAMMASI O'TDI" if not fails else "XATO: " + ", ".join(fails)))
sys.exit(1 if fails else 0)
