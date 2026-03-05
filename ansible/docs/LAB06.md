# Lab 6: Advanced Ansible & CI/CD - Submission

**Name:** Marina Lavrova  
**Date:** 2026-03-05   
**Lab Points:** 10 points (without bonus)

## Task 1: Blocks & Tags (2 pts)

- **common role:**
  - Package management (`apt` update + install) is grouped into a `block` with `rescue` (retry `apt-get update --fix-missing`) and `always` (logging to `/tmp/common_packages.log`).
  - A user‑management block is added, driven by the `common_users` variable and tagged with `users`.
  - The role and tasks are tagged with `common`, `packages`, `users`.
- **docker role:**
  - Docker installation (GPG key, repo, packages) is grouped into a `block` with `rescue` (retry `apt-get update` with a delay) and `always` (ensuring the Docker service is enabled and running).
  - Configuration (user in `docker` group, `python3-docker`) is placed in a separate block.
  - Tags: `docker`, `docker_install`, `docker_config`.

**Commands and expected behavior (used for screenshots):**

- `ansible-playbook playbooks/provision.yml --tags "docker"` — runs only tasks from the `docker` role.
- `ansible-playbook playbooks/provision.yml --skip-tags "common"` — skips the `common` role.
- `ansible-playbook playbooks/provision.yml --tags "packages"` — runs only package‑related tasks.
- `ansible-playbook playbooks/provision.yml --list-tags` — lists all available tags.

**Evidence (actual output):**

- Example: only Docker tasks:

```bash
$ ansible-playbook playbooks/provision.yml --tags "docker"

PLAY [Provision web servers] *****************************************************************************************************

TASK [Gathering Facts] ***********************************************************************************************************
ok: [devops-lab04-vm]

PLAY RECAP ***********************************************************************************************************************
devops-lab04-vm            : ok=1    changed=0    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0
```

- Example with `--skip-tags "common"`:

```bash
$ ansible-playbook playbooks/provision.yml --skip-tags "common"

TASK [docker : Install dependencies for Docker] **********************************************************************************
ok: [devops-lab04-vm]
...
PLAY RECAP ***********************************************************************************************************************
devops-lab04-vm            : ok=9    changed=0    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0
```

- Example with `--tags "packages"`:

```bash
$ ansible-playbook playbooks/provision.yml --tags "packages"

TASK [common : Update apt cache] *************************************************************************************************
ok: [devops-lab04-vm]
TASK [common : Install common packages] ******************************************************************************************
ok: [devops-lab04-vm]
TASK [common : Log common package management completion] *************************************************************************
changed: [devops-lab04-vm]
```

**Research answers:**

- What if the `rescue` block also fails?  
  The failure is recorded on the `rescue` task, the whole block is considered failed, but the `always` section still runs.
- Can blocks be nested?  
  Yes, blocks can be nested, but it hurts readability and makes debugging harder, so it should be used sparingly.
- How do tags behave with blocks?  
  Tags defined on a block/task are inherited by all nested tasks; task‑specific tags are merged with the block’s tags.



## Task 2: Docker Compose (3 pts)

- The `app_deploy` role was logically replaced by a new `web_app` role (`roles/web_app`), and `playbooks/deploy.yml` now uses `web_app`.
- In `roles/web_app/templates/docker-compose.yml.j2` I created a Jinja2‑based Docker Compose template with parameters:
  - `app_name`, `docker_image`, `docker_tag`, `app_port`, `app_internal_port`, `app_env`, `docker_compose_version`.
- In `roles/web_app/meta/main.yml` a dependency is added:
  - `dependencies: [ docker ]` so that Docker is always installed before deploying the app.
- In `roles/web_app/tasks/main.yml` deployment is implemented via `community.docker.docker_compose_v2` inside a block tagged with `app_deploy` and `compose`.
- In `roles/web_app/defaults/main.yml` I defined default values for the application and Compose (project directory `/opt/{{ app_name }}`).

**Before/after:**

- Before: deployment used `community.docker.docker_container` directly, with manual stop/remove/run logic.
- After: deployment is described declaratively in `docker-compose.yml` and applied via `docker_compose_v2`, which is easier to scale and maintain.

**Evidence (deployment + idempotency + accessibility):**

- First successful deployment:

```bash
$ ansible-playbook playbooks/deploy.yml --ask-vault-pass

PLAY [Deploy web application] ****************************************************************************************************
...
TASK [web_app : Deploy application stack with Docker Compose] ********************************************************************
changed: [devops-lab04-vm]

PLAY RECAP ***********************************************************************************************************************
devops-lab04-vm            : ok=13   changed=1    unreachable=0    failed=0    skipped=4    rescued=0    ignored=0
```

- Second run (idempotency – no changes):

```bash
$ ansible-playbook playbooks/deploy.yml --ask-vault-pass

PLAY RECAP ***********************************************************************************************************************
devops-lab04-vm            : ok=13   changed=0    unreachable=0    failed=0    skipped=4    rescued=0    ignored=0
```

- Container status on the VM:

```bash
$ ssh ubuntu@89.169.151.150 "sudo docker ps"

CONTAINER ID   IMAGE                                    COMMAND           CREATED          STATUS          PORTS                        NAMES
f7ae7fcfa2d4   mclavrushka/devops-info-service:latest   "python app.py"   6 seconds ago    Up 5 seconds    0.0.0.0:5000->5000/tcp ...   devops-info-service
```

- Access from inside the VM:

```bash
ubuntu@vm:~$ curl http://localhost:5000
{"service":{"name":"devops-info-service", ...}}

ubuntu@vm:~$ curl http://localhost:5000/health
{"status":"healthy","timestamp":"2026-03-05T15:08:38.403783+00:00","uptime_seconds":15}
```

- Access from my local machine:

```bash
$ curl http://89.169.151.150:5000
{"service":{"name":"devops-info-service", ...}}

$ curl http://89.169.151.150:5000/health
{"status":"healthy","timestamp":"2026-03-05T15:09:01.731610+00:00","uptime_seconds":38}
```

**Research answers:**

- `restart: always` vs `restart: unless-stopped`  
  `always` restarts the container even after a manual stop or daemon restart;  
  `unless-stopped` does not restart a container that was explicitly stopped by an administrator.
- Docker Compose networks vs bridge networks  
  Compose defines named networks and attaches services by name, providing simple service discovery; a plain `bridge` network is a single shared network without declarative relationships between services.
- Can Vault variables be used in the template?  
  Yes. Once Ansible decrypts Vault data, the variables are available like any other and can be referenced in the Jinja2 template.



## Task 3: Wipe Logic (1 pt)

- In `roles/web_app/tasks/wipe.yml` I implemented wipe logic:
  - `docker_compose_v2 state: absent` to stop and remove the stack.
  - Removal of `docker-compose.yml` and the application directory.
  - Logging via a `debug` message.
- In `roles/web_app/tasks/main.yml` wipe tasks are included at the beginning via `include_tasks: wipe.yml` and tagged with `web_app_wipe`.
- In `roles/web_app/defaults/main.yml` the flag `web_app_wipe: false` controls wipe behavior by default.

**Test scenarios and actual output:**

- **Scenario 1 — normal deployment (wipe does NOT run):**

```bash
$ ansible-playbook playbooks/deploy.yml --ask-vault-pass

TASK [web_app : Include wipe tasks] ****************************************************************************
included: roles/web_app/tasks/wipe.yml for devops-lab04-vm

TASK [web_app : Bring down application stack with Docker Compose] **********************************************
skipping: [devops-lab04-vm]
...
PLAY RECAP *****************************************************************************************************
devops-lab04-vm            : ok=13   changed=0    unreachable=0    failed=0    skipped=4    rescued=0    ignored=0

$ ssh ubuntu@89.169.151.150 "sudo docker ps"
CONTAINER ID   IMAGE                                    COMMAND         STATUS          PORTS                        NAMES
...            mclavrushka/devops-info-service:latest   "python app.py" Up ...          0.0.0.0:5000->5000/tcp      devops-info-service

$ ssh ubuntu@89.169.151.150 "ls /opt"
containerd
devops-info-service
```

- **Scenario 2 — wipe only (remove without redeploying):**

```bash
$ ansible-playbook playbooks/deploy.yml -e "web_app_wipe=true" --tags web_app_wipe --ask-vault-pass

TASK [web_app : Bring down application stack with Docker Compose] **********************************************
changed: [devops-lab04-vm]
TASK [web_app : Remove docker-compose.yml file] ****************************************************************
changed: [devops-lab04-vm]
TASK [web_app : Remove application directory] ******************************************************************
changed: [devops-lab04-vm]
TASK [web_app : Log wipe completion] ***************************************************************************
ok: [devops-lab04-vm] => {
    "msg": "Application devops-info-service wiped successfully"
}

$ ssh ubuntu@89.169.151.150 "sudo docker ps"
CONTAINER ID   IMAGE     COMMAND   CREATED   STATUS    PORTS     NAMES

$ ssh ubuntu@89.169.151.150 "ls /opt"
containerd
```

- **Scenario 3 — clean reinstall (wipe → deploy):**

```bash
$ ansible-playbook playbooks/deploy.yml -e "web_app_wipe=true" --ask-vault-pass

TASK [web_app : Bring down application stack with Docker Compose] **********************************************
...ignoring (directory may already be gone after previous wipe)
TASK [web_app : Remove docker-compose.yml file] ****************************************************************
ok: [devops-lab04-vm]
TASK [web_app : Remove application directory] ******************************************************************
ok: [devops-lab04-vm]
TASK [web_app : Log wipe completion] ***************************************************************************
ok: [devops-lab04-vm]
TASK [web_app : Ensure application directory exists] ***********************************************************
changed: [devops-lab04-vm]
TASK [web_app : Deploy application stack with Docker Compose] **************************************************
changed: [devops-lab04-vm]

$ ssh ubuntu@89.169.151.150 "sudo docker ps"
CONTAINER ID   IMAGE                                    COMMAND           STATUS          PORTS                         NAMES
8fe2dabe2e61   mclavrushka/devops-info-service:latest   "python app.py"   Up ...          0.0.0.0:5000->5000/tcp ...   devops-info-service

$ ssh ubuntu@89.169.151.150 "ls /opt"
containerd
devops-info-service
```

- **Scenario 4 — safety check: tag without variable (wipe does NOT run):**

```bash
$ ansible-playbook playbooks/deploy.yml --tags web_app_wipe --ask-vault-pass

TASK [web_app : Bring down application stack with Docker Compose] **********************************************
skipping: [devops-lab04-vm]
...
PLAY RECAP *****************************************************************************************************
devops-lab04-vm            : ok=2   changed=0    unreachable=0    failed=0    skipped=4    rescued=0    ignored=0

$ ssh ubuntu@89.169.151.150 "sudo docker ps"
CONTAINER ID   IMAGE                                    COMMAND           STATUS          PORTS                         NAMES
8fe2dabe2e61   mclavrushka/devops-info-service:latest   "python app.py"   Up ...          0.0.0.0:5000->5000/tcp ...   devops-info-service
```

**Research answers:**

- Why use both a variable and a tag?  
  This is a double‑safety mechanism: destructive wipe tasks run only when the operator explicitly sets the variable and explicitly opts into the tag.
- How is this different from the `never` tag?  
  `never` fully disables a task unless requested directly, while the variable+tag approach gives more flexible control (e.g., globally enabling wipes for specific environments by setting `web_app_wipe=true`).
- Why must wipe run before deployment?  
  To support clean reinstall: remove old state first, then deploy a fresh version.
- When choose clean reinstall vs rolling update?  
  Clean reinstall is fine for small services without strict uptime requirements; rolling updates are better for production with high availability demands.
- How to extend wipe to images and volumes?  
  Add `docker_image` tasks with `state: absent` and use `docker_volume` or `docker_prune` modules to remove unused resources.



## Task 4: CI/CD (3 pts)

- Created workflow `.github/workflows/ansible-deploy.yml`:
  - Triggered on changes in `ansible/**` and the workflow file itself.
  - `lint` job: installs Ansible and `ansible-lint`, runs lint with Vault password from secrets; passes when no violations remain.
  - `deploy` job (after `lint`): configures SSH from `SSH_PRIVATE_KEY`, runs `ansible-playbook playbooks/deploy.yml` with `ANSIBLE_VAULT_PASSWORD`, then verifies the app with `curl` to `VM_HOST:5000` and `/health`.
- GitHub Secrets used:
  - `ANSIBLE_VAULT_PASSWORD`, `SSH_PRIVATE_KEY`, `VM_HOST`, `VM_USER`.

**Evidence:**

- **Successful workflow run:** The "Ansible Deployment" workflow runs on push to the configured branches when `ansible/**` or the workflow file changes. Both jobs (`Ansible Lint` and `Deploy Application`) complete successfully. 
https://github.com/McLavrushka/DevOps-Core-Course/actions/workflows/ansible-deploy.yml
- **ansible-lint:** The lint step passes (no fatal violations); optional rules are relaxed via `ansible/.ansible-lint.yml` where needed.
- **ansible-playbook:** The deploy step runs the playbook with vault and inventory; PLAY RECAP shows `failed=0`.
- **Verification:** The "Verify Deployment" step runs `curl -f http://<VM_HOST>:5000` and `curl -f http://<VM_HOST>:5000/health`; both return success.

**Research answers:**

- Security risks of storing SSH keys in Secrets  
  If the repo or Actions configuration is compromised, an attacker may get access to infrastructure. Mitigations: use dedicated deploy keys with limited permissions, rotate them regularly, and restrict access to Secrets.
- Staging → production  
  Use two jobs/workflows: deploy to staging first with automated checks, then require a manual approval step (`environment` protection) to promote to production.
- Rollbacks  
  Keep previous versions of Compose files/playbooks and image tags. Add a CI/CD job or parameter to deploy a specific version or the previous tag to roll back.
- Self‑hosted runner and security  
  A self‑hosted runner runs inside your infrastructure, avoiding sending SSH keys to GitHub‑hosted machines and giving more control over network and environment, but you are responsible for hardening and maintaining that runner.



## Task 5: Documentation

- This file `ansible/docs/LAB06.md` serves as the main documentation for the lab.
- Additional inline documentation in the repo:
  - Comments in Ansible roles (blocks, tags, wipe logic).
  - CI/CD workflow with descriptive step names.



## Bonus Part 1: Multi-App (1.5 pts)

- The same `web_app` role can be reused to deploy multiple applications with different variable sets.
- Separate variable files and playbooks can be added for the Python app and a bonus app (Go/other), allowing independent and combined deployments.
- The key is to use different ports and app names so containers can run in parallel without conflicts.



## Bonus Part 2: Multi-App CI/CD (1 pt)

- (Not implemented in this lab; described as a possible extension.)
- Separate workflows per app or a matrix strategy can be used:
  - The Python app deploys only when its code/vars/playbooks change.
  - The bonus app deploys only when its own files change.
  - Changes to the shared `web_app` role trigger deployments for both apps.


