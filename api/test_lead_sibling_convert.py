"""Shared parent phone: explicit sibling confirmation preserves the original."""
import os, tempfile
from pathlib import Path
tmp = tempfile.TemporaryDirectory(prefix="lead-sibling-")
os.environ["DATABASE_URL"] = "sqlite:///" + (Path(tmp.name) / "db.sqlite").as_posix()
from fastapi.testclient import TestClient
import entry, models, roles
from database import SessionLocal, engine
from auth import create_access_token
c = TestClient(entry.app)
db = SessionLocal()
b = models.Branch(name="Test branch"); db.add(b); db.flush()
u = models.User(username="sibling-admin", full_name="Administrator", password_hash="unused", role=roles.SALES_MANAGER, branch_id=b.id, is_active=1)
db.add(u)
old = models.Student(full_name="Older sibling", parent_phone="+998 90 123 45 67", status="archived", branch_id=b.id, note="Keep original history")
db.add(old)
lead = models.Lead(full_name="Younger sibling", phone="901234567", branch_id=b.id, stage="trial_attended")
db.add(lead); db.commit()
old_id, lead_id = old.id, lead.id
headers={"Authorization":"Bearer " + create_access_token({"sub":u.username})}
url=f"/api/leads/{lead_id}/convert"
r=c.post(url,headers=headers,json={})
assert r.status_code == 409, r.text
assert r.json()["detail"]["message"].startswith("Bu odam bazada allaqachon bor:")
assert r.json()["detail"]["duplicate_student_id"]==old_id
db.expire_all()
assert db.query(models.Student).count()==1
assert db.get(models.Lead,lead_id).converted_student_id is None
original_phone = db.get(models.Student,old_id).parent_phone
assert c.post(url,headers=headers,json={"force":False,"family_sibling_id":old_id}).status_code==400
assert c.post(url,headers=headers,json={"force":True,"family_sibling_id":999999}).status_code==400
r=c.post(url,headers=headers,json={"force":True,"family_sibling_id":old_id})
assert r.status_code==200,r.text
new_id=r.json()["id"]
assert new_id != old_id
db.expire_all()
assert db.get(models.Student,new_id).full_name=="Younger sibling"
assert db.get(models.Student,new_id).phone=="901234567"
assert db.get(models.Student,old_id).status=="archived"
assert db.get(models.Student,old_id).parent_phone==original_phone
assert db.get(models.Student,old_id).note=="Keep original history"
parent_id = db.get(models.Student,old_id).parent_id
assert parent_id and db.get(models.Student,new_id).parent_id==parent_id
assert db.get(models.Student,new_id).parent_phone=="901234567"
assert db.query(models.Parent).count()==1
assert db.query(models.AuditLog).filter_by(entity_id=new_id,action="family_link").count()==1
assert db.get(models.Lead,lead_id).converted_student_id==new_id
assert c.post(url,headers=headers,json={"force":True}).status_code==400
assert db.query(models.Student).count()==2
# An archived sibling never qualifies the sole studying child for a discount.
import common
from datetime import timedelta
young = db.get(models.Student, new_id)
older = db.get(models.Student, old_id)
assert common._family_discount_percent(db, young) == 0
first = roles.local_today().replace(day=1)
g = models.Group(name="Family test", branch_id=b.id, monthly_fee=480000,
                 lesson_price=40000, standard_lessons_per_month=12, lesson_days="")
db.add(g); db.flush()
for day in range(12):
    db.add(models.Lesson(group_id=g.id, date=first + timedelta(days=day)))
young.group_id = older.group_id = g.id
young.enrolled_date = older.enrolled_date = first
db.commit()
r = c.post(f"/api/students/{new_id}/activate", headers=headers, json={"on":first.isoformat()})
assert r.status_code == 200, r.text
db.expire_all()
assert common._family_discount_percent(db, young) == 0
period = first.isoformat()[:7]
def charge(sid):
    return db.query(models.Payment).filter_by(student_id=sid,kind="charge",period=period).one()
assert charge(new_id).amount == -480000, charge(new_id).amount
# Second child returns: both new charge and existing sibling's bill become 90%.
r = c.post(f"/api/students/{old_id}/activate", headers=headers, json={"on":first.isoformat()})
assert r.status_code == 200, r.text
db.expire_all()
assert common._family_discount_percent(db, young) == 10
assert charge(new_id).amount == -432000, charge(new_id).amount
assert charge(old_id).amount == -432000, charge(old_id).amount
common._refresh_family_charges(db, young); db.commit()
assert charge(new_id).amount == -432000  # repeated refresh cannot compound discount
assert db.query(models.Discount).filter_by(kind="family").count() == 0
# A further confirmed sibling reuses the same family, instead of creating another.
third = models.Lead(full_name="Third sibling", phone="998901234567", branch_id=b.id)
db.add(third); db.commit()
r = c.post(f"/api/leads/{third.id}/convert", headers=headers,
           json={"force":True,"family_sibling_id":old_id,"group_id":g.id,"enrolled_date":first.isoformat()})
assert r.status_code == 200, r.text
db.expire_all()
child = db.get(models.Student, r.json()["id"])
assert child.parent_id == parent_id
assert db.query(models.Parent).count() == 1
# Payment/attendance automatic activation follows the same discount rule.
common._activate_student(db, child, on=first, reason="Test", user=u); db.commit()
assert charge(child.id).amount == -432000, charge(child.id).amount
assert charge(new_id).amount == -432000
# A name-only duplicate must not be silently turned into a family member.
other = models.Lead(full_name=young.full_name, phone="998907654321", branch_id=b.id)
db.add(other); db.commit()
other_url = f"/api/leads/{other.id}/convert"
r = c.post(other_url, headers=headers, json={})
assert r.status_code == 409, r.text
assert r.json()["detail"]["duplicate_student_id"] is None
r = c.post(other_url, headers=headers, json={"force":True,"family_sibling_id":new_id})
assert r.status_code == 400, r.text
db.expire_all()
assert db.get(models.Lead,other.id).converted_student_id is None
print("PASS: sibling confirmation, family reuse, archived exclusion, two-child 10%, both bills, auto activation, no double discount")

db.close(); engine.dispose(); tmp.cleanup()
