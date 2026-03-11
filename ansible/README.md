# Ansible — Lab 5 & Lab 6

[![Ansible Deployment](https://github.com/Arino4kaMyr/DevOps-Core-Course/actions/workflows/ansible-deploy.yml/badge.svg)](https://github.com/Arino4kaMyr/DevOps-Core-Course/actions/workflows/ansible-deploy.yml)

## Quick start

Run the commands below from the **`ansible/`** directory.

1. **Set your VM IP**
   Edit `inventory/hosts.ini`: replace the IP with your VM's public IP.

2. **Install Ansible collections:**
   ```bash
   ansible-galaxy install -r requirements.yml
   ```

3. **Create or edit encrypted variables** (Docker Hub credentials and app config):
   - If `group_vars/all.yml` **does not exist**:
     `ansible-vault create group_vars/all.yml`
     Paste content from `group_vars/all.yml.example`, save, remember the vault password.
   - If `group_vars/all.yml` **already exists**:
     `ansible-vault edit group_vars/all.yml`

4. **Test connectivity:**
   ```bash
   ansible all -m ping --ask-vault-pass
   ```

5. **Provision** (install common packages + Docker):
   ```bash
   ansible-playbook playbooks/provision.yml --ask-vault-pass
   ```

6. **Deploy application** (Docker Compose):
   ```bash
   ansible-playbook playbooks/deploy.yml --ask-vault-pass
   # Or: deploy_python.yml (Python only), deploy_bonus.yml (Go only), deploy_all.yml (both)
   ```

7. **Verify:**
   ```bash
   ansible webservers -a "docker ps" --ask-vault-pass
   curl http://<VM_IP>:8000/health
   ```

8. **Deploy monitoring stack (Lab 7 bonus)** — Loki, Promtail, Grafana + apps:
   ```bash
   ansible-playbook playbooks/deploy-monitoring.yml --ask-vault-pass
   ```
   Then open http://<VM_IP>:3000 (Grafana), add Loki data source `http://loki:3100`.

## Tag-based execution

```bash
# Run only docker tasks
ansible-playbook playbooks/provision.yml --tags "docker" --ask-vault-pass

# Skip common role
ansible-playbook playbooks/provision.yml --skip-tags "common" --ask-vault-pass

# Deploy only
ansible-playbook playbooks/deploy.yml --tags "app_deploy" --ask-vault-pass

# Wipe and redeploy
ansible-playbook playbooks/deploy.yml -e "web_app_wipe=true" --ask-vault-pass

# Wipe only (no redeploy)
ansible-playbook playbooks/deploy.yml -e "web_app_wipe=true" --tags web_app_wipe --ask-vault-pass

# List all tags
ansible-playbook playbooks/deploy.yml --list-tags
```

## Structure

```
ansible/
├── ansible.cfg
├── requirements.yml
├── inventory/
│   ├── hosts.ini            static (default)
│   └── yandex_cloud.yml     dynamic (Lab 5 bonus)
├── group_vars/
│   ├── all.yml              (encrypted)
│   └── all.yml.example
├── vars/
│   ├── app_python.yml       Lab 6 bonus: Python app vars
│   └── app_bonus.yml        Lab 6 bonus: Go app vars
├── playbooks/
│   ├── provision.yml        common + docker
│   ├── deploy.yml           web_app (default/single app)
│   ├── deploy_python.yml    Python app only
│   ├── deploy_bonus.yml     Go app only
│   ├── deploy_all.yml       both apps
│   └── deploy-monitoring.yml  Loki stack (Lab 7 bonus)
├── roles/
│   ├── common/               base system (apt, packages, timezone)
│   ├── docker/               Docker CE install and service
│   ├── web_app/              Docker Compose deployment + wipe logic
│   └── monitoring/           Loki/Promtail/Grafana stack (Lab 7 bonus)
│       ├── defaults/main.yml
│       ├── meta/main.yml     (depends on docker role)
│       ├── tasks/
│       │   ├── main.yml
│       │   ├── setup.yml     (dirs + template configs)
│       │   └── deploy.yml     (docker_compose_v2 + wait for Loki/Grafana)
│       └── templates/
│           ├── docker-compose.yml.j2
│           ├── loki-config.yml.j2
│           └── promtail-config.yml.j2
└── docs/
    ├── LAB05.md
    └── LAB06.md
```

Documentation: `docs/LAB05.md`, `docs/LAB05_BONUS.md` (dynamic inventory), `docs/LAB06.md`

### Troubleshooting

If "Failed to update apt cache" on the VM — the VM has no outbound internet. Check security group egress rules. See `docs/LAB05.md` for details.
