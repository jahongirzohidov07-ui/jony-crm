"""TEST VARIANTLARI + ARALASHTIRISH (2026-09-26).

Jahongir: "shu savollarni 4-5 xil variantini tayyorlab qoyish kerak
chunki ustozlar aynan testga tayyorlash holatlari kuzatilyabdi".

Tekshiriladi:
  A. exam_bank_variants.json: har variant asl (A) bilan bir xil
     tuzilishda (bo'lim soni, savol soni, tur, mavzu), listening
     bo'limida skript bor, savollar asl bilan takrorlanmaydi;
  B. Seed: fayldagi har (shablon, harf) uchun alohida shablon
     (variant B..E, sarlavhada "— B varianti"); ikkinchi seed hech
     narsa qo'shmaydi; asl shablon variant=A;
  C. mix_parts: har bo'lim tasodifiy variantdan, tuzilishi buzilmaydi,
     savol id/n lari 1..N, hammasi bitta variantdan bo'lib qolmaydi;
     tuzilishi boshqacha shablon aralashmaydi;
  D. Link: odatiy rejim aralash (o'quvchi 30 savol oladi, examiner
     "variants" va listening skriptini ko'radi, ustoz KO'RMAYDI,
     public sahifada skript yo'q); "single" rejim faqat tanlangan
     shablon; baholash ishlaydi (mavzu bilan javob varag'i);
  E. Test bazasi: variant yaratish/tahrirlash, noto'g'ri harf 400.
"""
import os
import sys
import json
import random
import tempfile
from datetime import timedelta

_DB = os.path.join(tempfile.gettempdir(), "exam_variants_test.db")
os.environ["DATABASE_URL"] = "sqlite:///" + _DB.replace("\\", "/")
if os.path.exists(_DB):
    os.remove(_DB)
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from fastapi.testclient import TestClient          # noqa: E402
import main, models, roles                          # noqa: E402
import entry  # noqa: F401,E402
import exam_online                                  # noqa: E402
import exam_bank_seed                               # noqa: E402
from database import SessionLocal                   # noqa: E402
from auth import hash_password                      # noqa: E402

client = TestClient(main.app)
fails = []


def ck(name, got, want):
    ok = got == want
    print(("OK  " if ok else "XATO ") + name + f": {got}"
          + ("" if ok else f"   (kutilgan {want})"))
    if not ok:
        fails.append(name)


def tok(u, p="x"):
    r = client.post("/api/auth/login", json={"username": u, "password": p})
    assert r.status_code == 200, r.text
    return {"Authorization": "Bearer " + r.json()["access_token"]}


print("=== A. exam_bank_variants.json TUZILISHI ===")
V = json.load(open(os.path.join(HERE, "exam_bank_variants.json"), encoding="utf-8"))
META = {k: t for k, t in exam_bank_seed.TEMPLATES}
bad, nq, nv = [], 0, 0
for key, letters in V.items():
    src = META.get(key)
    if not src:
        bad.append(f"{key}: seedda yo'q"); continue
    seen = set()
    for p in src["parts"]:
        for q in p["questions"]:
            seen.add((q.get("q") or "").strip().lower())
    for L, parts in letters.items():
        nv += 1
        if L not in "BCDE" or len(L) != 1:
            bad.append(f"{key}: harf {L!r}")
        if len(parts) != len(src["parts"]):
            bad.append(f"{key} {L}: bo'lim soni"); continue
        for sp, vp in zip(src["parts"], parts):
            if len(vp["questions"]) != len(sp["questions"]):
                bad.append(f"{key} {L} {sp['title']}: savol soni"); continue
            if "listening" in sp["title"].lower() and len((vp.get("script") or "").split()) < 8:
                bad.append(f"{key} {L} {sp['title']}: skript yo'q")
            for sq, vq in zip(sp["questions"], vp["questions"]):
                nq += 1
                if not vq.get("topic", "").split(" · ")[0] in ("Listening", "Reading", "Vocabulary", "Grammar"):
                    bad.append(f"{key} {L}: mavzu {vq.get('topic')!r}")
                if vq["type"] == "choice":
                    if not (isinstance(vq.get("answer"), int) and 0 <= vq["answer"] < len(vq.get("options") or [])):
                        bad.append(f"{key} {L}: javob indeksi")
                else:
                    if not vq.get("answer"):
                        bad.append(f"{key} {L}: matn javobi yo'q")
                qt = (vq.get("q") or "").strip().lower()
                if qt and len(qt) > 15 and qt in seen:
                    bad.append(f"{key} {L}: asl savol takrorlangan: {qt[:40]}")
ck("tuzilish xatosi yo'q", bad[:5], [])
ck("kamida 5 shablon, 20 variant", (len(V) >= 5, nv >= 20), (True, True))
ck("har variantda 30/40/45 savol", nq % 5 == 0 and nq >= 600, True)
print(f"   fayl: {len(V)} shablon, {nv} variant, {nq} savol")

print("\n=== B. SEED ===")
db = SessionLocal()
exam_online.seed_templates(db)
rows = [t for t in db.query(models.ExamTemplate).all()
        if (t.subject or "english") == "english"]     # matematika alohida (test_exam_math)
ck("asl shablonlar 42 ta, variant A", sum(1 for t in rows if (t.variant or "A") == "A"), 42)
ck("variant shablonlar = fayldagi soni", sum(1 for t in rows if t.variant in "BCDE" and t.variant), nv)
t2b = db.query(models.ExamTemplate).filter_by(level="step1", kind="unit", unit_no=2, variant="B").first()
ck("Step 1 U2 B bor, sarlavha", t2b.title.endswith("— B varianti"), True)
ck("B varianti 30 savol, mavzular bor",
   (sum(1 for _ in exam_online._questions(exam_online._load(t2b.parts))),
    all(q.get("topic") for q in exam_online._questions(exam_online._load(t2b.parts)))), (30, True))
ck("listening skripti saqlangan",
   len(exam_online._load(t2b.parts)[0].get("script", "").split()) >= 8, True)
n_before = len(rows)
exam_online.seed_templates(db)
ck("ikkinchi seed hech narsa qo'shmaydi",
   sum(1 for t in db.query(models.ExamTemplate).all() if (t.subject or "english") == "english"), n_before)

print("\n=== C. mix_parts ===")
base = db.query(models.ExamTemplate).filter_by(level="step1", kind="unit", unit_no=2, variant="A").first()
fam = exam_online._family(db, base)
ck("oila: 5 variant", [t.variant for t in fam], ["A", "B", "C", "D", "E"])
rnd = random.Random(7)
parts, chosen = exam_online.mix_parts(base, fam, rnd)
ck("5 bo'lim, 30 savol", (len(parts), sum(len(p["questions"]) for p in parts)), (5, 30))
ck("variantlar yozuvi 5 harf", (len(chosen.split(",")), set(chosen.split(",")) <= set("ABCDE")), (5, True))
ck("id va n 1..30 tartibda",
   [q["n"] for q in exam_online._questions(parts)] == list(range(1, 31))
   and len({q["id"] for q in exam_online._questions(parts)}) == 30, True)
ck("bitta variantdan bo'lib qolmaydi", len(set(chosen.split(","))) > 1, True)
# Aralashganini isbotlash: har bo'lim tanlangan variantnikiga teng
by_letter = {t.variant: exam_online._load(t.parts) for t in fam}
ok = all(parts[i]["questions"][0]["q"] == by_letter[L][i]["questions"][0]["q"]
         and parts[i]["questions"][0].get("options") == by_letter[L][i]["questions"][0].get("options")
         for i, L in enumerate(chosen.split(",")))
ck("har bo'lim aynan tanlangan variantdan", ok, True)
seen_combos = {exam_online.mix_parts(base, fam, random.Random(i))[1] for i in range(40)}
ck("40 urinishda kamida 20 xil kombinatsiya", len(seen_combos) >= 20, True)
# Tuzilishi boshqacha shablon aralashmaydi
odd = models.ExamTemplate(level="step1", kind="unit", unit_no=2, variant="F",
                          title="Boshqacha", parts=json.dumps(exam_online.clean_parts([
                              {"title": "Part 1", "questions": [
                                  {"type": "choice", "q": "x", "options": ["a", "b"], "answer": 0}]}])),
                          paper_max=0)
db.add(odd); db.commit()
fam2 = exam_online._family(db, base)
parts2, chosen2 = exam_online.mix_parts(base, fam2, random.Random(3))
ck("boshqacha tuzilgan F aralashmaydi", ("F" in chosen2, len(parts2)), (False, 5))
odd.is_active = 0; db.commit()

print("\n=== D. LINK: ARALASH / BITTA ===")
b = models.Branch(name="Zafar"); db.add(b); db.commit()
for un, role in [("asos", "founder"), ("exam", "examiner"), ("ustoz", "teacher")]:
    db.add(models.User(username=un, password_hash=hash_password("x"),
                       full_name=un.title(), role=role, branch_id=b.id))
tch = models.Teacher(full_name="Ustoz", branch_id=b.id); db.add(tch); db.commit()
g = models.Group(name="Apex", branch_id=b.id, teacher_id=tch.id, subject="english", level="step1")
db.add(g); db.commit()
s = models.Student(full_name="Aliyev Ali", branch_id=b.id, group_id=g.id, status="active",
                   enrolled_date=roles.local_today() - timedelta(days=30))
db.add(s); db.commit()
ex1 = models.Exam(group_id=g.id, kind="unit", unit_no=2, date=roles.local_today(), max_score=30, status="approved")
ex2 = models.Exam(group_id=g.id, kind="unit", unit_no=4, date=roles.local_today(), max_score=30, status="approved")
db.add_all([ex1, ex2]); db.commit()
E1, E2, SID, BASE = ex1.id, ex2.id, s.id, base.id
t4c = db.query(models.ExamTemplate).filter_by(level="step1", kind="unit", unit_no=4, variant="C").first()
T4C = t4c.id
db.close()
H, HE, HT = tok("asos"), tok("exam"), tok("ustoz")
r = client.get(f"/api/exams/{E1}/online", headers=HE)
tl = [t for t in r.json()["templates"] if t["level"] == "step1"]
ck("linkdan oldin ro'yxatda 5 variant (variant maydoni bilan)",
   sorted(t["variant"] for t in tl), ["A", "B", "C", "D", "E"])
r = client.post(f"/api/exams/{E1}/online", headers=HE, json={"template_id": BASE})
ck("aralash link 200", r.status_code, 200)
on = r.json()["online"]
ck("examiner variantlarni ko'radi", len((on.get("variants") or "").split(",")), 5)
ck("examiner listening skriptini ko'radi",
   (len(on["scripts"]) >= 1, "Listening" in on["scripts"][0]["part"]), (True, True))
ck("30 savol", on["online_max"], 30.0)
TOKEN = on["token"]
ont = client.get(f"/api/exams/{E1}/online", headers=HT).json()["online"]
ck("ustoz variant va skriptni KO'RMAYDI", (ont.get("variants"), ont.get("scripts")), (None, []))
client.post(f"/api/exams/{E1}/online/start", headers=HE, json={"minutes": 30, "countdown": 0})
pub = client.get(f"/api/public/exam/{TOKEN}").json()
ck("public: 5 bo'lim 30 savol, skript/javob yo'q",
   (len(pub["parts"]), sum(len(p["questions"]) for p in pub["parts"]),
    any("script" in p for p in pub["parts"]),
    any("answer" in q for p in pub["parts"] for q in p["questions"])), (5, 30, False, False))
# Barcha savollarga to'g'ri javob: link nusxasidan
d = SessionLocal()
o = d.query(models.ExamOnline).filter_by(exam_id=E1).first()
answers = {}
for q in exam_online._questions(exam_online._load(o.parts)):
    answers[q["id"]] = q["answer"] if q["type"] == "choice" else q["answer"][0]
d.close()
PHOTO = "data:image/jpeg;base64," + "A" * 200
r = client.post(f"/api/public/exam/{TOKEN}/submit", json={"photo": PHOTO, "student_id": SID, "answers": answers})
ck("topshirdi", r.status_code, 200)
subs = client.get(f"/api/exams/{E1}/online", headers=HE).json()["submissions"]
ck("30/30 baholandi, javob varag'ida mavzu bor",
   (subs[0]["online_score"], subs[0]["detail"][0].get("topic") is not None), (30.0, True))
# Bitta variant rejimi
r = client.post(f"/api/exams/{E2}/online", headers=HE, json={"template_id": T4C, "mode": "single"})
ck("single rejim: faqat C", r.json()["online"]["variants"], "C")

print("\n=== E. TEST BAZASI: VARIANT MAYDONI ===")
body = client.get(f"/api/exam-templates/{T4C}", headers=HE).json()
ck("GET variant C", body["variant"], "C")
r = client.post("/api/exam-templates", headers=H, json={
    "level": "step1", "kind": "unit", "unit_no": 12, "title": "Yangi", "paper_max": 0,
    "is_active": True, "variant": "f", "parts": body["parts"]})
ck("yangi shablon variant F (katta harf)", (r.status_code, r.json().get("variant")), (200, "F"))
r = client.post("/api/exam-templates", headers=H, json={
    "level": "step1", "kind": "unit", "unit_no": 12, "title": "Yangi", "paper_max": 0,
    "is_active": True, "variant": "9", "parts": body["parts"]})
ck("noto'g'ri harf 400", r.status_code, 400)

print("\n" + ("HAMMASI OK" if not fails else "XATOLAR: " + ", ".join(fails)))
sys.exit(1 if fails else 0)
