# AI Code Explainer & Debugger

A Flask web app for code explanations and debugging reviews. It has a no-key demo mode and optionally uses an OpenAI-compatible chat completions endpoint.

## Setup

Python 3.10+ is recommended. A `.venv` virtual environment is included.

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
python app.py
```

Open http://127.0.0.1:5000. Add an API key in `.env` to enable AI analysis. `OPENAI_BASE_URL` and `OPENAI_MODEL` can point to a compatible service. Keep `.env` private; submitted code is sent to that service when AI mode is enabled.

## API

`POST /api/analyze` accepts `{ "code": "...", "task": "explain|debug", "language": "python" }` and returns a `result` and `mode`.
