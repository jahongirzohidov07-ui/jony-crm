import os, sys
from datetime import date, timedelta
os.environ["DATABASE_URL"] = "sqlite:////tmp/grid.db"
if os.path.exists("/tmp/grid.db"): os.remove("/tmp/grid.db")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fastapi.testclient import TestClient
import main, models, entry
from database import SessionLocal
from auth import hash_password
c = TestClient(main.app); fails=[]
def ck(n,g,w):
    ok=g==w; print(("OK  " if ok else "XATO ")+n+f": {g}"+("" if ok else f" (kutilgan {w})"))
    if not ok: fails.append(n)
db=SessionLocal()
b=models.Branch(name="B"); db.add(b); db.commit()
t=models.Teacher(full_name="Asliddin Nabiyev", branch_id=b.id, is_active=1)
db.add(t); db.commit()
g=models.Group(name="North Carolina", branch_id=b.id, teacher_id=t.id,
               lesson_time="12:00-14:00"); db.add(g); db.commit()
old=models.Group(name="Eski guruh", branch_id=b.id, teacher_id=t.id); db.add(old); db.commit()
st=models.Student(full_name="Boboyeva Muslima", branch_id=b.id,
                  group_id=g.id, status="frozen")  # MUZLATILGAN
db.add(st); db.commit()
SID, GID, OID = st.id, g.id, old.id
today=date.today(); y,m=today.year, today.month
d1=date(y,m,3); d2=date(y,m,5); d3=date(y,m,7); d4=date(y,m,9)
ls=[]
for dd,grp in ((d1,GID),(d2,GID),(d3,GID),(d4,GID),(d1,OID)):
    l=models.Lesson(group_id=grp, date=dd, teacher_id=t.id, held=1)
    db.add(l); db.commit(); ls.append(l)
# davomat: kelmadi, keldi, kechikdi, (4-dars belgilanmagan), eski guruhda keldi
db.add_all([
 models.Attendance(lesson_id=ls[0].id, student_id=SID, present=0),
 models.Attendance(lesson_id=ls[1].id, student_id=SID, present=1),
 models.Attendance(lesson_id=ls[2].id, student_id=SID, present=2),
 models.Attendance(lesson_id=ls[4].id, student_id=SID, present=1)])
db.add(models.DailyGrade(lesson_id=ls[1].id, student_id=SID, score=9))
db.add(models.User(username="a", full_name="Asoschi", role="founder",
                   password_hash=hash_password("x"), is_active=1))
db.commit(); db.close()
H={"Authorization":"Bearer "+c.post("/api/auth/login",json={"username":"a","password":"x"}).json()["access_token"]}
r=c.get(f"/api/students/{SID}/attendance-grid?year={y}&month={m}", headers=H)
ck("200", r.status_code, 200)
j=r.json()
ck("muzlatilgan bo'lsa ham ko'rinadi", j["status"], "frozen")
ck("ikki guruh chiqdi", len(j["groups"]), 2)
cur=[x for x in j["groups"] if x["current"]][0]
ck("joriy guruh birinchi", j["groups"][0]["group"], "North Carolina")
ck("4 ta dars kuni", len(cur["days"]), 4)
ck("holatlar", [x["state"] for x in cur["days"]],
   ["absent","present","late","none"])
ck("baho ko'rinadi", cur["days"][1]["grade"], 9)
ck("keldi 2 (kechikkan ham keldi)", cur["present"], 2)
ck("kelmadi 1", cur["absent"], 1)
ck("belgilanmagan 1", cur["unmarked"], 1)
ck("foiz 67", cur["percent"], 67)
old_row=[x for x in j["groups"] if not x["current"]][0]
ck("eski guruh ham ko'rinadi", old_row["group"], "Eski guruh")
prev = c.get(f"/api/students/{SID}/attendance-grid?year={y}&month={1 if m!=1 else 2}", headers=H).json()
ck("boshqa oyda dars yo'q", len(prev["groups"]) <= 1, True)
print()
if fails: print("XATOLAR:", ", ".join(fails)); sys.exit(1)
print("HAMMASI O'TDI")
