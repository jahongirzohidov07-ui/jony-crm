"""IMTIHON O'TISH BALLI — TEST TURI BO'YICHA (2026-09-10).

Jahongir: "Maksimal ball bor o'tish balli yo'qku" -> "test turi
boyivha sozlamalarda bir marta, foizda olchanadi, 65% unit testda 60%
esa mid va end courselarda".

Ilgari o'tish chegarasi ikki joyda QOTIRIB yozilgan va bir-biriga
to'g'ri kelmasdi: sertifikat 60%, Analitika->Imtihonlar hisoboti 65%.
Ya'ni 62% olgan o'quvchi sertifikat olardi, lekin hisobotda
"o'tmagan" bo'lib chiqardi.

Endi: sozlamada tur bo'yicha bir marta belgilanadi, va test
YARATILGANDA o'sha qiymat imtihonga MUHRLANADI. Shuning uchun
sozlamani keyin o'zgartirish o'tib ketgan testlarni va ustoz
ko'rsatkichini qayta hisoblab yubormaydi (narx qulfi bilan bir xil
mantiq).

Tekshiriladi:
  A. Standart qiymatlar: unit 65%, mid 60%, end 60%; mock yo'q;
  B. Test ochilganda o'tish balli imtihonga muhrlanadi;
  C. Sozlama o'zgarsa — ESKI test o'z ballida qoladi, YANGI test
     yangi qiymatni oladi;
  D. Sertifikat aynan shu muhrlangan chegaradan beriladi;
  E. Hisobotda "o'tdi/o'tmadi" ham shu chegaradan;
  F. Chegarasi muhrlanmagan ESKI testlar avvalgi 65% da qoladi
     (tarix o'zgarmaydi);
  G. Mock'da o'tish balli yo'q;
  H. Noto'g'ri qiymat (0, 150, mock) qabul qilinmaydi;
  I. Frontend shu maydonlarni ishlatyapti.
"""
import os
import sys
import tempfile
from datetime import date, timedelta

_DB = os.path.join(tempfile.gettempdir(), "exam_pass_test.db")
os.environ["DATABASE_URL"] = "sqlite:///" + _DB.replace("\\", "/")
if os.path.exists(_DB):
    os.remove(_DB)
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

from fastapi.testclient import TestClient          # noqa: E402
import main, models, roles                          # noqa: E402
import entry  # noqa: F401,E402
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
    return {"Authorization": "Bearer " + client.post(
        "/api/auth/login", json={"username": u, "password": p}
    ).json()["access_token"]}


TODAY = roles.local_today()

db = SessionLocal()
b = models.Branch(name="Zafar")
db.add(b)
db.commit()
BID = b.id
db.add(models.User(username="asos", password_hash=hash_password("x"),
                   full_name="Asoschi", role="founder"))
db.commit()
t = models.Teacher(full_name="Ustoz", branch_id=BID)
db.add(t)
db.commit()
g = models.Group(name="Apex", branch_id=BID, teacher_id=t.id, level="B1")
db.add(g)
db.commit()
GID = g.id
S = {}
for nm in ["Aliyev", "Boboyev", "Valiyev"]:
    s = models.Student(full_name=nm, branch_id=BID, group_id=GID,
                       status="active",
                       enrolled_date=TODAY - timedelta(days=60))
    db.add(s)
    db.commit()
    S[nm] = s.id
db.close()

H = tok("asos")

print("=== 1. STANDART QIYMATLAR ===")
r = client.get("/api/exam-pass-rules", headers=H)
ck("javob 200", r.status_code, 200)
rules = {x["kind"]: x["percent"] for x in r.json()}
ck("unit 65%", rules.get("unit"), 65.0)
ck("mid 60%", rules.get("mid"), 60.0)
ck("end 60%", rules.get("end"), 60.0)
ck("mock ro'yxatda yo'q", "mock" in rules, False)
ck("yorliqlar bor",
   [x["label"] for x in r.json()],
   ["Unit test", "Mid-course", "End of course"])


def new_exam(kind, mx=50, unit=1, day=None):
    p = {"kind": kind, "date": (day or TODAY).isoformat(),
         "max_score": None if kind == "mock" else mx}
    if kind == "unit":
        p["unit_no"] = unit
    rr = client.post(f"/api/groups/{GID}/exams", json=p, headers=H)
    assert rr.status_code == 200, rr.text
    return rr.json()


print("\n=== 2. TEST OCHILGANDA MUHRLANADI ===")
e_unit = new_exam("unit", 50, 1)
e_mid = new_exam("mid", 100)
e_mock = new_exam("mock")
ck("unit testda 65%", e_unit["pass_percent"], 65.0)
ck("mid testda 60%", e_mid["pass_percent"], 60.0)
ck("mock'da o'tish balli yo'q", e_mock["pass_percent"], None)

print("\n=== 3. SOZLAMA O'ZGARSA — ESKI TEST O'Z BALLIDA QOLADI ===")
r = client.put("/api/exam-pass-rules", headers=H, json=[
    {"kind": "unit", "percent": 80}, {"kind": "mid", "percent": 60},
    {"kind": "end", "percent": 60}])
ck("saqlandi", r.status_code, 200)
ck("yangi unit qiymati",
   {x["kind"]: x["percent"] for x in r.json()}["unit"], 80.0)
old = client.get(f"/api/groups/{GID}/exams", headers=H).json()
old_unit = [x for x in old if x["id"] == e_unit["id"]][0]
ck("ESKI unit test hali ham 65%", old_unit["pass_percent"], 65.0)
e_unit2 = new_exam("unit", 50, 2)
ck("YANGI unit test 80%", e_unit2["pass_percent"], 80.0)

# Keyingi tekshiruvlar uchun 65% ga qaytaramiz
client.put("/api/exam-pass-rules", headers=H, json=[
    {"kind": "unit", "percent": 65}, {"kind": "mid", "percent": 60},
    {"kind": "end", "percent": 60}])

print("\n=== 4. SERTIFIKAT MUHRLANGAN CHEGARADAN ===")
e_end = new_exam("end", 100)
ck("end testda 60%", e_end["pass_percent"], 60.0)
# 62 -> o'tdi, 58 -> yiqildi (chegara 60)
r = client.put(f"/api/exams/{e_end['id']}/results", headers=H, json={
    "marks": [{"student_id": S["Aliyev"], "score": 62},
              {"student_id": S["Boboyev"], "score": 58}]})
ck("ballar saqlandi", r.status_code, 200)
db = SessionLocal()
certs = {c.student_id for c in db.query(models.Certificate)
         .filter(models.Certificate.kind == "level").all()}
ck("62% olgan sertifikat oldi", S["Aliyev"] in certs, True)
ck("58% olgan sertifikat olmadi", S["Boboyev"] in certs, False)
db.close()

print("\n=== 5. HISOBOTDA O'TDI/O'TMADI SHU CHEGARADAN ===")
rep = client.get("/api/analytics/exam-report", headers=H).json()
rows = {x["oquvchi"]: x for x in rep["students"]
        if x["imtihon"] == e_end["title"]}
ck("62% — o'tdi (eski 65% qoida bo'lsa o'tmagan bo'lardi)",
   rows["Aliyev"]["otdi"], True)
ck("58% — o'tmadi", rows["Boboyev"]["otdi"], False)
ck("sarlavhada turlar bo'yicha ko'rsatilgan",
   "Unit test 65%" in (rep.get("pass_label") or ""), True)

print("\n=== 6. ESKI TESTLAR (chegara muhrlanmagan) 65% DA QOLADI ===")
db = SessionLocal()
legacy = models.Exam(group_id=GID, kind="end", title="Eski test",
                     date=TODAY, max_score=100, status="approved",
                     pass_percent=None)      # eski yozuv — maydon bo'sh
db.add(legacy)
db.commit()
LID = legacy.id
for nm, sc in [("Aliyev", 62), ("Valiyev", 70)]:
    db.add(models.ExamResult(exam_id=LID, student_id=S[nm],
                             score=sc, percent=sc))
db.commit()
db.close()
rep2 = client.get("/api/analytics/exam-report", headers=H).json()
old_rows = {x["oquvchi"]: x for x in rep2["students"]
            if x["imtihon"] == "Eski test"}
ck("eski testda 62% — o'tmagan (avvalgi 65% qoida)",
   old_rows["Aliyev"]["otdi"], False)
ck("eski testda 70% — o'tgan", old_rows["Valiyev"]["otdi"], True)

print("\n=== 7. NOTO'G'RI QIYMAT QABUL QILINMAYDI ===")
r = client.put("/api/exam-pass-rules", headers=H,
               json=[{"kind": "mock", "percent": 50}])
ck("mock rad etiladi", r.status_code, 400)
r = client.put("/api/exam-pass-rules", headers=H,
               json=[{"kind": "unit", "percent": 0}])
ck("0% rad etiladi", r.status_code, 400)
r = client.put("/api/exam-pass-rules", headers=H,
               json=[{"kind": "unit", "percent": 150}])
ck("150% rad etiladi", r.status_code, 400)
still = {x["kind"]: x["percent"] for x in
         client.get("/api/exam-pass-rules", headers=H).json()}
ck("xato so'rovdan keyin qiymat buzilmadi", still["unit"], 65.0)

print("\n=== 8. FRONTEND ULANGANMI ===")
gam = open(os.path.join(ROOT, "src", "pages", "Gamification.tsx"),
           encoding="utf-8").read()
ck("sozlama qutisi bor", "function PassMarkBox" in gam, True)
ck("qutisi sahifada chaqirilgan", "<PassMarkBox" in gam, True)
ck("endpointga ulangan", '"/exam-pass-rules"' in gam, True)
gg = open(os.path.join(ROOT, "src", "components", "GroupGrids.tsx"),
          encoding="utf-8").read()
ck("Yangi test oynasida ko'rinadi", "passPercent" in gg, True)
ck("Yangi testda TAHRIRLANMAYDI (input yo'q)",
   "setPassPercent" in gg, False)
api_ts = open(os.path.join(ROOT, "src", "lib", "api.ts"),
              encoding="utf-8").read()
ck("ExamPassRule tipi bor", "export interface ExamPassRule" in api_ts, True)
ck("Exam tipida pass_percent bor", "pass_percent?:" in api_ts, True)

print("\n" + ("BARCHASI OK" if not fails else f"XATOLAR: {fails}"))
sys.exit(1 if fails else 0)
