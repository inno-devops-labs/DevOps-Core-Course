Lab 06 — Advanced Ansible & CI/CD

## 1. Overview

### What accomplished:
- Refactored roles to use `block` / `rescue` / `always` and added tags.
- Migrated application deployment to a templated Docker Compose file (.yml.j2) rendered by the `web_app` role.
- Implemented safe wipe logic with gating variables and tags.
- Implemented CI/CD pipeline using GitHub Actions and a self-hosted runner.

### Technologies used
- Ansible (2.16+), Docker, Docker Compose (v2 preferred), GitHub Actions, Jinja2.

## 2. Blocks & Tags

### Block usage and tag strategy
- `roles/common`: manages packages in a `block` with `rescue` that repairs apt cache; tags `packages` and `common`.
- `roles/docker`: two blocks `Docker installation` and `Docker configuration` with tags `docker_install`, `docker_config` and `docker`.
- `roles/web_app`: deploy block containing template render, image pull, and compose up; rescue collects logs and fails gracefully. Tags: `web_app_wipe`, `app_deploy` and `compose`.

### Execution examples
```
andpe@chale:~/ansible$ ansible-playbook playbooks/provision.yml --tags "docker"
BECOME password: 

PLAY [Provision web servers] ****************************************************************************************************************************

TASK [Gathering Facts] **********************************************************************************************************************************
ok: [wsl-local]

TASK [docker : Add Docker GPG key] **********************************************************************************************************************
ok: [wsl-local]

TASK [docker : Add Docker repository] *******************************************************************************************************************
ok: [wsl-local]

TASK [docker : Install Docker packages] *****************************************************************************************************************
ok: [wsl-local]

TASK [docker : Install Python Docker module for Ansible] ************************************************************************************************
ok: [wsl-local]

TASK [docker : Ensure Docker service is enabled and running] ********************************************************************************************
ok: [wsl-local]

TASK [docker : Ensure user is in docker group] **********************************************************************************************************
ok: [wsl-local]

TASK [docker : Confirm Docker configuration block completed] ********************************************************************************************
changed: [wsl-local]

PLAY RECAP **********************************************************************************************************************************************
wsl-local                  : ok=8    changed=1    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0
```

```
andpe@chale:~/ansible$ ansible-playbook playbooks/provision.yml --skip-tags "common"
BECOME password: 

PLAY [Provision web servers] ****************************************************************************************************************************

TASK [Gathering Facts] **********************************************************************************************************************************
ok: [wsl-local]

TASK [docker : Add Docker GPG key] **********************************************************************************************************************
ok: [wsl-local]

TASK [docker : Add Docker repository] *******************************************************************************************************************
ok: [wsl-local]

TASK [docker : Install Docker packages] *****************************************************************************************************************
ok: [wsl-local]

TASK [docker : Install Python Docker module for Ansible] ************************************************************************************************
ok: [wsl-local]

TASK [docker : Ensure Docker service is enabled and running] ********************************************************************************************
ok: [wsl-local]

TASK [docker : Ensure user is in docker group] **********************************************************************************************************
ok: [wsl-local]

TASK [docker : Confirm Docker configuration block completed] ********************************************************************************************
ok: [wsl-local]

PLAY RECAP **********************************************************************************************************************************************
wsl-local                  : ok=8    changed=0    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0
```

```
andpe@chale:~/ansible$ ansible-playbook playbooks/provision.yml --tags "packages"
BECOME password: 

PLAY [Provision web servers] ****************************************************************************************************************************

TASK [Gathering Facts] **********************************************************************************************************************************
ok: [wsl-local]

TASK [common : Update apt cache] ************************************************************************************************************************
ok: [wsl-local]

TASK [common : Install common packages] *****************************************************************************************************************
ok: [wsl-local]

TASK [common : Log package installation] ****************************************************************************************************************
changed: [wsl-local]

PLAY RECAP **********************************************************************************************************************************************
wsl-local                  : ok=4    changed=1    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0   
```

```
andpe@chale:~/ansible$ ansible-playbook playbooks/provision.yml --tags "docker" --check
BECOME password: 

PLAY [Provision web servers] ****************************************************************************************************************************

TASK [Gathering Facts] **********************************************************************************************************************************
ok: [wsl-local]

TASK [docker : Add Docker GPG key] **********************************************************************************************************************
ok: [wsl-local]

TASK [docker : Add Docker repository] *******************************************************************************************************************
ok: [wsl-local]

TASK [docker : Install Docker packages] *****************************************************************************************************************
ok: [wsl-local]

TASK [docker : Install Python Docker module for Ansible] ************************************************************************************************
ok: [wsl-local]

TASK [docker : Ensure Docker service is enabled and running] ********************************************************************************************
ok: [wsl-local]

TASK [docker : Ensure user is in docker group] **********************************************************************************************************
ok: [wsl-local]

TASK [docker : Confirm Docker configuration block completed] ********************************************************************************************
ok: [wsl-local]

PLAY RECAP **********************************************************************************************************************************************
wsl-local                  : ok=8    changed=0    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0
```

```
andpe@chale:~/ansible$ ansible-playbook playbooks/provision.yml --tags "docker_install"
BECOME password: 

PLAY [Provision web servers] ****************************************************************************************************************************

TASK [Gathering Facts] **********************************************************************************************************************************
ok: [wsl-local]

TASK [docker : Add Docker GPG key] **********************************************************************************************************************
ok: [wsl-local]

TASK [docker : Add Docker repository] *******************************************************************************************************************
ok: [wsl-local]

TASK [docker : Install Docker packages] *****************************************************************************************************************
ok: [wsl-local]

TASK [docker : Install Python Docker module for Ansible] ************************************************************************************************
ok: [wsl-local]

TASK [docker : Ensure Docker service is enabled and running] ********************************************************************************************
ok: [wsl-local]

PLAY RECAP **********************************************************************************************************************************************
wsl-local                  : ok=6    changed=0    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0
```

## 3. Docker Compose Migration

### Template structure
`ansible/roles/web_app/templates/docker-compose.yml.j2` defines `version`, `services`, map of ports and environment variables via `{{ app_name }}`, `{{ docker_image }}`, `{{ app_port }}` and `{{ app_internal_port }}`.

### Role dependencies
`web_app` depends on `docker` role via `meta` to ensure Docker is present before deploy.

### Before/after
- Before: static container creation, manual commands.
- After: templated Compose file, idempotent deployment handled by Ansible.

## 4. Wipe Logic

### Implementation details
- File: `ansible/roles/web_app/tasks/wipe.yml`.
- The wipe is gated by `web_app_wipe: false` default and the tag `web_app_wipe`.
- Actions: `docker compose down --remove-orphans` (ignore errors), remove compose file and directory, optional `docker rmi` when `web_app_wipe_images=true`.

Safety mechanisms
- Double gating (variable + tag) prevents accidental deletion.

Test results (summary)
- Scenario A: 
```
andpe@chale:~/ansible$ ansible-playbook playbooks/deploy.yml --ask-vault-pass
BECOME password: 
Vault password: 

PLAY [Deploy application] *******************************************************************************************************************************

TASK [Gathering Facts] **********************************************************************************************************************************
ok: [wsl-local]

TASK [docker : Add Docker GPG key] **********************************************************************************************************************
ok: [wsl-local]

TASK [docker : Add Docker repository] *******************************************************************************************************************
ok: [wsl-local]

TASK [docker : Install Docker packages] *****************************************************************************************************************
ok: [wsl-local]

TASK [docker : Install Python Docker module for Ansible] ************************************************************************************************
ok: [wsl-local]

TASK [docker : Ensure Docker service is enabled and running] ********************************************************************************************
ok: [wsl-local]

TASK [docker : Ensure user is in docker group] **********************************************************************************************************
ok: [wsl-local]

TASK [docker : Confirm Docker configuration block completed] ********************************************************************************************
ok: [wsl-local]

TASK [web_app : Include wipe tasks] *********************************************************************************************************************
included: /home/andpe/ansible/roles/web_app/tasks/wipe.yml for wsl-local

TASK [web_app : Stop and remove containers] *************************************************************************************************************
skipping: [wsl-local]

TASK [web_app : Remove docker-compose file] *************************************************************************************************************
skipping: [wsl-local]

TASK [web_app : Remove application directory] ***********************************************************************************************************
skipping: [wsl-local]

TASK [web_app : Optionally remove Docker image] *********************************************************************************************************
skipping: [wsl-local]

TASK [web_app : Log wipe completion] ********************************************************************************************************************
skipping: [wsl-local]

TASK [web_app : Login to Docker Hub] ********************************************************************************************************************
ok: [wsl-local]

TASK [web_app : Create application directory] ***********************************************************************************************************
ok: [wsl-local]

TASK [web_app : Template docker-compose file] ***********************************************************************************************************
ok: [wsl-local]

TASK [web_app : Pull latest Docker image] ***************************************************************************************************************
ok: [wsl-local]

TASK [web_app : Deploy application with Docker Compose] *************************************************************************************************
ok: [wsl-local]

TASK [web_app : Wait for app to be ready] ***************************************************************************************************************
ok: [wsl-local]

TASK [web_app : Check health endpoint] ******************************************************************************************************************
ok: [wsl-local]

TASK [Show dockerhub_username] **************************************************************************************************************************
ok: [wsl-local] => {
    "dockerhub_username": "chaleshka"
}

PLAY RECAP **********************************************************************************************************************************************
wsl-local                  : ok=17   changed=0    unreachable=0    failed=0    skipped=5    rescued=0    ignored=0   

andpe@chale:~/ansible$ docker ps
CONTAINER ID   IMAGE                                  COMMAND              CREATED          STATUS          PORTS                                        
 NAMES
de535781166b   chaleshka/devops-info-service:latest   "python -u app.py"   1 minute ago   Up 50 seconds   0.0.0.0:5000->5000/tcp, [::]:5000->5000/tcp   de535781166b_devops-info-service
```

- Scenario B: 
```
andpe@chale:~/ansible$ ansible-playbook playbooks/deploy.yml -e "web_app_wipe=true" --tags web_app_wipe --ask-vault-pass
BECOME password:
Vault password:

PLAY [Deploy application] *******************************************************************************************************************************

TASK [Gathering Facts] **********************************************************************************************************************************
ok: [wsl-local]

TASK [web_app : Include wipe tasks] *********************************************************************************************************************
included: /home/andpe/ansible/roles/web_app/tasks/wipe.yml for wsl-local

TASK [web_app : Stop and remove containers] *************************************************************************************************************
changed: [wsl-local]

TASK [web_app : Remove docker-compose file] *************************************************************************************************************
changed: [wsl-local]

TASK [web_app : Remove application directory] ***********************************************************************************************************
changed: [wsl-local]

TASK [web_app : Optionally remove Docker image] *********************************************************************************************************
skipping: [wsl-local]

TASK [web_app : Log wipe completion] ********************************************************************************************************************
ok: [wsl-local] => {
    "msg": "Application devops-info-service wiped successfully"
}

PLAY RECAP **********************************************************************************************************************************************
wsl-local                  : ok=6    changed=3    unreachable=0    failed=0    skipped=1    rescued=0    ignored=0   

andpe@chale:~/ansible$ docker ps
CONTAINER ID   IMAGE     COMMAND   CREATED   STATUS    PORTS     NAMES
andpe@chale:~/ansible$ ls /opt
containerd  infer
```

- Scenario C: 
```
andpe@chale:~/ansible$ ansible-playbook playbooks/deploy.yml -e "web_app_wipe=true" --ask-vault-pass
BECOME password: 
Vault password: 

PLAY [Deploy application] *******************************************************************************************************************************

TASK [Gathering Facts] **********************************************************************************************************************************
ok: [wsl-local]

TASK [docker : Add Docker GPG key] **********************************************************************************************************************
ok: [wsl-local]

TASK [docker : Add Docker repository] *******************************************************************************************************************
ok: [wsl-local]

TASK [docker : Install Docker packages] *****************************************************************************************************************
ok: [wsl-local]

TASK [docker : Install Python Docker module for Ansible] ************************************************************************************************
ok: [wsl-local]

TASK [docker : Ensure Docker service is enabled and running] ********************************************************************************************
ok: [wsl-local]

TASK [docker : Ensure user is in docker group] **********************************************************************************************************
ok: [wsl-local]

TASK [docker : Confirm Docker configuration block completed] ********************************************************************************************
ok: [wsl-local]

TASK [web_app : Include wipe tasks] *********************************************************************************************************************
included: /home/andpe/ansible/roles/web_app/tasks/wipe.yml for wsl-local

TASK [web_app : Stop and remove containers] *************************************************************************************************************
fatal: [wsl-local]: FAILED! => {"changed": false, "cmd": ["docker", "compose", "down", "--remove-orphans"], "delta": null, "end": null, "msg": "Unable to change directory before execution: [Errno 2] No such file or directory: b'/opt/devops-info-service'", "rc": null, "start": null, "stderr": "", "stderr_lines": [], "stdout": "", "stdout_lines": []}
...ignoring

TASK [web_app : Remove docker-compose file] *************************************************************************************************************
ok: [wsl-local]

TASK [web_app : Remove application directory] ***********************************************************************************************************
ok: [wsl-local]

TASK [web_app : Optionally remove Docker image] *********************************************************************************************************
skipping: [wsl-local]

TASK [web_app : Log wipe completion] ********************************************************************************************************************
ok: [wsl-local] => {
    "msg": "Application devops-info-service wiped successfully"
}

TASK [web_app : Login to Docker Hub] ********************************************************************************************************************
ok: [wsl-local]

TASK [web_app : Create application directory] ***********************************************************************************************************
changed: [wsl-local]

TASK [web_app : Template docker-compose file] ***********************************************************************************************************
changed: [wsl-local]

TASK [web_app : Pull latest Docker image] ***************************************************************************************************************
ok: [wsl-local]

TASK [web_app : Deploy application with Docker Compose] *************************************************************************************************
changed: [wsl-local]

TASK [web_app : Wait for app to be ready] ***************************************************************************************************************
ok: [wsl-local]

TASK [web_app : Check health endpoint] ******************************************************************************************************************
ok: [wsl-local]

TASK [Show dockerhub_username] **************************************************************************************************************************
ok: [wsl-local] => {
    "dockerhub_username": "chaleshka"
}

PLAY RECAP **********************************************************************************************************************************************
wsl-local                  : ok=21   changed=3    unreachable=0    failed=0    skipped=1    rescued=0    ignored=1   
```

- Scenario D: 
```
andpe@chale:~/ansible$ ansible-playbook playbooks/deploy.yml --tags web_app_wipe --ask-vault-pass
BECOME password: 
Vault password: 

PLAY [Deploy application] *******************************************************************************************************************************

TASK [Gathering Facts] **********************************************************************************************************************************
ok: [wsl-local]

TASK [web_app : Include wipe tasks] *********************************************************************************************************************
included: /home/andpe/ansible/roles/web_app/tasks/wipe.yml for wsl-local

TASK [web_app : Stop and remove containers] *************************************************************************************************************
skipping: [wsl-local]

TASK [web_app : Remove docker-compose file] *************************************************************************************************************
skipping: [wsl-local]

TASK [web_app : Remove application directory] ***********************************************************************************************************
skipping: [wsl-local]

TASK [web_app : Optionally remove Docker image] *********************************************************************************************************
skipping: [wsl-local]

TASK [web_app : Log wipe completion] ********************************************************************************************************************
skipping: [wsl-local]

PLAY RECAP **********************************************************************************************************************************************
wsl-local                  : ok=2    changed=0    unreachable=0    failed=0    skipped=5    rescued=0    ignored=0   


andpe@chale:~/ansible$ ansible-playbook playbooks/deploy.yml -e "web_app_wipe=true" --tags web_app_wipe --ask-vault-pass
BECOME password:
Vault password:

PLAY [Deploy application] *******************************************************************************************************************************

TASK [Gathering Facts] **********************************************************************************************************************************
ok: [wsl-local]

TASK [web_app : Include wipe tasks] *********************************************************************************************************************
included: /home/andpe/ansible/roles/web_app/tasks/wipe.yml for wsl-local

TASK [web_app : Stop and remove containers] *************************************************************************************************************
changed: [wsl-local]

TASK [web_app : Remove docker-compose file] *************************************************************************************************************
changed: [wsl-local]

TASK [web_app : Remove application directory] ***********************************************************************************************************
changed: [wsl-local]

TASK [web_app : Optionally remove Docker image] *********************************************************************************************************
skipping: [wsl-local]

TASK [web_app : Log wipe completion] ********************************************************************************************************************
ok: [wsl-local] => {
    "msg": "Application devops-info-service wiped successfully"
}

PLAY RECAP **********************************************************************************************************************************************
wsl-local                  : ok=6    changed=3    unreachable=0    failed=0    skipped=1    rescued=0    ignored=0   
```

## 5. CI/CD Integration

### Workflow architecture
`.github/workflows/ansible-deploy.yml` contains `lint` job (runs on `ubuntu-latest`) and `deploy` job (runs-on:`self-hosted`).

### Setup steps for runner
Register self-hosted runner in GitHub; install Docker and Python; add repository Secrets: `ANSIBLE_VAULT_PASSWORD` and `BECOME_PASSWORD`.

### Evidence of automated deployments
The workflow writes a temporary vault file and runs `ansible-playbook` on the self-hosted runner; logs show successful deploy steps and health checks. Success deploy action: https://github.com/Chaleshka/DevOps-Core-Course/actions/runs/22720230416. Also you can check http://chaleshka.ru:5050 and http://chaleshka.ru:5050/health

## 6. Challenges & Solutions

- Challenge: Generated compose file targets modern format; legacy standalone docker‑compose v1 fails (unsupported version:).
```
fatal: [local-vm]: FAILED! => {"changed": true, "cmd": ["docker-compose", "-f", "/opt/devops-info-service/docker-compose.yml", "logs", "--tail=50"], "delta": "0:00:00.266961", "end": "2026-03-04 22:23:37.685858", "msg": "non-zero return code", "rc": 1, "start": "2026-03-04 22:23:37.418897", "stderr": "Version in \"/opt/devops-info-service/docker-compose.yml\" is unsupported. You might be seeing this error because you're using the wrong Compose file version. Either specify a supported version (e.g \"2.2\" or \"3.3\") and place your service definitions under the `services` key, or omit the `version` key and place your service definitions at the root of the file to use version 1.\nFor more on the Compose file format versions, see https://docs.docker.com/compose/compose-file/", "stderr_lines": ["Version in \"/opt/devops-info-service/docker-compose.yml\" is unsupported. You might be seeing this error because you're using the wrong Compose file version. Either specify a supported version (e.g \"2.2\" or \"3.3\") and place your service definitions under the `services` key, or omit the `version` key and place your service definitions at the root of the file to use version 1.", "For more on the Compose file format versions, see https://docs.docker.com/compose/compose-file/"], "stdout": "", "stdout_lines": []}
```
- Solution: Install docker compose plugin on server.



## 7. Research Answers

### Refactor with Blocks & Tags
1. **What happens if rescue block also fails?**
- Will be normal task failure. `always` block still will ve runned
2. **Can you have nested blocks?**
- Yes. Ansible supports nested blocks.
3. **How do tags inherit to tasks within blocks?**
- Tags applied to all tasks in `block` section.

### Upgrade to Docker Compose
1. **What's the difference between `restart: always` and `restart: unless-stopped`?**
- `restart: always` restarts the container regardless of how it stopped. `restart: unless-stopped` restarts except when the container was manually stopped.
2. **How do Docker Compose networks differ from Docker bridge networks?**
- Docker Compose automatically creates a dedicated network for app and provides automatic service discovery using service names. With standard Docker networks, you have to manually link containers or manage IP addresses to let them communicate.
3. **Can you reference Ansible Vault variables in the template?**
- Yes. If vault is decrypted, the variables are available to Jinja2 templates.

### Wipe Logic Implementation
1. **Why use both variable AND tag?** (Double safety mechanism)
- This double-gating ensures maximum safety. Tag allows you to run only the wipe tasks. Variable prevents tasks from executing accidentally unless explicitly enabled.
2. **What's the difference between `never` tag and this approach?**
- A never tag statically prevents execution; the variable+tag approach requires explicit intent.
3. **Why must wipe logic come BEFORE deployment in main.yml?** (Clean reinstall scenario)
- It's ensures clean state (no port conflicts, leftover volumes, stale configs).
4. **When would you want clean reinstallation vs. rolling update?**
- Clean reinstall when state is corrupted, schema changes or testing from zero. Rolling update for minor changes and zero-downtime or preserving data/state.
5. **How would you extend this to wipe Docker images and volumes too?**
- Сhange wipe file and add guarded variables, optional dry-run/backup and conditional tasks that remove images and volumes only when explicitly requested.

### CI/CD with GitHub Actions
1. **What are the security implications of storing SSH keys in GitHub Secrets?**
- Secrets are encrypted at rest but can leak via logs, compromised accounts or poorly secured runners. Mitigations: least-privilege keys, rotate keys, restrict runner access, avoid printing secrets and use environment protection/approvals.
2. **How would you implement a staging → production deployment pipeline?**
- Use GitHub Actions Environments with protection rules like manual approvals. The workflow deploys to staging, runs tests, then waits for approval before deploying to production with its own secrets and inventory.
3. **What would you add to make rollbacks possible?**
- Keep previous artifacts, store deployment metadata, add a dedicated rollback playbook that redeploys a last-known-good tag and automate health checks that trigger rollback on failure.
4. **How does self-hosted runner improve security compared to GitHub-hosted?**
- Self-hosted runner improves security by keeping runners inside your network and avoiding exposing private hosts to public runners.