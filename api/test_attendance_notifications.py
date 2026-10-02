"""Davomat: keldi/kech keldi/kelmadi haqida ota-onaga Telegram
xabarnomasi (2026-08-09, Jahongir so'radi: "darsga keldi degan
bildirishnoma, ustoz kech keldi deb belgilasa kech keldi degan
bildirishnoma kelsin").

MUHIM: haqiqiy Telegram tokensiz sinash uchun notify.enabled()/
notify.send() MOCK qilinadi (haqiqiy tarmoq so'rovi yubormaymiz) —
lekin haqiqiy jonli yo'lga (`import entry`, PUT
/api/lessons/{id}/attendance) so'rov yuboriladi, shuning uchun
entry.py'dagi ikkita ustma-ust "delegate" wrapper (save_attendance_v2)
orqali groups_lessons.py'dagi haqiqiy funksiyaga yetib borishini ham
tasdiqlaydi."""
import os, sys
from datetime import date

os.environ["DATABASE_URL"] = "sqlite:////tmp/verify_att_notif/db.sqlite"
os.makedirs("/tmp/verify_att_notif", exist_ok=True)
if os.path.exists("/tmp/verify_att_notif/db.sqlite"):
    os.remove("/tmp/verify_att_notif/db.sqlite")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
import main, models, notify
import entry  # noqa: F401 - haqiqiy jonli yo'lni ro'yxatdan o'tkazadi
from database import SessionLocal
import common as _cm_stub                           # noqa: E402
# Login oylik yechimni ishga tushiradi (auth_users -> common, 2026-10-02
# dan beri to'g'ri ulangan). Bu test unga bog'liq emas — o'chiramiz.
_cm_stub._ensure_month_charges = lambda db, **kw: None
from auth import hash_password

client = TestClient(main.app)
fails = []


def ck(name, got, want):
    ok = got == want
    print(("OK  " if ok else "XATO ") + name + f": {got}"
          + ("" if ok else f"   (kutilgan {want})"))
    if not ok:
        fails.append(name)


# --- Mock: notify.enabled() -> True, notify.send() -> ro'yxatga yozadi ---
sent = []
notify.enabled = lambda: True
notify.send = lambda chat_id, text: sent.append((chat_id, text)) or True

db = SessionLocal()
b = models.Branch(name="Zafar")
db.add(b)
db.commit()

admin = models.User(username="dir1", full_name="Direktor",
                    password_hash=hash_password("x"), role="founder",
                    branch_id=b.id, is_active=1)
db.add(admin)
db.commit()

user_t = models.User(username="ust2", full_name="Ustoz Malika",
                     password_hash=hash_password("x"), role="teacher",
                     branch_id=b.id, is_active=1)
db.add(user_t)
db.commit()
teacher = models.Teacher(full_name="Ustoz Malika", branch_id=b.id,
                         user_id=user_t.id, is_active=1)
db.add(teacher)
db.commit()

g = models.Group(name="CEFR-2", subject="english", level="A2",
                 branch_id=b.id, teacher_id=teacher.id,
                 lesson_time="10:00", monthly_fee=400000,
                 lesson_days="246", capacity=12)
db.add(g)
db.commit()

today = date.today()


def mk_student(name, tag):
    s = models.Student(full_name=name, branch_id=b.id, group_id=g.id,
                       status="active", enrolled_date=today,
                       parent_token=f"tok-{tag}-" + "x" * 12,
                       public_id=f"STU-ATT-{tag}",
                       telegram_chat_id=f"chat-{tag}")
    db.add(s)
    db.commit()
    return s


s_a = mk_student("Ali Vositov", "a")   # keladi
s_b = mk_student("Bekzod Nortov", "b")  # kech keladi
s_c = mk_student("Cho'lpon Rayimova", "c")  # kelmaydi

ls = models.Lesson(group_id=g.id, date=today, teacher_id=user_t.id, held=0)
db.add(ls)
db.commit()


def login():
    r = client.post("/api/auth/login",
                    json={"username": "dir1", "password": "x"})
    return r.json()["access_token"]


tok = login()
H = {"Authorization": f"Bearer {tok}"}

print("=== BIRINCHI BELGILASH (hammasi YANGI — 3 ta xabar kutiladi) ===")
r = client.put(
    f"/api/lessons/{ls.id}/attendance",
    headers=H,
    json={"marks": [
        {"student_id": s_a.id, "present": True, "late": False},
        {"student_id": s_b.id, "present": True, "late": True},
        {"student_id": s_c.id, "present": False, "late": False},
    ]},
)
ck("status 200", r.status_code, 200)
ck("3 ta xabar yuborildi", len(sent), 3)

by_chat = {c: t for c, t in sent}
ck("Ali uchun 'keldi' xabari", "darsiga keldi" in by_chat.get("chat-a", ""),
   True)
ck("Bekzod uchun 'kech keldi' xabari",
   "kech keldi" in by_chat.get("chat-b", ""), True)
ck("Cho'lpon uchun 'kelmadi' xabari",
   "kelmadi" in by_chat.get("chat-c", ""), True)

print("\n=== IKKINCHI MARTA XUDDI SHU BELGILAR (0 ta YANGI xabar kutiladi) ===")
sent.clear()
r2 = client.put(
    f"/api/lessons/{ls.id}/attendance",
    headers=H,
    json={"marks": [
        {"student_id": s_a.id, "present": True, "late": False},
        {"student_id": s_b.id, "present": True, "late": True},
        {"student_id": s_c.id, "present": False, "late": False},
    ]},
)
ck("status 200 (takror)", r2.status_code, 200)
ck("o'zgarmagan belgilar uchun qayta xabar YO'Q", len(sent), 0)

print("\n=== CHO'LPON ENDI KELDI DEB TUZATILDI (faqat 1 ta YANGI xabar) ===")
sent.clear()
r3 = client.put(
    f"/api/lessons/{ls.id}/attendance",
    headers=H,
    json={"marks": [
        {"student_id": s_a.id, "present": True, "late": False},
        {"student_id": s_b.id, "present": True, "late": True},
        {"student_id": s_c.id, "present": True, "late": False},
    ]},
)
ck("status 200 (tuzatish)", r3.status_code, 200)
ck("faqat o'zgargan (Cho'lpon) uchun xabar", len(sent), 1)
ck("xabar aynan Cho'lponga (chat-c)", sent[0][0] if sent else None, "chat-c")
ck("yangi xabar 'keldi' matnida", "darsiga keldi" in sent[0][1] if sent else
   False, True)

print("\n" + ("BARCHASI OK" if not fails else f"XATOLAR: {fails}"))
sys.exit(1 if fails else 0)
