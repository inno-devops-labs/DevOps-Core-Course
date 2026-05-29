# Lab 1 — DevOps Info Service: Web Application Development

![difficulty](https://img.shields.io/badge/difficulty-beginner-success)
![topic](https://img.shields.io/badge/topic-Web%20Development-blue)
![points](https://img.shields.io/badge/points-10%2B2-orange)
![languages](https://img.shields.io/badge/languages-Python%20|%20Go-informational)

> **Goal:** Build the seed of your DevOps Info Service — a small HTTP service that reports its own metadata + the host it runs on. Every later lab grows this same service.
> **Deliverable:** A PR from `lab01` with `app_python/` (and optionally `app_go/`). The image you build over the next 16 weeks starts here.

---

## Overview

In this lab you will practice:
- Picking a Python web framework and justifying the choice
- Reading host/runtime info from `platform`, `socket`, `os`
- Wiring HTTP routes that return JSON (not HTML)
- Pinning dependencies, configuring via environment variables, writing real docs

> ⚠️ **Scope:** no database, no auth, no Docker yet. That comes in Lab 2+. Don't get clever — keep the code short and obvious.

---

## Project State

**You should have from previous labs:**
- Nothing — this is week 1.

**This lab adds:**
- `app_python/` — Python service with `GET /` (info) and `GET /health` (probe)
- *(optional bonus)* `app_go/` — compiled-language sibling with the same endpoints

By Lab 9 this service runs on Kubernetes; by Lab 13 ArgoCD deploys it. So the choices you make this week — framework, layout, env-var config — outlive Lab 1.

---

## Setup

You need only:

```bash
python3 --version         # 3.12+ (course standardizes on 3.13)
pip3 --version
```

> 📝 **`python` vs `python3`**: on Debian/Ubuntu the binary is `python3`; on macOS/Windows it may be `python`. Pick whichever exists on your box — the rest of this lab writes `python app.py` for brevity, substitute `python3 app.py` if that's how your system spells it.

Create the directory layout (you'll fill the files yourself):

```
app_python/
├── app.py
├── requirements.txt
├── .gitignore
├── README.md
├── tests/
│   └── __init__.py            # empty; tests come in Lab 3
└── docs/
    └── LAB01.md               # your submission report
```

---

## Task 1 — Python Web Application (6 pts)

### 1.1 — Pick a framework and justify it

You may use **Flask 3.1**, **FastAPI 0.136**, or **Django 5.2** (overkill for this; do it if you want the practice). In `docs/LAB01.md`, give your one-paragraph reasoning + a small comparison table covering at least: footprint, async support, OpenAPI/docs, learning curve.

### 1.2 — `GET /` returns the full info JSON

`YOUR TASK`: write a handler at the root path that returns JSON with **five** top-level keys: `service`, `system`, `runtime`, `request`, `endpoints`.

Requirements:

- `service`: `name`, `version`, `description`, `framework` (your choice from 1.1)
- `system`: `hostname`, `platform`, `platform_version`, `architecture`, `cpu_count`, `python_version`
- `runtime`: `uptime_seconds` (int), `uptime_human` (e.g. `"1 hour, 3 minutes"`), `current_time` (ISO 8601 UTC), `timezone`
- `request`: `client_ip`, `user_agent`, `method`, `path`
- `endpoints`: list of `{path, method, description}` for every route you publish

Hints:

- `platform.system()`, `platform.machine()`, `platform.python_version()` cover most of `system`
- `socket.gethostname()` for the hostname
- Uptime = `datetime.now(timezone.utc) - START_TIME` captured at module import — be **timezone-aware** throughout (mixing naive + aware datetimes raises `TypeError`)
- Per-framework request access: Flask → `request.remote_addr` / `request.headers.get('User-Agent')`; FastAPI → `request.client.host` / `request.headers.get('user-agent')`

<details>
<summary>💡 Stuck on the structure?</summary>

Sketch — no Python code given, intentionally:

```
imports → app object → constants (SERVICE_NAME, START_TIME, ...) → helper get_system_info() → helper get_uptime() → route handler returning the 5-key dict → error handlers → __main__ block
```

Lecture 1 slide on the lifecycle, lecture 2 on configuration — both apply here.

</details>

### 1.3 — `GET /health` returns a small JSON + HTTP 200

`YOUR TASK`: write a second handler that returns `{status, timestamp, uptime_seconds}` and status code **200**. This will be your Kubernetes liveness/readiness target in Lab 9 — keep it cheap (no DB calls, no external HTTP).

### 1.4 — Configurable via environment variables

`YOUR TASK`: read `HOST`, `PORT`, `DEBUG` from the environment with sensible defaults (`0.0.0.0`, `5000`, `False`). The app must run unchanged with:

```bash
python app.py                            # default 0.0.0.0:5000
PORT=8080 python app.py                  # custom port
HOST=127.0.0.1 PORT=3000 python app.py   # both
```

Hint: cast `PORT` to `int` and `DEBUG` to `bool` by **lowercase string comparison** (`os.getenv("DEBUG","False").lower() == "true"`) — `bool("False")` is `True` in Python; that's the easy way to ship a debug-mode bug to production.

### 1.5 — Error handlers and logging

`YOUR TASK`: register handlers for **404** and **500** that return JSON (matching the rest of the API), and configure stdlib `logging` at INFO level with a format including timestamp/level. Don't `print()`.

### 1.6 — Proof of work

**Paste into `docs/LAB01.md`:**

- Four CLI captures, with the **exact commands** you ran:
  - `curl -s http://localhost:5000/ | jq .` — full JSON, your real hostname + uptime
  - `curl -s http://localhost:5000/health | jq .`
  - `curl -s -o /dev/null -w "HTTP %{http_code}\n" http://localhost:5000/nope` — proves the 404 handler
  - `PORT=8080 python app.py` started in another shell + a `curl` showing the new port served — proves env-var config
- The framework comparison table from 1.1
- 2–3 sentences on the biggest gotcha you hit and how you solved it

<details>
<summary>💡 Hints if you're stuck</summary>

- Make the framework choice early — switching mid-lab burns time.
- Build `GET /` last. Build `GET /health` first (5 lines), then incrementally add system info, uptime, request info.
- If JSON output looks "weird" (e.g., bytes prefix `b'...'`), you're returning a string instead of a dict — let the framework jsonify.

</details>

---

## Task 2 — Documentation & Best Practices (4 pts)

### 2.1 — `app_python/README.md`

`YOUR TASK`: write the user-facing README with these sections (no fluff, prefer commands over prose):

1. **Overview** — one paragraph
2. **Prerequisites** — Python version, OS
3. **Installation** — `python -m venv venv` … `pip install -r requirements.txt`
4. **Running** — default + custom-port examples
5. **API Endpoints** — table of `Method | Path | Description`
6. **Configuration** — table of env vars + defaults + purpose

### 2.2 — Code-quality hygiene

`YOUR TASK`: ship the things every Python service needs.

| File | Must contain |
|---|---|
| `requirements.txt` | The framework **pinned to an exact patch** (e.g. `Flask==3.1.3`, not `Flask>=3`). One framework only — drop the rest. |
| `.gitignore` | `__pycache__/`, `*.pyc`, `venv/`, `*.log`, IDE dirs (`.vscode/`, `.idea/`), `.DS_Store` |
| Imports in `app.py` | Grouped (stdlib → third-party → local), PEP 8 compliant |

### 2.3 — `app_python/docs/LAB01.md` — your submission report

Required sections, in order:

1. **Framework Selection** — your choice + comparison table
2. **Best Practices Applied** — bulleted list, each with one sentence of *why*
3. **API Documentation** — request + response example per endpoint
4. **Testing Evidence** — the four CLI captures from 1.6
5. **Challenges & Solutions** — at least one real one (not "I was new to Python")
6. **GitHub Community** — one paragraph; see 2.4

### 2.4 — GitHub community engagement

This is the social half of being a developer. The actions are public on your profile.

`YOUR TASK`:
1. **Star** the course repository.
2. **Star** [`simple-container-com/api`](https://github.com/simple-container-com/api) — an open-source container management tool worth knowing about.
3. **Follow** your professor [@Cre-eD](https://github.com/Cre-eD) and the TAs (the course page lists them).
4. **Follow** ≥ 3 classmates from this course.
5. In your `docs/LAB01.md` "GitHub Community" section, **put your GitHub username on the first line** (so the TA can verify your stars/follows in <30s) then write 2–3 sentences answering: *Why does starring a project actually help its maintainers? What concrete benefit do you get from following other developers?* — your own words, not the lecture's.

### 2.5 — Proof of work

**Paste into `docs/LAB01.md`:**

- The `docs/LAB01.md` itself satisfies all six required sections — that *is* the proof.
- Output of `find app_python -maxdepth 2 -type f | sort` showing every required file is present.

---

## Bonus Task — Compiled-Language Sibling (2 pts)

Re-implement the same service in a **compiled language**, in a sibling directory (e.g. `app_go/`).

Why bother? Lab 2's multi-stage Docker bonus shrinks a Go service from ~900 MB to ~15 MB — that doesn't work without a static binary to start with.

`YOUR TASK`:

- Same two endpoints (`/`, `/health`)
- Same JSON shape as your Python version (so the same `curl` calls work against both)
- A README in the sibling dir explaining build + run
- A `go.mod` (and `go.sum` if you pull deps) — Lab 2's bonus needs them as the build context
- In `docs/LAB01.md`, add a one-line **artifact size** for both. Measure the same way for each so the comparison is apples-to-apples:
  - Python: `du -sh app_python/venv` (the venv carries everything beyond the interpreter)
  - Compiled: `ls -lh app_go/<binary>` (the single static binary)
  - The size delta is the whole point. The real Docker-image comparison comes in Lab 2.

Choose one of:

| Language | Idiomatic HTTP | Notes |
|---|---|---|
| **Go** *(recommended)* | `net/http` | Single static binary; instant compile; smallest distroless image later |
| Rust | `actix-web` / `axum` | Strong types; longer compile; great for the security-minded |
| Java + Spring Boot | `spring-boot-starter-web` | Industry-standard for enterprise — heavier runtime |
| C# + ASP.NET Core | `WebApplication.Create` | Cross-platform .NET; comparable to Java but newer ergonomics |

Hints (no full code):

- For Go, `runtime.NumCPU()`, `runtime.GOOS`, `runtime.GOARCH`, `os.Hostname()` mirror Python's `os`/`platform`. JSON keys differ in casing — use struct tags (`json:"hostname"`) to keep the same wire shape.
- For Java/C#, start from `spring init` / `dotnet new web` — don't hand-write `pom.xml`/`csproj`.

---

## How to Submit

```bash
git switch -c lab01
git add app_python/
git add app_go/                   # only if you did the bonus
git commit -m "feat(lab01): devops info service — python (+ go bonus)"
git push -u origin lab01
```

Open **two** PRs:

- `your-fork:lab01` → `course-repo:master` *(reviewed)*
- `your-fork:lab01` → `your-fork:master` *(merges into your own main when done)*

PR checklist:

```text
- [ ] Task 1 done — /, /health, env config, error handlers, logging
- [ ] Task 2 done — README, requirements.txt, .gitignore, docs/LAB01.md, GitHub social
- [ ] Bonus done — app_go/ (or other) with same endpoints + size comparison
```

---

## Acceptance Criteria

### Task 1 (6 pts)
- ✅ Service starts with `python app.py` and serves on `0.0.0.0:5000`
- ✅ `GET /` returns HTTP 200 with all five top-level keys populated from *your real machine*
- ✅ `GET /health` returns HTTP 200 with the three required fields
- ✅ 404 handler returns JSON (not HTML)
- ✅ `PORT` env var overrides the port
- ✅ Logging is configured (you'll see startup log line in stdout)

### Task 2 (4 pts)
- ✅ `README.md` has all six sections
- ✅ `requirements.txt` pins an **exact** version
- ✅ `.gitignore` covers Python + IDE + OS artifacts
- ✅ `docs/LAB01.md` has all six sections including the GitHub Community paragraph
- ✅ Stars + follows visible on student's GitHub profile

### Bonus Task (2 pts)
- ✅ Sibling app builds and serves the same two endpoints
- ✅ Wire-compatible JSON (same `curl … | jq` works against both)
- ✅ Artifact-size comparison documented (`du -sh venv` vs `ls -lh <binary>`)
- ✅ Build manifest present (`go.mod` / `Cargo.toml` / `pom.xml` / `*.csproj`) so Lab 2's bonus has a build context to `COPY`

---

## Rubric

| Task | Points | Criteria |
|------|-------:|----------|
| **Task 1** — Python web app | **6** | Both routes correct, env-var config, error handlers, logging |
| **Task 2** — Docs & hygiene | **4** | All file/section requirements met; pinned deps; complete LAB01.md |
| **Bonus** — Compiled sibling | **2** | Same endpoints, wire-compatible JSON, size comparison |
| **Total** | **12** | 10 main + 2 bonus |

---

## Resources

<details>
<summary>📚 Documentation</summary>

- [Flask 3.1](https://flask.palletsprojects.com/en/latest/) — the canonical micro-framework
- [FastAPI](https://fastapi.tiangolo.com/) — async, OpenAPI free
- [Django 5.2](https://docs.djangoproject.com/en/stable/) — full-stack; overkill for this lab
- [Python `platform`](https://docs.python.org/3/library/platform.html) / [`socket`](https://docs.python.org/3/library/socket.html)
- [PEP 8](https://pep8.org/), [PEP 660](https://peps.python.org/pep-0660/)

</details>

<details>
<summary>⚠️ Common Pitfalls (from real dry-runs)</summary>

- **Naive vs aware datetimes** — `datetime.now() - START_TIME` raises `TypeError` if one is timezone-aware and the other isn't. Pick one (use `datetime.now(timezone.utc)` everywhere) and stay there.
- **`bool("False") == True`** — never write `DEBUG = bool(os.getenv("DEBUG", "False"))`. Use a lowercase string compare.
- **Flask 3 deprecation warning** on `flask.__version__` — use `importlib.metadata.version("flask")` if you need to print the framework version.
- **Returning a dict directly from FastAPI vs Flask** — FastAPI auto-serializes; Flask needs `jsonify(...)`. Don't return a bare dict from a Flask handler.
- **`socket.gethostname()` inside a container** later returns the container ID, not your laptop name — that's correct, not a bug. You'll see it again in Lab 2.
- **Port 5000 occupied on macOS** — macOS Monterey+ runs the *AirPlay Receiver* on `:5000`. The Flask default conflicts; you'll see your `curl` hit Apple's service instead. Either turn AirPlay Receiver off (System Settings → General → AirDrop & Handoff) or pick `PORT=5050` for your default run.
- **`pip install -r requirements.txt` outside the venv** — installs Flask system-wide, then `python app.py` may still pick up a stale Flask elsewhere. Always activate the venv (`source venv/bin/activate`) before `pip install` and before `python app.py`.
- **Don't return a Response from `@app.errorhandler`'s default** — Flask's 500 handler must return a tuple `(body, status)`. Returning a bare `jsonify(...)` sends HTTP 200 with the error JSON — a subtle bug that breaks the Lab 9 probe later.

</details>

<details>
<summary>🛠️ Dev tools worth knowing</summary>

- [jq](https://jqlang.github.io/jq/) — JSON CLI; `curl ... | jq .` is your friend
- [HTTPie](https://httpie.io/) — friendlier than `curl` for ad-hoc testing
- [Ruff](https://docs.astral.sh/ruff/) — fast Python linter (used in Lab 3 CI)

</details>

---

## Looking Ahead

| Lab | What it adds to this service |
|---:|---|
| 2 | Multi-stage Dockerfile, image scan, push to a registry |
| 3 | CI: pytest + lint + image build + Trivy gate on every PR |
| 7 / 8 | Structured JSON logs (Loki + Alloy) and a `/metrics` endpoint (Prometheus) |
| 9 / 10 | Deploy to Kubernetes (k3d) + Helm 4 chart |
| 11 / 12 | OpenBao for secrets, ConfigMaps + PVCs for state |
| 13 / 14 | ArgoCD GitOps + canary rollouts |

Keep the code simple. You'll come back and rewrite parts of it; that's the point.
