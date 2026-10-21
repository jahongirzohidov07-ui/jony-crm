"""UMUMIY VAZIFA — BITTASI BAJARSA HAMMADAN YO'QOLADI (2026-10-21).

Jahongir: "adminga task berilsa qildim desa o'sha filial adminlaridan
ham olib tashlasin bildirishnomalardan".

Tekshiriladi:
  1. "KETISH XAVFI" — filialning har bir adminiga nusxa. Bittasi
     "bajarildi" desa, qolgan nusxalar ham yopiladi (kalitli va kalitsiz
     eski yozuvlar); boshqa filial va boshqa o'quvchi vazifasiga
     tegilmaydi; oddiy (qo'lda berilgan) vazifaga tegilmaydi.
  2. Muzlatish muddati tugagan o'quvchi bildirishnomasi: aloqa
     vazifasini bitta admin bajarsa — filialdagi hamma admindan
     yo'qoladi. Ikkinchi marta muzlatilsa — yangi vazifa yaratiladi.
"""
import os
import sys
import tempfile
from datetime import date, datetime, timedelta

_DIR = os.path.join(tempfile.gettempdir(), "shared_tasks_test")
os.makedirs(_DIR, exist_ok=True)
_DB = os.path.join(_DIR, "db.sqlite")
os.environ["DATABASE_URL"] = "sqlite:///" + _DB.replace(chr(92), "/")
if os.path.exists(_DB):
    os.remove(_DB)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient          # noqa: E402
import main, models, roles                         # noqa: E402
import entry                                       # noqa: E402,F401
import common                                      # noqa: E402
from database import SessionLocal                  # noqa: E402
from auth import hash_password                     # noqa: E402

c = TestClient(main.app)
fails = []


def ck(name, got, want):
    ok = got == want
    print(("OK  " if ok else "XATO ") + name + f": {got}"
          + ("" if ok else f"   (kutilgan {want})"))
    if not ok:
        fails.append(name)


db = SessionLocal()
b1, b2 = models.Branch(name="Zafar"), models.Branch(name="Chilonzor")
db.add_all([b1, b2]); db.commit()


def user(login, role, br):
    u = models.User(username=login, password_hash=hash_password("x"),
                    full_name=login.upper(), role=role, branch_id=br.id,
                    is_active=1)
    db.add(u); db.commit()
    return u


A1 = user("adm1", roles.SALES_MANAGER, b1)
A2 = user("adm2", roles.SALES_MANAGER, b1)
A3 = user("adm3", roles.ADMINISTRATOR, b1)
B1 = user("adm4", roles.SALES_MANAGER, b2)
FO = user("asos", roles.FOUNDER, b1)


def tok(u):
    r = c.post("/api/auth/login", json={"username": u, "password": "x"})
    return {"Authorization": "Bearer " + r.json()["access_token"]}


H1, H2, H3, H4 = tok("adm1"), tok("adm2"), tok("adm3"), tok("adm4")


def open_ids(uid):
    db.expire_all()
    return [t.id for t in db.query(models.Task).filter(
        models.Task.assignee_id == uid,
        models.Task.status.notin_(("done", "cancelled"))).all()]


def task(uid, br, title, key=None, source="risk", desc="Qarzi ko'p"):
    t = models.Task(title=title, description=desc, assignee_id=uid,
                    branch_id=br.id, deadline=date.today() + timedelta(days=2),
                    priority="urgent", source=source, created_by="Tizim",
                    group_key=key, created_at=datetime.utcnow())
    db.add(t); db.commit()
    return t.id


print("=== 1. KETISH XAVFI — KALITLI NUSXALAR ===")
k = "risk:7:payment_late:2026-10-21"
t1 = task(A1.id, b1, "KETISH XAVFI: Ali", k)
t2 = task(A2.id, b1, "KETISH XAVFI: Ali", k)
t3 = task(A3.id, b1, "KETISH XAVFI: Ali", k)
other = task(A2.id, b1, "KETISH XAVFI: Vali",
             "risk:8:payment_late:2026-10-21")
manual = task(A3.id, b1, "Hisobot topshiring", None, source="manual")
r = c.put(f"/api/tasks/{t1}", headers=H1,
          json={"status": "done", "result": "Ota-onasi bilan gaplashdim"})
ck("bajarildi", r.status_code, 200)
ck("adm2 da Ali vazifasi yopildi", t2 in open_ids(A2.id), False)
ck("adm3 da Ali vazifasi yopildi", t3 in open_ids(A3.id), False)
ck("adm2 dagi boshqa o'quvchi vazifasi qoldi", other in open_ids(A2.id), True)
ck("qo'lda berilgan vazifaga tegilmadi", manual in open_ids(A3.id), True)
db.expire_all()
ck("natijada kim bajargani", db.query(models.Task).get(t2).result,
   "ADM1 bajardi: Ota-onasi bilan gaplashdim")
al = c.get("/api/my/alerts", headers=H2).json()
ck("adm2 bildirishnomasida 1 ta vazifa (faqat Vali)",
   any("1 ta ochiq vazifangiz" in i["text"] for i in al["items"]), True)

print("\n=== 2. KALITSIZ ESKI NUSXALAR ===")
o1 = task(A1.id, b1, "KETISH XAVFI: Soli", None)
o2 = task(A2.id, b1, "KETISH XAVFI: Soli", None)
ob = task(B1.id, b2, "KETISH XAVFI: Soli", None)   # boshqa filial
c.put(f"/api/tasks/{o2}", headers=H2, json={"status": "done"})
ck("eski nusxa ham yopildi", o1 in open_ids(A1.id), False)
ck("boshqa filialga tegilmadi", ob in open_ids(B1.id), True)

print("\n=== 3. MUZLATISH MUDDATI TUGAGAN O'QUVCHI ===")
st = models.Student(full_name="Muz Bola", branch_id=b1.id, status="frozen",
                    frozen_until=date.today() - timedelta(days=1))
db.add(st); db.commit()
common._freeze_task(db, st, st.frozen_until, "kasal"); db.commit()
db.expire_all()
ft = db.query(models.Task).filter(
    models.Task.title == "Muzlatilgan o'quvchi: Muz Bola").first()
ck("vazifa kalit bilan", ft.group_key,
   common.freeze_task_key(st.id, st.frozen_until))


def freeze_alert(h):
    return any("Muz Bola" in i["text"]
               for i in c.get("/api/my/alerts", headers=h).json()["items"])


ck("oldin: adm2 da bildirishnoma bor", freeze_alert(H2), True)
ck("oldin: adm3 da bildirishnoma bor", freeze_alert(H3), True)
owner_h = {A1.id: H1, A2.id: H2, A3.id: H3}[ft.assignee_id]
r = c.put(f"/api/tasks/{ft.id}", headers=owner_h, json={
    "status": "done", "delay_reason": "dam olish kuni edi",
    "result": "Qo'ng'iroq qilindi"})
ck("aloqa vazifasi bajarildi", r.status_code, 200)
ck("keyin: adm2 da bildirishnoma yo'q", freeze_alert(H2), False)
ck("keyin: adm3 da bildirishnoma yo'q", freeze_alert(H3), False)
# Qayta muzlatildi — yangi muddat, yangi vazifa, bildirishnoma qaytadi
st.frozen_until = date.today() - timedelta(days=0)
db.commit()
common._freeze_task(db, st, st.frozen_until, "yana"); db.commit()
db.expire_all()
n = db.query(models.Task).filter(
    models.Task.title == "Muzlatilgan o'quvchi: Muz Bola").count()
ck("ikkinchi muzlatishda yangi vazifa yaratildi", n, 2)
ck("yangi muddat — bildirishnoma yana chiqdi", freeze_alert(H2), True)

print()
if fails:
    print(f"XATO: {len(fails)} ta tekshiruv o'tmadi")
    for x in fails:
        print("   - " + x)
    sys.exit(1)
print("HAMMASI O'TDI")
sys.exit(0)
