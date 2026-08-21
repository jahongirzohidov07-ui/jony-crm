"""ADAPTIV DARAJA TESTI (2026-08-21).

Jahongir: "darajasini aniqlaydigan chuqur bir test qoshaylik...
togri topsa qiyinlashib ketaveradi, topolmasa osha darajadan berib
koradi yana topolmasa pastroq... Grammar, Vocabular, Reading,
Listeningdan aniqlashi kerak."

Tekshiriladi: to'g'ri javobda daraja ko'tarilishi, 2 xatoda pastga
tushish, to'g'ri javob mijozga oldindan yuborilmasligi, 4 bo'lim
yakunida natija saqlangani, XP_PER_LEVEL 2x bo'lgani va maqsad
muddati 4x cho'zilgani."""
import os, sys

os.environ["DATABASE_URL"] = "sqlite:////tmp/verify_lt/db.sqlite"
os.makedirs("/tmp/verify_lt", exist_ok=True)
if os.path.exists("/tmp/verify_lt/db.sqlite"):
    os.remove("/tmp/verify_lt/db.sqlite")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import json
from fastapi.testclient import TestClient
import main, models, roles
import entry  # noqa: F401
import level_test
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


b = models.Branch(name="Zafar"); db.add(b); db.commit()
s = models.Student(full_name="Test Talaba", branch_id=b.id,
                   status="active", phone="998901112299",
                   public_id="STU-LT-1")
db.add(s); db.commit()
u = models.User(username="998901112299",
                password_hash=hash_password("jonyjony"),
                full_name="Test Talaba", role=roles.STUDENT,
                branch_id=b.id, is_active=1)
db.add(u); db.commit()
s.user_id = u.id; db.commit()
H = {"Authorization": f"Bearer {c.post('/api/auth/login', json={'username':'998901112299','password':'jonyjony'}).json()['access_token']}"}


def answer_of(sess_row):
    st = json.loads(sess_row.state)
    return st["cur"]["answer"], st


def cur_sess():
    return (db.query(models.LevelTestSession)
            .filter(models.LevelTestSession.status == "active")
            .order_by(models.LevelTestSession.id.desc()).first())


print("=== BOSHLASH ===")
r = c.post("/api/student/level-test/start", headers=H)
ck("status 200", r.status_code, 200)
q = r.json()
ck("grammar bo'limidan boshlanadi", q["section"], "grammar")
ck("javob mijozga yuborilmaydi", "answer" in q["question"], False)
ck("variantlar bor", len(q["question"]["options"]) >= 3, True)

print("\n=== ADAPTIV: 3 TO'G'RI -> DARAJA YUTILADI ===")
db.expire_all()
ans, st0 = answer_of(cur_sess())
ck("A2 dan boshlangan", st0["idx"], 1)
r = c.post("/api/student/level-test/answer", headers=H,
           json={"answer": ans})
ck("to'g'ri deb topildi", r.json()["correct"], True)
db.expire_all()
_, st1 = answer_of(cur_sess())
ck("1 to'g'ri hali yetmaydi (o'sha daraja)", st1["idx"], 1)
ck("blok hisobi yuribdi", st1["lvl_ok"], 1)
for _ in range(2):  # jami 3 to'g'ri
    db.expire_all()
    ans, _ = answer_of(cur_sess())
    c.post("/api/student/level-test/answer", headers=H,
           json={"answer": ans})
db.expire_all()
_, st2 = answer_of(cur_sess())
ck("3 to'g'ridan keyin daraja ko'tarildi (B1)", st2["idx"], 2)
ck("blok qayta boshlandi", (st2["lvl_ok"], st2["lvl_bad"]), (0, 0))

print("\n=== ADAPTIV: 2 XATO -> PASTGA ===")
r = c.post("/api/student/level-test/answer", headers=H,
           json={"answer": "###notogri###"})
ck("xato deb topildi", r.json()["correct"], False)
ck("to'g'ri javob endi ko'rsatiladi",
   bool(r.json().get("expected")), True)
db.expire_all()
_, st3 = answer_of(cur_sess())
ck("1 xato hali yiqitmaydi", st3["idx"], 2)
r = c.post("/api/student/level-test/answer", headers=H,
           json={"answer": "###notogri###"})
db.expire_all()
sess = cur_sess()
# A2 yutilgan edi -> pastga tushishda bo'lim tugashi kerak
st4 = json.loads(sess.state)
ck("grammar yakunlandi, keyingi bo'lim", st4["sec_i"], 1)
ck("grammar natijasi A2", st4["results"]["grammar"], "A2")

print("\n=== QOLGAN BO'LIMLARNI O'TISH ===")
guard = 0
while guard < 400:
    guard += 1
    db.expire_all()
    sess = cur_sess()
    if not sess:
        break
    st = json.loads(sess.state)
    if not st.get("cur"):
        break
    r = c.post("/api/student/level-test/answer", headers=H,
               json={"answer": st["cur"]["answer"]})
    j = r.json()
    if j.get("done"):
        final = j
        break
ck("test yakunlandi", j.get("done"), True)
ck("grammar A2 qoldi", final["grammar"], "A2")
ck("vocabulary aniqlangan", final["vocabulary"] in
   ("A1", "A2", "B1", "B2"), True)
ck("reading aniqlangan", final["reading"] in ("A1", "A2", "B1"), True)
ck("listening aniqlangan", final["listening"] in
   ("A1", "A2", "B1", "B2"), True)
ck("umumiy daraja bor", final["overall"] in
   ("A1", "A2", "B1", "B2"), True)
ck("hammasini topgan -> vocab eng tepada", final["vocabulary"], "B2")

res = (db.query(models.LevelTestResult).order_by(
    models.LevelTestResult.id.desc()).first())
ck("natija bazada saqlandi", res is not None, True)
ck("bazadagi umumiy = javobdagi", res.overall_level, final["overall"])

print("\n=== STATUS ===")
r = c.get("/api/student/level-test/status", headers=H)
ck("faol test yo'q", r.json()["active"], False)
ck("oxirgi natija qaytadi", r.json()["overall"], final["overall"])

print("\n=== XP 2X VA MAQSAD 4X ===")
ck("XP_PER_LEVEL endi 200", roles.XP_PER_LEVEL, 200)
import inspect
src = inspect.getsource(sys.modules["student_app"])
ck("maqsad muddati 4x cho'zilgan", "hours_left *= 4.0" in src, True)
ck("bo'lim shifti 36 savol", level_test.MAX_PER_SECTION, 36)

print("\n=== XAVFSIZLIK ===")
r = c.post("/api/student/level-test/start")
ck("loginsiz yopiq", r.status_code in (401, 403), True)

print()
if fails:
    print("XATOLAR:", fails)
    sys.exit(1)
print("BARCHASI OK")
