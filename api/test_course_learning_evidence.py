"""Learning evidence uses an isolated SQLite fixture and no external services."""
import unittest
from sqlalchemy import event
from datetime import datetime, timedelta
from unittest.mock import patch

import test_student_course_practice as baseline
import models
import course_motivation as m
import student_course_practice as practice


class LearningEvidenceTests(unittest.TestCase):
    tearDown = baseline.CoursePracticeTests.tearDown

    def setUp(self):
        baseline.CoursePracticeTests.setUp(self)
        self.clock = patch.object(m, "now", return_value=datetime(2026, 10, 19, 8))
        self.time = self.clock.start()
        self.addCleanup(self.clock.stop)
        self.student = self.db.get(models.Student, 1)

    def items(self, lesson=1, language="en"):
        return [(section, q) for row, section, q in m.exact_questions(language).values()
                if row["lesson"] == lesson]

    def diverse(self, lesson=1, language="en"):
        items = self.items(lesson, language)
        first = items[0]
        other = next(item for item in items if item[0]["id"] != first[0]["id"])
        third = next(item for item in items if item[1]["id"] not in {first[1]["id"], other[1]["id"]})
        return [first[1], other[1], third[1]]

    def add(self, q, correct=1, at=None, review=False, answer="meaningful answer", student=1):
        self.db.add(models.SkillAttempt(student_id=student, skill="course-practice:en:reading",
                    ref=("course-review:v1:" if review else "course-practice:v1:") + q["id"],
                    answer=answer, correct=correct, created_at=at or m.now()))
        self.db.flush()

    def view(self, language="en"):
        return m.motivation(self.db, self.student, language)

    def test_readiness_requires_distinct_questions_and_sections(self):
        items = self.items()
        same = [q for section, q in items if section["id"] == items[0][0]["id"]][:3]
        for q in same:
            self.add(q)
        for _ in range(4):
            self.add(same[0])
        self.assertNotIn(1, m.ready_lessons(self.db, 1, "en"))
        for q in self.diverse():
            self.add(q)
        self.assertIn(1, m.ready_lessons(self.db, 1, "en"))
        self.assertNotIn(1, m.mastered_lessons(self.db, 1, "en"))

    def test_delayed_recall_boundary_and_latest_failure(self):
        questions = self.diverse()
        first = m.now()
        for q in questions:
            self.add(q)
        self.time.return_value = first + timedelta(hours=24) - timedelta(microseconds=1)
        for q in questions:
            self.add(q, review=True)
        self.assertEqual(m.evidence(self.db, 1, "en")["delayed_recall"], {"correct": 0, "total": 0})
        self.time.return_value = first + timedelta(hours=24)
        for q in questions:
            self.add(q, review=True)
        self.assertIn(1, m.mastered_lessons(self.db, 1, "en"))
        self.add(questions[0], correct=0)
        self.assertNotIn(1, m.ready_lessons(self.db, 1, "en"))
        self.assertNotIn(1, m.mastered_lessons(self.db, 1, "en"))
        evidence = m.evidence(self.db, 1, "en")
        self.assertEqual(evidence["delayed_recall"], {"correct": 3, "total": 3})
        self.assertEqual(evidence["first_attempt"], {"correct": 3, "total": 3})

    def test_practice_after_day_is_not_verified_recall(self):
        q = self.diverse()[0]
        self.add(q, correct=0)
        self.add(q)
        self.time.return_value += timedelta(days=2)
        self.add(q)
        ev = m.evidence(self.db, 1, "en")
        self.assertEqual(ev["first_attempt"], {"correct": 0, "total": 1})
        self.assertEqual(ev["delayed_recall"], {"correct": 0, "total": 0})
        self.assertEqual(m.mastery(self.db, 1, "en"), {})

    def test_correction_after_forgetting_needs_new_recall(self):
        q = self.diverse()[0]
        self.add(q)
        self.time.return_value += timedelta(days=1)
        self.add(q, review=True)
        self.assertIn(q["id"], m.mastery(self.db, 1, "en"))
        self.add(q, correct=0)
        self.add(q)
        self.assertNotIn(q["id"], m.mastery(self.db, 1, "en"))
        self.time.return_value += timedelta(days=1)
        self.add(q, review=True)
        self.assertIn(q["id"], m.mastery(self.db, 1, "en"))

    def test_api_contract_disabled_rewards_still_count_effort(self):
        self.db.add(models.XpRule(event_code="course_practice_correct", is_active=0,
                                  name="Paused", default_xp=2, category="academic"))
        self.db.commit()
        response = self.client.get("/api/student/course-practice/motivation?language=en")
        self.assertEqual(response.status_code, 200, response.text)
        before = response.json()["plan"]
        step = before["steps"][0]
        q = m.canonical_questions("en")[step["question_id"]][2]
        response = self.client.post("/api/student/course-practice/answer", json={
            "language": "en", "lesson": step["lesson"], "question_id": q["id"], "answer": q["expected"][0]})
        self.assertEqual(response.status_code, 200, response.text)
        view = self.client.get("/api/student/course-practice/motivation?language=en").json()
        self.assertEqual(view["daily"]["done"], 1)
        self.assertEqual(view["rewards"]["xp"], 0)
        self.assertEqual(view["plan"]["steps"][0]["id"], step["id"])
        self.assertTrue(view["plan"]["steps"][0]["done"])
        self.assertEqual(set(view["evidence"]), {"lessons", "first_attempt", "delayed_recall", "comparison", "skills", "since"})

    def test_small_bank_threshold_and_no_exact_questions(self):
        bank = {"en": [{"lesson": 1, "sections": [
            {"id": "a", "questions": [{"id": "a", "mode": "exact", "expected": ["a"]}]},
            {"id": "b", "questions": [{"id": "b", "mode": "exact", "expected": ["b"]}]}]},
            {"lesson": 2, "sections": []}]}
        with patch.object(practice, "BANK", bank):
            self.assertEqual(m.lesson_coverage("en", {"a"}), set())
            self.assertEqual(m.lesson_coverage("en", {"a", "b"}), {1})

    def test_daily_effort_no_ledger_repeats_self_and_local_midnight(self):
        self.student.full_name = "Learner (demo)"
        q = self.diverse()[0]
        boundary = datetime(2026, 10, 18, 19)
        self.add(q, correct=0, at=boundary)
        self.add(q, correct=0)
        selfq = next(q for _, _, q in m.canonical_questions("en").values() if q["mode"] == "self")
        self.add(selfq, correct=1)  # A forged legacy correct flag must not verify a self check.
        self.add(self.diverse()[1], at=boundary-timedelta(microseconds=1))
        self.add(self.diverse()[2], answer=" ... ")
        view = self.view()
        self.assertEqual(view["daily"], {"target": 5, "done": 2})
        self.assertEqual(view["rewards"]["xp"], 0)
        self.assertEqual(sum(x["self_assessed"] for x in view["evidence"]["skills"]), 1)
        self.assertEqual(view["evidence"]["first_attempt"], {"correct": 1, "total": 2})
        self.assertEqual(self.view("de")["daily"]["done"], 0)

    def test_stable_plan_completion_wrong_effort_and_rollover(self):
        first = self.view()["plan"]
        self.assertEqual(len(first["steps"]), 3)
        self.assertEqual(sum(step["minutes"] for step in first["steps"]), 15)
        self.assertEqual(first["steps"][0]["kind"], "practice")
        for step in first["steps"]:
            self.add(m.canonical_questions("en")[step["question_id"]][2], correct=0)
        practice._save_position(self.db, 1, "en", 12)
        second = self.view()["plan"]
        self.assertEqual([s["id"] for s in first["steps"]], [s["id"] for s in second["steps"]])
        self.assertTrue(second["completed"])
        self.time.return_value += timedelta(days=1)
        third = self.view()["plan"]
        self.assertFalse(third["completed"])
        self.assertNotEqual(first["steps"][0]["id"], third["steps"][0]["id"])
        self.assertEqual(third["steps"][0]["kind"], "review")

    def test_due_review_then_latest_wrong_then_current_speaking(self):
        due = self.diverse(1)[0]
        self.add(due)
        self.time.return_value += timedelta(days=1)
        wrong = self.diverse(4)[0]
        self.add(wrong, correct=0)
        practice._save_position(self.db, 1, "en", 7)
        plan = self.view()["plan"]
        self.assertEqual(plan["steps"][0]["kind"], "review")
        self.assertEqual(plan["steps"][0]["question_id"], due["id"])
        self.assertEqual(plan["steps"][1]["question_id"], wrong["id"])
        self.assertEqual(plan["steps"][2]["lesson"], 7)
        self.assertEqual(plan["steps"][2]["kind"], "speaking")

    def test_challenge_effort_is_unique_and_not_lesson_evidence(self):
        q = {"id": "en:boss:1:1"}
        bank = {1: {"questions": [q]}}
        with patch.object(m, "checkpoint_bank", return_value=bank):
            for _ in range(2):
                self.db.add(models.SkillAttempt(student_id=1, skill="course-challenge:en",
                            ref="course-challenge:v1:" + q["id"], answer="wrong but attempted",
                            correct=0, created_at=m.now()))
            self.db.flush()
            self.assertEqual(m.daily_effort(self.db, 1, "en"), {q["id"]})
            self.assertEqual(m.evidence(self.db, 1, "en")["first_attempt"]["total"], 0)

    def test_latest_delayed_result_overrides_previous_success(self):
        q = self.diverse()[0]
        self.add(q)
        self.time.return_value += timedelta(days=1)
        self.add(q, review=True)
        self.add(q, review=True, correct=0)
        self.assertEqual(m.evidence(self.db, 1, "en")["delayed_recall"], {"correct": 0, "total": 1})

    def test_exposed_review_becomes_same_target_practice_without_completion(self):
        q = self.diverse()[0]
        self.add(q)
        self.time.return_value += timedelta(days=1)
        before = self.view()["plan"]["steps"][0]
        self.assertEqual(before["kind"], "review")
        m.expose_feedback(self.db, 1, {q["id"]: m.now()})
        after = self.view()["plan"]["steps"][0]
        self.assertEqual(after["id"], before["id"])
        self.assertEqual(after["question_id"], before["question_id"])
        self.assertEqual(after["kind"], "practice")
        self.assertFalse(after["done"])
        self.add(q)
        self.assertTrue(self.view()["plan"]["steps"][0]["done"])
        self.assertEqual(m.evidence(self.db, 1, "en")["delayed_recall"]["total"], 0)

    def test_plan_storage_is_bounded_across_days(self):
        for _ in range(3):
            self.view()
            self.time.return_value += timedelta(days=1)
        count = self.db.query(models.IntegrationSetting).filter(
            models.IntegrationSetting.key.startswith("course-plan:v1:1:en:")).count()
        self.assertEqual(count, 1)

    def test_query_count_does_not_grow_per_question(self):
        self.view()  # Persist the daily queue/plan before comparing steady-state reads.
        statements = []
        def record(conn, cursor, statement, parameters, context, executemany):
            if statement.lstrip().upper().startswith("SELECT"):
                statements.append(statement)
        event.listen(self.engine, "before_cursor_execute", record)
        try:
            self.view()
            empty_count = len(statements)
            for lesson in range(1, 21):
                for q in self.diverse(lesson):
                    self.add(q)
            statements.clear()
            self.view()
            self.assertEqual(len(statements), empty_count)
            self.assertLess(len(statements), 30)
        finally:
            event.remove(self.engine, "before_cursor_execute", record)

    def test_comparison_uses_identical_question_denominator(self):
        first, second, unrelated = self.diverse()
        self.add(first, correct=0)
        self.add(first)
        self.add(second)
        self.add(unrelated)
        self.time.return_value += timedelta(hours=24)
        self.add(first, review=True)
        self.add(first, review=True)  # Repeats must not increase the denominator.
        self.add(second, review=True, correct=0)
        ev = m.evidence(self.db, 1, "en")
        self.assertEqual(ev["first_attempt"]["total"], 3)
        self.assertEqual(ev["comparison"], {"total": 2, "before_correct": 1, "after_correct": 1})

    def test_comparison_regresses_on_latest_review_failure(self):
        q = self.diverse()[0]
        self.add(q)
        self.time.return_value += timedelta(hours=24)
        self.add(q, review=True)
        self.assertEqual(m.evidence(self.db, 1, "en")["comparison"],
                         {"total": 1, "before_correct": 1, "after_correct": 1})
        self.add(q, review=True, correct=0)
        self.add(q)  # Ordinary practice cannot replace the delayed-review result.
        self.assertEqual(m.evidence(self.db, 1, "en")["comparison"],
                         {"total": 1, "before_correct": 1, "after_correct": 0})

    def test_comparison_requires_normal_baseline_and_eligible_delay(self):
        q, orphan, early = self.diverse()
        self.assertEqual(m.evidence(self.db, 1, "en")["comparison"],
                         {"total": 0, "before_correct": 0, "after_correct": 0})
        self.add(q, review=True)  # Legacy review cannot become the normal baseline.
        self.add(q, correct=0)
        self.add(q)
        self.add(orphan, review=True)
        self.add(early)
        self.time.return_value += timedelta(hours=23)
        self.add(early, review=True)
        self.time.return_value += timedelta(hours=1)
        self.add(q, review=True)
        self.add(orphan, review=True)
        self.assertEqual(m.evidence(self.db, 1, "en")["comparison"],
                         {"total": 1, "before_correct": 0, "after_correct": 1})

    def test_prior_attempt_does_not_complete_new_plan(self):
        q = self.diverse()[0]
        self.add(q)
        plan = self.view()["plan"]
        self.assertFalse(any(step["done"] for step in plan["steps"]))
        self.add(q, student=2)
        self.assertFalse(self.view()["plan"]["completed"])

    def test_checkpoint_ready_not_retained_and_pass_survives_regression(self):
        for lesson in range(1, 7):
            for q in self.diverse(lesson):
                self.add(q)
        self.assertTrue(m.checkpoint_status(self.db, 1, "en", {"week": 1})["available"])
        self.assertEqual(m.mastered_lessons(self.db, 1, "en"), set())
        state = {"passed": True, "submitted_at": m.now().isoformat(), "reward": {"xp": 15}, "round": 0}
        m.put(self.db, m.boss_key(1, "en", 1), state)
        self.add(self.diverse()[0], correct=0)
        self.assertTrue(m.checkpoint_status(self.db, 1, "en", {"week": 1})["passed"])
        self.assertEqual(m.get(self.db, m.boss_key(1, "en", 1)), state)


if __name__ == "__main__":
    unittest.main()
