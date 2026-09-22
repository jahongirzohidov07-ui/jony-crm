import os
import unittest
from unittest.mock import patch
import httpx
from speaking_ai import speaking_reply


class SpeakingProviderTest(unittest.TestCase):
    def response(self, status=200, content="Hello! What do you enjoy?", finish="stop"):
        return httpx.Response(status, json={"choices": [{"message": {"content": content}, "finish_reason": finish}]})

    @patch.dict(os.environ, {"GROQ_API_KEY": "test-only", "OPENAI_API_KEY": "must-not-use"}, clear=True)
    def test_provider_and_roles(self):
        with patch("speaking_ai.httpx.post", return_value=self.response()) as post:
            self.assertIn("Hello", speaking_reply("tutor", [{"role": "teacher", "text": "Hi"}, {"role": "student", "text": "Hello"}]))
            self.assertEqual(post.call_count, 1)
            self.assertEqual(post.call_args.args[0], "https://api.groq.com/openai/v1/chat/completions")
            body = post.call_args.kwargs["json"]
            self.assertEqual([m["role"] for m in body["messages"]], ["system", "assistant", "user"])
            self.assertFalse(body["include_reasoning"])

    @patch.dict(os.environ, {"OPENAI_API_KEY": "must-not-use"}, clear=True)
    def test_missing_key_never_calls_paid_service(self):
        with patch("speaking_ai.httpx.post") as post:
            with self.assertRaises(RuntimeError):
                speaking_reply("tutor", [])
            post.assert_not_called()

    @patch.dict(os.environ, {"GROQ_API_KEY": "test-only"}, clear=True)
    def test_failures_do_not_fallback(self):
        for response, error in [(self.response(429), TimeoutError), (self.response(401), LookupError), (self.response(500), LookupError), (self.response(content=""), LookupError), (self.response(finish="length"), LookupError)]:
            with patch("speaking_ai.httpx.post", return_value=response) as post:
                with self.assertRaises(error):
                    speaking_reply("tutor", [])
                self.assertEqual(post.call_count, 1)


if __name__ == "__main__":
    unittest.main()
