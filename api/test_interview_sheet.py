"""SUHBAT VARAQASI (2026-10-08).

Jahongir: HR suhbat savollarini mukammal qilib, "nomzodlar degan joyiga
qo'shib ber, savol va javobini yozishga bo'sh joy qoldirib".

Tekshiriladi:
  1. Savollar ro'yxati: id lar takrorlanmaydi, kamsituvchi savol yo'q.
  2. Varaqa saqlanadi; foiz serverda (1-5 ballar o'rtachasi);
     noma'lum savol / noto'g'ri ball rad etiladi.
  3. Har suhbatdoshning o'z varaqasi; boshqasiniki "others" da.
  4. Kartadagi intervyu bahosi (0-10) varaqalar o'rtachasidan.
  5. Ruxsat: administrator — 403; o'quv bo'limi rahbari — faqat ustoz
     nomzodi.
"""
import os
import sys
import tempfile

_DIR = os.path.join(tempfile.gettempdir(), "interview_sheet_test")
os.makedirs(_DIR, exist_ok=True)
_DB = os.path.join(_DIR, "db.sqlite")
os.environ["DATABASE_URL"] = "sqlite:///" + _DB.replace(chr(92), "/")
if os.path.exists(_DB):
    os.remove(_DB)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient          # noqa: E402
import main, models, roles                         # noqa: E402
import entry                                       # noqa: E402,F401
import interview_guide                             # noqa: E402
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


def user(login, role):
    u = models.User(username=login, password_hash=hash_password("x"),
                    full_name=login.upper(), role=role, branch_id=b.id,
                    is_active=1)
    db.add(u); db.commit()
    return u


hr = user("hr", roles.HR_MANAGER)
fo = user("asos", roles.FOUNDER)
user("adm", roles.ADMINISTRATOR)
user("oquv", roles.ACADEMIC_HEAD)

cand = models.Candidate(full_name="Nomzod Admin", phone="901234567",
                        branch_id=b.id, position="administrator")
db.add(cand); db.commit()
CID = cand.id


def tok(u):
    r = c.post("/api/auth/login", json={"username": u, "password": "x"})
    return {"Authorization": "Bearer " + r.json()["access_token"]}


HH, HF, HA, HO = tok("hr"), tok("asos"), tok("adm"), tok("oquv")

print("=== 1. SAVOLLAR ===")
g = c.get("/api/hr/interview-guide", headers=HH).json()
ids = [q["id"] for s in g["sections"] for q in s["items"]]
ck("id lar takrorlanmaydi", len(ids), len(set(ids)))
ck("jami savol", g["total"], len(ids))
text = " ".join(q["text"].lower() for s in g["sections"] for q in s["items"])
ck("farzand haqida so'ralmaydi", "farzand" in text, False)
ck("oyligini bizga berish taklifi yo'q", "oyligingizni bizga" in text, False)

print("\n=== 2. SAQLASH ===")
url = f"/api/candidates/{CID}/interview-sheet"
r = c.put(url, headers=HH, json={
    "answers": {"q1": {"a": "Tartibli gapirdi", "s": 4},
                "q8": {"a": "Konversiya 25% -> 35%", "s": 5},
                "o4": {"ok": True},
                "q2": {"a": "Telegram kanal", "s": 3},   # note — ball yo'q
                "zzz": {"a": "noma'lum"}},
    "recommendation": "yes",
    "strengths": "Raqamda fikrlaydi"})
ck("saqlandi", r.status_code, 200)
d = r.json()
ck("foiz (4+5)/2/5", d["percent"], 90.0)
ck("note savolga ball yozilmaydi", "s" in d["answers"]["q2"], False)
ck("noma'lum savol tashlanadi", "zzz" in d["answers"], False)
ck("kuzatuv", (d["checks_ok"], d["checks_total"]), (1, 1))
ck("javob berilgan", d["answered"], 4)
ck("tavsiya", d["recommendation_label"], "Olsa bo'ladi")
r = c.put(url, headers=HH, json={"answers": {"q1": {"s": 7}}})
ck("ball 1-5 dan tashqari — 400", r.status_code, 400)
r = c.put(url, headers=HH, json={"answers": {}, "recommendation": "zo'r"})
ck("noto'g'ri tavsiya — 400", r.status_code, 400)

print("\n=== 3. IKKINCHI SUHBATDOSH ===")
r = c.put(url, headers=HF, json={"answers": {"q1": {"s": 3}}})
ck("asoschi o'z varaqasi", r.json()["percent"], 60.0)
d = c.get(url, headers=HH).json()
ck("HR o'z varaqasini ko'radi", d["mine"]["percent"], 90.0)
ck("asoschiniki others da", [s["author"] for s in d["others"]], ["ASOS"])
ck("HR javobi saqlangan", d["mine"]["answers"]["q8"]["a"],
   "Konversiya 25% -> 35%")

print("\n=== 4. KARTADAGI BAHO ===")
db.expire_all()
ck("intervyu bahosi (90+60)/2/10",
   db.query(models.Candidate).get(CID).interview_score, 7.5)

print("\n=== 5. RUXSAT ===")
ck("administrator — 403", c.get(url, headers=HA).status_code, 403)
ck("o'quv bo'limi: ustoz bo'lmagan nomzod — 403",
   c.get(url, headers=HO).status_code, 403)
ct = models.Candidate(full_name="Ustoz Nomzod", branch_id=b.id,
                      position="teacher")
db.add(ct); db.commit()
ck("o'quv bo'limi: ustoz nomzodi — 200",
   c.get(f"/api/candidates/{ct.id}/interview-sheet",
         headers=HO).status_code, 200)
ck("yo'q nomzod — 404",
   c.get("/api/candidates/99999/interview-sheet", headers=HH).status_code,
   404)

print("\n=== 6. BAHOLASH (hamma suhbatdoshlar) ===")
c.put(url, headers=HF, json={"answers": {"q1": {"s": 3}},
                              "recommendation": "maybe"})
d = c.get(url, headers=HH).json()
ev = d["evaluation"]
ck("o'rtacha foiz (90+60)/2", ev["percent"], 75.0)
ck("daraja", ev["band"], "Mos keladi")
ck("suhbatdoshlar", ev["interviewers"], 2)
ck("tavsiyalar sanaladi",
   sorted((r["key"], r["count"]) for r in ev["recommendations"]),
   [("maybe", 1), ("yes", 1)])
ck("fikrlar tarqoq (30% farq)", ev["split"], True)
sec1 = next(s for s in ev["by_section"] if s["key"] == "intro")
ck("1-bo'lim o'rtachasi (4+3)/2", sec1["avg"], 3.5)
sm = c.get("/api/hr/interview-summary", headers=HH).json()["rows"]
ck("ro'yxat uchun xulosa", sm[str(CID)]["percent"], 75.0)
ck("o'quv bo'limiga ustoz bo'lmagan nomzod xulosasi ko'rinmaydi",
   str(CID) in c.get("/api/hr/interview-summary",
                     headers=HO).json()["rows"], False)

print("\n=== 7. SAVOLLARNI TAHRIRLASH ===")
g = c.get("/api/hr/interview-guide", headers=HH).json()
ck("HR tahrirlay oladi", g["can_edit"], True)
ck("standart ro'yxat", g["customized"], False)
secs = g["sections"]
intro = next(s for s in secs if s["key"] == "intro")
intro["items"] = [q for q in intro["items"] if q["id"] != "q1"]   # o'chirish
intro["items"].append({"text": "Nega ingliz tilini o'rgatmoqchisiz?",
                       "kind": "score", "core": True,
                       "good": "O'z tajribasidan aytadi"})
secs.append({"title": "Qo'shimcha", "items": [
    {"text": "Haydovchilik guvohnomangiz bormi?", "kind": "note"}]})
r = c.put("/api/hr/interview-guide", headers=HH, json={"sections": secs})
ck("saqlandi", r.status_code, 200)
g2 = r.json()
ck("endi o'zgartirilgan", g2["customized"], True)
ids2 = [q["id"] for s in g2["sections"] for q in s["items"]]
ck("q1 o'chdi", "q1" in ids2, False)
new_ids = [i for i in ids2 if i.startswith("u")]
ck("yangi savollarga id berildi", len(new_ids), 2)
ck("id lar takrorlanmaydi", len(ids2), len(set(ids2)))
ck("yangi bo'lim kaliti bor",
   bool(g2["sections"][-1]["key"]), True)
# q1 o'chdi — HR varaqasi foizi qayta hisoblanadi: faqat q8 (5) qoladi
d = c.get(url, headers=HH).json()
ck("o'chgan savol bahosi hisobga kirmaydi", d["mine"]["percent"], 100.0)
ck("eski javob bazada saqlangan", d["mine"]["answers"]["q1"]["s"], 4)
r = c.put(url, headers=HH, json={"answers": {
    new_ids[0]: {"a": "Bolalarni yaxshi ko'radi", "s": 2},
    "q8": {"a": "Konversiya 25% -> 35%", "s": 5}}})
ck("yangi savolga javob", r.json()["answers"][new_ids[0]]["s"], 2)
ck("eski q1 javobi yo'qolmadi", r.json()["answers"].get("q1", {}).get("s"), 4)
ck("ruxsat: o'quv bo'limi tahrirlay olmaydi",
   c.put("/api/hr/interview-guide", headers=HO,
         json={"sections": secs}).status_code, 403)
ck("bo'sh savol matni — 400",
   c.put("/api/hr/interview-guide", headers=HH,
         json={"sections": [{"title": "X", "items": [{"text": " "}]}]}
         ).status_code, 400)
ck("bo'sh ro'yxat — 400",
   c.put("/api/hr/interview-guide", headers=HH,
         json={"sections": []}).status_code, 400)
r = c.post("/api/hr/interview-guide/reset", headers=HH)
ck("asl holiga qaytdi", r.json()["customized"], False)
d = c.get(url, headers=HH).json()
ck("q1 qaytdi — eski bahosi yana hisobda",
   d["mine"]["percent"], 90.0)

print()
if fails:
    print(f"XATO: {len(fails)} ta tekshiruv o'tmadi")
    for x in fails:
        print("   - " + x)
    sys.exit(1)
print("HAMMASI O'TDI")
sys.exit(0)
