"""Isolated Intensive assignment/history/review regressions; never uses a real DB."""
import os, sys, json
from datetime import datetime, timedelta
from types import SimpleNamespace
os.environ['DATABASE_URL']='sqlite://'
sys.path.insert(0, os.path.abspath('api'))
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi import HTTPException, FastAPI
from fastapi.testclient import TestClient
from database import Base, get_db
import models, roles, assignments as a, intensive_course as ic

engine=create_engine('sqlite://')
Base.metadata.create_all(engine)
Session=sessionmaker(bind=engine)
# Sending notifications is explicitly disabled for local fixtures.
a._tg=lambda *args: None

with Session() as db:
    branch=models.Branch(name='QA Intensive'); other=models.Branch(name='QA Other')
    db.add_all([branch,other]);db.flush()
    group=models.Group(name='QA Intensive',branch_id=branch.id)
    db.add(group);db.flush()
    st=models.Student(full_name='QA One',group_id=group.id,user_id=8001,status='active')
    peer=models.Student(full_name='QA Two',group_id=group.id,user_id=8002,status='active')
    db.add_all([st,peer]);db.commit()
    staff=SimpleNamespace(id=9001,full_name='QA Staff',role=roles.FOUNDER,branch_id=None)
    student=SimpleNamespace(id=8001,full_name=st.full_name,role=roles.STUDENT)
    sibling=SimpleNamespace(id=8002,full_name=peer.full_name,role=roles.STUDENT)
    sent=a.send_from_plan(group.id,a.FromPlanIn(course='intensive',lesson_no=7,parts=['grammar','vocab','reading','writing','speaking']),db,staff)
    assert len(sent['created'])==5 and not sent['skipped']
    source=db.query(models.Assignment).filter_by(skill='grammar').one()
    questions=json.loads(source.questions)
    detail=a.my_assignment(source.id,db,student)
    assert all('answer' not in q for q in detail['questions'])
    # One wrong item creates exactly three private recall sets, containing only that item.
    answers={str(i):q['answer'][0] for i,q in enumerate(questions)}
    answers['0']='definitely incorrect'
    a.submit(source.id,a.SubmitIn(answers=answers),db,student)
    first=db.query(models.AssignmentSubmission).filter_by(assignment_id=source.id).one()
    assert first.auto_score==len(questions)-1
    reviews=db.query(models.Assignment).filter_by(kind='intensive_review').order_by(models.Assignment.sent_at).all()
    assert len(reviews)==3
    for review,day in zip(reviews,[1,3,7]):
        assert json.loads(review.questions)==[questions[0]]
        assert review.student_id==st.id and json.loads(review.targets)==[st.id]
        assert abs((review.sent_at-datetime.utcnow()).total_seconds()-day*86400)<10
        assert not a._visible(review,st)
        try:a.my_assignment(review.id,db,student);raise AssertionError('early access allowed')
        except HTTPException as e:assert e.status_code==404
    ic.schedule_reviews(db,source,first,json.loads(first.result));db.commit()
    a.submit(source.id,a.SubmitIn(answers=answers),db,student)
    assert db.query(models.Assignment).filter_by(kind='intensive_review').count()==3
    history=ic.report(group.id,db,staff)
    row=next(x for x in history['rows'] if x['id']==source.id)
    assert row['students'][0]['score']==len(questions)-1 and row['students'][0]['wrong']==1
    assert history['scheduled_reviews']==3
    review=reviews[0];review.sent_at=datetime.utcnow()-timedelta(seconds=1);db.commit()
    assert a._visible(review,st) and not a._visible(review,peer)
    a.submit(review.id,a.SubmitIn(answers={'0':'still incorrect'}),db,student)
    assert db.query(models.Assignment).filter_by(kind='intensive_review').count()==3
    assert review.id in [x['id'] for x in a.my_assignments(db,student)['items']]
    assert review.id not in [x['id'] for x in a.my_assignments(db,sibling)['items']]
    # Many classmates' due reviews cannot hide this student's ordinary assignments.
    for i in range(65):
        db.add(models.Assignment(group_id=group.id,student_id=peer.id,kind='intensive_review',course='intensive',skill='grammar',title='Other learner review',lesson_no=7,questions='[]',targets=json.dumps([peer.id]),status='sent',sent_at=datetime.utcnow()-timedelta(days=1)))
    db.commit()
    assert source.id in [x['id'] for x in a.my_assignments(db,student)['items']]
    writing=db.query(models.Assignment).filter_by(skill='writing').one()
    a.submit(writing.id,a.SubmitIn(text='My own written response.'),db,student)
    written=db.query(models.AssignmentSubmission).filter_by(assignment_id=writing.id).one()
    assert written.status=='submitted' and written.auto_score is None
    outsider=SimpleNamespace(id=9002,role=roles.ADMINISTRATOR,branch_id=other.id,full_name='Other staff')
    try:ic.report(group.id,db,outsider);raise AssertionError('other branch read allowed')
    except HTTPException as e:assert e.status_code==403
    orphan_teacher=SimpleNamespace(id=9003,role=roles.TEACHER,branch_id=branch.id,full_name='Unlinked teacher')
    try:ic.report(group.id,db,orphan_teacher);raise AssertionError('unlinked teacher read allowed')
    except HTTPException as e:assert e.status_code==403

# Every day/part must build; explicit alternatives must not accept just half an answer.
for no in range(1,193):
    for part in ['grammar','vocab','reading','writing','speaking']:
        assert ic.assignment(no,part)['questions'],(no,part)
compound=[{'kind':'gap','prompt':'Two blanks','answer':['am / is']}]
assert a.auto_grade(compound,{'0':'am'},literal_answers=True)['score']==0
assert a.auto_grade(compound,{'0':'am / is'},literal_answers=True)['score']==1
app=FastAPI();app.include_router(ic.router)
assert TestClient(app).get('/api/groups/1/intensive/report').status_code in (401,403)
print('PASS: 960 daily assignments; saved scores; hidden answers; private 1/3/7-day reviews; idempotency; no recursive reviews; list isolation; teacher marking; branch/teacher/auth scope; complete-answer grading')
