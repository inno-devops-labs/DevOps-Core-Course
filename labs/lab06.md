# Lab 6 — Advanced Ansible & Continuous Deployment

![difficulty](https://img.shields.io/badge/difficulty-intermediate-yellow)
![topic](https://img.shields.io/badge/topic-Ansible%20%26%20CI%2FCD-blue)
![points](https://img.shields.io/badge/points-10%2B2-orange)
![tech](https://img.shields.io/badge/tech-Ansible%202.21%20|%20Docker%20Compose%20v2%20|%20GitHub%20Actions-informational)

> **Goal:** Turn the Lab 5 playbooks into a real deployment pipeline — refactor with `block`/`rescue`/`always`, template a Compose stack with Jinja2, add a double-gated wipe, and push-button deploy from GitHub Actions.
> **Deliverable:** A PR from `lab06` with refactored `ansible/roles/{common,docker,web_app}`, `.github/workflows/ansible-deploy.yml`, and `ansible/docs/LAB06.md` showing real proof (list-tags, rescue fired, idempotent PLAY RECAP).

---

## Overview

In Lab 5 you built roles that **configure** a server. In Lab 6 you make those same roles **deliver** an application — repeatedly, safely, and from CI. You will:

- Refactor `common` and `docker` with `block`/`rescue`/`always` and a deliberate tag taxonomy
- Replace `docker run` with a Jinja2-templated Compose stack via `community.docker.docker_compose_v2`
- Add a clean-reinstall button (`web_app_wipe`) that is gated **twice** so a single typo can't destroy prod
- Wire `.github/workflows/ansible-deploy.yml` to lint → deploy → verify on every push to `ansible/**`

> ⚠️ **Scope:** the lab targets one VM (yours from Lab 4) plus localhost for offline practice. Multi-host rolling rollouts are discussed but proven only structurally — same patterns transfer.

**What stays from Lab 5:** YAML, role layout, inventory, group_vars, Vault. We do **not** re-teach them.

---

## Project State

**You have from previous labs:**
- The DevOps Info Service (Lab 1) on a registry (Lab 2/3)
- A target VM with SSH access (Lab 4)
- Ansible roles `common`, `docker`, `app_deploy`, an inventory, group_vars + Vault (Lab 5)

**This lab adds:**
- `ansible/roles/{common,docker}` refactored with blocks + tags
- `ansible/roles/web_app/` (renamed from `app_deploy`) with `meta/main.yml`, `templates/docker-compose.yml.j2`, `tasks/main.yml`, `tasks/wipe.yml`, `defaults/main.yml`
- `.github/workflows/ansible-deploy.yml`
- `ansible/docs/LAB06.md` — your proof report

---

## Setup

```bash
ansible --version | head -1                  # ansible-core 2.21.x
ansible-galaxy collection install community.docker    # 4.x
ansible-lint --version
docker compose version                       # v2.x (the plugin, NOT docker-compose v1)
```

Rename the Lab 5 role before you start — the new name lines up with the wipe variable in Task 3:

```bash
cd ansible/roles && git mv app_deploy web_app
# update every reference: playbook roles:, group_vars keys, docs
```

---

## Task 1 — Refactor with Blocks & Tags (2 pts)

Lab 5's `common` and `docker` were linear task lists. You will restructure them so that (a) a transient apt/GPG flake doesn't kill the run, (b) you can target a single phase from the CLI, and (c) the `systemd` enable step runs **even when the install fails**.

### 1.1 Tag strategy (three axes)

Adopt three orthogonal tag axes and apply them consistently across both roles. This is the single decision that decides whether `--tags` is useful or noise.

| Axis | Tag names you must use | Used for |
|------|------------------------|----------|
| Component | `common`, `docker`, `web_app` | "Touch one role only" |
| Action | `install`, `config`, `deploy`, `wipe` | "Run one phase across roles" |
| Risk gate | `web_app_wipe` | Dangerous, opt-in only (Task 3) |

`YOUR TASK`: in `ansible/docs/LAB06.md`, write a 3-line table showing which two-or-three tags each block gets. Example row: *"`roles/docker` install block → `[docker, docker_install, install]`."* This forces you to commit to the taxonomy **before** sprinkling tags.

### 1.2 Refactor the `docker` role

**File:** `roles/docker/tasks/main.yml`

Group the apt-key + repo + `docker-ce` install in a block. Give it a `rescue` that handles a flaky mirror/GPG fetch, and an `always` that guarantees the service is enabled — cleanup is sacred, it must run whether the install succeeded or not.

`YOUR TASK`: fill in the shape below. Hints in the comments — do not paste solutions from Lab 5 unchanged; you are restructuring them.

```yaml
- name: ___                                    # YOUR TASK: name the parent block
  block:
    - name: ___                                # YOUR TASK: add Docker apt GPG key
      ___:                                     # YOUR TASK: pick the right ansible.builtin module
        ___                                    # YOUR TASK: its args

    - name: ___                                # YOUR TASK: add Docker apt repo
      ___:
        ___

    - name: Install docker-ce
      ansible.builtin.apt:
        name: docker-ce
        update_cache: true
  rescue:
    - name: ___                                # YOUR TASK: what's a sensible recovery
                                               #            for a flaky mirror/GPG fetch?
      ___:
        ___
      retries: ___                             # YOUR TASK: pick a small int, justify in docs
      delay: ___
  always:
    - name: ___                                # YOUR TASK: ensure dockerd enabled + started
      ___:
        ___
  become: true
  tags: [___, ___, ___]                        # YOUR TASK: pick three tags from the taxonomy
```

> A tag on a `block` inherits to every task inside — do **not** re-tag each task. Lift `become: true` to the block, do not repeat it. If the `rescue` also fails, the host is marked failed and `always` still runs.

### 1.3 Refactor the `common` role

**File:** `roles/common/tasks/main.yml`

Apply the same shape with these requirements:
- The block installs your Lab 5 baseline packages (curl, gnupg, ca-certificates, …).
- `rescue` runs `apt-get update --fix-missing` then retries.
- `always` writes a small completion marker to `/tmp/lab6-common-ran` so you can prove the block executed end-to-end.
- Tags follow the taxonomy. Lift `become: true` to the block.

`YOUR TASK`: write the file. Same shape as 1.2, different module choices (`apt` package list, `command`/`shell` for the marker — pick the right one and justify).

### 1.4 Prove a `rescue` actually fires

It's easy to write `rescue:` and never exercise it — and an unproven rescue path is worse than no rescue at all (you'll find out it doesn't work the day you need it).

`YOUR TASK`: deliberately break a task inside one of your blocks **once** (e.g. point an `apt_repository` at `http://does-not-exist.example.com/` for a single run), confirm the rescue runs, then revert. Capture the **rescue task's output** in the proof section — the recap line `rescued=1` alone is not enough.

### 1.5 Verify selective execution

```bash
ansible-playbook playbooks/provision.yml --list-tags
ansible-playbook playbooks/provision.yml --tags docker_install
ansible-playbook playbooks/provision.yml --skip-tags common
ansible-playbook playbooks/provision.yml --tags docker --check     # dry-run
```

### 1.6 Proof of work — paste into `docs/LAB06.md`

- The **`--list-tags` output**, unedited. Must show your three-axis taxonomy.
- One **selective `--tags`** run showing **most tasks skipped** (not "all 12 ran with tag=docker_install").
- The **rescue path output** from 1.4 — the actual task name + result, not just `PLAY RECAP`.
- Your taxonomy table from 1.1.

**Research (answer in your docs):**
- How do tags inherit from a `block` into its tasks? Do tags on the role import combine or override?
- Difference between the special `never` tag and a normal opt-in tag like `web_app_wipe`?
- What happens to a host's downstream tasks when its `rescue` also fails?

---

## Task 2 — Upgrade to Docker Compose (3 pts)

Replace the Lab 5 `docker run` with a Jinja2-templated Compose stack, applied via `community.docker.docker_compose_v2`. The win is declarative state + free idempotency: re-running with the same rendered file shows `changed=0`.

### 2.1 Declare the role dependency

**File:** `roles/web_app/meta/main.yml`

A `meta/main.yml` dependency makes `web_app` pull in `docker` automatically, in the right order, exactly once per play. You do not need a second `roles:` entry in your playbook.

`YOUR TASK`: write this file. The shape:

```yaml
---
dependencies:
  - role: ___                                  # YOUR TASK: which role must run first?
    vars:
      ___: ["{{ ansible_user }}"]              # YOUR TASK: variable name from your
                                               #            Lab 5 docker role
```

### 2.2 Template the Compose file

**File:** `roles/web_app/templates/docker-compose.yml.j2`

**Target render:** a working `docker-compose.yml` for **one** service that:
- pulls `{{ docker_image }}:{{ docker_tag }}`,
- publishes `{{ app_host_port }}:{{ app_internal_port }}`,
- injects every key/value from `{{ app_env }}` (a dict from group_vars) as environment variables,
- restarts per `{{ restart_policy }}` (default `unless-stopped` — use a Jinja filter),
- ships a **healthcheck** hitting `/health` on `{{ app_internal_port }}` so `docker compose ps` shows `(healthy)`.

You must use **all three** Jinja2 mechanisms:
1. `{{ var }}` interpolation
2. At least one `{% if %}` block (e.g. skip `environment:` when `app_env` is empty)
3. At least one filter chain (e.g. `| default('...')` or `| to_nice_yaml`)

`YOUR TASK`: write the template. The shape (intentionally incomplete — fill the body):

```jinja
{# Compose v2 — NO top-level `version:` field (dropped in 2023) #}
services:
  {{ ___ }}:                                   # YOUR TASK: service name var
    image: ___                                 # YOUR TASK: image:tag, two vars
    container_name: ___
    ports:
      - "___:___"                              # YOUR TASK: host:container, two vars
{% if ___ %}                                   # YOUR TASK: only render env block when app_env non-empty
    environment:
{% for ___, ___ in ___ %}                      # YOUR TASK: iterate the dict
      ___: "___"
{% endfor %}
{% endif %}
    restart: {{ ___ | default('___') }}        # YOUR TASK: var + the default value
    healthcheck:
      test: ___                                # YOUR TASK: curl/wget the in-container /health
      interval: ___                            # YOUR TASK: sensible default
      timeout: ___
      retries: ___
```

> Compose v2 dropped the top-level `version:` key — if a tutorial still writes `version: '3.8'`, it predates 2023. Leave it off. Test the render locally with `ansible all -i localhost, -m template -a "src=... dest=/tmp/out.yml"` before running the full play.

### 2.3 Implement the deploy tasks

**File:** `roles/web_app/tasks/main.yml`

The shape — fill the bodies:

```yaml
---
- name: Include wipe tasks (gated — Task 3)
  ansible.builtin.include_tasks: wipe.yml
  tags: [web_app, web_app_wipe]

- name: ___                                    # YOUR TASK: name the deploy block
  block:
    - name: Create project directory
      ansible.builtin.file:
        path: "{{ compose_project_dir }}"
        state: directory
        mode: "0755"
      # NOTE: an aborted previous run can leave /tmp/<project> as a FILE — see Common Pitfalls

    - name: Render compose file
      ansible.builtin.template:
        src: ___                               # YOUR TASK: which template?
        dest: "___/docker-compose.yml"         # YOUR TASK: where on the target?
        mode: "0644"

    - name: ___                                # YOUR TASK: name this — "docker compose up -d"
      ___:                                     # YOUR TASK: the FQCN module — NOT the v1 module
                                               #            (Common Pitfalls: v1 vs v2)
        project_src: "{{ compose_project_dir }}"
        state: ___                             # YOUR TASK: which state means "up"?
        pull: ___
        remove_orphans: ___

    - name: Smoke test /health
      ansible.builtin.uri:
        url: "___"                             # YOUR TASK: build the URL from app_host_port
        status_code: 200
      register: hc
      retries: ___                             # YOUR TASK: bounded, not infinite
      delay: ___
      until: ___                               # YOUR TASK: condition on hc
  rescue:
    - name: ___                                # YOUR TASK: surface the failure
                                               #            (debug, fail, slack — your call)
      ___:
  tags: [___, ___, ___]                        # YOUR TASK: three tags from the taxonomy
```

Setup notes (these don't need YOUR-TASK; they are plumbing):
- Collection installed on the **controller**: `ansible-galaxy collection install community.docker`.
- `python3-docker` on the **target** (your `docker` role does this).
- Re-running the same play with no changes must show `changed=0`. If it doesn't, something in your template depends on a mutable input (timestamp, random, unsorted dict iteration).

### 2.4 Variables

**File:** `roles/web_app/defaults/main.yml`

`YOUR TASK`: declare the defaults. The keys you need: `app_name`, `docker_image`, `docker_tag`, `app_host_port`, `app_internal_port`, `compose_project_dir`, `restart_policy`, `app_env`. Use sensible defaults. **Do not** default `docker_tag` to `latest` for prod — pin it per-env in `group_vars`. Keep real secrets in your Lab 5 Vault file (`group_vars/.../vault.yml`) and merge them into `app_env` from there.

### 2.5 Verify

```bash
ansible-playbook playbooks/deploy.yml --tags deploy     # run #1: changed
ansible-playbook playbooks/deploy.yml --tags deploy     # run #2: ok (changed=0)
docker compose -f /opt/<app>/docker-compose.yml ps      # (healthy)
curl -fsS http://<VM-IP>:<port>/health | jq .
```

### 2.6 Proof of work — paste into `docs/LAB06.md`

- The **rendered** `docker-compose.yml` (post-template) — at least the first 20 lines.
- Both PLAY RECAPs side-by-side — run #1 `changed≥1`, run #2 `changed=0`. **This is the idempotency proof.** A second run that still shows `changed=2` means your template renders differently each time (sort your dict keys, drop timestamps).
- `docker compose ps` showing `(healthy)`.
- `curl /health` output with your real hostname/uptime.

**Research:**
- `restart: always` vs `unless-stopped` — when does the difference actually bite?
- Why does `python3-docker` go on the **target**, not the controller?
- Why is one templated Compose file better than N `docker run` tasks?

---

## Task 3 — Double-Gated Wipe Logic (2 pts)

A clean reinstall is sometimes the only safe rollback: corrupted volume, rotated secret, broken cache. You need the button, **and** you need it gated so a sleepy 2am `--tags` typo can't destroy prod.

### 3.1 The double gate

Two **independent** gates: a `when:` variable check **and** an opt-in tag. Both must align for the wipe to run.

| Invocation | Wipe? | Why |
|------------|-------|-----|
| `deploy.yml` | No | var false, tag not requested |
| `deploy.yml --tags web_app_wipe` | No | `when` blocks it (var still false) |
| `deploy.yml -e web_app_wipe=true` | Yes — wipe **then** deploy | clean reinstall |
| `deploy.yml -e web_app_wipe=true --tags web_app_wipe` | Yes — wipe **only** | deploy tasks skipped by tag |

> The special `never` tag alone is not enough — a typo in `--tags never` is one character away from `--tags ever`. Two **independent** gates: a typo in one cannot also flip the other.

### 3.2 Implement

**File:** `roles/web_app/tasks/wipe.yml`

The shape:

```yaml
---
- name: Wipe web application
  block:
    - name: ___                                # YOUR TASK: name it — "compose down"
      ___:                                     # YOUR TASK: which module?
        project_src: "{{ compose_project_dir }}"
        state: ___                             # YOUR TASK: which state removes it?
      failed_when: ___                         # YOUR TASK: be tolerant when dir doesn't exist yet
                                               #            (already-clean case)

    - name: ___                                # YOUR TASK: remove the project dir
      ___:
        path: "___"
        state: ___

    - name: ___                                # YOUR TASK: small completion debug
      ___:
        msg: "___"
  when: ___ | bool                             # YOUR TASK: gate #1 — variable
                                               #            (why is `| bool` mandatory?
                                               #             see Common Pitfalls)
  tags: [___, ___]                             # YOUR TASK: gate #2 — opt-in tag
```

**File:** `roles/web_app/defaults/main.yml` — add:

```yaml
web_app_wipe: ___                              # YOUR TASK: safe default — what should it be?
```

The `include_tasks: wipe.yml` line from Task 2.3 sits **before** the deploy block, so `-e web_app_wipe=true` gives you wipe-then-deploy in one run.

### 3.3 Verify all four rows

`YOUR TASK`: run each of the four invocations in §3.1 and capture the output. For each, prove what you claim:
- Row 1 (plain `deploy.yml`) — search the recap or `--list-tasks` output for the wipe tasks; they should be skipped.
- Row 2 (`--tags web_app_wipe` alone) — the wipe tasks **enter** the play but the `when:` skips them. The recap shows `skipped`, not `ok`.
- Row 3 (`-e web_app_wipe=true`) — `docker ps` before (running) → `docker ps` after the wipe inside the run (gone) → after deploy (running again, fresh container ID).
- Row 4 (`-e ... --tags web_app_wipe`) — wipe runs, deploy tasks skipped by tag, `docker ps` ends empty.

### 3.4 Proof of work — paste into `docs/LAB06.md`

- Four terminal captures, one per row, each labelled with the invocation.
- `docker ps --filter name=<app>` immediately before and immediately after the wipe-only run.
- A one-line note explaining **why `| bool` is mandatory** on the `when:`. (Spoiler in Common Pitfalls if you're stuck.)

---

## Task 4 — CI/CD with GitHub Actions (3 pts)

Automate the whole thing: push to `main` → lint → deploy → verify. Prefer **OIDC short-lived credentials** to a long-lived SSH key where the target supports it.

### 4.1 Workflow skeleton

**File:** `.github/workflows/ansible-deploy.yml`

The shape — fill the bodies:

```yaml
name: Ansible Deploy

on:
  push:
    branches: [main]
    paths:
      - '___'                                  # YOUR TASK: trigger on ansible/** changes
      - '!___'                                 # YOUR TASK: exclude docs-only changes
      - '___'                                  # YOUR TASK: self-test on workflow file edits
  workflow_dispatch:                           # manual deploys

permissions:
  contents: read
  id-token: ___                                # YOUR TASK: which value enables OIDC?

jobs:
  lint:
    runs-on: ubuntu-24.04
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - run: pip install '___' ___             # YOUR TASK: pin ansible-core to 2.21.* + ansible-lint
      - run: ___                               # YOUR TASK: lint the ansible/ tree

  deploy:
    needs: ___                                 # YOUR TASK: depend on lint
    runs-on: ubuntu-24.04
    environment: ___                           # YOUR TASK: GH Environment name
                                               #            (gives you approval + per-env secrets)
    steps:
      - uses: actions/checkout@v4
      # YOUR TASK: pick ONE auth tier from §4.2 and run the playbook + smoke test
```

> Pin `ansible-core==2.21.*` so CI matches your local lockfile. ansible-core has **no LTS label** — pin the exact minor that matches your `community.docker` 4.x collection.

### 4.2 Pick an auth tier

| Tier | Mechanism | Trade-off |
|------|-----------|-----------|
| Repo secret as env | `secrets.SSH_KEY` → `~/.ssh/id_ed25519` | Simple; a long-lived key is the new "password in source" |
| GitHub Environment | Per-env secrets + manual approval | Needed for prod; small ops overhead |
| **OIDC + cloud IAM** | Short-lived federated token, no static key | Recommended where the target supports it |

`YOUR TASK`: pick one, implement it. Justify your choice in the docs in 2–3 sentences referencing the trade-offs above. The skeletons:

**OIDC (recommended):**

```yaml
      - uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: ___                  # YOUR TASK: an IAM role ARN trusting GH OIDC
          aws-region: ___
      - name: Deploy
        run: |
          ___                                  # YOUR TASK: ansible-playbook against your inventory
```

**SSH-in-secret (fallback):**

```yaml
      - env:
          VAULT: ${{ secrets.VAULT_PASS }}
          SSH:   ${{ secrets.SSH_KEY }}
        run: |
          install -m 600 /dev/stdin ~/.ssh/id_ed25519 <<< "$SSH"
          install -m 600 /dev/stdin /tmp/vault        <<< "$VAULT"
          ___                                  # YOUR TASK: ansible-playbook with --vault-password-file
```

> Never echo a secret to the log (no `run: echo "$SSH"` for debugging — pipe it into a file with redirected stdin, like the install above). A self-hosted runner on the target network removes the SSH key entirely — but it is a trust boundary, **never** run it on PRs from forks.

### 4.3 Verify in CI, not just exit 0

`ansible-playbook` returning 0 only means the playbook ran without errors — it does **not** mean the app responds. Add a smoke-test step.

`YOUR TASK`: write a step that polls `/health` up to N times (you pick a bounded N), exits 0 on first 200, exits 1 if it never comes up. Use plain shell, not a third-party action. Hint: `curl -fsS` returns non-zero on non-2xx; pair it with a small retry loop.

Add the status badge to your repo `README.md`:

```markdown
[![Ansible Deploy](https://github.com/<you>/<repo>/actions/workflows/ansible-deploy.yml/badge.svg)](https://github.com/<you>/<repo>/actions/workflows/ansible-deploy.yml)
```

### 4.4 Deployment strategy

`serial:` on a play caps how many hosts deploy **at the same moment**. It does NOT mean "deploy to 25% of hosts and stop" — see Common Pitfalls.

```yaml
- name: Deploy web tier
  hosts: webservers
  serial: "___"                                # YOUR TASK: pick one — explain the meaning
                                               #            in your docs (rolling vs canary vs all)
  max_fail_percentage: ___                     # YOUR TASK: pick a small int, justify
  roles: [web_app]
```

| Strategy | Typical `serial:` | When |
|----------|-------------------|------|
| Rolling | `1` or `25%` | Zero-downtime behind a load balancer |
| Canary | `1` (first batch, then observe) | Test on one host before continuing |
| All-at-once | omit `serial:` | Dev/staging only |

In your docs: which strategy did you pick for prod, and why?

### 4.5 Proof of work — paste into `docs/LAB06.md`

- A screenshot (or pasted log block) of a green workflow run.
- Log lines showing **ansible-lint passing** (not skipped, not all-warnings).
- The smoke-test step output (curl 200).
- The passing status badge URL.
- 2–3 sentences justifying your `serial:` + auth-tier choices.

**Research:**
- Security implications: long-lived SSH key in a repo secret vs OIDC + cloud IAM. What's the blast radius if each leaks?
- How would you add a rollback job that triggers on the verify step failing? Sketch the YAML.
- Why must a self-hosted runner never execute jobs from fork PRs?

---

## Bonus — Multi-Environment Promotion (2 pts)

> Single bonus task (2 pts). Promote **one immutable image** through `staging` → `prod` using per-environment inventories and a manual approval gate. Same artifact, never rebuilt, never retagged.

Build on your Task 4 workflow. The whole point: the identical image (pinned by SHA or SemVer, **not** `:latest`) flows to staging automatically, then to prod only after a human approves.

`YOUR TASK`:

1. **Two inventories** with per-env pinned `docker_tag` (staging leads, prod lags):

   ```
   ansible/inventories/
     staging/hosts.ini   group_vars/all.yml   docker_tag: ___        # YOUR TASK: rc tag
     prod/hosts.ini      group_vars/all.yml   docker_tag: ___        # YOUR TASK: pinned older tag
   ```

   Per-env Vault files. Do **not** branch the playbook on `inventory_hostname == 'prod'` — branch on **variables only**.

2. **Promotion workflow** — extend `ansible-deploy.yml` (or add `ansible-promote.yml`):
   - `deploy-staging` runs automatically on push to `main` against `inventories/staging`.
   - `deploy-prod` `needs: deploy-staging`, uses `environment: production` with a **required reviewer**, targets `inventories/prod`.
   - The **same** `docker_image` flows to both; only `docker_tag` differs per env.
   - Prod uses `serial:` + `max_fail_percentage:` from Task 4.4.

   Skeleton:

   ```yaml
   deploy-prod:
     needs: ___                                # YOUR TASK
     environment: ___                          # YOUR TASK: env name with required reviewer
     runs-on: ubuntu-24.04
     steps:
       - uses: actions/checkout@v4
       # YOUR TASK: assume creds (auth tier from Task 4.2), then:
       #   - run deploy.yml -i ansible/inventories/prod
       #   - smoke-test /health on a prod host
   ```

3. **Verify** end to end:
   - Staging deploy auto-runs on push.
   - Prod job **pauses** for approval (screenshot the GitHub UI showing the gate).
   - Both envs serve the expected (different) tags via `/health` or a `?version=` field.

**Proof:** the two `group_vars/all.yml` files with different pinned tags, the prod approval gate screenshot, and `curl` output proving each env runs its pinned version.

---

## How to Submit

```bash
git switch -c lab06
git add ansible/ .github/workflows/ansible-deploy.yml ansible/docs/LAB06.md
git commit -m "feat(lab06): advanced ansible — blocks, tags, compose, CI"
git push -u origin lab06
```

Confirm `.vault_pass` and any unencrypted secret are **not** staged. Encrypted Vault files are fine to commit.

Open **two** PRs:
- `your-fork:lab06` → `course-repo:master` *(reviewed)*
- `your-fork:lab06` → `your-fork:master` *(merges into your own main when done)*

PR checklist:

```text
- [ ] Task 1 — roles refactored, --list-tags + selective --tags captured, rescue fired
- [ ] Task 2 — Compose templated, idempotent (changed=0 on run #2), /health 200
- [ ] Task 3 — all four wipe rows verified, | bool justified
- [ ] Task 4 — workflow green, ansible-lint, smoke test, badge
- [ ] Bonus — two-env promotion behind required reviewer (optional)
```

---

## Acceptance Criteria

### Main Tasks (10 pts)

**Blocks & Tags (2 pts):**
- ✅ `docker` and `common` refactored with `block`/`rescue`/`always`
- ✅ Three-axis tag taxonomy applied to every block
- ✅ `--list-tags` output + one selective `--tags` run captured
- ✅ Rescue path demonstrably **fired** (task output, not just `rescued=1`)

**Docker Compose (3 pts):**
- ✅ `app_deploy` renamed to `web_app`, all references updated
- ✅ `meta/main.yml` declares the `docker` dependency
- ✅ Jinja2 template uses interpolation **+** `{% if %}` **+** at least one filter
- ✅ Deployed via `community.docker.docker_compose_v2`; both runs captured (changed → 0)
- ✅ App reachable on `/health`; container shows `(healthy)`

**Wipe Logic (2 pts):**
- ✅ Gated by `when: web_app_wipe | bool` **and** the `web_app_wipe` tag
- ✅ Included **before** the deploy block (clean reinstall works in one run)
- ✅ All four invocation rows captured

**CI/CD (3 pts):**
- ✅ Workflow runs `ansible-lint` then deploy
- ✅ Path filters configured (docs excluded; workflow self-test)
- ✅ Auth via OIDC or GitHub Environment secret (no secret echoed)
- ✅ Smoke-test step + passing badge
- ✅ `serial:` chosen and justified

### Bonus (2 pts)
- ✅ Separate `staging` / `prod` inventories with per-env pinned `docker_tag`
- ✅ Same immutable image promoted (no rebuild, no `:latest`)
- ✅ Prod behind a required-reviewer Environment
- ✅ Rolling rollout with `serial:` + `max_fail_percentage:`
- ✅ Evidence both envs serve their pinned versions

---

## Rubric

| Task | Points | Criteria |
|------|-------:|----------|
| **Task 1** — Blocks & Tags | **2** | block/rescue/always; three-axis tags; rescue fired with output |
| **Task 2** — Docker Compose | **3** | renamed role + meta dep; Jinja2 (vars+if+filter); idempotent |
| **Task 3** — Wipe Logic | **2** | double-gated; all four rows verified |
| **Task 4** — CI/CD | **3** | lint → deploy → verify; OIDC/Environment auth; serial justified |
| **Bonus** — Multi-Env Promotion | **2** | immutable image; required-reviewer gate; both envs proven |
| **Total** | **12** | 10 main + 2 bonus |

**Grading scale:**
- **10/10:** Everything works; rescue + wipe + idempotency all proven; CI verifies; sharp docs.
- **8–9/10:** All works; minor gaps in proof or docs.
- **6–7/10:** Core deploy works; weak tag strategy, missing rescue proof, or thin CI verify.
- **<6/10:** Missing Compose deploy, ungated wipe, or no working workflow.

---

## Resources

<details>
<summary>📚 Documentation</summary>

- [Ansible Blocks (error handling)](https://docs.ansible.com/ansible/latest/playbook_guide/playbooks_blocks.html)
- [Ansible Tags](https://docs.ansible.com/ansible/latest/playbook_guide/playbooks_tags.html)
- [Role dependencies](https://docs.ansible.com/ansible/latest/playbook_guide/playbooks_reuse_roles.html#using-role-dependencies)
- [`community.docker.docker_compose_v2`](https://docs.ansible.com/ansible/latest/collections/community/docker/docker_compose_v2_module.html)
- [Compose file reference](https://docs.docker.com/reference/compose-file/)
- [Jinja2 templating](https://jinja.palletsprojects.com/)
- [GHA `paths` filters](https://docs.github.com/en/actions/using-workflows/triggering-a-workflow#using-filters)
- [GitHub OIDC for cloud deploys](https://docs.github.com/en/actions/deployment/security-hardening-your-deployments/about-security-hardening-with-openid-connect)
- [Environments & required reviewers](https://docs.github.com/en/actions/deployment/targeting-different-environments/using-environments-for-deployment)

</details>

<details>
<summary>⚠️ Common Pitfalls (from real dry-runs)</summary>

- **Stale `/tmp/<project>` as a file blocks `state: directory`.** An aborted previous run can leave the project path as a file (or a symlink to one). The `file: state=directory` task fails with *"file exists, refusing to overwrite"*. Fix: `rm -rf <dir>` once, then re-run; or add an explicit `file: state=absent` before the create (only safe if your wipe doesn't depend on contents).
- **Compose v2 vs v1 module names.** `community.docker.docker_compose` (v1, deprecated) and `community.docker.docker_compose_v2` (current) look one underscore apart. v1 shells out to the dead `docker-compose` Python CLI and errors with *"docker-compose: command not found"* on a fresh Ubuntu 24.04. **Always use `docker_compose_v2`.**
- **FQCN vs bare module name.** `ansible-lint` flags `apt:` / `file:` / `template:` as `fqcn[action-core]`. Use `ansible.builtin.apt`, `ansible.builtin.file`, `ansible.builtin.template`. CI will fail your PR otherwise.
- **`serial: "50%"` semantics.** `serial` caps **concurrent** hosts, not total. With 10 hosts and `serial: "50%"`, Ansible runs **two batches of 5** — every host eventually gets the new version. It is **not** "deploy to 50% and stop." For a true canary, use `serial: [1, 5, "100%"]` (a list — first batch is 1, then 5, then the rest).
- **`-e web_app_wipe=true` is a STRING.** Without `| bool`, the `when` evaluates `"true"` — which is truthy as a non-empty string, so `when: web_app_wipe` would also pass `when: web_app_wipe="false"`. The `| bool` filter coerces `"true"`/`"false"`/`"yes"`/`"no"` to real booleans. Forget it and the gate is broken in the most dangerous direction.
- **`| default('latest')` in production.** Convenient for dev, fatal in prod — re-deploying with `docker_tag=latest` silently picks up whatever was pushed to the registry since. Pin per-env in `group_vars`. The Bonus task makes this explicit.
- **`become: true` repeated per task.** Lift it to the `block`; tagging the block also tags every task inside. Less noise, fewer drift bugs.

</details>

<details>
<summary>🛠️ Dev tools worth knowing</summary>

- `ansible-lint` — runs in CI; matches it locally first to save round-trips
- `ansible-playbook --list-tasks --list-tags --list-hosts` — three flags, no execution; ideal for pre-flight checks
- `ansible-doc -t filter -l` — every Jinja2 filter that ships with ansible-core
- `jq` — pair with `community.docker.docker_compose_v2` `register:`-ed output

</details>

---

## Looking Ahead

You've shipped the app — next labs see and measure it:

| Lab | What it adds to this service |
|---:|---|
| 7 | Loki + Alloy logging — deploy the stack with the very patterns from this lab |
| 8 | Prometheus `/metrics`, instrumented endpoints, RED-method PromQL |
| 9 | Kubernetes (k3d) — migrate from Compose to K8s, reusing `/health` |
| 10 | Helm 4 charts for templated K8s deploys |
| 13 | ArgoCD — declarative, pull-based GitOps |
| 14 | Argo Rollouts — canary + blue/green for the same service |

---

**Good luck.** Block gives you the error boundary, tag gives you the scalpel, Compose gives you the declarative state, CI gives you the button — and the double gate keeps the button from going off by itself.
