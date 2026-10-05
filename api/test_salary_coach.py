import unittest
from datetime import date
from types import SimpleNamespace
from unittest.mock import Mock
import roles
from salary_coach import own_smm_salary, smm_salary_goal, student_fixed_salary


class SalaryCoachTests(unittest.TestCase):
    def setUp(self):
        self.user = SimpleNamespace(full_name="Test videographer", branch_id=7,
                                    branch=SimpleNamespace(name="Test branch"), fix_salary=2_000_000)
        self.today = date(2026, 10, 5)

    def result(self, percent):
        bonus, _ = roles.smm_sales_bonus(percent)
        return smm_salary_goal(self.user, dict(plan=100, fact=percent,
                                               percent=percent, bonus=bonus), self.today)

    def test_below_first_tier(self):
        r = self.result(65)
        self.assertEqual((r['total'], r['next_total'], r['gap']), (1_500_000, 2_500_000, 15))
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
        self.assertEqual(r['total'], 11_000_000)
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
        self.assertIsNone(r['total'])

    def test_fixed_boundaries(self):
        for n, expected in [(0,1500000),(100,1500000),(101,2000000),
                            (150,2000000),(151,3000000),(200,3000000),
                            (201,5000000),(300,5000000),(301,8000000),(1000,8000000)]:
            self.assertEqual(student_fixed_salary(n), expected)

    def test_threshold_requires_whole_student(self):
        r = smm_salary_goal(self.user, dict(plan=251, fact=200), self.today)
        self.assertEqual(r['bonus'], 0)
        self.assertEqual(r['gap'], 1)
        self.assertEqual(r['next_total'], 6000000)

    def test_month_end(self):
        self.today = date(2026, 10, 31)
        self.assertEqual(self.result(90)['days_left'], 1)

    def test_301_plus_salary_and_bonus(self):
        r = smm_salary_goal(self.user, dict(plan=300, fact=301), self.today)
        self.assertEqual(r['fix_salary'], 8000000)
        self.assertEqual(r['bonus'], 3000000)
        self.assertEqual(r['total'], 11000000)
        self.assertEqual(r['gap'], 29)
        self.assertEqual(r['next_total'], 12000000)
        self.assertIsNone(r['next_fixed_count'])

    def test_300_next_fixed_threshold(self):
        r = smm_salary_goal(self.user, dict(plan=300, fact=300), self.today)
        self.assertEqual(r['next_fixed_count'], 301)
        self.assertEqual(r['next_fixed_salary'], 8000000)

    def test_display_rounding_does_not_award_bonus_early(self):
        r = smm_salary_goal(self.user, dict(plan=10001, fact=8000), self.today)
        self.assertEqual(r['percent'], 80.0)
        self.assertEqual(r['bonus'], 0)
        self.assertEqual(r['gap'], 1)


if __name__ == '__main__':
    unittest.main()
