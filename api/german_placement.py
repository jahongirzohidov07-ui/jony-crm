"""German intake: server-scored, atomic and retry-safe CRM persistence."""
import hashlib
import json
import re
from datetime import datetime, timedelta
from pathlib import Path
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field, StrictInt
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
import models, roles
from auth import require_role
from database import get_db
from common import _ensure_public_id, scope_to_branch
from leads import _web_rate_ok

router = APIRouter()
BANK = json.loads(Path(__file__).with_name('german_placement_bank.json').read_text(encoding='utf-8'))
LABELS = ['A1 poydevor', 'A1 yakuni', 'A2 poydevor', 'A2 yakuni', 'B1 poydevor', 'B1 yakuni']

class Submission(BaseModel):
    attempt_id: UUID
    full_name: str = Field(min_length=3, max_length=120)
    phone: str = Field(min_length=9, max_length=24)
    branch_id: StrictInt
    answers: dict[str, StrictInt] = Field(min_length=48, max_length=48)

def assess(answers):
    if set(answers) != {q['id'] for q in BANK} or any(v not in range(-1,4) for v in answers.values()):
        raise HTTPException(422, '48 ta savolga javob bering')
    blocks=[]
    for month in range(1,7):
        qs=[q for q in BANK if q['month']==month]
        right=[q for q in qs if answers[q['id']]==q['answer']]
        passed=len(right)>=6 and sum(q['skill']=='grammar' for q in right)>=3 and sum(q['skill']=='reading' for q in right)>=1
        blocks.append(dict(month=month,label=LABELS[month-1],correct=len(right),total=8,passed=passed))
    gap=next((b['month'] for b in blocks if not b['passed']),None)
    month=gap or 6
    return dict(score=sum(b['correct'] for b in blocks),month=month,lesson=(month-1)*12+1 if gap else 70,blocks=blocks,
                label=LABELS[month-1] if gap else 'B1 bilimlari: to‘rt ko‘nikma sinovi kerak',
                gaps=[q['topic'] for q in BANK if q['month']<=month and answers[q['id']]!=q['answer']])

@router.post('/api/public/german-placement')
def submit(payload: Submission, request: Request, db: Session=Depends(get_db)):
    name=' '.join(payload.full_name.split())
    phone=re.sub(r'\D','',payload.phone)
    if len(phone)==9: phone='998'+phone
    if len(name)<3 or not re.fullmatch(r'998\d{9}',phone):
        raise HTTPException(422,'Ism va O‘zbekiston telefon raqamini tekshiring')
    result=assess(payload.answers)
    digest=hashlib.sha256(json.dumps([name,phone,payload.branch_id,payload.answers],sort_keys=True).encode()).hexdigest()
    def existing():
        row=db.query(models.GermanPlacementResult).filter_by(attempt_id=str(payload.attempt_id)).first()
        if row and row.payload_hash!=digest: raise HTTPException(409,'Bu test avval boshqa ma’lumot bilan saqlangan')
        return row
    old=existing()
    if old: return {'saved':True,'result':json.loads(old.result_json)}
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
    lead.note=((lead.note or '')+'\n'+note).strip()
    row=models.GermanPlacementResult(attempt_id=str(payload.attempt_id),payload_hash=digest,lead_id=lead.id,branch_id=branch.id,full_name=name,phone=phone,result_json=json.dumps(result,ensure_ascii=False),answers_json=json.dumps(payload.answers))
    db.add(row)
    try: db.commit()
    except IntegrityError:
        db.rollback()
        if not existing(): raise
    return {'saved':True,'result':result}

@router.get('/api/german-placement/results')
def results(branch_id: int|None=None, db: Session=Depends(get_db), user=Depends(require_role(*roles.LEAD_ACCESS))):
    q=scope_to_branch(db.query(models.GermanPlacementResult),models.GermanPlacementResult,user,branch_id)
    # Unassigned non-org staff must never fall through to organization-wide data.
    if user.role not in roles.ORG_WIDE_ROLES and not user.branch_id: return {'rows':[]}
    rows=q.order_by(models.GermanPlacementResult.id.desc()).limit(100).all()
    return {'rows':[dict(id=r.id,lead_id=r.lead_id,name=r.full_name,phone=r.phone,date=r.created_at.isoformat()+'Z',result=json.loads(r.result_json)) for r in rows]}
