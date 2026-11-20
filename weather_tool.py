import json
import os
import sys
import urllib.request


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

    url = f"{base_url.rstrip('/')}/chat/completions"
    payload = json.dumps({
        "model": model,
        "messages": messages,
        "temperature": 0.3,
    }).encode()

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }

    req = urllib.request.Request(url, data=payload, headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=30) as resp:
        body = json.loads(resp.read().decode())
        return body["choices"][0]["message"]["content"]


try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

API_KEY = os.environ.get("OPENWEATHER_API_KEY")


class WeatherError(Exception):
    """Raised when the weather API call fails."""


def get_weather(city):
    """Fetch current weather via the OpenWeatherMap API.

    If the API returns an error or the city is not found, raises a
    WeatherError - no mock data fallback.
    """
    if not API_KEY:
        raise WeatherError(
            "OPENWEATHER_API_KEY not set.\n"
            "Put it in .env or export it as an environment variable."
        )

    from urllib import parse, error
    from datetime import datetime

    query = parse.urlencode({"q": city, "appid": API_KEY, "units": "metric"})
    url = "https://api.openweathermap.org/data/2.5/weather?" + query

    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
    except error.HTTPError as exc:
        raise WeatherError(
            f"API returned {exc.code} for '{city}' - city not found or bad key."
        ) from exc
    except error.URLError as exc:
        raise WeatherError(f"Could not reach weather API ({exc.reason}).") from exc

    return {
        "city": data["name"],
        "country": data["sys"]["country"],
        "temperature_c": data["main"]["temp"],
        "feels_like_c": data["main"]["feels_like"],
        "humidity": data["main"]["humidity"],
        "description": data["weather"][0]["description"].capitalize(),
        "wind_speed_ms": data["wind"]["speed"],
        "timestamp": datetime.now().isoformat(),
    }


def format_weather_summary(weather):
    """Convert weather dict into a readable summary string."""
    lines = [
        f"Current weather in {weather['city']}, {weather['country']}:",
        f"   Temperature : {weather['temperature_c']}C (feels like {weather['feels_like_c']}C)",
        f"   Condition   : {weather['description']}",
        f"   Humidity    : {weather['humidity']}%",
        f"   Wind speed  : {weather['wind_speed_ms']} m/s",
    ]
    return "\n".join(lines)


if __name__ == "__main__":
    city = sys.argv[1] if len(sys.argv) > 1 else None
    if not city:
        print("Usage: python weather_tool.py <city> [state]", file=sys.stderr)
        sys.exit(1)

    args = sys.argv[1:]
    if len(args) >= 2 and not args[0].endswith(","):
        location = f"{args[0]},{args[1]}"
    elif "," in args[0]:
        location = args[0].replace(",", "").strip() + " " + (args[1].strip() if len(args) >= 2 else "")
    else:
        location = args[0]

    try:
        weather = get_weather(location)
        print(format_weather_summary(weather))
    except WeatherError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
