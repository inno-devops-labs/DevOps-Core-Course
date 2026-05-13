# Documentation

## Overview (What you accomplished and technologies used)

- My stack consisted of Ansible core 2.20.2, Docker Compose 2.39.2, Jinja 3.1.6, python 3.11.9.
- I've accomplished refactoring the roles for using with docker-compose, implemented a wipe logic, and set up a new CI/CD worflow.

## Blocks & Tags (Block usage in each role, tag strategy, execution examples with screenshots)

All tags are made for quick understanding of the block usage.

### Common role

- block with package installation tasks (tag: packages)
- block with user creation (tag: users)
- block with timezone set up (tag: timezone)

### Docker role

- block with docker installation and set up (tag: docker_install)
- block with docker configuration (tag: docker_config)

### Web-app role

- block for app deployment with docker compose and possible wipe logic (from wipe.yaml with tag web_app_wipe), (tags: app_deploy, compose)

## Screenshots and terminal outputs

### Test provision with only docker
![](./screenshots/lab06-shots/Test%20provision%20with%20only%20docker.png)

### Skip common role
![](./screenshots/lab06-shots/Skip%20common%20role.png)

### Install packages only across all roles
![](./screenshots/lab06-shots/Install%20packages%20only%20across%20all%20roles.png)

### Check mode to see what would run
![](./screenshots/lab06-shots/Check%20mode%20to%20see%20what%20would%20run.png)

### Run only docker installation tasks
![](./screenshots/lab06-shots/Run%20only%20docker%20installation%20tasks.png)

### Error handling with rescue block triggered

```bash
(devops) fountainer@Veronicas-MacBook-Air ansible % ansible-playbook playbooks/provision.yml --tags "docker_install"

PLAY [Provision web servers] ********************************************************************************************************************************************

TASK [Gathering Facts] **************************************************************************************************************************************************
ok: [terraform]

TASK [docker : Install prerequisites] ***********************************************************************************************************************************
ok: [terraform]

TASK [docker : Add Docker GPG key] **************************************************************************************************************************************
[ERROR]: Task failed: Module failed: unknown url type: 'blabla'
Origin: /Users/fountainer/uni/devops/DevOps-Core-Course/app_python/ansible/roles/docker/tasks/main.yml:14:7

12         state: present
13         update_cache: yes
14     - name: Add Docker GPG key
         ^ column 7

fatal: [terraform]: FAILED! => {"changed": false, "msg": "unknown url type: 'blabla'", "status": -1, "url": "blabla"}

TASK [docker : Wait before retry] ***************************************************************************************************************************************
Pausing for 10 seconds
(ctrl+C then 'C' = continue early, ctrl+C then 'A' = abort)
ok: [terraform]

TASK [docker : Retry apt update] ****************************************************************************************************************************************
changed: [terraform]

TASK [docker : Retry adding Docker GPG key] *****************************************************************************************************************************
ok: [terraform]

TASK [docker : ensure docker service is enabled] ************************************************************************************************************************
ok: [terraform]

PLAY RECAP **************************************************************************************************************************************************************
terraform                  : ok=6    changed=1    unreachable=0    failed=0    skipped=0    rescued=1    ignored=0   
```

### List all available tags

```bash
(devops) fountainer@Veronicas-MacBook-Air ansible % ansible-playbook playbooks/provision.yml --list-tags

playbook: playbooks/provision.yml

  play #1 (webservers): Provision web servers   TAGS: []
      TASK TAGS: [common, docker, docker_config, docker_install, packages, timezone, users]
```

## Docker Compose Migration (Template structure, role dependencies, before/after comparison)

### Comparison

- docker-compose provides richer functionality to set up env variables, dependencies, and configs, compared to just the docker container

- docker-compose.yaml.j2

```yml
version: '{{ docker_compose_version }}'

services:
  {{ app_name }}:
    image: {{ web_app_docker_image }}:{{ web_app_docker_tag }}

    ports:
      - "{{ app_port }}:{{ app_internal_port }}"

    restart: unless-stopped

    environment:
{% for key, value in web_app_env.items() %}
      {{ key }}: "{{ value }}"
{% endfor %}

    networks:
      - {{ app_name }}_network

networks:
  {{ app_name }}_network:
    driver: bridge
```

### First run

```bash
(devops) fountainer@Veronicas-MacBook-Air ansible % ansible-playbook playbooks/deploy.yml --extra-vars @./group_vars/all.yml

PLAY [Deploy application] *****************************************************************************************************************************************

TASK [Gathering Facts] ********************************************************************************************************************************************
ok: [terraform]

TASK [docker : Install prerequisites] *****************************************************************************************************************************
ok: [terraform]

TASK [docker : Add Docker GPG key] ********************************************************************************************************************************
ok: [terraform]

TASK [docker : Add Docker APT repository] *************************************************************************************************************************
[WARNING]: Deprecation warnings can be disabled by setting `deprecation_warnings=False` in ansible.cfg.
[DEPRECATION WARNING]: INJECT_FACTS_AS_VARS default to `True` is deprecated, top-level facts will not be auto injected after the change. This feature will be removed from ansible-core version 2.24.
Origin: /Users/fountainer/uni/devops/DevOps-Core-Course/app_python/ansible/roles/docker/defaults/main.yml:7:14

5 docker_user: "ubuntu"
6 docker_gpg_url: "https://download.docker.com/linux/ubuntu/gpg"
7 docker_repo: "deb [arch=amd64] https://download.docker.com/linux/ubuntu {{ ansible_distribution_release }} stable"
               ^ column 14

Use `ansible_facts["fact_name"]` (no `ansible_` prefix) instead.

ok: [terraform]

TASK [docker : Install Docker packages] ***************************************************************************************************************************
ok: [terraform]

TASK [docker : Install python3-docker for Ansible Docker modules] *************************************************************************************************
ok: [terraform]

TASK [docker : ensure docker service is enabled] ******************************************************************************************************************
ok: [terraform]

TASK [docker : Add user to Docker group] **************************************************************************************************************************
ok: [terraform]

TASK [web_app : Create application directory] *********************************************************************************************************************
ok: [terraform]

TASK [web_app : Template docker-compose.yml] **********************************************************************************************************************
changed: [terraform]

TASK [web_app : Deploy with Docker Compose] ***********************************************************************************************************************
[WARNING]: Docker compose: unknown None: /opt/my-app/docker-compose.yml: the attribute `version` is obsolete, it will be ignored, please remove it to avoid potential confusion
changed: [terraform]

TASK [web_app : Log deployment attempt] ***************************************************************************************************************************
[DEPRECATION WARNING]: INJECT_FACTS_AS_VARS default to `True` is deprecated, top-level facts will not be auto injected after the change. This feature will be removed from ansible-core version 2.24.
Origin: /Users/fountainer/uni/devops/DevOps-Core-Course/app_python/ansible/roles/web_app/tasks/main.yml:33:18

31     - name: Log deployment attempt
32       copy:
33         content: "Docker Compose deployment attempted on {{ ansible_date_time.iso8601 }}"
                    ^ column 18

Use `ansible_facts["fact_name"]` (no `ansible_` prefix) instead.

changed: [terraform]

PLAY RECAP ********************************************************************************************************************************************************
terraform                  : ok=12   changed=3    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0 
```

### Second run removed "changed" status of some fields (not with the current time)

```bash
TASK [web_app : Template docker-compose.yml] **********************************************************************************************************************
ok: [terraform]

TASK [web_app : Deploy with Docker Compose] ***********************************************************************************************************************
[WARNING]: Docker compose: unknown None: /opt/my-app/docker-compose.yml: the attribute `version` is obsolete, it will be ignored, please remove it to avoid potential confusion
ok: [terraform]
```

### Verifying on target VM

```bash
ubuntu@fhmebroid75qocec3dc3:~$ docker ps
CONTAINER ID   IMAGE                      COMMAND           CREATED          STATUS          PORTS                                           NAMES
7c279d0b3c18   fountainer/my-app:latest   "python app.py"   10 minutes ago   Up 10 minutes   0.0.0.0:1999->12345/tcp, [::]:1999->12345/tcp   my-app-my-app-1
0a0701a21e3a   9582a1fe4631               "python app.py"   25 hours ago     Up 25 hours     0.0.0.0:8080->12345/tcp                         my-app
ubuntu@fhmebroid75qocec3dc3:~$ curl http://localhost:1999
{
  "message": {
    "endpoints": [
      {
        "description": "Service information",
        "method": "GET",
        "path": "/"
      },
      {
        "description": "Health check",
        "method": "GET",
        "path": "/health"
      }
    ],
    "request": {
      "client_ip": "127.0.0.1",
      "method": "GET",
      "path": "/",
      "port": 12345,
      "user_agent": "curl/7.81.0"
    },
    "runtime": {
      "current_time": "2026-01-07T14:30:00.000Z",
      "timezone": "UTC",
      "uptime_human": "1 hour, 0 minutes",
      "uptime_seconds": {
        "human": "0 hours, 0 minutes",
        "seconds": 0
      }
    },
    "service": {
      "debug status": true,
      "description": "DevOps course info service",
      "framework": "Flask",
      "name": "devops-info-service",
      "version": "1.0.0"
    },
    "system": {
      "architecture": "x86_64",
      "cpu_count": 8,
      "hostname": "7c279d0b3c18",
      "platform": "Linux",
      "platform_version": "Ubuntu 24.04",
      "python_version": "3.13.12"
    }
  }
}
ubuntu@fhmebroid75qocec3dc3:~$ 
```

## Wipe Logic (Implementation details, variable + tag approach, test results)

- Implementation details can be seen in ansible/roles/web-app/tasks/wipe.yml.

- The tag is web_app_wipe, the task is triggered by "when: web_app_wipe | bool"

- Variables: "{{ web_app_compose_project_dir }}", "{{ ansible_check_mode }}", {{ app_name }}

### Scenario 1: Normal deployment (wipe should NOT run)

```bash
(devops) fountainer@Veronicas-MacBook-Air ansible % ansible-playbook playbooks/deploy.yml --extra-vars @./group_vars/all.yml

PLAY [Deploy application] *****************************************************************************************************************************************

TASK [Gathering Facts] ********************************************************************************************************************************************
ok: [terraform]

TASK [docker : Install prerequisites] *****************************************************************************************************************************
ok: [terraform]

TASK [docker : Add Docker GPG key] ********************************************************************************************************************************
ok: [terraform]

TASK [docker : Add Docker APT repository] *************************************************************************************************************************
[WARNING]: Deprecation warnings can be disabled by setting `deprecation_warnings=False` in ansible.cfg.
[DEPRECATION WARNING]: INJECT_FACTS_AS_VARS default to `True` is deprecated, top-level facts will not be auto injected after the change. This feature will be removed from ansible-core version 2.24.
Origin: /Users/fountainer/uni/devops/DevOps-Core-Course/app_python/ansible/roles/docker/defaults/main.yml:7:14

5 docker_user: "ubuntu"
6 docker_gpg_url: "https://download.docker.com/linux/ubuntu/gpg"
7 docker_repo: "deb [arch=amd64] https://download.docker.com/linux/ubuntu {{ ansible_distribution_release }} stable"
               ^ column 14

Use `ansible_facts["fact_name"]` (no `ansible_` prefix) instead.

ok: [terraform]

TASK [docker : Install Docker packages] ***************************************************************************************************************************
ok: [terraform]

TASK [docker : Install python3-docker for Ansible Docker modules] *************************************************************************************************
ok: [terraform]

TASK [docker : ensure docker service is enabled] ******************************************************************************************************************
ok: [terraform]

TASK [docker : Add user to Docker group] **************************************************************************************************************************
ok: [terraform]

TASK [web_app : Create application directory] *********************************************************************************************************************
ok: [terraform]

TASK [web_app : Template docker-compose.yml] **********************************************************************************************************************
ok: [terraform]

TASK [web_app : Include wipe tasks] *******************************************************************************************************************************
included: /Users/fountainer/uni/devops/DevOps-Core-Course/app_python/ansible/roles/web_app/tasks/wipe.yml for terraform

TASK [web_app : Stop and remove containers] ***********************************************************************************************************************
skipping: [terraform]

TASK [web_app : Remove docker-compose file] ***********************************************************************************************************************
skipping: [terraform]

TASK [web_app : Remove application directory] *********************************************************************************************************************
skipping: [terraform]

TASK [web_app : Log wipe completion] ******************************************************************************************************************************
skipping: [terraform]

TASK [web_app : Deploy with Docker Compose] ***********************************************************************************************************************
[WARNING]: Docker compose: unknown None: /opt/my-app/docker-compose.yml: the attribute `version` is obsolete, it will be ignored, please remove it to avoid potential confusion
ok: [terraform]

TASK [web_app : Log deployment attempt] ***************************************************************************************************************************
[DEPRECATION WARNING]: INJECT_FACTS_AS_VARS default to `True` is deprecated, top-level facts will not be auto injected after the change. This feature will be removed from ansible-core version 2.24.
Origin: /Users/fountainer/uni/devops/DevOps-Core-Course/app_python/ansible/roles/web_app/tasks/main.yml:38:18

36     - name: Log deployment attempt
37       copy:
38         content: "Docker Compose deployment attempted on {{ ansible_date_time.iso8601 }}"
                    ^ column 18

Use `ansible_facts["fact_name"]` (no `ansible_` prefix) instead.

changed: [terraform]

PLAY RECAP ********************************************************************************************************************************************************
terraform                  : ok=13   changed=1    unreachable=0    failed=0    skipped=4    rescued=0    ignored=0   

(devops) fountainer@Veronicas-MacBook-Air ansible % 
```

```bash
(devops) fountainer@Veronicas-MacBook-Air ansible % ssh ubuntu@93.77.181.173 "docker ps"
CONTAINER ID   IMAGE                      COMMAND           CREATED          STATUS          PORTS                                           NAMES
7c279d0b3c18   fountainer/my-app:latest   "python app.py"   21 minutes ago   Up 21 minutes   0.0.0.0:1999->12345/tcp, [::]:1999->12345/tcp   my-app-my-app-1
0a0701a21e3a   9582a1fe4631               "python app.py"   25 hours ago     Up 25 hours     0.0.0.0:8080->12345/tcp                         my-app
(devops) fountainer@Veronicas-MacBook-Air ansible % 
```

### Scenario 2: Wipe only (remove existing deployment)

```bash
(devops) fountainer@Veronicas-MacBook-Air ansible % ansible-playbook playbooks/deploy.yml -e "web_app_wipe=true" --tags web_app_wipe --extra-vars @./group_vars/all.yml

PLAY [Deploy application] *****************************************************************************************************************************************

TASK [Gathering Facts] ********************************************************************************************************************************************
ok: [terraform]

TASK [web_app : Include wipe tasks] *******************************************************************************************************************************
included: /Users/fountainer/uni/devops/DevOps-Core-Course/app_python/ansible/roles/web_app/tasks/wipe.yml for terraform

TASK [web_app : Stop and remove containers] ***********************************************************************************************************************
[ERROR]: Task failed: Module failed: "/opt/my-app" is not a directory
Origin: /Users/fountainer/uni/devops/DevOps-Core-Course/app_python/ansible/roles/web_app/tasks/wipe.yml:5:7

3   block:
4
5     - name: Stop and remove containers
        ^ column 7

fatal: [terraform]: FAILED! => {"changed": false, "msg": "\"/opt/my-app\" is not a directory"}
...ignoring

TASK [web_app : Remove docker-compose file] ***********************************************************************************************************************
ok: [terraform]

TASK [web_app : Remove application directory] *********************************************************************************************************************
ok: [terraform]

TASK [web_app : Log wipe completion] ******************************************************************************************************************************
ok: [terraform] => {
    "msg": "Application my-app wiped successfully"
}

PLAY RECAP ********************************************************************************************************************************************************
terraform                  : ok=6    changed=0    unreachable=0    failed=0    skipped=0    rescued=0    ignored=1   
```

```bash
(devops) fountainer@Veronicas-MacBook-Air ansible % ssh ubuntu@93.77.181.173 "docker ps"               
CONTAINER ID   IMAGE     COMMAND   CREATED   STATUS    PORTS     NAMES
(devops) fountainer@Veronicas-MacBook-Air ansible % ssh ubuntu@93.77.181.173 "ls /opt"                 
containerd
(devops) fountainer@Veronicas-MacBook-Air ansible %
```

### Scenario 3: Clean reinstallation (wipe → deploy)

```bash
(devops) fountainer@Veronicas-MacBook-Air ansible % ansible-playbook playbooks/deploy.yml -e "web_app_wipe=true" --extra-vars @./group_vars/all.yml

PLAY [Deploy application] *****************************************************************************************************************************************

TASK [Gathering Facts] ********************************************************************************************************************************************
ok: [terraform]

TASK [docker : Install prerequisites] *****************************************************************************************************************************
ok: [terraform]

TASK [docker : Add Docker GPG key] ********************************************************************************************************************************
ok: [terraform]

TASK [docker : Add Docker APT repository] *************************************************************************************************************************
[WARNING]: Deprecation warnings can be disabled by setting `deprecation_warnings=False` in ansible.cfg.
[DEPRECATION WARNING]: INJECT_FACTS_AS_VARS default to `True` is deprecated, top-level facts will not be auto injected after the change. This feature will be removed from ansible-core version 2.24.
Origin: /Users/fountainer/uni/devops/DevOps-Core-Course/app_python/ansible/roles/docker/defaults/main.yml:7:14

5 docker_user: "ubuntu"
6 docker_gpg_url: "https://download.docker.com/linux/ubuntu/gpg"
7 docker_repo: "deb [arch=amd64] https://download.docker.com/linux/ubuntu {{ ansible_distribution_release }} stable"
               ^ column 14

Use `ansible_facts["fact_name"]` (no `ansible_` prefix) instead.

ok: [terraform]

TASK [docker : Install Docker packages] ***************************************************************************************************************************
ok: [terraform]

TASK [docker : Install python3-docker for Ansible Docker modules] *************************************************************************************************
ok: [terraform]

TASK [docker : ensure docker service is enabled] ******************************************************************************************************************
ok: [terraform]

TASK [docker : Add user to Docker group] **************************************************************************************************************************
ok: [terraform]

TASK [web_app : Include wipe tasks] *******************************************************************************************************************************
included: /Users/fountainer/uni/devops/DevOps-Core-Course/app_python/ansible/roles/web_app/tasks/wipe.yml for terraform

TASK [web_app : Stop and remove containers] ***********************************************************************************************************************
[ERROR]: Task failed: Module failed: "/opt/my-app" is not a directory
Origin: /Users/fountainer/uni/devops/DevOps-Core-Course/app_python/ansible/roles/web_app/tasks/wipe.yml:5:7

3   block:
4
5     - name: Stop and remove containers
        ^ column 7

fatal: [terraform]: FAILED! => {"changed": false, "msg": "\"/opt/my-app\" is not a directory"}
...ignoring

TASK [web_app : Remove docker-compose file] ***********************************************************************************************************************
ok: [terraform]

TASK [web_app : Remove application directory] *********************************************************************************************************************
ok: [terraform]

TASK [web_app : Log wipe completion] ******************************************************************************************************************************
ok: [terraform] => {
    "msg": "Application my-app wiped successfully"
}

TASK [web_app : Create application directory] *********************************************************************************************************************
changed: [terraform]

TASK [web_app : Template docker-compose.yml] **********************************************************************************************************************
changed: [terraform]

TASK [web_app : Deploy with Docker Compose] ***********************************************************************************************************************
[WARNING]: Docker compose: unknown None: /opt/my-app/docker-compose.yml: the attribute `version` is obsolete, it will be ignored, please remove it to avoid potential confusion
changed: [terraform]

TASK [web_app : Log deployment attempt] ***************************************************************************************************************************
[DEPRECATION WARNING]: INJECT_FACTS_AS_VARS default to `True` is deprecated, top-level facts will not be auto injected after the change. This feature will be removed from ansible-core version 2.24.
Origin: /Users/fountainer/uni/devops/DevOps-Core-Course/app_python/ansible/roles/web_app/tasks/main.yml:37:18

35     - name: Log deployment attempt
36       copy:
37         content: "Docker Compose deployment attempted on {{ ansible_date_time.iso8601 }}"
                    ^ column 18

Use `ansible_facts["fact_name"]` (no `ansible_` prefix) instead.

changed: [terraform]

PLAY RECAP ********************************************************************************************************************************************************
terraform                  : ok=17   changed=4    unreachable=0    failed=0    skipped=0    rescued=0    ignored=1 
```

```bash
(devops) fountainer@Veronicas-MacBook-Air ansible % ssh ubuntu@93.77.181.173 "docker ps"               
CONTAINER ID   IMAGE                      COMMAND           CREATED          STATUS          PORTS                                           NAMES
167ea730bdc1   fountainer/my-app:latest   "python app.py"   20 seconds ago   Up 19 seconds   0.0.0.0:1999->12345/tcp, [::]:1999->12345/tcp   my-app-my-app-1
```
### Scenario 4: Safety checks (should NOT wipe)

```bash
(devops) fountainer@Veronicas-MacBook-Air ansible % ansible-playbook playbooks/deploy.yml --tags web_app_wipe --extra-vars @./group_vars/all.yml

PLAY [Deploy application] *****************************************************************************************************************************************

TASK [Gathering Facts] ********************************************************************************************************************************************
ok: [terraform]

TASK [web_app : Include wipe tasks] *******************************************************************************************************************************
included: /Users/fountainer/uni/devops/DevOps-Core-Course/app_python/ansible/roles/web_app/tasks/wipe.yml for terraform

TASK [web_app : Stop and remove containers] ***********************************************************************************************************************
skipping: [terraform]

TASK [web_app : Remove docker-compose file] ***********************************************************************************************************************
skipping: [terraform]

TASK [web_app : Remove application directory] *********************************************************************************************************************
skipping: [terraform]

TASK [web_app : Log wipe completion] ******************************************************************************************************************************
skipping: [terraform]

PLAY RECAP ********************************************************************************************************************************************************
terraform                  : ok=2    changed=0    unreachable=0    failed=0    skipped=4    rescued=0    ignored=0   

(devops) fountainer@Veronicas-MacBook-Air ansible % 
```

```bash
(devops) fountainer@Veronicas-MacBook-Air ansible % ansible-playbook playbooks/deploy.yml -e "web_app_wipe=true" --tags web_app_wipe --extra-vars @./group_vars/all.yml

PLAY [Deploy application] *****************************************************************************************************************************************

TASK [Gathering Facts] ********************************************************************************************************************************************
ok: [terraform]

TASK [web_app : Include wipe tasks] *******************************************************************************************************************************
included: /Users/fountainer/uni/devops/DevOps-Core-Course/app_python/ansible/roles/web_app/tasks/wipe.yml for terraform

TASK [web_app : Stop and remove containers] ***********************************************************************************************************************
[WARNING]: Docker compose: unknown None: /opt/my-app/docker-compose.yml: the attribute `version` is obsolete, it will be ignored, please remove it to avoid potential confusion
changed: [terraform]

TASK [web_app : Remove docker-compose file] ***********************************************************************************************************************
changed: [terraform]

TASK [web_app : Remove application directory] *********************************************************************************************************************
changed: [terraform]

TASK [web_app : Log wipe completion] ******************************************************************************************************************************
ok: [terraform] => {
    "msg": "Application my-app wiped successfully"
}

PLAY RECAP ********************************************************************************************************************************************************
terraform                  : ok=6    changed=3    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0
```

### App running after complete reinstall

![](./screenshots/lab06-shots/app%20running%20after%20clean%20reinstall.png)


## CI/CD Integration (Workflow architecture, setup steps, evidence of automated deployments)

### Workflow

- this workflow runs ansible-lint on pushes and pr’s first to catch errors, then deploys the app automatically on master/lab06 branches

### Setup steps

- setup steps include checking out code, installing python and ansible, configuring ssh with github secrets, decoding vault vars, and running the playbook remotely

### Evidence

- evidence of automated deployment is in the deploy job: it ssh’s to the vm, runs ansible-playbook with vault and extra vars, then verifies the app with curl requests

![](./screenshots/lab06-shots/ci:cd%20success.png)

Terminal output:

```bash
ssh -i ~/.ssh/terraform-vm-key ubuntu@*** "echo connected"
  
  echo '***' > /tmp/vault_pass
  cd app_python/ansible
  
  ansible-playbook playbooks/deploy.yml \
    -i inventory/hosts.ini \
    --vault-password-file /tmp/vault_pass \
    --extra-vars @./group_vars/all.yml
  
  rm /tmp/vault_pass
  shell: /usr/bin/bash -e {0}
  env:
    pythonLocation: /opt/hostedtoolcache/Python/3.12.12/x64
    PKG_CONFIG_PATH: /opt/hostedtoolcache/Python/3.12.12/x64/lib/pkgconfig
    Python_ROOT_DIR: /opt/hostedtoolcache/Python/3.12.12/x64
    Python2_ROOT_DIR: /opt/hostedtoolcache/Python/3.12.12/x64
    Python3_ROOT_DIR: /opt/hostedtoolcache/Python/3.12.12/x64
    LD_LIBRARY_PATH: /opt/hostedtoolcache/Python/3.12.12/x64/lib
connected

PLAY [Deploy application] ******************************************************

TASK [Gathering Facts] *********************************************************
ok: [terraform]

TASK [docker : Install prerequisites] ******************************************
ok: [terraform]

TASK [docker : Add Docker GPG key] *********************************************
ok: [terraform]
Warning: : Deprecation warnings can be disabled by setting `deprecation_warnings=False` in ansible.cfg.

TASK [docker : Add Docker APT repository] **************************************
[DEPRECATION WARNING]: INJECT_FACTS_AS_VARS default to `True` is deprecated, top-level facts will not be auto injected after the change. This feature will be removed from ansible-core version 2.24.
Origin: /home/runner/work/DevOps-Core-Course/DevOps-Core-Course/app_python/ansible/roles/docker/defaults/main.yml:8:14

6 docker_user: "ubuntu"
7 docker_gpg_url: "https://download.docker.com/linux/ubuntu/gpg"
8 docker_repo: "deb [arch=amd64] https://download.docker.com/linux/ubuntu {{ ansible_distribution_release }} stable"
               ^ column 14

Use `ansible_facts["fact_name"]` (no `ansible_` prefix) instead.

ok: [terraform]

TASK [docker : Install Docker packages] ****************************************
ok: [terraform]

TASK [docker : Install python3-docker for Ansible Docker modules] **************
ok: [terraform]

TASK [docker : Ensure docker service is enabled] *******************************
ok: [terraform]

TASK [docker : Add user to Docker group] ***************************************
ok: [terraform]

TASK [web_app : Include wipe tasks] ********************************************
included: /home/runner/work/DevOps-Core-Course/DevOps-Core-Course/app_python/ansible/roles/web_app/tasks/wipe.yml for terraform

TASK [web_app : Stop and remove containers] ************************************
skipping: [terraform]

TASK [web_app : Remove docker-compose file] ************************************
skipping: [terraform]

TASK [web_app : Remove application directory] **********************************
skipping: [terraform]

TASK [web_app : Log wipe completion] *******************************************
skipping: [terraform]

TASK [web_app : Create application directory] **********************************
ok: [terraform]

TASK [web_app : Template docker-compose.yml] ***********************************
ok: [terraform]

TASK [web_app : Deploy with Docker Compose] ************************************
Warning: : Docker compose: unknown None: /opt/my-app/docker-compose.yml: the attribute `version` is obsolete, it will be ignored, please remove it to avoid potential confusion
ok: [terraform]

TASK [web_app : Log deployment attempt] ****************************************
[DEPRECATION WARNING]: INJECT_FACTS_AS_VARS default to `True` is deprecated, top-level facts will not be auto injected after the change. This feature will be removed from ansible-core version 2.24.
Origin: /home/runner/work/DevOps-Core-Course/DevOps-Core-Course/app_python/ansible/roles/web_app/tasks/main.yml:41:18

39     - name: Log deployment attempt
40       ansible.builtin.copy:
41         content: "Docker Compose deployment attempted on {{ ansible_date_time.iso8601 }}"
                    ^ column 18

Use `ansible_facts["fact_name"]` (no `ansible_` prefix) instead.

changed: [terraform]

PLAY RECAP *********************************************************************
terraform                  : ok=13   changed=1    unreachable=0    failed=0    skipped=4    rescued=0    ignored=0   

  sleep 10
  curl -f http://***:1999 || exit 1
  curl -f http://***:1999/health || exit 1
  shell: /usr/bin/bash -e {0}
  env:
    pythonLocation: /opt/hostedtoolcache/Python/3.12.12/x64
    PKG_CONFIG_PATH: /opt/hostedtoolcache/Python/3.12.12/x64/lib/pkgconfig
    Python_ROOT_DIR: /opt/hostedtoolcache/Python/3.12.12/x64
    Python2_ROOT_DIR: /opt/hostedtoolcache/Python/3.12.12/x64
    Python3_ROOT_DIR: /opt/hostedtoolcache/Python/3.12.12/x64
    LD_LIBRARY_PATH: /opt/hostedtoolcache/Python/3.12.12/x64/lib
  % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                 Dload  Upload   Total   Spent    Left  Speed

  0     0    0     0    0     0      0      0 --:--:-- --:--:-- --:--:--     0
  0  1058    0     0    0     0      0      0 --:--:-- --:--:-- --:--:--     0
100  1058  100  1058    0     0   4059      0 --:--:-- --:--:-- --:--:--  4053
{
  "message": {
    "endpoints": [
      {
        "description": "Service information",
        "method": "GET",
        "path": "/"
      },
      {
        "description": "Health check",
        "method": "GET",
        "path": "/health"
      }
    ],
    "request": {
      "client_ip": "127.0.0.1",
      "method": "GET",
      "path": "/",
      "port": 12345,
      "user_agent": "curl/7.81.0"
    },
    "runtime": {
      "current_time": "2026-01-07T14:30:00.000Z",
      "timezone": "UTC",
      "uptime_human": "1 hour, 0 minutes",
      "uptime_seconds": {
        "human": "0 hours, 0 minutes",
        "seconds": 0
      }
    },
    "service": {
      "debug status": true,
      "description": "DevOps course info service",
      "framework": "Flask",
      "name": "devops-info-service",
      "version": "1.0.0"
    },
    "system": {
      "architecture": "x86_64",
      "cpu_count": 8,
      "hostname": "8081285df89f",
      "platform": "Linux",
      "platform_version": "Ubuntu 24.04",
      "python_version": "3.13.12"
    }
  }
}
  % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                 Dload  Upload   Total   Spent    Left  Speed

  0     0    0     0    0     0      0      0 --:--:-- --:--:-- --:--:--     0
100    99  100    99    0     0    364      0 --:--:-- --:--:-- --:--:--   365
{
  "status": "healthy",
  "timestamp": "2026-03-07T16:04:23.506918",
  "uptime_seconds": 146470
}
```

## Testing Results (All test scenarios, idempotency verification, application accessibility)

- all testing results are provided in the corresponding sections above

## Challenges & Solutions (Difficulties encountered and how you solved them)

- I had a hard time making ssh connection work in the github actions and wasted 2 days after the deadline for this... it was eventually solved by generating new ssh pair and coniguring vm's authorised keys again.

## Research Answers (All research questions answered with analysis)

### 1.3

Q1: What happens if rescue block also fails?

- if the rescue block fails, ansible just shows an error and moves on to the always block. it won’t stop the playbook completely

Q2: Can you have nested blocks?

- yes, you can nest blocks inside other blocks, each with their own rescue/always if needed

Q3: How do tags inherit to tasks within blocks?

- tags on a block automatically apply to all tasks inside, but you can override or add extra tags per task

### 2.3

Q1: What's the difference between restart: always and restart: unless-stopped?

- restart: always makes the container restart no matter what, even if you stop it manually. unless-stopped restarts it only if it crashes or docker restarts, but not if you stopped it yourself

Q2: How do Docker Compose networks differ from Docker bridge networks?

- docker compose networks are defined per project and let containers talk using service names. bridge networks are default docker networks, simpler and not tied to a compose project

Q3: Can you reference Ansible Vault variables in the template?

- yes, you can use ansible vault variables in templates by referencing them like any other ansible variable ({{ vault_var_name }})

### 2.5

Q1: Look up community.docker.docker_compose_v2 module

- community.docker.docker_compose_v2 manages compose projects using docker compose v2 cli under the hood, can pull images, recreate services, and set project source

Q2: Compare state: present vs other state options

- state: present makes sure services are running, absent removes them, stopped just stops without removing, restarted forces a restart

Q3: Understand recreate parameter options

- recreate: auto only recreates changed containers, never won’t recreate, force always recreates even if unchanged

### 3.6

Q1: Why use both variable AND tag? (Double safety mechanism)

- using both variable and tag is double safety: the variable controls behavior in code, tag controls execution from command line

Q2: What's the difference between never tag and this approach?

- never tag completely ignores tasks unless explicitly forced, this approach lets you selectively run blocks with normal tags

Q3: Why must wipe logic come BEFORE deployment in main.yml? (Clean reinstall scenario)

- wipe logic must run first to remove old containers/configs so deployment starts clean, avoids conflicts or leftover data

Q4: When would you want clean reinstallation vs. rolling update?

- clean reinstall is good if configs or images changed, rolling update is better for small changes with minimal downtime

Q5: How would you extend this to wipe Docker images and volumes too?

- extend wipe by adding tasks that remove docker images (docker_image module) and volumes (docker_volume module) before deployment

### 4.10

Q1: What are the security implications of storing SSH keys in GitHub Secrets?

- storing ssh keys in github secrets is safe if encrypted, but exposure risk exists if repo or workflows are misconfigured

Q2: How would you implement a staging → production deployment pipeline?

- implement staging → production by having two environments, separate compose dirs, and deploy to staging first, then promote to production after tests pass

Q3: What would you add to make rollbacks possible?

- for rollbacks, keep previous compose files and image tags, and add tasks to revert to last known good version if deployment fails

Q4: How does self-hosted runner improve security compared to GitHub-hosted?

- self-hosted runners limit exposure because the runner machine is under your control, unlike github-hosted where VM is shared and short-lived  