"""FastAPI web application exposing web analyzer API + UI."""

from __future__ import annotations

import time
from typing import Any, Dict, Literal

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from .analyzer import run_basic_analysis, run_full_audit
from .url_safety import validate_public_url

APP_TITLE = "Web Analyzer API"
APP_VERSION = "2.2.0"

INDEX_HTML = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Web Analyzer</title>
  <style>
    :root {
      --bg: #f4f7fb;
      --surface: #ffffff;
      --text: #102332;
      --muted: #587084;
      --brand: #0f766e;
      --brand-strong: #0a5b56;
      --ok: #0c7a43;
      --warn: #b76e00;
      --bad: #b42318;
      --line: #dbe5ef;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: "Segoe UI", Tahoma, Geneva, Verdana, sans-serif;
      background: radial-gradient(circle at 20% 0%, #eaf5f2 0%, var(--bg) 55%);
      color: var(--text);
    }
    .wrap {
      max-width: 980px;
      margin: 0 auto;
      padding: 28px 18px 48px;
    }
    .hero {
      margin-bottom: 22px;
    }
    .hero h1 {
      margin: 0 0 8px;
      font-size: 30px;
      line-height: 1.1;
      letter-spacing: 0.3px;
    }
    .hero p {
      margin: 0;
      color: var(--muted);
      font-size: 15px;
    }
    .panel {
      background: var(--surface);
      border: 1px solid var(--line);
      border-radius: 14px;
      padding: 18px;
      box-shadow: 0 8px 24px rgba(16, 35, 50, 0.05);
    }
    .row {
      display: grid;
      grid-template-columns: 1fr;
      gap: 12px;
      margin-bottom: 12px;
    }
    @media (min-width: 860px) {
      .row.two { grid-template-columns: 2fr 1fr; }
      .row.three { grid-template-columns: repeat(3, 1fr); }
    }
    label {
      display: block;
      margin-bottom: 6px;
      font-size: 13px;
      color: var(--muted);
      font-weight: 600;
    }
    input[type="text"],
    input[type="number"],
    select,
    textarea {
      width: 100%;
      border: 1px solid var(--line);
      background: #fff;
      color: var(--text);
      border-radius: 10px;
      padding: 11px 12px;
      font-size: 14px;
      outline: none;
    }
    input:focus,
    select:focus,
    textarea:focus {
      border-color: var(--brand);
      box-shadow: 0 0 0 3px rgba(15, 118, 110, 0.12);
    }
    .check {
      display: flex;
      gap: 8px;
      align-items: center;
      padding-top: 26px;
      color: var(--muted);
      font-size: 14px;
    }
    button {
      background: linear-gradient(135deg, var(--brand), var(--brand-strong));
      color: #fff;
      border: none;
      border-radius: 10px;
      padding: 11px 16px;
      font-size: 14px;
      font-weight: 700;
      cursor: pointer;
      transition: transform 0.12s ease, opacity 0.12s ease;
    }
    button:disabled {
      opacity: 0.65;
      cursor: wait;
    }
    button:hover:not(:disabled) {
      transform: translateY(-1px);
    }
    .status {
      min-height: 22px;
      margin-top: 10px;
      color: var(--muted);
      font-size: 14px;
    }
    .result {
      margin-top: 20px;
      display: none;
    }
    .overall {
      margin: 14px 0;
      padding: 14px;
      border-radius: 12px;
      background: #edf8f6;
      border: 1px solid #cfeee8;
      font-size: 16px;
      font-weight: 700;
    }
    .score-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
      gap: 10px;
      margin: 12px 0 14px;
    }
    .score {
      border: 1px solid var(--line);
      border-radius: 10px;
      padding: 10px;
      background: #fcfdff;
    }
    .score .label {
      font-size: 12px;
      color: var(--muted);
      margin-bottom: 4px;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      font-weight: 700;
    }
    .score .value {
      font-size: 22px;
      font-weight: 800;
    }
    .raw {
      width: 100%;
      min-height: 260px;
      font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
      font-size: 12px;
      line-height: 1.45;
      white-space: pre;
      resize: vertical;
    }
    .badge {
      display: inline-block;
      border-radius: 999px;
      padding: 3px 8px;
      font-size: 12px;
      font-weight: 700;
      margin-left: 8px;
    }
    .badge.good { background: #e8f7ef; color: var(--ok); }
    .badge.mid { background: #fff7e8; color: var(--warn); }
    .badge.bad { background: #fdecec; color: var(--bad); }
  </style>
</head>
<body>
  <main class="wrap">
    <section class="hero">
      <h1>Web Analyzer</h1>
      <p>Run quick quality audits for performance, security, SEO and accessibility.</p>
    </section>

    <section class="panel">
      <form id="analyze-form">
        <div class="row two">
          <div>
            <label for="url">Target URL</label>
            <input id="url" name="url" type="text" placeholder="https://example.com" required />
          </div>
          <div>
            <label for="mode">Mode</label>
            <select id="mode" name="mode">
              <option value="full">Full audit</option>
              <option value="basic">Basic check</option>
            </select>
          </div>
        </div>

        <div class="row three">
          <div>
            <label for="timeout">Timeout (seconds)</label>
            <input id="timeout" name="timeout" type="number" min="2" max="60" value="10" />
          </div>
          <div class="check">
            <input id="use_lighthouse" name="use_lighthouse" type="checkbox" />
            <label for="use_lighthouse" style="margin:0">Try Lighthouse (if available)</label>
          </div>
          <div style="display:flex;align-items:end;justify-content:flex-end">
            <button id="submit-btn" type="submit">Analyze</button>
          </div>
        </div>
      </form>
      <div id="status" class="status"></div>

      <section id="result" class="result">
        <div id="overall" class="overall"></div>
        <div id="scores" class="score-grid"></div>
        <label for="raw">JSON output</label>
        <textarea id="raw" class="raw" readonly></textarea>
      </section>
    </section>
  </main>

  <script>
    const form = document.getElementById('analyze-form');
    const submitBtn = document.getElementById('submit-btn');
    const statusEl = document.getElementById('status');
    const resultEl = document.getElementById('result');
    const overallEl = document.getElementById('overall');
    const scoresEl = document.getElementById('scores');
    const rawEl = document.getElementById('raw');

    function badge(score) {
      if (score >= 85) return '<span class="badge good">excellent</span>';
      if (score >= 70) return '<span class="badge good">good</span>';
      if (score >= 50) return '<span class="badge mid">needs work</span>';
      return '<span class="badge bad">critical</span>';
    }

    function renderResult(result, mode) {
      if (mode === 'full' && result.overall_score !== undefined) {
        overallEl.innerHTML = `Overall score: ${result.overall_score}/100 ${badge(result.overall_score)}`;
      } else {
        overallEl.innerHTML = `Basic check completed (status ${result.status || 'N/A'})`;
      }

      scoresEl.innerHTML = '';
      if (result.criteria) {
        const order = ['performance', 'security', 'seo', 'accessibility', 'best_practices'];
        for (const key of order) {
          const item = result.criteria[key];
          if (!item) continue;
          const card = document.createElement('article');
          card.className = 'score';
          card.innerHTML = `
            <div class="label">${key.replace('_', ' ')}</div>
            <div class="value">${item.score}/100</div>
            <div style="font-size:12px;color:#587084">${item.method}</div>
          `;
          scoresEl.appendChild(card);
        }
      }

      rawEl.value = JSON.stringify(result, null, 2);
      resultEl.style.display = 'block';
    }

    form.addEventListener('submit', async (event) => {
      event.preventDefault();
      const payload = {
        url: document.getElementById('url').value,
        mode: document.getElementById('mode').value,
        timeout: Number(document.getElementById('timeout').value || 10),
        use_lighthouse: document.getElementById('use_lighthouse').checked,
      };

      submitBtn.disabled = true;
      statusEl.textContent = 'Running analysis...';

      try {
        const response = await fetch('/api/analyze', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        });

        const data = await response.json();
        if (!response.ok) {
          throw new Error(data.detail || 'Request failed');
        }

        renderResult(data.result, payload.mode);
        statusEl.textContent = `Done in ${data.elapsed_ms}ms`;
      } catch (error) {
        statusEl.textContent = `Error: ${error.message}`;
      } finally {
        submitBtn.disabled = false;
      }
    });
  </script>
</body>
</html>
"""


class AnalyzeRequest(BaseModel):
    url: str = Field(..., description="Target URL")
    mode: Literal["basic", "full"] = Field(default="full")
    timeout: int = Field(default=10, ge=2, le=60)
    use_lighthouse: bool = Field(default=False)


class AnalyzeResponse(BaseModel):
    ok: bool
    elapsed_ms: int
    result: Dict[str, Any]


app = FastAPI(title=APP_TITLE, version=APP_VERSION)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    return INDEX_HTML


@app.get("/api/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.post("/api/analyze", response_model=AnalyzeResponse)
def analyze(payload: AnalyzeRequest) -> AnalyzeResponse:
    started = time.time()

    try:
        safe_url = validate_public_url(payload.url)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if payload.mode == "basic":
        result = run_basic_analysis(safe_url, timeout=payload.timeout)
    else:
        result = run_full_audit(
            safe_url,
            timeout=payload.timeout,
            use_lighthouse=payload.use_lighthouse,
        )

    if result.get("error"):
        error = result["error"]
        if error == "timeout":
            raise HTTPException(status_code=504, detail="Request timed out")
        if error == "connection_error":
            raise HTTPException(status_code=502, detail="Could not connect to target URL")
        raise HTTPException(status_code=500, detail=f"Analyzer error: {error}")

    elapsed_ms = int((time.time() - started) * 1000)
    return AnalyzeResponse(ok=True, elapsed_ms=elapsed_ms, result=result)
