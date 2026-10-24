"""Eski dars bahosini tahrirlash — HR (2026-10-24)."""
import os, sys
from datetime import date
os.environ["DATABASE_URL"] = "sqlite:////tmp/obs_edit_test.db"
if os.path.exists("/tmp/obs_edit_test.db"):
    os.remove("/tmp/obs_edit_test.db")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fastapi.testclient import TestClient  # noqa: E402
import main, models, roles, entry  # noqa: E402,F401
from database import SessionLocal  # noqa: E402
from auth import hash_password  # noqa: E402

c = TestClient(main.app)
fails = []


def ck(n, got, want):
    ok = got == want
    print(("OK  " if ok else "XATO ") + n + f": {got}" + ("" if ok else f" (kutilgan {want})"))
    if not ok:
        fails.append(n)


db = SessionLocal()
b = models.Branch(name="Zafar"); db.add(b); db.commit()
for un, r in (("hr", roles.HR_MANAGER), ("hex", roles.HEAD_EXAMINER),
              ("ust", roles.TEACHER)):
    db.add(models.User(username=un, password_hash=hash_password("x"),
                       full_name=un.upper(), role=r, is_active=1, branch_id=b.id))
t = models.Teacher(full_name="Elena", branch_id=b.id, is_active=1)
db.add(t); db.commit(); TID = t.id
db.close()


def tok(u):
    return {"Authorization": "Bearer " + c.post("/api/auth/login", json={
        "username": u, "password": "x"}).json()["access_token"]}


H = tok("hr")
rub = c.get("/api/rubrics", headers=H).json()
main_r = next(r for r in rub["rows"] if r["key"] == roles.RUBRIC_MAIN)
crit = main_r["criteria"]
r = c.post("/api/observations", headers=H, json={
    "rubric_key": roles.RUBRIC_MAIN, "target_type": "teacher",
    "teacher_id": TID, "date": "2026-09-10",
    "scores": [{"criterion_id": x["id"], "fact": 0} for x in crit]})
ck("yaratildi", r.status_code, 200)
OID = r.json()["id"]
ck("boshida 0%", r.json()["percent"], 0)

full = [{"criterion_id": x["id"], "fact": x["points"] + 99} for x in crit]
r = c.put(f"/api/observations/{OID}", headers=H, json={
    "scores": full, "strengths": "Yaxshi", "date": "2026-09-11"})
ck("HR tahrirladi", r.status_code, 200)
d = r.json()
ck("mezon balidan oshmadi — 100%", d["percent"], 100.0)
ck("jami = max", d["total"], d["max_total"])
ck("izoh va sana", (d.get("strengths"), d.get("date")), ("Yaxshi", "2026-09-11"))
s2 = SessionLocal()
ck("mahorat balli yangilandi", s2.query(models.Teacher).get(TID).skill_score, 100.0)
au = s2.query(models.AuditLog).filter(models.AuditLog.field.like("Dars bahosi%")).first()
ck("auditda eski -> yangi", (au.old_value, au.new_value) if au else None, ("0.0%", "100.0%"))
ck("baholagan o'zgarmadi", s2.query(models.LessonObservation).get(OID).observer, "HR")
ck("ball qatorlari ko'paymadi", s2.query(models.ObservationScore).filter(
    models.ObservationScore.observation_id == OID).count(), len(crit))
s2.close()
ck("ustoz tahrirlay olmaydi", c.put(f"/api/observations/{OID}", headers=tok("ust"),
   json={"note": "x"}).status_code, 403)
ck("bosh examiner tahrirlay olmaydi", c.put(f"/api/observations/{OID}",
   headers=tok("hex"), json={"note": "x"}).status_code, 403)
print()
if fails:
    print(f"{len(fails)} ta XATO: {fails}"); sys.exit(1)
print("HAMMASI OK")
