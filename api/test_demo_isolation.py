"""Production aggregates exclude both legacy-named and flagged training branches."""
import os, tempfile
from pathlib import Path
from datetime import datetime
_tmp = tempfile.TemporaryDirectory(prefix="demo-isolation-")
os.environ["DATABASE_URL"] = "sqlite:///" + (Path(_tmp.name) / "db.sqlite").as_posix()
import entry, common, models, roles
from database import SessionLocal, engine
from auth import create_access_token
from fastapi.testclient import TestClient
c = TestClient(entry.app)
db = SessionLocal()
real = models.Branch(name="Real branch")
legacy = models.Branch(name="Test - filial")
flagged = models.Branch(name="Training DEMO_TOKEN", is_test=1)
db.add_all([real,legacy,flagged]); db.flush()
founder = models.User(username="demo-founder", full_name="Founder", role=roles.FOUNDER, password_hash="unused", is_active=1)
admin = models.User(username="demo-admin", full_name="Admin", role=roles.ADMINISTRATOR, branch_id=real.id, password_hash="unused", is_active=1)
db.add_all([founder,admin]); db.flush()
db.add(models.UserBranch(user_id=admin.id,branch_id=flagged.id))
today = roles.local_today()
for b, score in [(real,40),(legacy,100),(flagged,100)]:
    label = "Real" if b == real else "DEMO_TOKEN"
    t = models.Teacher(full_name=label, branch_id=b.id)
    db.add(t);db.flush()
    g = models.Group(name=label,branch_id=b.id,teacher_id=t.id)
    db.add(g);db.flush()
    st = models.Student(full_name=label,branch_id=b.id,group_id=g.id,status="active",enrolled_date=today,address=label,school=label)
    db.add(st);db.flush()
    e = models.Exam(group_id=g.id,date=today,kind="unit",status="approved")
    db.add(e);db.flush()
    db.add(models.ExamResult(exam_id=e.id,student_id=st.id,percent=score,absent=0,counted=1))
    db.add(models.Payment(student_id=st.id,kind="payment",amount=100 if b==real else 99999,created_at=datetime.utcnow()))
    db.add(models.Lead(full_name=label,branch_id=b.id,source="visit",address=label,school=label))
    db.add(models.NpsResponse(student_id=st.id,branch_id=b.id,teacher_id=t.id,quarter=f"{today.year}-Q{(today.month-1)//3+1}",who="student",score=4 if b==real else 10))
db.commit()
headers={"Authorization":"Bearer "+create_access_token({"sub":founder.username})}
def get(path):
    r=c.get(path,headers=headers)
    assert r.status_code==200,(path,r.status_code,r.text[:600])
    return r.json()
a=get("/api/examiner/analysis")
assert a["total_results"]==1,a
assert len(a["by_branch"])==1 and a["by_branch"][0]["avg"]==40,a
assert len(get("/api/examiner/exams"))==1
assert get(f"/api/examiner/analysis?branch_id={flagged.id}")["total_results"]==1
assert get(f"/api/examiner/analysis?branch_id={flagged.id}")["by_branch"][0]["avg"]==100
assert get("/api/dashboard")["active_students"]==1
assert get("/api/dashboard")["month_income"]==100
assert get("/api/nps/summary")["total"]==1
assert get("/api/reports/cashflow?months=1")["totals"]["income"]==100
assert common._payroll_branches(db,founder)=={real.id}
for path in ["/api/analytics/exam-trend","/api/ceo/branches","/api/analytics/academic", "/api/analytics/sources","/api/analytics/acquisition","/api/analytics/romi", "/api/smm/sales-plan", "/api/reports/cash-day", f"/api/reports/cashflow-ledger?year={today.year}&month={today.month}"]:
    result=get(path)
    assert "DEMO_TOKEN" not in str(result),(path,result)
    print("PASS",path)
# Additional practice assignments never contaminate an administrator's all-branch scope.
ids={s.branch_id for s in common.scope_to_branch(db.query(models.Student),models.Student,admin).all()}
assert ids=={real.id},ids
assert common._branch_scope_ids(db,admin,None)==[real.id]
assert common._branch_scope_ids(db,admin,flagged.id)==[flagged.id]
# Flag changes are visible immediately, even after an earlier scope lookup.
assert flagged.id in common.test_branch_ids(db)
flagged.is_test=0;db.commit()
assert flagged.id not in common.test_branch_ids(db)
flagged.is_test=1;real.is_test=1;db.commit()
assert common._branch_scope_ids(db,founder,None)==[-1]
assert get("/api/examiner/analysis")["total_results"]==0
print("PASS: exam averages, counts, revenue, NPS, analytics, explicit demo view, staff scope, flag changes, empty scope")
db.close();engine.dispose();_tmp.cleanup()
