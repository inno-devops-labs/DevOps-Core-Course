# Ansible — Lab 5

## Quick start

Run the commands below from the **`ansible/`** directory (or adjust paths if running from the repo root).

1. **Set your VM IP**  
   Edit `inventory/hosts.ini`: replace `YOUR_VM_IP` with your VM's public IP.  
   Get IP from Pulumi: `cd pulumi && pulumi stack output public_ip`  
   Change `ansible_user` if not `ubuntu`.

2. **Install Ansible collections** (if not already installed):
   ```bash
   ansible-galaxy install -r requirements.yml
   ```

3. **Create or edit encrypted variables** (Docker Hub credentials and app config):
   - If `group_vars/all.yml` **does not exist**:  
     `ansible-vault create group_vars/all.yml`  
     Paste content from `group_vars/all.yml.example` (replace placeholders), save, remember the vault password.
   - If `group_vars/all.yml` **already exists** (e.g. you created it earlier):  
     `ansible-vault edit group_vars/all.yml`  
     Enter your vault password and edit as needed.

4. **Test connectivity** (Ansible loads group_vars, so vault password is required):
   ```bash
   ansible all -m ping --ask-vault-pass
   ```

5. **Provision** (install common packages + Docker). Vault password needed because group_vars are loaded:
   ```bash
   ansible-playbook playbooks/provision.yml --ask-vault-pass
   ```
   Run it twice to confirm idempotency (second run should show "ok", not "changed").

6. **Deploy application:**
   ```bash
   ansible-playbook playbooks/deploy.yml --ask-vault-pass
   ```
   If you see **"no vault secrets found"**: you ran without `--ask-vault-pass`; add it so Ansible can decrypt `group_vars/all.yml`.
   If you see **"Decryption failed"**: the password you entered is wrong for this file. Try again; if you forgot it, create a new vault file (`mv group_vars/all.yml group_vars/all.yml.bak` then `ansible-vault create group_vars/all.yml`) and paste content from `all.yml.example`.
   If you see **`dockerhub_password` is undefined**: open the encrypted vars with `ansible-vault edit group_vars/all.yml` and ensure it contains both `dockerhub_username` and `dockerhub_password` (see `group_vars/all.yml.example`).

7. **Verify:** `ansible webservers -a "docker ps" --ask-vault-pass` and `curl http://<VM_IP>:5001/health`

**Note:** Because `group_vars/all.yml` is encrypted, use `--ask-vault-pass` for any Ansible command (`ping`, `playbook`, `ansible webservers -a "..."`) so Ansible can decrypt variables.

## Structure

- `inventory/hosts.ini` — target hosts (fill in VM IP).
- `roles/common` — base system (apt, packages, timezone).
- `roles/docker` — Docker CE install and service.
- `roles/app_deploy` — pull image and run container (uses vaulted `group_vars/all.yml`).
- `playbooks/provision.yml` — common + docker.
- `playbooks/deploy.yml` — app_deploy only.

Documentation: `docs/LAB05.md` (fill in terminal outputs and analysis for submission).

### If "Failed to update apt cache" on the VM

**"Network is unreachable" or "connection timed out"** means the VM has **no working outbound internet**. Ansible cannot fix this — the VM or cloud network must allow egress.

**Yandex Cloud (Pulumi from Lab 4):**
- In `pulumi/__main__.py` the VM has `nat=True`; the security group must also have an **egress** rule so the VM can reach the internet. Add (if missing) an egress rule, e.g. `direction="egress"`, `protocol="ANY"`, `v4_cidr_blocks=["0.0.0.0/0"]`. Then run `pulumi up` so the rule is applied.
- If the VM was created earlier without egress, run `pulumi up` again after adding the egress rule; no need to recreate the VM.
- From the VM: `curl -4 -v http://mirror.yandex.ru/` — if this fails, fix the cloud network first (NAT, egress, or use another subnet).

**Other checks:**
1. **On the VM** (SSH in): `sudo apt-get update` and `curl -4 http://mirror.yandex.ru/` — same errors mean no outbound.
2. **Security group / firewall:** Allow **egress** (outbound) HTTP (80) and HTTPS (443), not only ingress.
3. **DNS:** On the VM, `cat /etc/resolv.conf` — there should be nameservers.

**Ansible-side:** The `common` role uses Yandex mirror by default and forces apt to use **IPv4 only** (to avoid IPv6 "Network is unreachable"). If your VM is not in Yandex Cloud, set `use_yandex_mirror: false` in `roles/common/defaults/main.yml`.
