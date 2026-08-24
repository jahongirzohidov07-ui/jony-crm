"""IELTS LISTENING: SPELLING / RAQAM / ARALASH (2026-08-24).

Jahongir: "Listening bo'limda birinchi spelling names bo'lsin, har
xil britaniya shaxarlari kochalar nomlari, british odamlarni
ismlarini yozish bo'lsin spelling mashqlar 50ta kamida, keyin 50ta
number practice... 3-mash spelling mixed koproq postcodelar harf va
son aralsh ham 50ta... hammasi sekinidan boshlab qiyinlashib borsin
va tezlashib borsin".
"""
import os, sys, json

os.environ["DATABASE_URL"] = "sqlite:////tmp/verify_iel/db.sqlite"
os.makedirs("/tmp/verify_iel", exist_ok=True)
if os.path.exists("/tmp/verify_iel/db.sqlite"):
    os.remove("/tmp/verify_iel/db.sqlite")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

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


b = models.Branch(name="Zafar"); db.add(b); db.commit()
st = models.Student(full_name="Test O'quvchi", branch_id=b.id,
                    status="active")
db.add(st); db.commit()
u = models.User(username="stud", full_name="Test O'quvchi",
                password_hash=hash_password("Parol123!"),
                role=roles.STUDENT, branch_id=b.id, is_active=1)
db.add(u); db.commit()
st.user_id = u.id; db.commit()
tok = c.post("/api/auth/login",
             json={"username": "stud", "password": "Parol123!"}
             ).json()["access_token"]
H = {"Authorization": f"Bearer {tok}"}

print("=== 1. HAR MASHQDA 50 DAN KO'P ELEMENT ===")
r = c.get("/api/student/ielts/listening/parts", headers=H)
ck("status 200", r.status_code, 200)
parts = {p["kind"]: p for p in r.json()["parts"]}
# 2026-08-24: 4- va 5-mashq qo'shildi (ma'lumot ilib olish,
# chalg'ituvchi javoblar) - endi beshta.
# 2026-08-24: 6-mashq — exact word trap (A/B/C)
ck("oltita mashq", len(parts), 6)
ck("tartib: spelling birinchi", parts["ielts_spell"]["no"], 1)
ck("tartib: raqam ikkinchi", parts["ielts_number"]["no"], 2)
ck("tartib: aralash uchinchi", parts["ielts_mixed"]["no"], 3)
for k in ("ielts_spell", "ielts_number", "ielts_mixed"):
    ck(f"{k}: 50+ mashq ({parts[k]['total']})",
       parts[k]["total"] >= 50, True)

print("\n=== 2. OSONDAN QIYINGA, SEKINDAN TEZGA ===")
r = c.get("/api/student/ielts/listening/round"
          "?kind=ielts_spell&count=50", headers=H)
items = r.json()["items"]
ck("50 ta keldi", len(items), 50)
steps = [x["step"] for x in items]
ck("bosqichlar kamaymaydi (osondan qiyinga)",
   steps == sorted(steps), True)
rates = [x["rate"] for x in items]
ck("tezlik ham kamaymaydi", rates == sorted(rates), True)
ck("birinchisi sekin", rates[0] <= 0.6, True)
ck("oxirgisi imtihon tezligida", rates[-1] >= 0.95, True)
ck("javob mijozga KETMAYDI",
   any("answer" in x or "expected" in x for x in items), False)

print("\n=== 3. KONTENT MAZMUNI ===")
sp = [x["say"] for x in items]
ck("harflab aytiladi (vergul bilan)", "," in sp[0], True)
ck("bo'sh joy 'space' deb aytiladi",
   any("space" in x for x in sp), True)
r = c.get("/api/student/ielts/listening/round"
          "?kind=ielts_number&count=50", headers=H)
nitems = r.json()["items"]
hints = {x["hint"] for x in nitems}
ck("telefon raqami bor", "Telefon raqami" in hints, True)
ck("karta raqami bor", "Bank kartasi raqami" in hints, True)
r = c.get("/api/student/ielts/listening/round"
          "?kind=ielts_mixed&count=50", headers=H)
mitems = r.json()["items"]
ck("aralashda postcode izohi",
   any("Postcode" in (x["hint"] or "") for x in mitems), True)

print("\n=== 4. JAVOB TEKSHIRUVI ===")
ref = items[0]["ref"]
pid = int(ref.split(":")[1])
right = db.query(models.PracticeItem).get(pid).answer
r = c.post("/api/student/ielts/listening/answer", headers=H,
           json={"ref": ref, "answer": right})
ck("to'g'ri javob qabul qilindi", r.json()["correct"], True)
ck("XP berildi", r.json()["xp"] > 0, True)
# registr va bo'sh joy farq qilmasin
ref2 = mitems[0]["ref"]
right2 = db.query(models.PracticeItem).get(
    int(ref2.split(":")[1])).answer
r = c.post("/api/student/ielts/listening/answer", headers=H,
           json={"ref": ref2, "answer": right2.lower().replace(" ", "")})
ck("kichik harf va bo'sh joysiz ham to'g'ri",
   r.json()["correct"], True)
r = c.post("/api/student/ielts/listening/answer", headers=H,
           json={"ref": ref, "answer": "ZZZZZ"})
ck("xato javob rad etildi", r.json()["correct"], False)
ck("to'g'ri javob ko'rsatildi", r.json()["expected"], right)
r = c.post("/api/student/ielts/listening/answer", headers=H,
           json={"ref": ref, "answer": "   "})
ck("bo'sh javob to'g'ri emas", r.json()["correct"], False)

print("\n=== 5. BALL LISTENING KO'NIKMASIGA TUSHDI ===")
n = (db.query(models.SkillAttempt)
     .filter(models.SkillAttempt.student_id == st.id,
             models.SkillAttempt.skill == "listening").count())
ck("urinishlar yozildi", n >= 4, True)
r = c.get("/api/student/skills", headers=H)
sk = {x["key"]: x["points"] for x in r.json()["skills"]}
ck("listening balli o'sdi", sk["listening"] >= 2, True)

print("\n=== 6. YECHILGANLAR ORQAGA SURILADI ===")
r = c.get("/api/student/ielts/listening/parts", headers=H)
p2 = {p["kind"]: p for p in r.json()["parts"]}
ck("bajarilgani sanoqda", p2["ielts_spell"]["solved"] >= 1, True)
r = c.get("/api/student/ielts/listening/round"
          "?kind=ielts_spell&count=5", headers=H)
ck("yechilgan element endi birinchi emas",
   r.json()["items"][0]["ref"] == ref, False)

print("\n=== 7. XAVFSIZLIK VA CHEGARALAR ===")
r = c.get("/api/student/ielts/listening/round?kind=xxx", headers=H)
ck("noma'lum mashq 404", r.status_code, 404)
r = c.post("/api/student/ielts/listening/answer", headers=H,
           json={"ref": "pi:999999", "answer": "X"})
ck("yo'q element 404", r.status_code, 404)
# oddiy listening mashqi IELTS javobiga o'tmasin
other = (db.query(models.PracticeItem)
         .filter(models.PracticeItem.skill == "listening").first())
if other:
    r = c.post("/api/student/ielts/listening/answer", headers=H,
               json={"ref": f"pi:{other.id}", "answer": "X"})
    ck("boshqa bo'lim mashqi qabul qilinmaydi", r.status_code, 404)
r = c.get("/api/student/ielts/listening/round?kind=ielts_spell")
ck("loginsiz yopiq", r.status_code in (401, 403), True)
r = c.get("/api/student/ielts/listening/round"
          "?kind=ielts_spell&count=999", headers=H)
ck("count cheklangan", len(r.json()["items"]) <= 60, True)


print("\n=== 9. 4- VA 5-MASHQ (2026-08-24) ===")
r = c.get("/api/student/ielts/listening/parts", headers=H)
parts = {p["kind"]: p for p in r.json()["parts"]}
ck("endi 6 ta mashq", len(parts), 6)
ck("4-mashq: ma'lumot ilib olish", parts["ielts_detail"]["no"], 4)
ck("5-mashq: chalg'ituvchi javoblar", parts["ielts_trap"]["no"], 5)
ck(f"detail 100 ta ({parts['ielts_detail']['total']})",
   parts["ielts_detail"]["total"] >= 100, True)
ck(f"trap 100 ta ({parts['ielts_trap']['total']})",
   parts["ielts_trap"]["total"] >= 100, True)

r = c.get("/api/student/ielts/listening/round"
          "?kind=ielts_detail&count=60", headers=H)
di = r.json()["items"]
ck("savol matni keladi", all(x.get("prompt") for x in di), True)
ck("bosqichlar osib boradi",
   [x["step"] for x in di] == sorted(x["step"] for x in di), True)
ck("javob mijozga ketmaydi",
   any("answer" in x or "expected" in x for x in di), False)

r = c.get("/api/student/ielts/listening/round"
          "?kind=ielts_trap&count=60", headers=H)
tr = r.json()["items"]
ck("trapda ham savol bor", all(x.get("prompt") for x in tr), True)
ck("chalg'ituvchilar mijozga OCHIQ ketmaydi",
   any("others" in x for x in tr), False)

print("\n=== 10. JAVOB SHAKLLARI KECHIRIMLI ===")
# Jahongirning misoli: jami 2,020 km (chalg'ituvchi 206 va 632)
it = (db.query(models.PracticeItem)
      .filter(models.PracticeItem.kind == "ielts_trap",
              models.PracticeItem.answer == "2020").first())
ck("Jahongir misoli bazada", it is not None, True)
if it:
    pl = json.loads(it.payload)
    ck("chalg'ituvchilar yozilgan", "206" in pl["others"], True)
    for variant in ("2020", "2,020", "2 020", "2020 km"):
        r = c.post("/api/student/ielts/listening/answer", headers=H,
                   json={"ref": f"pi:{it.id}", "answer": variant})
        ck(f"'{variant}' qabul qilinadi", r.json()["correct"], True)
    r = c.post("/api/student/ielts/listening/answer", headers=H,
               json={"ref": f"pi:{it.id}", "answer": "206"})
    ck("chalg'ituvchi javob RAD etiladi", r.json()["correct"], False)

# soat: 9:30 / 9.30 / 930
tim = (db.query(models.PracticeItem)
       .filter(models.PracticeItem.kind == "ielts_detail",
               models.PracticeItem.answer == "9.30").first())
if tim:
    for variant in ("9.30", "9:30", "930"):
        r = c.post("/api/student/ielts/listening/answer", headers=H,
                   json={"ref": f"pi:{tim.id}", "answer": variant})
        ck(f"soat '{variant}' qabul qilinadi", r.json()["correct"], True)

# hafta kuni: katta-kichik harf farq qilmasin
wd = (db.query(models.PracticeItem)
      .filter(models.PracticeItem.kind == "ielts_detail",
              models.PracticeItem.answer == "Wednesday").first())
if wd:
    for variant in ("Wednesday", "wednesday", " WEDNESDAY "):
        r = c.post("/api/student/ielts/listening/answer", headers=H,
                   json={"ref": f"pi:{wd.id}", "answer": variant})
        ck(f"kun '{variant.strip()}' qabul qilinadi",
           r.json()["correct"], True)
    r = c.post("/api/student/ielts/listening/answer", headers=H,
               json={"ref": f"pi:{wd.id}", "answer": "Tuesday"})
    ck("boshqa kun rad etiladi", r.json()["correct"], False)


print("\n=== 11. EXACT WORD TRAP (A/B/C) ===")
r = c.get("/api/student/ielts/listening/parts", headers=H)
parts = {p["kind"]: p for p in r.json()["parts"]}
ck("6-mashq ro'yxatda", parts["ielts_exact"]["no"], 6)
ck(f"100 ta ({parts['ielts_exact']['total']})",
   parts["ielts_exact"]["total"] >= 100, True)

r = c.get("/api/student/ielts/listening/round"
          "?kind=ielts_exact&count=60", headers=H)
ex = r.json()["items"]
ck("variantlar keladi", all(len(x.get("options") or []) == 3
                            for x in ex), True)
ck("savol ham keladi", all(x.get("prompt") for x in ex), True)
ck("to'g'ri javob mijozga KETMAYDI",
   any("answer" in x or "expected" in x for x in ex), False)
ck("bosqichlar osib boradi",
   [x["step"] for x in ex] == sorted(x["step"] for x in ex), True)

print("\n=== 12. TUZOQ HAQIQATAN ISHLAYDIMI ===")
# Har element uchun: noto'g'ri variantlar so'zlari audioda BOR,
# to'g'ri javobniki esa YO'Q — Jahongirning talabi shu.
import re as _re


def _in_audio(phrase, audio):
    return phrase.lower() in audio.lower()


bad_correct, bad_wrong = [], []
for it in (db.query(models.PracticeItem)
           .filter(models.PracticeItem.kind == "ielts_exact").all()):
    pl = json.loads(it.payload)
    say = pl["say"]
    if _in_audio(it.answer, say):
        bad_correct.append(it.answer)
    for o in pl["options"]:
        if o == it.answer:
            continue
        if not _in_audio(o, say):
            bad_wrong.append((o, say[:60]))
ck("to'g'ri javob so'zlari audioda YO'Q (hammasida)",
   bad_correct[:3], [])
ck("noto'g'ri variantlar so'zlari audioda BOR (hammasida)",
   bad_wrong[:3], [])

print("\n=== 13. TANLOV TEKSHIRUVI ===")
it = (db.query(models.PracticeItem)
      .filter(models.PracticeItem.kind == "ielts_exact",
              models.PracticeItem.answer == "young professional people")
      .first())
ck("Jahongir misoli (Sheepmarket) bazada", it is not None, True)
if it:
    pl = json.loads(it.payload)
    ck("uchta variant", len(pl["options"]), 3)
    # Gap boshida katta harf bilan kelishi mumkin — registrsiz
    ck("audioda 'students from the university' bor",
       "students from the university" in pl["say"].lower(), True)
    ck("audioda 'young professional' YO'Q",
       "young professional" in pl["say"].lower(), False)
    r = c.post("/api/student/ielts/listening/answer", headers=H,
               json={"ref": f"pi:{it.id}",
                     "answer": "young professional people"})
    ck("to'g'ri variant qabul qilindi", r.json()["correct"], True)
    r = c.post("/api/student/ielts/listening/answer", headers=H,
               json={"ref": f"pi:{it.id}",
                     "answer": "students from the university"})
    ck("eshitilgan so'z tuzog'i RAD etiladi", r.json()["correct"], False)
    ck("izohda tuzoq tushuntiriladi",
       "TUZOQ" in (r.json().get("explain") or ""), True)

print("\n=== 14. JAVOB A/B/C BO'YLAB TARQALGAN ===")
pos = {0: 0, 1: 0, 2: 0}
for it in (db.query(models.PracticeItem)
           .filter(models.PracticeItem.kind == "ielts_exact").all()):
    pl = json.loads(it.payload)
    pos[pl["options"].index(it.answer)] += 1
ck("A da ham, B da ham, C da ham javob bor",
   all(v >= 20 for v in pos.values()), True)

print("\n" + ("HAMMASI O'TDI" if not fails else f"XATOLAR: {fails}"))
sys.exit(1 if fails else 0)
