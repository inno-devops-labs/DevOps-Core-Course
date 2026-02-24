# Ansible — Lab 5

## Quick start

1. **Install Ansible** (macOS: `brew install ansible`). Check: `ansible --version`.

2. **Install collections:**
   ```bash
   ansible-galaxy collection install -r requirements.yml
   ```

3. **Set your VM IP** in `inventory/hosts.ini`: replace `<VM-IP-ADDRESS>` with the VM public IP (e.g. from `terraform output vm_public_ip`).

4. **Test connectivity:**
   ```bash
   cd ansible
   ansible all -m ping
   ansible webservers -a "uname -a"
   ```

5. **Provision (common + Docker):**
   ```bash
   ansible-playbook playbooks/provision.yml
   ```
   Run it again to confirm idempotency (all tasks should be `ok` on the second run).

6. **Vault and deploy:**
   - Create encrypted variables: `ansible-vault create group_vars/all.yml`
   - Use the content from `group_vars/all.yml.example` (set your Docker Hub username and access token).
   - Deploy: `ansible-playbook playbooks/deploy.yml --ask-vault-pass`

7. **Verify:** `ansible webservers -a "docker ps"`, then `curl http://<VM-IP>:5000/health`.

Documentation: `docs/LAB05.md`.
