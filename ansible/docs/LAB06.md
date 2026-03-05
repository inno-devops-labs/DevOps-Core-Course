# Lab 06 Report — Advanced Ansible & CI/CD

## 1. Task 1: Refactoring with Blocks & Tags

### Implementation Details

**Role `common`:**
Grouped package management and user creation into logical blocks.

**Role `docker`:**
Implemented error handling using `rescue` blocks to retry `apt-get update` if GPG key acquisition fails.

### Error Handling

Added `always` blocks to log task completion in `/tmp/ansible_status.log`.

### Tag Strategy

* `packages`: For system-wide package updates
* `docker_install` / `docker_config`: Separate installation from configuration
* `common`: Execute the entire baseline role

### Research Answers

**Q: What happens if a rescue block also fails?**
A: If the `rescue` block fails, the play stops for that host and is marked as failed unless `ignore_errors: true` is set.

**Q: Can you have nested blocks?**
A: Yes, Ansible supports nesting blocks within `block`, `rescue`, or `always` sections.

**Q: How do tags inherit within blocks?**
A: Tags applied at the block level are automatically inherited by all tasks inside that block.

---

## 2. Task 2: Migration to Docker Compose

### Why Docker Compose?

Transitioning from `docker run` to Docker Compose allowed for:

* Declarative infrastructure
* Easier environment variable management
* Better restart policy control (`unless-stopped`)

### Role Dependencies (`meta/main.yml`)

The `web_app` role explicitly depends on the `docker` role to ensure the engine is installed before deployment.

### Idempotency Verification

**First Run:**
`Changed=1` — directory created, template rendered, container started.

**Second Run:**
`Changed=0` — all states matched the manifest.

---

## 3. Task 3: Wipe Logic Implementation

### Double-Gating Mechanism

To prevent accidental data loss, wipe logic requires **two conditions**:

1. Variable: `web_app_wipe: true` (passed via `-e`)
2. Tag: `--tags web_app_wipe`

### Test Scenarios

| Scenario        | Command                                                                  | Result                             |
| --------------- | ------------------------------------------------------------------------ | ---------------------------------- |
| Normal Deploy   | `ansible-playbook deploy.yml`                                            | Wipe tasks skipped                 |
| Wipe Only       | `ansible-playbook deploy.yml -e "web_app_wipe=true" --tags web_app_wipe` | App removed, deploy skipped        |
| Clean Reinstall | `ansible-playbook deploy.yml -e "web_app_wipe=true"`                     | Wipe runs first, then fresh deploy |

---

## 4. Task 4: CI/CD with GitHub Actions

### Workflow Architecture

The pipeline consists of two stages:

1. **Linting** — Uses `ansible-lint` to detect best-practice violations and syntax errors.
2. **Deployment** — Triggered only when changes occur in the `ansible/` directory.

### Security

* Used GitHub Secrets for `ANSIBLE_VAULT_PASSWORD` and `SSH_PRIVATE_KEY`
* Created a temporary vault password file during workflow execution
* Securely removed the file after the playbook run

---

## 5. Challenges & Solutions

**Challenge:** SSH host key verification failing in GitHub Actions.

**Solution:** Used `ssh-keyscan` to populate the `known_hosts` file inside the GitHub runner before executing the playbook.

---

## Summary

This lab demonstrated how to transform basic Ansible automation into a **production-grade infrastructure workflow**.

Key takeaways:

* Structured error handling using `block`, `rescue`, and `always`
* Improved deployment reproducibility with Docker Compose
* Safe infrastructure teardown with gated wipe logic
* Automated CI/CD deployment using GitHub Actions

