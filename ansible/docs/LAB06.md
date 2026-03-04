# Lab 6: Advanced Ansible & CI/CD - Submission

**Name:** Amirkhan Kurbanov
**Date:** 2026-03-04  
**Lab Points:** 10


## Task 1: Blocks & Tags (2 pts)

### Implementation
- Refactored the `common` role to use a block for package installation with tags `packages` and an `always` block for logging completion.
- Refactored the `docker` role into two blocks: `docker_install` (installation tasks) and `docker_config` (configuration tasks), each with corresponding tags. Added an `always` block to ensure Docker service is enabled.
- Added tags at role level (`common`, `docker`) and at task/block level for fine‑grained control.

### Testing Evidence

#### List all available tags
```bash
s3rap1s in ~/devops/DevOps-Core-Course/ansible on lab06 ● ● λ ansible-playbook playbooks/provision.yml --list-tags --vault-password-file .vault_pass 

playbook: playbooks/provision.yml

  play #1 (webservers): Provision web servers with common tools and Docker      TAGS: []
      TASK TAGS: [common, docker, docker_config, docker_install, packages]
```

#### Run only `common` role
```bash
s3rap1s in ~/devops/DevOps-Core-Course/ansible on lab05 ● λ ansible-playbook playbooks/provision.yml --tags common --vault-password-file .vault_pass

PLAY [Provision web servers with common tools and Docker] ************************************************************************************************************************************************************************

TASK [Gathering Facts] ***********************************************************************************************************************************************************************************************************
ok: [devops-vm]

TASK [common : Update apt cache] *************************************************************************************************************************************************************************************************
changed: [devops-vm]

TASK [common : Install common packages] ******************************************************************************************************************************************************************************************
ok: [devops-vm]

TASK [common : Log completion] ***************************************************************************************************************************************************************************************************
[WARNING]: Deprecation warnings can be disabled by setting `deprecation_warnings=False` in ansible.cfg.
[DEPRECATION WARNING]: INJECT_FACTS_AS_VARS default to `True` is deprecated, top-level facts will not be auto injected after the change. This feature will be removed from ansible-core version 2.24.
Origin: /home/s3rap1s/devops/DevOps-Core-Course/ansible/roles/common/tasks/main.yml:29:18

27     - name: Log completion
28       copy:
29         content: "Common role completed at {{ ansible_date_time.iso8601 }}"
                    ^ column 18

Use `ansible_facts["fact_name"]` (no `ansible_` prefix) instead.

changed: [devops-vm]

PLAY RECAP ***********************************************************************************************************************************************************************************************************************
devops-vm                  : ok=4    changed=2    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0   
```

#### Run only `packages` tag (within `common` role)
```bash
s3rap1s in ~/devops/DevOps-Core-Course/ansible on lab05 ● λ ansible-playbook playbooks/provision.yml --tags packages --vault-password-file .vault_pass

PLAY [Provision web servers with common tools and Docker] ************************************************************************************************************************************************************************

TASK [Gathering Facts] ***********************************************************************************************************************************************************************************************************
ok: [devops-vm]

TASK [common : Update apt cache] *************************************************************************************************************************************************************************************************
ok: [devops-vm]

TASK [common : Install common packages] ******************************************************************************************************************************************************************************************
ok: [devops-vm]

PLAY RECAP ***********************************************************************************************************************************************************************************************************************
devops-vm                  : ok=3    changed=0    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0   

```

#### Run only `docker_install` tag
```bash
s3rap1s in ~/devops/DevOps-Core-Course/ansible on lab06 ● ● λ ansible-playbook playbooks/provision.yml --tags docker_install --vault-password-file .vault_pass

PLAY [Provision web servers with common tools and Docker] ************************************************************************************************************************************************************************

TASK [Gathering Facts] ***********************************************************************************************************************************************************************************************************
ok: [devops-vm]

TASK [docker : Remove conflicting packages] **************************************************************************************************************************************************************************************
ok: [devops-vm]

TASK [docker : Install required system packages] *********************************************************************************************************************************************************************************
ok: [devops-vm]

TASK [docker : Create keyrings directory] ****************************************************************************************************************************************************************************************
ok: [devops-vm]

TASK [docker : Add Docker GPG key] ***********************************************************************************************************************************************************************************************
ok: [devops-vm]

TASK [docker : Add Docker APT repository] ****************************************************************************************************************************************************************************************
[WARNING]: Deprecation warnings can be disabled by setting `deprecation_warnings=False` in ansible.cfg.
[DEPRECATION WARNING]: INJECT_FACTS_AS_VARS default to `True` is deprecated, top-level facts will not be auto injected after the change. This feature will be removed from ansible-core version 2.24.
Origin: /home/s3rap1s/devops/DevOps-Core-Course/ansible/roles/docker/tasks/main.yml:41:15

39     - name: Add Docker APT repository
40       apt_repository:
41         repo: "deb [arch={{ ansible_architecture | replace('x86_64','amd64') }} signed-by=/etc/apt/keyrings/docker...
                 ^ column 15

Use `ansible_facts["fact_name"]` (no `ansible_` prefix) instead.

ok: [devops-vm]

TASK [docker : Install Docker packages] ******************************************************************************************************************************************************************************************
ok: [devops-vm]

TASK [docker : Ensure Docker service is running] *********************************************************************************************************************************************************************************
ok: [devops-vm]

TASK [docker : Ensure Docker enabled after block] ********************************************************************************************************************************************************************************
ok: [devops-vm]

PLAY RECAP ***********************************************************************************************************************************************************************************************************************
devops-vm                  : ok=9    changed=0    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0   

```

#### Run only `docker_config` tag
```bash
s3rap1s in ~/devops/DevOps-Core-Course/ansible on lab06 ● ● λ ansible-playbook playbooks/provision.yml --tags docker_config --vault-password-file .vault_pass

PLAY [Provision web servers with common tools and Docker] ************************************************************************************************************************************************************************

TASK [Gathering Facts] ***********************************************************************************************************************************************************************************************************
ok: [devops-vm]

TASK [docker : Add user to docker group] *****************************************************************************************************************************************************************************************
ok: [devops-vm]

TASK [docker : Install python3-docker] *******************************************************************************************************************************************************************************************
ok: [devops-vm]

PLAY RECAP ***********************************************************************************************************************************************************************************************************************
devops-vm                  : ok=3    changed=0    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0   
```

### Research Answers
- **Q: What happens if rescue block also fails?**  
  If the rescue block itself fails, the task execution stops and Ansible reports a failure. The `always` block will still run regardless of success or failure of both the main block and the rescue block.
- **Q: Can you have nested blocks?**  
  Yes, blocks can be nested. Inner blocks inherit the directives (`when`, `become`, `tags`) of outer blocks, and each block can have its own rescue/always sections.
- **Q: How do tags inherit to tasks within blocks?**  
  Tags applied to a block are automatically applied to all tasks inside that block, unless a task overrides them with its own tags.


## Task 2: Upgrade to Docker Compose (3 pts)

### Implementation
- Renamed `app_deploy` role to `web_app` (`mv app_deploy web_app`).
- Created a Jinja2 template `roles/web_app/templates/docker-compose.yml.j2`:
  ```yaml
  services:
  {{ app_name }}:
    image: "{{ docker_image }}:{{ docker_tag }}"
    container_name: "{{ app_name }}"
    ports:
      - "{{ app_port }}:{{ app_internal_port }}"
    environment:
      - HOST=0.0.0.0
      - PORT={{ app_internal_port }}
{% if app_env_vars is defined and app_env_vars %}
{% for key, value in app_env_vars.items() %}
      - {{ key }}={{ value }}
{% endfor %}
{% endif %}
    restart: unless-stopped
    networks:
      - app_network

networks:
  app_network:
    driver: bridge
  ```
- Added role dependency in `roles/web_app/meta/main.yml`:
  ```yaml
  dependencies:
    - role: docker
  ```
- Updated `roles/web_app/tasks/main.yml` to create the project directory, template the compose file, and deploy using `community.docker.docker_compose_v2`.
- Configured variables in `group_vars/all.yml` (encrypted with Vault):
  ```yaml
  app_name: devops-python
  docker_image: s3rap1s/devops-info-service
  docker_tag: latest
  app_port: 8000
  app_internal_port: 8000
  compose_project_dir: "/opt/{{ app_name }}"
  ```

### Testing Evidence

#### First deployment (shows changes)
```bash
s3rap1s in ~/devops/DevOps-Core-Course/ansible on lab06 ● ● λ ansible-playbook playbooks/deploy.yml --vault-password-file .vault_pass

PLAY [Deploy application] ********************************************************************************************************************************************************************************************************

TASK [Gathering Facts] ***********************************************************************************************************************************************************************************************************
ok: [devops-vm]

TASK [docker : Remove conflicting packages] **************************************************************************************************************************************************************************************
ok: [devops-vm]

TASK [docker : Install required system packages] *********************************************************************************************************************************************************************************
ok: [devops-vm]

TASK [docker : Create keyrings directory] ****************************************************************************************************************************************************************************************
ok: [devops-vm]

TASK [docker : Add Docker GPG key] ***********************************************************************************************************************************************************************************************
ok: [devops-vm]

TASK [docker : Add Docker APT repository] ****************************************************************************************************************************************************************************************
[WARNING]: Deprecation warnings can be disabled by setting `deprecation_warnings=False` in ansible.cfg.
[DEPRECATION WARNING]: INJECT_FACTS_AS_VARS default to `True` is deprecated, top-level facts will not be auto injected after the change. This feature will be removed from ansible-core version 2.24.
Origin: /home/s3rap1s/devops/DevOps-Core-Course/ansible/roles/docker/tasks/main.yml:41:15

39     - name: Add Docker APT repository
40       apt_repository:
41         repo: "deb [arch={{ ansible_architecture | replace('x86_64','amd64') }} signed-by=/etc/apt/keyrings/docker...
                 ^ column 15

Use `ansible_facts["fact_name"]` (no `ansible_` prefix) instead.

ok: [devops-vm]

TASK [docker : Install Docker packages] ******************************************************************************************************************************************************************************************
ok: [devops-vm]

TASK [docker : Ensure Docker service is running] *********************************************************************************************************************************************************************************
ok: [devops-vm]

TASK [docker : Ensure Docker enabled after block] ********************************************************************************************************************************************************************************
ok: [devops-vm]

TASK [docker : Add user to docker group] *****************************************************************************************************************************************************************************************
ok: [devops-vm]

TASK [docker : Install python3-docker] *******************************************************************************************************************************************************************************************
ok: [devops-vm]

TASK [docker : Docker role complete (always)] ************************************************************************************************************************************************************************************
ok: [devops-vm] => {
    "msg": "Docker role finished"
}

TASK [web_app : Include wipe tasks] **********************************************************************************************************************************************************************************************
skipping: [devops-vm]

TASK [web_app : Ensure project directory exists] *********************************************************************************************************************************************************************************
ok: [devops-vm]

TASK [web_app : Template docker-compose.yml] *************************************************************************************************************************************************************************************
ok: [devops-vm]

TASK [web_app : Deploy with docker-compose] **************************************************************************************************************************************************************************************
ok: [devops-vm]

PLAY RECAP ***********************************************************************************************************************************************************************************************************************
devops-vm                  : ok=15   changed=0    unreachable=0    failed=0    skipped=1    rescued=0    ignored=0
```

#### Second run (idempotency – no changes)
```bash
s3rap1s in ~/devops/DevOps-Core-Course/ansible on lab06 ● ● λ ansible-playbook playbooks/deploy.yml --vault-password-file .vault_pass

PLAY [Deploy application] ********************************************************************************************************************************************************************************************************

TASK [Gathering Facts] ***********************************************************************************************************************************************************************************************************
ok: [devops-vm]

TASK [docker : Remove conflicting packages] **************************************************************************************************************************************************************************************
ok: [devops-vm]

TASK [docker : Install required system packages] *********************************************************************************************************************************************************************************
ok: [devops-vm]

TASK [docker : Create keyrings directory] ****************************************************************************************************************************************************************************************
ok: [devops-vm]

TASK [docker : Add Docker GPG key] ***********************************************************************************************************************************************************************************************
ok: [devops-vm]

TASK [docker : Add Docker APT repository] ****************************************************************************************************************************************************************************************
[WARNING]: Deprecation warnings can be disabled by setting `deprecation_warnings=False` in ansible.cfg.
[DEPRECATION WARNING]: INJECT_FACTS_AS_VARS default to `True` is deprecated, top-level facts will not be auto injected after the change. This feature will be removed from ansible-core version 2.24.
Origin: /home/s3rap1s/devops/DevOps-Core-Course/ansible/roles/docker/tasks/main.yml:41:15

39     - name: Add Docker APT repository
40       apt_repository:
41         repo: "deb [arch={{ ansible_architecture | replace('x86_64','amd64') }} signed-by=/etc/apt/keyrings/docker...
                 ^ column 15

Use `ansible_facts["fact_name"]` (no `ansible_` prefix) instead.

ok: [devops-vm]

TASK [docker : Install Docker packages] ******************************************************************************************************************************************************************************************
ok: [devops-vm]

TASK [docker : Ensure Docker service is running] *********************************************************************************************************************************************************************************
ok: [devops-vm]

TASK [docker : Ensure Docker enabled after block] ********************************************************************************************************************************************************************************
ok: [devops-vm]

TASK [docker : Add user to docker group] *****************************************************************************************************************************************************************************************
ok: [devops-vm]

TASK [docker : Install python3-docker] *******************************************************************************************************************************************************************************************
ok: [devops-vm]

TASK [docker : Docker role complete (always)] ************************************************************************************************************************************************************************************
ok: [devops-vm] => {
    "msg": "Docker role finished"
}

TASK [web_app : Include wipe tasks] **********************************************************************************************************************************************************************************************
skipping: [devops-vm]

TASK [web_app : Ensure project directory exists] *********************************************************************************************************************************************************************************
ok: [devops-vm]

TASK [web_app : Template docker-compose.yml] *************************************************************************************************************************************************************************************
ok: [devops-vm]

TASK [web_app : Deploy with docker-compose] **************************************************************************************************************************************************************************************
ok: [devops-vm]

PLAY RECAP ***********************************************************************************************************************************************************************************************************************
devops-vm                  : ok=15   changed=0    unreachable=0    failed=0    skipped=1    rescued=0    ignored=0
```

#### Generated docker-compose.yml on target VM
```bash
devops@devops:~$ cat /opt/devops-python/docker-compose.yml 
services:
  devops-python:
    image: "s3rap1s/devops-info-service:latest"
    container_name: "devops-python"
    ports:
      - "8000:8000"
    environment:
      - HOST=0.0.0.0
      - PORT=8000
    restart: unless-stopped
    networks:
      - app_network

networks:
  app_network:
    driver: bridge
```

#### Application is accessible
```bash
devops@devops:~$ curl http://localhost:8000/health
{"status":"healthy","timestamp":"2026-03-04T14:32:32.965187+00:00","uptime_seconds":5351}
```

### Research Answers
- **Q: What's the difference between `restart: always` and `restart: unless-stopped`?**  
  `always` restarts the container regardless of its exit status, even if it was manually stopped. `unless-stopped` restarts unless the container was explicitly stopped by the user.
- **Q: How do Docker Compose networks differ from Docker bridge networks?**  
  Compose creates a user‑defined bridge network with automatic DNS resolution between containers. It provides better isolation and service discovery than the default bridge.
- **Q: Can you reference Ansible Vault variables in the template?**  
  Yes, variables decrypted by Ansible Vault can be used directly in templates. The template is rendered after vault decryption.


## Task 3: Wipe Logic (1 pt)

### Implementation
- Added `web_app_wipe` variable (default: `false`) in `roles/web_app/defaults/main.yml`.
- Created `roles/web_app/tasks/wipe.yml` with tasks to stop/remove containers, delete the compose file, and remove the project directory, all inside a block with `when: web_app_wipe | bool` and tag `web_app_wipe`.
- Included `wipe.yml` at the beginning of `roles/web_app/tasks/main.yml` with the same tag.
- The wipe logic runs only when explicitly enabled (`-e "web_app_wipe=true"`) and/or the tag is used.

### Testing Scenarios

#### Scenario 1: Normal deployment (wipe should NOT run)
```bash
s3rap1s in ~/devops/DevOps-Core-Course/ansible on lab06 ● ● λ ansible-playbook playbooks/deploy.yml --vault-password-file .vault_pass

PLAY [Deploy application] ********************************************************************************************************************************************************************************************************

TASK [Gathering Facts] ***********************************************************************************************************************************************************************************************************
ok: [devops-vm]

TASK [docker : Remove conflicting packages] **************************************************************************************************************************************************************************************
ok: [devops-vm]

TASK [docker : Install required system packages] *********************************************************************************************************************************************************************************
ok: [devops-vm]

TASK [docker : Create keyrings directory] ****************************************************************************************************************************************************************************************
ok: [devops-vm]

TASK [docker : Add Docker GPG key] ***********************************************************************************************************************************************************************************************
ok: [devops-vm]

TASK [docker : Add Docker APT repository] ****************************************************************************************************************************************************************************************
[WARNING]: Deprecation warnings can be disabled by setting `deprecation_warnings=False` in ansible.cfg.
[DEPRECATION WARNING]: INJECT_FACTS_AS_VARS default to `True` is deprecated, top-level facts will not be auto injected after the change. This feature will be removed from ansible-core version 2.24.
Origin: /home/s3rap1s/devops/DevOps-Core-Course/ansible/roles/docker/tasks/main.yml:41:15

39     - name: Add Docker APT repository
40       apt_repository:
41         repo: "deb [arch={{ ansible_architecture | replace('x86_64','amd64') }} signed-by=/etc/apt/keyrings/docker...
                 ^ column 15

Use `ansible_facts["fact_name"]` (no `ansible_` prefix) instead.

ok: [devops-vm]

TASK [docker : Install Docker packages] ******************************************************************************************************************************************************************************************
ok: [devops-vm]

TASK [docker : Ensure Docker service is running] *********************************************************************************************************************************************************************************
ok: [devops-vm]

TASK [docker : Ensure Docker enabled after block] ********************************************************************************************************************************************************************************
ok: [devops-vm]

TASK [docker : Add user to docker group] *****************************************************************************************************************************************************************************************
ok: [devops-vm]

TASK [docker : Install python3-docker] *******************************************************************************************************************************************************************************************
ok: [devops-vm]

TASK [docker : Docker role complete (always)] ************************************************************************************************************************************************************************************
ok: [devops-vm] => {
    "msg": "Docker role finished"
}

TASK [web_app : Include wipe tasks] **********************************************************************************************************************************************************************************************
skipping: [devops-vm]

TASK [web_app : Ensure project directory exists] *********************************************************************************************************************************************************************************
ok: [devops-vm]

TASK [web_app : Template docker-compose.yml] *************************************************************************************************************************************************************************************
ok: [devops-vm]

TASK [web_app : Deploy with docker-compose] **************************************************************************************************************************************************************************************
ok: [devops-vm]

PLAY RECAP ***********************************************************************************************************************************************************************************************************************
devops-vm                  : ok=15   changed=0    unreachable=0    failed=0    skipped=1    rescued=0    ignored=0   
```

#### Scenario 2: Wipe only (remove existing deployment)
```bash
s3rap1s in ~/devops/DevOps-Core-Course/ansible on lab06 ● ● λ ansible-playbook playbooks/deploy.yml -e "web_app_wipe=true" --tags web_app_wipe --vault-password-file .vault_pass

PLAY [Deploy application] ********************************************************************************************************************************************************************************************************

TASK [Gathering Facts] ***********************************************************************************************************************************************************************************************************
ok: [devops-vm]

TASK [web_app : Include wipe tasks] **********************************************************************************************************************************************************************************************
included: /home/s3rap1s/devops/DevOps-Core-Course/ansible/roles/web_app/tasks/wipe.yml for devops-vm

TASK [web_app : Stop and remove containers] **************************************************************************************************************************************************************************************
changed: [devops-vm]

TASK [web_app : Remove docker-compose file] **************************************************************************************************************************************************************************************
changed: [devops-vm]

TASK [web_app : Remove project directory] ****************************************************************************************************************************************************************************************
changed: [devops-vm]

TASK [web_app : Log wipe completion] *********************************************************************************************************************************************************************************************
ok: [devops-vm] => {
    "msg": "Application devops-python wiped successfully"
}

PLAY RECAP ***********************************************************************************************************************************************************************************************************************
devops-vm                  : ok=6    changed=3    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0   
```
After this, the container and directory are gone.

#### Scenario 3: Clean reinstallation (wipe → deploy)
```bash
s3rap1s in ~/devops/DevOps-Core-Course/ansible on lab06 ● ● λ ansible-playbook playbooks/deploy.yml -e "web_app_wipe=true" --vault-password-file .vault_pass

PLAY [Deploy application] ********************************************************************************************************************************************************************************************************

TASK [Gathering Facts] ***********************************************************************************************************************************************************************************************************
ok: [devops-vm]

TASK [docker : Remove conflicting packages] **************************************************************************************************************************************************************************************
ok: [devops-vm]

TASK [docker : Install required system packages] *********************************************************************************************************************************************************************************
ok: [devops-vm]

TASK [docker : Create keyrings directory] ****************************************************************************************************************************************************************************************
ok: [devops-vm]

TASK [docker : Add Docker GPG key] ***********************************************************************************************************************************************************************************************
ok: [devops-vm]

TASK [docker : Add Docker APT repository] ****************************************************************************************************************************************************************************************
[WARNING]: Deprecation warnings can be disabled by setting `deprecation_warnings=False` in ansible.cfg.
[DEPRECATION WARNING]: INJECT_FACTS_AS_VARS default to `True` is deprecated, top-level facts will not be auto injected after the change. This feature will be removed from ansible-core version 2.24.
Origin: /home/s3rap1s/devops/DevOps-Core-Course/ansible/roles/docker/tasks/main.yml:41:15

39     - name: Add Docker APT repository
40       apt_repository:
41         repo: "deb [arch={{ ansible_architecture | replace('x86_64','amd64') }} signed-by=/etc/apt/keyrings/docker...
                 ^ column 15

Use `ansible_facts["fact_name"]` (no `ansible_` prefix) instead.

ok: [devops-vm]

TASK [docker : Install Docker packages] ******************************************************************************************************************************************************************************************
ok: [devops-vm]

TASK [docker : Ensure Docker service is running] *********************************************************************************************************************************************************************************
ok: [devops-vm]

TASK [docker : Ensure Docker enabled after block] ********************************************************************************************************************************************************************************
ok: [devops-vm]

TASK [docker : Add user to docker group] *****************************************************************************************************************************************************************************************
ok: [devops-vm]

TASK [docker : Install python3-docker] *******************************************************************************************************************************************************************************************
ok: [devops-vm]

TASK [docker : Docker role complete (always)] ************************************************************************************************************************************************************************************
ok: [devops-vm] => {
    "msg": "Docker role finished"
}

TASK [web_app : Include wipe tasks] **********************************************************************************************************************************************************************************************
included: /home/s3rap1s/devops/DevOps-Core-Course/ansible/roles/web_app/tasks/wipe.yml for devops-vm

TASK [web_app : Stop and remove containers] **************************************************************************************************************************************************************************************
[ERROR]: Task failed: Module failed: "/opt/devops-python" is not a directory
Origin: /home/s3rap1s/devops/DevOps-Core-Course/ansible/roles/web_app/tasks/wipe.yml:3:7

1 - name: Wipe application
2   block:
3     - name: Stop and remove containers
        ^ column 7

fatal: [devops-vm]: FAILED! => {"changed": false, "msg": "\"/opt/devops-python\" is not a directory"}
...ignoring

TASK [web_app : Remove docker-compose file] **************************************************************************************************************************************************************************************
ok: [devops-vm]

TASK [web_app : Remove project directory] ****************************************************************************************************************************************************************************************
ok: [devops-vm]

TASK [web_app : Log wipe completion] *********************************************************************************************************************************************************************************************
ok: [devops-vm] => {
    "msg": "Application devops-python wiped successfully"
}

TASK [web_app : Ensure project directory exists] *********************************************************************************************************************************************************************************
changed: [devops-vm]

TASK [web_app : Template docker-compose.yml] *************************************************************************************************************************************************************************************
changed: [devops-vm]

TASK [web_app : Deploy with docker-compose] **************************************************************************************************************************************************************************************
changed: [devops-vm]

PLAY RECAP ***********************************************************************************************************************************************************************************************************************
devops-vm                  : ok=20   changed=3    unreachable=0    failed=0    skipped=0    rescued=0    ignored=1 
```
After completion, the application is running fresh.

#### Scenario 4a: Safety check – tag specified but variable false
```bash
s3rap1s in ~/devops/DevOps-Core-Course/ansible on lab06 ● ● λ ansible-playbook playbooks/deploy.yml --tags web_app_wipe --vault-password-file .vault_pass

PLAY [Deploy application] ********************************************************************************************************************************************************************************************************

TASK [Gathering Facts] ***********************************************************************************************************************************************************************************************************
ok: [devops-vm]

TASK [web_app : Include wipe tasks] **********************************************************************************************************************************************************************************************
skipping: [devops-vm]

PLAY RECAP ***********************************************************************************************************************************************************************************************************************
devops-vm                  : ok=1    changed=0    unreachable=0    failed=0    skipped=1    rescued=0    ignored=0
```
Wipe does not run because `when` condition is false.

#### Scenario 4b: Variable true, only wipe (deployment skipped)
```bash
s3rap1s in ~/devops/DevOps-Core-Course/ansible on lab06 ● ● λ ansible-playbook playbooks/deploy.yml -e "web_app_wipe=true" --tags web_app_wipe --vault-password-file .vault_pass

PLAY [Deploy application] ********************************************************************************************************************************************************************************************************

TASK [Gathering Facts] ***********************************************************************************************************************************************************************************************************
ok: [devops-vm]

TASK [web_app : Include wipe tasks] **********************************************************************************************************************************************************************************************
included: /home/s3rap1s/devops/DevOps-Core-Course/ansible/roles/web_app/tasks/wipe.yml for devops-vm

TASK [web_app : Stop and remove containers] **************************************************************************************************************************************************************************************
changed: [devops-vm]

TASK [web_app : Remove docker-compose file] **************************************************************************************************************************************************************************************
changed: [devops-vm]

TASK [web_app : Remove project directory] ****************************************************************************************************************************************************************************************
changed: [devops-vm]

TASK [web_app : Log wipe completion] *********************************************************************************************************************************************************************************************
ok: [devops-vm] => {
    "msg": "Application devops-python wiped successfully"
}

PLAY RECAP ***********************************************************************************************************************************************************************************************************************
devops-vm                  : ok=6    changed=3    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0
```
Only wipe runs, no deployment.

### Research Answers
- **Why use both variable AND tag?**  
  Double safety: the tag allows selective execution, while the variable ensures that even if the tag is accidentally used, the wipe won't run unless explicitly enabled.
- **What's the difference between `never` tag and this approach?**  
  The `never` tag prevents tasks from running unless specifically requested. This approach uses a variable for finer control – wipe can be triggered either by the tag alone (if variable is true) or by the variable alone (if tag not used but variable true).
- **Why must wipe logic come BEFORE deployment in main.yml?**  
  To enable clean reinstallation: wipe removes the old application, then deployment installs a fresh copy.
- **When would you want clean reinstallation vs. rolling update?**  
  Clean reinstallation is useful when configuration has changed drastically or the application needs a fresh state. Rolling updates are for zero‑downtime upgrades.
- **How would you extend this to wipe Docker images and volumes too?**  
  Add tasks to prune images (`docker image prune -af`) and remove volumes (`docker volume prune -f`) using Ansible modules.


## Task 4: CI/CD with GitHub Actions (3 pts)

### Implementation
- Set up a self‑hosted runner on the target VM (Ubuntu 24.04) following GitHub instructions.
- Created workflow file `.github/workflows/ansible-deploy.yml` with path filters to trigger only on changes to `ansible/**` and the workflow itself.
- The workflow uses the self‑hosted runner (`runs-on: self-hosted`), installs Ansible and required packages via `apt`, decrypts the vault password from a GitHub secret, runs `deploy.yml`, and verifies the application with `curl`.

### Workflow File
```yaml
name: Ansible Deployment

on:
  push:
    branches: [ main, master, lab06 ]
    paths:
      - 'ansible/**'
      - '.github/workflows/ansible-deploy.yml'

jobs:
  deploy:
    runs-on: self-hosted
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Install Ansible and dependencies
        run: |
          sudo apt update
          sudo apt install -y ansible python3-docker python3-pip

      - name: Create inventory file for local connection
        run: |
          cd ansible
          echo "[webservers]" > inventory/ci.ini
          echo "localhost ansible_connection=local" >> inventory/ci.ini

      - name: Deploy with Ansible
        env:
          ANSIBLE_VAULT_PASSWORD: ${{ secrets.ANSIBLE_VAULT_PASSWORD }}
        run: |
          cd ansible
          echo "$ANSIBLE_VAULT_PASSWORD" > /tmp/vault_pass
          ansible-playbook -i inventory/ci.ini playbooks/deploy.yml --vault-password-file /tmp/vault_pass
          rm /tmp/vault_pass
      - name: Verify deployment
        run: |
          sleep 10
          curl -f http://localhost:8000/health || exit 1
```

### GitHub Secret
- `ANSIBLE_VAULT_PASSWORD` – the vault password (stored as a secret).

### Successful Workflow Log
```
Current runner version: '2.332.0'
Runner name: '***'
Runner group name: 'Default'
Machine name: '***'
GITHUB_TOKEN Permissions
Secret source: Actions
Prepare workflow directory
Prepare all required actions
Getting action download info
Download action repository 'actions/checkout@v4' (SHA:34e114876b0b11c390a56381ad16ebd13914f8d5)
Complete job name: deploy
1s
2s
Reading package lists...
Building dependency tree...
Reading state information...
7 packages can be upgraded. Run 'apt list --upgradable' to see them.
WARNING: apt does not have a stable CLI interface. Use with caution in scripts.
Reading package lists...
Building dependency tree...
Reading state information...
ansible is already the newest version (9.2.0+dfsg-0ubuntu5).
python3-docker is already the newest version (5.0.3-1ubuntu1.1).
python3-pip is already the newest version (24.0+dfsg-1ubuntu1.3).
0 upgraded, 0 newly installed, 0 to remove and 7 not upgraded.
0s
Run cd ansible
  
23s
Run cd ansible
  
PLAY [Deploy application] ******************************************************
TASK [Gathering Facts] *********************************************************
ok: [localhost]
TASK [app_deploy : Log in to Docker Hub] ***************************************
ok: [localhost]
TASK [app_deploy : Pull Docker image] ******************************************
ok: [localhost]
TASK [app_deploy : Check if container is running] ******************************
ok: [localhost]
TASK [app_deploy : Stop and remove existing container if it exists] ************
changed: [localhost]
TASK [app_deploy : Run Docker container] ***************************************
changed: [localhost]
TASK [app_deploy : Wait for application to be ready] ***************************
ok: [localhost]
TASK [app_deploy : Verify health endpoint] *************************************
ok: [localhost]
TASK [app_deploy : Display health check result] ********************************
ok: [localhost] => {
    "msg": "Health check passed! Response: {'status': 'healthy', 'timestamp': '2026-03-04T13:54:53.345136+00:00', 'uptime_seconds': 5}"
}
PLAY RECAP *********************************************************************
localhost                  : ok=9    changed=2    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0   
10s
Run sleep 10
  
  % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                 Dload  Upload   Total   Spent    Left  Speed
  0     0    0     0    0     0      0      0 --:--:-- --:--:-- --:--:--     0
{"status":"healthy","timestamp":"2026-03-04T13:55:03.528080+00:00","uptime_seconds":3102}
100    90  100    90    0     0   9153      0 --:--:-- --:--:-- --:--:-- 10000
0s
Post job cleanup.
/usr/bin/git version
git version 2.43.0
Temporarily overriding HOME='/home/***/actions-runner/_work/_temp/099c7d1c-ff33-42f8-aca6-2bfd69c3eac2' before making global git config changes
Adding repository directory to the temporary git global config as a safe directory
/usr/bin/git config --global --add safe.directory /home/***/actions-runner/_work/DevOps-Core-Course/DevOps-Core-Course
/usr/bin/git config --local --name-only --get-regexp core\.sshCommand
/usr/bin/git submodule foreach --recursive sh -c "git config --local --name-only --get-regexp 'core\.sshCommand' && git config --local --unset-all 'core.sshCommand' || :"
/usr/bin/git config --local --name-only --get-regexp http\.https\:\/\/github\.com\/\.extraheader
http.https://github.com/.extraheader
/usr/bin/git config --local --unset-all http.https://github.com/.extraheader
/usr/bin/git submodule foreach --recursive sh -c "git config --local --name-only --get-regexp 'http\.https\:\/\/github\.com\/\.extraheader' && git config --local --unset-all 'http.https://github.com/.extraheader' || :"
/usr/bin/git config --local --name-only --get-regexp ^includeIf\.gitdir:
/usr/bin/git submodule foreach --recursive git config --local --show-origin --name-only --get-regexp remote.origin.url
0s
Cleaning up orphan processes
```

### Status Badge
Added to `ansible/README.md`:
```markdown
[![Ansible Deployment](https://github.com/s3rap1s/DevOps-Core-Course/actions/workflows/ansible-deploy.yml/badge.svg)](https://github.com/s3rap1s/DevOps-Core-Course/actions/workflows/ansible-deploy.yml)
```

### Research Answers
- **What are the security implications of storing SSH keys in GitHub Secrets?**  
  Secrets are encrypted and not exposed in logs, but they are still accessible to anyone with write access to the repository. They should be rotated regularly and have minimal permissions.
- **How would you implement a staging → production deployment pipeline?**  
  Use separate workflows for staging and production, or use environments with approval gates. The staging workflow could deploy to a test VM, run integration tests, and then trigger production deployment after manual approval.
- **What would you add to make rollbacks possible?**  
  Store previous Docker image tags and have a playbook that redeploys the previous version. In CI/CD, you could keep the last successful image tag and provide a rollback workflow.
- **How does self-hosted runner improve security compared to GitHub-hosted?**  
  A self‑hosted runner behind your firewall eliminates the need to open SSH ports to the internet and keeps secrets entirely within your infrastructure.
