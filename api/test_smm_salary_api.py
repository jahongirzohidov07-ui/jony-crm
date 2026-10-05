"""Self-only salary endpoint: no live database or salary writes."""
import os
import tempfile
import unittest
from datetime import date
from types import SimpleNamespace
from unittest.mock import patch

os.environ['DATABASE_URL'] = 'sqlite:///' + os.path.join(tempfile.gettempdir(), 'jony_smm_salary_route_test.db').replace('\\', '/')
from fastapi import FastAPI
from fastapi.testclient import TestClient
import me
import salary_coach
from auth import get_current_user
from database import get_db
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
import models


class StudentPlanSourceTests(unittest.TestCase):
    def test_own_active_students_and_school_year_target(self):
        engine = create_engine('sqlite:///:memory:')
        tables = [models.Branch.__table__, models.Student.__table__, models.PlanTarget.__table__]
        models.Base.metadata.create_all(engine, tables=tables)
        with Session(engine) as db:
            db.add_all([models.Branch(id=7, name='Own'), models.Branch(id=8, name='Other')])
            db.add_all([models.Student(full_name='A', branch_id=7, status='active'),
                        models.Student(full_name='B', branch_id=7, status='archived'),
                        models.Student(full_name='C', branch_id=8, status='active'),
                        models.Student(full_name='D', branch_id=7, status='frozen')])
            db.add_all([models.PlanTarget(branch_id=7, year=2026, month=1, metric='students', value=250),
                        models.PlanTarget(branch_id=7, year=2027, month=1, metric='students', value=999),
                        models.PlanTarget(branch_id=8, year=2026, month=1, metric='students', value=888),
                        models.PlanTarget(branch_id=7, year=2026, month=1, metric='revenue', value=100000000)])
            db.commit()
            self.assertEqual(salary_coach.student_plan_state(db, 7, 2027, 1), {'plan': 250, 'fact': 1})
            self.assertEqual(salary_coach.student_plan_state(db, 7, 2027, 2), {'plan': 0, 'fact': 1})
            self.assertIsNone(salary_coach.student_plan_state(db, None, 2027, 1))
        engine.dispose()


class SmmSalaryApiTests(unittest.TestCase):
    def setUp(self):
        self.user = SimpleNamespace(id=9, role='smm_manager', full_name='Test employee',
                                    branch_id=7, branch=SimpleNamespace(name='Own branch'),
                                    fix_salary=2_000_000, extra_roles=[])
        self.app = FastAPI()
        self.app.include_router(me.router)
        self.app.dependency_overrides[get_current_user] = lambda: self.user
        self.app.dependency_overrides[get_db] = lambda: None
        self.client = TestClient(self.app)

    @patch.object(me.roles, 'local_today', return_value=date(2026, 10, 5))
    @patch.object(salary_coach, 'student_plan_state', return_value=dict(plan=100, fact=85, percent=85, bonus=1_000_000))
    def test_branch_query_cannot_replace_own_branch(self, load, today):
        r = self.client.get('/api/me/smm-salary?branch_id=999')
        self.assertEqual(r.status_code, 200, r.text)
        load.assert_called_once_with(None, 7, 2026, 10)
        self.assertEqual(r.json()['total'], 2_500_000)
        self.assertEqual(r.json()['gap'], 5)

    def test_student_cannot_read_salary_endpoint(self):
        self.user.role = 'student'
        self.assertEqual(self.client.get('/api/me/smm-salary').status_code, 403)

    @patch.object(salary_coach, 'student_plan_state')
    def test_missing_branch_cannot_aggregate(self, load):
        self.user.branch_id = None
        self.user.branch = None
        r = self.client.get('/api/me/smm-salary')
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual(r.json()['status'], 'no_branch')
        load.assert_not_called()


if __name__ == '__main__':
    unittest.main()
