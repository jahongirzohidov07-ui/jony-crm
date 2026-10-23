"""Daily-six contract/security tests; isolated SQLite, no external AI/DB."""
import copy
import json
import tempfile
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import test_student_course_practice as baseline
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
import models
import student_daily_six as daily
import student_course_practice as practice
import course_motivation as motivation

BASE = '/api/student/course-practice/daily-six'


class DailySixTests(unittest.TestCase):
    tearDown = baseline.CoursePracticeTests.tearDown

    def setUp(self):
        baseline.CoursePracticeTests.setUp(self)
        self.clock = patch.object(motivation, 'now', return_value=datetime(2026, 10, 22, 12))
        self.time = self.clock.start()
        self.addCleanup(self.clock.stop)
        self.provider = patch.object(daily.writing_ai, '_call', side_effect=self.good_verdict)
        self.ai_grade = self.provider.start()
        self.addCleanup(self.provider.stop)

    @staticmethod
    def good_verdict(system, text):
        answer = json.loads(text)['student_answer']
        return json.dumps(dict(relevant=True, language_ok=True, task_met=True, meaningful=True,
                               evidence=[answer[:30]], feedback='Vazifa mazmuni to‘g‘ri.'))

    def plan(self, language='en'):
        r = self.client.get(BASE, params={'language':language})
        self.assertEqual(r.status_code, 200, r.text)
        return r.json()

    def state(self):
        return motivation.get(self.db, daily.plan_key(1, motivation.local_day().isoformat()))

    def body(self, q, answer=None, plan=None):
        plan = plan or self.state()
        mode = q['mode']
        if answer is None:
            answer = q['expected'][0] if mode == 'exact' else (
                'I have a book. My teacher is kind. I read at school.' if q.get('sentence_range') else
                'student teacher kind happy; a kind teacher; a happy student')
        value = dict(language=plan['language'], day=plan['day'], question_id=q['id'], answer=answer)
        if mode == 'audio':
            value['speech_source'] = 'speech_recognition'
        return value

    def answer(self, q, answer=None, plan=None):
        r = self.client.post(BASE+'/answer', json=self.body(q, answer, plan))
        self.assertEqual(r.status_code, 200, r.text)
        return r.json()

    def complete(self, language='en', skip_last=False):
        self.plan(language)
        plan = self.state()
        questions = [q for s in plan['skills'] for q in s['questions']]
        out = []
        for q in questions[:-1] if skip_last else questions:
            out.append(self.answer(q))
        return questions, out

    def test_all_six_partial_xp_and_one_daily_coin_independent_of_xp_cap(self):
        self.db.add(models.CoinEntry(student_id=1,source='daily_grade',ref_id=91,amount=17,note='Teacher award'))
        self.db.commit()
        questions, results = self.complete(skip_last=True)
        self.assertTrue(any(r['reward']['xp'] for r in results))
        self.assertTrue(all(r['reward']['coins']==0 for r in results))
        self.assertEqual(results[-1]['plan']['completed_steps'],5)
        result = self.answer(questions[-1])
        self.assertEqual(result['plan']['completed_steps'],6)
        self.assertTrue(result['plan']['awarded'])
        self.assertEqual(result['reward']['coins'],1)
        self.assertEqual(result['reward']['xp'],0)  # 20 XP-award transactions already reached.
        self.assertEqual(self.db.query(models.XpTransaction).count(),20)
        self.assertEqual(self.db.query(models.CoinEntry).filter_by(source='daily_grade').one().amount,17)
        for q in questions:
            self.assertEqual(self.answer(q)['reward'],motivation.ZERO)
        self.assertEqual(self.db.query(models.CoinEntry).filter_by(source=daily.COIN_SOURCE).count(),1)
        self.assertEqual(self.db.query(models.SkillAttempt).count(),23)

    def test_german_full_bundle(self):
        _, results = self.complete('de')
        self.assertEqual(results[-1]['plan']['completed_steps'],6)
        self.assertEqual(results[-1]['reward']['coins'],1)
        self.assertEqual(results[-1]['assessment'],'transcript_semantics')

    def test_read_only_reward_status_no_plan_creation_and_coin_proof(self):
        statements=[]
        def observe(conn,cursor,statement,*args): statements.append(statement)
        event.listen(self.engine,'before_cursor_execute',observe)
        try:
            status=daily.reward_status(self.db,self.db.get(models.Student,1))
            self.assertEqual(status,dict(day='2026-10-22',completed_steps=0,awarded=False,reward_eligible=True))
            self.assertTrue(all(s.lstrip().upper().startswith('SELECT') for s in statements),statements)
        finally: event.remove(self.engine,'before_cursor_execute',observe)
        self.assertEqual(self.db.query(models.IntegrationSetting).count(),0)
        motivation.put(self.db,daily.award_key(1,'2026-10-22'),True)
        self.db.commit()
        self.assertFalse(daily.reward_status(self.db,self.db.get(models.Student,1))['awarded'])

    def test_language_lesson_content_freeze_and_account_isolation(self):
        p=self.plan()
        q=self.state()['skills'][0]['questions'][0]
        self.answer(q)
        practice._save_position(self.db,1,'en',17)
        self.db.commit()
        switched=self.plan('de')
        self.assertEqual(switched['language'],'en')
        self.assertEqual(switched['lesson'],1)
        self.assertIn(q['id'],switched['answers'])
        body=self.body(q); body['language']='de'
        self.assertEqual(self.client.post(BASE+'/answer',json=body).status_code,409)
        self.user=SimpleNamespace(id=22,role='student',full_name='Two',is_active=1)
        other=self.plan('de')
        self.assertNotEqual(p['id'],other['id'])
        self.assertEqual(other['student_id'],2)
        self.assertEqual(other['answers'],{})

    def test_day_boundary_rotation_and_second_day_coin(self):
        old=self.plan()
        old_qids=[q['id'] for s in old['skills'] for q in s['questions']]
        q=self.state()['skills'][0]['questions'][0]
        old_body=self.body(q)
        self.time.return_value=datetime(2026,10,22,18,59,59)
        self.assertEqual(self.plan()['day'],'2026-10-22')
        self.time.return_value+=timedelta(seconds=1)
        self.assertEqual(self.client.post(BASE+'/answer',json=old_body).status_code,409)
        new=self.plan('de')
        self.assertEqual(new['day'],'2026-10-23')
        self.assertEqual(new['language'],'de')
        self.assertEqual(new['completed_steps'],0)
        self.complete('de')
        self.time.return_value+=timedelta(days=1)
        self.complete('en')
        self.assertEqual(self.db.query(models.CoinEntry).filter_by(source=daily.COIN_SOURCE).count(),2)
        self.assertNotEqual(old_qids,[q['id'] for s in self.plan()['skills'] for q in s['questions']])

    def test_no_client_correct_or_out_of_plan_question_or_typed_speaking(self):
        self.plan()
        state=self.state(); q=state['skills'][0]['questions'][0]
        body=self.body(q); body['correct']=True
        self.assertEqual(self.client.post(BASE+'/answer',json=body).status_code,422)
        body=self.body(q); body['question_id']='en:192:reading:1'
        self.assertEqual(self.client.post(BASE+'/answer',json=body).status_code,422)
        sq=state['skills'][-1]['questions'][0]
        body=self.body(sq); body.pop('speech_source')
        self.assertEqual(self.client.post(BASE+'/answer',json=body).status_code,422)
        result=self.answer(q,'wrong')
        self.assertFalse(result['correct'])
        self.assertEqual(result['reward'],motivation.ZERO)
        self.assertEqual(self.ai_grade.call_count,0)

    def test_plan_sanitizes_keys_and_uses_one_passage_all_lessons(self):
        for language, rows in practice.BANK.items():
            for row in rows:
                frozen=daily._build(1,'2026-10-22',language,row)
                projected=daily.public_plan(self.db,self.db.get(models.Student,1),frozen)
                self.assertEqual([s['target'] for s in projected['skills']],[10,5,3,3,1,1])
                for sec in projected['skills']:
                    self.assertNotIn('transcript',sec)
                    for q in sec['questions']:
                        self.assertNotIn('expected',q)
                        self.assertNotIn('explanation',q)
                for sec in frozen['skills']:
                    if sec['skill'] in ('reading','listening'):
                        source=next(s for s in row['sections'] if s['skill']==sec['skill'] and
                                    sum(q['mode']=='exact' for q in s['questions'])>=3)
                        self.assertTrue({q['id'] for q in sec['questions']} <= {q['id'] for q in source['questions']})
                        field='text' if sec['skill']=='reading' else 'transcript'
                        self.assertEqual(sec[field],source[field])

    def test_productive_grade_failure_content_guards_and_no_lock_during_provider(self):
        self.plan()
        q=self.state()['skills'][-2]['questions'][0]
        self.assertIsNone(q['sentence_range'])  # foundation labels are valid
        self.ai_grade.side_effect=lambda *_: (_ for _ in ()).throw(daily.writing_ai.WritingAIError('no_key'))
        r=self.client.post(BASE+'/answer',json=self.body(q))
        self.assertEqual(r.status_code,503)
        self.assertEqual(self.plan()['answers'],{})
        for bad in ['{}',json.dumps({'correct':True}), json.dumps(dict(relevant=True,language_ok=True,task_met=True,
                    meaningful=True,evidence=['fabricated words'],feedback='ok'))]:
            self.ai_grade.side_effect=None; self.ai_grade.return_value=bad
            self.assertEqual(self.client.post(BASE+'/answer',json=self.body(q)).status_code,503)
        self.assertEqual(self.db.query(models.CoinEntry).count(),0)
        def no_lock(system,text):
            self.assertFalse(self.db.in_transaction())
            return self.good_verdict(system,text)
        self.ai_grade.side_effect=no_lock
        self.assertTrue(self.answer(q)['correct'])

    def test_semantic_rejection_cached_and_limit_bounded(self):
        self.plan()
        q=self.state()['skills'][-1]['questions'][0]
        def reject(system,text):
            verdict=json.loads(self.good_verdict(system,text)); verdict['task_met']=False
            return json.dumps(verdict)
        self.ai_grade.side_effect=reject
        self.assertFalse(self.answer(q,'unrelated response')['correct'])
        self.assertFalse(self.answer(q,'unrelated response')['correct'])
        self.assertEqual(self.ai_grade.call_count,1)
        for n in range(19): self.answer(q,f'unrelated response number {n}')
        self.assertEqual(self.ai_grade.call_count,20)
        self.assertEqual(self.client.post(BASE+'/answer',json=self.body(q,'another answer')).status_code,429)
        self.assertEqual(self.ai_grade.call_count,20)
        exact=self.state()['skills'][0]['questions'][0]
        self.assertTrue(self.answer(exact)['correct'])
        self.assertEqual(self.plan()['completed_steps'],0)

    def test_standard_writing_sentence_guard_and_provider_rollover(self):
        practice._save_position(self.db,1,'en',31); self.db.commit()
        self.plan(); q=self.state()['skills'][-2]['questions'][0]
        self.assertFalse(self.answer(q,'One short sentence only.')['correct'])
        self.assertEqual(self.ai_grade.call_count,0)
        def rollover(system,text):
            self.time.return_value+=timedelta(days=1)
            return self.good_verdict(system,text)
        self.ai_grade.side_effect=rollover
        r=self.client.post(BASE+'/answer',json=self.body(q))
        self.assertEqual(r.status_code,409)
        self.assertFalse(self.db.in_transaction())
        self.assertEqual(self.db.query(models.XpTransaction).count(),0)

    def test_demo_ineligible_and_authentication(self):
        self.db.get(models.Student,1).full_name='One (DEMO)'; self.db.commit()
        p=self.plan(); self.assertFalse(p['reward_eligible'])
        self.assertEqual(p['reward_note'],'Demo rejimida coin berilmaydi.')
        self.complete()
        self.assertEqual(self.db.query(models.XpTransaction).count(),0)
        self.assertEqual(self.db.query(models.CoinEntry).count(),0)
        self.user=SimpleNamespace(id=11,role='teacher',full_name='One',is_active=1)
        self.assertEqual(self.client.get(BASE).status_code,403)
        self.user=SimpleNamespace(id=33,role='student',full_name='Unlinked',is_active=1)
        self.assertEqual(self.client.get(BASE).status_code,403)
        from auth import get_current_user
        self.app.dependency_overrides.pop(get_current_user)
        self.assertEqual(self.client.get(BASE).status_code,401)

    def test_parallel_final_answer_single_coin(self):
        # Independent connections, durable SQLite write locks (not an in-process mock).
        with tempfile.TemporaryDirectory() as tmp:
            engine=create_engine('sqlite:///'+str(Path(tmp)/'race.db'),connect_args={'check_same_thread':False,'timeout':20})
            for table in (models.Student,models.IntegrationSetting,models.SkillAttempt,models.XpTransaction,
                          models.CoinEntry,models.XpSeason,models.XpLeague,models.XpRule,models.StudentGamification,
                          models.StudentLeagueHistory,models.Branch,models.User):
                table.__table__.create(engine)
            sessions=sessionmaker(bind=engine)
            frozen=daily._build(1,'2026-10-22','en',practice._lesson('en',1))
            last=frozen['skills'][0]['questions'][0]  # exact avoids network in race
            for sec in frozen['skills']:
                for q in sec['questions']:
                    if q['id']!=last['id']:
                        frozen['answers'][q['id']]={'answer':'saved','feedback':{'correct':True,'explanation':'verified'}}
            with sessions() as db:
                db.add(models.Student(id=1,user_id=11,full_name='One',status='active'))
                motivation.put(db,daily.plan_key(1,'2026-10-22'),frozen); db.commit()
            barrier=threading.Barrier(2)
            body=daily.AnswerIn(**self.body(last,plan=frozen))
            def worker(_):
                with sessions() as db:
                    s=db.get(models.Student,1)
                    barrier.wait(timeout=10)
                    return daily.submit(db,s,body)
            try:
                with ThreadPoolExecutor(max_workers=2) as pool: results=list(pool.map(worker,range(2)))
                self.assertEqual(sorted(r['reward']['coins'] for r in results),[0,1])
                with sessions() as db:
                    self.assertEqual(db.query(models.CoinEntry).count(),1)
                    self.assertEqual(db.query(models.SkillAttempt).count(),1)
            finally: engine.dispose()


if __name__=='__main__': unittest.main(verbosity=2)
