# Lab 3 — Continuous Integration (CI/CD)

![difficulty](https://img.shields.io/badge/difficulty-beginner-success)
![topic](https://img.shields.io/badge/topic-CI/CD-blue)
![points](https://img.shields.io/badge/points-10%2B2.5-orange)
![tech](https://img.shields.io/badge/tech-GitHub%20Actions-informational)

> Automate your Python app testing and Docker builds with GitHub Actions CI/CD pipeline.

## Overview

Take your containerized app from Labs 1-2 and add automated testing and deployment. Learn how CI/CD catches bugs early, ensures code quality, and automates the Docker build/push workflow.

**What You'll Learn:**
- Writing effective unit tests
- GitHub Actions workflow syntax
- CI/CD best practices (caching, matrix builds, security scanning)
- Automated Docker image publishing
- Continuous integration for multiple applications

**Tech Stack:** GitHub Actions | pytest 8+ | Python 3.11+ | Snyk | Docker

**Connection to Previous Labs:**
- **Lab 1:** Test the endpoints you created
- **Lab 2:** Automate the Docker build/push workflow
- **Lab 4+:** This CI pipeline will run for all future labs

---

## Tasks

### Task 1 — Unit Testing (3 pts)

**Objective:** Write comprehensive unit tests for your Python application to ensure reliability.

**Requirements:**

1. **Choose a Testing Framework**
   - Research Python testing frameworks (pytest, unittest, etc.)
   - Select one and justify your choice
   - Install it in your `requirements.txt` or create `requirements-dev.txt`

2. **Write Unit Tests**
   - Create `app_python/tests/` directory
   - Write tests for **all** your endpoints:
     - `GET /` - Verify JSON structure and required fields
     - `GET /health` - Verify health check response
   - Test both successful responses and error cases
   - Aim for meaningful test coverage (not just basic smoke tests)

3. **Run Tests Locally**
   - Verify all tests pass locally before CI setup
   - Document how to run tests in your README

<details>
<summary>💡 Testing Framework Guidance</summary>

**Popular Python Testing Frameworks:**

**pytest (Recommended):**
- Pros: Simple syntax, powerful fixtures, excellent plugin ecosystem
- Cons: Additional dependency
- Use case: Most modern Python projects

**unittest:**
- Pros: Built into Python (no extra dependencies)
- Cons: More verbose, less modern features
- Use case: Minimal dependency projects

**Key Testing Concepts to Research:**
- Test fixtures and setup/teardown
- Mocking external dependencies
- Testing HTTP endpoints (test client usage)
- Test coverage measurement
- Assertions and expected vs actual results

**What Should You Test?**
- Correct HTTP status codes (200, 404, 500)
- Response data structure (JSON fields present)
- Response data types (strings, integers, etc.)
- Edge cases (invalid requests, missing data)
- Error handling (what happens when things fail?)

**Questions to Consider:**
- How do you test a Flask/FastAPI app without starting the server?
- Should you test that `hostname` returns your actual hostname, or just that the field exists?
- How do you simulate different client IPs or user agents in tests?

**Resources:**
- [Pytest Documentation](https://docs.pytest.org/)
- [Flask Testing](https://flask.palletsprojects.com/en/stable/testing/)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [Python unittest](https://docs.python.org/3/library/unittest.html)

**Anti-Patterns to Avoid:**
- Testing framework functionality instead of your code
- Tests that always pass regardless of implementation
- Tests with no assertions
- Tests that depend on external services

</details>

**What to Document:**
- Your testing framework choice and why
- Test structure explanation
- How to run tests locally
- Terminal output showing all tests passing

---

### Task 2 — GitHub Actions CI Workflow (4 pts)

**Objective:** Create a GitHub Actions workflow that automatically tests your code and builds Docker images with proper versioning.

**Requirements:**

1. **Create Workflow File**
   - Create `.github/workflows/python-ci.yml` in your repository
   - Name your workflow descriptively

2. **Implement Essential CI Steps**

   Your workflow must include these logical stages:

   **a) Code Quality & Testing:**
   - Install dependencies
   - Run a linter (pylint, flake8, black, ruff, etc.)
   - Run your unit tests

   **b) Docker Build & Push with Versioning:**
   - Authenticate with Docker Hub
   - Build your Docker image
   - Tag with proper version strategy (see versioning section below)
   - Push to Docker Hub with multiple tags

3. **Versioning Strategy**

   Choose **one** versioning approach and implement it:

   **Option A: Semantic Versioning (SemVer)**
   - Version format: `v1.2.3` (major.minor.patch)
   - Use git tags for releases
   - Tag images like: `username/app:1.2.3`, `username/app:1.2`, `username/app:latest`
   - **When to use:** Traditional software releases with breaking changes

   **Option B: Calendar Versioning (CalVer)**
   - Version format: `2024.01.15` or `2024.01` (year.month.day or year.month)
   - Based on release date
   - Tag images like: `username/app:2024.01`, `username/app:latest`
   - **When to use:** Time-based releases, continuous deployment

   **Required:**
   - Document which strategy you chose and why
   - Implement it in your CI workflow
   - Show at least 2 tags per image (e.g., version + latest)

4. **Workflow Triggers**
   - Configure when the workflow runs (push, pull request, etc.)
   - Consider which branches should trigger builds

5. **Testing the Workflow**
   - Push your workflow file and verify it runs
   - Fix any issues that arise
   - Ensure all steps complete successfully
   - Verify Docker Hub shows your version tags

<details>
<summary>💡 GitHub Actions Concepts</summary>

**Core Concepts to Research:**

**Workflow Anatomy:**
- `name` - What is your workflow called?
- `on` - When does it run? (push, pull_request, schedule, etc.)
- `jobs` - What work needs to be done?
- `steps` - Individual commands within a job
- `runs-on` - What OS environment? (ubuntu-latest, etc.)

**Key Questions:**
- Should you run CI on every push, or only on pull requests?
- What happens if tests fail? Should the workflow continue?
- How do you access secrets (like Docker Hub credentials) securely?
- Why might you want multiple jobs vs multiple steps in one job?

**Python CI Steps Pattern:**
```yaml
# This is a pattern, not exact copy-paste code
# Research the actual syntax and actions needed

- Set up Python environment
- Install dependencies
- Run linter
- Run tests
```

**Docker CI Steps Pattern:**
```yaml
# This is a pattern, not exact copy-paste code
# Research the actual actions and their parameters

- Log in to Docker Hub
- Extract metadata for tags
- Build and push Docker image
```

**Important Concepts:**
- **Actions Marketplace:** Reusable actions (actions/checkout@v4, actions/setup-python@v5, docker/build-push-action@v6)
- **Secrets:** How to store Docker Hub credentials securely
- **Job Dependencies:** Can one job depend on another succeeding?
- **Matrix Builds:** Testing multiple Python versions (optional but good to know)
- **Caching:** Speed up workflows by caching dependencies (we'll add this in Task 3)

**Resources:**
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Building and Testing Python](https://docs.github.com/en/actions/automating-builds-and-tests/building-and-testing-python)
- [Publishing Docker Images](https://docs.docker.com/ci-cd/github-actions/)
- [GitHub Actions Marketplace](https://github.com/marketplace?type=actions)
- [Workflow Syntax](https://docs.github.com/en/actions/using-workflows/workflow-syntax-for-github-actions)

**Security Best Practices:**
- Never hardcode passwords or tokens in workflow files
- Use GitHub Secrets for sensitive data
- Understand when secrets are exposed to pull requests from forks
- Use `secrets.GITHUB_TOKEN` for GitHub API access (auto-provided)

**Docker Hub Authentication:**
You'll need to create a Docker Hub access token and add it as a GitHub Secret. Research:
- How to create Docker Hub access tokens
- How to add secrets to your GitHub repository
- How to reference secrets in workflow files (hint: `${{ secrets.NAME }}`)

</details>

<details>
<summary>💡 Versioning Strategy Guidance</summary>

**Semantic Versioning (SemVer):**

**Format:** MAJOR.MINOR.PATCH (e.g., 1.2.3)
- **MAJOR:** Breaking changes (incompatible API changes)
- **MINOR:** New features (backward-compatible)
- **PATCH:** Bug fixes (backward-compatible)

**Implementation Approaches:**
1. **Manual Git Tags:** Create git tags (v1.0.0) and reference in workflow
2. **Automated from Commits:** Parse conventional commits to bump version
3. **GitHub Releases:** Trigger on release creation

**Docker Tagging Example:**
- `username/app:1.2.3` (full version)
- `username/app:1.2` (minor version, rolling)
- `username/app:1` (major version, rolling)
- `username/app:latest` (latest stable)

**Pros:** Clear when breaking changes occur, industry standard for libraries
**Cons:** Requires discipline to follow rules correctly

---

**Calendar Versioning (CalVer):**

**Common Formats:**
- `YYYY.MM.DD` (e.g., 2024.01.15) - Daily releases
- `YYYY.MM.MICRO` (e.g., 2024.01.0) - Monthly with patch number
- `YYYY.0M` (e.g., 2024.01) - Monthly releases

**Implementation Approaches:**
1. **Date-based:** Generate from current date in workflow
2. **Git SHA:** Combine with short commit SHA (2024.01-a1b2c3d)
3. **Build Number:** Use GitHub run number (2024.01.42)

**Docker Tagging Example:**
- `username/app:2024.01` (month version)
- `username/app:2024.01.123` (with build number)
- `username/app:latest` (latest build)

**Pros:** No ambiguity, good for continuous deployment, easier to remember
**Cons:** Doesn't indicate breaking changes

---

**How to Implement in CI:**

**Using docker/metadata-action:**
```yaml
# Pattern - research actual syntax
- name: Docker metadata
  uses: docker/metadata-action
  with:
    # Define your tagging strategy here
    # Can reference git tags, dates, commit SHAs
```

**Manual Tagging:**
```yaml
# Pattern - research actual syntax
- name: Generate version
  run: echo "VERSION=$(date +%Y.%m.%d)" >> $GITHUB_ENV

- name: Build and push
  # Use ${{ env.VERSION }} in tags
```

**Questions to Consider:**
- How often will you release? (Daily? Per feature? Monthly?)
- Do users need to know about breaking changes explicitly?
- Are you building a library (use SemVer) or a service (CalVer works)?
- How will you track what's in each version?

**Resources:**
- [Semantic Versioning](https://semver.org/)
- [Calendar Versioning](https://calver.org/)
- [Docker Metadata Action](https://github.com/docker/metadata-action)
- [Conventional Commits](https://www.conventionalcommits.org/) (for automated SemVer)

</details>

<details>
<summary>💡 Debugging GitHub Actions</summary>

**Common Issues & How to Debug:**

**Workflow Won't Trigger:**
- Check your `on:` configuration
- Verify you pushed to the correct branch
- Look at Actions tab for filtering options

**Steps Failing:**
- Click into the failed step to see full logs
- Check for typos in action names or parameters
- Verify secrets are configured correctly
- Test commands locally first

**Docker Build Fails:**
- Ensure Dockerfile is in the correct location
- Check context path in build step
- Verify base image exists and is accessible
- Test Docker build locally first

**Authentication Issues:**
- Verify secret names match exactly (case-sensitive)
- Check that Docker Hub token has write permissions
- Ensure you're using `docker/login-action` correctly

**Debugging Techniques:**
- Add `run: echo "Debug message"` steps to understand workflow state
- Use `run: env` to see available environment variables
- Check Actions tab for detailed logs
- Enable debug logging (add `ACTIONS_RUNNER_DEBUG` secret = true)

</details>

**What to Document:**
- Your workflow trigger strategy and reasoning
- Why you chose specific actions from the marketplace
- Your Docker tagging strategy (latest? version tags? commit SHA?)
- Link to successful workflow run in GitHub Actions tab
- Terminal output or screenshot of green checkmark

---

### Task 3 — CI Best Practices & Security (3 pts)

**Objective:** Optimize your CI workflow and add security scanning.

**Requirements:**

1. **Add Status Badge**
   - Add a GitHub Actions status badge to your `app_python/README.md`
   - The badge should show the current workflow status (passing/failing)

2. **Implement Dependency Caching**
   - Add caching for Python dependencies to speed up workflow
   - Measure and document the speed improvement

3. **Add Security Scanning with Snyk**
   - Integrate Snyk vulnerability scanning into your workflow
   - Configure it to check for vulnerabilities in your dependencies
   - Document any vulnerabilities found and how you addressed them

4. **Apply CI Best Practices**
   - Research and implement at least 3 additional CI best practices
   - Document which practices you applied and why they matter

<details>
<summary>💡 CI Best Practices Guidance</summary>

**Dependency Caching:**

Caching speeds up workflows by reusing previously downloaded dependencies.

**Key Concepts:**
- What should be cached? (pip packages, Docker layers, etc.)
- What's the cache key? (based on requirements.txt hash)
- When does cache become invalid?
- How much time does caching save?

**Actions to Research:**
- `actions/cache` for general caching
- `actions/setup-python` has built-in cache support

**Questions to Explore:**
- Where are Python packages stored that should be cached?
- How do you measure cache hit vs cache miss?
- What happens if requirements.txt changes?

**Status Badges:**

Show workflow status directly in your README.

**Format Pattern:**
```markdown
![Workflow Name](https://github.com/username/repo/workflows/workflow-name/badge.svg)
```

Research how to:
- Get the correct badge URL for your workflow
- Make badges clickable (link to Actions tab)
- Display specific branch status

**CI Best Practices to Consider:**

Research and choose at least 3 to implement:

1. **Fail Fast:** Stop workflow on first failure
2. **Matrix Builds:** Test multiple Python versions (3.12, 3.13)
3. **Job Dependencies:** Don't push Docker if tests fail
4. **Conditional Steps:** Only push on main branch
5. **Pull Request Checks:** Require passing CI before merge
6. **Workflow Concurrency:** Cancel outdated workflow runs
7. **Docker Layer Caching:** Cache Docker build layers
8. **Environment Variables:** Use env for repeated values
9. **Secrets Scanning:** Prevent committing secrets
10. **YAML Validation:** Lint your workflow files

**Resources:**
- [GitHub Actions Best Practices](https://docs.github.com/en/actions/learn-github-actions/usage-limits-billing-and-administration#usage-limits)
- [Caching Dependencies](https://docs.github.com/en/actions/using-workflows/caching-dependencies-to-speed-up-workflows)
- [Security Hardening](https://docs.github.com/en/actions/security-guides/security-hardening-for-github-actions)

</details>

<details>
<summary>💡 Snyk Integration Guidance</summary>

**What is Snyk?**

Snyk is a security tool that scans your dependencies for known vulnerabilities.

**Key Concepts:**
- Vulnerability databases (CVEs)
- Severity levels (low, medium, high, critical)
- Automated dependency updates
- Security advisories

**Integration Options:**

1. **Snyk GitHub Action:**
   - Use `snyk/actions` from GitHub Marketplace
   - Requires Snyk API token (free tier available)
   - Can fail builds on vulnerabilities

2. **Snyk CLI in Workflow:**
   - Install Snyk CLI in workflow
   - Run `snyk test` command
   - More flexible but requires setup

**Setup Steps:**
1. Create free Snyk account
2. Get API token from Snyk dashboard
3. Add token as GitHub Secret
4. Add Snyk step to workflow
5. Configure severity threshold (what level fails the build?)

**Questions to Explore:**
- Should every vulnerability fail your build?
- What if vulnerabilities have no fix available?
- How do you handle false positives?
- When should you break the build vs just warn?

**Resources:**
- [Snyk GitHub Actions](https://github.com/snyk/actions)
- [Snyk Python Example](https://github.com/snyk/actions/tree/master/python)
- [Snyk Documentation](https://docs.snyk.io/integrations/ci-cd-integrations/github-actions-integration)

**Common Issues:**
- Dependencies not installed before Snyk runs
- API token not configured correctly
- Overly strict severity settings breaking builds
- Virtual environment confusion

**What to Document:**
- Your severity threshold decision and reasoning
- Any vulnerabilities found and your response
- Whether you fail builds on vulnerabilities or just warn

</details>

**What to Document:**
- Status badge in README (visible proof it works)
- Caching implementation and speed improvement metrics
- CI best practices you applied with explanations
- Snyk integration results and vulnerability handling
- Terminal output showing improved workflow performance

---

## Bonus Task — Multi-App CI with Path Filters + Test Coverage (2.5 pts)

**Objective:** Set up CI for your compiled language app with intelligent path-based triggers AND add test coverage tracking.

**Part 1: Multi-App CI (1.5 pts)**

1. **Create Second CI Workflow**
   - Create `.github/workflows/<language>-ci.yml` for your Go/Rust/Java app
   - Implement similar CI steps (lint, test, build Docker image)
   - Use language-specific actions and best practices
   - Apply versioning strategy (SemVer or CalVer) consistently

2. **Implement Path-Based Triggers**
   - Python workflow should only run when `app_python/` files change
   - Compiled language workflow should only run when `app_<language>/` files change
   - Neither should run when only docs or other files change

3. **Optimize for Multiple Apps**
   - Ensure both workflows can run in parallel
   - Consider using workflow templates (DRY principle)
   - Document the benefits of path-based triggers

**Part 2: Test Coverage Badge (1 pt)**

4. **Add Coverage Tracking**
   - Install coverage tool (`pytest-cov` for Python, coverage tool for your other language)
   - Generate coverage reports in CI workflow
   - Integrate with codecov.io or coveralls.io (free for public repos)
   - Add coverage badge to README showing percentage

5. **Coverage Goals**
   - Document your current coverage percentage
   - Identify what's not covered and why
   - Set a coverage threshold in CI (e.g., fail if below 70%)

<details>
<summary>💡 Path Filters & Multi-App CI</summary>

**Why Path Filters?**

In a monorepo with multiple apps, you don't want to run Python CI when only Go code changes.

**Path Filter Syntax:**
```yaml
on:
  push:
    paths:
      - 'app_python/**'
      - '.github/workflows/python-ci.yml'
```

**Key Concepts:**
- Glob patterns for path matching
- When to include workflow file itself
- Exclude patterns (paths-ignore)
- How to test path filters

**Questions to Explore:**
- Should changes to README.md trigger CI?
- Should changes to the root .gitignore trigger CI?
- What about changes to both apps in one commit?
- How do you test that path filters work correctly?

**Multi-Language CI Patterns:**

**For Go:**
- actions/setup-go
- golangci-lint for linting
- go test for testing
- Multi-stage Docker builds (from Lab 2 bonus)

**For Rust:**
- actions-rs/toolchain
- cargo clippy for linting
- cargo test for testing
- cargo-audit for security

**For Java:**
- actions/setup-java
- Maven or Gradle for build
- Checkstyle or SpotBugs for linting
- JUnit tests

**Workflow Reusability:**

Consider:
- Reusable workflows (call one workflow from another)
- Composite actions (bundle steps together)
- Workflow templates (DRY for similar workflows)

**Resources:**
- [Path Filters](https://docs.github.com/en/actions/using-workflows/workflow-syntax-for-github-actions#onpushpull_requestpaths)
- [Reusable Workflows](https://docs.github.com/en/actions/using-workflows/reusing-workflows)
- [Starter Workflows](https://github.com/actions/starter-workflows/tree/main/ci)

</details>

<details>
<summary>💡 Test Coverage Tracking</summary>

**What is Test Coverage?**

Coverage measures what percentage of your code is executed by your tests. High coverage = more code is tested.

**Why Coverage Matters:**
- Identifies untested code paths
- Prevents regressions (changes breaking untested code)
- Increases confidence in refactoring
- Industry standard quality metric

**Coverage Tools by Language:**

**Python (pytest-cov):**
```bash
# Install
pip install pytest-cov

# Run with coverage
pytest --cov=app_python --cov-report=xml --cov-report=term

# Generates coverage.xml for upload
```

**Go (built-in):**
```bash
go test -coverprofile=coverage.out ./...
go tool cover -html=coverage.out
```

**Rust (tarpaulin):**
```bash
cargo install cargo-tarpaulin
cargo tarpaulin --out Xml
```

**Java (JaCoCo with Maven/Gradle):**
```bash
mvn test jacoco:report
# or
gradle test jacocoTestReport
```

**Integration Services:**

**Codecov (Recommended):**
- Free for public repos
- Beautiful visualizations
- PR comments with coverage diff
- Setup: Sign in with GitHub, add repo, upload coverage report

**Coveralls:**
- Alternative to Codecov
- Similar features
- Different UI

**Coverage in CI Workflow:**
```yaml
# Pattern for Python (research actual syntax)
- name: Run tests with coverage
  run: pytest --cov=. --cov-report=xml

- name: Upload to Codecov
  uses: codecov/codecov-action@v4
  with:
    file: ./coverage.xml
    token: ${{ secrets.CODECOV_TOKEN }}
```

**Coverage Badge:**
```markdown
![Coverage](https://codecov.io/gh/username/repo/branch/main/graph/badge.svg)
```

**Setting Coverage Thresholds:**

You can fail CI if coverage drops below a threshold:

```yaml
# In pytest.ini or pyproject.toml
[tool:pytest]
addopts = --cov=. --cov-fail-under=70
```

**Questions to Consider:**
- What's a reasonable coverage target? (70%? 80%? 90%?)
- Should you aim for 100% coverage? (Usually no - diminishing returns)
- What code is OK to leave untested? (Error handlers, config, main)
- How do you test hard-to-reach code paths?

**Best Practices:**
- Don't chase 100% coverage blindly
- Focus on testing critical business logic
- Integration points should have high coverage
- Simple getters/setters can be skipped
- Measure coverage trends, not just absolute numbers

**Resources:**
- [Codecov Documentation](https://docs.codecov.com/)
- [pytest-cov Documentation](https://pytest-cov.readthedocs.io/)
- [Go Coverage](https://go.dev/blog/cover)
- [Cargo Tarpaulin](https://github.com/xd009642/tarpaulin)
- [JaCoCo](https://www.jacoco.org/)

</details>

**What to Document:**
- Second workflow implementation with language-specific best practices
- Path filter configuration and testing proof
- Benefits analysis: Why path filters matter in monorepos
- Example showing workflows running independently
- Terminal output or Actions tab showing selective triggering
- **Coverage integration:** Screenshot/link to codecov/coveralls dashboard
- **Coverage analysis:** Current percentage, what's covered/not covered, your threshold

---

## How to Submit

1. **Create Branch:**
   - Create a new branch called `lab03`
   - Develop your CI workflows on this branch

2. **Commit Work:**
   - Add workflow files (`.github/workflows/`)
   - Add test files (`app_python/tests/`)
   - Add documentation (`app_python/docs/LAB03.md`)
   - Commit with descriptive message following conventional commits

3. **Verify CI Works:**
   - Push to your fork and verify workflows run
   - Check that all jobs pass
   - Review workflow logs for any issues

4. **Create Pull Requests:**
   - **PR #1:** `your-fork:lab03` → `course-repo:master`
   - **PR #2:** `your-fork:lab03` → `your-fork:master`
   - CI should run automatically on your PRs

---

## Acceptance Criteria

### Main Tasks (10 points)

**Unit Testing (3 pts):**
- [ ] Testing framework chosen with justification
- [ ] Tests exist in `app_python/tests/` directory
- [ ] All endpoints have test coverage
- [ ] Tests pass locally (terminal output provided)
- [ ] README updated with testing instructions

**GitHub Actions CI (4 pts):**
- [ ] Workflow file exists at `.github/workflows/python-ci.yml`
- [ ] Workflow includes: dependency installation, linting, testing
- [ ] Workflow includes: Docker Hub login, build, and push
- [ ] Versioning strategy chosen (SemVer or CalVer) and implemented
- [ ] Docker images tagged with at least 2 tags (e.g., version + latest)
- [ ] Workflow triggers configured appropriately
- [ ] All workflow steps pass successfully
- [ ] Docker Hub shows versioned images
- [ ] Link to successful workflow run provided

**CI Best Practices (3 pts):**
- [ ] Status badge added to README and working
- [ ] Dependency caching implemented with performance metrics
- [ ] Snyk security scanning integrated
- [ ] At least 3 CI best practices applied
- [ ] Documentation complete (see Documentation Requirements section)

### Bonus Task (2.5 points)

**Part 1: Multi-App CI (1.5 pts)**
- [ ] Second workflow created for compiled language app (`.github/workflows/<language>-ci.yml`)
- [ ] Language-specific linting and testing implemented
- [ ] Versioning strategy applied to second app
- [ ] Path filters configured for both workflows
- [ ] Path filters tested and proven to work (workflows run selectively)
- [ ] Both workflows can run in parallel
- [ ] Documentation explains benefits and shows selective triggering

**Part 2: Test Coverage (1 pt)**
- [ ] Coverage tool integrated (`pytest-cov` or equivalent)
- [ ] Coverage reports generated in CI workflow
- [ ] Codecov or Coveralls integration complete
- [ ] Coverage badge added to README
- [ ] Coverage threshold set in CI (optional but recommended)
- [ ] Documentation includes coverage analysis (percentage, what's covered/not)

---

## Documentation Requirements

Create `app_python/docs/LAB03.md` with these sections:

### 1. Overview
- Testing framework used and why you chose it
- What endpoints/functionality your tests cover
- CI workflow trigger configuration (when does it run?)
- Versioning strategy chosen (SemVer or CalVer) and rationale

### 2. Workflow Evidence
```
Provide links/terminal output for:
- ✅ Successful workflow run (GitHub Actions link)
- ✅ Tests passing locally (terminal output)
- ✅ Docker image on Docker Hub (link to your image)
- ✅ Status badge working in README
```

### 3. Best Practices Implemented
Quick list with one-sentence explanations:
- **Practice 1:** Why it helps
- **Practice 2:** Why it helps
- **Practice 3:** Why it helps
- **Caching:** Time saved (before vs after)
- **Snyk:** Any vulnerabilities found? Your action taken

### 4. Key Decisions
Answer these briefly (2-3 sentences each):
- **Versioning Strategy:** SemVer or CalVer? Why did you choose it for your app?
- **Docker Tags:** What tags does your CI create? (e.g., latest, version number, etc.)
- **Workflow Triggers:** Why did you choose those triggers?
- **Test Coverage:** What's tested vs not tested?

### 5. Challenges (Optional)
- Any issues you encountered and how you fixed them
- Keep it brief - bullet points are fine

---

## Rubric

| Criteria | Points | Description |
|----------|--------|-------------|
| **Unit Testing** | 3 pts | Comprehensive tests, good coverage |
| **CI Workflow** | 4 pts | Complete, functional, automated |
| **Best Practices** | 3 pts | Optimized, secure, well-documented |
| **Bonus** | 2.5 pts | Multi-app CI with path filters |
| **Total** | 12.5 pts | 10 pts required + 2.5 pts bonus |

**Grading:**
- **10/10:** All tasks complete, CI works flawlessly, clear documentation, meaningful tests
- **8-9/10:** CI works, good test coverage, best practices applied, solid documentation
- **6-7/10:** CI functional, basic tests, some best practices, minimal documentation
- **<6/10:** CI broken or missing steps, poor tests, incomplete work

**Quick Checklist for Full Points:**
- ✅ Tests actually test your endpoints (not just imports)
- ✅ CI workflow runs and passes
- ✅ Docker image builds and pushes successfully
- ✅ At least 3 best practices applied (caching, Snyk, status badge, etc.)
- ✅ Documentation complete but concise (no essay needed!)
- ✅ Links/evidence provided (workflow runs, Docker Hub, etc.)

**Documentation Should Take:** 15-30 minutes to write, 5 minutes to review

---

## Resources

<details>
<summary>📚 GitHub Actions Documentation</summary>

- [GitHub Actions Quickstart](https://docs.github.com/en/actions/quickstart)
- [Workflow Syntax](https://docs.github.com/en/actions/using-workflows/workflow-syntax-for-github-actions)
- [Building and Testing Python](https://docs.github.com/en/actions/automating-builds-and-tests/building-and-testing-python)
- [Publishing Docker Images](https://docs.docker.com/ci-cd/github-actions/)
- [GitHub Actions Marketplace](https://github.com/marketplace?type=actions)

</details>

<details>
<summary>🧪 Testing Resources</summary>

- [Pytest Documentation](https://docs.pytest.org/)
- [Flask Testing Guide](https://flask.palletsprojects.com/en/stable/testing/)
- [FastAPI Testing Guide](https://fastapi.tiangolo.com/tutorial/testing/)
- [Python Testing Best Practices](https://realpython.com/python-testing/)

</details>

<details>
<summary>🔒 Security & Quality</summary>

- [Snyk GitHub Actions](https://github.com/snyk/actions)
- [Snyk Python Integration](https://docs.snyk.io/integrations/ci-cd-integrations/github-actions-integration)
- [GitHub Security Best Practices](https://docs.github.com/en/actions/security-guides/security-hardening-for-github-actions)
- [Dependency Scanning](https://docs.github.com/en/code-security/supply-chain-security)

</details>

<details>
<summary>⚡ Performance & Optimization</summary>

- [Caching Dependencies](https://docs.github.com/en/actions/using-workflows/caching-dependencies-to-speed-up-workflows)
- [Docker Build Cache](https://docs.docker.com/build/cache/)
- [Workflow Optimization](https://docs.github.com/en/actions/learn-github-actions/usage-limits-billing-and-administration)

</details>

<details>
<summary>🛠️ CI/CD Tools</summary>

- [act](https://github.com/nektos/act) - Run GitHub Actions locally
- [actionlint](https://github.com/rhysd/actionlint) - Lint workflow files
- [GitHub CLI](https://cli.github.com/) - Manage workflows from terminal

</details>

---

## Looking Ahead

- **Lab 4-6:** CI will validate your Terraform and Ansible code
- **Lab 7-8:** CI will run integration tests with logging/metrics
- **Lab 9-10:** CI will validate Kubernetes manifests and Helm charts
- **Lab 13:** ArgoCD will deploy what CI builds (GitOps!)
- **All Future Labs:** This pipeline is your safety net for changes

---

**Good luck!** 🚀

> **Remember:** CI isn't about having green checkmarks—it's about catching problems before they reach production. Focus on meaningful tests and understanding why each practice matters. Think like a DevOps engineer: automate everything, fail fast, and learn from failures.
