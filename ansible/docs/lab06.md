# LAB06 - Advanced Ansible Features & CI/CD

## 1. Overview

This lab extends the previous infrastructure automation from **Lab05**
by introducing more advanced Ansible concepts and a CI/CD pipeline.

Main goals:

-   Organize roles using **blocks and tags**
-   Implement **Docker Compose deployment**
-   Add **wipe functionality** for safe environment cleanup
-   Integrate **CI/CD automation using GitHub Actions**
-   Demonstrate **idempotent infrastructure management**

Target infrastructure:

  Component         Value
  ----------------- -----------------------------
  Cloud Provider    Yandex Cloud
  VM OS             Ubuntu 24.04 LTS
  Public IP         93.77.185.128
  User              ubuntu
  Application       FastAPI service
  Container image   darriyan0/app_python:latest

------------------------------------------------------------------------

# 2. Blocks and Tags

Tasks were organized using **tags** so that specific parts of the
infrastructure can be executed independently.

Example:

``` bash
ansible-playbook playbooks/provision.yml --list-tags
```

Output:

    TASK TAGS: [common, docker, docker_config, docker_install, packages, users]

### Install only base packages

``` bash
ansible-playbook playbooks/provision.yml --tags packages
```

### Create system users

``` bash
ansible-playbook playbooks/provision.yml --tags users
```

### Install Docker

``` bash
ansible-playbook playbooks/provision.yml --tags docker_install
```

### Configure Docker

``` bash
ansible-playbook playbooks/provision.yml --tags docker_config
```

Using tags allows partial execution and simplifies debugging and CI/CD
pipelines.

------------------------------------------------------------------------

# 3. Docker Compose Deployment

Deployment was migrated from the `docker_container` module to **Docker
Compose**.

Benefits:

-   cleaner service definition
-   easier lifecycle management
-   simpler scaling

Compose template:

`roles/web_app/templates/docker-compose.yml.j2`

``` yaml
services:
  {{ app_name }}:
    image: "{{ docker_image }}:{{ docker_image_tag }}"
    container_name: "{{ app_container_name }}"
    restart: "{{ app_restart_policy }}"
    ports:
      - "{{ app_port }}:{{ app_internal_port }}"
    environment: {{ app_env }}
```

Compose project directory:

    /opt/app_python

------------------------------------------------------------------------

# 4. Deployment Role (web_app)

The role manages the full lifecycle of the application.

Main tasks:

1.  Ensure project directory exists
2.  Remove legacy container from Lab05
3.  Render docker-compose configuration
4.  Deploy services via Docker Compose
5.  Wait for service availability
6.  Verify health endpoint

Example deployment task:

``` yaml
- name: Web app | Deploy via Docker Compose
  community.docker.docker_compose_v2:
    project_src: "{{ compose_project_dir }}"
    state: present
```

------------------------------------------------------------------------

# 5. Deployment Verification

Run deployment:

``` bash
ansible-playbook playbooks/deploy.yml --vault-password-file ./.vault_pass
```

Example playbook result:

    PLAY RECAP
    lab04-vm : ok=9 changed=4 unreachable=0 failed=0 skipped=2

Check running containers:

``` bash
ansible webservers -a "docker ps"
```

Example output:

    CONTAINER ID   IMAGE                         PORTS                    NAMES
    190b7c8aeff9   darriyan0/app_python:latest   0.0.0.0:5000->5000/tcp   app_python

External health check:

``` bash
curl http://93.77.185.128:5000/health
```

Example response:

``` json
{
 "status": "healthy",
 "timestamp": "2026-03-04T16:16:46.840728+00:00",
 "uptime_seconds": 415
}
```

The service is reachable via the VM public IP.

------------------------------------------------------------------------

# 6. Wipe Functionality

A **wipe mode** was implemented to remove the deployment environment.

Command:

``` bash
ansible-playbook playbooks/deploy.yml   --vault-password-file ./.vault_pass   -e "web_app_wipe=true"   --tags web_app_wipe
```

Verification after wipe:

``` bash
ansible webservers -m shell -a "docker ps -a | grep -F app_python; echo GREP_RC=$?"
```

Output:

    GREP_RC=1

Meaning the container does not exist.

Check project directory:

``` bash
ansible webservers -m shell -a "test -d /opt/app_python && echo EXISTS || echo NOT_FOUND"
```

Output:

    NOT_FOUND

------------------------------------------------------------------------

# 7. Redeployment After Wipe

Redeploy application:

``` bash
ansible-playbook playbooks/deploy.yml --vault-password-file ./.vault_pass
```

This demonstrates reproducible infrastructure.

------------------------------------------------------------------------

# 8. CI/CD Automation (GitHub Actions)

CI/CD pipeline implemented using **GitHub Actions**.

Workflow file:

    .github/workflows/lab06-deploy.yml

Pipeline stages:

1.  Checkout repository
2.  Configure SSH
3.  Install Ansible
4.  Install Docker collection
5.  Run deployment playbook
6.  Perform health check

Example health check step:

``` yaml
- name: Health check
  run: |
    curl -fsS "http://${{ secrets.VM_HOST }}:5000/health"
```

------------------------------------------------------------------------

# 9. Secure SSH Access for CI

Instead of using a personal SSH key, a dedicated **CI deploy key** was
created.

Generate key:

``` bash
ssh-keygen -t ed25519 -f ~/.ssh/lab06_ci_key -N ""
```

Add public key to VM:

``` bash
ssh-copy-id -i ~/.ssh/lab06_ci_key.pub ubuntu@93.77.185.128
```

Add private key to GitHub Secrets:

    SSH_PRIVATE_KEY

Benefits:

-   isolates CI credentials
-   improves security
-   allows easy revocation

------------------------------------------------------------------------

# 10. Key Improvements Compared to Lab05

  Feature               Lab05              Lab06
  --------------------- ------------------ ------------------
  Deployment            docker_container   Docker Compose
  Role structure        basic              block + tags
  Environment cleanup   none               wipe mode
  CI/CD                 manual deploy      GitHub Actions
  SSH security          personal key       dedicated CI key

------------------------------------------------------------------------

# 11. Conclusion

Lab06 demonstrates a production-style infrastructure workflow combining:

-   Ansible role architecture
-   Docker Compose deployment
-   automated cleanup
-   CI/CD integration
-   secure credential management

The resulting infrastructure is:

-   reproducible
-   automated
-   secure
-   ready for continuous deployment.
