# Lab 5 — Ansible Fundamentals

## 1. Architecture Overview

* **Ansible version:** 2.16.14
* **Target VM OS:** Ubuntu 24.04 LTS
* **Role structure:**

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

**Why roles?**
Roles allow modular, reusable, and maintainable code. Each role encapsulates tasks, defaults, handlers, and variables, so playbooks remain clean.

# Command to run:
```bash
docker run -it --rm -v ${PWD}\app_python\ansible:/ansible -v C:\Users\maior\.ssh\vm_machine_ubuntu:/root/.ssh/vm_machine_ubuntu  -w /ansible willhallonline/ansible:2.16-debian-bookworm-slim ` bash
```
---

## 2. Roles Documentation

### **2.1 Common Role**

* **Purpose:** Basic system provisioning (apt updates, packages, timezone)
* **Defaults:** `common_packages: [python3-pip, curl, git, vim, htop]`
* **Handlers:** None
* **Dependencies:** None

### **2.2 Docker Role**

* **Purpose:** Install and configure Docker engine
* **Defaults:** Docker version, user to add to `docker` group
* **Handlers:** `restart docker` — restarts Docker service if needed
* **Dependencies:** `common` role

### **2.3 App Deploy Role**

* **Purpose:** Deploy containerized Python app from previous labs
* **Defaults:**
  * `app_name: devops-info-service`
  * `docker_image_tag: latest`
  * `app_port: 5000`
  * `app_container_name: devops-info-service`
  * link to image: https://hub.docker.com/r/daniil20xx/devops-info-service
* **Handlers:** `restart app container` — restarts app container if task triggers
* **Dependencies:** `docker` role

---

## 3. Idempotency Demonstration

### **3.1 Provisioning (common + docker)**

**First run:**

![playbook-1](/ansible/docs/screenshots/playbook-1.png)

* Tasks with **error** and **changes**

**Second run:**

![playbook-2](/ansible/docs/screenshots/playbook-2.png)


* Tasks with **changes**

**Third run:**

![playbook-3](/ansible/docs/screenshots/playbook-3.png)

* All tasks `ok` (green), `changed=0`
* Idempotency confirmed

### **3.2 Deployment (app_deploy)**

**First run:**

![docker-playbook-1](/ansible/docs/screenshots/docker-playbook-1.png)

* Docker container pulled and started
* `changed=3` (container creation, old container removal, docker login)
* `ignored=1`(container was not created yet)

**Second run:**

![docker-playbook-2](/ansible/docs/screenshots/docker-playhook-2.png)

* Many tasks `ok`, `changed=3`

**Third run:**

![docker-playbook-3](/ansible/docs/screenshots/docker-playhook-3.png)

* Many tasks `ok`, `changed=3`

**Analysis:**

##### changed=3 is repeated why:
- Stop existing container - the module checks if the container is running; even if the container is already running, Ansible marks the task as changed when bringing it to the desired state (e.g. restart or pull latest image).
- Remove old container - the old container is removed (if it is updated or recreated).
- Run container - a new container is created based on the latest image (if tag latest, Ansible pulls the latest image even when restarting).

---

## 4. Ansible Vault Usage

* Vault file: `group_vars/all.yml`

```yaml
dockerhub_username: daniil20xx
dockerhub_password: [HIDDEN]
app_name: devops-info-service
docker_image: "{{ dockerhub_username }}/{{ app_name }}"
docker_image_tag: latest
app_port: 5000
app_container_name: "{{ app_name }}"
```

* Vault password not committed to repo
* Deployed with:

```bash
ansible-playbook playbooks/deploy.yml --ask-vault-pass
```

* **Purpose:** Keep Docker Hub credentials secure
* **Best practice:** `no_log: true` prevents secrets from appearing in logs

---

## 5. Deployment Verification

**Check containers:**

![docker-check](/ansible/docs/screenshots/docker-check.png)

**Health check:**

![health-check](/ansible/docs/screenshots/working_url.png)

---

## 6. Key Decisions

* **Why use roles instead of plain playbooks?**
  Roles separate concerns, making playbooks modular, reusable, and easier to maintain.

* **How do roles improve reusability?**
  Each role encapsulates a repeatable task set, which can be reused in multiple projects.

* **What makes a task idempotent?**
  Using stateful modules ensures tasks only make changes when necessary.

* **How do handlers improve efficiency?**
  Handlers execute only when notified, avoiding unnecessary service restarts.

* **Why is Ansible Vault necessary?**
  Vault securely stores credentials and sensitive variables, preventing secrets from leaking in version control.

---

## 7. Challenges

* Run `ansible` on Docker and move nessasary keys to it
* Connect to vm using ansible and ssh keys

---
