"""Calendar reports, weighted drilldowns, owner history and branch/teacher isolation."""
import os, tempfile
from pathlib import Path
from datetime import timedelta
_tmp=tempfile.TemporaryDirectory(prefix="exam-monthly-")
os.environ["DATABASE_URL"]="sqlite:///"+(Path(_tmp.name)/"db.sqlite").as_posix()
import entry, models, roles
from database import SessionLocal, engine
from auth import create_access_token
from fastapi.testclient import TestClient
c=TestClient(entry.app);db=SessionLocal()
a=models.Branch(name="Real A");b=models.Branch(name="Real B");demo=models.Branch(name="Training",is_test=1)
db.add_all([a,b,demo]);db.flush()
f=models.User(username="exam-founder",full_name="Founder",role=roles.FOUNDER,password_hash="unused",is_active=1)
u=models.User(username="exam-teacher",full_name="Teacher",role=roles.TEACHER,branch_id=a.id,password_hash="unused",is_active=1)
v=models.User(username="other-teacher",full_name="Other",role=roles.TEACHER,branch_id=a.id,password_hash="unused",is_active=1)
ex=models.User(username="exam-local",full_name="Examiner",role=roles.EXAMINER,branch_id=a.id,password_hash="unused",is_active=1)
db.add_all([f,u,v,ex]);db.flush()
t=models.Teacher(full_name="Teacher",branch_id=a.id,user_id=u.id);other=models.Teacher(full_name="Other",branch_id=a.id,user_id=v.id)
db.add_all([t,other]);db.flush()
g=models.Group(name="Alpha",branch_id=a.id,teacher_id=t.id,level="Step 1")
g2=models.Group(name="Beta",branch_id=a.id,teacher_id=t.id)
g3=models.Group(name="Another branch",branch_id=b.id,teacher_id=other.id)
g4=models.Group(name="DEMO",branch_id=demo.id,teacher_id=other.id)
db.add_all([g,g2,g3,g4]);db.flush()
start=roles.local_today().replace(day=1);prev=start-timedelta(days=1)
def exam(group,day,marks):
    e=models.Exam(group_id=group.id,date=day,kind="unit",unit_no=1,status="approved")
    db.add(e);db.flush()
    for value,absent,counted in marks:
        s=models.Student(full_name=f"Student {e.id}-{value}",branch_id=group.branch_id,group_id=group.id,status="active")
        db.add(s);db.flush();db.add(models.ExamResult(exam_id=e.id,student_id=s.id,percent=value,absent=absent,counted=counted))
    return e
first=exam(g,start,[(80,0,1),(0,1,1),(0,0,0)])
exam(g2,start,[(40,0,1),(60,0,1)])
exam(g,prev,[(95,0,1)])
exam(g3,start,[(90,0,1)])
exam(g4,start,[(100,0,1)])
db.commit()
period=start.strftime("%Y-%m")
def get(user,url):
    return c.get(url,headers={"Authorization":"Bearer "+create_access_token({"sub":user.username})})
url=f"/api/reports/exams-monthly?period={period}"
r=get(f,url);assert r.status_code==200,r.text
d=r.json();assert d["exams"]==3 and d["avg"]==67.5,d
assert len(d["by_teacher"])==2 and len(d["by_group"])==3
teacher=next(x for x in d["by_teacher"] if x["key"]==t.id)
assert teacher["exams"]==2 and teacher["groups"]==2 and teacher["avg"]==60,teacher
assert set(teacher["test_ids"])=={x["key"] for x in d["tests"] if x["teacher_id"]==t.id}
assert next(x for x in d["tests"] if x["key"]==first.id)["absent"]==1
assert len(d["by_student"])==6  # includes absent/uncounted rows, not their scores
assert get(f,url+f"&branch_id={demo.id}").json()["avg"]==100
assert get(ex,url+f"&branch_id={b.id}").json()["avg"]==60
assert get(u,url).json()["exams"]==2
assert get(v,"/api/teacher/exam-history?period="+period).json()["exams"]==1
own=get(u,"/api/teacher/exam-history?period="+period).json()
assert len(own["history"])==2 and own["avg"]==60
# Group reassignments do not move already recorded exams to another teacher/branch.
g.teacher_id=other.id;g.branch_id=b.id;db.commit()
assert get(u,"/api/teacher/exam-history?period="+period).json()["avg"]==60
assert get(f,url+f"&branch_id={a.id}").json()["exams"]==2
assert get(f,"/api/reports/exams-monthly?period=2026-13").status_code==400
assert get(f,"/api/reports/exams-monthly?period=garbage").status_code==400
assert get(f,"/api/reports/exams-monthly?period=2000-01").json()["exams"]==0
print("PASS: calendar boundaries, weighted results, drilldowns, demo exclusion, own history, reassignment, access, empty/invalid month")
db.close();engine.dispose();_tmp.cleanup()
