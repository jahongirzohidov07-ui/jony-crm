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
assert r.json()["detail"].startswith("Bu odam bazada allaqachon bor:")
db.expire_all()
assert db.query(models.Student).count()==1
assert db.get(models.Lead,lead_id).converted_student_id is None
original_phone = db.get(models.Student,old_id).parent_phone
r=c.post(url,headers=headers,json={"force":True})
assert r.status_code==200,r.text
new_id=r.json()["id"]
assert new_id != old_id
db.expire_all()
assert db.get(models.Student,new_id).full_name=="Younger sibling"
assert db.get(models.Student,new_id).phone=="901234567"
assert db.get(models.Student,old_id).status=="archived"
assert db.get(models.Student,old_id).parent_phone==original_phone
assert db.get(models.Student,old_id).note=="Keep original history"
assert db.get(models.Lead,lead_id).converted_student_id==new_id
assert c.post(url,headers=headers,json={"force":True}).status_code==400
assert db.query(models.Student).count()==2
print("PASS: duplicate warning, explicit sibling conversion, original preserved, repeat rejected")
db.close(); engine.dispose(); tmp.cleanup()
