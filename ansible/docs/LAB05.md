# 1. Architecture Overview

### Ansible version: 2.12.5
### Target VM OS: Ubuntu 24.04 LTS
### Role structure:
```text
ansible/
├── inventory/
│   └── hosts.ini
├── roles/
│   ├── common/
│   ├── docker/
│   └── app_deploy/
├── playbooks/
│   ├── site.yml
│   ├── provision.yml
│   └── deploy.yml
├── group_vars/
│   └── all.yml
├── ansible.cfg
└── docs/
    └── LAB05.md
```

### Why roles:
- They allow you to separate tasks by functionality.
- They improve code reuse.
- They are easy to maintain and test independently.

# 2. Roles Documentation
### 2.1 common
- Purpose: Basic system setup (apt update, package installation, time settings).
- Variables: list of packages defaults/main.yml.
- Handlers: no.
- Dependencies: no.

### 2.2 docker
- Purpose: Install and run Docker, add a user to the docker group.
- Variables: Docker version, username.
- Handlers: restart docker service.
- Dependencies: common.
### 2.3 app_deploy
- Purpose: deploying a Python container.
- Variables: Docker Hub username, password, application name, port, container name, image tag.
- Handlers: restart the container if necessary.
- Dependencies: docker.

# 3. Idempotency Demonstration

### First run of playbook deploy.yml:
![First run](ansible/docs/screenshots/img.png)

### Second run of playbook deploy.yml:
![Second run](ansible/docs/screenshots/img_1.png)

### Analysis:

- `ok` — tasks where no changes were made (e.g., a port is already open).
- `changed` — tasks that updated the state (pull, run, restart the container).
The roles are idempotent by design, but starting a container always calls "changed" because we're deleting the old one and creating a new one.

# 4. Ansible Vault Usage

### Vault file: `group_vars/all.yml`
Content:
```yml
dockerhub_username: th1ef
dockerhub_password: my_password
app_name: devops-info-service
docker_image: "{{ dockerhub_username }}/{{ app_name }}"
docker_image_tag: latest
app_port: 5000
app_container_name: "{{ app_name }}"
```

# 5. Deployment Verification
### Container condition:
![Container condition](ansible/docs/screenshots/img_2.png)

### Health check:
![Health check](ansible/docs/screenshots/img_3.png)


### 6. Key Decisions

- **Why roles instead of monolithic playbooks?** \
They allow you to structure tasks and are easier to maintain and test.
- **How do roles improve reusability?** \
You can use a single role across different VMs and projects without duplicating code.
- **What makes a task idempotent?** \
The module checks the current state and makes changes only when necessary (state: present, state: started).
- **How do handlers improve efficiency?** \
They are executed only when the state changes, preventing unnecessary service restarts.
- **Why Ansible Vault?** \
To securely store sensitive data (passwords, tokens) in the repository.

### 7. Challenges
- Errors when logging into Docker Hub without a collection.
- Incorrect SSH key permissions in the container.
- Pull errors if the image wasn't on Docker Hub — resolved by uploading the image using your own account.