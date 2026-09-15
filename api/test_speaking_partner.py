"""JONY TEACHER — AI SPEAKING PARTNER (2026-08-18).

Jahongir: "practice uchun AI speaking partner qoshish kerak savollar
bersa, savol berib koproq oquvchini gapirtiradigan Jony Teacher nomi
bilan".

AI'ning o'zi testda chaqirilmaydi (tashqi xizmat) — _ai_reply
almashtiriladi. Tekshiriladigani BIZNING qoidalar:
  - faqat o'quvchi kira oladi;
  - kalit yo'q bo'lsa tushunarli 503 (ilova yiqilmaydi);
  - XP: mazmunli javobga +1, "hi" ga berilmaydi, kunlik chegara 10;
  - tarix tozalanadi (20 tadan ortig'i va 500 belgidan uzuni kesiladi);
  - suhbat boshida Teacher o'zi savol bilan boshlaydi.
"""
import os, sys
import tempfile
from pathlib import Path
_temp = tempfile.TemporaryDirectory(prefix="jony-speaking-")
os.environ["DATABASE_URL"] = "sqlite:///" + str(Path(_temp.name) / "test.db").replace("\\", "/")
for key in ("OPENAI_API_KEY", "GEMINI_API_KEY", "JonyTeacher", "JONYTEACHER"):
    os.environ.pop(key, None)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fastapi.testclient import TestClient          # noqa: E402
import main, models, roles                         # noqa: E402
import entry                                       # noqa: E402
import student_app                                 # noqa: E402
from database import SessionLocal                  # noqa: E402
from auth import hash_password                     # noqa: E402

c = TestClient(main.app)
fails = []


def ck(n, g, w):
    ok = g == w
    print(("OK  " if ok else "MUAMMO ") + n + f": {g}"
          + ("" if ok else f" (kutilgan {w})"))
    if not ok:
        fails.append(n)


db = SessionLocal()
b = models.Branch(name="Bekobod 2"); db.add(b); db.commit()
s = models.Student(full_name="Abduvalieva Munisa", phone="998940411480",
                   branch_id=b.id, status="active")
db.add(s); db.commit(); SID = s.id
su = models.User(username="stu", full_name="Munisa",
                 password_hash=hash_password("x"), role=roles.STUDENT,
                 branch_id=b.id)
db.add(su); db.commit()
s.user_id = su.id
db.add(models.User(username="asos", full_name="Asoschi",
                   password_hash=hash_password("x"), role=roles.FOUNDER,
                   branch_id=b.id))
db.commit(); db.close()


def tok(u):
    return c.post("/api/auth/login",
                  json={"username": u, "password": "x"}).json()["access_token"]


ST = {"Authorization": f"Bearer {tok('stu')}"}
AS = {"Authorization": f"Bearer {tok('asos')}"}

# ---------------------------------------------------------------- 1
print("\n=== 1. Kalit yo'q — tushunarli 503 ===")
r = c.post("/api/student/speaking", headers=ST,
           json={"topic": "School", "messages": []})
ck("503 qaytdi", r.status_code, 503)
ck("xabari tushunarli", "ulanmagan" in r.json().get("detail", ""), True)

# ---------------------------------------------------------------- 2
print("\n=== 2. AI o'rniga soxta javob ulaymiz ===")
seen = {}


def fake_ai(system, messages):
    seen["system"] = system
    seen["messages"] = messages
    return "Nice! What is your favourite lesson at school?"


student_app._ai_reply = fake_ai

r = c.post("/api/student/speaking", headers=ST,
           json={"topic": "School", "messages": []})
ck("ishladi", r.status_code, 200)
j = r.json()
ck("javob keldi", "favourite lesson" in j["reply"], True)
ck("suhbat boshi — XP yo'q", j["xp_given"], 0)
ck("promptda Jony Teacher bor", "Jony Teacher" in seen["system"], True)
ck("promptda mavzu bor", "School" in seen["system"], True)
ck("boshlanish ko'rsatmasi ketdi",
   "just opened the chat" in seen["messages"][0]["text"], True)

# ---------------------------------------------------------------- 3
print("\n=== 3. Mazmunli javob +1 XP, 'hi' ga XP yo'q ===")
hist = [{"role": "teacher", "text": "What is your favourite lesson?"},
        {"role": "student", "text": "My favourite lesson is English"}]
r = c.post("/api/student/speaking", headers=ST,
           json={"topic": "School", "messages": hist}).json()
ck("+1 XP berildi", r["xp_given"], 1)
ck("bugungi hisob 1", r["xp_today"], 1)

r = c.post("/api/student/speaking", headers=ST,
           json={"topic": "School",
                 "messages": hist + [
                     {"role": "teacher", "text": r["reply"]},
                     {"role": "student", "text": "hi"}]}).json()
ck("bitta so'zga XP yo'q", r["xp_given"], 0)
ck("hisob 1 ligicha", r["xp_today"], 1)

# ---------------------------------------------------------------- 4
print("\n=== 4. Kunlik chegara 10 XP ===")
base = list(hist)
for i in range(12):
    base += [{"role": "teacher", "text": f"Q{i}?"},
             {"role": "student", "text": f"That is my answer number {i}"}]
    r = c.post("/api/student/speaking", headers=ST,
               json={"topic": "School", "messages": base}).json()
ck("chegaradan oshmadi", r["xp_today"], 10)
db = SessionLocal()
tot = (db.query(models.XpTransaction)
       .filter(models.XpTransaction.student_id == SID,
               models.XpTransaction.source_type == "speaking").count())
ck("bazada ham 10 ta yozuv", tot, 10)
db.close()

# ---------------------------------------------------------------- 5
print("\n=== 5. Tarix tozalanadi ===")
long_hist = [{"role": "student", "text": "x" * 2000}] * 40
r = c.post("/api/student/speaking", headers=ST,
           json={"topic": "School", "messages": long_hist})
ck("yiqilmadi", r.status_code, 200)
ck("20 tadan oshmadi", len(seen["messages"]) <= 20, True)
ck("500 belgidan uzuni kesildi",
   max(len(m["text"]) for m in seen["messages"]) <= 500, True)

# ---------------------------------------------------------------- 6
print("\n=== 6. O'quvchi bo'lmagan kira olmaydi ===")
r = c.post("/api/student/speaking", headers=AS,
           json={"topic": "School", "messages": []})
ck("asoschiga yopiq (bu bola ekrani)", r.status_code, 403)

print("\n" + ("HAMMASI JOYIDA" if not fails
              else f"MUAMMO: {len(fails)} ta -> {fails}"))
from database import engine
engine.dispose()
_temp.cleanup()
sys.exit(1 if fails else 0)
