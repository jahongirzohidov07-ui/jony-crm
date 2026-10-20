"""Isolated, persisted-attempt endpoint regressions; no live DB or AI."""
import unittest
from datetime import timedelta
from types import SimpleNamespace

import test_course_learning_evidence as fixture
import models
import course_motivation as m
from auth import get_current_user


class SessionSummaryTests(unittest.TestCase):
    setUp = fixture.LearningEvidenceTests.setUp
    tearDown = fixture.LearningEvidenceTests.tearDown
    items = fixture.LearningEvidenceTests.items
    diverse = fixture.LearningEvidenceTests.diverse
    add = fixture.LearningEvidenceTests.add

    def summary(self, language="en"):
        response = self.client.get("/api/student/course-practice/session-summary",
                                   params={"language": language})
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()

    def plan(self, questions=None, language="en", student=1, minutes=25):
        if questions is None:
            questions = self.diverse(language=language)
        m.put(self.db, f"course-plan:v1:{student}:{language}:current", {
            "day": m.local_day().isoformat(), "created_at": m.now().isoformat(),
            "after_id": self.db.query(models.SkillAttempt).count(),
            "steps": [{"question_id": q["id"], "minutes": 5} for q in questions]})
        m.put(self.db, m.plan_preference_key(student, language), minutes)
        self.db.commit()
        return questions

    def test_missing_stale_and_empty_plan_are_explicit_and_read_only(self):
        q = self.diverse()[0]
        self.add(q)
        self.db.commit()
        before = self.db.query(models.IntegrationSetting).count()
        view = self.summary()
        self.assertEqual(view["plan"], {"status": "missing", "total": 0, "completed": 0})
        self.assertIsNone(view["comparison"])
        self.assertIsNone(view["next_review"])
        self.assertEqual(view["independent"]["count"], 0)
        self.assertEqual(self.db.query(models.IntegrationSetting).count(), before)
        self.plan([])
        self.assertEqual(self.summary()["plan"], {"status": "active", "total": 0, "completed": 0})
        self.time.return_value += timedelta(days=1)
        self.assertEqual(self.summary()["plan"]["status"], "missing")

    def test_first_ever_correct_and_reloads_deduplicate_without_rewards(self):
        q = self.plan()[0]
        for _ in range(3):
            self.add(q)
        self.db.commit()
        a = self.summary()
        self.db.expire_all()
        self.assertEqual(a, self.summary())
        self.assertEqual(a["independent"]["count"], 1)
        self.assertEqual(a["plan"]["completed"], 1)
        self.assertEqual(a["corrections"]["count"], 0)
        self.assertIsNone(a["comparison"])
        self.assertEqual(self.db.query(models.XpTransaction).count(), 0)
        self.assertEqual(self.db.query(models.SkillAttempt).count(), 3)

    def test_wrong_repeats_are_not_corrections_then_right_is_one_correction(self):
        q = self.plan()[0]
        for _ in range(3):
            self.add(q, correct=0)
        a = self.summary()
        self.assertEqual(a["corrections"]["count"], 0)
        self.assertEqual(a["independent"]["count"], 0)
        self.assertEqual(a["needs_practice"]["count"], 1)
        for _ in range(3):
            self.add(q)
        a = self.summary()
        self.assertEqual(a["corrections"]["count"], 1)
        self.assertEqual(a["independent"]["count"], 0)
        self.assertEqual(a["needs_practice"]["count"], 0)
        self.add(q, correct=0)
        regressed = self.summary()
        self.assertEqual(regressed["needs_practice"]["count"], 1)
        self.assertEqual(regressed["corrections"]["count"], 1)

    def test_prior_attempt_disqualifies_independence_and_is_comparable(self):
        q = self.diverse()[0]
        self.add(q, correct=0, at=m.now() - timedelta(days=1))
        self.plan([q])
        self.add(q)
        a = self.summary()
        self.assertEqual(a["independent"]["count"], 0)
        self.assertEqual(a["corrections"]["count"], 1)
        self.assertEqual(a["comparison"], {"question_count": 1, "before_correct": 0, "after_correct": 1})
        self.add(q, correct=0)
        self.assertEqual(self.summary()["comparison"]["after_correct"], 0)

    def test_comparison_uses_same_questions_and_latest_previous_day(self):
        q, fresh, unrelated = self.diverse()
        self.add(q, correct=0, at=m.now() - timedelta(days=2))
        self.add(q, at=m.now() - timedelta(days=1))
        self.add(unrelated, at=m.now() - timedelta(days=1))
        self.plan([q, fresh])
        self.add(q, correct=0)
        self.add(fresh)
        self.assertEqual(self.summary()["comparison"],
                         {"question_count": 1, "before_correct": 1, "after_correct": 0})

    def test_prior_correct_does_not_count_as_a_correction(self):
        q = self.diverse()[0]
        self.add(q, correct=0, at=m.now() - timedelta(days=2))
        self.add(q, at=m.now() - timedelta(days=1))
        self.plan([q])
        self.add(q)
        a = self.summary()
        self.assertEqual(a["corrections"]["count"], 0)
        self.assertEqual(a["independent"]["count"], 0)
        self.assertEqual(a["comparison"],
                         {"question_count": 1, "before_correct": 1, "after_correct": 1})

    def test_ungraded_is_separate_and_has_no_recall_or_failure(self):
        q = next(q for _, _, q in m.canonical_questions("en").values() if q["mode"] == "self")
        self.plan([q])
        self.add(q, correct=0)
        self.add(q, correct=0)
        a = self.summary()
        self.assertEqual(a["ungraded"]["count"], 1)
        for group in ("independent", "corrections", "needs_practice"):
            self.assertEqual(a[group]["count"], 0)
        self.assertIsNone(a["next_review"])
        self.assertIsNone(a["comparison"])

    def test_scope_budget_duplicates_watermark_and_future_attempts(self):
        a, b, c = self.diverse()
        self.add(a)
        self.plan([a, a, b, c], minutes=15)
        self.add(b, student=2)
        self.add(c)
        self.add(b, at=m.now() + timedelta(seconds=1))
        view = self.summary()
        self.assertEqual(view["plan"], {"status": "active", "total": 2, "completed": 0})
        self.assertEqual(view["independent"]["count"], 0)
        self.add(b)
        self.assertEqual(self.summary()["plan"]["completed"], 1)
        self.assertEqual(self.summary("de")["plan"]["status"], "missing")

    def test_tashkent_day_boundary_and_equal_timestamp_order(self):
        self.time.return_value = m.now().replace(hour=19, minute=0)
        q = self.diverse()[0]
        self.add(q, correct=0, at=m.now() - timedelta(microseconds=1))
        self.plan([q])
        self.add(q, correct=0)
        self.add(q)
        a = self.summary()
        self.assertEqual(a["date"], "2026-10-20")
        self.assertEqual(a["corrections"]["count"], 1)
        self.assertEqual(a["comparison"]["question_count"], 1)

    def test_recall_matches_existing_schedule_and_exposure_deferral(self):
        q = self.plan()[0]
        self.add(q)
        self.assertEqual(self.summary()["next_review"]["due_at"], "2026-10-20")
        m.put(self.db, m.state_key(1, q["id"]), {"stage": 2, "due": "2026-10-26"})
        self.assertEqual(self.summary()["next_review"]["due_at"], "2026-10-26")
        m.put(self.db, m.state_key(1, q["id"]), {"stage": len(m.REVIEW_INTERVALS), "due": "2026-10-26"})
        self.assertIsNone(self.summary()["next_review"])
        self.add(q, correct=0)
        self.assertEqual(self.summary()["next_review"]["due_at"], "2026-10-26")

    def test_review_attempts_and_language_are_scoped(self):
        en = self.diverse()[0]
        de = self.diverse(language="de")[0]
        self.plan([en])
        self.plan([de], language="de")
        self.add(en, correct=0)
        self.add(en, review=True)
        self.add(de)
        self.assertEqual(self.summary()["corrections"]["items"][0]["question_id"], en["id"])
        self.assertEqual(self.summary("de")["independent"]["items"][0]["question_id"], de["id"])
        self.user = SimpleNamespace(id=22, role="student", full_name="Two", is_active=1)
        self.assertEqual(self.summary()["plan"]["status"], "missing")

    def test_prompt_projection_has_no_answer_keys_even_for_untouched(self):
        q, untouched, _ = self.plan()
        self.add(q)
        a = self.summary()
        self.assertNotIn(untouched["id"], str(a))
        item = a["independent"]["items"][0]
        self.assertEqual(set(item), {"question_id", "lesson", "prompt", "skill"})
        self.assertEqual(item["prompt"], q["prompt"])
        for key in ("expected", "explanation", "transcript", "mastery", "cefr"):
            self.assertNotIn('"' + key + '"', self.client.get(
                "/api/student/course-practice/session-summary").text)

    def test_auth_and_parameter_validation(self):
        url = "/api/student/course-practice/session-summary"
        self.assertEqual(self.client.get(url + "?language=fr").status_code, 422)
        self.assertEqual(self.client.get(url + "?student_id=2").status_code, 422)
        self.user = SimpleNamespace(id=11, role="teacher", full_name="One", is_active=1)
        self.assertEqual(self.client.get(url).status_code, 403)
        self.user = SimpleNamespace(id=33, role="student", full_name="Unlinked", is_active=1)
        self.assertEqual(self.client.get(url).status_code, 403)
        del self.app.dependency_overrides[get_current_user]
        self.assertIn(self.client.get(url).status_code, (401, 403))

    def test_blank_and_unknown_attempts_do_not_create_observations(self):
        q = self.plan()[0]
        self.add(q, answer="   ")
        self.add({"id": "en:1:unknown"})
        self.assertEqual(self.summary()["plan"]["completed"], 0)
        # Even a punctuation-only incorrect response is a real checked failure.
        self.add(q, correct=0, answer="?")
        self.add(q)
        self.assertEqual(self.summary()["independent"]["count"], 0)
        self.assertEqual(self.summary()["corrections"]["count"], 1)


if __name__ == "__main__":
    unittest.main()
