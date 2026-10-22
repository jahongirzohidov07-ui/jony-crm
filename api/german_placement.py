"""German intake: server-scored, atomic and retry-safe CRM persistence.

2026-10-22 — taxminan bosishga qarshi (placement_guard.py). Savollar
endi serverdan BITTADAN beriladi (/start, /answer, /current) va javob
kaliti mijozga umuman chiqmaydi. "Bilmayman" = choice -1 (xato, alohida
sanaladi). Savol berilgandan o'qishga yetmaydigan tezlikda kelgan javob
to'g'ri bo'lsa ham XATO va "juda tez" deb yoziladi. Holat shifrlangan
"state" tokenda yuradi — yangi jadval/ustun yo'q. Deploydan oldin
ochilgan sahifa javoblarni eskicha (answers) yuborsa ham qabul qilinadi,
faqat vaqt tekshirilmaydi (timed=false) — roles.PLACEMENT_LEGACY_SUBMIT_UNTIL
sanasigacha; undan keyin 409 "Sahifani yangilang".
"""
import hashlib
import json
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Annotated, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field, StrictInt
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
import models, roles
import placement_guard as PG
from auth import require_role
from database import get_db
from common import _ensure_public_id, scope_to_branch
from leads import _web_rate_ok

router = APIRouter()
BANK = json.loads(Path(__file__).with_name('german_placement_bank.json').read_text(encoding='utf-8'))
LABELS = ['A1 poydevor', 'A1 yakuni', 'A2 poydevor', 'A2 yakuni', 'B1 poydevor', 'B1 yakuni']
SKILLS = {'grammar': 'Grammatika', 'vocabulary': "Lug'at", 'reading': "O'qib tushunish"}
# Savollar bank tartibida bittadan, faqat oldinga (placement_guard.SeqTest).
SEQ = PG.SeqTest('de-placement', BANK)

class Submission(BaseModel):
    attempt_id: UUID
    full_name: str = Field(min_length=3, max_length=120)
    phone: str = Field(min_length=9, max_length=24)
    branch_id: StrictInt
    # Yangi sahifa: server bergan holat — javoblar va "juda tez" belgilari
    # shu tokendan olinadi, mijoz yuborgan javoblardan emas.
    state: Optional[str] = Field(default=None, max_length=8000)
    # Eski sahifa (deploydan oldin ochilgan): javoblarni o'zi yuboradi.
    answers: Optional[Annotated[dict[str, StrictInt], Field(min_length=48, max_length=48)]] = None

class StartIn(BaseModel):
    attempt_id: UUID

class StateIn(BaseModel):
    attempt_id: Optional[UUID] = None
    state: str = Field(min_length=16, max_length=8000)

class AnswerIn(StateIn):
    qid: str = Field(min_length=1, max_length=32)
    choice: StrictInt          # 0..variantlar-1, "Bilmayman" = -1

def assess(answers, fast=frozenset(), timed=False):
    """Server bahosi. fast — "juda tez" kelgan savollar: kalitga mos
    bo'lsa ham XATO. "Bilmayman" (-1) — xato, alohida sanaladi."""
    by_id={q['id']:q for q in BANK}
    if set(answers)!=set(by_id) or any(type(v) is not int or v not in range(-1,len(by_id[k]['options'])) for k,v in answers.items()):
        raise HTTPException(422, '48 ta savolga javob bering')
    fast=set(fast)&set(by_id)
    def ok(q): return answers[q['id']]==q['answer'] and q['id'] not in fast
    def idk(qs): return sum(answers[q['id']]==PG.IDK for q in qs)
    def quick(qs): return sum(q['id'] in fast for q in qs)
    blocks=[]
    for month in range(1,7):
        qs=[q for q in BANK if q['month']==month]
        right=[q for q in qs if ok(q)]
        passed=len(right)>=6 and sum(q['skill']=='grammar' for q in right)>=3 and sum(q['skill']=='reading' for q in right)>=1
        blocks.append(dict(month=month,label=LABELS[month-1],correct=len(right),total=len(qs),passed=passed,idk=idk(qs),fast=quick(qs)))
    gap=next((b['month'] for b in blocks if not b['passed']),None)
    month=gap or 6
    skills=[dict(skill=k,label=v,total=sum(q['skill']==k for q in BANK),correct=sum(q['skill']==k and ok(q) for q in BANK),
                 idk=idk([q for q in BANK if q['skill']==k]),fast=quick([q for q in BANK if q['skill']==k])) for k,v in SKILLS.items()]
    res=dict(score=sum(b['correct'] for b in blocks),month=month,lesson=(month-1)*12+1 if gap else 70,blocks=blocks,
                label=LABELS[month-1] if gap else 'B1 bilimlari: to‘rt ko‘nikma sinovi kerak',
                gaps=[q['topic'] for q in BANK if q['month']<=month and not ok(q)],
                allPassed=gap is None,skills=skills,timed=bool(timed),
                fast_ids=[q['id'] for q in BANK if q['id'] in fast],
                **PG.summary(idk(BANK),len(fast),len(BANK)))
    # State'siz (eski sahifa) yuborishda vaqt o'lchanmagan: "juda tez" — 0 emas,
    # noma'lum (None, "—"), shunda bunday natija hech qachon "toza" ko'rinmaydi.
    return res if timed else PG.untimed(res)

# ---- Savollar bittadan (2026-10-22) ----------------------------------
@router.post('/api/public/german-placement/start')
def start(payload: StartIn):
    """1-savol va state. Savol berilgan vaqt state ichida (server soati)."""
    return SEQ.start(payload.attempt_id)

@router.post('/api/public/german-placement/current')
def current(payload: StateIn):
    """Sahifa yangilanganda joriy savol — vaqt qayta boshlanmaydi."""
    return SEQ.current(payload.state, payload.attempt_id)

@router.post('/api/public/german-placement/answer')
def answer(payload: AnswerIn):
    """Javob qabul qilinadi, keyingi savol beriladi. Baho aytilmaydi."""
    return SEQ.answer(payload.state, payload.qid, payload.choice, payload.attempt_id)

@router.post('/api/public/german-placement')
def submit(payload: Submission, request: Request, db: Session=Depends(get_db)):
    name=' '.join(payload.full_name.split())
    phone=re.sub(r'\D','',payload.phone)
    if len(phone)==9: phone='998'+phone
    if len(name)<3 or not re.fullmatch(r'998\d{9}',phone):
        raise HTTPException(422,'Ism va O‘zbekiston telefon raqamini tekshiring')
    if payload.state:
        answers,fast=SEQ.final(payload.state,payload.attempt_id); timed=True
    elif payload.answers is not None:
        # Eski sahifa: vaqt o'lchanmagan — "juda tez" qoidasi qo'llanmaydi.
        answers,fast,timed=payload.answers,set(),False
    else:
        raise HTTPException(422,'48 ta savolga javob bering')
    result=assess(answers,fast,timed)
    digest=hashlib.sha256(json.dumps([name,phone,payload.branch_id,answers],sort_keys=True).encode()).hexdigest()
    def existing():
        row=db.query(models.GermanPlacementResult).filter_by(attempt_id=str(payload.attempt_id)).first()
        if row and row.payload_hash!=digest: raise HTTPException(409,'Bu test avval boshqa ma’lumot bilan saqlangan')
        return row
    old=existing()
    if old: return {'saved':True,'result':PG.public(json.loads(old.result_json))}
    # Eski yo'l faqat deploydan keyingi qisqa muddatga (roles.PLACEMENT_LEGACY_SUBMIT_UNTIL):
    # keyin qo'lda yasalgan so'rov "juda tez" qoidasini chetlab o'tolmasin.
    if not timed and not PG.legacy_submit_open(): raise HTTPException(409,PG.LEGACY_CLOSED_TEXT)
    branch=db.get(models.Branch,payload.branch_id)
    if not branch or (branch.name or '').lower().startswith('test'):
        raise HTTPException(422,'Filialni tanlang')
    if not _web_rate_ok(request.client.host if request.client else '?'):
        raise HTTPException(429,'Juda ko‘p urinish. Keyinroq qayta yuboring.')
    recent=db.query(models.GermanPlacementResult).filter(models.GermanPlacementResult.phone==phone,models.GermanPlacementResult.created_at>datetime.utcnow()-timedelta(days=1)).count()
    if recent>=10: raise HTTPException(429,'Bu raqam uchun bugungi testlar chegarasiga yetildi')
    # Phone alone is never identity: siblings may share a parent's number.
    candidates=db.query(models.Lead).filter(models.Lead.branch_id==branch.id,func.lower(models.Lead.full_name)==name.lower()).all()
    matching=[l for l in candidates if re.sub(r'\D','',l.phone or '') in (phone,phone[3:])]
    lead=matching[0] if len(matching)==1 else None
    if lead is None:
        lead=models.Lead(full_name=name,phone='+'+phone,branch_id=branch.id,source='website',stage='new',created_by='Nemis kirish testi')
        db.add(lead); db.flush(); _ensure_public_id(db,'lead',lead)
    note=f"Nemis testi: {result['score']}/48 · {result['month']}-oy, {result['lesson']}-dars. Ustoz tasdig‘i kerak."
    if result['idk'] or result['fast']: note+=' '+PG.guard_text(result['idk'],result['fast'],result['guess_warning'])
    lead.note=((lead.note or '')+'\n'+note).strip()
    row=models.GermanPlacementResult(attempt_id=str(payload.attempt_id),payload_hash=digest,lead_id=lead.id,branch_id=branch.id,full_name=name,phone=phone,result_json=json.dumps(result,ensure_ascii=False),answers_json=json.dumps(answers))
    db.add(row)
    try: db.commit()
    except IntegrityError:
        db.rollback()
        if not existing(): raise
    # Test topshiruvchiga "juda tez" hisoblari ko'rsatilmaydi.
    return {'saved':True,'result':PG.public(result)}

@router.get('/api/german-placement/results')
def results(branch_id: int|None=None, db: Session=Depends(get_db), user=Depends(require_role(*roles.LEAD_ACCESS))):
    q=scope_to_branch(db.query(models.GermanPlacementResult),models.GermanPlacementResult,user,branch_id)
    # Unassigned non-org staff must never fall through to organization-wide data.
    if user.role not in roles.ORG_WIDE_ROLES and not user.branch_id: return {'rows':[]}
    rows=q.order_by(models.GermanPlacementResult.id.desc()).limit(100).all()
    return {'rows':[dict(id=r.id,lead_id=r.lead_id,name=r.full_name,phone=r.phone,date=r.created_at.isoformat()+'Z',result=_staff_result(r)) for r in rows]}

def _staff_result(row):
    """Xodimlar uchun natija. 2026-10-22 dan oldingi yozuvlarda hisoblar
    yo'q: "Bilmayman" javoblardan sanaladi, "juda tez" — noma'lum (None,
    "—"; vaqt o'lchanmagan, timed=false). Eski baholar o'zgarmaydi."""
    r=json.loads(row.result_json)
    if 'guess_warning' not in r:
        try: ans=json.loads(row.answers_json or '{}')
        except ValueError: ans={}
        ans=ans if isinstance(ans,dict) else {}
        month={q['id']:q['month'] for q in BANK}
        idk_ids={k for k,v in ans.items() if v==PG.IDK}
        r.update(PG.summary(len(idk_ids),0,len(ans)))
        for b in r.get('blocks') or []:
            b.setdefault('idk',sum(month.get(k)==b.get('month') for k in idk_ids))
        PG.untimed(r)
    return r
