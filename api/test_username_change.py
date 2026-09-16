"""LOGINNI O'ZGARTIRISH (2026-09-16, Jahongir: "loginni ham har bir xodim
va HR edit qila olsin, hozir faqat parol o'zgartirishga ruxsat bor").

Tekshiriladi:
  - xodim o'z loginini joriy parol bilan almashtiradi va yangi token oladi
    (token ichida login turadi — eskisi endi ishlamaydi);
  - HR xodim kartasidan loginni almashtiradi, lekin asoschi va filial
    rahbarinikini emas (parol bilan bir xil himoya);
  - login qoidasi va bandlik (katta-kichik harf farqsiz)."""
import os, sys, tempfile

_tmp = tempfile.mkdtemp(prefix="jony_login_")
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


def mk(username, role):
    u = models.User(username=username, full_name=username.title(),
                    password_hash=hash_password(PW), role=role,
                    branch_id=b.id, is_active=1)
    db.add(u); db.commit()
    return u


def login(username, pw=PW):
    return c.post("/api/auth/login",
                  json={"username": username, "password": pw})


def H(tok):
    return {"Authorization": f"Bearer {tok}"}


founder = mk("asoschi", roles.FOUNDER)
hr = mk("hr", roles.HR_MANAGER)
bm = mk("rahbar", roles.BRANCH_MANAGER)
hs = mk("supboshliq", roles.HEAD_SUPPORT)
t = mk("ustoz", roles.TEACHER)
sup = mk("sup", roles.SUPPORT_TEACHER)
adm = mk("admin1", roles.ADMINISTRATOR)
stu = mk("oquvchi", roles.STUDENT)

print("=== XODIM O'Z LOGINI ===")
old_tok = login("ustoz").json()["access_token"]


def self_change(tok, new, pw=PW):
    return c.put("/api/auth/me/username", headers=H(tok),
                 json={"current_password": pw, "new_username": new})


ck("noto'g'ri parol", self_change(old_tok, "ustoz_new", "xato123").status_code, 400)
ck("probel bilan rad", self_change(old_tok, "ustoz new").status_code, 400)
ck("juda qisqa rad", self_change(old_tok, "ab").status_code, 400)
ck("kirill rad", self_change(old_tok, "устоз").status_code, 400)
ck("band (katta harf bilan ham)", self_change(old_tok, "HR").status_code, 400)
ck("eskisi bilan bir xil", self_change(old_tok, "ustoz").status_code, 400)
r = self_change(old_tok, "Anvar.Ustoz")
ck("almashtirildi", r.status_code, 200)
new_tok = r.json()["access_token"]
ck("eski token endi ishlamaydi",
   c.get("/api/auth/me", headers=H(old_tok)).status_code, 401)
ck("yangi token ishlaydi",
   c.get("/api/auth/me", headers=H(new_tok)).json()["username"], "Anvar.Ustoz")
ck("eski login bilan kirib bo'lmaydi", login("ustoz").status_code, 401)
ck("yangi login bilan kiradi", login("Anvar.Ustoz").status_code, 200)
ck("raqamli login ham mumkin",
   self_change(login("admin1").json()["access_token"], "901234567")
   .status_code, 200)
ck("o'quvchi o'zgartira olmaydi",
   self_change(login("oquvchi").json()["access_token"], "oquvchi2")
   .status_code, 403)
db.expire_all()
ck("tarixga yozildi", db.query(models.AuditLog)
   .filter(models.AuditLog.entity == "user",
           models.AuditLog.field == "username",
           models.AuditLog.new_value == "Anvar.Ustoz").count() >= 1, True)

print("\n=== HR XODIM KARTASIDAN ===")
Hhr = H(login("hr").json()["access_token"])


def upd(h, uid, **body):
    return c.put(f"/api/users/{uid}", headers=h, json=body)


r = upd(Hhr, t.id, username="anvar")
ck("HR ustoz loginini o'zgartirdi", r.status_code, 200)
ck("javobda yangi login", r.json()["username"], "anvar")
ck("yangi login bilan kiradi", login("anvar").status_code, 200)
ck("HR band loginni berolmaydi", upd(Hhr, t.id, username="SUP").status_code, 400)
ck("HR noto'g'ri loginni berolmaydi",
   upd(Hhr, t.id, username="a b").status_code, 400)
ck("o'sha login qayta yuborilsa — o'zgarishsiz",
   upd(Hhr, t.id, username="anvar", phone="+998901112233").status_code, 200)
ck("HR asoschi loginiga tegolmaydi",
   upd(Hhr, founder.id, username="boss").status_code, 403)
ck("HR filial rahbari loginiga tegolmaydi",
   upd(Hhr, bm.id, username="rahbar2").status_code, 403)
r = upd(Hhr, hr.id, username="hr.menejer")
ck("HR o'z loginini kartadan ham o'zgartiradi", r.status_code, 200)
nt = r.headers.get("X-New-Token")
ck("javob sarlavhasida yangi token", bool(nt), True)
ck("eski token endi ishlamaydi",
   c.get("/api/auth/me", headers=Hhr).status_code, 401)
Hhr = H(nt)
ck("yangi token ishlaydi",
   c.get("/api/auth/me", headers=Hhr).json()["username"], "hr.menejer")
r = upd(Hhr, t.id, username="anvar.u")
ck("boshqa xodimda yangi token berilmaydi",
   (r.status_code, r.headers.get("X-New-Token")), (200, None))
r = upd(Hhr, t.id, username="anvar")

print("\n=== XAVFSIZLIK ===")
ck("demo. loginini berib bo'lmaydi (demo tozalashda o'chardi)",
   upd(Hhr, t.id, username="Demo.anvar").status_code, 400)
ck("o'quvchi loginini kartadan o'zgartirib bo'lmaydi",
   upd(Hhr, stu.id, username="oquvchi_yangi").status_code, 403)

print("\n=== BOG'LANGAN MA'LUMOTLAR O'ZGARMAYDI ===")
# Oylik, natija, davomat — hammasi user_id orqali. Login almashsa ham
# o'sha yozuvlar o'sha odamda qoladi.
tc = models.Teacher(full_name="Anvar", branch_id=b.id, user_id=t.id,
                    is_active=1)
db.add(tc); db.commit()
db.add(models.SupportAdjustment(user_id=t.id, points=3, reason="test"))
db.add(models.ConductViolation(user_id=t.id, date=roles.local_today(),
                               kind="late"))
db.commit()
ck("login almashdi", upd(Hhr, t.id, username="anvar.oxirgi").status_code, 200)
db.expire_all()
ck("ustoz kartasi o'sha xodimda",
   db.query(models.Teacher).get(tc.id).user_id, t.id)
ck("jarima o'sha xodimda", db.query(models.SupportAdjustment)
   .filter_by(user_id=t.id).count(), 1)
ck("intizom yozuvi o'sha xodimda", db.query(models.ConductViolation)
   .filter_by(user_id=t.id).count(), 1)

print("\n=== BOSHQA ROLLAR ===")
Hf = H(login("asoschi").json()["access_token"])
ck("asoschi filial rahbari loginini o'zgartiradi",
   upd(Hf, bm.id, username="rahbar_bek").status_code, 200)
Hhs = H(login("supboshliq").json()["access_token"])
ck("support rahbari support loginini o'zgartiradi",
   upd(Hhs, sup.id, username="sup_aziza").status_code, 200)
ck("support rahbari ustoz loginiga tegolmaydi",
   upd(Hhs, t.id, username="anvar3").status_code, 403)
Ht = H(login("anvar.oxirgi").json()["access_token"])
ck("ustoz boshqa xodim loginiga tegolmaydi",
   upd(Ht, sup.id, username="xx_yy").status_code, 403)

print()
if fails:
    print("XATOLAR:", fails)
    sys.exit(1)
print("HAMMASI O'TDI")
