# Lab 6: Advanced Ansible & CI/CD - Submission


## Overview

This submission upgrades the previous lab’s Ansible automation to be more production-like by adding:

- **Blocks + rescue/always** for clearer grouping and safer failure handling
- **Tags** for selective execution
- Migration from `docker_container` to **Docker Compose v2** using an Ansible-templated compose file
- **Role dependency** so the application role automatically installs Docker first
- **Safe wipe logic** with double-gating (**variable + tag**)
- **CI/CD** deployment via **GitHub Actions** with ansible-lint + deploy + verification

Repository structure highlights:

- `roles/common` refactored with `packages` and `users` blocks
- `roles/docker` refactored with `docker_install` and `docker_config` blocks
- `roles/web_app` (renamed from `app_deploy`) now deploys with Compose
- `.github/workflows/ansible-deploy.yml` automates lint + deployment

---

## Task 1: Blocks & Tags (2 pts)

### What changed

**common role**
- Packages are in a block tagged `packages`
- Users are in a block tagged `users`
- `rescue` retries apt update using `apt-get update --fix-missing`
- `always` writes a completion log to `/tmp/*`

**docker role**
- Installation tasks in a block tagged `docker_install`
- Configuration tasks in a block tagged `docker_config`
- `rescue` waits 10 seconds then retries apt update (covers transient key/network issues)
- `always` ensures Docker service is enabled and running

### Tag strategy

- `common` / `docker` tags applied at **role level** in `playbooks/provision.yml`
- Block tags:
  - `packages`, `users`
  - `docker_install`, `docker_config`

### Evidence to include

1. List tags:
```bash
ansible-playbook playbooks/provision.yml --list-tags
```

```text
playbook: playbooks/provision.yml

  play #1 (webservers): Provision web servers   TAGS: []
      TASK TAGS: [common, docker, docker_config, docker_install, packages, users]
```

2. Run only docker:
```bash
ansible-playbook playbooks/provision.yml --tags docker
```
```text
PLAY [Provision web servers] *****************************************************************************************************************************************

TASK [Gathering Facts] ***********************************************************************************************************************************************
ok: [aws_vm]

TASK [docker : Install prerequisites for Docker repository] **********************************************************************************************************
ok: [aws_vm]

TASK [docker : Ensure /etc/apt/keyrings exists] **********************************************************************************************************************
ok: [aws_vm]

TASK [docker : Remove legacy Docker repo list if present] ************************************************************************************************************
changed: [aws_vm]

TASK [docker : Remove legacy Docker keyring if present] **************************************************************************************************************
ok: [aws_vm]

TASK [docker : Download Docker GPG key (ascii)] **********************************************************************************************************************
changed: [aws_vm]

TASK [docker : Dearmor Docker GPG key into keyring] ******************************************************************************************************************
ok: [aws_vm]

TASK [docker : Add Docker apt repository] ****************************************************************************************************************************
changed: [aws_vm]

TASK [docker : Update apt cache after adding Docker repo] ************************************************************************************************************
changed: [aws_vm]

TASK [docker : Install Docker packages] ******************************************************************************************************************************
ok: [aws_vm]

TASK [docker : Install Python Docker SDK for Ansible docker modules] *************************************************************************************************
ok: [aws_vm]

TASK [docker : Ensure Docker service enabled and running] ************************************************************************************************************
ok: [aws_vm]

TASK [docker : Add users to docker group] ****************************************************************************************************************************
ok: [aws_vm] => (item=ubuntu)

PLAY RECAP ***********************************************************************************************************************************************************
aws_vm                     : ok=13   changed=4    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0   
```

3. Run only packages:
```bash
ansible-playbook playbooks/provision.yml --tags packages
```

```text
PLAY [Provision web servers] *****************************************************************************************************************************************

TASK [Gathering Facts] ***********************************************************************************************************************************************
ok: [aws_vm]

TASK [common : Update apt cache] *************************************************************************************************************************************
ok: [aws_vm]

TASK [common : Install common packages] ******************************************************************************************************************************
ok: [aws_vm]

TASK [common : Log completion (packages)] ****************************************************************************************************************************
changed: [aws_vm]

PLAY RECAP ***********************************************************************************************************************************************************
aws_vm                     : ok=4    changed=1    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0   
```

4. Skip common:
```bash
ansible-playbook playbooks/provision.yml --skip-tags common
```

```text
PLAY [Provision web servers] *****************************************************************************************************************************************

TASK [Gathering Facts] ***********************************************************************************************************************************************
ok: [aws_vm]

TASK [docker : Install prerequisites for Docker repository] **********************************************************************************************************
ok: [aws_vm]

TASK [docker : Ensure /etc/apt/keyrings exists] **********************************************************************************************************************
ok: [aws_vm]

TASK [docker : Remove legacy Docker repo list if present] ************************************************************************************************************
changed: [aws_vm]

TASK [docker : Remove legacy Docker keyring if present] **************************************************************************************************************
ok: [aws_vm]

TASK [docker : Download Docker GPG key (ascii)] **********************************************************************************************************************
ok: [aws_vm]

TASK [docker : Dearmor Docker GPG key into keyring] ******************************************************************************************************************
ok: [aws_vm]

TASK [docker : Add Docker apt repository] ****************************************************************************************************************************
changed: [aws_vm]

TASK [docker : Update apt cache after adding Docker repo] ************************************************************************************************************
changed: [aws_vm]

TASK [docker : Install Docker packages] ******************************************************************************************************************************
ok: [aws_vm]

TASK [docker : Install Python Docker SDK for Ansible docker modules] *************************************************************************************************
ok: [aws_vm]

TASK [docker : Ensure Docker service enabled and running] ************************************************************************************************************
ok: [aws_vm]

TASK [docker : Add users to docker group] ****************************************************************************************************************************
ok: [aws_vm] => (item=ubuntu)

PLAY RECAP ***********************************************************************************************************************************************************
aws_vm                     : ok=13   changed=3    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0   
```
### Research answers

- **Q: What happens if a rescue block also fails?**  
  The play fails (the rescued block is still considered failed). The `always` section still runs, then Ansible reports the failure.

- **Q: Can you have nested blocks?**  
  Yes. Blocks can be nested to create sub-groups with their own `rescue/always` semantics.

- **Q: How do tags inherit to tasks within blocks?**  
  Tags applied at the block level apply to all tasks inside the block. Tags can also be added/overridden on individual tasks.

---

## Task 2: Docker Compose (3 pts)

### Migration summary

The role `app_deploy` was renamed to **`web_app`** and migrated from `community.docker.docker_container` to **`community.docker.docker_compose_v2`**.

### Compose template

File: `roles/web_app/templates/docker-compose.yml.j2`

Key properties:
- service name == `{{ app_name }}`
- image == `{{ docker_image }}:{{ docker_image_tag }}`
- ports == `{{ app_port }}:{{ app_internal_port }}`
- restart policy: `unless-stopped`
- secrets: `APP_SECRET_KEY` sourced from an Ansible variable (should be vaulted in real use)

### Role dependency

File: `roles/web_app/meta/main.yml`  
This defines a dependency on the `docker` role so running deploy automatically ensures Docker is installed first.

### Evidence to include

1. Deploy:
```bash
ansible-playbook playbooks/deploy.yml
```

```text
PLAY [Deploy application] ********************************************************************************************************************************************

TASK [Gathering Facts] ***********************************************************************************************************************************************
ok: [aws_vm]

TASK [docker : Install prerequisites for Docker repository] **********************************************************************************************************
ok: [aws_vm]

TASK [docker : Ensure /etc/apt/keyrings exists] **********************************************************************************************************************
ok: [aws_vm]

TASK [docker : Remove legacy Docker repo list if present] ************************************************************************************************************
changed: [aws_vm]

TASK [docker : Remove legacy Docker keyring if present] **************************************************************************************************************
ok: [aws_vm]

TASK [docker : Download Docker GPG key (ascii)] **********************************************************************************************************************
ok: [aws_vm]

TASK [docker : Dearmor Docker GPG key into keyring] ******************************************************************************************************************
ok: [aws_vm]

TASK [docker : Add Docker apt repository] ****************************************************************************************************************************
changed: [aws_vm]

TASK [docker : Update apt cache after adding Docker repo] ************************************************************************************************************
changed: [aws_vm]

TASK [docker : Install Docker packages] ******************************************************************************************************************************
ok: [aws_vm]

TASK [docker : Install Python Docker SDK for Ansible docker modules] *************************************************************************************************
ok: [aws_vm]

TASK [docker : Ensure Docker service enabled and running] ************************************************************************************************************
ok: [aws_vm]

TASK [docker : Add users to docker group] ****************************************************************************************************************************
ok: [aws_vm] => (item=ubuntu)

TASK [web_app : Include wipe tasks] **********************************************************************************************************************************
included: /Users/philarmonia/Documents/current_course/CBS-02/DevOps/DevOps-Core-Course/ansible/roles/web_app/tasks/wipe.yml for aws_vm

TASK [web_app : Stop and remove containers] **************************************************************************************************************************
skipping: [aws_vm]

TASK [web_app : Remove docker-compose file] **************************************************************************************************************************
skipping: [aws_vm]

TASK [web_app : Remove application directory] ************************************************************************************************************************
skipping: [aws_vm]

TASK [web_app : Log wipe completion] *********************************************************************************************************************************
skipping: [aws_vm]

TASK [web_app : Check if container exists] ***************************************************************************************************************************
ok: [aws_vm]

TASK [web_app : Remove existing container] ***************************************************************************************************************************
changed: [aws_vm]

TASK [web_app : Ensure app directory exists] *************************************************************************************************************************
ok: [aws_vm]

TASK [web_app : Template docker-compose.yml] *************************************************************************************************************************
ok: [aws_vm]

TASK [web_app : Bring up application (compose v2)] *******************************************************************************************************************
[WARNING]: Docker compose: unknown None: /opt/devops-core-app-python/docker-compose.yml: the attribute `version` is obsolete, it will be ignored, please remove it to avoid potential confusion
changed: [aws_vm]

TASK [web_app : Wait for app port to be reachable] *******************************************************************************************************************
ok: [aws_vm]

TASK [web_app : Check /health endpoint] ******************************************************************************************************************************
ok: [aws_vm]

PLAY RECAP ***********************************************************************************************************************************************************
aws_vm                     : ok=21   changed=5    unreachable=0    failed=0    skipped=4    rescued=0    ignored=0   
```

2. Idempotency:
```bash
ansible-playbook playbooks/deploy.yml
```

```text
PLAY [Deploy application] ********************************************************************************************************************************************

TASK [Gathering Facts] ***********************************************************************************************************************************************
ok: [aws_vm]

TASK [docker : Install prerequisites for Docker repository] **********************************************************************************************************
ok: [aws_vm]

TASK [docker : Ensure /etc/apt/keyrings exists] **********************************************************************************************************************
ok: [aws_vm]

TASK [docker : Remove legacy Docker repo list if present] ************************************************************************************************************
changed: [aws_vm]

TASK [docker : Remove legacy Docker keyring if present] **************************************************************************************************************
ok: [aws_vm]

TASK [docker : Download Docker GPG key (ascii)] **********************************************************************************************************************
ok: [aws_vm]

TASK [docker : Dearmor Docker GPG key into keyring] ******************************************************************************************************************
ok: [aws_vm]

TASK [docker : Add Docker apt repository] ****************************************************************************************************************************
changed: [aws_vm]

TASK [docker : Update apt cache after adding Docker repo] ************************************************************************************************************
changed: [aws_vm]

TASK [docker : Install Docker packages] ******************************************************************************************************************************
ok: [aws_vm]

TASK [docker : Install Python Docker SDK for Ansible docker modules] *************************************************************************************************
ok: [aws_vm]

TASK [docker : Ensure Docker service enabled and running] ************************************************************************************************************
ok: [aws_vm]

TASK [docker : Add users to docker group] ****************************************************************************************************************************
ok: [aws_vm] => (item=ubuntu)

TASK [web_app : Include wipe tasks] **********************************************************************************************************************************
included: /Users/philarmonia/Documents/current_course/CBS-02/DevOps/DevOps-Core-Course/ansible/roles/web_app/tasks/wipe.yml for aws_vm

TASK [web_app : Stop and remove containers] **************************************************************************************************************************
skipping: [aws_vm]

TASK [web_app : Remove docker-compose file] **************************************************************************************************************************
skipping: [aws_vm]

TASK [web_app : Remove application directory] ************************************************************************************************************************
skipping: [aws_vm]

TASK [web_app : Log wipe completion] *********************************************************************************************************************************
skipping: [aws_vm]

TASK [web_app : Check if container exists] ***************************************************************************************************************************
ok: [aws_vm]

TASK [web_app : Remove existing container] ***************************************************************************************************************************
changed: [aws_vm]

TASK [web_app : Ensure app directory exists] *************************************************************************************************************************
ok: [aws_vm]

TASK [web_app : Template docker-compose.yml] *************************************************************************************************************************
ok: [aws_vm]

TASK [web_app : Bring up application (compose v2)] *******************************************************************************************************************
[WARNING]: Docker compose: unknown None: /opt/devops-core-app-python/docker-compose.yml: the attribute `version` is obsolete, it will be ignored, please remove it to avoid potential confusion
changed: [aws_vm]

TASK [web_app : Wait for app port to be reachable] *******************************************************************************************************************
ok: [aws_vm]

TASK [web_app : Check /health endpoint] ******************************************************************************************************************************
ok: [aws_vm]

PLAY RECAP ***********************************************************************************************************************************************************
aws_vm                     : ok=21   changed=5    unreachable=0    failed=0    skipped=4    rescued=0    ignored=0   
```

3. Verify:
```bash
ssh -i ~/Downloads/labsuser-4.pem ubuntu@98.80.174.112 "docker ps"
ssh -i ~/Downloads/labsuser-4.pem ubuntu@98.80.174.112 "docker compose -f /opt/devops-core-app-python/docker-compose.yml ps"
curl http://98.80.174.112:5000/
curl http://98.80.174.112:5000/health
```

```text
CONTAINER ID   IMAGE                                     COMMAND           CREATED         STATUS         PORTS                                         NAMES
5a09280934db   s1mphonia/devops-core-app-python:latest   "python app.py"   3 minutes ago   Up 3 minutes   0.0.0.0:5000->8000/tcp, [::]:5000->8000/tcp   devops-core-app-python

NAME                     IMAGE                                     COMMAND           SERVICE                  CREATED         STATUS         PORTS
devops-core-app-python   s1mphonia/devops-core-app-python:latest   "python app.py"   devops-core-app-python   4 minutes ago   Up 4 minutes   0.0.0.0:5000->8000/tcp, [::]:5000->8000/tcp
time="2026-03-05T21:51:19+03:00" level=warning msg="/opt/devops-core-app-python/docker-compose.yml: the attribute `version` is obsolete, it will be ignored, please remove it to avoid potential confusion"

{"endpoints":[{"description":"Service information","method":"GET","path":"/"},{"description":"Health check","method":"GET","path":"/health"}],"request":{"client_ip":"83.243.122.75","method":"GET","path":"/","user_agent":"curl/8.4.0"},"runtime":{"current_time":"2026-03-05T18:51:36.594733+00:00","timezone":"UTC","uptime_human":"4 minutes","uptime_seconds":279},"service":{"description":"DevOps course info service","framework":"Flask","name":"devops-info-service","version":"1.0.0"},"system":{"architecture":"x86_64","cpu_count":2,"hostname":"5a09280934db","platform":"Linux","platform_version":"#7~24.04.1-Ubuntu SMP Thu Jan 22 21:04:49 UTC 2026","python_version":"3.13.12"}}

{"status":"healthy","timestamp":"2026-03-05T18:51:44.524416+00:00","uptime_seconds":287}
```

### Research answers

- **Q: `restart: always` vs `unless-stopped`?**  
  `always` restarts even after manual stop; `unless-stopped` restarts unless the container was manually stopped.

- **Q: How do Compose networks differ from Docker bridge networks?**  
  Compose creates project-scoped networks automatically and attaches services by name; the default Docker bridge is global and not project-scoped.

- **Q: Can you reference Vault variables in the template?**  
  Yes. A vaulted variable is just an Ansible variable at runtime; templates can render it like any other.

---

## Task 3: Wipe Logic (1 pt)

### Implementation

- Variable: `web_app_wipe` (default `false`)
- Tag: `web_app_wipe`

Wipe tasks are included at the top of `roles/web_app/tasks/main.yml` and implemented in `roles/web_app/tasks/wipe.yml`.

### Why variable AND tag?

This is **double safety**:
- Tag prevents wipe from running during normal deploy runs
- Variable prevents wipe from running even if someone mistakenly uses `--tags web_app_wipe`

### Test scenarios

1. Normal deploy (wipe should not execute):
```bash
ansible-playbook playbooks/deploy.yml
```

```text
PLAY [Deploy application] ********************************************************************************************************************************************

TASK [Gathering Facts] ***********************************************************************************************************************************************
ok: [aws_vm]

TASK [docker : Install prerequisites for Docker repository] **********************************************************************************************************
ok: [aws_vm]

TASK [docker : Ensure /etc/apt/keyrings exists] **********************************************************************************************************************
ok: [aws_vm]

TASK [docker : Remove legacy Docker repo list if present] ************************************************************************************************************
changed: [aws_vm]

TASK [docker : Remove legacy Docker keyring if present] **************************************************************************************************************
ok: [aws_vm]

TASK [docker : Download Docker GPG key (ascii)] **********************************************************************************************************************
ok: [aws_vm]

TASK [docker : Dearmor Docker GPG key into keyring] ******************************************************************************************************************
ok: [aws_vm]

TASK [docker : Add Docker apt repository] ****************************************************************************************************************************
changed: [aws_vm]

TASK [docker : Update apt cache after adding Docker repo] ************************************************************************************************************
changed: [aws_vm]

TASK [docker : Install Docker packages] ******************************************************************************************************************************
ok: [aws_vm]

TASK [docker : Install Python Docker SDK for Ansible docker modules] *************************************************************************************************
ok: [aws_vm]

TASK [docker : Ensure Docker service enabled and running] ************************************************************************************************************
ok: [aws_vm]

TASK [docker : Add users to docker group] ****************************************************************************************************************************
ok: [aws_vm] => (item=ubuntu)

TASK [web_app : Include wipe tasks] **********************************************************************************************************************************
included: /Users/philarmonia/Documents/current_course/CBS-02/DevOps/DevOps-Core-Course/ansible/roles/web_app/tasks/wipe.yml for aws_vm

TASK [web_app : Stop and remove containers] **************************************************************************************************************************
skipping: [aws_vm]

TASK [web_app : Remove docker-compose file] **************************************************************************************************************************
skipping: [aws_vm]

TASK [web_app : Remove application directory] ************************************************************************************************************************
skipping: [aws_vm]

TASK [web_app : Log wipe completion] *********************************************************************************************************************************
skipping: [aws_vm]

TASK [web_app : Check if container exists] ***************************************************************************************************************************
ok: [aws_vm]

TASK [web_app : Remove existing container] ***************************************************************************************************************************
changed: [aws_vm]

TASK [web_app : Ensure app directory exists] *************************************************************************************************************************
ok: [aws_vm]

TASK [web_app : Template docker-compose.yml] *************************************************************************************************************************
ok: [aws_vm]

TASK [web_app : Bring up application (compose v2)] *******************************************************************************************************************
[WARNING]: Docker compose: unknown None: /opt/devops-core-app-python/docker-compose.yml: the attribute `version` is obsolete, it will be ignored, please remove it to avoid potential confusion
changed: [aws_vm]

TASK [web_app : Wait for app port to be reachable] *******************************************************************************************************************
ok: [aws_vm]

TASK [web_app : Check /health endpoint] ******************************************************************************************************************************
ok: [aws_vm]

PLAY RECAP ***********************************************************************************************************************************************************
aws_vm                     : ok=21   changed=5    unreachable=0    failed=0    skipped=4    rescued=0    ignored=0   
```

2. Wipe only:
```bash
ansible-playbook playbooks/deploy.yml -e "web_app_wipe=true" --tags web_app_wipe
```

```text
PLAY [Deploy application] ********************************************************************************************************************************************

TASK [Gathering Facts] ***********************************************************************************************************************************************
ok: [aws_vm]

TASK [web_app : Include wipe tasks] **********************************************************************************************************************************
included: /Users/philarmonia/Documents/current_course/CBS-02/DevOps/DevOps-Core-Course/ansible/roles/web_app/tasks/wipe.yml for aws_vm

TASK [web_app : Stop and remove containers] **************************************************************************************************************************
[WARNING]: Docker compose: unknown None: /opt/devops-core-app-python/docker-compose.yml: the attribute `version` is obsolete, it will be ignored, please remove it to avoid potential confusion
changed: [aws_vm]

TASK [web_app : Remove docker-compose file] **************************************************************************************************************************
changed: [aws_vm]

TASK [web_app : Remove application directory] ************************************************************************************************************************
changed: [aws_vm]

TASK [web_app : Log wipe completion] *********************************************************************************************************************************
ok: [aws_vm] => {
    "msg": "Application devops-core-app-python wiped successfully"
}

PLAY RECAP ***********************************************************************************************************************************************************
aws_vm                     : ok=6    changed=3    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0   
```

3. Clean reinstall (wipe then deploy):
```bash
ansible-playbook playbooks/deploy.yml -e "web_app_wipe=true"
```

```text
PLAY [Deploy application] ********************************************************************************************************************************************

TASK [Gathering Facts] ***********************************************************************************************************************************************
ok: [aws_vm]

TASK [docker : Install prerequisites for Docker repository] **********************************************************************************************************
ok: [aws_vm]

TASK [docker : Ensure /etc/apt/keyrings exists] **********************************************************************************************************************
ok: [aws_vm]

TASK [docker : Remove legacy Docker repo list if present] ************************************************************************************************************
changed: [aws_vm]

TASK [docker : Remove legacy Docker keyring if present] **************************************************************************************************************
ok: [aws_vm]

TASK [docker : Download Docker GPG key (ascii)] **********************************************************************************************************************
ok: [aws_vm]

TASK [docker : Dearmor Docker GPG key into keyring] ******************************************************************************************************************
ok: [aws_vm]

TASK [docker : Add Docker apt repository] ****************************************************************************************************************************
changed: [aws_vm]

TASK [docker : Update apt cache after adding Docker repo] ************************************************************************************************************
changed: [aws_vm]

TASK [docker : Install Docker packages] ******************************************************************************************************************************
ok: [aws_vm]

TASK [docker : Install Python Docker SDK for Ansible docker modules] *************************************************************************************************
ok: [aws_vm]

TASK [docker : Ensure Docker service enabled and running] ************************************************************************************************************
ok: [aws_vm]

TASK [docker : Add users to docker group] ****************************************************************************************************************************
ok: [aws_vm] => (item=ubuntu)

TASK [web_app : Include wipe tasks] **********************************************************************************************************************************
included: /Users/philarmonia/Documents/current_course/CBS-02/DevOps/DevOps-Core-Course/ansible/roles/web_app/tasks/wipe.yml for aws_vm

TASK [web_app : Check if compose project dir exists] *****************************************************************************************************************
ok: [aws_vm]

TASK [web_app : Stop and remove containers] **************************************************************************************************************************
skipping: [aws_vm]

TASK [web_app : Remove docker-compose file (if any)] *****************************************************************************************************************
ok: [aws_vm]

TASK [web_app : Remove application directory (or file if mistakenly created)] ****************************************************************************************
ok: [aws_vm]

TASK [web_app : Log wipe completion] *********************************************************************************************************************************
ok: [aws_vm] => {
    "msg": "Application devops-core-app-python wiped successfully"
}

TASK [web_app : Check if container exists] ***************************************************************************************************************************
ok: [aws_vm]

TASK [web_app : Remove existing container] ***************************************************************************************************************************
skipping: [aws_vm]

TASK [web_app : Ensure app directory exists] *************************************************************************************************************************
changed: [aws_vm]

TASK [web_app : Template docker-compose.yml] *************************************************************************************************************************
changed: [aws_vm]

TASK [web_app : Bring up application (compose v2)] *******************************************************************************************************************
[WARNING]: Docker compose: unknown None: /opt/devops-core-app-python/docker-compose.yml: the attribute `version` is obsolete, it will be ignored, please remove it to avoid potential confusion
changed: [aws_vm]

TASK [web_app : Wait for app port to be reachable] *******************************************************************************************************************
ok: [aws_vm]

TASK [web_app : Check /health endpoint] ******************************************************************************************************************************
ok: [aws_vm]

PLAY RECAP ***********************************************************************************************************************************************************
aws_vm                     : ok=24   changed=6    unreachable=0    failed=0    skipped=2    rescued=0    ignored=0   
```
4. Safety checks:
```bash
ansible-playbook playbooks/deploy.yml --tags web_app_wipe
```

```text
PLAY [Deploy application] ********************************************************************************************************************************************

TASK [Gathering Facts] ***********************************************************************************************************************************************
ok: [aws_vm]

TASK [web_app : Include wipe tasks] **********************************************************************************************************************************
included: /Users/philarmonia/Documents/current_course/CBS-02/DevOps/DevOps-Core-Course/ansible/roles/web_app/tasks/wipe.yml for aws_vm

TASK [web_app : Check if compose project dir exists] *****************************************************************************************************************
skipping: [aws_vm]

TASK [web_app : Stop and remove containers] **************************************************************************************************************************
skipping: [aws_vm]

TASK [web_app : Remove docker-compose file (if any)] *****************************************************************************************************************
skipping: [aws_vm]

TASK [web_app : Remove application directory (or file if mistakenly created)] ****************************************************************************************
skipping: [aws_vm]

TASK [web_app : Log wipe completion] *********************************************************************************************************************************
skipping: [aws_vm]

PLAY RECAP ***********************************************************************************************************************************************************
aws_vm                     : ok=2    changed=0    unreachable=0    failed=0    skipped=5    rescued=0    ignored=0   
```
### Research answers

1. **Why use both variable AND tag?**  
   Prevents accidental destructive actions. Both must be intentionally provided.

2. **Difference between `never` tag and this approach?**  
   `never` requires explicit inclusion and is a special-case mechanism. This lab’s approach uses normal tags + runtime gating, which is clearer and portable.

3. **Why must wipe logic come before deployment?**  
   Supports the clean reinstall path (remove old state first, then deploy fresh).

4. **Clean reinstall vs rolling update?**  
   Clean reinstall is useful for corrupted state/config drift or major changes; rolling updates are better when you want minimal downtime.

5. **How extend to images/volumes?**  
   Add tasks to remove images and named volumes/networks, still protected by the same gating.

---

## Task 4: CI/CD with GitHub Actions (3 pts)

### Workflow

File: `.github/workflows/ansible-deploy.yml`

Jobs:
1. `lint` runs `ansible-lint`
2. `deploy` runs playbook and verifies with `curl`

Required GitHub secrets:
- `ANSIBLE_VAULT_PASSWORD`
- `SSH_PRIVATE_KEY`
- `VM_HOST`
- `VM_USER`

### Research answers

1. **Security implications of SSH keys in GitHub Secrets?**  
   Secrets are encrypted at rest, but compromise of repo/admin access or workflow exfiltration can leak them. Use least-privilege keys, rotate regularly, restrict environments.

2. **Staging → production pipeline?**  
   Use separate jobs/environments, require manual approvals for production, separate inventories/variables, and promote through stages.

3. **Rollback strategy?**  
   Pin image tags (immutable), deploy previous tag, or add a rollback workflow that redeploys a known-good tag.

4. **Self-hosted runner security benefits?**  
   Keys don’t need to leave your infra; runner can access private networks directly; less secret material stored in GitHub.

---

## Task 5: Documentation (1 pt)

This file (`ansible/docs/LAB06.md`) is the documentation and contains:
- Overview
- Implementation notes per task
- Commands to reproduce
- Research answers
- Places to paste evidence outputs/screenshots

---

## Summary

**Key learnings**
- Blocks improve readability and failure handling.
- Tags make playbooks faster and safer to operate.
- Compose deployments are cleaner than imperative container tasks.
- Double-gated wipes prevent catastrophic mistakes.
- CI/CD enforces quality and makes deployments repeatable.

