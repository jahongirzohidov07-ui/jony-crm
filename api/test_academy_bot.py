"""JONY ACADEMY BOTI — JonyOS ichida webhook (2026-10-13).

Railway trial tugab bot o'chdi; endi bot jonyos.uz webhookida. Bu test
Telegram'ga bormaydi (TEST_MODE) va butun oqimni tekshiradi:
/start -> ism -> telefon -> sinf -> kurs -> filial -> tasdiqlash,
JonyOS lidi, sotuv guruhi xabari, holat tugmasi, takroriy raqam,
admin buyruqlari, noto'g'ri sir, kunlik hisobot.
"""
import os
import sys
import tempfile
from datetime import datetime

_DIR = os.path.join(tempfile.gettempdir(), "academy_bot_test")
os.makedirs(_DIR, exist_ok=True)
_DB = os.path.join(_DIR, "db.sqlite")
os.environ["DATABASE_URL"] = "sqlite:///" + _DB.replace(chr(92), "/")
os.environ["ACADEMY_BOT_TOKEN"] = "test-token-123"
os.environ["ACADEMY_SALES_GROUP_ID"] = "-100555"
os.environ["ACADEMY_ADMIN_IDS"] = "777"
if os.path.exists(_DB):
    os.remove(_DB)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient          # noqa: E402
import main, models, roles                         # noqa: E402
import academy_bot as ab                           # noqa: E402
from database import SessionLocal                  # noqa: E402

ab.TEST_MODE = True
c = TestClient(main.app)
fails = []


def ck(n, g, w):
    ok = g == w
    print(("OK  " if ok else "XATO ") + n + f": {g}"
          + ("" if ok else f" (kutilgan {w})"))
    if not ok:
        fails.append(n)


db = SessionLocal()
for nm in ("Bekobod 1", "Bekobod 2", "Zafar", "Stretinko"):
    db.add(models.Branch(name=nm))
db.commit()
db.close()

SEC = ab.webhook_secret()
URL = f"/api/tg/academy-bot/{SEC}"
H = {"X-Telegram-Bot-Api-Secret-Token": SEC}
USER = {"id": 5001, "first_name": "Ali", "username": "ali_test"}
CHAT = {"id": 5001, "type": "private"}
_mid = [100]


def msg(text=None, contact=None, chat=CHAT, user=USER):
    _mid[0] += 1
    m = {"message_id": _mid[0], "chat": chat, "from": user}
    if text is not None:
        m["text"] = text
    if contact:
        m["contact"] = contact
    return c.post(URL, json={"update_id": _mid[0], "message": m}, headers=H)


def cb(data, chat=CHAT, user=USER, mid=1):
    _mid[0] += 1
    return c.post(URL, headers=H, json={"update_id": _mid[0], "callback_query": {
        "id": str(_mid[0]), "data": data, "from": user,
        "message": {"message_id": mid, "chat": chat}}})


def last_text():
    for m, p in reversed(ab._SENT):
        if m in ("sendMessage", "editMessageText"):
            return p.get("text", "")
    return ""


print("=== Himoya ===")
ck("noto'g'ri sir — 404", c.post("/api/tg/academy-bot/xato", json={},
                                 headers=H).status_code, 404)
ck("sarlavhasiz — 404", c.post(URL, json={}).status_code, 404)

print("=== Ro'yxatdan o'tish ===")
ck("/start 200", msg("/start").status_code, 200)
ck("ism so'raladi", "to'liq ismingizni" in last_text(), True)
msg("Ali Valiyev")
ck("telefon so'raladi", "Telefon raqamingizni" in last_text(), True)
msg("12345")
ck("noto'g'ri raqam rad etiladi", "noto'g'ri formatda" in last_text(), True)
msg(contact={"phone_number": "998901112233", "user_id": 5001})
ck("sinf so'raladi", "nechanchi sinfda" in last_text(), True)
msg("7-sinf")
ck("kurs so'raladi", "kursga" in last_text(), True)
cb("course:Rus tili")
ck("filial so'raladi", "filialga" in last_text(), True)
cb("branch:Bekobod Shahar")
ck("tasdiqlash so'raladi", last_text(), "Yuqoridagi ma'lumotlar to'g'rimi?")
ab._SENT.clear()
msg("✅ Tasdiqlash")
texts = [p.get("text", "") for m, p in ab._SENT if m == "sendMessage"]
ck("foydalanuvchiga 'qabul qilindi'",
   any("muvaffaqiyatli qabul qilindi" in t for t in texts), True)
ck("filial kontakti yuborildi",
   any("+998772769777" in t for t in texts), True)
grp = [p for m, p in ab._SENT
       if m == "sendMessage" and p.get("chat_id") == "-100555"]
ck("sotuv guruhiga xabar", len(grp), 1)
ck("guruh xabarida tugmalar",
   bool(grp and grp[0].get("reply_markup", {}).get("inline_keyboard")), True)

db = SessionLocal()
reg = db.query(models.AcademyBotReg).first()
ck("murojaat saqlandi", (reg.name, reg.phone, reg.course, reg.branch),
   ("Ali Valiyev", "+998901112233", "Rus tili", "Bekobod Shahar"))
lead = db.query(models.Lead).get(reg.lead_id) if reg.lead_id else None
ck("JonyOS lidi ochildi", lead is not None, True)
b1 = db.query(models.Branch).filter(models.Branch.name == "Bekobod 1").first()
ck("lid manbasi telegram, Bekobod 1",
   (lead.source, lead.branch_id) if lead else None, ("telegram", b1.id))
ck("guruh xabar ID saqlandi", bool(reg.group_message_id), True)
RID = reg.id
db.close()

print("=== Holat tugmasi ===")
ab._SENT.clear()
cb(f"status:{RID}:called", chat={"id": -100555, "type": "supergroup"},
   user={"id": 9, "first_name": "Baxriniso"})
db = SessionLocal()
ck("holat o'zgardi", db.query(models.AcademyBotReg).get(RID).status,
   "called")
db.close()
ck("guruhga izoh", "Qo'ng'iroq qilindi" in last_text(), True)

print("=== Takroriy raqam ===")
U2 = {"id": 6002, "first_name": "Vali"}
C2 = {"id": 6002, "type": "private"}
msg("/start", chat=C2, user=U2)
msg("Vali", chat=C2, user=U2)
msg("+998 90 111 22 33", chat=C2, user=U2)
ck("takror rad etiladi", "allaqachon ro'yxatdan" in last_text(), True)

print("=== Admin buyruqlari ===")
msg("/stat")
ck("oddiy foydalanuvchiga /stat yopiq", "faqat adminlar" in last_text(), True)
A = {"id": 777, "first_name": "Admin"}
AC = {"id": 777, "type": "private"}
msg("/stat", chat=AC, user=A)
ck("adminga statistika", "Jami: <b>1</b>" in last_text(), True)
ab._SENT.clear()
msg("/royxat", chat=AC, user=A)
ck("adminga CSV", [m for m, _ in ab._SENT], ["sendDocument"])
msg("/broadcast", chat=AC, user=A)
ab._SENT.clear()
msg("Ertaga dars bor", chat=AC, user=A)
ck("broadcast yuborildi",
   any(p.get("chat_id") == "5001" for m, p in ab._SENT
       if m == "sendMessage"), True)
ab._SENT.clear()
msg("salom", chat={"id": -100555, "type": "supergroup"},
    user={"id": 9, "first_name": "B"})
ck("guruhdagi oddiy xabarga jim", ab._SENT, [])

print("=== Kunlik hisobot ===")
db = SessionLocal()
ck("20:00 dan boshqa vaqtda yubormaydi (force'siz)",
   ab.daily_report(db) if ab._now_local().hour != 20 else False, False)
ab._SENT.clear()
ck("force bilan yuboriladi", ab.daily_report(db, force=True), True)
ck("guruhga KUNLIK HISOBOT", "KUNLIK HISOBOT" in last_text(), True)
db.close()

print("=== Asoschi tokenni JonyOS'da o'zi ulaydi ===")
from auth import hash_password                     # noqa: E402
db = SessionLocal()
db.add_all([
    models.User(username="asos", full_name="Asoschi", role=roles.FOUNDER,
                password_hash=hash_password("x"), is_active=1),
    models.User(username="adm", full_name="Admin",
                role=roles.ADMINISTRATOR, password_hash=hash_password("x"),
                is_active=1),
])
db.commit()
db.close()


def hdr(u):
    return {"Authorization": "Bearer " + c.post(
        "/api/auth/login", json={"username": u, "password": "x"}
    ).json()["access_token"]}


FH, AH = hdr("asos"), hdr("adm")
NEWTOK = "123456789:" + "A" * 35
ck("admin ulay olmaydi", c.post("/api/tg/academy-bot-connect",
   json={"token": NEWTOK}, headers=AH).status_code, 403)
ck("noto'g'ri token rad", c.post("/api/tg/academy-bot-connect",
   json={"token": "salom"}, headers=FH).status_code, 400)
r = c.post("/api/tg/academy-bot-connect", json={"token": NEWTOK}, headers=FH)
ck("ulash 200", r.status_code, 200)
j = r.json()
ck("javobda token YO'Q", NEWTOK in r.text or "AAAAAAAAAA" in r.text, False)
ck("bot nomi", j.get("bot"), "test_academy_bot")
ck("guruh havolasi", (j.get("group_link") or "").startswith(
    "https://t.me/test_academy_bot?startgroup=g_"), True)
db = SessionLocal()
ck("token bazada", db.query(models.IntegrationSetting).get(
    ab.K_TOKEN).value, NEWTOK)
db.close()
ck("webhook o'rnatildi", any(m == "setWebhook" for m, _ in ab._SENT), True)

# Yangi token bilan sir o'zgaradi — eski manzil endi 404
SEC2 = ab.webhook_secret()
ck("sir yangilandi", SEC2 != SEC, True)
ck("eski sir 404", c.post(URL, json={}, headers=H).status_code, 404)
URL, H = f"/api/tg/academy-bot/{SEC2}", {"X-Telegram-Bot-Api-Secret-Token": SEC2}
CODE = j["group_link"].split("g_", 1)[1]

ab._SENT.clear()
msg("/start@test_academy_bot g_noto'g'ri",
    chat={"id": -100999, "type": "group"}, user={"id": 1, "first_name": "X"})
db = SessionLocal()
ck("noto'g'ri kod guruhni ulamaydi",
   (db.query(models.IntegrationSetting).get(ab.K_GROUP) or
    models.IntegrationSetting(value=None)).value, None)
db.close()
msg(f"/start@test_academy_bot g_{CODE}",
    chat={"id": -100999, "type": "group"}, user={"id": 1, "first_name": "X"})
ck("guruh ulandi xabari", "sotuv guruhi sifatida" in last_text(), True)
db = SessionLocal()
ck("guruh bazada", db.query(models.IntegrationSetting).get(
    ab.K_GROUP).value, "-100999")
db.close()
msg(None, chat={"id": -100999, "type": "group"},
    user={"id": 1, "first_name": "X"})
c.post(URL, headers=H, json={"update_id": 99999, "message": {
    "message_id": 1, "chat": {"id": -100999, "type": "group"},
    "from": {"id": 1}, "migrate_to_chat_id": -1001234}})
db = SessionLocal()
ck("supergroupga o'tsa ID yangilanadi", db.query(
    models.IntegrationSetting).get(ab.K_GROUP).value, "-1001234")
db.close()

U9, C9 = {"id": 4242, "first_name": "Jahongir"}, {"id": 4242, "type": "private"}
msg("/stat", chat=C9, user=U9)
ck("kodsiz admin emas", "faqat adminlar" in last_text(), True)
msg(f"/start a_{CODE}", chat=C9, user=U9)
ck("admin bo'ldi", "admini bo'ldingiz" in last_text(), True)
msg("/stat", chat=C9, user=U9)
ck("endi /stat ishlaydi", "Jami:" in last_text(), True)
st = c.get("/api/tg/academy-bot-status", headers=FH).json()
ck("holat: guruh va admin", (st["sales_group"], st["admins"] >= 2),
   (True, True))
ck("holatda token yo'q", "AAAAAAAAAA" in str(st), False)
old = st["group_link"]
st2 = c.post("/api/tg/academy-bot-new-code", headers=FH).json()
ck("yangi kod — havola o'zgardi", st2["group_link"] != old, True)

print()
print("XATOLAR:", fails if fails else "yo'q")
sys.exit(1 if fails else 0)
