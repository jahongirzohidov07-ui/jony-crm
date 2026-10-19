"""Isolated SQLite integration tests: python api/test_course_collaboration.py."""
import copy
import os
import sys
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

os.environ['DATABASE_URL'] = 'sqlite://'
sys.path.insert(0, str(Path(__file__).resolve().parent))
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import models
import course_collaboration as c
from auth import get_current_user
from database import get_db


class CollaborationTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine('sqlite://', connect_args={'check_same_thread': False}, poolclass=StaticPool)
        for model in (models.Branch, models.User, models.Student, models.Teacher, models.Group,
                      models.StudentGroupLink, models.IntegrationSetting, models.XpTransaction, models.SkillAttempt):
            model.__table__.create(self.engine)
        self.sessions = sessionmaker(bind=self.engine, expire_on_commit=False)
        self.db = self.sessions()
        self.db.add_all([models.Branch(id=1, name='Real'), models.Branch(id=2, name='Other'),
                         models.Branch(id=3, name='Practice', is_test=1)])
        for uid, role in [(11, 'student'), (22, 'student'), (33, 'student'), (44, 'student'),
                          (101, 'teacher'), (102, 'teacher'), (103, 'administrator')]:
            self.db.add(models.User(id=uid, username=f'u{uid}', password_hash='unused', full_name=f'User {uid}', role=role, is_active=1))
        self.db.add_all([models.Teacher(id=1, user_id=101, full_name='Teacher One', is_active=1),
                         models.Teacher(id=2, user_id=102, full_name='Teacher Two', is_active=1),
                         models.Group(id=1, name='Group One', branch_id=1, teacher_id=1),
                         models.Group(id=2, name='Group Two', branch_id=2, teacher_id=2),
                         models.Group(id=3, name='Demo group', branch_id=3, teacher_id=1)])
        for sid, uid, gid in [(1, 11, 1), (2, 22, 1), (3, 33, 1), (4, 44, 2)]:
            self.db.add(models.Student(id=sid, user_id=uid, full_name=f'Student {sid}', status='active', group_id=gid, branch_id=1 if gid == 1 else 2))
        self.db.commit()
        self.user = self.db.get(models.User, 11)
        app = FastAPI()
        app.include_router(c.router)
        app.dependency_overrides[get_db] = lambda: self.db
        app.dependency_overrides[get_current_user] = lambda: self.user
        self.app = app
        self.client = TestClient(app)

    def tearDown(self):
        self.client.close()
        self.db.close()
        self.engine.dispose()

    def as_user(self, uid):
        self.user = self.db.get(models.User, uid)

    def url(self, suffix='', gid=1, language='en', lesson=1):
        return f'/api/course-collaboration/groups/{gid}{suffix}?language={language}&lesson={lesson}'

    def post(self, suffix, body=None, status=200, **query):
        result = self.client.post(self.url(suffix, **query), json=body or {})
        self.assertEqual(result.status_code, status, result.text)
        return result.json()

    def invite(self):
        return self.post('/invites', {'peer_id': 2}, 201)['id']

    def accepted(self):
        eid = self.invite()
        self.as_user(22)
        r = self.client.post(self.url(f'/{eid}/respond') + '&accept=true', json={})
        self.assertEqual(r.status_code, 200, r.text)
        self.as_user(11)
        return eid

    def version(self, eid, expected=0, **changes):
        return self.post(f'/{eid}/versions', {'expected_version': expected, 'title': 'Our dialogue',
            'text': 'Hello! My name is Ali. Hi Ali, I am Sara.',
            'contributions': {'1': 'Opening lines', '2': 'Response lines'}, **changes}, 201)

    def submit(self, eid, version=1):
        self.as_user(11)
        self.post(f'/{eid}/consent', {'expected_version': version})
        self.as_user(22)
        return self.post(f'/{eid}/consent', {'expected_version': version})

    def review_body(self, version=1, **changes):
        return {'expected_version': version, 'decision': 'approved', 'task': 3, 'language': 3, 'collaboration': 3,
                'strength': 'Both speakers introduce themselves clearly.',
                'next_step': 'Add one question about your partner and answer it.', **changes}

    def test_complete_workflow_immutable_history_version_bound_approval_no_xp(self):
        eid = self.accepted()
        first = self.version(eid)['versions'][0]
        self.as_user(101)
        self.assertEqual(self.client.get(self.url()).json()['entries'], [])
        self.as_user(11)
        one = self.post(f'/{eid}/consent', {'expected_version': 1})
        duplicate = self.post(f'/{eid}/consent', {'expected_version': 1})
        self.assertEqual(one, duplicate)
        self.assertIsNone(one['versions'][0]['submitted_at'])
        self.as_user(101)
        self.post(f'/{eid}/review', self.review_body(), 409)
        self.assertEqual(self.client.get(self.url()).json()['entries'], [])
        both = self.submit(eid)
        self.assertEqual(set(both['versions'][0]['consents']), {'1', '2'})
        self.post(f'/{eid}/versions', {'expected_version': 1, 'title': 'Oops', 'text': 'New', 'contributions': {'1': 'A', '2': 'B'}}, 409)
        self.as_user(101)
        approved = self.post(f'/{eid}/review', self.review_body())
        original = copy.deepcopy(approved['versions'][0])
        self.assertEqual(original['review']['version'], 1)
        self.post(f'/{eid}/review', self.review_body(), 409)
        self.as_user(11)
        second = self.version(eid, 1, text='Improved version')
        self.assertEqual(second['versions'][0], original)
        self.assertEqual(second['versions'][1]['consents'], {})
        self.assertIsNone(second['versions'][1]['review'])
        self.post(f'/{eid}/consent', {'expected_version': 1}, 409)
        self.as_user(101)
        self.post(f'/{eid}/review', self.review_body(), 409)
        visible = self.client.get(self.url()).json()['entries'][0]['versions']
        self.assertEqual(visible, [original])
        self.submit(eid, 2)
        self.as_user(101)
        reviewed = self.post(f'/{eid}/review', self.review_body(2, decision='changes_requested', language=1))
        self.assertEqual(reviewed['versions'][0], original)
        self.assertEqual(reviewed['versions'][1]['review']['decision'], 'changes_requested')
        self.db.close()
        self.db = self.sessions()
        reloaded = self.client.get(self.url()).json()
        self.assertEqual(reloaded['entries'][0]['versions'][0], original)
        self.assertEqual(original['text'], first['text'])
        self.assertEqual(reloaded['xp'], 0)
        self.assertFalse(reloaded['verified_mastery'])
        self.assertEqual(self.db.query(models.XpTransaction).count(), 0)
        self.assertEqual(self.db.query(models.SkillAttempt).count(), 0)

    def test_invitation_acceptance_and_cross_student_access(self):
        eid = self.invite()
        self.post(f'/{eid}/versions', {'expected_version': 0, 'title': 'x', 'text': 'x', 'contributions': {'1': 'a', '2': 'b'}}, 409)
        self.assertEqual(self.client.post(self.url(f'/{eid}/respond') + '&accept=true').status_code, 409)
        self.as_user(33)
        self.assertEqual(self.client.get(self.url()).json()['entries'], [])
        self.assertEqual(self.client.post(self.url(f'/{eid}/respond') + '&accept=true').status_code, 404)
        self.post(f'/{eid}/consent', {'expected_version': 0}, 404)
        self.post(f'/{eid}/versions', {'expected_version': 0, 'title': 'x', 'text': 'x', 'contributions': {'1': 'a', '2': 'b'}}, 404)
        self.as_user(22)
        self.assertEqual(self.client.post(self.url(f'/{eid}/respond') + '&accept=false').status_code, 200)
        self.assertEqual(self.client.post(self.url(f'/{eid}/respond') + '&accept=true').status_code, 409)
        self.post(f'/{eid}/consent', {'expected_version': 0}, 409)

    def test_group_teacher_and_role_defense(self):
        eid = self.accepted()
        self.version(eid)
        self.submit(eid)
        self.post(f'/{eid}/review', self.review_body(), 403)
        for uid in (44, 102):
            self.as_user(uid)
            self.assertEqual(self.client.get(self.url()).status_code, 404)
            self.post(f'/{eid}/review', self.review_body(), 404)
        self.as_user(101)
        self.post('/invites', {'peer_id': 2}, 403)
        self.post(f'/{eid}/consent', {'expected_version': 1}, 403)
        self.post(f'/{eid}/review', self.review_body(), 404, gid=2)
        self.db.get(models.Teacher, 1).is_active = 0
        self.db.commit()
        self.assertEqual(self.client.get(self.url()).status_code, 403)
        self.as_user(103)
        self.assertEqual(self.client.get(self.url()).status_code, 403)
        self.app.dependency_overrides.pop(get_current_user)
        self.assertIn(self.client.get(self.url()).status_code, (401, 403))

    def test_membership_revocation_and_primary_link_override(self):
        eid = self.accepted()
        self.version(eid)
        link = models.StudentGroupLink(student_id=2, group_id=1, active=1, status='frozen')
        self.db.add(link); self.db.commit()
        self.post(f'/{eid}/consent', {'expected_version': 1}, 404)
        self.assertNotIn(2, [p['id'] for p in self.client.get(self.url()).json()['peers']])
        for changes in [{'status': 'trial'}, {'status': 'active', 'active': 0},
                        {'active': 1, 'left_date': c._today()},
                        {'left_date': None, 'joined_date': c._today() + timedelta(days=1)},
                        {'joined_date': None, 'activated_on': c._today() + timedelta(days=1)}]:
            for k, value in changes.items(): setattr(link, k, value)
            self.db.commit()
            self.post('/invites', {'peer_id': 2}, 404)
        link.activated_on = None; self.db.commit()
        self.assertIn(2, [p['id'] for p in self.client.get(self.url()).json()['peers']])
        self.db.get(models.Student, 2).status = 'archived'; self.db.commit()
        self.post(f'/{eid}/consent', {'expected_version': 1}, 404)

    def test_secondary_active_membership_and_branch_test_separation(self):
        self.db.add(models.StudentGroupLink(student_id=4, group_id=1, active=1, status='active'))
        self.db.commit()
        self.post('/invites', {'peer_id': 4}, 201)
        self.db.get(models.Branch, 1).is_test = 1; self.db.commit()
        self.assertEqual(self.client.get(self.url()).status_code, 403)
        self.as_user(101)
        self.assertEqual(self.client.get('/api/course-collaboration/groups').json()['groups'], [])

    def test_account_activity_role_and_demo_peers(self):
        for field, value in [('is_active', 0), ('role', 'teacher'), ('username', 'demo.student')]:
            user = self.db.get(models.User, 22)
            original = getattr(user, field)
            setattr(user, field, value); self.db.commit()
            self.post('/invites', {'peer_id': 2}, 404)
            setattr(user, field, original); self.db.commit()
        self.user.username = 'demo.owner'; self.db.commit()
        self.assertEqual(self.client.get(self.url()).status_code, 403)

    def test_validation_scope_and_review_threshold(self):
        self.post('/invites', {'peer_id': 1}, 404)
        self.post('/invites', {'peer_id': 4}, 404)
        self.post('/invites', {'peer_id': 2, 'student_id': 1}, 422)
        self.assertEqual(self.client.get(self.url() + '&demo=true').status_code, 422)
        self.assertEqual(self.client.get(self.url(language='de', lesson=73)).status_code, 404)
        eid = self.accepted()
        body = {'expected_version': 0, 'title': 'x', 'text': 'x', 'contributions': {'1': 'a', '2': 'b'}}
        for change in [{'text': ' '}, {'text': 'x' * 6001}, {'contributions': {'1': 'x', '3': 'y'}},
                       {'contributions': {'1': 'a'}}, {'title': ' '}, {'expected_version': True}]:
            self.post(f'/{eid}/versions', {**body, **change}, 422)
        self.version(eid)
        self.post(f'/{eid}/consent', {'expected_version': 1}, 404, lesson=2)
        self.submit(eid)
        self.as_user(101)
        self.post(f'/{eid}/review', self.review_body(language=2), 422)
        self.post(f'/{eid}/review', self.review_body(next_step=' '), 422)
        self.post(f'/{eid}/review', self.review_body(task=5), 422)

    def test_stale_cas_and_revision_never_overwrite(self):
        eid = self.accepted()
        self.version(eid)
        key = 'course-collaboration:v1:1:en:1'
        old = self.db.query(models.IntegrationSetting.value).filter_by(key=key).scalar()
        self.version(eid, 1, text='New version')
        with self.assertRaises(HTTPException) as caught:
            c._save(self.db, key, old, {'entries': []})
        self.assertEqual(caught.exception.status_code, 409)
        with self.assertRaises(HTTPException) as caught:
            c._save(self.db, key, None, {'entries': []})
        self.assertEqual(caught.exception.status_code, 409)
        self.assertEqual(len(self.client.get(self.url()).json()['entries'][0]['versions']), 2)
        self.post(f'/{eid}/consent', {'expected_version': 1}, 409)
        self.assertIn('no-store', self.client.get(self.url()).headers['cache-control'])

    def test_tashkent_day_and_group_end_archive(self):
        instant = datetime(2026, 10, 18, 21, tzinfo=timezone.utc)
        with patch.object(c, 'datetime') as clock:
            clock.now.side_effect = lambda tz: instant.astimezone(tz)
            self.assertEqual(str(c._today()), '2026-10-19')
        group = self.db.get(models.Group, 1)
        for key, value in [('end_date', c._today() - timedelta(days=1)), ('archived_at', datetime.now())]:
            setattr(group, key, value); self.db.commit()
            self.assertEqual(self.client.get(self.url()).status_code, 404)
            setattr(group, key, None); self.db.commit()

    def test_pending_queue_only_owned_submitted_unreviewed(self):
        eid = self.accepted()
        self.version(eid)
        self.as_user(101)
        queue = '/api/course-collaboration/review-queue'
        self.assertEqual(self.client.get(queue).json()['items'], [])
        self.submit(eid)
        self.assertEqual(self.client.get(queue).status_code, 403)
        self.as_user(102)
        self.assertEqual(self.client.get(queue).json()['items'], [])
        self.as_user(101)
        item = self.client.get(queue).json()['items'][0]
        self.assertEqual((item['entry_id'], item['group_id'], item['lesson'], item['language']), (eid, 1, 1, 'en'))
        self.assertNotIn('text', item)
        self.post(f'/{eid}/review', self.review_body())
        self.assertEqual(self.client.get(queue).json()['items'], [])

    def test_revision_limit_and_duplicate_invitation(self):
        eid = self.accepted()
        self.post('/invites', {'peer_id': 2}, 409)
        for n in range(10):
            self.version(eid, n, text=f'Version {n + 1}')
        self.post(f'/{eid}/versions', {'expected_version': 10, 'title': 'x', 'text': 'x', 'contributions': {'1': 'a', '2': 'b'}}, 409)

    def test_teacher_review_response_cannot_leak_superseded_private_draft(self):
        eid = self.accepted()
        self.version(eid, text='Private draft, not consented')
        self.version(eid, 1, text='Both approved this text')
        self.submit(eid, 2)
        self.as_user(101)
        response = self.post(f'/{eid}/review', self.review_body(2))
        self.assertEqual([v['number'] for v in response['versions']], [2])
        self.assertNotIn('Private draft', str(response))
        self.as_user(11)
        self.assertEqual(len(self.client.get(self.url()).json()['entries'][0]['versions']), 2)

    def test_live_speaking_validation_and_legacy_defaults(self):
        eid = self.accepted()
        self.version(eid)
        self.submit(eid)
        self.as_user(101)
        for changes in [
            {'speaking_observed': True},
            {'speaking_observed': True, 'fluency': 3},
            {'speaking_observed': True, 'pronunciation': 3},
            {'fluency': 2}, {'speaking_observed': False, 'pronunciation': 0},
            {'speaking_observed': True, 'fluency': -1, 'pronunciation': 3},
            {'speaking_observed': True, 'fluency': 3, 'pronunciation': 5},
            {'speaking_observed': True, 'fluency': True, 'pronunciation': 3},
            {'speaking_observed': 'true', 'fluency': 3, 'pronunciation': 3},
            {'speaking_observed': True, 'fluency': 3.5, 'pronunciation': 3},
            {'observed_at': '2026-01-01'}, {'observed_by': 2},
        ]:
            self.post(f'/{eid}/review', self.review_body(**changes), 422)
        result = self.post(f'/{eid}/review', self.review_body())['versions'][0]['review']
        self.assertFalse(result['speaking_observed'])
        for key in ('fluency', 'pronunciation', 'observed_at', 'observed_by'):
            self.assertIsNone(result[key])

    def test_live_speaking_is_version_bound_teacher_only_and_immutable(self):
        eid = self.accepted()
        self.version(eid)
        self.submit(eid)
        body = self.review_body(speaking_observed=True, fluency=0, pronunciation=4)
        self.post(f'/{eid}/review', body, 403)
        self.as_user(102)
        self.post(f'/{eid}/review', body, 404)
        self.as_user(101)
        original = self.post(f'/{eid}/review', body)['versions'][0]['review']
        self.assertTrue(original['speaking_observed'])
        self.assertEqual((original['fluency'], original['pronunciation']), (0, 4))
        self.assertEqual(original['observed_by'], 1)
        self.assertEqual(original['version'], 1)
        self.assertIsNotNone(datetime.fromisoformat(original['observed_at']).tzinfo)
        self.post(f'/{eid}/review', self.review_body(speaking_observed=True, fluency=4, pronunciation=4), 409)
        self.as_user(11)
        self.assertEqual(self.client.get(self.url()).json()['entries'][0]['versions'][0]['review'], original)
        second = self.version(eid, 1)
        self.assertIsNone(second['versions'][1]['review'])
        self.submit(eid, 2)
        self.as_user(101)
        result = self.post(f'/{eid}/review', self.review_body(2))
        self.assertEqual(result['versions'][0]['review'], original)
        self.assertFalse(result['versions'][1]['review']['speaking_observed'])
        self.assertEqual(self.db.query(models.XpTransaction).count(), 0)


if __name__ == '__main__':
    unittest.main()
