# Lab 5 — Ansible Fundamentals

![difficulty](https://img.shields.io/badge/difficulty-beginner-success)
![topic](https://img.shields.io/badge/topic-Configuration%20Management-blue)
![points](https://img.shields.io/badge/points-10%2B2.5-orange)
![tech](https://img.shields.io/badge/tech-Ansible-informational)

> Learn configuration management fundamentals by building reusable Ansible roles for infrastructure provisioning and application deployment.

## Overview

Master the basics of Ansible by creating a professional role-based automation system. You'll build roles for system provisioning (Docker, common packages) and application deployment, demonstrating idempotency, handlers, and secure credential management with Ansible Vault.

**What You'll Learn:**
- Ansible roles architecture and best practices
- Role-based code organization for reusability
- Writing tasks, handlers, and defaults
- Idempotency and why it matters
- Ansible Vault for secure credential management
- Handlers for efficient service management
- Infrastructure verification and health checks
- Basic application deployment with Docker

**Tech Stack:** Ansible 2.16+ | Ansible Vault | Docker | YAML

**Connection to Previous Labs:**
- **Lab 4:** Use the VM you created (cloud or local)
- **Labs 1-3:** Deploy your containerized Python app with CI/CD-built images
- **Lab 6:** Add advanced features (blocks, tags, Docker Compose, CI/CD)

---

## Prerequisites

You need a target VM from Lab 4:
- **Option A:** Cloud VM from Lab 4 (Terraform/Pulumi)
- **Option B:** Local VM (VirtualBox/Vagrant)
- **Option C:** Recreate VM using your Lab 4 code

**VM Requirements:**
- Ubuntu 24.04 LTS or 22.04 LTS
- SSH access configured
- Your SSH key added
- Sudo access (passwordless recommended for automation)
- Python 3 installed (usually pre-installed on Ubuntu)

---

## Tasks

### Task 1 — Ansible Setup & Role Structure (2 pts)

**Objective:** Install Ansible locally, create proper role-based project structure, and configure inventory.

#### 1.1 Install Ansible

Install Ansible on your local machine (control node):

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install ansible
```

**macOS:**
```bash
brew install ansible
```

**Windows:**
- Use WSL2 and install in Linux environment
- OR use Ansible via Docker

Verify installation: `ansible --version`

#### 1.2 Create Role-Based Project Structure

Create this structure:

```
ansible/
├── inventory/
│   └── hosts.ini              # Static inventory
├── roles/
│   ├── common/                # Common system tasks
│   │   ├── tasks/
│   │   │   └── main.yml
│   │   └── defaults/
│   │       └── main.yml
│   ├── docker/                # Docker installation
│   │   ├── tasks/
│   │   │   └── main.yml
│   │   ├── handlers/
│   │   │   └── main.yml
│   │   └── defaults/
│   │       └── main.yml
│   └── app_deploy/            # Application deployment
│       ├── tasks/
│       │   └── main.yml
│       ├── handlers/
│       │   └── main.yml
│       └── defaults/
│           └── main.yml
├── playbooks/
│   ├── site.yml               # Main playbook
│   ├── provision.yml          # System provisioning
│   └── deploy.yml             # App deployment
├── group_vars/
│   └── all.yml               # Encrypted variables (Vault)
├── ansible.cfg               # Ansible configuration
└── docs/
    └── LAB05.md              # Your documentation
```

<details>
<summary>💡 Why Ansible Roles?</summary>

**What are Roles?**

Roles are the standard way to organize Ansible code for reusability and maintainability.

**Benefits of Roles:**

1. **Reusability**: Use same role across projects
2. **Organization**: Clear structure, easy to navigate
3. **Maintainability**: Changes in one place
4. **Sharing**: Share roles via Ansible Galaxy
5. **Testing**: Test roles independently
6. **Modularity**: Mix and match roles

**Role Structure:**

Each role has a standard structure:

```
role_name/
├── tasks/           # Main task list
│   └── main.yml
├── handlers/        # Handler definitions
│   └── main.yml
├── defaults/        # Default variables (low priority)
│   └── main.yml
├── vars/            # Role variables (high priority)
│   └── main.yml
├── files/           # Static files to copy
├── templates/       # Jinja2 templates
└── meta/            # Role metadata and dependencies
    └── main.yml
```

**Only create directories you need!** Empty directories can be omitted.

**Resources:**
- [Ansible Roles Documentation](https://docs.ansible.com/ansible/latest/user_guide/playbooks_reuse_roles.html)
- [Role Directory Structure](https://docs.ansible.com/ansible/latest/user_guide/playbooks_reuse_roles.html#role-directory-structure)

</details>

#### 1.3 Configure Inventory

Create `inventory/hosts.ini` with your VM details:

```ini
[webservers]
your-vm-name ansible_host=<VM-IP-ADDRESS> ansible_user=<username>
```

<details>
<summary>💡 Inventory Configuration</summary>

**Static Inventory Format:**
```ini
[group_name]
hostname ansible_host=192.168.1.100 ansible_user=ubuntu ansible_ssh_private_key_file=~/.ssh/id_rsa

[group_name:vars]
ansible_python_interpreter=/usr/bin/python3
```

**Common Connection Parameters:**
- `ansible_host` - IP address or hostname
- `ansible_user` - SSH username
- `ansible_port` - SSH port (default: 22)
- `ansible_ssh_private_key_file` - Path to SSH key
- `ansible_python_interpreter` - Python path on target

**Testing Connectivity:**
```bash
ansible all -i inventory/hosts.ini -m ping
ansible webservers -i inventory/hosts.ini -a "uptime"
```

**Resources:**
- [Ansible Inventory Documentation](https://docs.ansible.com/ansible/latest/user_guide/intro_inventory.html)

</details>

#### 1.4 Create Ansible Configuration

Create `ansible.cfg`:

```ini
[defaults]
inventory = inventory/hosts.ini
roles_path = roles
host_key_checking = False
remote_user = ubuntu
retry_files_enabled = False

[privilege_escalation]
become = True
become_method = sudo
become_user = root
```

#### 1.5 Test Connectivity

Verify Ansible can connect to your VM:

```bash
cd ansible/
ansible all -m ping
ansible webservers -a "uname -a"
```

You should see successful responses (green "SUCCESS" messages).

---

### Task 2 — System Provisioning Roles (4 pts)

**Objective:** Create dedicated roles for system provisioning and demonstrate idempotency.

#### 2.1 Create Common Role

Create `roles/common/tasks/main.yml`:

**Required Tasks:**
- Update apt cache
- Install essential packages (python3-pip, curl, git, vim, htop, etc.)
- Set timezone (optional but good practice)

**Create `roles/common/defaults/main.yml`:**
Define default variables for packages to install.

<details>
<summary>💡 Common Role Pattern</summary>

**Purpose:**
Basic system setup that every server needs.

**Typical Tasks:**
- Update package cache
- Install essential tools
- Configure system settings
- Set up logging
- Create users/groups

**Example pattern to research:**
```yaml
---
- name: Update apt cache
  apt:
    update_cache: yes
    cache_valid_time: 3600

- name: Install common packages
  apt:
    name: "{{ common_packages }}"
    state: present
```

**Questions:**
- What does `cache_valid_time` do?
- How do you define a list of packages in defaults?
- Should you use `state: present` or `state: latest`?

**Resources:**
- [apt module](https://docs.ansible.com/ansible/latest/collections/ansible/builtin/apt_module.html)
- [timezone module](https://docs.ansible.com/ansible/latest/collections/community/general/timezone_module.html)

</details>

#### 2.2 Create Docker Role

Create `roles/docker/tasks/main.yml`:

**Required Tasks:**
1. Add Docker GPG key
2. Add Docker repository
3. Install Docker packages (docker-ce, docker-ce-cli, containerd.io)
4. Ensure Docker service is running and enabled
5. Add user to docker group
6. Install python3-docker (for Ansible docker modules)

**Create `roles/docker/handlers/main.yml`:**
- Handler to restart Docker service

**Create `roles/docker/defaults/main.yml`:**
- Docker version constraints (if any)
- User to add to docker group

<details>
<summary>💡 Docker Installation Pattern</summary>

**Docker Installation Steps:**

You need to research the official Docker installation for Ubuntu and translate it to Ansible tasks.

**Key Modules:**
- `apt_key` - Manage APT repository keys
- `apt_repository` - Manage APT repositories
- `apt` - Manage packages
- `service` - Manage services
- `user` - Manage users and groups

**Questions to Research:**
- What's Docker's official GPG key URL?
- What repository URL should you use for Ubuntu?
- How do you use Ansible facts like `{{ ansible_distribution_release }}`?
- Why add user to docker group?
- When should the handler be triggered?

**Handler Pattern:**
```yaml
---
- name: restart docker
  service:
    name: docker
    state: restarted
```

**Trigger handler with:**
```yaml
- name: Some task
  module: ...
  notify: restart docker
```

**Resources:**
- [Install Docker on Ubuntu (Official)](https://docs.docker.com/engine/install/ubuntu/)
- [Ansible Handlers](https://docs.ansible.com/ansible/latest/user_guide/playbooks_handlers.html)

</details>

#### 2.3 Create Provisioning Playbook

Create `playbooks/provision.yml`:

```yaml
---
- name: Provision web servers
  hosts: webservers
  become: yes

  roles:
    - common
    - docker
```

**That's it!** The playbook is clean because all logic is in roles.

#### 2.4 Run Provisioning and Demonstrate Idempotency

**First Run:**
```bash
ansible-playbook playbooks/provision.yml
```

Observe the output - tasks should show "changed" status (yellow).

**Second Run:**
```bash
ansible-playbook playbooks/provision.yml
```

**CRITICAL:** Tasks should show "ok" status (green), not "changed". This demonstrates idempotency!

<details>
<summary>💡 Understanding Idempotency</summary>

**What is Idempotency?**

An idempotent operation produces the same result whether executed once or multiple times.

**In Ansible:**
- Running a playbook multiple times should be safe
- Only makes changes when needed
- Doesn't break if run repeatedly
- Converges to desired state

**Ansible Output Colors:**
- **Green (ok):** Task ran, no change needed (desired state already achieved)
- **Yellow (changed):** Task made a change to reach desired state
- **Red (failed):** Task failed
- **Dark (skipped):** Task was skipped

**Why Idempotency Matters:**

1. **Safety:** Can re-run playbooks without fear
2. **Reliability:** Consistent results
3. **Recovery:** Re-run after partial failure
4. **Drift Detection:** Changes only when state drifts
5. **Confidence:** Know exactly what will change

**Making Tasks Idempotent:**

**Use Stateful Modules:**
- `apt: state=present` (not just `apt: name=package`)
- `service: state=started` (not `command: systemctl start`)
- `file: state=directory` (not `command: mkdir`)

**Testing Idempotency:**

1. Run playbook first time → many "changed"
2. Run playbook second time → all "ok", zero "changed"
3. If tasks show "changed" on second run, investigate why

**Resources:**
- [Ansible Idempotency](https://docs.ansible.com/ansible/latest/reference_appendices/glossary.html)

</details>

**What to Document:**
- Terminal output from BOTH runs
- Analysis: Which tasks changed first time? Why?
- Explanation: Why nothing changed second time?

---

### Task 3 — Application Deployment Role (2 pts)

**Objective:** Create a deployment role that securely pulls and runs your Python containerized app using Ansible Vault for credentials.

#### 3.1 Initialize Ansible Vault

Create encrypted file for sensitive data:

```bash
ansible-vault create group_vars/all.yml
```

You'll be prompted for a vault password. **Remember this password!**

Add your Docker Hub credentials and app configuration:

```yaml
---
# Docker Hub credentials
dockerhub_username: your-username
dockerhub_password: your-access-token

# Application configuration
app_name: devops-app
docker_image: "{{ dockerhub_username }}/{{ app_name }}"
docker_image_tag: latest
app_port: 5000
app_container_name: "{{ app_name }}"
```

Save and exit.

<details>
<summary>💡 Ansible Vault Best Practices</summary>

**What is Ansible Vault?**

Ansible Vault encrypts sensitive data so it can be safely stored in version control.

**Vault Commands:**

```bash
# Create encrypted file
ansible-vault create filename.yml

# Edit encrypted file
ansible-vault edit filename.yml

# View encrypted file
ansible-vault view filename.yml

# Encrypt existing file
ansible-vault encrypt filename.yml

# Decrypt file (careful!)
ansible-vault decrypt filename.yml
```

**Using Vaulted Files:**

**Option 1: Prompt for password:**
```bash
ansible-playbook playbook.yml --ask-vault-pass
```

**Option 2: Password file:**
```bash
echo "your-password" > .vault_pass
chmod 600 .vault_pass
# Add .vault_pass to .gitignore!

ansible-playbook playbook.yml --vault-password-file .vault_pass
```

**Option 3: In ansible.cfg:**
```ini
[defaults]
vault_password_file = .vault_pass
```

**Best Practices:**

1. **Never commit unencrypted secrets**
2. **Use separate file for vault password** (add to .gitignore)
3. **Rotate vault password regularly**
4. **Don't decrypt files permanently**
5. **Use `no_log: true` for tasks with secrets**

**Resources:**
- [Ansible Vault Documentation](https://docs.ansible.com/ansible/latest/user_guide/vault.html)

</details>

#### 3.2 Create Application Deployment Role

Create `roles/app_deploy/tasks/main.yml`:

**Required Tasks:**
1. Log in to Docker Hub (using vaulted credentials)
2. Pull Docker image
3. Stop existing container (if running)
4. Remove old container (if exists)
5. Run new container with:
   - Proper port mapping (5000:5000)
   - Environment variables (if any)
   - Restart policy (unless-stopped)
   - Container name
6. Wait for application to be ready (port check)
7. Verify health endpoint

**Create `roles/app_deploy/handlers/main.yml`:**
- Handler to restart application container

**Create `roles/app_deploy/defaults/main.yml`:**
- Default port
- Default restart policy
- Default environment variables

<details>
<summary>💡 Docker Deployment with Ansible</summary>

**Key Modules:**

**docker_login:**
Authenticate with Docker registry.

**Questions:**
- How do you pass credentials from vaulted variables?
- What's the `no_log` parameter for?

**docker_image:**
Manage Docker images (pull, build, remove).

**Questions:**
- How do you pull an image?
- What's the `source: pull` parameter?

**docker_container:**
Manage Docker containers.

**Questions:**
- How do you ensure a container is running?
- What restart policies exist?
- How do you map ports?
- How do you set environment variables?
- What's the difference between `state: started` and `state: present`?

**wait_for:**
Wait for port to be available.

**uri:**
Make HTTP requests (for health checks).

**Security Note:**
Always use `no_log: true` for tasks with credentials:
```yaml
- name: Login
  docker_login:
    username: "{{ dockerhub_username }}"
    password: "{{ dockerhub_password }}"
  no_log: true  # Prevents credentials in logs
```

**Resources:**
- [docker_login module](https://docs.ansible.com/ansible/latest/collections/community/docker/docker_login_module.html)
- [docker_image module](https://docs.ansible.com/ansible/latest/collections/community/docker/docker_image_module.html)
- [docker_container module](https://docs.ansible.com/ansible/latest/collections/community/docker/docker_container_module.html)
- [wait_for module](https://docs.ansible.com/ansible/latest/collections/ansible/builtin/wait_for_module.html)
- [uri module](https://docs.ansible.com/ansible/latest/collections/ansible/builtin/uri_module.html)

</details>

#### 3.3 Create Deployment Playbook

Create `playbooks/deploy.yml`:

```yaml
---
- name: Deploy application
  hosts: webservers
  become: yes

  roles:
    - app_deploy
```

#### 3.4 Run Deployment

```bash
ansible-playbook playbooks/deploy.yml --ask-vault-pass
```

Or if using password file:
```bash
ansible-playbook playbooks/deploy.yml
```

**Verify:**
- Container is running: `ansible webservers -a "docker ps"`
- App is accessible: `curl http://<VM-IP>:5000/health`
- Check main endpoint: `curl http://<VM-IP>:5000/`

**What to Document:**
- Terminal output from deployment
- Container status: `docker ps` output
- Health check verification
- Handler execution (if any)

---

### Task 4 — Documentation (2 pts)

**Objective:** Document your Ansible implementation and demonstrate understanding.

Create `ansible/docs/LAB05.md` with these sections:

#### 1. Architecture Overview
- Ansible version used
- Target VM OS and version
- Role structure diagram or explanation
- Why roles instead of monolithic playbooks?

#### 2. Roles Documentation

For each role (common, docker, app_deploy):
- **Purpose**: What does this role do?
- **Variables**: Key variables and defaults
- **Handlers**: What handlers are defined?
- **Dependencies**: Does it depend on other roles?

#### 3. Idempotency Demonstration
- Terminal output from FIRST provision.yml run
- Terminal output from SECOND provision.yml run
- Analysis: What changed first time? What didn't change second time?
- Explanation: What makes your roles idempotent?

#### 4. Ansible Vault Usage
- How you store credentials securely
- Vault password management strategy
- Example of encrypted file (show it's encrypted!)
- Why Ansible Vault is important

#### 5. Deployment Verification
- Terminal output from deploy.yml run
- Container status: `docker ps` output
- Health check verification: `curl` outputs
- Handler execution (if any)

#### 6. Key Decisions
Answer briefly (2-3 sentences each):
- **Why use roles instead of plain playbooks?**
- **How do roles improve reusability?**
- **What makes a task idempotent?**
- **How do handlers improve efficiency?**
- **Why is Ansible Vault necessary?**

#### 7. Challenges (Optional)
- Issues encountered and solutions
- Keep it brief - bullet points OK

---

## Bonus Task — Dynamic Inventory with Cloud Plugins (2.5 pts)

**Objective:** Use Ansible's built-in inventory plugins to dynamically discover your cloud VMs instead of hardcoding IPs.

<details>
<summary>💡 Why Dynamic Inventory?</summary>

**The Problem with Static Inventory:**
```ini
[webservers]
vm ansible_host=192.168.1.100 ansible_user=ubuntu
```
- IP changes? Must update manually
- Multiple VMs? Update each one
- Scaling? Very tedious

**Dynamic Inventory Solution:**
- Query cloud provider API automatically
- Always up-to-date IPs
- Filter by tags/labels
- Group automatically
- Scale to hundreds of VMs

**Ansible Inventory Plugins:**
Ansible has official plugins for major clouds.

**Available Plugins:**
- `yandex.cloud.yandex_compute` - Yandex Cloud
- `amazon.aws.aws_ec2` - Amazon EC2
- `google.gcp.gcp_compute` - Google Cloud
- `azure.azcollection.azure_rm` - Microsoft Azure
- `community.digitalocean.digitalocean` - DigitalOcean

</details>

**Requirements:**

1. **Install the collection for your cloud provider** from Lab 4

2. **Create inventory plugin configuration file** - `ansible/inventory/<cloud>.yml`
   - Must specify plugin name
   - Must configure authentication
   - Must set `ansible_host` to public IP (use `compose` parameter)
   - Must set `ansible_user` (use `compose` parameter)
   - Should filter running VMs only
   - Should create groups (like `webservers`)

3. **Update ansible.cfg** to use the plugin

4. **Test the inventory:**
   ```bash
   ansible-inventory --graph    # Show discovered hosts
   ansible all -m ping          # Test connectivity
   ```

5. **Run your playbooks** with dynamic inventory

<details>
<summary>💡 Research Path</summary>

**Steps to Complete:**

1. **Find the right plugin** for your cloud provider
   - Search: "ansible [your-cloud] inventory plugin"
   - Official documentation link

2. **Install collection:**
   - Use `ansible-galaxy collection install <collection-name>`
   - Some require additional Python packages

3. **Understand required parameters:**
   - Authentication: How does plugin authenticate?
   - Connection: How to set `ansible_host` from cloud metadata?
   - Grouping: How to organize hosts?
   - Filtering: How to select only your VMs?

4. **Create YAML config file:**
   - Must start with `plugin: <plugin-name>`
   - Research what each cloud calls their fields
   - Example: AWS uses `public_ip_address`, GCP uses `networkInterfaces[0]...`, etc.

5. **Key Questions to Research:**
   - What authentication method to use?
   - What's the API field name for public IP?
   - How to filter only running VMs?
   - How to create host groups?

**Hints by Cloud:**

**Yandex Cloud:**
- Collection: `yandex.cloud`
- Key parameters: `auth_kind`, `folder_id`, `compose`
- IP field is nested: `network_interfaces[0]...`

**AWS:**
- Collection: `amazon.aws`
- Key parameters: `regions`, `filters`, `compose`
- IP field: `public_ip_address`
- Filter by tags: `"tag:Name": value`

**GCP:**
- Collection: `google.gcp`
- Key parameters: `projects`, `auth_kind`, `compose`
- IP field: `networkInterfaces[0].accessConfigs[0].natIP`

**Azure:**
- Collection: `azure.azcollection`
- Key parameters: `include_vm_resource_groups`, `compose`
- IP field: `public_ipv4_addresses[0]`

**Documentation Links:**
- [Ansible Inventory Plugins](https://docs.ansible.com/ansible/latest/plugins/inventory.html)
- [Dynamic Inventory Guide](https://docs.ansible.com/ansible/latest/user_guide/intro_dynamic_inventory.html)
- Search: "ansible [cloud] inventory plugin" for specific docs

</details>

**What to Document:**
- Which cloud plugin you chose and why
- How you configured authentication
- How you mapped cloud metadata to Ansible variables
- Terminal output from `ansible-inventory --graph` showing auto-discovered hosts
- Terminal output from running playbooks with dynamic inventory
- Explanation: What happens when VM IP changes? (No manual updates needed!)
- Benefits compared to static inventory

---

## How to Submit

1. **Create Branch:**
   ```bash
   git checkout -b lab05
   ```

2. **Commit Work:**
   - Add Ansible project (`ansible/` directory with roles)
   - Add documentation (`ansible/docs/LAB05.md`)
   - **IMPORTANT:** Add to `.gitignore`:
     ```
     # Ansible
     *.retry
     .vault_pass
     ansible/inventory/*.pyc
     __pycache__/
     ```
   - Commit: `git commit -m "feat: complete lab05 - ansible fundamentals"`

3. **Verify No Secrets:**
   - ✅ Check vault password not committed
   - ✅ Check `.vault_pass` not committed
   - ✅ Encrypted vault files OK to commit (they're encrypted!)
   - ✅ SSH private keys not committed

4. **Create Pull Requests:**
   - **PR #1:** `your-fork:lab05` → `course-repo:master`
   - **PR #2:** `your-fork:lab05` → `your-fork:master`

---

## Acceptance Criteria

### Main Tasks (10 points)

**Setup & Structure (2 pts):**
- [ ] Proper role-based directory structure created
- [ ] All three roles created (common, docker, app_deploy)
- [ ] Each role has appropriate tasks, handlers, and defaults
- [ ] Ansible.cfg configured correctly
- [ ] Inventory configured and connectivity tested

**System Provisioning (4 pts):**
- [ ] Common role implemented
- [ ] Docker role implemented with all required tasks
- [ ] Provision playbook uses roles correctly
- [ ] **Idempotency demonstrated** (two runs, second shows no changes)
- [ ] Terminal output from both runs provided
- [ ] Handlers used appropriately

**Application Deployment (2 pts):**
- [ ] Ansible Vault used for credentials
- [ ] Vault file encrypted (verify with `ansible-vault view`)
- [ ] App_deploy role complete with all required tasks
- [ ] Deploy playbook uses role correctly
- [ ] Container running with proper configuration
- [ ] Health check verification included
- [ ] Handlers defined in role

**Documentation (2 pts):**
- [ ] `ansible/docs/LAB05.md` complete with all sections
- [ ] Architecture and role structure explained
- [ ] Each role documented (purpose, variables, handlers)
- [ ] Idempotency analysis included
- [ ] Vault usage documented
- [ ] Key decisions explained

### Bonus Task (2.5 points)

**Dynamic Inventory (2.5 pts):**
- [ ] Cloud inventory plugin configured
- [ ] Integrates with your cloud provider from Lab 4
- [ ] Playbooks work with dynamic inventory
- [ ] Terminal output showing `ansible-inventory --graph`
- [ ] Benefits documented

---

## Rubric

| Criteria | Points | Description |
|----------|--------|-------------|
| **Setup & Structure** | 2 pts | Proper role architecture, clean organization |
| **System Provisioning** | 4 pts | All roles working, idempotent, handlers used |
| **Application Deployment** | 2 pts | Vault used, role-based deployment, app running |
| **Documentation** | 2 pts | Complete, clear, justifies decisions |
| **Bonus: Dynamic Inventory** | 2.5 pts | Cloud plugin working |
| **Total** | 12.5 pts | 10 pts required + 2.5 pts bonus |

**Grading:**
- **10/10:** Perfect role structure, deep understanding, excellent idempotency demo
- **8-9/10:** Working roles, good practices, solid understanding
- **6-7/10:** Basic roles work, some understanding, missing best practices
- **<6/10:** Roles don't work properly, no idempotency, poor structure

**Critical Requirements:**
- ✅ MUST use role-based structure (not monolithic playbooks)
- ✅ MUST demonstrate idempotency (two runs documented)
- ✅ MUST use Ansible Vault for credentials
- ✅ MUST NOT commit vault password or unencrypted secrets

---

## Resources

<details>
<summary>📚 Ansible Core</summary>

- [Ansible Documentation](https://docs.ansible.com/)
- [Ansible Roles](https://docs.ansible.com/ansible/latest/user_guide/playbooks_reuse_roles.html)
- [Best Practices](https://docs.ansible.com/ansible/latest/user_guide/playbooks_best_practices.html)

</details>

<details>
<summary>🔒 Security</summary>

- [Ansible Vault](https://docs.ansible.com/ansible/latest/user_guide/vault.html)
- [Security Best Practices](https://docs.ansible.com/ansible/latest/user_guide/playbooks_best_practices.html#best-practices-for-security)

</details>

<details>
<summary>🐳 Docker with Ansible</summary>

- [Docker Modules](https://docs.ansible.com/ansible/latest/collections/community/docker/index.html)
- [Docker Scenario Guide](https://docs.ansible.com/ansible/latest/scenario_guides/guide_docker.html)

</details>

<details>
<summary>🔄 Dynamic Inventory</summary>

- [Dynamic Inventory](https://docs.ansible.com/ansible/latest/user_guide/intro_dynamic_inventory.html)
- [Inventory Plugins](https://docs.ansible.com/ansible/latest/plugins/inventory.html)

</details>

---

## Looking Ahead

**Lab 6:** Advanced Ansible features (blocks, tags, Docker Compose, CI/CD automation)

You'll build on these roles by:
- Adding blocks and tags for better control
- Upgrading to Docker Compose
- Implementing wipe logic
- Automating deployment with GitHub Actions

---

**Good luck!** 🚀

> **Remember:** Roles are the foundation of Ansible. Focus on creating clean, idempotent roles with proper structure. Use handlers efficiently. Secure your credentials with Vault. Document your decisions, not just your code. This foundation will be essential for Lab 6!
