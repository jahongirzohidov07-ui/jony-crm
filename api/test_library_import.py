"""Library bulk import: permissions, atomic validation and repeat safety."""
import os
import tempfile
from pathlib import Path

tmp = tempfile.TemporaryDirectory(prefix="library-import-")
os.environ["DATABASE_URL"] = "sqlite:///" + (Path(tmp.name) / "db.sqlite").as_posix()
from fastapi.testclient import TestClient
import entry
import models
import roles
from auth import create_access_token
from database import SessionLocal, engine

client = TestClient(entry.app)
db = SessionLocal()
users = []
for i, role in enumerate((roles.FOUNDER, roles.TEACHER)):
    user = models.User(username=f"import-{i}", full_name=f"Import {i}",
                       password_hash="unused", role=role, is_active=1)
    db.add(user); db.flush(); users.append(user)
db.commit()
def headers(user):
    return {"Authorization": "Bearer " + create_access_token({"sub": user.username})}
admin, teacher = map(headers, users)
def post(items, h=admin):
    return client.post("/api/library/import", headers=h, json={"items": items})
existing = entry._LI(title="Existing", kind="book", required=1, active=1, description="Keep")
db.add(existing); db.commit()
payload = [{"title": "  New   book ", "description": "Muallif: Test"},
           {"title": "existing", "description": "Do not replace"},
           {"title": "NEW BOOK"}]
assert client.post("/api/library/import", json={"items": payload}).status_code in (401,403)
assert post(payload, teacher).status_code == 403
r = post(payload)
assert r.status_code == 200, r.text
assert (r.json()["added"], r.json()["skipped"]) == (1, 2), r.text
r = post(payload)
assert (r.json()["added"], r.json()["skipped"]) == (0, 3)
db.expire_all()
new = db.query(entry._LI).filter_by(title="New book").one()
assert new.required == 0 and new.active == 1 and new.target_roles is None
assert db.get(entry._LI, existing.id).description == "Keep"
assert db.get(entry._LI, existing.id).required == 1
assert post([{"title": "Valid"}, {"title": ""}]).status_code == 400
assert db.query(entry._LI).filter_by(title="Valid").count() == 0
assert post([]).status_code == 400
assert post([{"title": "x"}] * 501).status_code == 400
assert post([{"title": "O‘qish"}, {"title": "o'qish"}]).json()["added"] == 1
source = "test-books.xlsx"
new.description = "Excel test. Manba: " + source + "."
db.add(new); db.add(entry._LP(item_id=new.id, user_id=users[1].id, percent=40)); db.commit()
r = client.post("/api/library/import/archive", headers=teacher, json={"source":source})
assert r.status_code == 403
r = client.post("/api/library/import/archive", headers=admin, json={"source":source})
assert r.status_code == 200 and r.json()["archived"] == 1, r.text
db.expire_all()
assert db.get(entry._LI, new.id).active == 0
assert db.get(entry._LI, existing.id).active == 1
assert db.query(entry._LP).filter_by(item_id=new.id).one().percent == 40
assert client.put(f"/api/library/{new.id}", headers=admin, json={"active":True}).status_code == 200
print("Library import: permissions, idempotency, optional status, validation, preservation OK")
db.close(); engine.dispose(); tmp.cleanup()
