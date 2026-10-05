import unittest
from datetime import date
from types import SimpleNamespace
from unittest.mock import Mock
import roles
from salary_coach import own_smm_salary, smm_salary_goal


class SalaryCoachTests(unittest.TestCase):
    def setUp(self):
        self.user = SimpleNamespace(full_name="Test videographer", branch_id=7,
                                    branch=SimpleNamespace(name="Test branch"), fix_salary=2_000_000)
        self.today = date(2026, 10, 5)

    def result(self, percent):
        bonus, _ = roles.smm_sales_bonus(percent)
        return smm_salary_goal(self.user, dict(plan=100_000_000, fact=percent*1_000_000,
                                               percent=percent, bonus=bonus), self.today)

    def test_below_first_tier(self):
        r = self.result(65)
        self.assertEqual((r['total'], r['next_total'], r['gap']), (2_000_000, 3_000_000, 15_000_000))
        self.assertEqual(r['days_left'], 27)

    def test_exact_tier_uses_next_higher_bonus(self):
        for percent, bonus, _ in roles.SMM_SALES_BONUS:
            r = self.result(percent)
            self.assertEqual(r['bonus'], bonus)
            if percent < 150:
                self.assertGreater(r['next_percent'], percent)
                self.assertGreater(r['next_total'], r['total'])
                self.assertGreater(r['gap'], 0)

    def test_top_tier(self):
        r = self.result(170)
        self.assertEqual(r['total'], 10_000_000)
        self.assertIsNone(r['gap'])
        self.assertIsNone(r['next_total'])

    def test_missing_plan_is_not_top_tier(self):
        r = smm_salary_goal(self.user, dict(plan=0, fact=50, percent=None, bonus=0), self.today)
        self.assertEqual(r['status'], 'no_plan')
        self.assertIsNone(r['next_total'])

    def test_employee_branch_only(self):
        load = Mock(return_value=dict(plan=0, fact=0, percent=None, bonus=0))
        own_smm_salary(self.user, 'db', self.today, load)
        load.assert_called_once_with('db', 7, 2026, 10)

    def test_unassigned_never_loads_all_branches(self):
        self.user.branch_id = None
        load = Mock()
        r = own_smm_salary(self.user, 'db', self.today, load)
        load.assert_not_called()
        self.assertEqual(r['status'], 'no_branch')
        self.assertEqual(r['total'], 2_000_000)

    def test_month_end(self):
        self.today = date(2026, 10, 31)
        self.assertEqual(self.result(90)['days_left'], 1)


if __name__ == '__main__':
    unittest.main()
