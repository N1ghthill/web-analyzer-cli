"""FastAPI web application exposing web analyzer API + UI."""

from __future__ import annotations

import os
import queue
import threading
import time
import uuid
from collections import defaultdict, deque
from datetime import datetime, timezone
from typing import Any, Deque, Dict, Literal, Set, Tuple

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel, Field

from .analyzer import run_basic_analysis, run_full_audit
from .url_safety import validate_public_url

APP_TITLE = "Web Analyzer API"
APP_VERSION = "2.3.0"


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _int_env(name: str, default: int, minimum: int = 1) -> int:
    raw = os.getenv(name, "").strip()
    if not raw:
        return default
    try:
        value = int(raw)
    except ValueError:
        return default
    if value < minimum:
        return minimum
    return value


def _load_api_keys() -> Set[str]:
    values = []
    single = os.getenv("WEB_ANALYZER_API_KEY", "")
    multi = os.getenv("WEB_ANALYZER_API_KEYS", "")
    if single:
        values.extend(single.split(","))
    if multi:
        values.extend(multi.split(","))
    return {item.strip() for item in values if item.strip()}


def _client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for", "").strip()
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client and request.client.host:
        return request.client.host
    return "unknown"


class FixedWindowRateLimiter:
    """In-memory fixed-window limiter (per instance)."""

    def __init__(self) -> None:
        self._hits: Dict[str, Deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def allow(self, identity: str, max_requests: int, window_seconds: int) -> Tuple[bool, int]:
        now = time.time()
        cutoff = now - window_seconds

        with self._lock:
            bucket = self._hits[identity]
            while bucket and bucket[0] <= cutoff:
                bucket.popleft()

            if len(bucket) >= max_requests:
                retry_after = max(1, int(window_seconds - (now - bucket[0])))
                return False, retry_after

            bucket.append(now)
            return True, 0

    def clear(self) -> None:
        with self._lock:
            self._hits.clear()


RATE_LIMITER = FixedWindowRateLimiter()

JOB_QUEUE: "queue.Queue[str]" = queue.Queue()
JOBS: Dict[str, Dict[str, Any]] = {}
JOBS_LOCK = threading.Lock()
WORKER_STARTED = False
WORKER_LOCK = threading.Lock()


def _ensure_worker_started() -> None:
    global WORKER_STARTED
    with WORKER_LOCK:
        if WORKER_STARTED:
            return

        thread = threading.Thread(target=_job_worker, name="web-analyzer-worker", daemon=True)
        thread.start()
        WORKER_STARTED = True


def _job_worker() -> None:
    while True:
        job_id = JOB_QUEUE.get()
        try:
            with JOBS_LOCK:
                job = JOBS.get(job_id)
                if not job:
                    continue
                job["status"] = "running"
                job["updated_at"] = _utcnow()

            payload = job["request"]
            result = run_full_audit(
                payload["url"],
                timeout=payload["timeout"],
                use_lighthouse=payload["use_lighthouse"],
            )

            with JOBS_LOCK:
                if result.get("error"):
                    job["status"] = "failed"
                    job["error"] = result["error"]
                else:
                    job["status"] = "completed"
                    job["result"] = result
                job["updated_at"] = _utcnow()
        except Exception as exc:  # pragma: no cover - defensive fallback
            with JOBS_LOCK:
                job = JOBS.get(job_id)
                if job:
                    job["status"] = "failed"
                    job["error"] = str(exc)
                    job["updated_at"] = _utcnow()
        finally:
            JOB_QUEUE.task_done()


def _queue_heavy_job(url: str, timeout: int, use_lighthouse: bool, requested_by: str) -> Dict[str, Any]:
    _ensure_worker_started()

    job_id = uuid.uuid4().hex
    now = _utcnow()

    job = {
        "id": job_id,
        "status": "queued",
        "created_at": now,
        "updated_at": now,
        "requested_by": requested_by,
        "request": {
            "url": url,
            "mode": "full",
            "timeout": timeout,
            "use_lighthouse": use_lighthouse,
        },
        "result": None,
        "error": None,
    }

    with JOBS_LOCK:
        JOBS[job_id] = job

    JOB_QUEUE.put(job_id)

    return {
        "job_id": job_id,
        "status_url": f"/api/jobs/{job_id}",
    }


def _require_api_key(request: Request) -> str:
    valid_keys = _load_api_keys()
    if not valid_keys:
        raise HTTPException(
            status_code=503,
            detail="Server misconfigured: set WEB_ANALYZER_API_KEY or WEB_ANALYZER_API_KEYS",
        )

    provided = request.headers.get("x-api-key", "").strip()
    if not provided:
        raise HTTPException(status_code=401, detail="Missing x-api-key header")

    if provided not in valid_keys:
        raise HTTPException(status_code=401, detail="Invalid API key")

    return provided


def _apply_rate_limit(request: Request, api_key: str) -> None:
    max_requests = _int_env("WEB_ANALYZER_RATE_LIMIT_REQUESTS", 20, minimum=1)
    window_seconds = _int_env("WEB_ANALYZER_RATE_LIMIT_WINDOW_SECONDS", 60, minimum=1)

    identity = f"{api_key}:{_client_ip(request)}"
    allowed, retry_after = RATE_LIMITER.allow(identity, max_requests=max_requests, window_seconds=window_seconds)

    if not allowed:
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded. Retry in {retry_after}s",
            headers={"Retry-After": str(retry_after)},
        )


def reset_runtime_state() -> None:
    """Test helper to clear in-memory runtime state."""
    RATE_LIMITER.clear()
    with JOBS_LOCK:
        JOBS.clear()


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
    .hero h1 {
      margin: 0 0 8px;
      font-size: 30px;
      line-height: 1.1;
      letter-spacing: 0.3px;
    }
    .hero p {
      margin: 0 0 22px;
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
      <p>API-protected quality audits with rate-limit and async queue for heavy Lighthouse runs.</p>
    </section>

    <section class="panel">
      <form id="analyze-form">
        <div class="row two">
          <div>
            <label for="api_key">API key (x-api-key)</label>
            <input id="api_key" name="api_key" type="text" placeholder="Your API key" required />
          </div>
          <div>
            <label for="url">Target URL</label>
            <input id="url" name="url" type="text" placeholder="https://example.com" required />
          </div>
        </div>

        <div class="row three">
          <div>
            <label for="mode">Mode</label>
            <select id="mode" name="mode">
              <option value="full">Full audit</option>
              <option value="basic">Basic check</option>
            </select>
          </div>
          <div>
            <label for="timeout">Timeout (seconds)</label>
            <input id="timeout" name="timeout" type="number" min="2" max="60" value="10" />
          </div>
          <div class="check">
            <input id="use_lighthouse" name="use_lighthouse" type="checkbox" />
            <label for="use_lighthouse" style="margin:0">Use Lighthouse (queued)</label>
          </div>
        </div>

        <div style="display:flex;justify-content:flex-end">
          <button id="submit-btn" type="submit">Analyze</button>
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

    async function pollJob(statusUrl, apiKey) {
      const maxAttempts = 120;

      for (let i = 1; i <= maxAttempts; i += 1) {
        statusEl.textContent = `Queued job. Polling (${i}/${maxAttempts})...`;

        const response = await fetch(statusUrl, {
          method: 'GET',
          headers: {
            'x-api-key': apiKey,
          },
        });

        const data = await response.json();
        if (!response.ok) {
          throw new Error(data.detail || 'Job status failed');
        }

        const job = data.job;
        if (job.status === 'completed') {
          return job.result;
        }

        if (job.status === 'failed') {
          throw new Error(job.error || 'Background job failed');
        }

        await new Promise((resolve) => setTimeout(resolve, 2000));
      }

      throw new Error('Timed out while waiting for queued job');
    }

    form.addEventListener('submit', async (event) => {
      event.preventDefault();

      const apiKey = document.getElementById('api_key').value.trim();
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
          headers: {
            'Content-Type': 'application/json',
            'x-api-key': apiKey,
          },
          body: JSON.stringify(payload),
        });

        const data = await response.json();
        if (!response.ok) {
          throw new Error(data.detail || 'Request failed');
        }

        if (data.queued) {
          const result = await pollJob(data.status_url, apiKey);
          renderResult(result, payload.mode);
          statusEl.textContent = `Queued job completed (${data.job_id})`;
          return;
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


class AnalyzeSyncResponse(BaseModel):
    ok: bool
    queued: bool = False
    elapsed_ms: int
    result: Dict[str, Any]


class AnalyzeQueuedResponse(BaseModel):
    ok: bool
    queued: bool = True
    job_id: str
    status_url: str
    message: str


class JobStatusResponse(BaseModel):
    ok: bool
    job: Dict[str, Any]


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
def health() -> Dict[str, Any]:
    return {
        "status": "ok",
        "version": APP_VERSION,
        "auth_configured": bool(_load_api_keys()),
        "queue_size": JOB_QUEUE.qsize(),
        "rate_limit": {
            "requests": _int_env("WEB_ANALYZER_RATE_LIMIT_REQUESTS", 20, minimum=1),
            "window_seconds": _int_env("WEB_ANALYZER_RATE_LIMIT_WINDOW_SECONDS", 60, minimum=1),
        },
    }


@app.post(
    "/api/analyze",
    responses={
        200: {"model": AnalyzeSyncResponse},
        202: {"model": AnalyzeQueuedResponse},
    },
)
def analyze(payload: AnalyzeRequest, request: Request):
    started = time.time()

    api_key = _require_api_key(request)
    _apply_rate_limit(request, api_key)

    try:
        safe_url = validate_public_url(payload.url)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    # Heavy Lighthouse runs go through async queue.
    if payload.mode == "full" and payload.use_lighthouse:
        queued = _queue_heavy_job(
            url=safe_url,
            timeout=payload.timeout,
            use_lighthouse=True,
            requested_by=f"{api_key}:{_client_ip(request)}",
        )
        return JSONResponse(
            status_code=202,
            content={
                "ok": True,
                "queued": True,
                "job_id": queued["job_id"],
                "status_url": queued["status_url"],
                "message": "Heavy analysis queued. Poll status_url for completion.",
            },
        )

    if payload.mode == "basic":
        result = run_basic_analysis(safe_url, timeout=payload.timeout)
    else:
        result = run_full_audit(
            safe_url,
            timeout=payload.timeout,
            use_lighthouse=False,
        )

    if result.get("error"):
        error = result["error"]
        if error == "timeout":
            raise HTTPException(status_code=504, detail="Request timed out")
        if error == "connection_error":
            raise HTTPException(status_code=502, detail="Could not connect to target URL")
        raise HTTPException(status_code=500, detail=f"Analyzer error: {error}")

    elapsed_ms = int((time.time() - started) * 1000)
    return AnalyzeSyncResponse(ok=True, queued=False, elapsed_ms=elapsed_ms, result=result)


@app.get("/api/jobs/{job_id}", response_model=JobStatusResponse)
def get_job_status(job_id: str, request: Request) -> JobStatusResponse:
    api_key = _require_api_key(request)
    _apply_rate_limit(request, api_key)

    with JOBS_LOCK:
        job = JOBS.get(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        data = dict(job)

    return JobStatusResponse(ok=True, job=data)
