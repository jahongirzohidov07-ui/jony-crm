"""Run from repository root: python scripts/test-russian-placement-api.py."""
import os
import sys
import uuid
from pathlib import Path
from types import SimpleNamespace
from itertools import product

os.environ['DATABASE_URL'] = 'sqlite://'
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'api'))
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from database import Base, get_db
import models, roles
import russian_placement as rp

# 2026-10-22: state'siz "answers" yo'li faqat PLACEMENT_LEGACY_SUBMIT_UNTIL
# gacha ochiq. Bu test baho va saqlashni tekshiradi — sanadan qat'i nazar
# ishlasin.
roles.PLACEMENT_LEGACY_SUBMIT_UNTIL = '2099-12-31'

assert len(rp.BANK) == 48
assert len({q['id'] for q in rp.BANK}) == 48
all_right = {q['id']: q['answer'] for q in rp.BANK}
unknown = {q['id']: -1 for q in rp.BANK}
assert rp.assess(unknown)['score'] == 0
assert rp.assess(unknown)['lesson'] == 1
assert rp.assess(all_right)['allPassed']
assert rp.assess(all_right)['lesson'] is None
assert rp.assess(all_right)['month'] is None
for stage in range(1, 7):
    qs = [q for q in rp.BANK if q['stage'] == stage]
    assert len(qs) == 8
    assert [q['skill'] for q in qs].count('grammar') == 4
    assert [q['skill'] for q in qs].count('vocabulary') == 2
    assert [q['skill'] for q in qs].count('reading') == 2
    for q in qs:
        # 2026-10-22: 5 ta haqiqiy variant ("Bilmayman" sahifada alohida)
        assert len(q['options']) == len(set(q['options'])) == 5
        assert q['answer'] in range(4)  # kalit indeksi o'zgarmagan (5-variant oxirida)
        assert q['prompt'] and q['topic']
        if q['skill'] == 'reading':
            assert q['text']
    # Every possible correctness pattern, including each floor and exact boundary.
    for mask in product((False, True), repeat=8):
        answers = {**all_right, **{q['id']: q['answer'] if yes else -1 for q, yes in zip(qs, mask)}}
        passed = sum(mask) >= 6 and sum(mask[:4]) >= 3 and sum(mask[6:]) >= 1
        result = rp.assess(answers)
        assert result['blocks'][stage-1]['passed'] == passed
        assert result['allPassed'] == passed
        if not passed:
            assert result['stage'] == stage
            assert result['month'] == (stage-1)*2+1
            assert result['lesson'] == (stage-1)*24+1
print('PASS: 48 independent items, 1,536 score patterns, all six entry points, sentinel and prerequisite floors')

engine = create_engine('sqlite://', connect_args={'check_same_thread': False}, poolclass=StaticPool)
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
def db():
    with Session() as s:
        yield s
app = FastAPI()
app.include_router(rp.router)
app.dependency_overrides[get_db] = db
client = TestClient(app, raise_server_exceptions=False)
with Session() as s:
    a, b = models.Branch(name='Chilonzor'), models.Branch(name='Yunusobod')
    s.add_all([a, b]); s.commit(); bid, other = a.id, b.id

def payload(**extra):
    return dict(attempt_id=str(uuid.uuid4()), full_name='Анна Алиева', phone='901234567',
                branch_id=bid, answers=all_right, **extra)
def post(p):
    return client.post('/api/public/russian-placement', json=p)

public = client.get('/api/public/russian-placement/questions')
assert public.status_code == 200
assert len(public.json()['questions']) == 48
assert all('answer' not in q for q in public.json()['questions'])
p = payload()
r = post(p)
assert r.status_code == 200, r.text
result = r.json()['result']
assert result['score'] == 48 and result['allPassed'] and result['lesson'] is None
assert result['recommendation'] == dict(branch_id=bid, branch_name='Chilonzor', stage=None,
                                       label=result['label'], oral_required=True)
assert post(p).json() == r.json()
with Session() as s:
    assert s.query(models.RussianPlacementResult).count() == 1
    assert s.query(models.Lead).count() == 1
    assert s.query(models.Lead).first().note.count('48/48') == 1
assert post({**p, 'full_name': 'Other Person'}).status_code == 409
assert post({**p, 'answers': unknown}).status_code == 409
assert post({**payload(), 'full_name': 'Анна  Алиева', 'phone': '+998 90 123 45 67'}).status_code == 200
assert post({**payload(), 'full_name': 'анна алиева'}).status_code == 200
assert post({**payload(), 'full_name': 'Брат Алиев'}).status_code == 200
assert post({**payload(), 'branch_id': other}).status_code == 200
with Session() as s:
    assert s.query(models.Lead).count() == 3, 'name AND normalized phone AND branch identity'
    assert s.query(models.RussianPlacementResult).count() == 5

# A later perfect block cannot bridge an early gap, including in persisted results.
r = post({**payload(), 'answers': {**all_right, **{q['id']: -1 for q in rp.BANK if q['stage'] == 2}}})
assert r.status_code == 200, r.text
assert r.json()['result']['lesson'] == 25
assert r.json()['result']['recommendation']['stage'] == 2
# 2026-10-22: 5 ta variant (0..4) — 5 chegaradan tashqari
for bad in ({}, {**all_right, 'rp-1': -2}, {**all_right, 'rp-1': 5},
            {**all_right, 'rp-1': True}, {**all_right, 'rp-1': '0'},
            {**all_right, 'rp-1': 0.0}, {**all_right, 'alien': 0}):
    assert post({**payload(), 'answers': bad}).status_code == 422
wrong_ids = dict(all_right); wrong_ids['alien'] = wrong_ids.pop('rp-1')
assert post({**payload(), 'answers': wrong_ids}).status_code == 422
for bad in ({'branch_id': 9999}, {'branch_id': True}, {'phone': '123456789000'},
            {'full_name': '   '}, {'attempt_id': 'invalid'}):
    assert post({**payload(), **bad}).status_code == 422
assert client.get('/api/russian-placement/results').status_code in (401, 403)
dep = rp.results.__defaults__[-1].dependency
staff = next(role for role in roles.LEAD_ACCESS if role not in roles.ORG_WIDE_ROLES)
app.dependency_overrides[dep] = lambda: SimpleNamespace(id=9999, role=staff, branch_id=bid)
rows = client.get('/api/russian-placement/results').json()['rows']
assert len(rows) == 5
assert all(row['result']['recommendation']['branch_id'] == bid for row in rows)
response = client.get(f'/api/russian-placement/results?branch_id={other}')
assert response.status_code == 403 or all(row['result']['recommendation']['branch_id'] == bid for row in response.json()['rows'])
app.dependency_overrides[dep] = lambda: SimpleNamespace(id=9999, role=staff, branch_id=None)
assert client.get('/api/russian-placement/results').json()['rows'] == []
org = next(role for role in roles.LEAD_ACCESS if role in roles.ORG_WIDE_ROLES)
app.dependency_overrides[dep] = lambda: SimpleNamespace(id=9999, role=org, branch_id=None)
assert len(client.get(f'/api/russian-placement/results?branch_id={other}').json()['rows']) == 1
print('PASS: authoritative save, no public key, replay/conflict, Cyrillic family identity, validation, branch/auth isolation')

# Force a database failure after lead/note mutations; nothing may persist.
def fail_commit(session):
    raise IntegrityError('forced regression failure', {}, Exception('forced'))
with Session() as s:
    before = (s.query(models.Lead).count(), s.query(models.RussianPlacementResult).count(),
              [(l.id, l.note) for l in s.query(models.Lead).all()])
event.listen(Session, 'before_commit', fail_commit)
try:
    assert post({**payload(), 'full_name': 'Rollback New Learner'}).status_code == 500
    assert post(payload()).status_code == 500
finally:
    event.remove(Session, 'before_commit', fail_commit)
with Session() as s:
    after = (s.query(models.Lead).count(), s.query(models.RussianPlacementResult).count(),
             [(l.id, l.note) for l in s.query(models.Lead).all()])
assert after == before
original_rate = rp._web_rate_ok
rp._web_rate_ok = lambda _: False
try:
    assert post(payload()).status_code == 429
    assert post(p).status_code == 200, 'idempotent replay bypasses throttle'
finally:
    rp._web_rate_ok = original_rate
print('PASS: failed transaction rolls back new lead, existing note and result; throttled retries stay idempotent')
