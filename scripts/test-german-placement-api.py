import os,sys,json,uuid
os.environ['DATABASE_URL']='sqlite://'
sys.path.insert(0,os.path.abspath('api'))
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import german_placement as gp
from database import Base,get_db
import models,roles
# 2026-10-22: state'siz "answers" yo'li faqat PLACEMENT_LEGACY_SUBMIT_UNTIL gacha
# ochiq. Bu test baho va saqlashni tekshiradi — sanadan qat'i nazar ishlasin.
roles.PLACEMENT_LEGACY_SUBMIT_UNTIL='2099-12-31'
engine=create_engine('sqlite://',connect_args={'check_same_thread':False},poolclass=StaticPool)
Base.metadata.create_all(engine)
Session=sessionmaker(bind=engine)
def db():
 with Session() as s: yield s
app=FastAPI();app.include_router(gp.router);app.dependency_overrides[get_db]=db
client=TestClient(app)
with Session() as s:
 b=models.Branch(name='Local QA');s.add(b);s.commit();bid=b.id
answers={q['id']:q['answer'] for q in gp.BANK}
p={'attempt_id':str(uuid.uuid4()),'full_name':'QA Learner','phone':'901234567','branch_id':bid,'answers':answers}
r=client.post('/api/public/german-placement',json=p);assert r.status_code==200,r.text
assert r.json()['result']['lesson']==70
assert client.post('/api/public/german-placement',json=p).status_code==200
with Session() as s:
 assert s.query(models.GermanPlacementResult).count()==1
 assert s.query(models.Lead).count()==1
 assert '48/48' in s.query(models.Lead).first().note
bad={**p,'full_name':'Other Person'};assert client.post('/api/public/german-placement',json=bad).status_code==409
p2={**p,'attempt_id':str(uuid.uuid4()),'full_name':'QA Sibling'};assert client.post('/api/public/german-placement',json=p2).status_code==200
p3={**p,'attempt_id':str(uuid.uuid4())};assert client.post('/api/public/german-placement',json=p3).status_code==200
with Session() as s: assert s.query(models.Lead).count()==2
assert client.post('/api/public/german-placement',json={**p,'attempt_id':str(uuid.uuid4()),'answers':{}}).status_code==422
assert client.post('/api/public/german-placement',json={**p,'attempt_id':str(uuid.uuid4()),'branch_id':99999}).status_code==422
assert client.get('/api/german-placement/results').status_code in (401,403)
print('PASS: server scoring, CRM lead+result, replay idempotency, payload conflict, shared family phone, existing lead reuse, validation, anonymous read denied')

from types import SimpleNamespace
admin_role=next(r for r in roles.LEAD_ACCESS if r not in roles.ORG_WIDE_ROLES)
auth_dependency=gp.results.__defaults__[-1].dependency
app.dependency_overrides[auth_dependency]=lambda: SimpleNamespace(id=9999,role=admin_role,branch_id=bid)
assert len(client.get('/api/german-placement/results').json()['rows'])==3
app.dependency_overrides[auth_dependency]=lambda: SimpleNamespace(id=9999,role=admin_role,branch_id=99999)
assert client.get('/api/german-placement/results').json()['rows']==[]
app.dependency_overrides[auth_dependency]=lambda: SimpleNamespace(id=9999,role=admin_role,branch_id=None)
assert client.get('/api/german-placement/results').json()['rows']==[]
print('PASS: same-branch visibility, other-branch and unassigned staff isolation')

# Unknown choices remain answered and persist as -1, with no points.
unknown={q['id']:-1 for q in gp.BANK}
pu={**p,'attempt_id':str(uuid.uuid4()),'answers':unknown}
ru=client.post('/api/public/german-placement',json=pu)
assert ru.status_code==200,ru.text
assert ru.json()['result']['score']==0
assert ru.json()['result']['lesson']==1
with Session() as s:
 row=s.query(models.GermanPlacementResult).filter_by(attempt_id=pu['attempt_id']).one()
 assert json.loads(row.answers_json)==unknown
for value in (None,False,'-1',5,-2):  # 2026-10-22: 5 ta variant (0..4), 5 — chegaradan tashqari
 invalid={**unknown,'gp-1':value}
 assert client.post('/api/public/german-placement',json={**pu,'attempt_id':str(uuid.uuid4()),'answers':invalid}).status_code==422
print('PASS: unknown choices persist as answered, zero score, prerequisite gate and strict invalid-answer rejection')
