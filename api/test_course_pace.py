"""Isolated pace, frozen plans and first-answer evidence regression tests."""
import unittest
from datetime import timedelta
from types import SimpleNamespace
from unittest.mock import patch

import test_student_course_practice as baseline
import course_motivation as motivation
import course_pace as pace
import models
import student_course_practice as practice


class PaceTests(unittest.TestCase):
    tearDown = baseline.CoursePracticeTests.tearDown

    def setUp(self):
        baseline.CoursePracticeTests.setUp(self)
        self.app.include_router(pace.make_router(practice._student, practice._lesson),
                                prefix="/api/student/course-practice")
        self.student = self.db.get(models.Student, 1)
        self.items = list(motivation.exact_questions("en").values())

    def attempt(self, item=None, student_id=1, days=0, correct=1):
        row, section, q = item or self.items[0]
        a = models.SkillAttempt(student_id=student_id,
            skill="course-practice:en:" + section["skill"], ref=practice._ref(q["id"]),
            answer="answer", correct=correct, created_at=motivation.now() - timedelta(days=days))
        self.db.add(a)
        self.db.commit()
        return a

    def send(self, attempt, item=None, **changes):
        row, _, q = item or self.items[0]
        body = dict(language="en", lesson=row["lesson"], question_id=q["id"],
                    active_seconds=90, attempt_id=attempt.id)
        body.update(changes)
        return self.client.post("/api/student/course-practice/pace", json=body)

    def test_scope_validation_and_no_reward_or_attempt_side_effect(self):
        a = self.attempt()
        for value in [True, 2, 601, 1.5, "90", 10**30]:
            self.assertEqual(self.send(a, active_seconds=value).status_code, 422)
        self.assertEqual(self.send(a, student_id=2).status_code, 422)
        self.assertEqual(self.send(a, lesson=2).status_code, 404)
        self.assertEqual(self.send(a, language="de").status_code, 404)
        self.assertEqual(self.send(a, attempt_id=99999).status_code, 404)
        foreign = self.attempt(student_id=2)
        self.assertEqual(self.send(foreign).status_code, 404)
        for days in [29, -1]:
            self.assertEqual(self.send(self.attempt(days=days)).status_code, 404)
        before = self.db.query(models.SkillAttempt).count()
        self.assertEqual(self.send(a, active_seconds=600).status_code, 200)
        self.assertEqual(self.db.query(models.SkillAttempt).count(), before)
        self.assertEqual(self.db.query(models.XpTransaction).count(), 0)
        self.assertEqual(self.db.query(models.CoinEntry).count(), 0)
        sample = pace.estimates(self.db, 1, "en")[0]
        self.assertTrue(sample["client_reported"])
        self.assertTrue(sample["recorded_at"].endswith("Z"))
        self.assertEqual(pace.estimates(self.db, 2, "en"), [])
        self.assertEqual(pace.estimates(self.db, 1, "de"), [])

    def test_retry_window_bounded_and_evicted_retry_not_reinserted(self):
        first = self.attempt()
        self.send(first)
        retry = self.send(first, active_seconds=300).json()
        self.assertTrue(retry["duplicate"])
        self.assertEqual(retry["sample"]["active_seconds"], 90)
        for _ in range(61):
            self.send(self.attempt())
        self.assertEqual(len(pace.estimates(self.db, 1, "en")), 60)
        self.assertFalse(self.send(first).json()["saved"])
        self.db.expire_all()
        self.assertEqual(len(pace.estimates(self.db, 1, "en")), 60)
        with patch.object(motivation, "now", return_value=motivation.now() + timedelta(days=29)):
            self.assertEqual(pace.estimates(self.db, 1, "en"), [])

    def test_median_minimum_skill_fallback_and_clamps(self):
        samples = [{"attempt_id": n, "skill": "reading" if n < 3 else "grammar",
                    "active_seconds": v} for n, v in enumerate([3, 60, 90, 120, 600])]
        self.assertEqual(pace.estimate(samples[:4], "reading")["minutes"], 5)
        result = pace.estimate(samples, "reading")
        self.assertEqual((result["minutes"], result["sample_count"], result["estimate_source"]),
                         (1, 3, "skill_median"))
        self.assertEqual(pace.estimate(samples, "grammar")["estimate_source"], "overall_median")
        self.assertEqual(pace.estimate(samples, "grammar")["minutes"], 1.5)
        for s in samples:
            s["active_seconds"] = 3
        self.assertEqual(pace.estimate(samples, "reading")["minutes"], .5)

    def test_frozen_plan_estimates_and_initial_denominator(self):
        for _ in range(5):
            self.send(self.attempt(), active_seconds=60)
        plan = motivation.daily_plan(self.db, 1, "en", [])
        self.db.commit()
        original = [(s["question_id"], s["minutes"], s["sample_count"]) for s in plan["steps"]]
        history_key = "course-plan-history:v1:1:en"
        targets = motivation.get(self.db, history_key)[0]["targets"]
        for _ in range(8):
            self.send(self.attempt(), active_seconds=600)
        motivation.choose_plan(self.db, 1, "en", 5)
        motivation.daily_plan(self.db, 1, "en", [])
        self.assertEqual(motivation.get(self.db, history_key)[0]["targets"], targets)
        motivation.choose_plan(self.db, 1, "en", 15)
        again = motivation.daily_plan(self.db, 1, "en", [])
        self.assertEqual([(s["question_id"], s["minutes"], s["sample_count"]) for s in again["steps"]], original)

    def test_fast_learner_budget_pool_is_not_limited_to_five_questions(self):
        for _ in range(5):
            self.send(self.attempt(), active_seconds=30)
        practice._save_position(self.db, 1, "en", 10)
        motivation.choose_plan(self.db, 1, "en", 25)
        plan = motivation.daily_plan(self.db, 1, "en", [])
        self.assertGreater(len(plan["steps"]), 5)
        self.assertLessEqual(len(plan["steps"]), 50)
        self.assertTrue(all(s["lesson"] <= 10 for s in plan["steps"]))
        self.assertLessEqual(plan["estimated_minutes"], 25)

    def test_unknown_plan_still_five_minutes(self):
        plan = motivation.daily_plan(self.db, 1, "en", [])
        self.assertEqual(len(plan["steps"]), 3)
        self.assertTrue(all(s["minutes"] == 5 and s["estimate_source"] == "default" for s in plan["steps"]))

    def test_first_exact_distinct_and_rolling_windows(self):
        for item in self.items[:5]:
            self.attempt(item, days=9, correct=0)
            self.attempt(item, days=1, correct=1)  # retry cannot improve baseline
        for item in self.items[5:10]:
            self.attempt(item, days=1, correct=1)
        self_item = next(v for v in motivation.canonical_questions("en").values() if v[2]["mode"] == "self")
        self.attempt(self_item, correct=1)
        result = motivation.measurement(self.db, 1, "en")["difficulty"]
        overall = result["overall"]
        self.assertEqual(overall["first_attempt"]["total"], 10)
        self.assertEqual(overall["last7"]["accuracy_percent"], 100)
        self.assertEqual(overall["prior7"]["accuracy_percent"], 0)
        self.assertEqual(overall["change_percentage_points"], 100)
        empty = motivation.difficulty_evidence(self.db, 2, "en")["overall"]
        self.assertIsNone(empty["first_attempt"]["accuracy_percent"])
        self.assertIsNone(empty["change_percentage_points"])
        self.assertEqual(sum(s["first_attempt"]["total"] for s in result["skills"]), 10)


if __name__ == "__main__":
    unittest.main()
