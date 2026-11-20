from weather_tool import get_weather, format_weather_summary, call_llm, LLMError
from clothing_tool import suggest_clothing, format_clothing_suggestions

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

    def __init__(self):
        self.tools = {
            "weather": self._execute_weather_tool,
            "clothing": self._execute_clothing_tool,
        }

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
        "  - Greetings (hello/hi/hey, etc.) -> intent = \"greeting\"\n"
        "  - A bare location without any explicit request -> intent = \"weather\"\n"
        "  - Clothing keywords (wear/clothes/dress/etc.) near a city -> intent = \"clothing\"\n"
        "  - Everything else with no city -> intent = \"general\"\n"
        '  - Strip punctuation from the city name\n'
        "  - Return ONLY valid JSON - no markdown, no backticks, no explanation."
    )

    _INTENT_USER_FMT = (
        'Message: "{user_message}"'
    )

    _RESPONSE_PROMPT_TEMPLATE = (
        "The user asked: \"{user_message}\"\n\n"
        "Current weather data:\n{weather_summary}\n\n"
        "Your task:\n"
        "  - If intent was a greeting, respond warmly and briefly describe your abilities.\n"
        "  - If intent was general (no city), explain what you can do with examples.\n"
        "  - If intent was weather or clothing, provide a helpful natural-language\n"
        "    summary of the weather AND practical clothing recommendations based on\n"
        "    temperature, humidity, wind, and conditions.  Sound like a caring friend,\n"
        "    not a robot."
    )

    def _extract_intent(self, user_message):
        """Ask the LLM to parse the user message and return structured intent."""
        import json

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
            print("ERROR: LLM returned invalid JSON. Check model output.", file=sys.stderr)
            sys.exit(1)

    # ------------------------------------------------------------------
    # Tool execution helpers
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
        return {
            "query": query,
            "weather": w,
            "summary": format_weather_summary(w),
            "display_city": f"{city} {state.upper()}".strip() if state else city,
        }

    def _execute_clothing_tool(self, weather_data):
        """Generate clothing suggestions from weather data."""
        suggestions = suggest_clothing(weather_data)
        return format_clothing_suggestions(suggestions)

    # ------------------------------------------------------------------
    # Main agent loop
    # ------------------------------------------------------------------

    def respond(self, user_message):
        """Parse a natural-language message using AI, execute tools, and reply."""

        # Step 1: LLM parses the intent
        try:
            parsed = self._extract_intent(user_message)
        except LLMError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            sys.exit(1)

        intent = parsed["intent"]
        city = parsed["city"]
        state = parsed["state"]

        # Greeting or general - respond without tools
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

        # Step 2: Execute tools based on intent
        weather_result = self._execute_weather_tool(city, state)

        if not weather_result or "weather" not in weather_result:
            return f"I could not find the weather for {city}. Please check the spelling."

        weather_data = weather_result["weather"]
        summary = weather_result["summary"]

        clothing_text = self._execute_clothing_tool(weather_data)

        # Step 3: If only clothing was requested, skip full summary
        if intent == "clothing":
            return (
                f"Here are my clothing suggestions for {weather_result['display_city']} "
                f"based on current conditions:\n\n{clothing_text}"
            )

        # Step 4: Let the LLM craft a natural-language response using real weather data
        llm_prompt = self._RESPONSE_PROMPT_TEMPLATE.format(
            user_message=user_message,
            weather_summary=summary + "\n\nClothing suggestions:\n" + clothing_text,
        )

        try:
            llm_response = call_llm([{"role": "user", "content": llm_prompt}])
        except LLMError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            sys.exit(1)

        if llm_response:
            return llm_response

        # Final fallback - hand-crafted response
        return (
            f"Hi there! Here is your update for {weather_result['display_city']}:\n\n"
            + summary + "\n\n" + clothing_text
        )


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python agent.py \"weather in Springfield IL\"")
        print("       python agent.py \"What should I wear in London?\"")
        print()
        print("City + state (e.g. Springfield IL) disambiguates duplicate city names.")
        sys.exit(1)

    agent = WeatherAgent()
    message = " ".join(sys.argv[1:])
    print(agent.respond(message))
