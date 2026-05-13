# Lab 6: Advanced Ansible & CI/CD - Submission

**Name:** FILL ME
**Date:** FILL ME
**Lab Points:** 10 + bonus

---

## Overview 

This lab enhanced the Ansible automation from Lab 5 with production-ready features. Technologies used: Ansible 2.16+, Docker Compose v2, GitHub Actions, Jinja2 templating.

**What was accomplished:**
- Refactored roles with blocks for error handling (`block`/`rescue`/`always`)
- Implemented comprehensive tag strategy for selective execution
- Migrated from `docker_container` to Docker Compose with Jinja2 templates
- Added role dependencies for automatic Docker installation
- Implemented double-gated wipe logic (variable + tag)
- Configured GitHub Actions CI/CD with ansible-lint, syntax check, and automated deployment
- Achieved idempotency for all system-level tasks

## Task 1: Blocks & Tags (2 pts)

### Block usage

| Role | Blocks | Rescue | Always | Purpose |
|------|--------|--------|--------|---------|
| `common` | System provisioning, User management, Timezone | Apt cache fix on failure | Log completion | Ensure base system setup with error recovery |
| `docker` | Docker installation, Docker configuration | GPG key retry on timeout | Enable Docker service | Handle network issues during Docker repo setup |
| `web_app` | Deployment with Compose | Log deployment failure | - | Atomic deployment with cleanup on failure |

### Tag Strategy

| Tag | Scope | Used For |
|-----|-------|----------|
| `common` | Entire common role | Skip common setup |
| `packages` | Apt operations | Quick package updates |
| `users` | User management | User-only changes |
| `docker` | Entire docker role | Docker-only runs |
| `docker_install` | Docker installation only | Fresh Docker setup |
| `docker_config` | Docker configuration only | User/group changes |
| `app_deploy` | Full deployment | Normal deployments |
| `web_app_wipe` | Wipe only | Selective cleanup |

### Rescue Block Demonstration

The Docker GPG key task includes a rescue block that waits 10 seconds and retries on failure, simulating transient network issues common with external repository keys.

- Selective execution with Ansible tags (all tags)
  ![Selective execution with Ansible tags](/lab_solutions/lab1/ansible/docs/lab6-evidence/tags-all.png)

- Selective execution with Ansible tags (docker tags)
  ![Selective execution with Ansible tags](/lab_solutions/lab1/ansible/docs/lab6-evidence/tags-docker-1.png)

- Selective execution with Ansible tags (skip tags)
  ![Selective execution with Ansible tags](/lab_solutions/lab1/ansible/docs/lab6-evidence/tags-skip.png)

- Selective execution with Ansible tags (packages tags)
  ![Selective execution with Ansible tags](/lab_solutions/lab1/ansible/docs/lab6-evidence/tags-packages-1.png)

- Selective execution with Ansible tags (check tags)
  ![Selective execution with Ansible tags](/lab_solutions/lab1/ansible/docs/lab6-evidence/tags-check.png)

- Selective execution with Ansible tags (docker_install tags)
  ![Selective execution with Ansible tags](/lab_solutions/lab1/ansible/docs/lab6-evidence/tags-docker-install.png)
- Rescue block
  ![Selective execution with Ansible tags](/lab_solutions/lab1/ansible/docs/lab6-evidence/tags-rescue.png)

## Task 2: Docker Compose (3 pts)
FILL ME

- Idempotency check on the second playbook run

    Deploy with Docker Compose is being showed as changed because it always looks for docker image, but ansible doesn't create new container if one already exist

  ![Idempotency check on the second playbook run](/lab_solutions/lab1/ansible/docs/lab6-evidence/idemp-1.png)
  ![Idempotency check on the second playbook run](/lab_solutions/lab1/ansible/docs/lab6-evidence/idemp-2.png)

- Docker Compose deployment success
  ![Docker Compose deployment success](/lab_solutions/lab1/ansible/docs/lab6-evidence/deploy-ev-1.png)
  ![Docker Compose deployment success](/lab_solutions/lab1/ansible/docs/lab6-evidence/deploy-ev-2.png)

- Contents of templated docker-compose.yml
  ![Provision playbook initial run](/lab_solutions/lab1/ansible/docs/lab6-evidence/templated-docker-yml.png)

## Task 3: Wipe Logic (1 pt)
FILL ME


- Output of Scenario 1
  ![Output of Scenario 1](/lab_solutions/lab1/ansible/docs/lab6-evidence/wipe-1-1.png)
  ![Output of Scenario 1](/lab_solutions/lab1/ansible/docs/lab6-evidence/wipe-1-2.png)
  
- Output of Scenario 2
    ![Output of Scenario 2](/lab_solutions/lab1/ansible/docs/lab6-evidence/wipe-2.png)
  
- Output of Scenarion 3
    ![Output of Scenario 3](/lab_solutions/lab1/ansible/docs/lab6-evidence/wipe-3-1.png)
  ![Output of Scenario 3](/lab_solutions/lab1/ansible/docs/lab6-evidence/wipe-3-2.png)
  ![Output of Scenario 3 + app health check](/lab_solutions/lab1/ansible/docs/lab6-evidence/wipe-3-3.png)

## Task 4: CI/CD (3 pts)
FILL ME

- Workflow evidence
  ![ansible lint](/lab_solutions/lab1/ansible/docs/lab6-evidence/action-ev-1.png)
  ![ansible syntax](/lab_solutions/lab1/ansible/docs/lab6-evidence/action-ev-2.png)
  ![ansible deploy](/lab_solutions/lab1/ansible/docs/lab6-evidence/action-ev-3.png)

## Summary
Was quite interesting configuring ansible deployment in CI/CD. Tags really provides a mojor assist while developing, you can quickly change ansimble instructions. 
