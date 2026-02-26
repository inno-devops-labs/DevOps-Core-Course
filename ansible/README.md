# Ansible — Lab 5

## Prerequisites

- Target VM from Lab 4 (Ubuntu 22.04/24.04, SSH access).
- Ansible 2.16+ on your machine: `brew install ansible` (macOS) or `sudo apt install ansible` (Linux).

## First-time setup

1. **Install collections**
   ```bash
   ansible-galaxy collection install -r requirements.yml
   ```

2. **Configure inventory**  
   Edit `inventory/hosts.ini`: set `ansible_host` (VM IP) and `ansible_user` (e.g. `ubuntu`).

3. **Test connectivity**
   ```bash
   ansible all -m ping
   ```

4. **Create Vault file for deploy**  
   Copy the example and encrypt (use a strong password and store it safely):
   ```bash
   cp group_vars/all.yml.example group_vars/all.yml
   ansible-vault encrypt group_vars/all.yml
   ansible-vault edit group_vars/all.yml   # set dockerhub_username, dockerhub_password, app_name
   ```
   Use a Docker Hub **access token**, not your account password.

## Run

- **Provision (common + Docker):**
  ```bash
  ansible-playbook playbooks/provision.yml
  ```
  Run twice to confirm idempotency (second run should show only "ok").

- **Deploy app (pull image, run container):**
  ```bash
  ansible-playbook playbooks/deploy.yml --ask-vault-pass
  ```

- **Or run everything:**
  ```bash
  ansible-playbook playbooks/site.yml --ask-vault-pass
  ```

## Verify

```bash
ansible webservers -a "docker ps"
curl http://<VM-IP>:5000/health
```

Documentation and acceptance criteria: see `docs/LAB05.md`.
