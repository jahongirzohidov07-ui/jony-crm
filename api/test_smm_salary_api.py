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
from auth import get_current_user
from database import get_db


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
    @patch.object(me, '_smm_sales_state', return_value=dict(plan=100_000_000, fact=85_000_000, percent=85, bonus=1_000_000))
    def test_branch_query_cannot_replace_own_branch(self, load, today):
        r = self.client.get('/api/me/smm-salary?branch_id=999')
        self.assertEqual(r.status_code, 200, r.text)
        load.assert_called_once_with(None, 7, 2026, 10)
        self.assertEqual(r.json()['total'], 3_000_000)
        self.assertEqual(r.json()['gap'], 5_000_000)

    def test_student_cannot_read_salary_endpoint(self):
        self.user.role = 'student'
        self.assertEqual(self.client.get('/api/me/smm-salary').status_code, 403)

    @patch.object(me, '_smm_sales_state')
    def test_missing_branch_cannot_aggregate(self, load):
        self.user.branch_id = None
        self.user.branch = None
        r = self.client.get('/api/me/smm-salary')
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual(r.json()['status'], 'no_branch')
        load.assert_not_called()


if __name__ == '__main__':
    unittest.main()
