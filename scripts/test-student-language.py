"""Regression: no English exercise fallback in non-English student practice.
Uses an isolated in-memory SQLite database; no notifications or production access.
"""
import os, sys, json
from types import SimpleNamespace
os.environ['DATABASE_URL']='sqlite://'
sys.path.insert(0, os.path.abspath('api'))
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from fastapi import HTTPException
from database import Base
import models, schemas, student_app as app
engine=create_engine('sqlite://')
Base.metadata.create_all(engine)
app._me=lambda db,user: SimpleNamespace(id=1)
app.award_xp=lambda *args,**kwargs: {'ok':False}
user=SimpleNamespace(id=1)
with Session(engine) as db:
    refs={}
    for lang,sentence in [('en','I am happy.'),('de','Ich bin glücklich.'),('ru','Я дома.'),('ko','저는 학생입니다.'),(None,'She is happy.')]:
        q=models.GrammarQuestion(topic='QA',language=lang,kind='order',prompt='Tarjima',options=json.dumps(sentence.split()),answer=sentence,level='A1')
        db.add(q);db.flush();refs[lang]=f'gram:{q.id}'
        db.add(models.VocabWord(word=sentence.split()[0],translation='QA',language=lang or 'en'))
    tx=models.ReadingText(title='English only',body='This is English.',level='A1');db.add(tx);db.flush()
    db.add(models.ReadingQuestion(text_id=tx.id,prompt='English question',options='["yes", "no"]',answer='yes'))
    for skill,kind in [('writing','write_transform'),('speaking','speak_repeat'),('reading','read_tfng'),('listening','listen_qa')]:
        db.add(models.PracticeItem(skill=skill,kind=kind,level='A1',payload=json.dumps({'instruction':'English','given':'English','say':'English','text':'English','statement':'English','prompt':'English','options':['yes','no']}),answer='English'))
    db.commit()
    for lang in ('de','ru','ko','en'):
        allowed={refs[lang]} | ({refs[None]} if lang=='en' else set())
        for skill in ('writing','speaking','listening'):
            result=app.practice_round(skill,language=lang,db=db,user=user)
            assert result['items'], (lang,skill)
            assert all(it['ref'] in allowed for it in result['items'] if it['ref'].startswith('gram:')), (lang,skill,result)
        levels=app.practice_levels('writing',language=lang,db=db,user=user)['levels']
        assert levels[0]['total']==(3 if lang=='en' else 1), (lang,levels)
        if lang!='en':
            assert all(l['total']==0 for l in app.practice_levels('reading',language=lang,db=db,user=user)['levels'])
            for skill,kind in [('reading',None),('reading','read_tfng'),('writing','write_transform'),('speaking','speak_repeat'),('listening','listen_qa')]:
                try: app.practice_round(skill,kind=kind,language=lang,db=db,user=user)
                except HTTPException as e: assert e.status_code==404
                else: raise AssertionError((lang,skill,kind,'English fallback'))
    assert app.practice_round('reading',language='en',db=db,user=user)['items'][0]['prompt']=='English question'
    assert app.practice_round('writing',kind='write_transform',language='en',db=db,user=user)['items']
    answer=app.practice_answer(schemas.PracticeAnswerIn(skill='writing',ref=refs['de'],answer='bin Ich glücklich.'),db=db,user=user)
    assert not answer['correct'] and 'Ingliz' not in answer['why'] and 'tartibi' in answer['why']
    assert app._word_overlap('Ich bin glücklich.', 'Ich bin glücklich.')==1
    db.query(models.GrammarQuestion).filter_by(language='de').delete();db.query(models.VocabWord).filter_by(language='de').delete();db.commit()
    for skill in ('writing','speaking','listening'):
        assert app.practice_round(skill,language='de',db=db,user=user)['items']==[], skill
print('PASS: language-isolated rounds, level counts, unavailable types, empty banks, German feedback and English regressions')
