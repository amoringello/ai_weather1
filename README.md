# Weather & Wear — AI Assistant

A smart weather checker that suggests what to wear, powered by an LLM.

## Quick Start

### Web Dashboard (recommended)

```bash
cd ai_agent/
python3 server.py --debug
# → open http://localhost:8080 in your browser
```

### CLI

```bash
python3 agent.py "What is the weather in Tokyo?"
python3 agent.py "What should I wear in Springfield IL?"
```

## Files

| File                  | Purpose                                    |
|-----------------------|--------------------------------------------|
| `agent.py`            | Core agent class — LLM intent parsing + response generation |
| `server.py`           | Flask web server with dashboard UI         |
| `templates/index.html`| Modern dark-mode dashboard (HTML/CSS/JS)   |
| `weather_tool.py`     | OpenWeatherMap API client                  |
| `llm_client.py`       | OpenAI-compatible LLM client               |

## Configuration

Copy `.env_sample` to `.env` and fill in your keys:

```bash
cp .env_sample .env
```

| Variable          | Description                                      |
|-------------------|--------------------------------------------------|
| `OPENWEATHER_API_KEY` | Your OpenWeatherMap API key                    |
| `LLM_BASE_URL`      | LLM endpoint (e.g. `https://api.openai.com/v1`) |
| `LLM_API_KEY`       | Your LLM API key                                 |
| `LLM_MODEL`         | Model name (default: `gpt-4o-mini`)              |

## Web Server Options

```bash
python3 server.py                    # default host 0.0.0.0, port 8080
python3 server.py --port 8080        # custom port
python3 server.py --host localhost   # bind to localhost only
python3 server.py --debug            # enable Flask debug mode

# Or via environment variables:
FLASK_HOST=0.0.0.0 FLASK_PORT=8080 python3 server.py
```
