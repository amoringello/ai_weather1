from llm_client import call_llm, LLMError
from weather_tool import get_weather, format_weather_summary

import json
import sys


# US state codes for API disambiguation
_US_STATES = {
    "AL","AK","AZ","AR","CA","CO","CT","DE","FL","GA",
    "HI","ID","IL","IN","IA","KS","KY","LA","ME","MD",
    "MA","MI","MN","MS","MO","MT","NE","NV","NH","NJ",
    "NM","NY","NC","ND","OH","OK","OR","PA","RI","SC",
    "SD","TN","TX","UT","VT","VA","WA","WV","WI","WY",
}


class WeatherAgent:
    """An agentic AI that uses an LLM to parse user input, fetches weather
    via tools, and generates clothing suggestions — all driven by AI."""

    # ------------------------------------------------------------------
    # LLM-powered intent extraction
    # ------------------------------------------------------------------

    _INTENT_SYSTEM = (
        "You are an assistant that extracts structured data from user messages for a "
        "weather-and-clothing service.  Analyze the message and return ONLY a JSON object with:\n"
        "\n"
        '  "intent": one of "greeting", "weather", "clothing", "general"\n'
        '  "city"  : the city name as a string, or null if none mentioned\n'
        '  "state" : uppercase US state code (e.g. "TX") if explicitly provided next to '
        "the city; otherwise null\n"
        "\n"
        "Rules:\n"
        '  - Greetings (hello/hi/hey, etc.) -> intent = "greeting"\n'
        '  - A bare location without any explicit request -> intent = "weather"\n'
        '  - Clothing keywords (wear/clothes/dress/etc.) near a city -> intent = "clothing"\n'
        '  - Everything else with no city -> intent = "general"\n'
        "  - Strip punctuation from the city name\n"
        "  - Return ONLY valid JSON - no markdown, no backticks, no explanation, no thinking block text."
    )

    _INTENT_USER_FMT = (
        'Message: "{user_message}"'
    )

    _RESPONSE_SYSTEM_PROMPT = (
        "You are a helpful weather assistant. Given current conditions, provide "
        "a natural-language summary of the weather AND practical clothing recommendations. "
        "Base your suggestions on temperature, humidity, wind, and conditions. "
        "Finally summarize the suggestion with contextual emoji bullet points relating to each related weather condition. Summary should also include emoji bullet points for the resulting suggested clothing option."
    )

    _RESPONSE_USER_TEMPLATE = (
        "User asked: {user_message}\n\n"
        "Current weather for {city}:\n"
        "  Temperature     : {temp}°C (feels like {feels_like}°C)\n"
        "  Condition       : {condition}\n"
        "  Humidity        : {humidity}%\n"
        "  Wind speed      : {wind} m/s\n"
    )

    # ------------------------------------------------------------------
    # Intent extraction
    # ------------------------------------------------------------------

    def _extract_intent(self, user_message):
        """Ask the LLM to parse the user message and return structured intent."""

        try:
            messages = [
                {"role": "system", "content": self._INTENT_SYSTEM},
                {"role": "user", "content": self._INTENT_USER_FMT.format(user_message=user_message)},
            ]
            response = call_llm(messages)
        except LLMError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            sys.exit(1)

        try:
            data = json.loads(response)
            return {
                "intent": str(data.get("intent", "general")).lower(),
                "city": str(data["city"]) if data.get("city") else None,
                "state": str(data["state"]).upper() if data.get("state") else None,
            }
        except (json.JSONDecodeError, KeyError, TypeError):
            print(f"ERROR: LLM returned invalid JSON. Check model output.\n{response}", file=sys.stderr)
            sys.exit(1)

    # ------------------------------------------------------------------
    # Tool execution
    # ------------------------------------------------------------------

    def _build_query(self, city, state):
        """Build the API query string from city and optional state."""
        if city is None:
            return None
        if state and state.upper() in _US_STATES:
            return f"{city},{state.upper()},US"
        return city

    def _execute_weather_tool(self, city, state):
        """Fetch weather data for a given location."""
        query = self._build_query(city, state)
        if not query:
            return None
        w = get_weather(query)
        display = f"{city} {state.upper()}".strip() if state else city
        return {"weather": w, "summary": format_weather_summary(w), "display_city": display}

    # ------------------------------------------------------------------
    # Main agent loop
    # ------------------------------------------------------------------

    def respond(self, user_message):
        """Parse intent, fetch weather, and let the LLM generate a response."""

        parsed = self._extract_intent(user_message)
        intent = parsed["intent"]
        city = parsed["city"]
        state = parsed["state"]

        # Non-weather intents — no tools needed
        if intent == "greeting":
            return (
                "Hello! I am your weather assistant. I can check the current weather "
                "for any city and suggest what to wear. Just tell me a city name - "
                "e.g. What is the weather in San Francisco?"
            )

        if intent == "general":
            return (
                "I specialize in checking the weather and suggesting clothing. "
                "Try something like Weather in Tokyo or What should I wear in Berlin? "
                "(You can also include a state, e.g. Springfield IL, to disambiguate.)"
            )

        # Fetch real weather data
        weather_result = self._execute_weather_tool(city, state)

        if not weather_result or "weather" not in weather_result:
            return f"I could not find the weather for {city}. Please check the spelling."

        w = weather_result["weather"]

        # Let the LLM generate both a weather summary and clothing suggestions
        llm_prompt = self._RESPONSE_USER_TEMPLATE.format(
            user_message=user_message,
            city=weather_result["display_city"],
            temp=w["temperature_c"],
            feels_like=w["feels_like_c"],
            condition=w["description"],
            humidity=w["humidity"],
            wind=w["wind_speed_ms"],
        )

        try:
            return call_llm([
                {"role": "system", "content": self._RESPONSE_SYSTEM_PROMPT},
                {"role": "user", "content": llm_prompt},
            ])
        except LLMError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print('Usage: python agent.py "weather in Springfield IL"')
        print('       python agent.py "What should I wear in London?"')
        print()
        print("City + state (e.g. Springfield IL) disambiguates duplicate city names.")
        sys.exit(1)

    agent = WeatherAgent()
    message = " ".join(sys.argv[1:])
    print(agent.respond(message))
