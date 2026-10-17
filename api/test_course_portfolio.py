"""Run: python api/test_course_portfolio.py (isolated SQLite, no AI/network)."""
import base64
import json
import os
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

os.environ["DATABASE_URL"] = "sqlite://"
sys.path.insert(0, str(Path(__file__).resolve().parent))
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import models
import course_portfolio as portfolio
import course_missions as missions
import student_course_practice as practice
from auth import get_current_user
from database import get_db


class PortfolioTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
        for table in (models.Student, models.IntegrationSetting, models.SkillAttempt, models.XpTransaction):
            table.__table__.create(self.engine)
        self.sessions = sessionmaker(bind=self.engine)
        self.db = self.sessions()
        self.db.add_all([models.Student(id=1, user_id=11, full_name="One", status="active"),
                         models.Student(id=2, user_id=22, full_name="Two", status="active"),
                         models.Student(id=3, full_name="Unlinked", status="active")])
        self.db.commit()
        self.user = SimpleNamespace(id=11, role="student", full_name="One", is_active=1)
        self.app = FastAPI()
        self.app.include_router(practice.router)
        self.app.dependency_overrides[get_db] = lambda: self.db
        self.app.dependency_overrides[get_current_user] = lambda: self.user
        self.client = TestClient(self.app)

    def tearDown(self):
        self.client.close()
        self.db.close()
        self.engine.dispose()

    def url(self, entry_id="", language="en", lesson=1):
        return "/api/student/course-practice/portfolio" + ("/" + entry_id if entry_id else "") + f"?language={language}&lesson={lesson}"

    def body(self, **changes):
        return {"title": "Mening dialogim", "type": "dialogue", "text": "Hello, my friend!", **changes}

    def audio(self, size=100):
        raw = b"\x1aE\xdf\xa3A_OPUS" + b"\x00" * (size - 10)
        return {"mime": "audio/webm;codecs=opus", "base64": base64.b64encode(raw).decode()}

    def create(self, **changes):
        result = self.client.post(self.url(), json=self.body(**changes))
        self.assertEqual(result.status_code, 201, result.text)
        return result.json()

    def test_immutable_revisions_reload_playback_no_rewards(self):
        first = self.create(audio=self.audio())
        url = self.url(first["id"])
        second_audio = self.audio(150)
        result = self.client.put(url, json=self.body(text="My own revised story", type="story", audio=second_audio, expected_version=1))
        self.assertEqual(result.status_code, 200, result.text)
        self.db.close()
        self.db = self.sessions()
        restored = self.client.get(url)
        self.assertIn("no-store", restored.headers["cache-control"])
        versions = restored.json()["versions"]
        self.assertEqual(versions[0], first["versions"][0])
        self.assertEqual(versions[1]["audio"], second_audio)
        self.assertEqual(versions[1]["text"], "My own revised story")
        self.assertEqual(self.client.put(url, json=self.body(expected_version=1)).status_code, 409)
        listing = self.client.get(self.url()).json()
        self.assertFalse(listing["verified_mastery"])
        self.assertEqual(listing["xp"], 0)
        self.assertNotIn("base64", str(listing))
        self.assertEqual(self.db.query(models.SkillAttempt).count(), 0)
        self.assertEqual(self.db.query(models.XpTransaction).count(), 0)

    def test_student_language_lesson_isolation_and_auth(self):
        entry = self.create()
        for language, lesson in [("de", 1), ("en", 2)]:
            url = self.url(entry["id"], language, lesson)
            self.assertEqual(self.client.get(url).status_code, 404)
            self.assertEqual(self.client.put(url, json=self.body(expected_version=1)).status_code, 404)
            self.assertEqual(self.client.delete(url).status_code, 404)
        self.user = SimpleNamespace(id=22, role="student", full_name="Two", is_active=1)
        self.assertEqual(self.client.get(self.url()).json()["entries"], [])
        self.assertEqual(self.client.get(self.url(entry["id"])).status_code, 404)
        self.assertEqual(self.client.put(self.url(entry["id"]), json=self.body(expected_version=1)).status_code, 404)
        self.assertEqual(self.client.delete(self.url(entry["id"])).status_code, 404)
        for uid, role in [(33, "student"), (11, "teacher")]:
            self.user = SimpleNamespace(id=uid, role=role, full_name="Unlinked", is_active=1)
            self.assertEqual(self.client.get(self.url()).status_code, 403)
        self.assertIsNone(self.db.get(models.Student, 3).user_id)
        self.app.dependency_overrides.pop(get_current_user)
        self.assertIn(self.client.get(self.url()).status_code, (401, 403))

    def test_validation_static_route_and_course_prompts(self):
        for language, lesson, status in [("en", 192, 200), ("de", 72, 200), ("de", 73, 404), ("fr", 1, 422), ("en", 0, 422)]:
            response = self.client.get(self.url(language=language, lesson=lesson))
            self.assertEqual(response.status_code, status, response.text)
            if status == 200:
                self.assertEqual(response.json()["lesson_title"], practice.LESSONS[language][lesson]["title"])
                self.assertTrue(response.json()["prompt"])
        for changes in [dict(title=" "), dict(title="x" * 101), dict(text=" " ), dict(text="x" * 6001),
                        dict(type="essay"), dict(student_id=2), dict(title=1), dict(audio_url="https://example.com/private"),
                        dict(audio={"mime": "text/html", "base64": "YQ=="}),
                        dict(audio={"mime": "audio/webm", "base64": "https://example.com/a"}),
                        dict(audio={"mime": "audio/webm", "base64": base64.b64encode(b"<script>evil</script>").decode()}),
                        dict(audio=self.audio(portfolio.MAX_AUDIO + 1))]:
            self.assertEqual(self.client.post(self.url(), json=self.body(**changes)).status_code, 422)
        self.assertEqual(self.client.get(self.url() + "&student_id=2").status_code, 422)
        self.create(text="", type="speaking", audio=self.audio())

    def test_caps_delete_and_cross_language_total(self):
        first = self.create()
        url = self.url(first["id"])
        for version in (1, 2):
            self.assertEqual(self.client.put(url, json=self.body(expected_version=version)).status_code, 200)
        self.assertEqual(self.client.put(url, json=self.body(expected_version=3)).status_code, 409)
        for _ in range(7):
            self.create()
        self.assertEqual(self.client.post(self.url(), json=self.body()).status_code, 409)
        self.assertEqual(self.client.post(self.url(language="de"), json=self.body()).status_code, 201)
        self.assertEqual(self.client.post(self.url(lesson=2), json=self.body()).status_code, 201)
        self.assertEqual(self.client.delete(url).status_code, 200)
        self.assertEqual(self.client.get(url).status_code, 404)
        self.create()

    def test_text_budget_global_and_delete_recovers_space(self):
        with patch.object(portfolio, "MAX_TOTAL_TEXT", 100):
            entry = self.create(text="x" * 70)
            response = self.client.post(self.url(language="de"), json=self.body(text="x" * 70))
            self.assertEqual(response.status_code, 409)
            self.assertEqual(self.client.get(self.url()).json()["total_entries"], 1)
            self.assertEqual(self.client.delete(self.url(entry["id"])).status_code, 200)
            self.assertEqual(self.client.post(self.url(language="de"), json=self.body(text="x" * 70)).status_code, 201)

    def test_total_audio_cap_does_not_silently_prune(self):
        audio = self.audio(portfolio.MAX_AUDIO)
        for _ in range(2):
            entry = self.create(audio=audio)
            for version in (1, 2):
                self.assertEqual(self.client.put(self.url(entry["id"]), json=self.body(audio=audio, expected_version=version)).status_code, 200)
        entry = self.create(audio=audio)
        url = self.url(entry["id"])
        self.assertEqual(self.client.put(url, json=self.body(audio=audio, expected_version=1)).status_code, 200)
        self.assertEqual(self.client.put(url, json=self.body(audio=audio, expected_version=2)).status_code, 409)
        self.assertEqual(len(self.client.get(url).json()["versions"]), 2)

    def test_compare_and_swap_conflicts_never_overwrite(self):
        self.create()
        key, raw, state = portfolio._load(self.db, 1)
        self.create(title="Other tab")
        with self.assertRaises(HTTPException) as caught:
            portfolio._persist(self.db, key, raw, state)
        self.assertEqual(caught.exception.status_code, 409)
        self.assertEqual(len(self.client.get(self.url()).json()["entries"]), 2)
        with self.assertRaises(HTTPException):
            portfolio._persist(self.db, key, None, {"entries": []})
        self.assertEqual(len(self.client.get(self.url()).json()["entries"]), 2)

    def test_mission_curriculum_namespaces_and_rejection(self):
        for language, lesson, key in [("en", 1, "identity-card"), ("en", 51, "past-event"),
                                      ("en", 86, "request-help"), ("de", 18, "request-help"),
                                      ("de", 30, "past-event")]:
            listing = self.client.get(self.url(language=language, lesson=lesson)).json()
            ids = [m["id"] for m in listing["missions"]]
            self.assertIn(f"{language}:{lesson}:{key}", ids)
            self.assertTrue(all(m["language"] == language and m["lesson"] == lesson for m in listing["missions"]))
        for language in ("en", "de"):
            choices = self.client.get(self.url(language=language)).json()["missions"]
            self.assertTrue(all(m["foundation"] for m in choices))
            self.assertFalse(any("past-event" in m["id"] or "request-help" in m["id"] for m in choices))
        for bad in ("de:1:identity-card", "en:2:identity-card", "en:1:past-event", "invented", "x" * 81, 12):
            response = self.client.post(self.url(), json=self.body(mission_id=bad))
            self.assertEqual(response.status_code, 422, response.text)
        self.assertEqual(self.db.query(models.IntegrationSetting).count(), 0)

    def test_mission_and_coaching_survive_reload_without_rewriting_history(self):
        first = self.create(mission_id="en:1:identity-card", text="pencil")
        self.assertEqual(first["mission"]["id"], "en:1:identity-card")
        self.assertEqual(first["mission_evidence"], {"status": "artifact_saved", "version": 1,
                                                    "verified_mastery": False, "xp": 0})
        first_version = first["versions"][0]
        self.assertIn("pencil", first_version["coaching"]["observed_positive"])
        url = self.url(first["id"])
        # Legacy clients omit mission_id on PUT: the persisted personal choice survives.
        revised = self.client.put(url, json=self.body(text="pencil, teacher", expected_version=1))
        self.assertEqual(revised.status_code, 200, revised.text)
        self.assertEqual(revised.json()["versions"][0], first_version)
        self.assertEqual(revised.json()["versions"][1]["mission_id"], first["mission"]["id"])
        self.db.close()
        self.db = self.sessions()
        reloaded = self.client.get(url).json()
        self.assertEqual(reloaded, revised.json())
        self.assertEqual(reloaded["mission_evidence"]["version"], 2)
        self.assertEqual(self.client.put(url, json=self.body(mission_id="en:1:object-label", expected_version=2)).status_code, 409)
        self.assertEqual(self.client.put(url, json=self.body(expected_version=1)).status_code, 409)
        self.assertEqual(self.db.query(models.SkillAttempt).count(), 0)
        self.assertEqual(self.db.query(models.XpTransaction).count(), 0)

    def test_feedback_is_observation_not_audio_or_language_score(self):
        row = practice.LESSONS["en"][7]
        matched = missions.coaching(row, {"text": "I am ready", "type": "dialogue"})
        self.assertIn("«am»", matched["observed_positive"])
        self.assertIn("yangi satr", matched["next_improvement"])
        substring = missions.coaching(row, {"text": "Sammy", "type": "story"})
        self.assertNotIn("«am»", substring["observed_positive"])
        self.assertIn("«am»", substring["next_improvement"])
        audio_only = self.create(text="", type="speaking", audio=self.audio(), mission_id="en:1:identity-card")
        feedback = audio_only["versions"][0]["coaching"]
        self.assertEqual(feedback["basis"], "audio_unassessed")
        self.assertIn("tekshirilmagan", feedback["disclaimer"])
        for value in [matched, substring, feedback]:
            self.assertIsInstance(value["next_improvement"], str)
            self.assertTrue(value["retry"])
            self.assertFalse(value["verified_mastery"])
            self.assertFalse(value["assessed_audio"])
            self.assertFalse({"score", "cefr", "pronunciation", "accuracy"} & value.keys())
        de = missions.coaching(practice.LESSONS["de"][30], {"text": "Ich war dort.", "type": "story"})
        self.assertIn("«war»", de["observed_positive"])

    def test_legacy_projection_does_not_mutate_saved_data(self):
        entry = self.create()
        key, raw, state = portfolio._load(self.db, 1)
        old = state["entries"][0]
        old.pop("mission", None)
        old["versions"][0].pop("coaching", None)
        old["versions"][0].pop("mission_id", None)
        portfolio._persist(self.db, key, raw, state)
        stored = portfolio._load(self.db, 1)[1]
        response = self.client.get(self.url(entry["id"])).json()
        self.assertIsNone(response["mission"])
        self.assertIsNone(response["mission_evidence"])
        self.assertTrue(response["versions"][0]["coaching"]["next_improvement"])
        self.assertEqual(portfolio._load(self.db, 1)[1], stored)
        revised = self.client.put(self.url(entry["id"]), json=self.body(expected_version=1))
        self.assertEqual(revised.status_code, 200, revised.text)
        self.assertEqual(revised.json()["versions"][0], response["versions"][0])
        persisted = json.loads(portfolio._load(self.db, 1)[1])
        self.assertNotIn("coaching", persisted["entries"][0]["versions"][0])

    def test_all_course_lessons_offer_bounded_choices_and_reject_forged_feedback(self):
        for language, rows in practice.BANK.items():
            for row in rows:
                self.assertEqual(row["language"], language)
                offered = missions.choices(language, row)
                self.assertGreaterEqual(len(offered), 2)
                self.assertLessEqual(len(offered), 4)
                self.assertEqual(len({m["id"] for m in offered}), len(offered))
                for mission in offered:
                    self.assertEqual(mission["lesson_title"], row["title"])
                    self.assertLessEqual(len(mission["targets"]), 6)
        for forged in [{"coaching": {"score": 100}}, {"mission": {"id": "en:1:fake"}},
                       {"mission_evidence": {"verified_mastery": True}}]:
            self.assertEqual(self.client.post(self.url(), json=self.body(**forged)).status_code, 422)

    def test_retry_hint_changes_when_observable_suggestion_is_addressed(self):
        url = self.url(lesson=7)
        created = self.client.post(url, json=self.body(type="story", text="Sammy", mission_id="en:7:introduce"))
        self.assertEqual(created.status_code, 201, created.text)
        entry = created.json()
        first = entry["versions"][0]
        self.assertIn("«am»", first["coaching"]["next_improvement"])
        url = self.url(entry["id"], lesson=7)
        revised = self.client.put(url, json=self.body(type="story", text="I am ready.", expected_version=1)).json()
        second = revised["versions"][1]
        self.assertEqual(revised["versions"][0], first)
        self.assertIn("«am»", second["coaching"]["observed_positive"])
        self.assertNotEqual(first["coaching"]["next_improvement"], second["coaching"]["next_improvement"])
        third = self.client.put(url, json=self.body(type="story", text="I am ready at school.", expected_version=2)).json()
        self.assertIn("alohida yangi ish", third["versions"][2]["coaching"]["retry"])
        self.assertEqual(third["versions"][:2], revised["versions"])
        for language in ("en", "de"):
            row = practice.LESSONS[language][1]
            mission = missions.choices(language, row)[0]
            feedback = missions.coaching(row, {"text": mission["targets"][0], "type": "story"}, mission)
            self.assertIn("to‘liq gap shart emas", feedback["next_improvement"])
        audio = missions.coaching(practice.LESSONS["en"][1], {"number": 3, "text": "", "type": "speaking"})
        self.assertIn("alohida yangi ish", audio["retry"])


if __name__ == "__main__":
    unittest.main()
