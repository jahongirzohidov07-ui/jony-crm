import unittest
from study_plan import estimate, equivalent_hours

class StudyPlanTests(unittest.TestCase):
    def test_budgets(self):
        for band, total in [(0.5,105),(2,330),(3.5,780),(5,1080),(5.5,1180),(6.5,1380),(7,1586.67),(8,2000)]:
            self.assertEqual(estimate(band,0,2)["target_hours"],total)
    def test_daily_time(self):
        self.assertEqual(estimate(6.5,0,1)["days"],1380)
        self.assertEqual(estimate(6.5,0,2)["days"],690)
        self.assertEqual(estimate(8,0,5)["days"],400)
    def test_existing_level(self):
        self.assertEqual(estimate(8,6.5,2)["remaining_hours"],620)
        self.assertEqual(estimate(8,6.5,2)["days"],310)
        self.assertEqual(estimate(6.5,6.5,2)["days"],0)
    def test_target_bands_have_distinct_monotone_durations(self):
        days = [estimate(b,1,2)["days"] for b in [5.5,6,6.5,7,7.5,8]]
        self.assertTrue(all(a < b for a,b in zip(days,days[1:])))
        self.assertLess(estimate(5.5,5.49,2)["remaining_hours"],3)
        self.assertEqual(estimate(5.5,5.5,2)["remaining_hours"],0)
    def test_boundaries(self):
        self.assertIsNone(estimate(9,0,2)["days"])
        self.assertIsNone(estimate(None,0,2)["days"])
        self.assertEqual(equivalent_hours(0),0)
        with self.assertRaises(ValueError): estimate(7,0,0)

if __name__ == "__main__": unittest.main()
