"""Run: python api/test_course_feedback.py. Isolated DB, mocked provider, no paid calls."""
import json
import unittest
from datetime import datetime, timezone, timedelta
from types import SimpleNamespace
from unittest.mock import patch
from test_course_portfolio import PortfolioTests
import course_missions as missions
import course_portfolio as portfolio
import student_course_practice as practice
import models


class FeedbackTests(unittest.TestCase):
    setUp = PortfolioTests.setUp
    tearDown = PortfolioTests.tearDown
    url = PortfolioTests.url
    body = PortfolioTests.body
    audio = PortfolioTests.audio
    create = PortfolioTests.create

    def endpoint(self, entry, number=1):
        return self.url(entry["id"] + "/feedback/" + str(number))

    def reply(self, text="Hello", before=None):
        return json.dumps({
            "criteria": [{"id": key, "evidence": text, "comment": "Specific contextual explanation"}
                         for key in missions.RUBRIC],
            "next_step": "Use 'Hello, my friend!' to address your friend.",
            "comparison": None if before is None else {
                "before": before, "after": text, "comment": "The greeting now identifies its listener."}})

    def test_explicit_only_private_immutable_and_no_rewards(self):
        with patch("speaking_ai.speaking_reply", return_value=self.reply()) as ai:
            entry = self.create(audio=self.audio())
            self.client.get(self.url())
            self.client.get(self.url(entry["id"]))
            ai.assert_not_called()
            response = self.client.post(self.endpoint(entry))
            self.assertEqual(response.status_code, 200, response.text)
            self.assertIn("no-store", response.headers["cache-control"])
            feedback = response.json()["versions"][0]["feedback"]
            self.assertEqual(feedback["status"], "ready")
            self.client.post(self.endpoint(entry))
            self.client.get(self.url(entry["id"]))
            self.assertEqual(ai.call_count, 1)
            payload = json.loads(ai.call_args.args[1][0]["text"])
            self.assertNotIn("audio", payload)
            self.assertNotIn("title", payload)
            self.assertNotIn("student_id", payload)
            self.assertNotIn("base64", str(payload))
            self.assertFalse(feedback["assessed_audio"])
            self.assertFalse(feedback["verified_mastery"])
            self.assertEqual(feedback["xp"], 0)
            saved = self.client.put(self.url(entry["id"]), json=self.body(text="Hello, friend!", expected_version=1)).json()
            self.assertEqual(saved["versions"][0]["feedback"], feedback)
            self.assertNotIn("feedback", saved["versions"][1])
            key, raw, state = portfolio._load(self.db, 1)
            self.assertNotIn("feedback", state["entries"][0]["versions"][0])
            self.assertEqual(self.db.query(models.SkillAttempt).count(), 0)
            self.assertEqual(self.db.query(models.XpTransaction).count(), 0)

    def test_revision_comparison_and_mission_prompt(self):
        mission = self.client.get(self.url()).json()["missions"][0]
        entry = self.create(mission_id=mission["id"])
        self.client.put(self.url(entry["id"]), json=self.body(text="Hello, friend!", expected_version=1))
        with patch("speaking_ai.speaking_reply", return_value=self.reply("friend", "Hello")) as ai:
            response = self.client.post(self.endpoint(entry, 2))
        result = response.json()["versions"][1]["feedback"]
        self.assertEqual(result["status"], "ready")
        self.assertEqual(result["comparison"]["previous_version"], 1)
        payload = json.loads(ai.call_args.args[1][0]["text"])
        self.assertEqual(payload["task"], mission["prompt"])
        self.assertTrue(payload["foundation"])
        self.assertEqual(payload["previous_text"], "Hello, my friend!")

    def test_failure_retry_and_ready_never_replaced(self):
        entry = self.create()
        with patch("speaking_ai.speaking_reply", side_effect=RuntimeError("secret-provider-body")) as ai:
            result = self.client.post(self.endpoint(entry)).json()
        self.assertEqual(result["versions"][0]["feedback"]["status"], "unavailable")
        self.assertNotIn("secret-provider-body", json.dumps(result))
        with patch("speaking_ai.speaking_reply", return_value=self.reply()) as ai:
            result = self.client.post(self.endpoint(entry)).json()
            self.assertEqual(result["versions"][0]["feedback"]["attempts"], 2)
            self.assertEqual(result["versions"][0]["feedback"]["status"], "ready")
            self.client.post(self.endpoint(entry))
            self.assertEqual(ai.call_count, 1)

    def test_malformed_and_hallucinated_evidence_are_unavailable(self):
        row = practice.LESSONS["en"][1]
        version = {"text": "Hello", "number": 1}
        for reply in ["not json", "[]", self.reply("invented"), self.reply().replace('"grammar"', '"meaning"')]:
            with patch("speaking_ai.speaking_reply", return_value=reply):
                self.assertEqual(missions.semantic_feedback("en", row, version)["status"], "unavailable")

    def test_retry_cap_and_daily_budget_survive_delete(self):
        with patch("speaking_ai.speaking_reply", side_effect=TimeoutError()) as ai:
            for _ in range(2):
                entry = self.create()
                for attempt in (1, 2, 3):
                    result = self.client.post(self.endpoint(entry))
                    self.assertEqual(result.status_code, 200)
                    self.assertEqual(result.json()["versions"][0]["feedback"]["attempts"], attempt)
                self.assertEqual(self.client.post(self.endpoint(entry)).status_code, 429)
                self.client.delete(self.url(entry["id"]))
            entry = self.create()
            self.assertEqual(self.client.post(self.endpoint(entry)).status_code, 429)
            self.assertEqual(ai.call_count, 6)

    def test_pending_claim_blocks_duplicate_and_stale_can_retry(self):
        entry = self.create()
        def complete(*args):
            nested = self.client.post(self.endpoint(entry))
            self.assertEqual(nested.json()["versions"][0]["feedback"]["status"], "pending")
            self.assertNotIn("claim", nested.text)
            return self.reply()
        with patch("speaking_ai.speaking_reply", side_effect=complete) as ai:
            self.assertEqual(self.client.post(self.endpoint(entry)).status_code, 200)
            self.assertEqual(ai.call_count, 1)
        key, old, state = portfolio._load(self.db, 1)
        state["entries"][0]["feedbacks"]["1"] = {
            "status": "pending", "claim": "dead-worker", "version": 1, "attempts": 1,
            "requested_at": (datetime.now(timezone.utc) - timedelta(seconds=121)).isoformat()}
        portfolio._persist(self.db, key, old, state)
        with patch("speaking_ai.speaking_reply", return_value=self.reply()) as ai:
            projected = self.client.get(self.url(entry["id"])).json()["versions"][0]["feedback"]
            self.assertEqual(projected["status"], "unavailable")
            ai.assert_not_called()
            response = self.client.post(self.endpoint(entry))
            self.assertEqual(response.json()["versions"][0]["feedback"]["attempts"], 2)
            self.assertEqual(ai.call_count, 1)

    def test_authorization_scope_audio_and_missing_version(self):
        entry = self.create()
        with patch("speaking_ai.speaking_reply") as ai:
            self.assertEqual(self.client.post(self.endpoint(entry, 99)).status_code, 404)
            self.assertEqual(self.client.post(self.endpoint(entry).replace("language=en", "language=de")).status_code, 404)
            audio = self.create(text="", audio=self.audio())
            self.assertEqual(self.client.post(self.endpoint(audio)).status_code, 422)
            self.user = SimpleNamespace(id=22, role="student", full_name="Two", is_active=1)
            self.assertEqual(self.client.post(self.endpoint(entry)).status_code, 404)
            ai.assert_not_called()

    def test_tashkent_budget_day(self):
        entry = self.create()
        instant = datetime(2026, 10, 19, 20, 0, tzinfo=timezone.utc)
        class Clock(datetime):
            @classmethod
            def now(cls, tz=None):
                return instant.astimezone(tz)
        with patch.object(portfolio, "datetime", Clock), patch("speaking_ai.speaking_reply", return_value=self.reply()):
            self.client.post(self.endpoint(entry))
        state = portfolio._load(self.db, 1)[2]
        self.assertEqual(state["feedback_budget"]["day"], "2026-10-20")

    def test_concurrent_revision_is_preserved(self):
        entry = self.create()
        def complete(*args):
            response = self.client.put(self.url(entry["id"]), json=self.body(text="New text", expected_version=1))
            self.assertEqual(response.status_code, 200)
            return self.reply()
        with patch("speaking_ai.speaking_reply", side_effect=complete):
            response = self.client.post(self.endpoint(entry))
        versions = response.json()["versions"]
        self.assertEqual(len(versions), 2)
        self.assertEqual(versions[0]["feedback"]["status"], "ready")
        self.assertEqual(versions[1]["text"], "New text")
        self.assertNotIn("feedback", versions[1])

    def test_recent_work_across_lessons_bounded_and_metadata_only(self):
        entries = []
        for lesson in range(1, 8):
            response = self.client.post(self.url(lesson=lesson), json=self.body(title=f"Work {lesson}", audio=self.audio()))
            self.assertEqual(response.status_code, 201)
            entries.append(response.json())
        response = self.client.get(self.url(lesson=20))
        self.assertIn("no-store", response.headers["cache-control"])
        self.assertEqual(response.headers["vary"], "Authorization")
        listing = response.json()
        self.assertEqual(listing["entries"], [])
        self.assertEqual([item["id"] for item in listing["recent_works"]],
                         [entry["id"] for entry in reversed(entries[-5:])])
        self.assertTrue(all(set(item) == {"id", "lesson", "title", "updated_at"}
                            for item in listing["recent_works"]))
        updated = self.client.put(self.url(entries[0]["id"]), json=self.body(
            title="Revised title", expected_version=1))
        self.assertEqual(updated.status_code, 200)
        recent = self.client.get(self.url()).json()["recent_works"]
        self.assertEqual(recent[0]["id"], entries[0]["id"])
        self.assertEqual(recent[0]["title"], "Revised title")
        self.client.delete(self.url(entries[0]["id"]))
        self.assertNotIn(entries[0]["id"], [e["id"] for e in self.client.get(self.url()).json()["recent_works"]])

    def test_recent_work_language_and_account_isolation(self):
        english = self.create(title="English private")
        german = self.client.post(self.url(language="de", lesson=2),
                                 json=self.body(title="German private")).json()
        with patch("speaking_ai.speaking_reply") as ai:
            en = self.client.get(self.url(lesson=5)).json()["recent_works"]
            de = self.client.get(self.url(language="de", lesson=5)).json()["recent_works"]
            self.assertEqual([e["id"] for e in en], [english["id"]])
            self.assertEqual([e["id"] for e in de], [german["id"]])
            self.user = SimpleNamespace(id=22, role="student", full_name="Two", is_active=1)
            for language in ("en", "de"):
                self.assertEqual(self.client.get(self.url(language=language)).json()["recent_works"], [])
            other = self.create(title="Other account")
            self.assertEqual(self.client.get(self.url()).json()["recent_works"][0]["id"], other["id"])
            self.user = SimpleNamespace(id=11, role="student", full_name="One", is_active=1)
            self.assertEqual([e["id"] for e in self.client.get(self.url()).json()["recent_works"]], [english["id"]])
            ai.assert_not_called()


if __name__ == "__main__":
    unittest.main()
