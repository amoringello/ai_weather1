from weather_tool import get_weather, format_weather_summary
from clothing_tool import suggest_clothing, format_clothing_suggestions


class WeatherAgent:
    """A simple agentic AI that monitors weather and suggests clothing."""

    def __init__(self):
        self.tools = {
            "weather": self.get_weather_tool,
            "clothing": self.clothing_suggestion_tool,
        }

    def _extract_location(self, message):
        """Extract (city, state) from a natural-language message.

        After a preposition ('in' / 'at') takes the next 1-2 words.
        If the last word looks like a US state abbreviation (2 letters), it's
        treated as the state.  Returns (city, state_or_None).

        Fallback: first capitalized token with optional following 2-letter
        state code.
        """
        tokens = message.split()

        def _try_parse(start_idx):
            """Given a starting index, return (city, state) or None."""
            words = []
            for j in range(start_idx, min(start_idx + 3, len(tokens))):
                c = tokens[j].rstrip(",.!?")
                if c:
                    words.append(c)
                else:
                    break

            if not words:
                return None

            state = None
            # If the last word is exactly 2 letters, treat it as a state code
            last = words[-1]
            if len(last) == 2 and last.isalpha():
                state = last
                words = words[:-1]

            if not words:
                return None

            city = " ".join(words)
            return city, state

        # --- Look for a whole-word preposition, then parse next words ---
        for i, tok in enumerate(tokens):
            clean = tok.rstrip(",.!?").lower()
            if clean in ("in", "at"):
                result = _try_parse(i + 1)
                if result:
                    return result

        # --- Fallback: first capitalized word (with optional state code) ---
        for i, token in enumerate(tokens):
            clean = token.rstrip(",.!?")
            if clean and clean[0].isupper():
                words_after = [clean]
                j = i + 1
                while j < len(tokens):
                    nxt = tokens[j].rstrip(",.!?")
                    if len(nxt) == 2 and nxt.isalpha():
                        words_after.append(nxt)
                        j += 1
                        break
                    else:
                        break

                state = None
                if len(words_after) == 2 and len(words_after[1]) == 2:
                    state = words_after[1]
                    city = words_after[0]
                else:
                    city = " ".join(words_after)
                    state = None

                return city, state

        return None, None

    _US_STATES = {
        "AL","AK","AZ","AR","CA","CO","CT","DE","FL","GA",
        "HI","ID","IL","IN","IA","KS","KY","LA","ME","MD",
        "MA","MI","MN","MS","MO","MT","NE","NV","NH","NJ",
        "NM","NY","NC","ND","OH","OK","OR","PA","RI","SC",
        "SD","TN","TX","UT","VT","VA","WA","WV","WI","WY",
    }

    def _build_query(self, city, state):
        """Build the API query string from city and optional state."""
        if state:
            upper_state = state.upper()
            if upper_state in self._US_STATES:
                return f"{city},{upper_state},US"
            return f"{city},{state}"
        return city

    def run(self, message):
        """Main agent loop: extract location, get weather, suggest clothing."""
        city, state = self._extract_location(message)
        query = self._build_query(city, state)

        # Update the user-facing city name (capitalize state code for display)
        display_city = f"{city} {state.upper()}".strip() if state else city

        weather = get_weather(query)
        suggestions = suggest_clothing(weather)
        ws = format_weather_summary(weather)
        cs = format_clothing_suggestions(suggestions)
        return {
            "display_city": display_city,
            "weather_summary": ws,
            "clothing_suggestions": cs,
            "full_recommendation": ws + chr(10) + chr(10) + cs,
        }

    def get_weather_tool(self, message):
        """Tool wrapper for weather fetching."""
        city, state = self._extract_location(message)
        query = self._build_query(city, state)
        w = get_weather(query)
        return {"tool": "weather", "city": query, "result": format_weather_summary(w)}

    def clothing_suggestion_tool(self, weather):
        """Tool wrapper for clothing suggestions."""
        suggestions = suggest_clothing(weather)
        return {"tool": "clothing", "result": format_clothing_suggestions(suggestions)}

    def respond(self, user_message):
        """Parse a natural-language message and execute relevant tools."""
        msg_lower = user_message.lower()

        city, state = self._extract_location(user_message)
        if not city:
            if any(w in msg_lower for w in ["hello", "hi", "hey"]):
                return ("Hello! I can check the weather and suggest what to wear. "
                       "Just tell me a city name, e.g. *What is the weather in San Francisco?*")
            return "I need a city name to check the weather. Try: Weather in Paris or What should I wear in Tokyo?"

        result = self.run(user_message)
        if "weather" in msg_lower or "temperature" in msg_lower:
            return "Hi there! Here is your update for " + result["display_city"] + ":\n\n" + result["full_recommendation"]

        if "wear" in msg_lower or "clothes" in msg_lower or "dress" in msg_lower:
            return "Here are my clothing suggestions for " + result["display_city"] + " based on current weather:\n\n" + result["clothing_suggestions"]

        # Default: show both
        return "Here is your update for " + result["display_city"] + ":\n\n" + result["full_recommendation"]


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python agent.py \"weather in Springfield IL\"")
        print("       python agent.py \"What should I wear in London?\"")
        print()
        print("City + state (e.g. Springfield IL) disambiguates duplicate city names.")
        sys.exit(1)

    agent = WeatherAgent()
    message = " ".join(sys.argv[1:])
    print(agent.respond(message))