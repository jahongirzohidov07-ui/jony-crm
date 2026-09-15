"""IZOHLAR TARIXI (2026-09-15).

Jahongir: "izoh yozish ... oldingilari bilan saqlanib turadigan qilib
bering raqamlar bilan ketma ket korinib tursin" va "muzlatsa
aktivlashtirsa o'quvchini kim qilgani ko'rinmas ekan".

Tekshiriladi:
  1. Izohlar ustidan yozilmaydi, 1, 2, 3 tartibda, muallif bilan;
  2. Eski "note" maydoni birinchi "Oldingi izoh" bo'lib chiqadi;
  3. Muzlatish va faollashtirish — kim qilgani bilan ro'yxatda;
  4. Lid izohlari, o'quvchiga aylangach o'quvchi kartasida ham;
  5. Ruxsat va filial chegarasi, bo'sh izoh rad etiladi.
"""
import os
import sys
import tempfile
from datetime import date, timedelta

_DIR = os.path.join(tempfile.gettempdir(), "comments_test")
os.makedirs(_DIR, exist_ok=True)
_DB = os.path.join(_DIR, "db.sqlite")
os.environ["DATABASE_URL"] = "sqlite:///" + _DB.replace(chr(92), "/")
if os.path.exists(_DB):
    os.remove(_DB)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient          # noqa: E402
import main, models                                # noqa: E402
from database import SessionLocal                  # noqa: E402
from auth import hash_password                     # noqa: E402

client = TestClient(main.app)
fails = []


def ck(name, got, want):
    ok = got == want
    print(("OK  " if ok else "XATO ") + name + f": {got}"
          + ("" if ok else f"   (kutilgan {want})"))
    if not ok:
        fails.append(name)


def tok(u, p="x"):
    return {"Authorization": "Bearer " + client.post(
        "/api/auth/login", json={"username": u, "password": p}
    ).json()["access_token"]}


db = SessionLocal()
b1 = models.Branch(name="Markaz"); db.add(b1)
b2 = models.Branch(name="Zafar"); db.add(b2)
db.commit()
B1, B2 = b1.id, b2.id
for u, name, role, br in [("asos", "Asoschi", "founder", None),
                          ("sotuv", "Dilnoza", "sales_manager", B1),
                          ("ustoz", "Ustoz", "teacher", B1),
                          ("boshqa", "Boshqa admin", "administrator", B2),
                          ("smm", "Smm", "smm_manager", None)]:
    db.add(models.User(username=u, password_hash=hash_password("x"), full_name=name,
                       role=role, branch_id=br, phone="998900000000"))
db.commit()
s = models.Student(full_name="Ali Valiyev", branch_id=B1, status="active",
                   note="Ota-onasi kechqurun qo'ng'iroq qilishni so'radi")
db.add(s); db.commit()
SID = s.id
lead = models.Lead(full_name="Ali Valiyev", phone="998901112233", source="visit",
                   stage="new", branch_id=B1, note="Birinchi murojaat",
                   created_by="Dilnoza", converted_student_id=SID)
db.add(lead); db.commit()
LID = lead.id
db.close()

H, SM, T, OTHER = tok("asos"), tok("sotuv"), tok("ustoz"), tok("boshqa")
URL = f"/api/students/{SID}/comments"

print("=== 1. IZOHLAR USTIDAN YOZILMAYDI ===")
ck("1-izoh", client.post(URL, headers=T, json={"text": "Uy vazifani qilmayapti"}).status_code, 200)
ck("2-izoh", client.post(URL, headers=H, json={"text": "Ota-onasi bilan gaplashildi"}).status_code, 200)
d = client.get(URL, headers=T).json()
texts = [r["text"] for r in d["rows"] if r["source"] == "student" and r["kind"] != "status"]
ck("eski izoh birinchi", texts[0], "Ota-onasi kechqurun qo'ng'iroq qilishni so'radi")
ck("ikkala yangi izoh saqlangan", texts[1:], ["Uy vazifani qilmayapti", "Ota-onasi bilan gaplashildi"])
ck("raqamlar ketma-ket", [r["n"] for r in d["rows"]], list(range(1, len(d["rows"]) + 1)))
ck("muallif yozilgan", [r["by"] for r in d["rows"] if r["kind"] == "comment"], ["Ustoz", "Asoschi"])
ck("lid paytidagi izoh ham bor", "Birinchi murojaat" in [r["text"] for r in d["rows"] if r["source"] == "lead"], True)

print("\n=== 2. KIM MUZLATDI / FAOLLASHTIRDI ===")
until = (date.today() + timedelta(days=20)).isoformat()
r = client.post(f"/api/students/{SID}/freeze", headers=SM, json={"until": until, "note": "Kasal"})
ck("sotuv menejeri muzlatdi", r.status_code, 200)
d = client.get(URL, headers=T).json()
st = [x for x in d["rows"] if x["kind"] == "status"]
ck("muzlatish ro'yxatda", [x["title"] for x in st], ["Muzlatildi"])
ck("kim muzlatgani ko'rinadi", st[0]["by"] if st else None, "Dilnoza")
ck("sarlavha uchun oxirgi holat", (d["last_status"] or {}).get("by"), "Dilnoza")
r = client.post(f"/api/students/{SID}/activate", headers=H, json={})
ck("asoschi faollashtirdi", r.status_code, 200)
d = client.get(URL, headers=T).json()
ck("faollashtirish ham ro'yxatda", [x["title"] for x in d["rows"] if x["kind"] == "status"],
   ["Muzlatildi", "Faollashtirildi"])
ck("oxirgi holatni kim qildi", (d["last_status"] or {}).get("by"), "Asoschi")
ck("oxirgi raqam oxirgi voqea", d["rows"][-1].get("title"), "Faollashtirildi")

print("\n=== 3. LID IZOHLARI ===")
LURL = f"/api/leads/{LID}/comments"
ck("lidga izoh", client.post(LURL, headers=SM, json={"text": "Qayta qo'ng'iroq qilindi"}).status_code, 200)
ck("yana izoh", client.post(LURL, headers=SM, json={"text": "Sinov darsiga yozildi"}).status_code, 200)
ld = client.get(LURL, headers=SM).json()
ck("lid izohlari tartibda", [(r["n"], r["text"]) for r in ld["rows"]],
   [(1, "Birinchi murojaat"), (2, "Qayta qo'ng'iroq qilindi"), (3, "Sinov darsiga yozildi")])
client.put(f"/api/leads/{LID}", headers=SM, json={"address": "Markaz mahalla"})
ck("lidni tahrirlash birinchi izohni o'chirmaydi",
   client.get(LURL, headers=SM).json()["rows"][0]["text"], "Birinchi murojaat")

print("\n=== 4. RUXSAT VA FILIAL ===")
ck("bo'sh izoh — rad", client.post(URL, headers=T, json={"text": "  "}).status_code, 400)
ck("boshqa filial o'quvchisi — yopiq", client.get(URL, headers=OTHER).status_code, 403)
ck("boshqa filial lidi — yopiq", client.get(LURL, headers=OTHER).status_code, 403)
ck("SMM o'quvchi izohini ko'rmaydi", client.get(URL, headers=tok("smm")).status_code, 403)
ck("yo'q o'quvchi — 404", client.get("/api/students/99999/comments", headers=H).status_code, 404)

print()
if fails:
    print(f"XATOLAR ({len(fails)}): " + ", ".join(fails))
    sys.exit(1)
print("HAMMASI O'TDI")
