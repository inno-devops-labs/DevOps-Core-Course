# lab 05: ansible fundamentals

## 1. infrastructure & vm setup

### existing infrastructure issue

the previous vm from an earlier lab05 attempt had:
- ssh authorization set to `os_login` mode (incompatible with metadata ssh keys)
- left over network resources consuming quota

### cleanup performed

```bash
# deleted orphaned resources using yandex cloud cli
yc compute instance delete lab05-vm
yc vpc subnet delete lab05-vm-subnet
yc vpc security-group delete lab05-vm-sg
yc vpc network delete lab05-vm-net
```

### new infrastructure created

resources created via terraform:

| resource | name | description |
|----------|------|-------------|
| vpc network | devops-network | virtual private cloud |
| vpc subnet | devops-subnet | REDDACTED__N6__/24 CIDR block |
| security group | devops-security-group | ssh (22), http (80), app (5000) |
| compute instance | devops-vm | ubuntu 22.04 LTS |

### vm details

| parameter | value |
|-----------|-------|
| public ip | 158.160.53.58 |
| platform | standard-v2 |
| cores | 2 (20% core fraction) |
| memory | 1 GB |
| disk | 10 GB network-hdd |
| os | ubuntu 22.04 LTS |

---

## 2. ansible setup & project structure

### ansible version

```
ansible [core 2.20.3]
python version = 3.14.3
jinja version = 3.1.6
```

### project structure

```
ansible/
├── inventory/
│   └── hosts.ini              # static inventory
├── roles/
│   ├── common/                # basic system setup
│   │   ├── tasks/main.yml
│   │   └── defaults/main.yml
│   ├── docker/                # docker installation
│   │   ├── tasks/main.yml
│   │   ├── handlers/main.yml
│   │   └── defaults/main.yml
│   └── app_deploy/            # application deployment
│       ├── tasks/main.yml
│       ├── handlers/main.yml
│       └── defaults/main.yml
├── playbooks/
│   ├── site.yml               # main playbook
│   ├── provision.yml          # system provisioning
│   └── deploy.yml             # app deployment
├── group_vars/
│   └── all.yml                # encrypted variables (vault)
├── ansible.cfg                # ansible configuration
├── .vault_pass                # vault password (gitignored)
└── docs/
    └── LAB05.md
```

### why roles instead of monolithic playbooks

1. **reusability**: roles can be shared across projects and environments
2. **organization**: clear separation of concerns (common, docker, app)
3. **maintainability**: changes are isolated to specific roles
4. **testing**: each role can be tested independently

---

## 3. roles documentation

### common role

**purpose**: basic system setup that every server needs.

| variable | default value | description |
|----------|---------------|-------------|
| `common_packages` | python3-pip, curl, git, vim, htop, wget, apt-transport-https, ca-certificates, gnupg, lsb-release, software-properties-common | essential packages |
| `common_timezone` | Europe/Moscow | server timezone |

**tasks**:
1. update apt cache (with 1 hour validity)
2. install common packages
3. set timezone

**handlers**: none

---

### docker role

**purpose**: install and configure docker CE.

| variable | default value | description |
|----------|---------------|-------------|
| `docker_user` | ubuntu | user to add to docker group |
| `docker_packages` | docker-ce, docker-ce-cli, containerd.io, docker-buildx-plugin, docker-compose-plugin | docker packages |

**tasks**:
1. create directory for docker gpg key
2. check if docker gpg key exists
3. add docker gpg key (conditional)
4. add docker repository
5. install docker packages
6. ensure docker service is running and enabled
7. add user to docker group
8. install python3-docker for ansible modules

**handlers**:

| handler | trigger |
|---------|---------|
| `restart docker` | when docker repo or packages change |

---

### app_deploy role

**purpose**: deploy the containerized python application.

| variable | default value | description |
|----------|---------------|-------------|
| `app_port` | 5000 | application port |
| `app_container_name` | devops-app | container name |
| `docker_image_tag` | v0 | image tag |
| `restart_policy` | unless-stopped | container restart policy |

**vault variables** (encrypted in `group_vars/all.yml`):

| variable | description |
|----------|-------------|
| `dockerhub_username` | docker hub username |
| `dockerhub_password` | docker hub access token |
| `docker_image` | full docker image name |

**tasks**:
1. log in to docker hub (with `no_log: true`)
2. pull docker image
3. stop existing container (ignored if not exists)
4. remove old container
5. run application container
6. wait for application to be ready
7. verify health endpoint

**handlers**:

| handler | trigger |
|---------|---------|
| `restart app container` | when container config changes |

---

## 4. idempotency demonstration

### first run

```
PLAY [Provision web servers] ***************************************************

TASK [common : Update apt cache] ***********************************************
changed: [devops-vm]

TASK [common : Install common packages] ****************************************
changed: [devops-vm]

TASK [common : Set timezone] ***************************************************
changed: [devops-vm]

TASK [docker : Add Docker GPG key] *********************************************
changed: [devops-vm]

TASK [docker : Add Docker repository] ******************************************
changed: [devops-vm]

TASK [docker : Install Docker packages] ****************************************
changed: [devops-vm]

TASK [docker : Add user to docker group] ***************************************
changed: [devops-vm]

TASK [docker : Install python3-docker] *****************************************
changed: [devops-vm]

PLAY RECAP *********************************************************************
devops-vm                  : ok=14   changed=10
```

### second run

```
PLAY [Provision web servers] ***************************************************

TASK [common : Update apt cache] ***********************************************
ok: [devops-vm]

TASK [common : Install common packages] ****************************************
ok: [devops-vm]

TASK [common : Set timezone] ***************************************************
ok: [devops-vm]

TASK [docker : Check if Docker GPG key exists] *********************************
ok: [devops-vm]

TASK [docker : Add Docker GPG key] *********************************************
skipping: [devops-vm]

TASK [docker : Add Docker repository] ******************************************
ok: [devops-vm]

TASK [docker : Install Docker packages] ****************************************
ok: [devops-vm]

TASK [docker : Add user to docker group] ***************************************
ok: [devops-vm]

PLAY RECAP *********************************************************************
devops-vm                  : ok=11   changed=0
```

### analysis

**first run**: 10 tasks changed because:
- apt cache needed updating
- packages were not installed
- timezone needed to be set
- docker gpg key and repo needed adding
- docker packages needed installing
- user needed adding to docker group

**second run**: `changed=0` because:
- all packages already installed with correct versions
- all files existed with correct permissions
- docker service already running
- timezone already set

**what makes roles idempotent**:
1. state-based modules (`apt: state=present` instead of `apt-get install`)
2. conditionals (check if gpg key exists before adding)
3. declarative approach (describe desired state, not actions)
4. `cache_valid_time` prevents unnecessary apt updates

---

## 5. ansible vault

### vault configuration

vault password stored in `.vault_pass` (gitignored):

```ini
# ansible.cfg
[defaults]
vault_password_file = /Users/s.razmakhov/bucket/courses/uni/devops-s26/ansible/.vault_pass
```

### encrypted file structure

```yaml
# group_vars/all.yml (encrypted)
---
dockerhub_username: onemoreslacker
dockerhub_password: dckr_pat_***  # access token
docker_image: "{{ dockerhub_username }}/devops-info-service"
```

### verification

```
$ ansible-vault view group_vars/all.yml --vault-password-file .vault_pass
---
# Docker Hub credentials
dockerhub_username: onemoreslacker
dockerhub_password: <encrypted>
...
```

### why ansible vault is necessary

1. **security**: credentials not stored in plain text
2. **version control**: encrypted files safe to commit
3. **collaboration**: team can use with vault password
4. **compliance**: meets security requirements for secrets

---

## 6. deployment verification

### deploy playbook output

```
PLAY [Deploy application] ******************************************************

TASK [app_deploy : Log in to Docker Hub] ***************************************
ok: [devops-vm]

TASK [app_deploy : Pull Docker image] ******************************************
changed: [devops-vm]

TASK [app_deploy : Run application container] **********************************
changed: [devops-vm]

TASK [app_deploy : Wait for application to be ready] ***************************
ok: [devops-vm]

TASK [app_deploy : Verify health endpoint] *************************************
ok: [devops-vm]

PLAY RECAP *********************************************************************
devops-vm                  : ok=8    changed=2
```

### container status

```
CONTAINER ID   IMAGE                                   COMMAND                  STATUS
6bad58ed1ff9   onemoreslacker/devops-info-service:v0   "uvicorn app:app --h…"   Up (healthy)
```

### health check

```bash
$ curl http://<VM-IP>:5000/health
{"status":"healthy","timestamp":"2026-03-09T13:42:06.789427+00:00","uptime_seconds":66}
```

---

## 7. key decisions

| question | answer |
|----------|--------|
| why use roles instead of plain playbooks? | roles provide better organization, reusability across projects, and independent testing capability |
| how do roles improve reusability? | can be shared via ansible galaxy, applied to different hosts, customized through variables |
| what makes a task idempotent? | uses state-based modules, checks current state before changes, produces same result on repeated runs |
| how do handlers improve efficiency? | only run when notified by changed tasks, prevent unnecessary service restarts |
| why is ansible vault necessary? | encrypts secrets for safe version control storage while remaining usable in playbooks |

---

## 8. challenges

### docker image platform mismatch

**problem**: initial image was built for ARM64 (mac) but vm is AMD64.

**error**: `no matching manifest for linux/amd64`

**solution**: rebuilt and pushed multi-arch image:
```bash
docker buildx build --platform linux/amd64,linux/arm64 -t onemoreslacker/devops-info-service:v0 --push .
```

### vault variable loading

**problem**: vault variables not loading in playbook despite working in ad-hoc commands.

**error**: `'dockerhub_password' is undefined`

**solution**: explicitly include `vars_files` in playbook:
```yaml
vars_files:
  - ../group_vars/all.yml
```

### ssh key injection

**problem**: existing vm had `ssh_authorization: OS_LOGIN` mode enabled.

**error**: `Permission denied (publickey)`

**solution**: deleted old vm and created new one with terraform, which properly injects ssh keys via metadata.
