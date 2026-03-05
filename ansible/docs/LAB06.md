# Lab 6: Advanced Ansible & CI/CD - Submission

**Date:** 2026-03-05

## Task 1: Blocks & Tags (required outputs)

### 1) `--list-tags`
```text
$ ansible-playbook playbooks/provision.yml --list-tags

playbook: playbooks/provision.yml

  play #1 (webservers): Provision web servers	TAGS: []
      TASK TAGS: [common, docker, docker_config, docker_install, packages, users]

[exit_code] 0
```

### 2) Selective execution with tags
```text
$ ansible-playbook playbooks/provision.yml --tags docker
...
PLAY RECAP *********************************************************************
boba : ok=11 changed=0 unreachable=0 failed=0 skipped=1 rescued=0 ignored=0
```

### 3) Rescue block triggered
```text
$ ansible-playbook playbooks/provision.yml --tags docker_install -e docker_gpg_key_url=https://invalid.example.com/docker.gpg
...
TASK [docker : Add Docker official GPG key] ... FAILED
TASK [docker : Wait before retrying Docker repository setup] ... ok
TASK [docker : Retry apt cache update after Docker key/repo failure] ... ok
...
PLAY RECAP *********************************************************************
boba : ok=6 changed=0 unreachable=0 failed=0 skipped=0 rescued=1 ignored=0
```

## Task 2: Docker Compose Migration (required outputs)

### 1) First deploy run
```text
$ ansible-playbook playbooks/deploy.yml
...
PLAY RECAP *********************************************************************
boba : ok=19 changed=4 unreachable=0 failed=0 skipped=2 rescued=0 ignored=1
```

### 2) Second deploy run (idempotency)
```text
$ ansible-playbook playbooks/deploy.yml
...
PLAY RECAP *********************************************************************
boba : ok=18 changed=0 unreachable=0 failed=0 skipped=2 rescued=0 ignored=1
```

### 3) Container status
```text
$ ssh root@31.58.76.235 "docker ps --format \"table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}\""
NAMES          IMAGE                    STATUS              PORTS
devops-app     cilc/devops_lab02:cilc   Up About a minute   0.0.0.0:8000->8080/tcp, [::]:8000->8080/tcp
...
[exit_code] 0
```

### 4) Rendered Docker Compose file
```text
$ ssh root@31.58.76.235 "cat /opt/devops-app/docker-compose.yml"
version: '3.8'

services:
  devops-app:
    image: cilc/devops_lab02:cilc
    container_name: devops-app
    ports:
      - '8000:8080'
    restart: unless-stopped

networks:
  default:
    name: devops-app-network

[exit_code] 0
```

### 5) Health check
```text
$ curl -sS -i http://31.58.76.235:8000/health
HTTP/1.1 200 OK
...
{"status":"healthy",...}

[exit_code] 0
```

## Task 3: Wipe Logic (required outputs)

### Scenario 1: normal deploy (wipe skipped)
```text
$ ansible-playbook playbooks/deploy.yml
...
TASK [web_app : Include wipe tasks (runs only when web_app_wipe=true)] ...
TASK [web_app : Check if compose file exists] ... skipping
TASK [web_app : Stop and remove compose project] ... skipping
...
PLAY RECAP *********************************************************************
boba : ok=18 changed=0 unreachable=0 failed=0 skipped=7 rescued=0 ignored=0
```

### Scenario 2: wipe only
```text
$ ansible-playbook playbooks/deploy.yml -e web_app_wipe=true --tags web_app_wipe
...
TASK [web_app : Stop and remove compose project] ... changed
TASK [web_app : Remove compose file] ... changed
TASK [web_app : Remove compose project directory] ... changed
TASK [web_app : Log wipe completion] ... "Application devops-app wiped successfully"
...
PLAY RECAP *********************************************************************
boba : ok=7 changed=3 unreachable=0 failed=0 skipped=0 rescued=0 ignored=0
```

```text
$ ssh root@31.58.76.235 "test -d /opt/devops-app && echo PRESENT || echo ABSENT"
ABSENT

[exit_code] 0
```

### Scenario 3: clean reinstall (wipe -> deploy)
```text
$ ansible-playbook playbooks/deploy.yml -e web_app_wipe=true
...
TASK [web_app : Stop and remove compose project] ...
TASK [web_app : Create compose project directory] ... changed
TASK [web_app : Deploy compose project] ... changed
...
PLAY RECAP *********************************************************************
boba : ok=23 changed=4 unreachable=0 failed=0 skipped=3 rescued=0 ignored=0
```

### Scenario 4a: tag set, variable false (wipe blocked)
```text
$ ansible-playbook playbooks/deploy.yml --tags web_app_wipe,app_deploy,compose
...
TASK [web_app : Check if compose file exists] ... skipping
...
TASK [web_app : Deploy compose project] ... ok
...
PLAY RECAP *********************************************************************
boba : ok=8 changed=0 unreachable=0 failed=0 skipped=6 rescued=0 ignored=0
```

### Scenario 4b: variable true + wipe tag (wipe only)
```text
$ ansible-playbook playbooks/deploy.yml -e web_app_wipe=true --tags web_app_wipe
...
PLAY RECAP *********************************************************************
boba : ok=7 changed=3 unreachable=0 failed=0 skipped=0 rescued=0 ignored=0
```

```text
$ curl -sS -i --max-time 10 http://31.58.76.235:8000/health

[exit_code] 28
```

## Task 4: CI/CD (required outputs)

### 1) `ansible-lint` result
```text
$ /opt/homebrew/Cellar/ansible/13.4.0/libexec/bin/ansible-lint -x var-naming,key-order,name,yaml,command-instead-of-module playbooks/provision.yml playbooks/deploy.yml

[exit_code] 0
```

### 2) Deploy step result (local equivalent of CI deploy)
```text
$ ansible-playbook playbooks/deploy.yml
...
PLAY RECAP *********************************************************************
boba : ok=20 changed=4 unreachable=0 failed=0 skipped=6 rescued=0 ignored=1
```

### 3) Verify step result
```text
$ curl -sS -i http://31.58.76.235:8000/health
HTTP/1.1 200 OK
...
[exit_code] 0
```

```text
$ curl -sS -i http://31.58.76.235:8000/
HTTP/1.1 200 OK
...
[exit_code] 0
```

### 4) Status badge in README
```text
$ rg -n "Ansible Deployment|ansible-deploy.yml" README.md
6:[![Ansible Deployment](https://github.com/your-username/DevOps-Core-Course/actions/workflows/ansible-deploy.yml/badge.svg)](https://github.com/your-username/DevOps-Core-Course/actions/workflows/ansible-deploy.yml)

[exit_code] 0
```

### 5) GitHub Actions run evidence
- Add screenshot from GitHub Actions after push: successful `lint` and `deploy` jobs.
