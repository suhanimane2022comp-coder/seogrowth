import json
from groq import Groq
from core.config import settings

client = Groq(api_key=settings.GROQ_API_KEY)

DEFAULT_MODEL = "llama-3.1-8b-instant"


def ai_json(prompt: str, temperature: float = 0.4, max_tokens: int = 2000, model: str = DEFAULT_MODEL) -> dict:
    """Call Groq chat completion and parse JSON response, with fallbacks."""
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        raw = response.choices[0].message.content.strip()
    except Exception as e:
        print(f"[ai_client] Groq call failed: {e}")
        return {}
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()
    try:
        return json.loads(raw)
    except Exception:
        # try to find the first {...} or [...] block
        start_obj, start_arr = raw.find("{"), raw.find("[")
        candidates = [s for s in (start_obj, start_arr) if s != -1]
        if candidates:
            start = min(candidates)
            end = max(raw.rfind("}"), raw.rfind("]"))
            if end > start:
                try:
                    return json.loads(raw[start:end + 1])
                except Exception:
                    pass
        return {}
