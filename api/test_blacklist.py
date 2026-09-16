"""HR QORA RO'YXATI (2026-09-16, Jahongir: "o'quv markaz qora ro'yxatini
shakllantir hr bo'limi uchun, bu bo'limga tushgan nomzodlar boshqa ishga
olinmasin").

Tekshiriladi: qo'shish/chiqarish qoidalari, odamni telefon va ism bo'yicha
tanish, va ishga olishning HAMMA yo'li yopiqligi."""
import os, sys, tempfile

_tmp = tempfile.mkdtemp(prefix="jony_bl_")
os.environ["DATABASE_URL"] = "sqlite:///" + os.path.join(
    _tmp, "db.sqlite").replace("\\", "/")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
import main, models, roles
import entry  # noqa
from database import SessionLocal
from auth import hash_password

c = TestClient(main.app)
db = SessionLocal()
fails = []
PW = "Parol123!"


def ck(n, g, w):
    ok = g == w
    print(("OK  " if ok else "XATO ") + f"{n}: {g}"
          + ("" if ok else f"  (kutilgan {w})"))
    if not ok:
        fails.append(n)


b = models.Branch(name="Zafar"); db.add(b); db.commit()


def mk(username, role, name=None, phone=None, active=1):
    u = models.User(username=username, full_name=name or username.title(),
                    password_hash=hash_password(PW), role=role,
                    branch_id=b.id, is_active=active, phone=phone)
    db.add(u); db.commit()
    return u


def H(username):
    r = c.post("/api/auth/login", json={"username": username, "password": PW})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


mk("asoschi", roles.FOUNDER)
mk("hr", roles.HR_MANAGER)
mk("rahbar", roles.BRANCH_MANAGER)
mk("ustoz", roles.TEACHER)
HR, BM, T = H("hr"), H("rahbar"), H("ustoz")


def add(body, h=HR):
    return c.post("/api/hr/blacklist", headers=h, json=body)


def new_cand(name, phone=None):
    r = c.post("/api/candidates", headers=HR, json={
        "full_name": name, "phone": phone, "position": "sales",
        "branch_id": b.id})
    assert r.status_code == 200, r.text
    return r.json()["id"]


print("=== QO'SHISH ===")
r = add({"full_name": "Karimov Aziz", "phone": "+998 90 111-22-33",
         "category": "theft", "reason": "Kassadan pul yo'qolgan"})
ck("HR qo'shdi", r.status_code, 200)
aziz_id = r.json()["id"]
ck("sababsiz rad", add({"full_name": "Boshqa Odam", "phone": "901112299",
                        "category": "other", "reason": "x"}).status_code, 400)
ck("tanib bo'lmaydigan (bitta so'z, telefonsiz) rad",
   add({"full_name": "Aziz", "category": "other",
        "reason": "Sabab yetarli uzun"}).status_code, 400)
ck("noto'g'ri toifa rad", add({"full_name": "Boshqa Odam", "phone": "901112299",
                               "category": "zzz",
                               "reason": "Sabab yetarli uzun"}).status_code, 400)
ck("takror rad (boshqa yozilishdagi raqam)",
   add({"full_name": "A K", "phone": "901112233", "category": "other",
        "reason": "Takror yozuv"}).status_code, 400)
ck("filial rahbari qo'sha olmaydi",
   add({"full_name": "Boshqa Odam", "phone": "901112299", "category": "other",
        "reason": "Sabab yetarli uzun"}, h=BM).status_code, 403)
ck("filial rahbari ko'radi",
   c.get("/api/hr/blacklist", headers=BM).status_code, 200)
ck("ustoz ko'rolmaydi", c.get("/api/hr/blacklist", headers=T).status_code, 403)
r = add({"full_name": "Soliyeva  Nodira", "category": "fraud",
         "reason": "Soxta diplom topshirgan"})
ck("faqat ism bilan qo'shildi", r.status_code, 200)

print("\n=== NOMZODNI TANISH ===")
cid = new_cand("Aziz Karimov", "90 111 22 33")
lst = {x["id"]: x for x in c.get("/api/candidates", headers=HR).json()}
ck("ro'yxatda belgi", lst[cid]["blacklist"]["category"], "theft")
d = c.get(f"/api/candidates/{cid}", headers=HR).json()
ck("kartada sabab", d["blacklist"]["reason"], "Kassadan pul yo'qolgan")
other = new_cand("Karimov Aziz", "+998 93 555 44 33")
lst = {x["id"]: x for x in c.get("/api/candidates", headers=HR).json()}
ck("ismdosh, lekin boshqa telefon — belgisiz", lst[other]["blacklist"], None)
nod = new_cand("nodira SOLIYEVA", "+998 97 000 11 22")
lst = {x["id"]: x for x in c.get("/api/candidates", headers=HR).json()}
ck("faqat ism bilan yozilgan — telefonli nomzod ham tanildi",
   lst[nod]["blacklist"] is not None, True)
pipe = c.get("/api/ats/pipeline", headers=HR).json()
flags = {r["candidate_id"]: r["blacklist"] for r in pipe["rows"]}
ck("quvurda belgi", flags[cid] is not None, True)

print("\n=== ISHGA OLISH YOPIQ ===")
r = c.put(f"/api/candidates/{cid}", headers=HR, json={"stage": "hired"})
ck("kartadan ishga olib bo'lmaydi", r.status_code, 403)
ck("xabarda sabab", "Kassadan pul" in r.json()["detail"], True)
db.expire_all()
ck("bosqich o'zgarmadi", db.query(models.Candidate).get(cid).stage, "applied")
ck("hisob ochilmadi", db.query(models.User)
   .filter(models.User.username == "998901112233").count(), 0)
app = db.query(models.CandidateApplication).filter_by(candidate_id=cid).first()
r = c.post(f"/api/ats/applications/{app.id}/move", headers=HR,
           json={"stage": "hired"})
ck("quvurdan ishga olib bo'lmaydi", r.status_code, 403)
r = c.post(f"/api/ats/applications/{app.id}/move", headers=HR,
           json={"stage": "offer"})
ck("taklif bosqichiga ham o'tmaydi", r.status_code, 403)
r = c.post("/api/ats/applications/%d/move" % app.id, headers=HR,
           json={"stage": "rejected", "reason": "other"})
ck("rad etish mumkin", r.status_code, 200)
r = c.post("/api/users", headers=HR, json={
    "full_name": "Karimov Aziz", "role": "sales_manager",
    "phone": "+998901112233", "branch_id": b.id})
ck("xodim hisobini ochib bo'lmaydi", r.status_code, 403)
r = c.post("/api/users", headers=HR, json={
    "full_name": "Karimov Aziz", "role": "sales_manager",
    "phone": "+998935554433", "branch_id": b.id})
ck("ismdosh boshqa odamga hisob ochiladi", r.status_code, 200)
ok_cand = new_cand("Yangi Xodim", "+998 99 777 66 55")
r = c.put(f"/api/candidates/{ok_cand}", headers=HR, json={"stage": "hired"})
ck("oddiy nomzod ishga olinadi", r.status_code, 200)

print("\n=== BO'SHATILGAN XODIM VA USTOZ ===")
old = mk("eski", roles.TEACHER, "Eshonov Bobur", "+998 91 234 56 78", active=0)
r = add({"user_id": old.id, "category": "left_bad",
         "reason": "Guruhni tashlab ketgan"})
ck("xodim kartasidan qo'shildi", (r.status_code, r.json()["full_name"]),
   (200, "Eshonov Bobur"))
r = c.put(f"/api/users/{old.id}", headers=HR, json={"is_active": True})
ck("ishga qaytarib bo'lmaydi", r.status_code, 403)
tc = models.Teacher(full_name="Eshonov Bobur", phone="912345678",
                    branch_id=b.id, is_active=1)
db.add(tc); db.commit()
r = c.post(f"/api/teachers/{tc.id}/account", headers=HR, json={})
ck("ustozga akkaunt ochib bo'lmaydi", r.status_code, 403)
ck("asoschini qo'shib bo'lmaydi",
   add({"user_id": 1, "category": "other",
        "reason": "Sabab yetarli uzun"}).status_code, 400)

print("\n=== ONLAYN ARIZA ===")
# Qo'lda qo'shilgan nomzodlar "kecha" kiritilgan bo'lsin — aks holda
# onlayn ariza 24 soatlik "takror bosish" himoyasiga tushadi
from datetime import datetime as _dt, timedelta as _td
db.query(models.Candidate).update(
    {models.Candidate.created_at: _dt.utcnow() - _td(days=2)})
db.commit()
photo = "data:image/jpeg;base64," + "A" * 200
r = c.post("/api/apply", json={"full_name": "Karimov Aziz Olimovich",
                               "phone": "+998901112233", "position": "sales",
                               "photo": photo})
ck("ariza qabul qilinadi (odamga bildirilmaydi)", r.status_code, 200)
rows = c.get("/api/hr/blacklist", headers=HR).json()["rows"]
az = next(x for x in rows if x["id"] == aziz_id)
ck("qayta ariza topshirgani ko'rinadi",
   "Karimov Aziz Olimovich" in [x["full_name"] for x in az["applied_again"]],
   True)

print("\n=== CHIQARISH ===")
ck("filial rahbari chiqara olmaydi",
   c.post(f"/api/hr/blacklist/{aziz_id}/remove", headers=BM,
          json={"reason": "Kechirildi, qaytadi"}).status_code, 403)
ck("sababsiz chiqarib bo'lmaydi",
   c.post(f"/api/hr/blacklist/{aziz_id}/remove", headers=HR,
          json={"reason": ""}).status_code, 400)
r = c.post(f"/api/hr/blacklist/{aziz_id}/remove", headers=HR,
           json={"reason": "Zarar qoplandi, rahbar ruxsat berdi"})
ck("HR chiqardi", (r.status_code, r.json()["is_active"]), (200, False))
ck("faol ro'yxatda yo'q", aziz_id in [x["id"] for x in c.get(
    "/api/hr/blacklist", headers=HR).json()["rows"]], False)
ck("tarixda qoldi", aziz_id in [x["id"] for x in c.get(
    "/api/hr/blacklist?status=removed", headers=HR).json()["rows"]], True)
cid2 = new_cand("Aziz Karimov", "901112233")
r = c.put(f"/api/candidates/{cid2}", headers=HR, json={"stage": "hired"})
ck("chiqarilgandan keyin ishga olinadi", r.status_code, 200)

print()
if fails:
    print("XATOLAR:", fails)
    sys.exit(1)
print("HAMMASI O'TDI")
