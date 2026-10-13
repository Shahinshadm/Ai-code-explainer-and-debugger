from __future__ import annotations

import os
from typing import Any

import requests
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request

load_dotenv()
app = Flask(__name__)


def model_response(code: str, task: str, language: str) -> str | None:
    """Call an OpenAI-compatible chat completions endpoint when configured."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None
    base = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    prompt = (
        f"You are a careful {task} assistant. Analyze this {language} code. Be concise, "
        "distinguish confirmed bugs from possibilities, and use markdown.\n\n"
        f"```{language}\n{code}\n```"
    )
    try:
        response = requests.post(
            f"{base}/chat/completions",
            headers={"Authorization": f"Bearer {api_key}"},
            json={"model": os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                  "messages": [{"role": "user", "content": prompt}], "temperature": 0.2},
            timeout=45,
        )
        response.raise_for_status()
        data: dict[str, Any] = response.json()
        return data["choices"][0]["message"]["content"]
    except (requests.RequestException, KeyError, IndexError, TypeError) as exc:
        raise RuntimeError(f"AI service request failed: {exc}") from exc


def demo_analysis(code: str, task: str) -> str:
    lines = code.splitlines()
    if task == "debug":
        hints = []
        if "except:" in code or "except Exception" in code:
            hints.append("Broad exception handling can hide the original failure; catch a specific exception.")
        if "range(len(" in code:
            hints.append("Check index boundaries; the last valid index is `len(sequence) - 1`.")
        if not hints:
            hints.append("A text-only scan cannot confirm a bug. Try representative inputs and inspect the full traceback.")
        return "### Debugging notes\n\n" + "\n".join(f"- {hint}" for hint in hints) + "\n\nDemo scan only. Configure an AI API key for deeper analysis."
    preview = "\n".join(f"{i:>3}: {line}" for i, line in enumerate(lines[:12], 1))
    if len(lines) > 12:
        preview += f"\n… ({len(lines) - 12} more lines)"
    return (
        f"### Code overview\n\nThe snippet contains **{len(lines)} line(s)**. Demo mode provides a structural preview, "
        "not a full explanation of program behavior. Configure an AI API key for line-by-line analysis.\n\n"
        f"### Numbered preview\n\n```text\n{preview}\n```"
    )


@app.get("/")
def home():
    return render_template("index.html")


@app.post("/api/analyze")
def analyze():
    payload = request.get_json(silent=True) or {}
    code = str(payload.get("code", "")).strip()
    task = str(payload.get("task", "explain")).lower()
    language = str(payload.get("language", "python"))[:40]
    if not code:
        return jsonify(error="Paste some code to get started."), 400
    if task not in {"explain", "debug"}:
        return jsonify(error="Choose explain or debug."), 400
    try:
        result = model_response(code, task, language)
        if result is None:
            result = demo_analysis(code, task)
        return jsonify(result=result, mode="ai" if os.getenv("OPENAI_API_KEY") else "demo")
    except RuntimeError as exc:
        return jsonify(error=str(exc)), 502


if __name__ == "__main__":
    app.run(debug=os.getenv("FLASK_DEBUG", "false").lower() == "true")
