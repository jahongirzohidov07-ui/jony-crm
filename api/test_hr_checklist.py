"""CHECKLIST — HR uchun bitta jadval (2026-09-26).

Jahongir: "checklist bo'limini ochib ber hr uchun, supportlarga ko'rgan
videolari va o'qigan kitobini o'tdi o'tmadi qilib bitta katta jadvalda
ko'rib tura olay".

Tekshiriladi:
  1. Faqat HR/asoschi/support boshlig'i ko'radi; support o'zi — 403.
  2. Qatorlar: faqat supportlar (asosiy YOKI qo'shimcha lavozim),
     ishdan ketgan (is_active=0) — yo'q.
  3. Ustunlar: supportga tegishli faol videolar va kutubxona yozuvlari;
     boshqa lavozimga mo'ljallangani va o'chirilgani — yo'q.
  4. Video "o'tdi" = pleyer done; kutubxona "o'tdi" = HR belgisi.
  5. Jadvaldan belgilash (mavjud endpoint) — katak o'tdi bo'ladi, kim va
     qachon belgilagani chiqadi; bekor qilish ham ishlaydi.
  6. Xulosa: majburiylardan nechtasi o'tildi, foiz.
"""
import os
import sys
import tempfile
from datetime import datetime

_DIR = os.path.join(tempfile.gettempdir(), "hr_checklist_test")
os.makedirs(_DIR, exist_ok=True)
_DB = os.path.join(_DIR, "db.sqlite")
os.environ["DATABASE_URL"] = "sqlite:///" + _DB.replace(chr(92), "/")
if os.path.exists(_DB):
    os.remove(_DB)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient          # noqa: E402
import main, models, roles                         # noqa: E402
import entry                                       # noqa: E402
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
b = models.Branch(name="Zafar"); db.add(b); db.commit()


def user(login, name, role, active=1):
    u = models.User(username=login, password_hash=hash_password("x"),
                    full_name=name, role=role, branch_id=b.id,
                    is_active=active)
    db.add(u); db.commit()
    return u


hr = user("hr", "HR Menejer", roles.HR_MANAGER)
s1 = user("s1", "Ali Support", roles.SUPPORT_TEACHER)
s2 = user("s2", "Vali Support", roles.SUPPORT_TEACHER)
gone = user("s3", "Ketgan Support", roles.SUPPORT_TEACHER, active=0)
tch = user("t1", "Ustoz", roles.TEACHER)
# Asosiy lavozimi ustoz, qo'shimchasi support
both = user("t2", "Ikki Lavozim", roles.TEACHER)
db.add(models.UserRole(user_id=both.id, role=roles.SUPPORT_TEACHER))
db.commit()

PdV, PdW = models.PdVideo, models.PdWatch
LI, LP = models.LibraryItem, models.LibraryProgress
v1 = PdV(title="Dars metodikasi", yt_id="aaaaaaaaaaa", duration=600,
         required=1, active=1, order_no=1)
v2 = PdV(title="Faqat ustozlarga", yt_id="bbbbbbbbbbb", duration=600,
         target_roles=roles.TEACHER, required=1, active=1, order_no=2)
v3 = PdV(title="O'chirilgan video", yt_id="ccccccccccc", duration=600,
         required=1, active=0, order_no=3)
bk = LI(title="Support qo'llanmasi", kind="book", url="https://x",
        target_roles=roles.SUPPORT_TEACHER, required=1, active=1)
opt = LI(title="Qo'shimcha havola", kind="link", url="https://y",
         required=0, active=1)
db.add_all([v1, v2, v3, bk, opt]); db.commit()
# Ali videoni ko'rib bo'lgan, Vali yarmini
db.add(PdW(video_id=v1.id, user_id=s1.id, percent=100, done=1,
           done_at=datetime(2026, 9, 20, 10, 0)))
db.add(PdW(video_id=v1.id, user_id=s2.id, percent=50, done=0))
# Vali kitobni 70% o'qigan (o'zi yozgan), HR hali belgilamagan
db.add(LP(item_id=bk.id, user_id=s2.id, percent=70, passed=0))
db.commit()


def tok(u):
    r = c.post("/api/auth/login", json={"username": u, "password": "x"})
    return {"Authorization": "Bearer " + r.json()["access_token"]}


H_HR, H_S1 = tok("hr"), tok("s1")

print("=== 1. RUXSAT ===")
r = c.get("/api/hr/checklist", headers=H_S1)
ck("support o'zi ko'rmaydi", r.status_code, 403)
r = c.get("/api/hr/checklist", headers=H_HR)
ck("HR ko'radi", r.status_code, 200)
d = r.json()

print("\n=== 2. QATORLAR ===")
names = sorted(x["name"] for x in d["rows"])
ck("supportlar + qo'shimcha lavozim, ketgan yo'q, ustoz yo'q", names,
   ["Ali Support", "Ikki Lavozim", "Vali Support"])

print("\n=== 3. USTUNLAR ===")
titles = [col["title"] for col in d["columns"]]
ck("supportga tegishli faollar", titles,
   ["Dars metodikasi", "Support qo'llanmasi", "Qo'shimcha havola"])
ck("video belgilanmaydi, kutubxona belgilanadi",
   [col["can_mark"] for col in d["columns"]], [False, True, True])

print("\n=== 4. KATAKLAR ===")
rows = {x["name"]: x for x in d["rows"]}
kv, kb = f"pd:{v1.id}", f"lib:{bk.id}"
ck("Ali: video o'tdi", rows["Ali Support"]["cells"][kv]["passed"], True)
ck("Ali: sana", rows["Ali Support"]["cells"][kv]["at"], "20.09.2026")
ck("Vali: video 50%", (rows["Vali Support"]["cells"][kv]["passed"],
                       rows["Vali Support"]["cells"][kv]["percent"]),
   (False, 50))
ck("Vali: kitob 70%, o'tmadi", (rows["Vali Support"]["cells"][kb]["passed"],
                                rows["Vali Support"]["cells"][kb]["percent"]),
   (False, 70))
ck("Ali: 1/2 majburiy", (rows["Ali Support"]["passed"],
                         rows["Ali Support"]["required"]), (1, 2))
ck("Ali: 50%", rows["Ali Support"]["percent"], 50)

print("\n=== 5. JADVALDAN BELGILASH ===")
r = c.put(f"/api/library/{bk.id}/people/{s2.id}", headers=H_HR,
          json={"passed": True})
ck("belgilandi", r.status_code, 200)
d = c.get("/api/hr/checklist", headers=H_HR).json()
rows = {x["name"]: x for x in d["rows"]}
cell = rows["Vali Support"]["cells"][kb]
ck("Vali: kitob o'tdi", cell["passed"], True)
ck("kim belgiladi", cell["by"], "HR Menejer")
r = c.put(f"/api/library/{bk.id}/people/{s2.id}", headers=H_HR,
          json={"passed": False})
d = c.get("/api/hr/checklist", headers=H_HR).json()
rows = {x["name"]: x for x in d["rows"]}
ck("bekor qilindi", rows["Vali Support"]["cells"][kb]["passed"], False)

print("\n=== 6. XULOSA VA LAVOZIM ALMASHTIRISH ===")
ck("odamlar soni", d["summary"]["people"], 3)
ck("to'liq o'tganlar yo'q", d["summary"]["complete"], 0)
r = c.get(f"/api/hr/checklist?role={roles.TEACHER}", headers=H_HR)
t_names = sorted(x["name"] for x in r.json()["rows"])
ck("ustozlar ro'yxati", t_names, ["Ikki Lavozim", "Ustoz"])
ck("ustozga o'z videosi ham chiqadi",
   "Faqat ustozlarga" in [col["title"] for col in r.json()["columns"]], True)
r = c.get("/api/hr/checklist?role=yo'q", headers=H_HR)
ck("noto'g'ri lavozim", r.status_code, 400)

print("\n=== 7. CHECKLISTDAN QO'SHISH / OLIB TASHLASH ===")
SUP = roles.SUPPORT_TEACHER


def cols(role=SUP):
    j = c.get(f"/api/hr/checklist?role={role}", headers=H_HR).json()
    return {col["title"]: col for col in j["columns"]}, j


_, j = cols()
ck("HR kutubxona va videoni tahrirlay oladi",
   (j["can_edit_lib"], j["can_edit_pd"]), (True, True))
r = c.post("/api/library", headers=H_HR,
           json={"title": "Qog'oz kitob", "kind": "book", "url": None,
                 "target_roles": [SUP], "required": True})
ck("havolasiz kitob qo'shildi", r.status_code, 200)
r2 = c.post("/api/library", headers=H_HR,
            json={"title": "Havolasiz havola", "kind": "link", "url": None,
                  "target_roles": [SUP]})
ck("havolasiz havola rad etiladi", r2.status_code, 400)
r3 = c.post("/api/pd/videos", headers=H_HR,
            json={"title": "Yangi video", "yt": "https://youtu.be/dQw4w9WgXcQ",
                  "target_roles": [SUP], "required": True})
ck("video qo'shildi", r3.status_code, 200)
cc, _ = cols()
ck("ikkalasi ustunda", ("Qog'oz kitob" in cc, "Yangi video" in cc),
   (True, True))
ck("video havolasi", cc["Yangi video"]["url"], "https://youtu.be/dQw4w9WgXcQ")
ck("faqat support uchun", cc["Qog'oz kitob"]["targets"], [SUP])
# Tahrirlash
c.put(f"/api/library/{r.json()['id']}", headers=H_HR,
      json={"title": "Qog'oz kitob (2-nashr)", "required": False})
cc, _ = cols()
ck("nomi va majburiyligi o'zgardi",
   cc.get("Qog'oz kitob (2-nashr)", {}).get("required"), False)
# Faqat shu lavozimdagi -> yashiriladi
c.put(f"/api/library/{r.json()['id']}", headers=H_HR, json={"active": False})
cc, _ = cols()
ck("yashirildi", "Qog'oz kitob (2-nashr)" in cc, False)
# Hammaga berilgan -> faqat support ro'yxatidan chiqadi
staff = [x for x in roles.STAFF_ROLES if x != SUP]
c.put(f"/api/library/{opt.id}", headers=H_HR, json={"target_roles": staff})
cc, _ = cols()
ct, _ = cols(roles.TEACHER)
ck("supportdan chiqdi, ustozda qoldi",
   ("Qo'shimcha havola" in cc, "Qo'shimcha havola" in ct), (False, True))
# Support boshlig'i: kutubxona ha, avtomat video yo'q
hs = user("hs", "Support Boshlig'i", roles.HEAD_SUPPORT)
H_HS = tok("hs")
j = c.get("/api/hr/checklist", headers=H_HS).json()
ck("support boshlig'i: kutubxona ha, video yo'q",
   (j["can_edit_lib"], j["can_edit_pd"]), (True, False))
r = c.post("/api/pd/videos", headers=H_HS,
           json={"title": "X", "yt": "dQw4w9WgXcQ", "target_roles": [SUP]})
ck("support boshlig'i video qo'sha olmaydi", r.status_code, 403)

print()
if fails:
    print(f"XATO: {len(fails)} ta tekshiruv o'tmadi")
    for f in fails:
        print("   - " + f)
    sys.exit(1)
print("HAMMASI O'TDI")
sys.exit(0)
