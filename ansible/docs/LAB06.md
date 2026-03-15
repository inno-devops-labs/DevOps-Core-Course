# lab 06: advanced ansible & ci/cd

## 1. blocks & tags refactoring

### understanding blocks

blocks allow you to:
- **group tasks** logically (e.g., all docker installation tasks)
- **apply directives** once to multiple tasks (when, become, tags)
- **handle errors** with rescue and always sections
- **improve readability** by showing task relationships

### common role refactoring

**file:** `roles/common/tasks/main.yml`

refactored into two blocks:

1. **package management block**
   - tags: `packages`, `common`
   - rescue: runs `apt-get update --fix-missing` on failure
   - always: logs completion to `/tmp/common_packages_install.log`

2. **system configuration block**
   - tags: `users`, `common`
   - always: logs completion to `/tmp/common_config.log`

```yaml
- name: Package management block
  block:
    - name: Update apt cache
      apt:
        update_cache: yes
        cache_valid_time: 3600

    - name: Install common packages
      apt:
        name: "{{ common_packages }}"
        state: present

  rescue:
    - name: Fix apt cache on failure
      command: apt-get update --fix-missing
      changed_when: true

    - name: Retry package installation after fix
      apt:
        name: "{{ common_packages }}"
        state: present

  always:
    - name: Log package installation completion
      copy:
        content: "Common packages installed at {{ ansible_date_time.iso8601 }}\n"
        dest: /tmp/common_packages_install.log
        mode: '0644'

  become: true
  tags:
    - packages
    - common
```

### docker role refactoring

**file:** `roles/docker/tasks/main.yml`

refactored into two blocks:

1. **docker installation block**
   - tags: `docker_install`, `docker`
   - rescue: waits 10 seconds and retries gpg key on network failure
   - always: ensures docker service is enabled

2. **docker configuration block**
   - tags: `docker_config`, `docker`
   - rescue: logs failure message
   - always: logs completion

### tag strategy

| role | tag | description |
|------|-----|-------------|
| common | `packages` | package installation tasks |
| common | `users` | system configuration tasks |
| common | `common` | all tasks in the role |
| docker | `docker_install` | docker installation tasks |
| docker | `docker_config` | docker configuration tasks |
| docker | `docker` | all tasks in the role |
| web_app | `app_deploy` | deployment tasks |
| web_app | `compose` | docker compose specific |
| web_app | `web_app` | all tasks in the role |
| web_app | `web_app_wipe` | wipe tasks (gated) |

### selective execution examples

```bashj
ansible-playbook playbooks/provision.yml --tags "docker"
ansible-playbook playbooks/provision.yml --list-tags

PLAY [Provision web servers] *************************************************************

TASK [Gathering Facts] *******************************************************************
ok: [devops-vm]

TASK [docker : Create directory for Docker GPG key] **************************************
ok: [devops-vm]

TASK [docker : Check if Docker GPG key exists] *******************************************
ok: [devops-vm]

TASK [docker : Add Docker GPG key] *******************************************************
skipping: [devops-vm]

TASK [docker : Add Docker repository] ****************************************************
[WARNING]: Deprecation warnings can be disabled by setting `deprecation_warnings=False` in ansible.cfg.
[DEPRECATION WARNING]: INJECT_FACTS_AS_VARS default to `True` is deprecated, top-level facts will not be auto injected after the change. This feature will be removed from ansible-core version 2.24.
Origin: /Users/s.razmakhov/bucket/courses/uni/devops-s26/ansible/roles/docker/tasks/main.yml:27:15

25     - name: Add Docker repository
26       apt_repository:
27         repo: "deb [arch={{ ansible_architecture | replace('x86_64', 'amd64') | replace('aarch64', 'arm64') }} sig...
               ^ column 15

Use `ansible_facts["fact_name"]` (no `ansible_` prefix) instead.

ok: [devops-vm]

TASK [docker : Install Docker packages] **************************************************
ok: [devops-vm]

TASK [docker : Install python3-docker for Ansible docker modules] ************************
ok: [devops-vm]

TASK [docker : Install docker-compose Python package] ************************************
changed: [devops-vm]

TASK [docker : Ensure Docker service is enabled] *****************************************
ok: [devops-vm]

TASK [docker : Ensure Docker service is running and enabled] *****************************
ok: [devops-vm]

TASK [docker : Add user to docker group] *************************************************
ok: [devops-vm]

TASK [docker : Log Docker configuration completion] **************************************
[DEPRECATION WARNING]: INJECT_FACTS_AS_VARS default to `True` is deprecated, top-level facts will not be auto injected after the change. This feature will be removed from ansible-core version 2.24.
Origin: /Users/s.razmakhov/bucket/courses/uni/devops-s26/ansible/roles/docker/tasks/main.yml:96:18

94     - name: Log Docker configuration completion
95       copy:
96         content: "Docker configuration completed at {{ ansible_date_time.iso8601 }}\n"
                  ^ column 18

Use `ansible_facts["fact_name"]` (no `ansible_` prefix) instead.

changed: [devops-vm]

PLAY RECAP *******************************************************************************
devops-vm                  : ok=11   changed=2    unreachable=0    failed=0    skipped=1    rescued=0    ignored=0


playbook: playbooks/provision.yml

play #1 (webservers): Provision web servers	TAGS: []
    TASK TAGS: [common, docker, docker_config, docker_install, packages, users]
```

### research questions

| question | answer |
|----------|--------|
| what happens if rescue block also fails? | if a rescue block fails, the playbook execution stops and the task is marked as failed. however, the `always` block will still execute. to handle rescue failures, you can nest another block inside the rescue. |
| can you have nested blocks? | yes, ansible supports nested blocks. you can have a block inside another block's tasks, rescue, or always sections. this is useful for complex error handling scenarios. |
| how do tags inherit to tasks within blocks? | tags applied at the block level are inherited by all tasks within that block. if a task has its own tags, they are combined with the block's tags. a task can be selected by either its own tags or the block's tags. |

---

## 2. docker compose migration

### role rename

the `app_deploy` role was renamed to `web_app`:
- directory: `roles/app_deploy` → `roles/web_app`
- playbook references updated in `deploy.yml` and `site.yml`

### why docker compose over docker run?

| docker run | docker compose |
|------------|----------------|
| imperative commands | declarative configuration |
| single container | multi-container management |
| manual env handling | .env files, variable substitution |
| manual updates | change config and recreate |
| harder to reproduce | consistent, reproducible deployments |

### docker compose template

**file:** `roles/web_app/templates/docker-compose.yml.j2`

```yaml
version: '3.8'

services:
  {{ app_name }}:
    image: {{ docker_image }}:{{ docker_tag }}
    container_name: {{ app_name }}
    ports:
      - "{{ app_port }}:{{ app_internal_port }}"
    restart: {{ restart_policy }}
{% if app_healthcheck is defined and app_healthcheck %}
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:{{ app_internal_port }}/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s
{% endif %}
```

### role dependencies

**file:** `roles/web_app/meta/main.yml`

```yaml
dependencies:
  - role: docker
```

this ensures docker is automatically installed when deploying the web application.

### web_app role variables

**file:** `roles/web_app/defaults/main.yml`

| variable | default value | description |
|----------|---------------|-------------|
| `app_name` | devops-app | service/container name |
| `app_port` | 5000 | host port |
| `app_internal_port` | 5000 | container port |
| `docker_tag` | v0 | image version |
| `restart_policy` | unless-stopped | container restart policy |
| `compose_project_dir` | /opt/{{ app_name }} | deployment directory |
| `web_app_wipe` | false | wipe control flag |
| `app_healthcheck` | true | enable healthcheck |

### deployment tasks

**file:** `roles/web_app/tasks/main.yml`

the deployment uses `community.docker.docker_compose_v2` module:
1. create app directory
2. log in to docker hub
3. pull docker image
4. template docker-compose.yml
5. deploy with docker compose
6. wait for application to be ready
7. verify health endpoint

---

## 3. wipe logic implementation

### understanding wipe logic

**purpose**: clean removal of deployed applications for:
- clean reinstallation (wipe old → deploy new)
- testing from fresh state
- rolling back to clean slate
- decommissioning applications

**implementation requirements**:
- controlled by variable: `web_app_wipe: true`
- gated by specific tag: `web_app_wipe`
- **not** using the special "never" tag
- default behavior: wipe tasks do **not** run

### wipe tasks

**file:** `roles/web_app/tasks/wipe.yml`

```yaml
- name: Wipe web application
  block:
    - name: Stop and remove containers with docker-compose
      community.docker.docker_compose_v2:
        project_src: "{{ compose_project_dir }}"
        state: absent
      ignore_errors: yes

    - name: Remove docker-compose.yml file
      file:
        path: "{{ compose_project_dir }}/docker-compose.yml"
        state: absent
      ignore_errors: yes

    - name: Remove application directory
      file:
        path: "{{ compose_project_dir }}"
        state: absent

  when: web_app_wipe | bool
  tags:
    - web_app_wipe
```

### double-gating mechanism

why both variable **and** tag?

this provides double safety against accidental data loss:
- the variable prevents accidental wipe when running with tags
- the tag prevents accidental wipe when setting the variable

### test scenarios

**scenario 1: normal deployment (wipe should not run)**
```bash
(venv) λ ~/bucket/courses/uni/devops-s26/ansible/ lab06* ansible-playbook playbooks/deploy.yml

PLAY [Deploy application] ****************************************************************

TASK [Gathering Facts] *******************************************************************
ok: [devops-vm]

TASK [docker : Create directory for Docker GPG key] **************************************
ok: [devops-vm]

TASK [docker : Check if Docker GPG key exists] *******************************************
ok: [devops-vm]

TASK [docker : Add Docker GPG key] *******************************************************
skipping: [devops-vm]

TASK [docker : Add Docker repository] ****************************************************
ok: [devops-vm]

TASK [docker : Install Docker packages] **************************************************
ok: [devops-vm]

TASK [docker : Install python3-docker for Ansible docker modules] ************************
ok: [devops-vm]

TASK [docker : Install docker-compose Python package] ************************************
ok: [devops-vm]

TASK [docker : Ensure Docker service is enabled] *****************************************
ok: [devops-vm]

TASK [docker : Ensure Docker service is running and enabled] *****************************
ok: [devops-vm]

TASK [docker : Add user to docker group] *************************************************
ok: [devops-vm]

TASK [web_app : Include wipe tasks] ******************************************************
included: /Users/s.razmakhov/bucket/courses/uni/devops-s26/ansible/roles/web_app/tasks/wipe.yml for devops-vm

TASK [web_app : Stop and remove containers with docker-compose] **************************
skipping: [devops-vm]

TASK [web_app : Remove docker-compose.yml file] ******************************************
skipping: [devops-vm]

TASK [web_app : Remove application directory] ********************************************
skipping: [devops-vm]

TASK [web_app : Log wipe completion] *****************************************************
skipping: [devops-vm]

TASK [web_app : Create app directory] ****************************************************
ok: [devops-vm]

TASK [web_app : Log in to Docker Hub] ****************************************************
ok: [devops-vm]

TASK [web_app : Pull Docker image] *******************************************************
ok: [devops-vm]

TASK [web_app : Check if old container exists (not managed by compose)] ******************
ok: [devops-vm]

TASK [web_app : Remove old container if exists and not managed by compose] ***************
skipping: [devops-vm]

TASK [web_app : Template docker-compose file] ********************************************
ok: [devops-vm]

TASK [web_app : Deploy with docker-compose] **********************************************
ok: [devops-vm]

TASK [web_app : Wait for application to be ready] ****************************************
ok: [devops-vm]

TASK [web_app : Verify health endpoint] **************************************************
ok: [devops-vm]

PLAY RECAP *******************************************************************************
devops-vm                  : ok=19   changed=0    unreachable=0    failed=0    skipped=6    rescued=0    ignored=0
```

**scenario 2: wipe only**
```bash
ansible-playbook playbooks/deploy.yml -e "web_app_wipe=true" --tags web_app_wipe
(venv) λ ~/bucket/courses/uni/devops-s26/ansible/ lab06* ansible-playbook playbooks/deploy.yml -e "web_app_wipe=true" --tags web_app_wipe

PLAY [Deploy application] ****************************************************************

TASK [Gathering Facts] *******************************************************************
ok: [devops-vm]

TASK [web_app : Include wipe tasks] ******************************************************
included: /Users/s.razmakhov/bucket/courses/uni/devops-s26/ansible/roles/web_app/tasks/wipe.yml for devops-vm

TASK [web_app : Stop and remove containers with docker-compose] **************************
changed: [devops-vm]

TASK [web_app : Remove docker-compose.yml file] ******************************************
changed: [devops-vm]

TASK [web_app : Remove application directory] ********************************************
changed: [devops-vm]

TASK [web_app : Log wipe completion] *****************************************************
ok: [devops-vm] => {
    "msg": "Application devops-app wiped successfully from /opt/devops-app"
}

PLAY RECAP *******************************************************************************
devops-vm                  : ok=6    changed=3    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0
```

**scenario 3: clean reinstallation**
```bash
ansible-playbook playbooks/deploy.yml -e "web_app_wipe=true"
(venv) λ ~/bucket/courses/uni/devops-s26/ansible/ lab06* ansible-playbook playbooks/deploy.yml -e "web_app_wipe=true"

PLAY [Deploy application] ****************************************************************

TASK [Gathering Facts] *******************************************************************
ok: [devops-vm]

TASK [docker : Create directory for Docker GPG key] **************************************
ok: [devops-vm]

TASK [docker : Check if Docker GPG key exists] *******************************************
ok: [devops-vm]

TASK [docker : Add Docker GPG key] *******************************************************
skipping: [devops-vm]

TASK [docker : Add Docker repository] ****************************************************
ok: [devops-vm]

TASK [docker : Install Docker packages] **************************************************
ok: [devops-vm]

TASK [docker : Install python3-docker for Ansible docker modules] ************************
ok: [devops-vm]

TASK [docker : Install docker-compose Python package] ************************************
ok: [devops-vm]

TASK [docker : Ensure Docker service is enabled] *****************************************
ok: [devops-vm]

TASK [docker : Ensure Docker service is running and enabled] *****************************
ok: [devops-vm]

TASK [docker : Add user to docker group] *************************************************
ok: [devops-vm]

TASK [web_app : Include wipe tasks] ******************************************************
included: /Users/s.razmakhov/bucket/courses/uni/devops-s26/ansible/roles/web_app/tasks/wipe.yml for devops-vm

TASK [web_app : Check if compose project directory exists] *******************************
ok: [devops-vm]

TASK [web_app : Stop and remove containers with docker-compose] **************************
skipping: [devops-vm]

TASK [web_app : Remove docker-compose.yml file] ******************************************
ok: [devops-vm]

TASK [web_app : Remove application directory] ********************************************
ok: [devops-vm]

TASK [web_app : Log wipe completion] *****************************************************
ok: [devops-vm] => {
    "msg": "Application devops-app wiped successfully from /opt/devops-app"
}

TASK [web_app : Create app directory] ****************************************************
changed: [devops-vm]

TASK [web_app : Log in to Docker Hub] ****************************************************
ok: [devops-vm]

TASK [web_app : Pull Docker image] *******************************************************
ok: [devops-vm]

TASK [web_app : Check if old container exists (not managed by compose)] ******************
ok: [devops-vm]

TASK [web_app : Remove old container if exists and not managed by compose] ***************
skipping: [devops-vm]

TASK [web_app : Template docker-compose file] ********************************************
changed: [devops-vm]

TASK [web_app : Deploy with docker-compose] **********************************************
changed: [devops-vm]

TASK [web_app : Wait for application to be ready] ****************************************
ok: [devops-vm]

TASK [web_app : Verify health endpoint] **************************************************
ok: [devops-vm]

PLAY RECAP *******************************************************************************
devops-vm                  : ok=23   changed=3    unreachable=0    failed=0    skipped=3    rescued=0    ignored=0
```

**scenario 4: safety check**
```bash
ansible-playbook playbooks/deploy.yml --tags web_app_wipe
(venv) λ ~/bucket/courses/uni/devops-s26/ansible/ lab06* ansible-playbook playbooks/deploy.yml --tags web_app_wipe

PLAY [Deploy application] ****************************************************************

TASK [Gathering Facts] *******************************************************************
ok: [devops-vm]

TASK [web_app : Include wipe tasks] ******************************************************
included: /Users/s.razmakhov/bucket/courses/uni/devops-s26/ansible/roles/web_app/tasks/wipe.yml for devops-vm

TASK [web_app : Check if compose project directory exists] *******************************
skipping: [devops-vm]

TASK [web_app : Stop and remove containers with docker-compose] **************************
skipping: [devops-vm]

TASK [web_app : Remove docker-compose.yml file] ******************************************
skipping: [devops-vm]

TASK [web_app : Remove application directory] ********************************************
skipping: [devops-vm]

TASK [web_app : Log wipe completion] *****************************************************
skipping: [devops-vm]

PLAY RECAP *******************************************************************************
devops-vm                  : ok=2    changed=0    unreachable=0    failed=0    skipped=5    rescued=0    ignored=0
```

### research questions

| question | answer |
|----------|--------|
| why use both variable and tag? | this provides double safety against accidental data loss. the variable prevents accidental wipe when running with tags, and the tag prevents accidental wipe when setting the variable. |
| what's the difference between `never` tag and this approach? | the `never` tag would require explicitly listing the tag to run those tasks, but combining with a variable gives more flexibility. with our approach, we can run wipe+deploy in one command for clean reinstallation. |
| why must wipe logic come before deployment in main.yml? | this enables the clean reinstallation use case - wipe removes the old installation, then deployment creates a fresh one. if wipe came after, you'd lose your new deployment. |
| when would you want clean reinstallation vs. rolling update? | clean reinstallation: major version upgrades, corrupted state, testing from scratch, changing fundamental configuration. rolling updates: zero-downtime deployments, minor updates, preserving data. |
| how would you extend this to wipe docker images and volumes too? | add tasks to remove the image with `docker_image: state: absent` and add `remove_volumes: true` to the docker_compose task. |

---

## 4. ci/cd with github actions

### workflow structure

**file:** `.github/workflows/ansible-deploy.yml`

```
code push → lint ansible → run ansible playbook → verify deployment
```

### workflow configuration

```yaml
name: Ansible Deployment

on:
  push:
    branches: [ master, main ]
    paths:
      - 'ansible/**'
      - '!ansible/docs/**'
      - '.github/workflows/ansible-deploy.yml'
  pull_request:
    branches: [ master, main ]
    paths:
      - 'ansible/**'
      - '!ansible/docs/**'

jobs:
  lint:
    name: Ansible Lint
    runs-on: ubuntu-latest
    # ansible-lint for syntax checking

  deploy:
    name: Deploy Application
    needs: lint
    runs-on: ubuntu-latest
    if: github.event_name == 'push'
    # deployment steps
```

### path filters

why path filters?
- don't run ansible workflow when changing docs
- separate workflows for different concerns
- faster ci, lower costs

### required github secrets

| secret | description |
|--------|-------------|
| `ANSIBLE_VAULT_PASSWORD` | password to decrypt ansible vault |
| `SSH_PRIVATE_KEY` | ssh key for target vm access |
| `VM_HOST` | target vm ip address |

### deployment steps

1. checkout code
2. set up python 3.12
3. install ansible and community.docker collection
4. configure ssh for remote access
5. run ansible-playbook with vault password
6. verify deployment with health check

### verification step

[successful deploy and verification](screenshots/00-ansible-deploy.png)

### research questions

| question | answer |
|----------|--------|
| what are the security implications of storing ssh keys in github secrets? | github secrets are encrypted at rest and in transit, only exposed to workflow runs. however, they can be leaked through workflow logs if not careful. use `no_log: true` and avoid echoing secrets. |
| how would you implement a staging → production deployment pipeline? | create separate workflows for staging and production, use environment protection rules, require approvals for production, use different branches or tags. |
| what would you add to make rollbacks possible? | store previous docker image tags, implement a rollback workflow that deploys the previous version, use git tags to track releases, implement blue-green deployments. |
| how does self-hosted runner improve security compared to github-hosted? | self-hosted runners keep secrets on your infrastructure, avoid sharing compute with other users, allow network access to internal resources, and provide more control over the execution environment. |

---

## 6. key decisions

| question | answer |
|----------|--------|
| why use blocks instead of individual tasks? | blocks provide logical grouping, shared directives, and error handling with rescue/always sections |
| why docker compose over docker run? | declarative configuration, multi-container support, easier updates, better for production |
| why double-gating for wipe logic? | prevents accidental data loss through two independent safety mechanisms |
| why include wipe before deployment? | enables clean reinstallation scenario - remove old, then install fresh |
| why path filters in ci/cd? | avoid unnecessary workflow runs, faster feedback, lower costs |

---

## 7. challenges

### docker compose module

**problem**: need to use `community.docker.docker_compose_v2` module.

**solution**: installed collection and pip package:
```bash
ansible-galaxy collection install community.docker
pip install docker-compose
```

### role rename

**problem**: existing role `app_deploy` needed to be renamed to `web_app`.

**solution**: renamed directory and updated all references in playbooks.

### wipe logic timing

**problem**: wipe tasks need to run before deployment for clean reinstall.

**solution**: included wipe tasks at the beginning of main.yml, using tags to control execution independently.
