# Lab 5 - Ansible Fundamentals

## 1. Architecture Overview
- **Ansible version used:** `ansible-core 2.16.17`
- **Target VM:** AWS EC2 Ubuntu (recreated from Lab 4 Pulumi code)
- **Target host:** `pulumi-vm` (`100.53.0.12`, user `ubuntu`)
- **Project structure:** role-based (`common`, `docker`, `app_deploy`) with separate playbooks for provisioning and deployment.
- **Why roles instead of one monolithic playbook:** roles isolate responsibilities, reduce duplication, and make automation easier to maintain.

## 2. Roles Documentation

### Role: `common`
- **Purpose:** baseline OS preparation.
- **Variables:**
  - `common_packages`
  - `common_timezone`
- **Handlers:** none.
- **Dependencies:** none.

### Role: `docker`
- **Purpose:** install Docker engine, configure repository, enable service.
- **Variables:**
  - `docker_packages`
  - `docker_user`
  - `docker_apt_repo`
  - `docker_apt_arch`
- **Handlers:**
  - `restart docker`
- **Dependencies:** should run after `common`.

### Role: `app_deploy`
- **Purpose:** Docker Hub login, image pull, container rollout, readiness and health checks.
- **Variables:**
  - `dockerhub_username`
  - `dockerhub_password` (vaulted)
  - `docker_image`, `docker_image_tag`
  - `app_host_port`, `app_container_port`, `app_container_name`
  - `app_restart_policy`, `app_env`
- **Handlers:**
  - `restart app container`
- **Dependencies:** Docker must be installed and running.

## 3. Idempotency Demonstration
- **First provision run:** `changed=10` (packages/repository/service/group setup applied).
- **Second provision run:** `changed=0` (state already converged).

This confirms idempotency: tasks use stateful modules and explicit target state (`present`, `started`, `enabled`, `absent`) so repeated execution does not re-apply unchanged configuration.

## 4. Ansible Vault Usage
- Credentials are stored in `group_vars/all.yml` encrypted with Ansible Vault.
- Playbooks are executed with `--ask-vault-pass`.
- Vault password is not committed; `.vault_pass` is gitignored for optional local usage.
- Sensitive Docker login task uses `no_log: true`.

## 5. Deployment Verification
Deployment was successful:
- Docker login succeeded.
- Image pull + container update completed.
- Health endpoint returned HTTP 200.
- Handler `restart app container` executed.

Live checks:
- `docker ps` showed running container `devops-lab3-python` on `0.0.0.0:5000->8080/tcp`.
- `curl http://100.53.0.12:5000/health` returned `200 OK`.
- `curl http://100.53.0.12:5000/` returned application JSON.

## 6. Key Decisions
- **Why use roles instead of plain playbooks?**
  Roles provide modularity and clear separation of concerns, which simplifies maintenance and troubleshooting.

- **How do roles improve reusability?**
  Defaults and role boundaries let the same automation logic be reused across hosts/environments by changing variables only.

- **What makes a task idempotent?**
  The task declares a desired end state and changes the system only when actual state differs from that target.

- **How do handlers improve efficiency?**
  Handlers run only when notified by changed tasks, avoiding unnecessary service restarts.

- **Why is Ansible Vault necessary?**
  It allows secrets to stay encrypted in Git while remaining usable during automation runs.

## 7. Challenges
- The original VM from Lab 4 was no longer reachable; infrastructure had to be recreated.
- WSL/Windows virtualenv mismatch required creating a Linux venv for Pulumi.
- Inventory and Ansible config parsing issues were resolved by normalizing file format and explicitly using project config.

## 8. Required Collections
Install collections before provisioning/deployment:

```bash
cd ansible
ansible-galaxy collection install -r collections/requirements.yml
```

## 9. Evidence Files
- `ansible/docs/provision-run1.txt` - first provisioning run (`changed=10`).
- `ansible/docs/provision-run2.txt` - second provisioning run (`changed=0`).
- `ansible/docs/deploy-run.txt` - deployment run output.
- `ansible/docs/docker-ps.txt` - running container verification.
- `ansible/docs/health.txt` - `/health` endpoint response.
- `ansible/docs/root.txt` - root endpoint response.

## 10. Bonus - Dynamic Inventory (AWS)
Implemented dynamic inventory plugin config for AWS EC2:
- `ansible/inventory/aws_ec2.yml`
- `ansible.cfg` updated with `amazon.aws.aws_ec2` plugin in `enable_plugins`
- `collections/requirements.yml` includes `amazon.aws`

Executed validation with AWS Academy temporary credentials exported in shell.

Observed results:
- `ansible-inventory -i inventory/aws_ec2.yml --graph` discovered EC2 hosts and grouped them automatically.
- Group `webservers` resolved to the target host `44.223.0.91` by tag filter.
- `ansible -i inventory/aws_ec2.yml webservers -m ping --ask-vault-pass` returned `pong`.
- `ansible-playbook -i inventory/aws_ec2.yml playbooks/provision.yml --ask-vault-pass` completed (`failed=0`).
- `ansible-playbook -i inventory/aws_ec2.yml playbooks/deploy.yml --ask-vault-pass` completed (`failed=0`).

What this proves:
- No manual `hosts.ini` IP updates are needed for dynamic mode.
- When public IP changes, inventory is refreshed from AWS API and Ansible continues to work via discovered `ansible_host`.

Bonus evidence files:
- `ansible/docs/bonus-inventory-graph.txt`
- `ansible/docs/bonus-ping.txt`
- `ansible/docs/bonus-provision.txt`
- `ansible/docs/bonus-deploy.txt`
## 11. `.vault_pass` Note
- `.vault_pass` is an optional local file containing your vault password in plain text (single line).
- Example content: `MyStrongVaultPassphrase`
- It must never be committed.
- In this repo, `.vault_pass` is listed in `.gitignore`.
- If you use it, run playbooks with:

```bash
ansible-playbook playbooks/deploy.yml --vault-password-file .vault_pass
```

