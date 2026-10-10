"""HR checklistda videoni QO'LDA o'tdi/o'tmadi (2026-10-10)."""
import os, sys
os.environ["DATABASE_URL"] = "sqlite:////tmp/pd_mark_test.db"
if os.path.exists("/tmp/pd_mark_test.db"):
    os.remove("/tmp/pd_mark_test.db")
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
for un, r in (("hr", roles.HR_MANAGER), ("sup", roles.SUPPORT_TEACHER),
              ("ust", roles.TEACHER)):
    db.add(models.User(username=un, password_hash=hash_password("x"),
                       full_name=un.upper(), role=r, is_active=1))
db.commit()
SUP = db.query(models.User).filter_by(username="sup").first().id
v = models.PdVideo(title="Metodika 1", yt_id="abc", duration=600,
                   target_roles="", required=1, active=1)
db.add(v); db.commit(); VID = v.id
db.close()


def tok(u):
    return {"Authorization": "Bearer " + c.post("/api/auth/login", json={
        "username": u, "password": "x"}).json()["access_token"]}


H = tok("hr")


def cell():
    d = c.get(f"/api/hr/checklist?role={roles.SUPPORT_TEACHER}", headers=H).json()
    col = next(x for x in d["columns"] if x["source"] == "pd")
    row = next(x for x in d["rows"] if x["user_id"] == SUP)
    return col, row["cells"][col["key"]], row


col, ce, row = cell()
ck("video katagi belgilanadi", col["can_mark"], True)
ck("boshida o'tmadi", ce["passed"], False)
r = c.put(f"/api/pd/{VID}/people/{SUP}", headers=H, json={"passed": True})
ck("o'tdi saqlandi", r.status_code, 200)
col, ce, row = cell()
ck("ko'rmasa ham o'tdi", ce["passed"], True)
ck("kim qo'ygani", ce["by"], "HR")
ck("foiz o'zgarmadi (0)", ce["percent"], 0)
ck("jami 1/1", (row["passed"], row["required"]), (1, 1))
r = c.put(f"/api/pd/{VID}/people/{SUP}", headers=H, json={"passed": False})
col, ce, row = cell()
ck("o'tmadi qaytdi", ce["passed"], False)
ck("ustoz belgilay olmaydi", c.put(f"/api/pd/{VID}/people/{SUP}",
   headers=tok("ust"), json={"passed": True}).status_code, 403)
db = SessionLocal()
ck("auditda", db.query(models.AuditLog).filter(
    models.AuditLog.field == "Video: Metodika 1").count(), 2)
db.close()
print()
if fails:
    print(f"{len(fails)} ta XATO: {fails}"); sys.exit(1)
print("HAMMASI OK")
