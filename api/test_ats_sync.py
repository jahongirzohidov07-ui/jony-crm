"""NOMZODLAR <-> ISHGA OLISH QUVURI MOSLIGI (2026-08-16).

Jahongir: "ishga olish quvuri bilan nomzodlar bo'limi deyarli bir
biriga bog'lanmayabdi, nomzodlardan suhbatdan o'tdi desa ishga olish
quvurida resume ko'rildi bo'lib turibdi".

Uchta nuqson tekshiriladi:
  1) bir nomzodda bir nechta ariza bo'lsa faqat oxirgisi yurardi;
  2) quvurdagi nozik bosqich (Telefon suhbati) karta saqlanganda
     yo'qolib ketardi;
  3) 2026-08-15 dan oldingi nomuvofiqlar o'z-o'zidan tuzalmasdi.
"""
import os, sys
os.environ["DATABASE_URL"] = "sqlite:////tmp/atssync.db"
if os.path.exists("/tmp/atssync.db"):
    os.remove("/tmp/atssync.db")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fastapi.testclient import TestClient          # noqa: E402
import main, models, roles                         # noqa: E402
import entry, hr_ats                               # noqa: E402
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
b = models.Branch(name="Bekobod 1"); db.add(b); db.commit(); BID = b.id
db.add(models.User(username="hr", full_name="HR Menejer",
                   role="hr_manager", branch_id=BID,
                   password_hash=hash_password("x"), is_active=1))
db.commit(); db.close()
H = {"Authorization": "Bearer " + c.post(
    "/api/auth/login", json={"username": "hr", "password": "x"})
    .json()["access_token"]}


def app_stages(cid):
    db = SessionLocal()
    out = [a.stage for a in db.query(models.CandidateApplication)
           .filter(models.CandidateApplication.candidate_id == cid)
           .order_by(models.CandidateApplication.id).all()]
    db.close()
    return out


def cand_stage(cid):
    db = SessionLocal()
    st = db.query(models.Candidate).get(cid).stage
    db.close()
    return st


print("=== 1. Xarita ikki tomonlama mos ===")
ck("phone -> interview", roles.APPLICATION_TO_CANDIDATE["phone"],
   "interview")
ck("telefon suhbati suhbat bilan bir xil holat",
   roles.stages_match("phone", "interview"), True)
ck("rezyume suhbat emas",
   roles.stages_match("screening", "interview"), False)
for k, v in roles.CANDIDATE_TO_APPLICATION.items():
    if k == "pool":
        continue
    ck(f"nomzod '{k}' -> quvur -> qaytib '{k}'",
       roles.APPLICATION_TO_CANDIDATE.get(v), k)

print("\n=== 2. Nomzodda bosqich o'zgarsa quvur yuradi ===")
r = c.post("/api/candidates", headers=H, json={
    "full_name": "Ustoz Nomzod", "phone": "+998901112233",
    "position": "teacher", "subject": "Ingliz tili",
    "stage": "applied", "source": "other", "branch_id": BID})
CID = r.json()["id"]
ck("ariza avtomat ochildi", app_stages(CID), ["new"])
c.put(f"/api/candidates/{CID}", headers=H, json={"stage": "screening"})
ck("rezyume ko'rildi", app_stages(CID), ["screening"])
c.put(f"/api/candidates/{CID}", headers=H, json={"stage": "interview"})
ck("suhbatga chaqirildi", app_stages(CID), ["interview"])

print("\n=== 3. Quvurdagi NOZIK bosqich yo'qolmaydi ===")
db = SessionLocal()
AID = db.query(models.CandidateApplication).filter(
    models.CandidateApplication.candidate_id == CID).first().id
db.close()
c.post(f"/api/ats/applications/{AID}/move", headers=H,
       json={"stage": "phone"})
ck("quvur telefon suhbatida", app_stages(CID), ["phone"])
ck("nomzod suhbatga chaqirilgan", cand_stage(CID), "interview")
c.put(f"/api/candidates/{CID}", headers=H, json={"cv": "yangi cv"})
ck("karta saqlandi — telefon suhbati QOLDI", app_stages(CID), ["phone"])
c.put(f"/api/candidates/{CID}", headers=H, json={"stage": "interview"})
ck("bosqich qayta tanlandi — baribir qoldi", app_stages(CID), ["phone"])

print("\n=== 4. BIR NECHTA ariza — hammasi birga yuradi ===")
db = SessionLocal()
db.add(models.CandidateApplication(candidate_id=CID, branch_id=BID,
                                   stage="new"))
db.commit(); db.close()
ck("ikkita ariza bor", len(app_stages(CID)), 2)
c.put(f"/api/candidates/{CID}", headers=H, json={"stage": "demo"})
ck("ikkalasi ham sinov darsida", app_stages(CID), ["demo", "demo"])

print("\n=== 5. ESKI nomuvofiqlik avtomat tuzatiladi ===")
db = SessionLocal()
old = models.Candidate(full_name="Eski Nomzod", branch_id=BID,
                       stage="interview", position="teacher")
db.add(old); db.commit(); OID = old.id
db.add_all([
    models.CandidateApplication(candidate_id=OID, branch_id=BID,
                                stage="screening"),
    models.CandidateApplication(candidate_id=OID, branch_id=BID,
                                stage="new"),
])
db.commit(); db.close()
ck("oldin nomuvofiq", app_stages(OID), ["screening", "new"])
db = SessionLocal()
n = hr_ats.fix_candidate_pipeline(db)
db.close()
ck("ikkita ariza tuzatildi", n, 2)
ck("endi ikkalasi ham suhbatda", app_stages(OID), ["interview", "interview"])
db = SessionLocal()
ck("ikkinchi marta ishlaganda tegmaydi",
   hr_ats.fix_candidate_pipeline(db), 0)
db.close()

print("\n=== 6. Tarix yozilib boradi ===")
db = SessionLocal()
logs = (db.query(models.ApplicationStageLog)
        .join(models.CandidateApplication,
              models.ApplicationStageLog.application_id
              == models.CandidateApplication.id)
        .filter(models.CandidateApplication.candidate_id == OID).count())
db.close()
ck("nomuvofiqlik tuzatilgani tarixda bor", logs >= 2, True)

print("\n=== 7. Rad etish ikki joyda ham yopiladi ===")
c.put(f"/api/candidates/{CID}", headers=H,
      json={"stage": "rejected", "reject_reason": "tajriba yetarli emas"})
ck("quvurda ham rad etildi", set(app_stages(CID)), {"rejected"})
ck("nomzodda ham", cand_stage(CID), "rejected")

print("\n=== 8. SUHBAT/SINOV DARSI KALENDARI ===")
from datetime import date as _d, timedelta as _td
r = c.post("/api/candidates", headers=H, json={
    "full_name": "Kalendar Nomzod", "phone": "+998907778899",
    "position": "teacher", "subject": "Ingliz tili",
    "stage": "applied", "source": "other", "branch_id": BID})
KID = r.json()["id"]
kun = (_d.today() + _td(days=3)).isoformat()
r = c.post(f"/api/candidates/{KID}/schedule", headers=H, json={
    "stage": "interview", "date": kun, "time": "14:30", "kind": "hr",
    "place": "Bekobod 1, 3-xona"})
ck("suhbat belgilandi", r.status_code, 200)
d = r.json()
ck("bosqich o'zgardi", d["stage"], "interview")
ck("soat saqlandi", d["interview"]["time"], "14:30")
ck("quvur ham yurdi", app_stages(KID), ["interview"])

kun2 = (_d.today() + _td(days=5)).isoformat()
r = c.post(f"/api/candidates/{KID}/schedule", headers=H, json={
    "stage": "demo", "date": kun2, "time": "09:00"})
ck("sinov darsi belgilandi", r.status_code, 200)
ck("turi avtomat demo bo'ldi", r.json()["interview"]["kind"], "demo")
ck("nomzod sinov darsida", cand_stage(KID), "demo")

r = c.get(f"/api/ats/interviews?date_from={kun}&date_to={kun2}", headers=H)
ck("kalendar oralig'i ishlaydi", r.status_code, 200)
rows = r.json()["rows"]
ck("ikkala yozuv ham bor", len(rows), 2)
ck("nomzod ismi kalendarda", rows[0]["candidate"], "Kalendar Nomzod")
ck("telefoni ham", rows[0]["phone"], "+998907778899")

o = (_d.today() - _td(days=1)).isoformat()
r = c.post(f"/api/candidates/{KID}/schedule", headers=H,
           json={"stage": "interview", "date": o})
ck("o'tib ketgan sana rad etiladi", r.status_code, 400)
r = c.post(f"/api/candidates/{KID}/schedule", headers=H,
           json={"stage": "offer", "date": kun})
ck("boshqa bosqich rad etiladi", r.status_code, 400)
r = c.get("/api/ats/interviews?date_from=xato", headers=H)
ck("noto'g'ri sana rad etiladi", r.status_code, 400)

print("\n" + ("HAMMASI OK" if not fails
              else f"{len(fails)} ta muammo: {fails}"))
sys.exit(1 if fails else 0)
