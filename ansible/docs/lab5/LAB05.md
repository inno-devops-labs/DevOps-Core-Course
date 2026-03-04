# Lab 5 - Ansible Implementation Documentation

## 1. Architecture Overview
- Ansible version: 2.15+ (tested on macOS with Python 3.10)

- Target VM OS: Ubuntu 22.04 LTS (5.15.0-151-generic)

- Role structure:
```
roles/
├── common
│   ├── tasks/
│   │   └── main.yml
│   └── defaults/
│       └── main.yml
├── docker
│   ├── tasks/
│   │   └── main.yml
│   ├── handlers/
│   │   └── main.yml
│   └── defaults/
│       └── main.yml
└── app_deploy
    ├── tasks/
    │   └── main.yml
    ├── handlers/
    │   └── main.yml
    └── defaults/
        └── main.yml
```

- Why roles: Roles separate concerns (system provisioning, Docker setup, app deployment), making playbooks modular, reusable, and easier to maintain.

## 2. Roles Documentation
**common**
- **Purpose**: Update system, install essential packages, optionally set timezone.
- **Variables**: 
    - `common_packages` — list of packages (`python3-pip, curl, git, vim, htop`), 
    - `timezone` — default: `UTC`
- **Handlers**: None
- **Dependencies**: None

**docker**
- **Purpose**: Install Docker, configure repository, ensure Docker service running, manage user access.
- **Variables**: 
    - `docker_version` — optional version constraints, 
    - `docker_user` — user to add to docker group
- **Handlers**: `restart docker` — triggered when Docker config changes
- **Dependencies**: `common` role should run first

**app_deploy**
- **Purpose**: Pull and run containerized Python app securely using Vault credentials.
- **Variables**: 
    - `dockerhub_username`, `dockerhub_password` (vaulted);
    - `app_name`, `docker_image_tag`, `app_port`, `app_container_name`
- **Handlers**:
    - `restart application container` — restarts container if configuration changes
- **Dependencies**: Depends on `docker` role

## 3. Idempotency Demonstration
**First run of** `provision.yml`:

![first run](screenshots/first%20run.png)

**Second run**:

![first run](screenshots/second%20run.png)

**Analysis**:
- First run: packages installed, Docker configured, user added — all tasks changed state.
- Second run: nothing changed because tasks checked current state before applying changes.
- **Idempotency**: Roles and tasks are designed to only make changes if the target state differs from the actual state.

## 4. Ansible Vault Usage
- **Secure storage**: Docker Hub credentials stored in `group_vars/all.yml` encrypted via `ansible-vault`.
- **Vault password strategy**: Use `--ask-vault-pass` or password file (not committed to repo).
- **Importance**: Protects sensitive credentials from accidental exposure in version control.

## 5. Deployment Verification

**Playbook run**:
![playbook run](screenshots/deployment%20playbook.png)

**Container status**:
![container status](screenshots/docker%20ps.png)

**Health check**:
![main endpoint](screenshots/main%20endpoint.png)
![health check](screenshots/health%20check.png)

**Handler execution**: The restart handler triggered only when container needed restart.

## 6. Key Decisions

- **Why roles**: Keep playbooks modular, easier to maintain, and reusable.
- **Reusability**: Roles can be applied to multiple hosts or projects without duplicating logic.
- **Idempotent tasks**: Ensure they check state before applying changes (apt, docker, etc.).
- **Handlers efficiency**: Avoid unnecessary restarts; only run when a change occurs.
- **Vault necessity**: Keeps sensitive credentials secure, prevents leaks in source control.

## 7. Challenges
- Docker Hub login failing when vault not loaded → resolved by including `vars_files` in playbook.
- Container inaccessible from outside → fixed by restarting.
- Handlers misconfigured (`state: restarted` not valid) → corrected to `started`.