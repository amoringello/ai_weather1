import json
import os
import sys
import urllib.parse
import urllib.request
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.environ.get("OPENWEATHER_API_KEY")


def get_weather(city: str) -> dict:
    """Fetch current weather via the OpenWeatherMap API.

    The API key is loaded automatically from the ``.env`` file (variable
    ``OPENWEATHER_API_KEY``).  If the API returns an error or the city is
    not found, prints a message to stderr and exits with status 1 -- no
    mock data fallback.
    """
    if not API_KEY:
        print(
            "ERROR: OPENWEATHER_API_KEY not set.\n"
            "Put it in .env or export it as an environment variable.",
            file=sys.stderr,
        )
        sys.exit(1)

    query = urllib.parse.urlencode({
        "q": city,
        "appid": API_KEY,
        "units": "metric",
    })
    url = "https://api.openweathermap.org/data/2.5/weather?" + query

    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            data = json.loads(resp.read().decode())
    except urllib.error.HTTPError as exc:
        print(f"ERROR: API returned {exc.code} for '{city}' — city not found or bad key.", file=sys.stderr)
        sys.exit(1)
    except urllib.error.URLError as exc:
        print(f"ERROR: Could not reach weather API ({exc.reason}).", file=sys.stderr)
        sys.exit(1)

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


def format_weather_summary(weather: dict) -> str:
    """Convert weather dict into a readable summary string."""
    return (
        f"🌤  Current weather in {weather['city']}, {weather['country']}:\n"
        f"   Temperature : {weather['temperature_c']}°C (feels like {weather['feels_like_c']}°C)\n"
        f"   Condition   : {weather['description']}\n"
        f"   Humidity    : {weather['humidity']}%\n"
        f"   Wind speed  : {weather['wind_speed_ms']} m/s"
    )


if __name__ == "__main__":
    city = sys.argv[1] if len(sys.argv) > 1 else None
    if not city:
        print("Usage: python weather_tool.py <city> [state]", file=sys.stderr)
        sys.exit(1)

    # Allow "City ST" or "City,ST" or "City, ST" on the command line
    args = sys.argv[1:]
    if len(args) >= 2 and not args[0].endswith(","):
        location = f"{args[0]},{args[1]}"
    elif "," in args[0]:
        location = args[0].replace(",", "").strip() + " " + (args[1].strip() if len(args) >= 2 else "")
    else:
        location = args[0]

    weather = get_weather(location)
    print(format_weather_summary(weather))
