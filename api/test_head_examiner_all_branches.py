"""EXAMINERLAR BOSHLIG'I BARCHA FILIALLARNI KO'RADI (2026-08-22).

Jahongir: "Exam manager boshligi bor bizda Husniddin qilganmiz u
butun filiallarni examlarini korib turishi kerak shuni togrlab
qoygin korolmayabdikan".

Muhimi: unga FILIAL BIRIKTIRILGAN bo'lsa ham (u qayerdadir o'tiradi),
ish doirasi butun tashkilot bo'lib qolishi kerak. Oddiy examiner esa
faqat o'z filialini ko'radi.
"""
import os, sys

os.environ["DATABASE_URL"] = "sqlite:////tmp/verify_hex/db.sqlite"
os.makedirs("/tmp/verify_hex", exist_ok=True)
if os.path.exists("/tmp/verify_hex/db.sqlite"):
    os.remove("/tmp/verify_hex/db.sqlite")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import date, timedelta
from fastapi.testclient import TestClient
import main, models, roles
import entry  # noqa: F401
from database import SessionLocal
from auth import hash_password

c = TestClient(main.app)
db = SessionLocal()
fails = []


def ck(n, g, w):
    ok = g == w
    print(("OK  " if ok else "XATO ") + f"{n}: {g}"
          + ("" if ok else f"   (kutilgan {w})"))
    if not ok:
        fails.append(n)


b1 = models.Branch(name="Zafar")
b2 = models.Branch(name="Chilonzor")
db.add_all([b1, b2]); db.commit()

g1 = models.Group(name="Zafar guruh", branch_id=b1.id)
g2 = models.Group(name="Chilonzor guruh", branch_id=b2.id)
db.add_all([g1, g2]); db.commit()

today = date.today()
db.add(models.Exam(group_id=g1.id, date=today - timedelta(days=3),
                   kind="unit", status="planned"))
db.add(models.Exam(group_id=g2.id, date=today - timedelta(days=2),
                   kind="unit", status="planned"))
db.commit()

# Boshliq FILIALGA BIRIKTIRILGAN — shunga qaramay hammasini ko'rishi kerak
head = models.User(username="husniddin", full_name="Ozodov Husniddin",
                   password_hash=hash_password("Parol123!"),
                   role=roles.HEAD_EXAMINER, branch_id=b2.id, is_active=1)
# Oddiy examiner — faqat o'z filiali
ex = models.User(username="exam1", full_name="Oddiy Examiner",
                 password_hash=hash_password("Parol123!"),
                 role=roles.EXAMINER, branch_id=b1.id, is_active=1)
db.add_all([head, ex]); db.commit()


def H(u):
    t = c.post("/api/auth/login",
               json={"username": u, "password": "Parol123!"}
               ).json()["access_token"]
    return {"Authorization": f"Bearer {t}"}


def groups_seen(headers, params=""):
    r = c.get(f"/api/examiner/exams?months=6{params}", headers=headers)
    if r.status_code != 200:
        return f"HTTP{r.status_code}"
    rows = r.json()
    rows = rows if isinstance(rows, list) else rows.get("rows", [])
    return sorted({x.get("group") or x.get("group_name") or "?" for x in rows})


print("=== 1. BOSHLIQ — IKKALA FILIAL ===")
hh = H("husniddin")
ck("filiali biriktirilgan bo'lsa ham hammasi",
   groups_seen(hh), ["Chilonzor guruh", "Zafar guruh"])

print("\n=== 2. BOSHLIQ BITTA FILIALNI TANLAB HAM KO'RADI ===")
ck("Zafarni tanladi", groups_seen(hh, f"&branch_id={b1.id}"), ["Zafar guruh"])
ck("Chilonzorni tanladi", groups_seen(hh, f"&branch_id={b2.id}"),
   ["Chilonzor guruh"])

print("\n=== 3. ODDIY EXAMINER — FAQAT O'Z FILIALI ===")
he = H("exam1")
ck("faqat Zafar", groups_seen(he), ["Zafar guruh"])
ck("boshqa filialni so'rasa ham o'ziniki",
   groups_seen(he, f"&branch_id={b2.id}"), ["Zafar guruh"])

print("\n=== 4. ROLLAR RO'YXATI ===")
ck("boshliq org-wide ro'yxatida",
   roles.HEAD_EXAMINER in roles.ORG_WIDE_ROLES, True)
ck("oddiy examiner org-wide EMAS",
   roles.EXAMINER in roles.ORG_WIDE_ROLES, False)

print("\n" + ("HAMMASI O'TDI" if not fails else f"XATOLAR: {fails}"))
sys.exit(1 if fails else 0)
