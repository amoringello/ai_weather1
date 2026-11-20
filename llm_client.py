"""OpenAI-compatible LLM client used across all agent modules."""
import os
from openai import OpenAI, APIError


class LLMError(Exception):
    """Raised when the LLM API call fails."""


def call_llm(messages, model=None, api_key=None, base_url=None):
    """Call an OpenAI-compatible chat completion API.

    Parameters are read from environment variables by default:
      LLM_BASE_URL  - e.g. "https://api.openai.com/v1" or "http://localhost:11434/v1"
      LLM_API_KEY   - your API key
      LLM_MODEL     - model name (e.g. "gpt-4o-mini")

    Returns the assistant text response, or raises LLMError on failure.
    """
    base_url = base_url or os.environ.get("LLM_BASE_URL", "")
    api_key = api_key or os.environ.get("LLM_API_KEY", "")
    model = model or os.environ.get("LLM_MODEL", "gpt-4o-mini")

    if not base_url or not api_key:
        raise LLMError(
            "LLM is not configured. Set LLM_BASE_URL and LLM_API_KEY in .env."
        )

    client = OpenAI(base_url=base_url, api_key=api_key)

    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.3,
        )
        return response.choices[0].message.content
    except APIError as exc:
        raise LLMError(f"LLM API error ({exc.status_code}): {exc.message}") from exc


# ------------------------------------------------------------------
# .env loading (side-effect on import)
# ------------------------------------------------------------------

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass
