"""Dedicated Speaking provider: no automatic paid-provider fallback."""
import os
import httpx


def speaking_reply(system, messages):
    key = os.getenv("GROQ_API_KEY", "").strip()
    if not key:
        raise RuntimeError("no-key")
    body = {
        "model": "openai/gpt-oss-20b",
        "reasoning_effort": "low",
        "include_reasoning": False,
        "max_completion_tokens": 1024,
        "temperature": 0.7,
        "messages": [{"role": "system", "content": system}] + [
            {"role": "assistant" if m["role"] == "teacher" else "user",
             "content": m["text"]} for m in messages],
    }
    try:
        r = httpx.post("https://api.groq.com/openai/v1/chat/completions",
                       headers={"Authorization": f"Bearer {key}"},
                       json=body, timeout=18)
    except httpx.RequestError:
        raise LookupError("Speaking provider unavailable") from None
    if r.status_code == 429:
        raise TimeoutError("Speaking provider quota exceeded")
    if r.status_code != 200:
        # Never persist provider response bodies: they can echo student data.
        raise LookupError(f"Speaking provider HTTP {r.status_code}")
    try:
        choice = r.json()["choices"][0]
        reply = choice["message"]["content"]
        if not isinstance(reply, str) or not reply.strip():
            raise ValueError()
        if choice.get("finish_reason") != "stop":
            raise ValueError()
    except (KeyError, IndexError, TypeError, ValueError):
        raise LookupError("Speaking provider returned no complete answer") from None
    return reply.strip()
