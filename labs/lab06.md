# Lab 6 — Advanced Ansible & Continuous Deployment

![difficulty](https://img.shields.io/badge/difficulty-intermediate-yellow)
![topic](https://img.shields.io/badge/topic-Ansible%20%26%20CI%2FCD-blue)
![points](https://img.shields.io/badge/points-10%2B2-orange)
![tech](https://img.shields.io/badge/tech-Ansible%202.21%20|%20Docker%20Compose%20v2%20|%20GitHub%20Actions-informational)

> Turn the Lab 5 playbooks into a real deployment pipeline: refactor with `block`/`rescue`/`always` and a tag strategy, template a `docker-compose.yml` with Jinja2, add double-gated wipe logic, then push-button deploy from GitHub Actions with OIDC and a rollout strategy.

## Overview

In Lab 5 you built roles that **configure** a server. In Lab 6 you make those roles **deliver** an application — repeatedly, safely, and from CI. You refactor `common` and `docker` with blocks and tags, replace the `docker run` deploy with a Jinja2-templated Docker Compose stack via `community.docker.docker_compose_v2`, add a clean-reinstall (`web_app_wipe`) button, and wire `.github/workflows/ansible-deploy.yml` to lint → deploy → verify on every push to `ansible/**`.

**What You'll Learn:**
- `block` / `rescue` / `always` for fail-fast, self-healing tasks
- A maintainable tag strategy (component / action / risk axes)
- Jinja2-templated Docker Compose + `community.docker.docker_compose_v2`
- Double-gated wipe logic (variable AND tag)
- GitHub Actions for Ansible: secrets, OIDC, path filters, verification
- Deployment strategies with `serial:` and `max_fail_percentage:`

**Tech Stack:** ansible-core **2.21** | Docker Compose **v2** | `community.docker` **4.x** | GitHub Actions (ubuntu-24.04) | Jinja2

**Prerequisites:** Lab 5 completed (roles `common`, `docker`, `app_deploy`; inventory; group_vars; Ansible Vault), a target VM from Lab 4, your containerized app on a registry from Labs 2–3.

> All command output and workflow logs in this lab are **illustrative skeletons** — your real values, hostnames, and timings will differ. Skeletons contain `# YOUR-TASK:` markers where you must write the implementation yourself.

---

## Tasks

Main tasks total **10 pts**. The bonus is a single task worth **2 pts**.

### Task 1 — Refactor with Blocks & Tags (2 pts)

Take the linear task lists from Lab 5's `common` and `docker` roles and restructure them with blocks and a deliberate tag taxonomy.

#### 1.1 Tag strategy

Adopt **three tag axes** and apply them consistently:

| Axis | Tag names | Used for |
|------|-----------|----------|
| Component | `common`, `docker`, `web_app` | Touch one role only |
| Action | `install`, `config`, `deploy`, `wipe` | Pick a phase across roles |
| Risk gate | `web_app_wipe` | Dangerous, opt-in only (Task 3) |

#### 1.2 Refactor the `docker` role

**File:** `roles/docker/tasks/main.yml`

Group install tasks in a block with a `rescue` that retries on a flaky GPG/mirror fetch, and an `always` that guarantees the service is enabled.

```yaml
- name: Install Docker engine
  block:
    # YOUR-TASK: add the apt key + repo + docker-ce install tasks from Lab 5
    - ansible.builtin.apt:
        name: docker-ce
        update_cache: true
  rescue:
    - name: Mirror/GPG flake — retry once
      ansible.builtin.apt:
        name: docker-ce
        update_cache: true
      retries: 3
      delay: 10
  always:
    - name: Ensure Docker is enabled
      ansible.builtin.systemd:
        name: docker
        enabled: true
        state: started
  become: true
  tags: [docker, docker_install, install]
```

> A tag on a `block` inherits to every task inside — you do not re-tag each task. `rescue` is not "ignore errors"; it is a recovery plan. If `rescue` also fails, the host is marked failed and `always` still runs.

#### 1.3 Refactor the `common` role

**File:** `roles/common/tasks/main.yml`

Apply the same pattern:
- Group package installation in a block tagged `[common, packages, install]`.
- `rescue`: run `apt-get update --fix-missing` then retry on a cache failure.
- `always`: write a small completion marker to `/tmp` so you can prove the block ran.
- Lift `become: true` to the block level instead of repeating per task.

#### 1.4 Verify selective execution

```bash
ansible-playbook playbooks/provision.yml --list-tags          # enumerate tags
ansible-playbook playbooks/provision.yml --tags docker_install # install slice only
ansible-playbook playbooks/provision.yml --skip-tags common    # everything but common
ansible-playbook playbooks/provision.yml --tags docker --check  # dry-run
```

**Evidence:** `--list-tags` output, one selective `--tags` run, and proof a `rescue` path ran at least once (e.g. temporarily point the apt repo at a bad mirror).

**Research (answer in your docs):**
- How do tags inherit into tasks inside a block?
- What is the difference between the special `never` tag and a normal opt-in tag?
- What happens if the `rescue` block itself fails?

---

### Task 2 — Upgrade to Docker Compose (3 pts)

Replace the `docker run` deployment with a templated Compose stack. Rename the Lab 5 `app_deploy` role to `web_app` first.

#### 2.1 Rename the role

```bash
cd ansible/roles && git mv app_deploy web_app
```

Update every reference: playbook `roles:` entries, docs, and variable prefixes (`web_app_*`). The new name lines up with the wipe variable in Task 3.

#### 2.2 Declare the role dependency

**File:** `roles/web_app/meta/main.yml`

Make `web_app` pull in `docker` automatically so a single `deploy.yml` provisions and deploys in the right order.

```yaml
---
dependencies:
  - role: docker
    vars:
      docker_users: ["{{ ansible_user }}"]
```

> Dependencies run **once per play**, before the role's own tasks. Don't nest them three deep — you lose all execution-order intuition.

#### 2.3 Template the Compose file

**File:** `roles/web_app/templates/docker-compose.yml.j2`

```jinja
{# Compose v2 — no top-level `version:` field (dropped in 2023) #}
services:
  {{ app_name }}:
    image: {{ docker_image }}:{{ docker_tag }}
    container_name: {{ app_name }}
    ports:
      - "{{ app_port }}:{{ app_internal_port }}"
    environment:
{% for key, value in app_env.items() %}
      {{ key }}: "{{ value }}"
{% endfor %}
    restart: {{ restart_policy | default('unless-stopped') }}
```

> Compose v2 dropped the top-level `version:` key. If a tutorial still writes `version: '3.8'`, it predates 2023 — leave it off. Use `| default(...)` filters so undefined optional vars don't break the render.

#### 2.4 Implement the deploy tasks

**File:** `roles/web_app/tasks/main.yml`

```yaml
---
- name: Include wipe tasks (Task 3 — runs only when gated)
  ansible.builtin.include_tasks: wipe.yml
  tags: [web_app, web_app_wipe]

- name: Deploy with Docker Compose
  block:
    - name: Create project directory
      ansible.builtin.file:
        path: "{{ compose_project_dir }}"
        state: directory
        mode: "0755"

    - name: Render compose file
      ansible.builtin.template:
        src: docker-compose.yml.j2
        dest: "{{ compose_project_dir }}/docker-compose.yml"
        mode: "0644"

    - name: docker compose up -d
      community.docker.docker_compose_v2:
        project_src: "{{ compose_project_dir }}"
        state: present
        pull: always
        remove_orphans: true
      register: compose_result
      # YOUR-TASK: add a uri smoke-test that retries until /health returns 200
  rescue:
    - name: Surface the deploy failure
      ansible.builtin.debug:
        msg: "Deploy of {{ app_name }} failed — see compose_result above"
  tags: [web_app, app_deploy, deploy]
```

Setup notes:
- Install the collection on the **controller**: `ansible-galaxy collection install community.docker` (4.x).
- Install `python3-docker` on the **target** — your `docker` role should already do this.
- Re-running with an identical rendered file is idempotent (`changed=0`).

#### 2.5 Variables

**File:** `roles/web_app/defaults/main.yml`

```yaml
---
app_name: devops-app
docker_image: your-registry/devops-info-service
docker_tag: latest            # override per-env in group_vars (see Bonus)
app_port: 8000
app_internal_port: 8000
compose_project_dir: "/opt/{{ app_name }}"
restart_policy: unless-stopped
app_env: {}                   # filled from group_vars / Vault
```

Keep secrets in your Lab 5 Vault file (`group_vars/.../vault.yml`) and reference them through `app_env`.

#### 2.6 Verify

```bash
ansible-playbook playbooks/deploy.yml          # first run: changed
ansible-playbook playbooks/deploy.yml          # second run: ok (idempotent)
ansible webservers -a "docker compose -f /opt/devops-app/docker-compose.yml ps"
curl -f http://<VM-IP>:8000/health
```

**Evidence:** rendered `docker-compose.yml`, both runs (changed → ok), `docker compose ps`, and a `curl` of `/health`.

**Research:**
- `restart: always` vs `unless-stopped` — when does it matter?
- Why does `python3-docker` need to be on the target, not the controller?
- Why is templating one Compose file better than one `docker run` per app?

---

### Task 3 — Double-Gated Wipe Logic (2 pts)

A clean reinstall is sometimes the only safe rollback (corrupted volume, rotated secret, broken cache). You need a button — and it must be **gated twice** so a single typo can't destroy a deployment.

#### 3.1 The double gate

| Invocation | Wipe? | Why |
|------------|-------|-----|
| `deploy.yml` | No | var false, tag not requested |
| `deploy.yml --tags web_app_wipe` | No | `when` blocks it (var still false) |
| `deploy.yml -e web_app_wipe=true` | Yes — wipe **then** deploy | clean reinstall |
| `deploy.yml -e web_app_wipe=true --tags web_app_wipe` | Yes — wipe **only** | deploy tasks skipped by tag |

> Why not the special `never` tag alone? A typo in `--tags` could still match it. Two independent gates (`when` variable **and** an opt-in tag) mean one mistake can't wipe a host by itself.

#### 3.2 Implement

**File:** `roles/web_app/tasks/wipe.yml`

```yaml
---
- name: Wipe web application
  block:
    - name: Compose down (stop + remove containers)
      community.docker.docker_compose_v2:
        project_src: "{{ compose_project_dir }}"
        state: absent
      # YOUR-TASK: tolerate the dir not existing yet (already-clean case)

    - name: Remove project directory
      ansible.builtin.file:
        path: "{{ compose_project_dir }}"
        state: absent

    - name: Log wipe completion
      ansible.builtin.debug:
        msg: "{{ app_name }} wiped"
  when: web_app_wipe | bool      # gate 1: variable (coerce the -e string!)
  tags: [web_app, web_app_wipe]  # gate 2: opt-in tag
```

The `include_tasks: wipe.yml` line you added in Task 2.4 sits **before** the deploy block, so `-e web_app_wipe=true` gives you wipe-then-deploy in one run.

**File:** `roles/web_app/defaults/main.yml` — add:

```yaml
web_app_wipe: false   # default: never wipe
```

#### 3.3 Verify all four rows

Run each invocation from the table above and capture the output. Confirm:
- Normal `deploy.yml` skips the wipe tasks.
- `--tags web_app_wipe` alone (no `-e`) is blocked by `when`.
- `-e web_app_wipe=true` removes the old install then redeploys.
- The `| bool` filter correctly coerces the `-e` string `"true"`.

**Evidence:** terminal output for all four rows, plus `docker ps` before/after the wipe-only run.

---

### Task 4 — CI/CD with GitHub Actions (3 pts)

Automate the whole thing: push to `main` → lint → deploy → verify. Use **OIDC short-lived credentials** rather than a long-lived SSH/cloud key where your target supports it.

#### 4.1 Workflow skeleton

**File:** `.github/workflows/ansible-deploy.yml`

```yaml
name: Ansible Deploy

on:
  push:
    branches: [main]
    paths:
      - 'ansible/**'
      - '!ansible/docs/**'                       # doc-only changes skip the run
      - '.github/workflows/ansible-deploy.yml'   # self-test on workflow edits
  workflow_dispatch:                             # manual deploys

permissions:
  contents: read
  id-token: write          # required for OIDC

jobs:
  lint:
    runs-on: ubuntu-24.04
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - run: pip install 'ansible-core==2.21.*' ansible-lint
      - run: ansible-lint ansible/

  deploy:
    needs: lint
    runs-on: ubuntu-24.04
    environment: production       # GH approval gate + per-env secrets
    steps:
      - uses: actions/checkout@v4
      # YOUR-TASK: choose ONE auth path below, then run the playbook + verify
```

> Pin `ansible-core==2.21.*` for the semester so CI matches your local lockfile. ansible-core has **no LTS label** — pin the exact minor that matches your `community.docker` 4.x collection.

#### 4.2 Pick an auth tier

| Tier | Mechanism | Trade-off |
|------|-----------|-----------|
| Repo secret as env | `secrets.SSH_KEY` → `~/.ssh/id_ed25519` | Simple; a long-lived key is the new "password in source" |
| GitHub Environment | Per-env secrets + manual approval | Needed for prod; small ops overhead |
| **OIDC + cloud IAM** | Short-lived federated token, no static key | Recommended where the target supports it |

**Recommended — OIDC (no static cloud key):**

```yaml
      - uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: arn:aws:iam::123456789012:role/ansible-deploy
          aws-region: eu-central-1
      # YOUR-TASK: with creds assumed, run ansible-playbook against your inventory
```

**Fallback — SSH key in a GitHub Environment secret:**

```yaml
      - env:
          VAULT: ${{ secrets.VAULT_PASS }}
          SSH:   ${{ secrets.SSH_KEY }}
        run: |
          install -m 600 /dev/stdin ~/.ssh/id_ed25519 <<< "$SSH"
          install -m 600 /dev/stdin /tmp/vault        <<< "$VAULT"
          ansible-playbook -i ansible/inventories/prod \
            ansible/playbooks/deploy.yml --vault-password-file /tmp/vault
```

> Never echo a secret to the log. A self-hosted runner on the target network removes the SSH key entirely — but it is a trust boundary, so never run it on PRs from forks.

#### 4.3 Verify in CI, not just exit 0

A deploy is done when the **app responds**, not when `ansible-playbook` exits 0.

```yaml
      - name: Smoke test
        run: |
          for i in $(seq 1 10); do
            curl -fsS "http://${{ vars.VM_HOST }}:8000/health" && exit 0
            sleep 6
          done
          exit 1
```

Add the status badge to your repo `README.md`:

```markdown
[![Ansible Deploy](https://github.com/<you>/<repo>/actions/workflows/ansible-deploy.yml/badge.svg)](https://github.com/<you>/<repo>/actions/workflows/ansible-deploy.yml)
```

#### 4.4 Deployment strategy

When you have more than one host, control the rollout cadence with `serial:` on the play.

```yaml
- name: Deploy web tier
  hosts: webservers
  serial: "25%"               # rolling: 25% of hosts per batch
  max_fail_percentage: 10     # abort the run if a batch exceeds 10% failures
  roles: [web_app]
```

| Strategy | `serial:` | When |
|----------|-----------|------|
| Rolling | `1` or `25%` | Zero-downtime behind a load balancer |
| Canary | `1` (first batch, then observe) | Test on one host before continuing |
| All-at-once | omit `serial:` | Dev/staging only |

In your docs, state which strategy you chose for prod and why.

**Evidence:** screenshot of a green workflow run, log lines showing `ansible-lint` passing and the playbook running, the smoke-test step output, and the passing badge.

**Research:**
- Security implications of a long-lived SSH key in a repo secret vs OIDC?
- How would you add a rollback job triggered by the verify step failing?
- Why must a self-hosted runner never execute on fork PRs?

---

## Bonus — Multi-Environment Promotion (2 pts)

> Single bonus task. Promote **one immutable image** through `staging` → `prod` using per-environment inventories and a manual approval gate — the same artifact, never rebuilt, never retagged.

Build on your Task 4 workflow. The goal is to deploy the identical image (pinned by an immutable SHA or SemVer tag, **not** `:latest`) to staging automatically, then to prod only after a human approves.

**Requirements:**

1. **Two inventories** with per-env `docker_tag`:
   ```
   ansible/inventories/
     staging/hosts.ini   group_vars/all.yml  → docker_tag: 1.4.0-rc1
     prod/hosts.ini      group_vars/all.yml  → docker_tag: 1.3.2   # pinned, lags staging
   ```
   Per-env Vault files so a leak in staging cannot expose prod. Do **not** branch the playbook on `inventory_hostname == 'prod'` — branch on variables only.

2. **Promotion workflow** — extend `ansible-deploy.yml` (or add `ansible-promote.yml`):
   - `deploy-staging` job runs automatically on push to `main`, targeting `-i ansible/inventories/staging`.
   - `deploy-prod` job `needs: deploy-staging`, uses `environment: production` (a GitHub Environment with a **required reviewer**), and targets `-i ansible/inventories/prod`.
   - The **same** `docker_image` flows to both; only the per-env `docker_tag` differs.

   ```yaml
   deploy-prod:
     needs: deploy-staging
     environment: production        # required reviewer = manual approval gate
     runs-on: ubuntu-24.04
     steps:
       - uses: actions/checkout@v4
       # YOUR-TASK: run deploy.yml against inventories/prod with a rolling serial
   ```

3. **Rolling rollout to prod** using `serial:` + `max_fail_percentage:` (Task 4.4).

4. **Verify**: capture the staging deploy auto-running, the prod job pausing for approval, and both environments serving the expected (different) tags via `/health` or a version field.

**Evidence:** the two inventory `group_vars` showing different pinned tags, a screenshot of the prod approval gate, and `curl` output proving each env runs its pinned version.

> This is genuinely harder than running two playbooks: you must keep one artifact immutable across environments, gate prod behind human approval, and prove the promotion path end to end.

---

## How to Submit

1. **Branch:**
   ```bash
   git checkout -b lab06
   ```

2. **Commit** the refactored Ansible tree, the workflow(s), and the docs:
   ```bash
   git add ansible/ .github/workflows/ansible-deploy.yml ansible/docs/LAB06.md
   git commit -m "feat: complete lab06 - advanced ansible & continuous deployment"
   git push -u origin lab06
   ```
   Confirm `.vault_pass` and any unencrypted secret are **not** staged. Encrypted Vault files are fine to commit.

3. **Pull Requests:**
   - **PR #1:** `your-fork:lab06` → `course-repo:master`
   - **PR #2:** `your-fork:lab06` → `your-fork:master`

4. **Documentation** — `ansible/docs/LAB06.md` should cover: tag strategy + a `rescue` that fired; Compose template + idempotency proof; the four wipe rows; the CI/CD workflow with chosen auth tier and rollout strategy; and answers to the research questions.

---

## Acceptance Criteria

### Main Tasks (10 points)

**Blocks & Tags (2 pts):**
- [ ] `docker` and `common` roles refactored into blocks with `rescue` + `always`
- [ ] Three-axis tag strategy applied (component / action / risk)
- [ ] `--list-tags` and a selective `--tags` run captured
- [ ] A `rescue` path demonstrably fired

**Docker Compose (3 pts):**
- [ ] `app_deploy` renamed to `web_app`; all references updated
- [ ] `meta/main.yml` declares the `docker` dependency
- [ ] Jinja2 `docker-compose.yml.j2` (no `version:` key) rendered correctly
- [ ] Deployed via `community.docker.docker_compose_v2`; idempotent (changed → ok)
- [ ] App reachable on `/health`

**Wipe Logic (2 pts):**
- [ ] `wipe.yml` gated by both `when: web_app_wipe | bool` and the `web_app_wipe` tag
- [ ] Included before the deploy block (clean reinstall works)
- [ ] All four invocation rows tested and captured

**CI/CD (3 pts):**
- [ ] `.github/workflows/ansible-deploy.yml` runs `ansible-lint` then deploy
- [ ] Path filters configured (docs excluded; workflow self-test)
- [ ] Auth via OIDC or a GitHub Environment secret (no key echoed to logs)
- [ ] Smoke-test verification step + passing status badge
- [ ] `serial:` deployment strategy chosen and justified

### Bonus Task (2 points)

**Multi-Environment Promotion (2 pts):**
- [ ] Separate `staging` / `prod` inventories with per-env pinned `docker_tag`
- [ ] Same immutable image promoted (no rebuild, no `:latest`)
- [ ] Prod gated behind a GitHub Environment manual approval
- [ ] Rolling rollout to prod with `serial:` + `max_fail_percentage:`
- [ ] Evidence both envs serve their pinned versions

---

## Rubric

| Criteria | Points | Description |
|----------|--------|-------------|
| **Blocks & Tags** | 2 pts | Roles refactored with block/rescue/always; clean three-axis tags; rescue fired |
| **Docker Compose** | 3 pts | Renamed role, role dependency, templated Compose v2, idempotent deploy |
| **Wipe Logic** | 2 pts | Double-gated (variable + tag), all four invocations verified |
| **CI/CD** | 3 pts | Lint → deploy → verify; OIDC/Environment auth; path filters; serial strategy |
| **Bonus: Multi-Env Promotion** | 2 pts | Immutable image promoted staging → prod behind manual approval |
| **Total** | 12 pts | 10 pts required + 2 pts bonus |

**Grading Scale:**
- **10/10:** Everything works, rescue/wipe demonstrated, clean CI with verification, sharp docs
- **8–9/10:** All works, good docs, minor gaps
- **6–7/10:** Core deploy works, weak tag strategy or thin CI verification
- **<6/10:** Missing Compose deploy, wipe ungated, or no working workflow

---

## Resources

<details>
<summary>📚 Ansible</summary>

- [Blocks (error handling)](https://docs.ansible.com/ansible/latest/playbook_guide/playbooks_blocks.html)
- [Tags](https://docs.ansible.com/ansible/latest/playbook_guide/playbooks_tags.html)
- [Role dependencies](https://docs.ansible.com/ansible/latest/playbook_guide/playbooks_reuse_roles.html#using-role-dependencies)
- [Vault](https://docs.ansible.com/ansible/latest/vault_guide/index.html)
- [`ansible-lint`](https://ansible.readthedocs.io/projects/lint/)

</details>

<details>
<summary>🐳 Docker Compose</summary>

- [`community.docker.docker_compose_v2`](https://docs.ansible.com/ansible/latest/collections/community/docker/docker_compose_v2_module.html)
- [Compose file reference](https://docs.docker.com/reference/compose-file/)
- [Jinja2 templating](https://jinja.palletsprojects.com/)

</details>

<details>
<summary>🔄 CI/CD & GitHub Actions</summary>

- [`paths` filters](https://docs.github.com/en/actions/using-workflows/triggering-a-workflow#using-filters)
- [OIDC for cloud deploys](https://docs.github.com/en/actions/deployment/security-hardening-your-deployments/about-security-hardening-with-openid-connect)
- [Environments & required reviewers](https://docs.github.com/en/actions/deployment/targeting-different-environments/using-environments-for-deployment)
- [Self-hosted runners (security)](https://docs.github.com/en/actions/hosting-your-own-runners/managing-self-hosted-runners/about-self-hosted-runners#self-hosted-runner-security)

</details>

---

## Looking Ahead

You've shipped the app — now you need to see what it says and how it behaves:

- **Lab 7:** Loki logging stack — deploy it with the very Ansible patterns from this lab
- **Lab 8:** Prometheus metrics — add a `/metrics` endpoint
- **Lab 9:** Kubernetes — migrate from Docker Compose to K8s, reusing your `/health` probe
- **Lab 10:** Helm charts for templated K8s deployments
- **Lab 13:** GitOps with ArgoCD — declarative, pull-based deployment

---

**Good luck!** 🚀

> **Remember:** a good deploy is small, automated, observable, and reversible. Blocks give you the error boundary, tags give you the scalpel, Compose gives you the declarative state, and CI gives you the button.
