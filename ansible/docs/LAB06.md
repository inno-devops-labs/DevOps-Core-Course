# Lab 6: Advanced Ansible & CI/CD - Submission

**Name:** j0cos  
**Date:** 2026-03-05  
**Lab Points:** 10 (+ bonus not completed)

---

## Task 1: Blocks & Tags (2 pts)

### Implementation

Refactored roles with blocks, rescue/always, and role/task tags.

Modified files:
- `ansible/roles/common/tasks/main.yml`
- `ansible/roles/common/defaults/main.yml`
- `ansible/roles/docker/tasks/main.yml`
- `ansible/playbooks/provision.yml`

Key changes:
- `common` role:
  - package tasks moved into a `block` with tag `packages`
  - rescue path added with `apt-get update --fix-missing`
  - always section logs completion to `/tmp/common_role.log`
  - user management grouped in separate `block` with tag `users`
- `docker` role:
  - install tasks grouped under `docker_install`
  - config tasks grouped under `docker_config`
  - rescue path retries apt update after wait
  - always section enforces docker service state
- Playbook role tags:
  - `common`, `docker` in `provision.yml`

### Tag Evidence

Evidence files:
- `ansible/docs/evidence/01-provision-list-tags.txt`
- `ansible/docs/evidence/02-provision-tags-docker.txt`
- `ansible/docs/evidence/03-provision-skip-common.txt`
- `ansible/docs/evidence/04-provision-tags-packages.txt`
- `ansible/docs/evidence/05-provision-docker-install-check.txt`

Observed results:
- `--list-tags` output:
  - `always, common, docker, docker_config, docker_install, limits, packages, timezone, users`
- `--tags docker`: only docker tasks executed, recap `ok=7 changed=1 failed=0`
- `--skip-tags common`: common tasks skipped, recap `ok=7 changed=0 failed=0`
- `--tags packages`: only package block in common ran, recap `ok=6 changed=2 failed=0`
- `--tags docker_install --check`: install subset dry-run worked, recap `ok=5 changed=0 failed=0`

### Research Answers

1. If rescue also fails, the task/play fails as normal unless errors are explicitly ignored.
2. Yes, nested blocks are supported.
3. Tags set on a block are inherited by tasks inside the block.

---

## Task 2: Docker Compose Migration (3 pts)

### Implementation

Role renamed and migrated from container run style to Compose.

Modified files:
- `ansible/roles/web_app/defaults/main.yml`
- `ansible/roles/web_app/tasks/main.yml`
- `ansible/roles/web_app/templates/docker-compose.yml.j2`
- `ansible/roles/web_app/meta/main.yml`
- `ansible/playbooks/deploy.yml`
- `ansible/playbooks/site.yml`

Migration details:
- Role rename: `app_deploy` -> `web_app`
- Compose template added (`docker-compose.yml.j2`)
- Role dependency configured:
  - `web_app` depends on `docker`
- Deployment flow:
  - create project directory
  - render compose file
  - run `community.docker.docker_compose_v2`
  - wait for `/health`

### Deployment and Idempotency Evidence

Evidence files:
- `ansible/docs/evidence/06-deploy-first.txt`
- `ansible/docs/evidence/07-deploy-second-idempotent.txt`
- `ansible/docs/evidence/08-deploy-list-tags.txt`

Observed results:
- First deploy recap: `ok=13 changed=2 failed=0`
- Second deploy recap: `ok=13 changed=0 failed=0` (idempotent)
- Deploy tags list:
  - `always, app_deploy, compose, docker_config, docker_install, web_app, web_app_wipe`

### Runtime Verification

From VM and local checks:
- Container running:
  - `docker ps` shows `devops-info-service` up with published port
- Endpoint checks successful:
  - `curl http://93.77.190.199:5000`
  - `curl http://93.77.190.199:5000/health`
  - `curl -i http://localhost:5000/`
  - `curl -i http://localhost:5000/health`

### Research Answers

1. `restart: always` also restarts after manual stop; `unless-stopped` respects manual stop.
2. Compose networks are project-scoped and lifecycle-managed by compose; default bridge is global and generic.
3. Yes, Vault variables can be referenced in templates like any normal Ansible variables.

---

## Task 3: Wipe Logic (1 pt)

### Implementation

Modified files:
- `ansible/roles/web_app/tasks/wipe.yml`
- `ansible/roles/web_app/tasks/main.yml`
- `ansible/roles/web_app/defaults/main.yml`

Behavior:
- Wipe controlled by `web_app_wipe` (default false)
- Wipe tasks tagged `web_app_wipe`
- Wipe included before deployment in `main.yml`
- Double gate: variable + tag

### Wipe Test Scenarios

Evidence files:
- `ansible/docs/evidence/09-wipe-s1-normal.txt`
- `ansible/docs/evidence/10-wipe-s2-wipe-only.txt`
- `ansible/docs/evidence/11-wipe-s4a-tag-only.txt`
- `ansible/docs/evidence/12-wipe-s3-clean-reinstall.txt`

Observed results:
- Scenario 1 (normal deploy): wipe skipped, recap `ok=13 changed=0 skipped=5`
- Scenario 2 (wipe only): app removed, recap `ok=8 changed=3`
- Scenario 4a (tag only, var false): wipe blocked by condition, recap `ok=3 changed=0 skipped=5`
- Scenario 3 (clean reinstall): wipe then redeploy, recap `ok=17 changed=3`

### Research Answers

1. Variable + tag provides double safety against accidental destructive runs.
2. `never` is tag-level suppression; variable+tag is explicit operational policy and easier to reason about.
3. Wipe must run before deploy to support clean reinstall in a single run.
4. Clean reinstall is useful for broken/drifted state; rolling update is preferred for minimal downtime.
5. Extend wipe by adding volume/image cleanup tasks (`docker_volume`, `docker_image`, compose volume removal).

---

## Task 4: CI/CD with GitHub Actions (3 pts)

### Implementation

Added workflow:
- `.github/workflows/ansible-deploy.yml`

Workflow includes:
- Path-filter trigger for `ansible/**`
- `lint` job with `ansible-lint`
- `deploy` job (push only) with:
  - SSH setup
  - temporary CI inventory generation
  - playbook run with vault password secret
  - curl verification of app endpoints

Required secrets configured in workflow:
- `ANSIBLE_VAULT_PASSWORD`
- `SSH_PRIVATE_KEY`
- `VM_HOST`
- `VM_USER`

Note:
- Workflow file is implemented and ready; GitHub Actions run screenshots/logs should be attached from repository Actions tab.

### Research Answers

1. SSH keys in GitHub Secrets can be exposed via malicious workflow/code changes; mitigate with branch protections, environment approvals, and least-privilege keys.
2. Staging -> production can be implemented with separate jobs/environments and manual approval gates.
3. Rollbacks require immutable versioned image tags and a deploy parameter selecting previous known-good tag.
4. Self-hosted runner can reduce external exposure and keep traffic in private network, but requires hardening/patching responsibilities.

---

## Task 5: Documentation (1 pt)

This file documents:
- blocks/tags design
- compose migration
- wipe safety logic
- vault refactor
- CI/CD workflow setup
- execution evidence and test outcomes

### Additional Security Refactor (Vault)

Implemented Vault-based secret handling:
- encrypted file: `ansible/inventory/group_vars/all.yml`
- mapped runtime vars in: `ansible/inventory/group_vars/webservers.yml`

This replaced direct secret dependence from `.env` in role logic.

---

## Challenges & Solutions

1. **Group vars not loading in expected path**
- Symptom: `docker_hub_password` undefined
- Fix: moved vars to `inventory/group_vars/` and normalized variable mapping.

2. **Compose YAML render errors with mixed env formats**
- Symptom: compose parse errors and malformed image reference
- Fix: hardened template quoting and image reference normalization logic.

3. **Health check variable dependency**
- Symptom: `app_port` undefined in health playbook
- Fix: added robust default variable in health check playbook.

4. **External endpoint unreachable**
- Root cause: cloud inbound rule missing for service port
- Fix: added security group rule, then external curl succeeded.

---

## Summary

- Lab goals for blocks/tags, compose migration, wipe logic, and documentation are implemented and validated with live VM runs.
- Deployment is idempotent (`changed=0` on second run).
- Wipe scenarios executed successfully with expected behavior.
- Application accessible and healthy from both VM localhost and external endpoint.
