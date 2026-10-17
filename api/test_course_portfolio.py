"""Run: python api/test_course_portfolio.py (isolated SQLite, no AI/network)."""
import base64
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


if __name__ == "__main__":
    unittest.main()
