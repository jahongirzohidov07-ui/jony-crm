"""Isolated HTTP/ledger tests; no startup seeds or external database."""
import os
import sys
import unittest
from datetime import date, timedelta
from unittest.mock import patch

os.environ['DATABASE_URL'] = 'sqlite://'
sys.path.insert(0, os.path.dirname(__file__))

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import auth
import models
import roles
import student_app as sa
import wordbank as wb
from database import Base, get_db


class RewardPathTest(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine('sqlite://', poolclass=StaticPool,
                                    connect_args={'check_same_thread': False})
        Base.metadata.create_all(self.engine)
        self.db = sessionmaker(bind=self.engine, autoflush=False)()
        self.users = []
        self.students = []
        for n in range(2):
            u = models.User(username=f'reward{n}', full_name=f'Student {n}',
                            password_hash='unused', role=roles.STUDENT, is_active=1)
            self.db.add(u)
            self.db.flush()
            s = models.Student(full_name=u.full_name, user_id=u.id,
                               status='active', branch_id=n + 1)
            self.db.add(s)
            self.db.flush()
            self.users.append(u)
            self.students.append(s)
        self.db.commit()
        self.app = FastAPI()
        self.app.include_router(sa.router)
        def db_override():
            yield self.db
        self.app.dependency_overrides[get_db] = db_override
        self.client = TestClient(self.app)

    def tearDown(self):
        self.client.close()
        self.db.close()
        self.engine.dispose()

    def get(self, n=0, query=''):
        token = auth.create_access_token({'sub': self.users[n].username})
        return self.client.get('/api/student/reward-path' + query,
                               headers={'Authorization': 'Bearer ' + token})

    def sources(self, response):
        self.assertEqual(response.status_code, 200, response.text)
        return {s['id']: s for s in response.json()['sources']}

    def streak(self, n=0):
        for i in range(7):
            self.db.add(models.VocabAttempt(student_id=self.students[n].id,
                        date=roles.local_today() - timedelta(days=i), game='test', correct=1))
        self.db.commit()

    def test_daily_six_read_only_unstarted_and_verified_ledger_status(self):
        statements = []
        def capture(conn, cursor, statement, parameters, context, many):
            statements.append(statement.strip().upper())
        event.listen(self.engine, 'before_cursor_execute', capture)
        try:
            result = self.sources(self.get())
        finally:
            event.remove(self.engine, 'before_cursor_execute', capture)
        daily = next(s for k, s in result.items() if k.startswith('daily-six:'))
        self.assertEqual((daily['have'], daily['target'], daily['coins']), (0, 6, 1))
        self.assertEqual(daily['status'], 'in_progress')
        self.assertEqual(daily['href'], '/student/course-practice?view=daily-six')
        self.assertFalse(any(sql.startswith(('INSERT', 'UPDATE', 'DELETE')) for sql in statements))
        for paid, expected in [(False, 'eligible'), (True, 'awarded')]:
            with patch('student_daily_six.reward_status', return_value={
                'day': '2026-10-23', 'completed_steps': 6, 'awarded': paid}):
                self.assertEqual(self.sources(self.get())['daily-six:2026-10-23']['status'], expected)

    def test_auth_and_student_isolation(self):
        self.assertEqual(self.client.get('/api/student/reward-path').status_code, 401)
        self.streak(1)
        r = self.get(0, '?student_id=' + str(self.students[1].id))
        self.assertEqual(r.json()['student_id'], self.students[0].id)
        self.assertEqual(self.sources(r)['streak:7']['have'], 0)
        self.assertEqual(self.sources(self.get(1))['streak:7']['have'], 7)
        self.users[0].role = 'teacher'
        self.db.commit()
        self.assertEqual(self.get().status_code, 403)

    def test_unlinked_and_inactive_denied(self):
        self.students[0].status = 'left'
        self.db.commit()
        self.assertEqual(self.get().status_code, 403)
        self.students[0].status = 'active'
        self.students[0].user_id = None
        self.db.commit()
        self.assertEqual(self.get().status_code, 403)

    def test_streak_eligible_then_paid_and_no_mutations(self):
        self.streak()
        sid = self.students[0].id
        self.db.add(models.CoinEntry(student_id=sid, amount=1, source='streak',
                                    ref_id=7, note='old run [2000-01-01]'))
        self.db.commit()
        statements = []
        def capture(conn, cursor, statement, parameters, context, executemany):
            statements.append(statement.strip().split()[0].upper())
        event.listen(self.engine, 'before_cursor_execute', capture)
        with patch.object(self.db, 'commit', side_effect=AssertionError('GET committed')):
            for _ in range(2):
                self.assertEqual(self.sources(self.get())['streak:7']['status'], 'eligible')
        event.remove(self.engine, 'before_cursor_execute', capture)
        self.assertTrue(statements)
        self.assertEqual(set(statements), {'SELECT'})
        tag = (roles.local_today() - timedelta(days=6)).isoformat()
        self.db.add(models.CoinEntry(student_id=sid, amount=1, source='streak',
                                    ref_id=7, note=f'7 kunlik streak sovrini [{tag}]'))
        self.db.commit()
        self.assertEqual(self.sources(self.get())['streak:7']['status'], 'awarded')
        self.assertEqual(self.sources(self.get(1))['streak:7']['status'], 'in_progress')

    def test_league_reversals_and_history_are_not_payment(self):
        sid = self.students[0].id
        lg = models.XpLeague(key='test', name='Test', minimum_xp=500, reward_coin=3)
        self.db.add(lg)
        self.db.add_all([models.XpTransaction(student_id=sid, amount=600),
                         models.XpTransaction(student_id=sid, amount=-200, is_reversal=1)])
        self.db.commit()
        row = self.sources(self.get())['league:test']
        self.assertEqual((row['have'], row['status']), (400, 'in_progress'))
        self.db.add(models.StudentLeagueHistory(student_id=sid, to_league_id=lg.id,
                                                reward_coin=3))
        self.db.commit()
        self.assertEqual(self.sources(self.get())['league:test']['status'], 'untracked')

    def test_wordbank_gating_readiness_and_payment(self):
        self.assertFalse(any(k.startswith('wordbank:') for k in self.sources(self.get())))
        self.db.add(models.IntegrationSetting(key=wb.FLAG_KEY, value='[1]'))
        for i in range(2):
            w = models.WordbankWord(rank=i+1, band=1, lemma=f'word{i}', uz_primary='soz')
            self.db.add(w)
            self.db.flush()
            self.db.add(models.WordbankStudentWord(student_id=self.students[0].id,
                                                   word_id=w.id, known=1))
        self.db.commit()
        self.assertFalse(any(k.startswith('wordbank:') for k in self.sources(self.get())))
        with patch.object(wb, 'BAND_SIZE', 2):
            row = self.sources(self.get())['wordbank:1']
            self.assertEqual((row['status'], row['have'], row['target']), ('eligible', 2, 2))
            self.assertEqual(row['href'], '/student/words')
            self.db.add(models.CoinEntry(student_id=self.students[0].id,
                                        source=wb.COIN_SOURCE, ref_id=1, amount=1))
            self.db.commit()
            self.assertEqual(self.sources(self.get())['wordbank:1']['status'], 'awarded')
            self.assertFalse(any(k.startswith('wordbank:') for k in self.sources(self.get(1))))

    def test_badges_count_answers_not_unique_words_and_keep_thresholds(self):
        self.db.add_all([models.VocabAttempt(student_id=self.students[0].id,
                         word_id=1, game='test', correct=1) for _ in range(100)])
        self.db.add(models.XpTransaction(student_id=self.students[0].id, amount=500))
        self.db.commit()
        rows = {b['key']: b for b in sa._badges(self.db, self.students[0])}
        self.assertTrue(rows['xp_500']['done'])
        self.assertEqual(rows['xp_500']['hint'], "500 XP to'pladingiz")
        v = rows['vocab_100']
        self.assertEqual((v['have'], v['target'], v['done']), (100, 100, True))
        self.assertEqual((v['metric'], v['category'], v['unit']),
                         ('vocab', 'vocabulary', 'correct_answers'))
        self.assertNotIn("so'z", v['label'])
        self.assertEqual(sa._daily_progress(self.db, self.students[0].id)['tasks'][0]['title'],
                         "10 ta to'g'ri javob")

    def test_tashkent_day_and_achievement_payment_status(self):
        local_day = date(2026, 10, 23)
        for i in range(7):
            self.db.add(models.VocabAttempt(student_id=self.students[0].id,
                date=local_day - timedelta(days=i), game='test', correct=1))
        self.db.commit()
        with patch.object(roles, 'local_today', return_value=local_day):
            self.assertEqual(self.sources(self.get())['streak:7']['status'], 'eligible')
            with patch.object(sa, '_award_streak_coins', return_value=None):
                data = sa.student_achievements(db=self.db, user=self.users[0])
                self.assertEqual(data['streak_rewards'][0]['status'], 'eligible')
            data = sa.student_achievements(db=self.db, user=self.users[0])
            self.assertEqual(data['streak_rewards'][0]['status'], 'awarded')
            self.assertEqual(data['streak_rewards'][0]['status_label'], 'Coin berilgan')
            self.assertEqual(data['streak_rewards'][0]['award_mode'], 'automatic')

    def test_skipped_lower_league_not_eligible(self):
        self.db.add_all([
            models.XpLeague(key='low', name='Low', rank=1, minimum_xp=100, reward_coin=1),
            models.XpLeague(key='high', name='High', rank=2, minimum_xp=500, reward_coin=3),
            models.XpTransaction(student_id=self.students[0].id, amount=600)])
        self.db.commit()
        rows = self.sources(self.get())
        self.assertEqual(rows['league:low']['status'], 'untracked')
        self.assertEqual(rows['league:high']['status'], 'eligible')
        self.assertEqual(rows['league:high']['practice_href'], '/student/vocab')

    def test_xp_ties_use_student_id_for_leaderboard_and_week_prize(self):
        today = roles.local_today()
        prev_week = today - timedelta(days=today.weekday() + 7)
        timestamp = sa._utc_window(prev_week, prev_week + timedelta(days=6))[0]
        # Insert the larger student ID first; insertion order must not decide.
        for student in reversed(self.students):
            self.db.add(models.XpTransaction(student_id=student.id, amount=100,
                                            created_at=timestamp + timedelta(hours=12)))
        self.db.commit()
        with patch.object(sa, '_gam_card', return_value={}):
            for n in (0, 1):
                result = sa.student_leaderboard(scope='all', period='all',
                                                db=self.db, user=self.users[n])
                self.assertEqual(result['me']['rank'], n + 1)
        prize = self.db.query(models.CoinEntry).filter_by(
            source='rank', ref_id=int(prev_week.strftime('%Y%m%d'))).one()
        self.assertEqual(prize.student_id, self.students[0].id)
        self.assertEqual(prize.amount, roles.RANK_PRIZE_COIN)
        sa._award_week_prizes(self.db)
        self.assertEqual(self.db.query(models.CoinEntry).filter_by(
            source='rank', ref_id=prize.ref_id).count(), 1)

    def test_xp_badge_uses_net_ledger_after_real_cancellation(self):
        from gamification import reverse_xp
        sid = self.students[0].id
        base = models.XpTransaction(student_id=sid, amount=483)
        award = models.XpTransaction(student_id=sid, amount=17)
        self.db.add_all([base, award])
        self.db.commit()
        def badge():
            return next(b for b in sa._badges(self.db, self.students[0])
                        if b['key'] == 'xp_500')
        self.assertTrue(badge()['done'])
        reverse_xp(self.db, award.id, by_user=self.users[0], reason='Test correction')
        result = badge()
        self.assertEqual((result['have'], result['left'], result['done']), (483, 17, False))
        cached = self.db.query(models.StudentGamification).filter_by(student_id=sid).one()
        self.assertEqual(cached.lifetime_xp, result['have'])
        self.assertEqual(award.amount, 17)  # original award remains in the ledger
        # Fractional XP must not round up into an unearned milestone.
        self.db.add(models.XpTransaction(student_id=sid, amount=16.6))
        self.db.commit()
        self.assertFalse(badge()['done'])
        self.db.add(models.XpTransaction(student_id=sid, amount=-1000, is_reversal=1))
        self.db.commit()
        result = badge()
        self.assertEqual((result['have'], result['percent'], result['left']), (0, 0, 500))

    def test_streak_badge_hints_name_vocabulary_activity(self):
        for key, label, hint, metric, target, icon, tone in roles.BADGES:
            if metric == 'streak':
                self.assertIn("lug'at mashqi", hint)

    def test_manual_is_not_pending_and_daily_coin_requires_six_skills(self):
        rows = self.sources(self.get())
        self.assertEqual(rows['manual']['status'], 'manual_review')
        self.assertIsNone(rows['manual']['coins'])
        self.assertEqual(rows['manual']['award_mode'], 'staff')
        daily = next(v for k, v in rows.items() if k.startswith('daily-six:'))
        self.assertEqual((daily['coins'], daily['target'], daily['have'], daily['status']), (1, 6, 0, 'in_progress'))
        for row in rows.values():
            self.assertEqual(set(row) - {'practice_href'}, {'id', 'title', 'description', 'coins', 'have',
                'target', 'unit', 'status', 'award_mode', 'href', 'action_label'})


if __name__ == '__main__':
    unittest.main()
