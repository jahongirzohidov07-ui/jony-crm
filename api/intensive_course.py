"""Bridge Intensive materials to existing authenticated assignments and history."""
import json
import random
from datetime import datetime, timedelta
from functools import lru_cache
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from auth import require_role
from common import _get_group_in_scope
import models, roles

router=APIRouter()

@lru_cache(maxsize=1)
def data():
    return json.loads(Path(__file__).with_name('intensive_course_data.json').read_text(encoding='utf-8'))

def lesson(no):
    if no<1 or no>192: raise HTTPException(404,'Dars topilmadi')
    return {'no':no,'title':f'Intensive · {no}-dars','intensive':True}

def topic_ids(no):
    week=(no-1)//6+1; day=(no-1)%6+1
    modules=[week-1] if week<=27 else [[0,1,2,3,4,5,6,7],[8,9,10,11,12],[13,14,15,16,17,18],[19,20,21,22,23],[24,25,26]][week-28]
    ids=[f'{mi+1}.{ti+1}' for mi in modules for ti,_ in enumerate(data()['modules'][mi]['items'])]
    return ids if day==6 else ids[(day-1)*len(ids)//5:day*len(ids)//5]

def assignment(no,part):
    lesson(no); d=data(); pack=d['skills'][no-1]
    def q(item): return {'kind':'gap','prompt':item['prompt'],'answer':item['answers'],'explain':item['explanation']}
    result={'kind':part,'skill':part,'title':f'Intensive · {no}-dars · {part}'}
    if part=='grammar':
        ids=topic_ids(no)
        random.Random(no).shuffle(ids)
        # Sample across topics before taking a second question from the same topic.
        qs=[q(d['exercises'][tid][i]) for i in range(max(len(d['exercises'][tid]) for tid in ids)) for tid in ids if i<len(d['exercises'][tid])]
        result.update(kind='grammar_test',questions=qs[:30])
    elif part=='vocab':
        week=(no-1)//6;day=(no-1)%6
        pool=d['words'][week*125:week*125+125] if day==5 else d['words'][week*125+day*25:week*125+day*25+25]
        # All taught words stay eligible; review samples span the complete week.
        if day==5: pool=pool[::5]
        result.update(kind='vocab_test',questions=[{'kind':'gap','prompt':f"Inglizcha bosh so‘zni yozing: {w['meaning']}",'answer':[w['word']],'explain':w['example']} for w in pool])
    elif part=='reading':
        result.update(text=pack['reading']['text'].split('\n'),questions=[q(x) for x in pack['reading']['questions']])
    elif part in ('writing','speaking'):
        rubric=[('Vazifani bajarish',2),('Tushunarlilik va izchillik',2),('Lug‘at',2),('Grammar',2)]
        result.update(instr='Ichki mashq: ustoz tekshiradi; sertifikat bali emas.',rubric=rubric,questions=[{'kind':'text' if part=='writing' else 'audio','prompt':pack[part]['prompt']+'\n'+'\n'.join(pack[part]['success']),'answer':''}])
    else:return None
    return result

def schedule_reviews(db,a,s,result):
    """Schedule one private 1/3/7-day recall set from first-attempt errors."""
    if a.course!='intensive' or a.kind=='intensive_review' or s.attempt!=1:return
    import models
    qs=json.loads(a.questions or '[]')
    wrong=[qs[x['i']] for x in result['items'] if not x['ok']]
    if not wrong:return
    # The source assignment/student key makes repeated deliveries idempotent.
    exists=db.query(models.IntensiveReviewSchedule).filter_by(assignment_id=a.id,student_id=s.student_id).first()
    if exists:return
    db.add(models.IntensiveReviewSchedule(assignment_id=a.id,student_id=s.student_id))
    for days in (1,3,7):
        start=datetime.utcnow()+timedelta(days=days)
        db.add(models.Assignment(group_id=a.group_id,student_id=s.student_id,course='intensive',lesson_no=a.lesson_no,
            kind='intensive_review',skill=a.skill,title=f'Intensive · {days}-kun: xatolarni qaytarish · {a.lesson_no}-dars',
            instr='Avval xato bo‘lgan bandlarni daftarsiz qayta bajaring.',text=a.text,questions=json.dumps(wrong,ensure_ascii=False),
            auto=1,max_score=float(len(wrong)),sent_at=start,due_at=start+timedelta(days=1),status='sent',
            targets=json.dumps([s.student_id]),created_by='Intensive qaytarish'))

@router.get('/api/groups/{gid}/intensive/report')
def report(gid:int,db:Session=Depends(get_db),user=Depends(require_role(*roles.TEACHING_ACCESS))):
    _get_group_in_scope(db,gid,user)
    assignments=db.query(models.Assignment).filter(models.Assignment.group_id==gid,models.Assignment.course=='intensive',models.Assignment.kind!='intensive_review').order_by(models.Assignment.id.desc()).limit(60).all()
    ids=[a.id for a in assignments]
    submissions=db.query(models.AssignmentSubmission).filter(models.AssignmentSubmission.assignment_id.in_(ids or [-1])).order_by(models.AssignmentSubmission.id).all()
    latest={(s.assignment_id,s.student_id):s for s in submissions}
    student_ids={sid for a in assignments for sid in json.loads(a.targets or '[]')}
    names={s.id:s.full_name for s in db.query(models.Student).filter(models.Student.id.in_(student_ids or [-1])).all()}
    rows=[]
    for a in assignments:
        students=[]
        for sid in json.loads(a.targets or '[]'):
            s=latest.get((a.id,sid));result=json.loads(s.result or '{}') if s else {}
            students.append(dict(id=sid,name=names.get(sid,'Arxivdagi o‘quvchi'),submission_id=s.id if s else None,status=s.status if s else 'pending',score=(s.auto_score if a.auto else s.teacher_score) if s else None,max=a.max_score,
                                 wrong=sum(not x['ok'] for x in result.get('items',[]))))
        rows.append(dict(id=a.id,title=a.title,lesson=a.lesson_no,skill=a.skill,students=students))
    scheduled=db.query(models.Assignment).filter(models.Assignment.group_id==gid,models.Assignment.course=='intensive',models.Assignment.kind=='intensive_review',models.Assignment.sent_at>datetime.utcnow()).count()
    return {'rows':rows,'scheduled_reviews':scheduled}
