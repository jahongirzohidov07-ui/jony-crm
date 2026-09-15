"""Writing provider payload and persisted progress regressions; no live services."""
import os
import json
import unittest
from types import SimpleNamespace
from unittest.mock import patch

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

import httpx
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
import models
import student_app as app


class WritingRegression(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:")
        models.SkillAttempt.__table__.create(self.engine)
        self.db = Session(self.engine)
        self.env = patch.dict(os.environ, {
            "OPENAI_API_KEY": "test", "GEMINI_API_KEY": "",
            "JonyTeacher": "", "JONYTEACHER": ""})
        self.env.start()

    def tearDown(self):
        self.env.stop()
        self.db.close()
        self.engine.dispose()

    def test_openai_message_formats(self):
        response = httpx.Response(200, request=httpx.Request("POST", "https://test"),
            json={"choices": [{"message": {"content": "DARAJA: B1"}}]})
        with patch("httpx.post", return_value=response) as post:
            result = app._ai_reply("system", [
                {"role": "teacher", "text": "hello"},
                {"role": "user", "content": "essay"}], max_tokens=800)
        self.assertEqual(result, "DARAJA: B1")
        body = post.call_args.kwargs["json"]
        self.assertEqual(body["messages"][-1], {"role": "user", "content": "essay"})
        self.assertEqual(body["messages"][1]["role"], "assistant")
        self.assertEqual(body["max_tokens"], 800)

    def test_gemini_message_formats(self):
        response = httpx.Response(200, request=httpx.Request("POST", "https://test"),
            json={"candidates": [{"content": {"parts": [{"text": "DARAJA: B1"}]}}]})
        with patch.dict(os.environ, {"OPENAI_API_KEY": "", "GEMINI_API_KEY": "test"}), \
             patch.object(app._ai_reply, "_avail", ["gemini-test"], create=True), \
             patch("httpx.post", return_value=response) as post:
            app._ai_reply("system", [{"role": "user", "content": "essay"}], max_tokens=800)
        body = post.call_args.kwargs["json"]
        self.assertEqual(body["contents"][0]["parts"], [{"text": "essay"}])
        self.assertEqual(body["generationConfig"]["maxOutputTokens"], 800)

    def test_progress_preserves_low_scores_and_isolates_students(self):
        self.assertEqual(app._writing_progress(self.db, 1)["submitted"], 0)
        for sid, ref, answer in [
            (1, "cwrite:a:1.1", '{"score": 100}'),
            (1, "cwrite:a:1.1", json.dumps({"score": 40, "expert_status": "unavailable"})),
            (2, "cwrite:private:2", '{"score": 99}'),
            (1, "cwdrill:1", '{"score": 99}')]:
            self.db.add(models.SkillAttempt(student_id=sid, skill="writing", ref=ref, answer=answer))
        self.db.commit()
        result = app._writing_progress(self.db, 1)
        self.assertEqual(result, {"submitted": 1, "latest": {
            "format_score": 40, "expert_status": "unavailable"}})
        self.assertEqual(app._writing_progress(self.db, 2)["latest"]["expert_status"], "unknown")

    def test_submission_saves_expert_success_and_failure(self):
        task = app._cwt.PART1[0]
        payload = {"task_id": task["id"], "part": "1.1", "text": task["model11"]}
        response = httpx.Response(200, request=httpx.Request("POST", "https://test"),
            json={"choices": [{"message": {"content": "DARAJA: B1"}}]})
        with patch.object(app, "_me", return_value=SimpleNamespace(id=1)), \
             patch.object(app, "award_xp", return_value={"ok": True}), \
             patch("httpx.post", return_value=response):
            result = app.cw_submit(payload, self.db, None)
        self.assertEqual(result["ai"], "DARAJA: B1")
        self.assertEqual(app._writing_progress(self.db, 1)["latest"]["expert_status"], "available")
        with patch.object(app, "_me", return_value=SimpleNamespace(id=1)), \
             patch.object(app, "award_xp", return_value={"ok": False}), \
             patch("httpx.post", side_effect=RuntimeError("secret-provider-detail")):
            result = app.cw_submit(payload, self.db, None)
        self.assertEqual(result["xp"], 0)
        self.assertNotIn("secret-provider-detail", result["ai_error"])
        self.assertEqual(app._writing_progress(self.db, 1)["latest"]["expert_status"], "unavailable")


if __name__ == "__main__":
    unittest.main()
