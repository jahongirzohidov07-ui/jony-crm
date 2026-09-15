"""Defensive handling of Gemini text replies (including thinking models)."""
def generation_config(model, max_tokens):
    config = {"maxOutputTokens": max(2048, max_tokens), "temperature": 0.7}
    if model.startswith("gemini-2.5-flash"):
        config["thinkingConfig"] = {"thinkingBudget": 0}
    elif model.startswith("gemini-3") and "flash" in model:
        config["thinkingConfig"] = {"thinkingLevel": "low"}
    return config


def response_text(data):
    candidates = data.get("candidates") or []
    for candidate in candidates:
        parts = (candidate.get("content") or {}).get("parts") or []
        text = "".join(p.get("text", "") for p in parts if not p.get("thought") and isinstance(p.get("text"), str)).strip()
        if text:
            return text
    reason = candidates[0].get("finishReason", "EMPTY") if candidates else data.get("promptFeedback", {}).get("blockReason", "EMPTY")
    raise ValueError(f"Gemini empty reply: {reason}")
