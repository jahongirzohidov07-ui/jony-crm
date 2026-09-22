# Jony Teacher Speaking

Speaking uses Groq `openai/gpt-oss-20b` with browser speech recognition and speech synthesis. Other AI features retain their existing providers. No automatic fallback to OpenAI or Gemini is made by Speaking.

1. Create a Groq account on the Free plan and create an API key at https://console.groq.com/keys . Do not upgrade or enable paid billing for a zero-cost setup.
2. Add `GROQ_API_KEY` to the JonyOS Vercel project's server-side production environment. Never use a VITE_ variable or commit the key.
3. Deploy these changes after setting the key.
4. Log in as a student, open Jony Teacher, select a topic, allow the microphone, and complete at least two spoken turns. Test on the actual phones used in class.

Free usage is limited at organization level (requests and tokens); the provider console is authoritative. A 429 pauses the conversation and never triggers paid fallback. A paid Groq account can charge for the same API, so the API code alone cannot guarantee a zero bill.

Voice support depends on the browser/device. Speech recognition may use the browser vendor's online service; recognized text is sent to Groq. This is turn-by-turn voice practice, not pronunciation scoring or a full-duplex audio model. API keys stay on the server.

Checks: `python api/test_speaking_ai.py`, `python api/test_speaking_partner.py`, `node node_modules/typescript/bin/tsc -p tsconfig.app.json --noEmit --incremental false`.
