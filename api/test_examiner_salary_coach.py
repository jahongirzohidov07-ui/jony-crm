import os
import unittest
from datetime import date
from types import SimpleNamespace
from unittest.mock import patch

os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
import roles
from salary_coach import examiner_salary_goal
from fastapi import FastAPI
from fastapi.testclient import TestClient
import me
from auth import get_current_user
from database import get_db


def pay(points=600, count=1):
    r = dict(roles.examiner_salary(points), period='2026-10', exam_count=count)
    if count == 0:
        r.update(salary=0, no_exams=True)
    return r


class GoalTests(unittest.TestCase):
    def goal(self, p):
        return examiner_salary_goal(p, date(2026, 10, 5))

    def test_next_milestones(self):
        for pts, target, gap in [(10,500000,490), (600,700000,100),
                                 (625.5,700000,74.5), (1499.5,1500000,.5),
                                 (-20,500000,520)]:
            r = self.goal(pay(pts))
            self.assertEqual(r['next_salary'], target)
            self.assertEqual(r['gap_points'], gap)
            self.assertTrue(0 <= r['progress'] <= 100)

    def test_maximum(self):
        for pts in [1500,1700]:
            r = self.goal(pay(pts))
            self.assertEqual(r['status'], 'maximum')
            self.assertIsNone(r['gap_points'])
            self.assertIsNone(r['next_salary'])

    def test_no_exams_does_not_require_400_points_for_minimum(self):
        r = self.goal(pay(0,0))
        self.assertEqual(r['status'], 'no_exams')
        self.assertEqual(r['next_salary'],400000)
        self.assertIsNone(r['gap_points'])

    def test_volunteer_has_no_money_target(self):
        r = self.goal(dict(pay(), volunteer=True, salary=0))
        self.assertEqual(r['status'],'volunteer')
        self.assertIsNone(r['next_salary'])

    def test_current_and_historical_days(self):
        self.assertEqual(self.goal(pay())['days_left'],27)
        self.assertEqual(self.goal(dict(pay(),period='2026-09'))['days_left'],0)


class EndpointTests(unittest.TestCase):
    def setUp(self):
        self.user = SimpleNamespace(id=91, role='examiner', extra_roles=[])
        app = FastAPI()
        app.include_router(me.router)
        app.dependency_overrides[get_current_user] = lambda: self.user
        app.dependency_overrides[get_db] = lambda: None
        self.client = TestClient(app)

    @patch.object(me, '_is_volunteer', return_value=False)
    @patch.object(me, '_examiner_month', side_effect=lambda *args: pay())
    @patch.object(me.roles, 'local_today', return_value=date(2026,10,5))
    def test_uses_own_account_and_preserves_salary(self, today, month, volunteer):
        r=self.client.get('/api/me/examiner-salary?user_id=999&branch_id=888')
        self.assertEqual(r.status_code,200,r.text)
        month.assert_called_once_with(None,91,2026,10)
        self.assertEqual(r.json()['salary'],600000)
        self.assertEqual(r.json()['goal']['gap_points'],100)

    @patch.object(me, '_is_volunteer', return_value=True)
    @patch.object(me, '_examiner_month', side_effect=lambda *args: pay())
    def test_volunteer_override_runs_before_goal(self, month, volunteer):
        r=self.client.get('/api/me/examiner-salary')
        self.assertEqual(r.status_code,200,r.text)
        self.assertEqual(r.json()['salary'],0)
        self.assertEqual(r.json()['goal']['status'],'volunteer')

    def test_other_role_denied(self):
        self.user.role='smm_manager'
        self.assertEqual(self.client.get('/api/me/examiner-salary').status_code,403)


if __name__ == '__main__':
    unittest.main()
