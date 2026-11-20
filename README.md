# Weather + Clothing Suggestion Agent

A simple agentic AI that monitors weather and suggests what to wear.

## Files

| File             | Purpose                                   |
|------------------|-------------------------------------------|
| `agent.py`       | Main agent class with natural language parsing |
| `weather_tool.py`| Fetches weather (API or mock data)        |
| `clothing_tool.py`| Suggests clothing based on conditions    |

## Usage

```bash
# Run the built-in demo
python3 agent.py

# Natural language interaction
python3 agent.py "What is the weather in Paris?"
python3 agent.py "What should I wear in Tokyo?"
```

## How It Works

1. **Agent** receives a user message (natural language).
2. It extracts a **city name** from the message.
3. The **weather tool** fetches current conditions for that city (uses mock data by default; add an OpenWeatherMap API key to use real data).
4. The **clothing tool** analyzes temperature, humidity, wind, and conditions to generate personalized outfit suggestions.

## Adding Real Weather Data

```python
agent = WeatherAgent(api_key="your-openweathermap-key")
result = agent.run("San Francisco")
```
