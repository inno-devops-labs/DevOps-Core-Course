# LAB06 --- Advanced Ansible & CI/CD

## Student: DevOps-Core-Course

## Environment:

-   Control node: macOS (Ansible in Python venv)
-   Target node: Ubuntu VM (vm1)
-   Connection: SSH with privilege escalation

------------------------------------------------------------------------

## Task 1 --- Blocks & Tags

### common role

Implemented: - block / rescue / always - tags: - common - packages -
config

Example commands:

``` bash
ansible-playbook playbooks/provision.yml --tags packages
ansible-playbook playbooks/provision.yml --skip-tags common
```

------------------------------------------------------------------------

### docker role

Implemented:

-   block / rescue / always
-   tags:
    -   docker
    -   docker_install
    -   docker_config

Docker installation and configuration are idempotent.

------------------------------------------------------------------------

## Task 2 --- Docker Compose deployment

Changes:

-   Renamed role:

    app_deploy → web_app

-   Added template:

    roles/web_app/templates/docker-compose.yml.j2

-   Deployment uses:

    community.docker.docker_compose_v2

-   Added role dependency:

    roles/web_app/meta/main.yml

Verified idempotency:

First run:

-   container created
-   compose deployed

Second run:

-   changed=0

Command used:

``` bash
ansible-playbook playbooks/deploy.yml -i inventory/hosts.ini --ask-vault-pass --ask-pass --ask-become-pass
```

------------------------------------------------------------------------

## Task 3 --- Safe wipe logic

Implemented safe wipe requiring BOTH:

-   variable:

    web_app_wipe=true

-   tag:

    web_app_wipe

Wipe-only:

``` bash
ansible-playbook playbooks/deploy.yml -i inventory/hosts.ini -e web_app_wipe=true --tags web_app_wipe --ask-vault-pass --ask-pass --ask-become-pass
```

Reinstall:

``` bash
ansible-playbook playbooks/deploy.yml -i inventory/hosts.ini --ask-vault-pass --ask-pass --ask-become-pass
```

------------------------------------------------------------------------

## Verification

### Container running:

``` bash
docker ps
```

Output:

devops-lab02-python

------------------------------------------------------------------------

### Health check:

``` bash
curl http://127.0.0.1:5000/health
```

Output:

status: healthy

------------------------------------------------------------------------

## Idempotency proof

Second run:

PLAY RECAP

changed=0

failed=0

unreachable=0

------------------------------------------------------------------------

## Conclusion

All requirements completed:

-   blocks / rescue / always
-   tags
-   docker compose deployment
-   safe wipe logic
-   idempotent deployment
-   vault secrets used
-   container deployed successfully

LAB06 completed successfully.
