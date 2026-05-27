# Lab 3 — Continuous Integration with GitHub Actions

![difficulty](https://img.shields.io/badge/difficulty-beginner-success)
![topic](https://img.shields.io/badge/topic-CI/CD-blue)
![points](https://img.shields.io/badge/points-10%2B2-orange)
![tech](https://img.shields.io/badge/tech-GitHub%20Actions-informational)

> Take the Python service from Labs 1–2 and put a pipeline behind it: every push runs tests, scans for vulnerabilities, builds the image, and publishes it to GHCR — automatically, on a clean runner, every time.

## Overview

A green checkmark on a laptop proves nothing. CI runs the *same* steps on the *same* runner for *every* commit, so "works on my machine" stops being a defence. In this lab you build the workflow Lecture 3 walks through: **test → scan → build → publish**, gated on every pull request.

**What You'll Learn:**
- Writing meaningful unit tests with pytest
- GitHub Actions workflow syntax (jobs, steps, `needs`, matrix)
- Publishing Docker images to GHCR with `GITHUB_TOKEN` (no secret to rotate)
- Gating merges on a Trivy vulnerability scan
- Speeding CI up with dependency + layer caching

**Tech Stack:** GitHub Actions (`ubuntu-24.04`) | pytest 8+ | Python 3.13 | Trivy `v0.69.3+` | GHCR

**Builds on:**
- **Lab 1** — the Flask/FastAPI service whose `/` and `/health` endpoints you'll test
- **Lab 2** — the Dockerfile your CI now builds and pushes for you
- **Lab 4+** — this pipeline keeps running as the safety net for every future lab

---

## A Note on Supply-Chain Safety (read before Task 2)

CI runs third-party code with access to your repository's secrets. That makes the tools in your pipeline part of your attack surface:

- **tj-actions/changed-files (CVE-2025-30066, Mar 2025)** — a compromised release leaked secrets from CI logs in **23,000+** repositories. Anyone pinned to `@main` or a floating tag pulled the malicious code automatically.
- **Trivy (CVE-2026-33634, Mar 2026)** — a malicious **`v0.69.4`** binary was published after maintainer keys were compromised. **Use `v0.69.3` or a later patched release — never `v0.69.4`.** The `trivy-action` (≥ `v0.35.0`) is post-incident-safe.

**What you do about it in this lab:**
- Pin the runner OS (`ubuntu-24.04`, not `ubuntu-latest`).
- Pin actions to a major tag (`actions/checkout@v4`). For high-risk or third-party actions, pin to a **full commit SHA** — a tag can be re-pointed by an attacker; a SHA cannot.
- Scope `permissions:` to the minimum each job needs.

> 📌 Example of a SHA-pinned step (comment keeps it readable):
> ```yaml
> - uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683 # v4.2.2
> ```

---

## Tasks

### Task 1 — Unit Tests with pytest (2 pts)

Before automating anything, your app needs tests worth running.

**Requirements:**

1. **Add a test framework.** Use **pytest** (fixtures + plain `assert` beat `unittest`'s boilerplate for most projects). Add it to a `requirements-dev.txt`:
   ```txt
   pytest==8.3.4
   pytest-cov==6.0.0
   ```

2. **Write real tests** in `app_python/tests/` covering both endpoints. Assert on *behaviour*, not just that the import works:
   - `GET /` → status `200`, JSON body contains the expected keys
   - `GET /health` → status `200`, `status == "healthy"`
   - An error path (e.g. an unknown route returns `404`)

3. **Run them locally** and confirm they pass before touching CI.

<details>
<summary>💡 Test skeleton (Flask)</summary>

```python
# app_python/tests/test_app.py
import pytest
from app import app  # adjust import to your structure

@pytest.fixture
def client():
    app.config["TESTING"] = True
    return app.test_client()

def test_root_returns_service_info(client):
    r = client.get("/")
    assert r.status_code == 200
    body = r.get_json()
    assert "service" in body
    assert "system" in body

def test_health_is_healthy(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.get_json()["status"] == "healthy"

def test_unknown_route_is_404(client):
    assert client.get("/nope").status_code == 404
```

For FastAPI, use `from fastapi.testclient import TestClient` instead of `app.test_client()`.

**Avoid:** tests with no assertions, tests that always pass, tests that hit a real network/prod URL, or testing the framework instead of your code.
</details>

**Run it:**
```bash
cd app_python
pip install -r requirements.txt -r requirements-dev.txt
pytest -q
```

**Document:** which framework and why; what each test checks; the local `pytest` output (illustrative, paste your real run).

---

### Task 2 — Test & Lint in CI (3 pts)

Create `.github/workflows/python-ci.yml` so the tests from Task 1 run on every push and PR. This task delivers the workflow's **test job**; Tasks 3–4 add jobs to the *same* file.

**Requirements:**

1. **Triggers** — run on `push` to `main` and on `pull_request`.
2. **A `test` job** on `ubuntu-24.04` that checks out the code, sets up Python 3.13 with pip caching, installs deps, lints (`ruff`/`flake8`/`pylint`), and runs `pytest`.
3. **Caching** — use `setup-python`'s built-in `cache: pip` keyed on your requirements file. Note the warm-cache speed-up in your docs.
4. **Matrix** — fan the test job over Python `3.12` and `3.13` with `fail-fast: false`.
5. **Concurrency** — cancel superseded runs on the same ref so PR pushes don't pile up.
6. **A status badge** in `app_python/README.md` linking to the Actions tab.

Fill in every `YOUR-TASK` marker below — you write the workflow:

```yaml
name: Python CI

on:
  # YOUR-TASK: trigger on push to main and on pull_request

permissions:
  contents: read          # least privilege; Task 3 adds packages: write to the build job

concurrency:
  # YOUR-TASK: group by ref and cancel-in-progress

jobs:
  test:
    runs-on: ubuntu-24.04
    strategy:
      fail-fast: false
      matrix:
        python-version: # YOUR-TASK: ["3.12", "3.13"]
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
          cache: pip
          cache-dependency-path: app_python/requirements.txt

      - name: Install dependencies
        run: # YOUR-TASK: pip install -r requirements.txt -r requirements-dev.txt (in app_python/)

      - name: Lint
        run: # YOUR-TASK: run ruff / flake8 / pylint

      - name: Test
        run: # YOUR-TASK: pytest
```

> 💡 The cache key is `runner.os + python-version + hash(requirements.txt)`. Change the file and it invalidates automatically — don't hand-roll `actions/cache` for pip unless `setup-python` doesn't fit.

**Document:** trigger choice and why; warm vs cold install time (illustrative — record your own); why the matrix uses `fail-fast: false`; link to a successful run.

---

### Task 3 — Build & Publish to GHCR (3 pts)

Lab 2 pushed images by hand. Automate it: add a `docker` job that builds your Lab 2 image and pushes it to **GitHub Container Registry (GHCR)** — authenticated with the auto-provisioned `GITHUB_TOKEN`, so there's **no secret to create or rotate**.

**Requirements:**

1. **`docker` job** that `needs: test` — it only runs if every matrix cell passed.
2. **Auth to GHCR** via `docker/login-action@v3` using `${{ secrets.GITHUB_TOKEN }}`.
3. **Tags** via `docker/metadata-action@v5` — at least two per image (a version/SHA tag plus `latest` on the default branch). Pick **SemVer** (git tags) or **CalVer** (date) and justify it.
4. **Build + push** via `docker/build-push-action@v6` with BuildKit GHA layer caching.

```yaml
  docker:
    needs: test
    runs-on: ubuntu-24.04
    permissions:
      contents: read
      packages: write       # required to push to GHCR
    steps:
      - uses: actions/checkout@v4

      - uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}   # ephemeral, scoped to this run

      - uses: docker/metadata-action@v5
        id: meta
        with:
          images: ghcr.io/${{ github.repository }}
          tags: |
            # YOUR-TASK: define your tag strategy, e.g.
            # type=sha,prefix=git-
            # type=raw,value=latest,enable={{is_default_branch}}

      - uses: docker/build-push-action@v6
        with:
          context: ./app_python
          push: # YOUR-TASK: true (consider: only push on main, not on PRs from forks)
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
```

> ⚠️ Never deploy `:latest` to production — it's mutable; tomorrow's image with the same tag is a different artifact. Pin by version or digest. `:latest` is a convenience pointer, not a release.

**Document:** SemVer vs CalVer choice and rationale; the tags your CI produces; a link to the pushed package under your repo's **Packages**.

---

### Task 4 — Trivy Vulnerability Gate (2 pts)

A scan that only warns gets ignored. Make Trivy a **gate**: a HIGH/CRITICAL finding fails the job and blocks the merge.

**Requirements:**

1. **Run Trivy** with `aquasecurity/trivy-action@0.35.0` (or later — **never `v0.69.4`**, see the supply-chain note). Scan the filesystem (`scan-type: fs`) to catch vulnerable dependencies in `requirements.txt`.
2. **Fail the build** on findings: `exit-code: "1"`, `severity: HIGH,CRITICAL`, `ignore-unfixed: true` (skip CVEs with no patch yet — but track them).
3. **Wire it as a gate** — put the scan in the `test` job (or a `scan` job that `docker` `needs:`), so a vulnerable dependency stops the image from being published.
4. **Branch protection** — in `Settings → Branches`, require the `test`/`scan` and `docker` checks to pass before merging to `main`.

```yaml
      - name: Trivy filesystem scan
        uses: aquasecurity/trivy-action@0.35.0   # >= 0.35.0; do NOT use Trivy v0.69.4
        with:
          scan-type: fs
          scan-ref: ./app_python
          severity: # YOUR-TASK: HIGH,CRITICAL
          exit-code: # YOUR-TASK: "1" to fail the job on findings
          ignore-unfixed: true
```

> 💡 If Trivy flags a dependency, the fix belongs in the PR: bump the version in `requirements.txt`. Don't silence it with `ignore-unfixed` for *fixable* CVEs, and don't blanket-suppress findings — track anything genuinely unfixable in an issue and revisit it.

**Document:** what Trivy reported on your deps (illustrative if clean), what you bumped, your severity threshold and why; a screenshot of branch protection requiring the checks.

---

## Bonus Task — Path-Filtered Multi-App CI + Coverage (2 pts)

Wire CI for your Lab 1 bonus compiled-language app **and** add coverage tracking.

**Part 1 — Second workflow with path filters (1 pt)**

1. Add `.github/workflows/<language>-ci.yml` for your Go/Rust/Java app (lint + test + build image), using language-specific actions.
2. **Path-filter both workflows** so each runs only when its own app changes — neither fires on a docs-only commit:
   ```yaml
   on:
     push:
       paths:
         - 'app_python/**'
         - '.github/workflows/python-ci.yml'
   ```
3. Demonstrate selective triggering (a commit touching only one app runs only one workflow).

**Part 2 — Coverage (1 pt)**

4. Generate coverage in CI (`pytest --cov=app_python --cov-report=xml`) and upload to Codecov or Coveralls (free for public repos).
5. Add a coverage badge to `app_python/README.md` and document your current percentage + what's intentionally uncovered.

**Document:** path-filter config + proof of selective runs; coverage percentage, badge, and a one-line analysis of what's not covered and why.

---

## How to Submit

1. **Branch:**
   ```bash
   git checkout -b lab03
   ```
2. **Commit** workflow files (`.github/workflows/`), tests (`app_python/tests/`), `requirements-dev.txt`, and docs (`app_python/docs/LAB03.md`):
   ```bash
   git add .github/ app_python/
   git commit -m "feat: add CI pipeline (test, scan, build, push)"
   git push -u origin lab03
   ```
3. **Verify CI runs** on your fork — all jobs green.
4. **Open Pull Requests:**
   - **PR #1:** `your-fork:lab03` → `course-repo:main`
   - **PR #2:** `your-fork:lab03` → `your-fork:main`

   CI runs automatically on both.

---

## Acceptance Criteria

### Main Tasks (10 points)

**Unit Tests (2 pts):**
- [ ] pytest chosen with justification; `requirements-dev.txt` present
- [ ] Tests in `app_python/tests/` cover `/`, `/health`, and an error path with real assertions
- [ ] Tests pass locally (output provided)

**Test & Lint in CI (3 pts):**
- [ ] `.github/workflows/python-ci.yml` triggers on push to `main` + PR
- [ ] `test` job: checkout, `setup-python@v5` with pip cache, install, lint, pytest
- [ ] Matrix over Python 3.12 + 3.13 with `fail-fast: false`
- [ ] Concurrency cancels superseded runs
- [ ] Status badge in `README.md`; link to a passing run

**Build & Publish to GHCR (3 pts):**
- [ ] `docker` job `needs: test`
- [ ] Logs in to `ghcr.io` with `GITHUB_TOKEN`; `packages: write` scoped to the job
- [ ] `metadata-action@v5` produces ≥ 2 tags; SemVer/CalVer choice justified
- [ ] `build-push-action@v6` with GHA layer cache; image visible under repo Packages

**Trivy Gate (2 pts):**
- [ ] `trivy-action@0.35.0+` filesystem scan (not Trivy v0.69.4)
- [ ] `severity: HIGH,CRITICAL`, `exit-code: "1"` — failing findings block the build
- [ ] Scan gates publishing (in `test`/`scan`, or `docker` `needs:` it)
- [ ] Branch protection requires the CI checks before merge

### Bonus Task (2 points)
- [ ] Second workflow for the compiled-language app (lint + test + build)
- [ ] Path filters on both workflows; selective triggering demonstrated
- [ ] Coverage generated in CI and uploaded to Codecov/Coveralls
- [ ] Coverage badge in README + brief coverage analysis

---

## Documentation Requirements

Create `app_python/docs/LAB03.md`:

1. **Overview** — framework choice; what the tests cover; trigger config; SemVer vs CalVer rationale.
2. **Workflow Evidence** — link to a passing run; local pytest output; GHCR package link; badge in README. *(Mark any pasted logs as illustrative if not from a real run.)*
3. **Best Practices** — caching (warm vs cold time), matrix, concurrency, least-privilege `permissions`, SHA-pinning where used — one line each.
4. **Security** — what Trivy found, what you bumped, your severity threshold; branch-protection screenshot.
5. **Challenges** *(optional)* — brief bullets.

> Target: 15–30 min to write, 5 min to review. No essays.

---

## Rubric

| Criteria | Points | Description |
|----------|--------|-------------|
| **Unit Tests** | 2 pts | Meaningful pytest coverage of both endpoints + error path |
| **Test & Lint in CI** | 3 pts | Matrix test job, pip caching, concurrency, badge |
| **Build & Publish** | 3 pts | GHCR push via metadata + build-push-action, ≥ 2 tags |
| **Trivy Gate** | 2 pts | Scan fails on HIGH/CRITICAL; gates the build; branch protection |
| **Bonus** | 2 pts | Path-filtered multi-app CI + coverage badge |
| **Total** | 12 pts | 10 pts required + 2 pts bonus |

**Grading:**
- **10/10:** All jobs green, scan gates correctly, meaningful tests, concise docs
- **8–9/10:** CI works, good tests, best practices applied, solid docs
- **6–7/10:** CI functional, basic tests, some best practices, minimal docs
- **<6/10:** CI broken or missing the scan/publish gate, weak tests

**For full points:** tests assert real behaviour · all jobs pass · image lands in GHCR with ≥ 2 tags · Trivy actually fails on HIGH/CRITICAL · docs concise with real evidence.

---

## Resources

<details>
<summary>📚 GitHub Actions</summary>

- [GitHub Actions Docs](https://docs.github.com/en/actions)
- [Workflow Syntax](https://docs.github.com/en/actions/using-workflows/workflow-syntax-for-github-actions)
- [Building & Testing Python](https://docs.github.com/en/actions/automating-builds-and-tests/building-and-testing-python)
- [Publishing to GHCR](https://docs.github.com/en/actions/publishing-packages/publishing-docker-images)
- [Security Hardening for Actions](https://docs.github.com/en/actions/security-guides/security-hardening-for-github-actions)

</details>

<details>
<summary>🧪 Testing & Coverage</summary>

- [pytest Documentation](https://docs.pytest.org/)
- [Flask Testing](https://flask.palletsprojects.com/en/stable/testing/) · [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [pytest-cov](https://pytest-cov.readthedocs.io/) · [Codecov](https://docs.codecov.com/)

</details>

<details>
<summary>🔒 Security & Supply Chain</summary>

- [Trivy](https://github.com/aquasecurity/trivy) · [trivy-action](https://github.com/aquasecurity/trivy-action) (use ≥ v0.35.0)
- [Grype](https://github.com/anchore/grype) — Apache-2.0 alternative scanner
- [Pinning actions to a SHA](https://docs.github.com/en/actions/security-guides/security-hardening-for-github-actions#using-third-party-actions)
- [tj-actions/changed-files advisory (CVE-2025-30066)](https://github.com/advisories/GHSA-mrrh-fwg8-r2c3)

</details>

<details>
<summary>🏷️ Versioning, Caching & Local Tooling</summary>

- [Semantic Versioning](https://semver.org/) · [Calendar Versioning](https://calver.org/) · [docker/metadata-action](https://github.com/docker/metadata-action)
- [Caching Dependencies](https://docs.github.com/en/actions/using-workflows/caching-dependencies-to-speed-up-workflows) · [Docker Build Cache](https://docs.docker.com/build/cache/)
- [act](https://github.com/nektos/act) (run Actions locally) · [actionlint](https://github.com/rhysd/actionlint) · [gh](https://cli.github.com/) (`gh run watch`)

</details>

---

## Looking Ahead

- **Lab 4–6:** CI validates your Terraform / Ansible (`terraform plan` as a gate — same idea as tests)
- **Lab 7–8:** CI runs integration tests once logging/metrics land
- **Lab 9–10:** CI validates Kubernetes manifests and Helm charts
- **Lab 13:** ArgoCD deploys the GHCR image your CI publishes (GitOps)
- **Every future lab:** this pipeline is your safety net

---

**Good luck!** 🚀

> **Remember:** a good pipeline is fast, deterministic, and boring. CI isn't about green checkmarks — it's about catching problems before they reach production.
