"""Flask web server for the Weather and Wear AI agent."""
from __future__ import annotations

import json, os, sys
from datetime import datetime

_ai_pkg = os.path.dirname(os.path.abspath(__file__))
if _ai_pkg not in sys.path:
    sys.path.insert(0, _ai_pkg)

from agent import WeatherAgent
from weather_tool import get_weather
from llm_client import call_llm

_agent = WeatherAgent()


def _run_agent(user_message):
    """Run the full agent pipeline. Returns a dict consumable by CLI or web."""
    try:
        parsed = _agent._extract_intent(user_message)
    except Exception as exc:
        return {'type': 'error',
                'response': f'Intent extraction failed: {exc}. Please try again later.'}

    intent = parsed.get('intent', 'general')
    city = parsed.get('city')
    state = parsed.get('state')

    if intent == 'greeting':
        return {'type': 'text', 'response': (
            'Hello! I am your weather assistant. I can check the current weather '
            'for any city and suggest what to wear. Just tell me a city name - '
            'e.g. What is the weather in San Francisco?')}

    if intent == 'general':
        return {'type': 'text', 'response': (
            'I specialize in checking the weather and suggesting clothing. '
            'Try something like Weather in Tokyo or What should I wear in Berlin? '
            '(You can also include a state, e.g. Springfield IL, to disambiguate.)')}

    query = _agent._build_query(city, state)
    if not query:
        return {'type': 'error',
                'response': f'I could not find the weather for {city}. Please check the spelling.'}

    try:
        raw = get_weather(query)
    except Exception as exc:
        return {'type': 'error', 'response': str(exc)}

    display_city = f'{city} {state.upper()}'.strip() if state else city

    llm_prompt = WeatherAgent._RESPONSE_USER_TEMPLATE.format(
        user_message=user_message, city=display_city,
        temp=raw['temperature_c'], feels_like=raw['feels_like_c'],
        condition=raw['description'], humidity=raw['humidity'],
        wind=raw['wind_speed_ms'])

    try:
        response = call_llm([
            {'role': 'system', 'content': WeatherAgent._RESPONSE_SYSTEM_PROMPT},
            {'role': 'user', 'content': llm_prompt}])
        if not response or not response.strip():
            return {'type': 'error',
                    'response': 'The AI returned an empty response. Please try again.',
                    'weather': _weather_payload(raw, display_city)}
    except Exception as exc:
        return {'type': 'error', 'response': f'LLM error: {exc}',
                'weather': _weather_payload(raw, display_city)}

    return {'type': 'full', 'response': response,
            'weather': _weather_payload(raw, display_city)}


def _weather_payload(raw, display_city):
    """Convert raw weather dict into the shape the frontend expects."""
    code = 800
    try:
        code = raw.get('weather', [{}])[0].get('id', 800)
    except (IndexError, KeyError):
        pass

    return {
        'city': raw['city'], 'country': raw['country'],
        'temperature_c': round(raw['temperature_c'], 1),
        'feels_like_c': round(raw['feels_like_c'], 1),
        'humidity': raw['humidity'],
        'description': raw['description'],
        'wind_speed_ms': raw['wind_speed_ms'],
        'timestamp': datetime.now().isoformat()}

# ------------------------------------------------------------------
# HTML template loaded from templates/ directory
# ------------------------------------------------------------------


from flask import Flask, request, jsonify, render_template  # noqa: E402

app = Flask(__name__, template_folder='templates')


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/query", methods=["POST"])
def api_query():
    data = request.get_json(silent=True) or {}
    user_message = data.get("query", "").strip()
    if not user_message:
        return jsonify({
            "error": "Please enter a city name (e.g. Tokyo or Springfield IL)."}), 400

    result = _run_agent(user_message)
    print(f"DEBUG api_query: type={result.get('type')}, response_len={len(str(result.get('response','')))}, weather_keys={list(result.get('weather',{}).keys())}", flush=True)

    # Plain text response (greeting / help)
    if result["type"] == "text":
        return jsonify({"response": result["response"]})

    # Error from weather fetch or LLM
    if result["type"] == "error":
        return jsonify({"error": result["response"]}), 500

    # Successful weather + clothing suggestion
    return jsonify({
        "response": result["response"],
        "weather": result["weather"],
        "display_city": result["weather"]["city"],
    })


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Weather & Wear web server")
    parser.add_argument("--host", default=os.environ.get("FLASK_HOST", "0.0.0.0"))
    parser.add_argument("--port", type=int, default=int(os.environ.get("FLASK_PORT", "8080")))
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args()

    print(f"  Weather & Wear running at http://{args.host}:{args.port}")
    app.run(host=args.host, port=args.port, debug=args.debug)
