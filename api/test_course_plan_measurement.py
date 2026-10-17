"""Isolated personal-plan, cooperation and longitudinal-observation regressions."""
import unittest
from datetime import timedelta
from types import SimpleNamespace

import test_course_learning_evidence as fixture
import models
import course_motivation as m
import student_course_practice as practice


class PlanMeasurementTests(unittest.TestCase):
    setUp = fixture.LearningEvidenceTests.setUp
    tearDown = fixture.LearningEvidenceTests.tearDown
    items = fixture.LearningEvidenceTests.items
    diverse = fixture.LearningEvidenceTests.diverse
    add = fixture.LearningEvidenceTests.add
    view = fixture.LearningEvidenceTests.view

    def choose(self, minutes=5, language="en", **extra):
        return self.client.post("/api/student/course-practice/motivation/plan",
                                json={"language": language, "minutes": minutes, **extra})

    def real(self):
        self.db.add(models.Branch(id=1, name="Real", is_test=0))
        self.db.add(models.User(id=11, username="real11", password_hash="unused",
                               full_name="One", role="student", is_active=1))
        self.student.branch_id = 1
        self.db.commit()

    def test_endpoint_validates_auth_language_and_budget(self):
        for value in (0, 10, 30, True, "5", 5.0):
            self.assertEqual(self.choose(value).status_code, 422)
        self.assertEqual(self.choose(language="fr").status_code, 422)
        self.assertEqual(self.choose(student_id=2).status_code, 422)
        self.assertEqual(self.client.post("/api/student/course-practice/motivation/plan?student_id=2",
            json={"language": "en", "minutes": 5}).status_code, 422)
        self.user = SimpleNamespace(id=11, role="teacher", full_name="One", is_active=1)
        self.assertEqual(self.choose().status_code, 403)

    def test_durable_budget_is_language_and_student_scoped(self):
        first = self.choose(25).json()
        self.assertEqual(first["plan"]["minutes"], 25)
        self.assertEqual(len(first["plan"]["steps"]), 5)
        self.assertEqual(first["plan"]["duration_basis"], "estimate")
        self.assertEqual(self.view("de")["plan"]["minutes"], 15)
        self.db.expire_all()
        self.assertEqual(self.view()["plan"]["minutes"], 25)
        self.user = SimpleNamespace(id=22, role="student", full_name="Two", is_active=1)
        self.assertEqual(self.choose(5).json()["measurement"]["started_on"], None)
        self.assertEqual(self.view()["plan"]["minutes"], 25)
        self.time.return_value += timedelta(days=1)
        self.assertEqual(self.view()["plan"]["minutes"], 25)

    def test_initial_get_does_not_freeze_default_before_explicit_choice(self):
        initial = self.view()["plan"]
        selected = self.choose(5).json()
        self.assertEqual(selected["measurement"]["plans"]["days"][0]["total"], 1)
        step = selected["plan"]["steps"][0]
        self.assertEqual(step["id"], initial["steps"][0]["id"])
        self.add(m.canonical_questions("en")[step["question_id"]][2], correct=0)
        expanded = self.choose(25).json()
        self.assertTrue(expanded["plan"]["steps"][0]["done"])
        self.assertEqual(expanded["measurement"]["completed_plan_days"], 1)
        self.assertEqual(expanded["measurement"]["plans"]["days"][0]["total"], 1)
        shrunk = self.choose(5).json()
        self.assertTrue(shrunk["plan"]["completed"])
        self.assertEqual(shrunk["plan"]["steps"][0]["id"], step["id"])
        self.assertEqual(self.db.query(models.XpTransaction).count(), 0)

    def test_legacy_three_step_plan_extends_without_resetting_progress(self):
        self.view()
        key = "course-plan:v1:1:en:current"
        legacy = m.get(self.db, key)
        legacy["steps"] = legacy["steps"][:3]
        legacy.pop("initial_minutes")
        original_ids = [step["id"] for step in legacy["steps"]]
        original_targets = [step["question_id"] for step in legacy["steps"]]
        m.put(self.db, key, legacy)
        # Old production plans predate measurement history as well as the pool.
        m.put(self.db, "course-plan-history:v1:1:en", [])
        self.add(m.canonical_questions("en")[original_targets[0]][2])
        practice._save_position(self.db, 1, "en", 1)
        response = self.choose(25)
        self.assertEqual(response.status_code, 200, response.text)
        result = response.json()
        steps = result["plan"]["steps"]
        self.assertEqual(len(steps), 5)
        self.assertEqual(result["plan"]["estimated_minutes"], 25)
        self.assertEqual([step["id"] for step in steps[:3]], original_ids)
        self.assertTrue(steps[0]["done"])
        self.assertTrue(all(step["lesson"] == 1 for step in steps[3:]))
        self.assertEqual(len({step["question_id"] for step in steps}), 5)
        saved = m.get(self.db, key)
        self.assertEqual(saved["created_at"], legacy["created_at"])
        self.assertEqual(saved["after_id"], legacy["after_id"])
        self.assertEqual(saved["initial_minutes"], 15)
        snapshot = m.get(self.db, "course-plan-history:v1:1:en")[0]
        self.assertEqual(snapshot["targets"], original_targets)
        self.assertEqual((snapshot["minutes"], snapshot["total"], snapshot["done"]), (15, 3, 1))
        replay = self.choose(25).json()["plan"]
        self.assertEqual(replay, result["plan"])
        for qid in original_targets[1:]:
            self.add(m.canonical_questions("en")[qid][2])
        completed = self.view()
        self.assertEqual(completed["measurement"]["completed_plan_days"], 1)
        self.assertFalse(completed["plan"]["completed"])
        self.assertEqual(self.db.query(models.XpTransaction).count(), 0)

    def test_no_get_after_answer_still_completes_prior_day(self):
        first = self.choose(5).json()
        q = m.canonical_questions("en")[first["plan"]["steps"][0]["question_id"]][2]
        self.add(q)
        self.time.return_value += timedelta(days=1)
        result = self.view()["measurement"]
        self.assertEqual(result["completed_plan_days"], 1)
        self.assertEqual(result["plan_days"], 2)
        self.assertEqual(result["plans"]["days"][0]["total"], 1)
        self.assertFalse(result["plans"]["days"][1]["completed"])

    def test_next_day_attempt_cannot_complete_previous_day(self):
        first = self.choose(5).json()
        self.time.return_value += timedelta(days=1)
        self.add(m.canonical_questions("en")[first["plan"]["steps"][0]["question_id"]][2])
        self.assertFalse(self.view()["measurement"]["plans"]["days"][0]["completed"])

    def test_history_is_bounded_and_measurement_is_idempotent(self):
        for _ in range(30):
            self.view()
            self.time.return_value += timedelta(days=1)
        a = self.view()["measurement"]
        b = self.view()["measurement"]
        self.assertEqual(a, b)
        self.assertEqual(a["plan_days"], 28)
        self.assertEqual(a["started_on"], None)
        self.assertEqual(a["return_day7"], {"eligible": False, "returned": None})
        self.assertEqual(a["active_days"], 0)
        self.assertEqual(a["completed_plan_days"], 0)
        log = m.get(self.db, "course-plan-history:v1:1:en")
        self.assertEqual(len(log), 28)

    def test_concrete_support_and_no_future_lesson_jump(self):
        section, _ = self.items()[0]
        questions = [q for sec, q in self.items() if sec["id"] == section["id"]]
        failed = questions[2]
        self.add(failed, correct=0)
        self.add(failed, correct=0)
        self.add(self.diverse(30)[0], correct=0)
        practice._save_position(self.db, 1, "en", 1)
        plan = self.view()["plan"]
        self.assertEqual(plan["steps"][0]["question_id"], questions[0]["id"])
        self.assertIn("Tayyorlov", plan["steps"][0]["reason"])
        self.assertTrue(all(step["lesson"] <= 1 for step in plan["steps"]))
        self.add(failed)
        self.assertEqual(self.view()["plan"]["steps"][0]["id"], plan["steps"][0]["id"])

    def test_success_selects_unseen_current_lesson_challenge(self):
        q = self.diverse()[0]
        self.add(q)
        practice._save_position(self.db, 1, "en", 1)
        plan = self.view()["plan"]
        self.assertNotEqual(plan["steps"][0]["question_id"], q["id"])
        self.assertEqual(plan["steps"][0]["lesson"], 1)

    def test_exact_d7_and_mature_denominator_not_visits(self):
        q = self.diverse()[0]
        self.add(q, correct=0)
        self.time.return_value += timedelta(days=7)
        self.assertEqual(self.view()["measurement"]["return_day7"], {"eligible": False, "returned": None})
        self.add(q, correct=0)
        self.time.return_value += timedelta(days=1)
        measure = self.view()["measurement"]
        self.assertEqual(measure["return_day7"], {"eligible": True, "returned": True})
        self.assertEqual(measure["d7"]["total"], 1)
        self.assertEqual(measure["active_days"], 2)
        self.assertEqual(self.view("de")["measurement"]["started_on"], None)

    def test_day8_return_does_not_count_as_day7(self):
        q = self.diverse()[0]
        self.add(q)
        self.time.return_value += timedelta(days=7)
        self.view()  # A visit on D7 does not qualify.
        self.time.return_value += timedelta(days=1)
        self.add(q)
        self.assertEqual(self.view()["measurement"]["return_day7"], {"eligible": True, "returned": False})

    def test_matched_seven_day_recall_boundary_and_regression(self):
        q, unrelated, _ = self.diverse()
        self.add(q, correct=0)
        self.add(q)
        self.add(unrelated)
        self.time.return_value += timedelta(days=7, microseconds=-1)
        self.add(q, review=True)
        self.assertEqual(self.view()["measurement"]["retention7"]["total"], 0)
        self.time.return_value += timedelta(microseconds=1)
        self.add(q, review=True)
        self.assertEqual(self.view()["measurement"]["retention7"],
                         {"total": 1, "before_correct": 0, "after_correct": 1})
        self.add(q, review=True, correct=0)
        self.assertEqual(self.view()["measurement"]["retention7"],
                         {"total": 1, "before_correct": 0, "after_correct": 0})
        self.time.return_value += timedelta(days=28)
        self.assertEqual(self.view()["measurement"]["retention7"]["total"], 0)

    def test_speaking_measures_distinct_effort_not_skill_or_opening(self):
        q = next(q for r, s, q in m.canonical_questions("en").values()
                 if r["lesson"] == 1 and s["skill"] == "speaking" and q["mode"] == "self")
        url = "/api/student/course-practice/speaking"
        body = {"language": "en", "lesson": 1, "question_id": q["id"], "messages": []}
        self.assertEqual(self.client.post(url, json=body).status_code, 200)
        self.assertEqual(self.view()["measurement"]["speaking_attempts"], 0)
        body["messages"] = [{"role": "student", "text": "My name is Alex"}]
        for _ in range(2):
            self.assertEqual(self.client.post(url, json=body).status_code, 200)
        self.add(q, answer="Another real speaking answer")
        measure = self.view()["measurement"]
        self.assertEqual(measure["speaking_attempts"], 1)
        self.assertEqual(measure["speaking_days"], 1)
        self.assertEqual(measure["retention7"]["total"], 0)
        # Repeating a legitimate response on a later day is new daily effort,
        # while network retries within that day remain idempotent.
        self.time.return_value += timedelta(days=1)
        for _ in range(2):
            self.assertEqual(self.client.post(url, json=body).status_code, 200)
        later = self.view()["measurement"]
        self.assertEqual(later["speaking_days"], 2)
        self.assertEqual(later["speaking_attempts"], 2)

    def test_foundation_short_speaking_is_real_effort_not_self_rating(self):
        self.real()
        m.opt_in(self.db, self.student, "en", True)
        known = m.canonical_questions("en")
        for lesson, answer in ((1, "robot, kind"), (2, "help"), (2, "walk")):
            q = next(q for r, sec, q in known.values()
                     if r["lesson"] == lesson and sec["skill"] == "speaking")
            self.add(q, correct=0, answer=answer)
        measure = self.view()["measurement"]
        self.assertEqual(measure["speaking_attempts"], 2)  # one question/day
        self.assertIsNotNone(measure["started_on"])
        self.assertEqual(m.weekly(self.db, self.student, "en")["my_points"], 1)
        q = next(q for r, sec, q in known.values() if r["lesson"] == 1 and sec["skill"] == "speaking")
        for answer in ("done", "ok", "yes", "5", "robot robot robot", "x x x", "..."):
            attempt = SimpleNamespace(ref=practice._ref(q["id"]), answer=answer)
            self.assertFalse(m.substantive(attempt, known), answer)

    def test_weekly_wrong_no_xp_since_join_and_demo_exclusion(self):
        self.real()
        q, second, _ = self.diverse()
        self.add(q, correct=0)  # Same timestamp but before enrollment in the team.
        m.opt_in(self.db, self.student, "en", True)
        self.assertEqual(m.weekly(self.db, self.student, "en")["my_points"], 0)
        self.add(q, correct=0)
        self.add(q, correct=0)
        self.add(second, correct=0)
        self.assertEqual(m.weekly(self.db, self.student, "en")["my_points"], 2)
        self.assertEqual(self.db.query(models.XpTransaction).count(), 0)
        self.assertEqual(m.weekly(self.db, self.student, "de")["my_points"], 0)
        self.db.get(models.Branch, 1).is_test = 1
        self.db.flush()
        self.assertFalse(m.weekly(self.db, self.student, "en")["opted_in"])

    def test_weekly_blank_and_self_spam_bounded_and_daily_cap(self):
        self.real()
        m.opt_in(self.db, self.student, "en", True)
        selfqs = [q for _, _, q in m.canonical_questions("en").values() if q["mode"] == "self"][:10]
        for q in selfqs:
            self.add(q, correct=0, answer="x x x x x")
        self.add(self.diverse()[0], answer=" ... ")
        self.assertEqual(m.weekly(self.db, self.student, "en")["my_points"], 0)
        for q in selfqs:
            self.add(q, correct=0, answer="I explain my answer")
        self.assertEqual(m.weekly(self.db, self.student, "en")["my_points"], 1)
        for lesson in range(1, 4):
            for q in self.diverse(lesson):
                self.add(q, correct=0)
        self.assertEqual(m.weekly(self.db, self.student, "en")["my_points"], 5)
        m.opt_in(self.db, self.student, "en", False)
        m.opt_in(self.db, self.student, "en", True)
        self.assertEqual(m.weekly(self.db, self.student, "en")["my_points"], 5)
        self.time.return_value += timedelta(days=1)
        self.add(self.diverse()[0], correct=0)
        result = m.weekly(self.db, self.student, "en")
        self.assertEqual(result["my_points"], 6)
        self.assertEqual(set(result["mission"]), {"title", "instruction"})


if __name__ == "__main__":
    unittest.main()
