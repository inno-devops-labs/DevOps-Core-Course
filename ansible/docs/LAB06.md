# Lab 6: Advanced Ansible & CI/CD - Submission

**Name:** Adilia Saifetdiarova
**Date:** 2026-02-21
**Lab Points:** 10 + X bonus

---

## Task 1: Blocks & Tags (2 pts)


## Refactor with Blocks & Tags

### Selective execution with `--tags`

```bash
ansible-playbook playbooks/provision.yml --tags "docker"
```

```bash
PLAY [Provision web servers] ***********************************************************************************************************************************

TASK [Gathering Facts] *****************************************************************************************************************************************
ok: [info-service]

TASK [common : Log package installation completion] ************************************************************************************************************
ok: [info-service] => {
    "msg": "Package installation block completed"
}

TASK [common : Create completion timestamp] ********************************************************************************************************************
changed: [info-service]

TASK [common : User management completed] **********************************************************************************************************************
ok: [info-service] => {
    "msg": "User management block finished"
}

TASK [docker : Docker role execution started] ******************************************************************************************************************
ok: [info-service] => {
    "msg": "Starting Docker role execution"
}

TASK [docker : Install Docker prerequisites] *******************************************************************************************************************
ok: [info-service]

TASK [docker : Add Docker GPG key] *****************************************************************************************************************************
ok: [info-service]

TASK [docker : Add Docker repository] **************************************************************************************************************************
ok: [info-service]

TASK [docker : Update apt cache after repository setup] ********************************************************************************************************
changed: [info-service]

TASK [docker : Install Docker packages] ************************************************************************************************************************
ok: [info-service]

TASK [docker : Install Docker Python SDK] **********************************************************************************************************************
ok: [info-service]

TASK [docker : Ensure Docker service is running] ***************************************************************************************************************
ok: [info-service]

TASK [docker : Add users to docker group] **********************************************************************************************************************
ok: [info-service] => (item=ubuntu)
ok: [info-service] => (item=ubuntu)

TASK [docker : Create docker-compose directory] ****************************************************************************************************************
ok: [info-service]

TASK [docker : Verify Docker installation] *********************************************************************************************************************
ok: [info-service]

TASK [docker : Display Docker version] *************************************************************************************************************************
ok: [info-service] => {
    "msg": "Docker version: Docker version 29.2.1, build a5c7197"
}

PLAY RECAP *****************************************************************************************************************************************************
info-service               : ok=16   changed=2    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0
```





```bash
ansible-playbook playbooks/provision.yml --skip-tags "common"
```

```bash
PLAY [Provision web servers] ***********************************************************************************************************************************

TASK [Gathering Facts] *****************************************************************************************************************************************
ok: [info-service]

TASK [docker : Docker role execution started] ******************************************************************************************************************
ok: [info-service] => {
    "msg": "Starting Docker role execution"
}

TASK [docker : Install Docker prerequisites] *******************************************************************************************************************
ok: [info-service]

TASK [docker : Add Docker GPG key] *****************************************************************************************************************************
ok: [info-service]

TASK [docker : Add Docker repository] **************************************************************************************************************************
ok: [info-service]

TASK [docker : Update apt cache after repository setup] ********************************************************************************************************
changed: [info-service]

TASK [docker : Install Docker packages] ************************************************************************************************************************
ok: [info-service]

TASK [docker : Install Docker Python SDK] **********************************************************************************************************************
ok: [info-service]

TASK [docker : Ensure Docker service is running] ***************************************************************************************************************
ok: [info-service]

TASK [docker : Add users to docker group] **********************************************************************************************************************
ok: [info-service] => (item=ubuntu)
ok: [info-service] => (item=ubuntu)

TASK [docker : Create docker-compose directory] ****************************************************************************************************************
ok: [info-service]

TASK [docker : Verify Docker installation] *********************************************************************************************************************
ok: [info-service]

TASK [docker : Display Docker version] *************************************************************************************************************************
ok: [info-service] => {
    "msg": "Docker version: Docker version 29.2.1, build a5c7197"
}

PLAY RECAP *****************************************************************************************************************************************************
info-service               : ok=13   changed=1    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0
```





```bash
ansible-playbook playbooks/provision.yml --tags "packages"
```

```bash
PLAY [Provision web servers] ***********************************************************************************************************************************

TASK [Gathering Facts] *****************************************************************************************************************************************
ok: [info-service]

TASK [common : Update apt cache] *******************************************************************************************************************************
ok: [info-service]

TASK [common : Install common packages] ************************************************************************************************************************
ok: [info-service]

TASK [common : Upgrade system packages] ************************************************************************************************************************
skipping: [info-service]

TASK [common : Log package installation completion] ************************************************************************************************************
ok: [info-service] => {
    "msg": "Package installation block completed"
}

TASK [common : Create completion timestamp] ********************************************************************************************************************
changed: [info-service]

TASK [common : User management completed] **********************************************************************************************************************
ok: [info-service] => {
    "msg": "User management block finished"
}

TASK [docker : Install Docker packages] ************************************************************************************************************************
ok: [info-service]

PLAY RECAP *****************************************************************************************************************************************************
info-service               : ok=7    changed=1    unreachable=0    failed=0    skipped=1    rescued=0    ignored=0 
```





```bash
ansible-playbook playbooks/provision.yml --tags "docker" --check
```

```bash
PLAY [Provision web servers] ***********************************************************************************************************************************

TASK [Gathering Facts] *****************************************************************************************************************************************
ok: [info-service]

TASK [common : Log package installation completion] ************************************************************************************************************
ok: [info-service] => {
    "msg": "Package installation block completed"
}

TASK [common : Create completion timestamp] ********************************************************************************************************************
changed: [info-service]

TASK [common : User management completed] **********************************************************************************************************************
ok: [info-service] => {
    "msg": "User management block finished"
}

TASK [docker : Docker role execution started] ******************************************************************************************************************
ok: [info-service] => {
    "msg": "Starting Docker role execution"
}

TASK [docker : Install Docker prerequisites] *******************************************************************************************************************
ok: [info-service]

TASK [docker : Add Docker GPG key] *****************************************************************************************************************************
ok: [info-service]

TASK [docker : Add Docker repository] **************************************************************************************************************************
ok: [info-service]

TASK [docker : Update apt cache after repository setup] ********************************************************************************************************
changed: [info-service]

TASK [docker : Install Docker packages] ************************************************************************************************************************
ok: [info-service]

TASK [docker : Install Docker Python SDK] **********************************************************************************************************************
ok: [info-service]

TASK [docker : Ensure Docker service is running] ***************************************************************************************************************
ok: [info-service]

TASK [docker : Add users to docker group] **********************************************************************************************************************
ok: [info-service] => (item=ubuntu)
ok: [info-service] => (item=ubuntu)

TASK [docker : Create docker-compose directory] ****************************************************************************************************************
ok: [info-service]

TASK [docker : Verify Docker installation] *********************************************************************************************************************
skipping: [info-service]

TASK [docker : Display Docker version] *************************************************************************************************************************
ok: [info-service] => {
    "msg": "Docker version: "
}

PLAY RECAP *****************************************************************************************************************************************************
info-service               : ok=15   changed=2    unreachable=0    failed=0    skipped=1    rescued=0    ignored=0
```





```bash
ansible-playbook playbooks/provision.yml --tags "docker_install"
```

```bash
PLAY [Provision web servers] ***********************************************************************************************************************************

TASK [Gathering Facts] *****************************************************************************************************************************************
ok: [info-service]

TASK [common : Log package installation completion] ************************************************************************************************************
ok: [info-service] => {
    "msg": "Package installation block completed"
}

TASK [common : Create completion timestamp] ********************************************************************************************************************
changed: [info-service]

TASK [common : User management completed] **********************************************************************************************************************
ok: [info-service] => {
    "msg": "User management block finished"
}

TASK [docker : Install Docker prerequisites] *******************************************************************************************************************
ok: [info-service]

TASK [docker : Add Docker GPG key] *****************************************************************************************************************************
ok: [info-service]

TASK [docker : Add Docker repository] **************************************************************************************************************************
ok: [info-service]

TASK [docker : Update apt cache after repository setup] ********************************************************************************************************
changed: [info-service]

TASK [docker : Install Docker packages] ************************************************************************************************************************
ok: [info-service]

TASK [docker : Install Docker Python SDK] **********************************************************************************************************************
ok: [info-service]

PLAY RECAP *****************************************************************************************************************************************************
info-service               : ok=10   changed=2    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0 
```

### List of all available tags

- app_user
- apt
- block_config
- block_install
- block_packages
- block_repository
- block_users
- common
- config
- containers
- debug
- directories
- docker
- docker_config
- docker_install
- gpg, hostname
- packages
- prerequisites
- python
- repository
- service
- ssh
- sudo
- system
- timezone
- upgrade
- users



## Task 2: Docker Compose (3 pts)

### Docker Compose deployment success

```bash
--ask-vault-pass
```

```bash
PLAY [Deploy application] ********************************************************************************************************************************************

TASK [Gathering Facts] ***********************************************************************************************************************************************
ok: [info-service]

TASK [docker : Install Docker prerequisites] *************************************************************************************************************************
ok: [info-service]

TASK [docker : Add Docker GPG key] ***********************************************************************************************************************************
changed: [info-service]

TASK [docker : Add Docker repository] ********************************************************************************************************************************
ok: [info-service]

TASK [docker : Update apt cache after repository setup] **************************************************************************************************************
changed: [info-service]

TASK [docker : Install Docker packages] ******************************************************************************************************************************
ok: [info-service]

TASK [docker : Install Docker Python SDK] ****************************************************************************************************************************
changed: [info-service]

TASK [docker : Ensure Docker service is running] *********************************************************************************************************************
changed: [info-service]

TASK [docker : Add users to docker group] ****************************************************************************************************************************
changed: [info-service] => (item=ubuntu)
changed: [info-service] => (item=appuser)

TASK [docker : Create docker-compose directory] **********************************************************************************************************************
changed: [info-service]

TASK [docker : Verify Docker installation] ***************************************************************************************************************************
ok: [info-service]

TASK [docker : Display Docker version] *******************************************************************************************************************************
ok: [info-service] => {
    "msg": "Docker version: Docker version 29.2.1, build a5c7197"
}

TASK [common : Update apt cache] *************************************************************************************************************************************
changed: [info-service]

TASK [common : Install common packages] ******************************************************************************************************************************
changed: [info-service]

TASK [common : Upgrade system packages] ******************************************************************************************************************************
skipping: [info-service]

TASK [common : Log package installation completion] ******************************************************************************************************************
ok: [info-service] => {
    "msg": "Package installation block completed"
}

TASK [common : Create completion timestamp] **************************************************************************************************************************
changed: [info-service]

TASK [common : Create application user] ******************************************************************************************************************************
changed: [info-service]

TASK [common : Ensure SSH directory exists for app user] *************************************************************************************************************
changed: [info-service]

TASK [common : Add users to sudo group] ******************************************************************************************************************************
skipping: [info-service]

TASK [common : User management completed] ****************************************************************************************************************************
ok: [info-service] => {
    "msg": "User management block finished"
}

TASK [common : Set timezone] *****************************************************************************************************************************************
changed: [info-service]

TASK [common : Configure hostname] ***********************************************************************************************************************************
changed: [info-service]

TASK [common : Configure SSH hardening] ******************************************************************************************************************************
ok: [info-service] => (item={'key': 'PasswordAuthentication', 'value': 'no'})
ok: [info-service] => (item={'key': 'PermitRootLogin', 'value': 'no'})
ok: [info-service] => (item={'key': 'ClientAliveInterval', 'value': '300'})

TASK [web_app : Login to Docker Hub] *********************************************************************************************************************************
ok: [info-service]

TASK [web_app : Pull Docker image] ***********************************************************************************************************************************
ok: [info-service]

TASK [web_app : Check if container exists] ***************************************************************************************************************************
ok: [info-service]

TASK [web_app : Stop existing container if running] ******************************************************************************************************************
changed: [info-service]

TASK [web_app : Remove old container if exists] **********************************************************************************************************************
changed: [info-service]

TASK [web_app : Create application directory] ************************************************************************************************************************
changed: [info-service]

TASK [web_app : Deploy application container] ************************************************************************************************************************
changed: [info-service]

TASK [web_app : Wait for application to start] ***********************************************************************************************************************
ok: [info-service]

TASK [web_app : Check application health endpoint] *******************************************************************************************************************
ok: [info-service]

TASK [web_app : Display health check result] *************************************************************************************************************************
ok: [info-service] => {
    "msg": "Application is healthy! Response: {'status': 'healthy', 'timestamp': '2026-02-10T13:06:04.889120+00:00', 'uptime_seconds': 13}"
}

TASK [Show running containers] ***************************************************************************************************************************************
changed: [info-service]

TASK [Display container status] **************************************************************************************************************************************
ok: [info-service] => {
    "msg": [
        "NAMES          IMAGE                              STATUS          PORTS",
        "info-service   sayfetik/info-service:latest   Up 17 seconds   0.0.0.0:8000->5000/tcp"
    ]
}

PLAY RECAP ***********************************************************************************************************************************************************
info-service               : ok=34   changed=19   unreachable=0    failed=0    skipped=2    rescued=0    ignored=0
```

### Idempotency

```bash
ansible-playbook playbooks/deploy.yml --ask-vault-pass
```

```bash
PLAY [Deploy application] ********************************************************************************************************************************************

TASK [Gathering Facts] ***********************************************************************************************************************************************
ok: [info-service]

TASK [docker : Install Docker prerequisites] *************************************************************************************************************************
ok: [info-service]

TASK [docker : Add Docker GPG key] ***********************************************************************************************************************************
ok: [info-service]

TASK [docker : Add Docker repository] ********************************************************************************************************************************
ok: [info-service]

TASK [docker : Update apt cache after repository setup] **************************************************************************************************************
changed: [info-service]

TASK [docker : Install Docker packages] ******************************************************************************************************************************
ok: [info-service]

TASK [docker : Install Docker Python SDK] ****************************************************************************************************************************
ok: [info-service]

TASK [docker : Ensure Docker service is running] *********************************************************************************************************************
ok: [info-service]

TASK [docker : Add users to docker group] ****************************************************************************************************************************
ok: [info-service] => (item=ubuntu)
ok: [info-service] => (item=appuser)

TASK [docker : Create docker-compose directory] **********************************************************************************************************************
ok: [info-service]

TASK [docker : Verify Docker installation] ***************************************************************************************************************************
ok: [info-service]

TASK [docker : Display Docker version] *******************************************************************************************************************************
ok: [info-service] => {
    "msg": "Docker version: Docker version 29.2.1, build a5c7197"
}

TASK [common : Update apt cache] *************************************************************************************************************************************
ok: [info-service]

TASK [common : Install common packages] ******************************************************************************************************************************
ok: [info-service]

TASK [common : Upgrade system packages] ******************************************************************************************************************************
skipping: [info-service]

TASK [common : Log package installation completion] ******************************************************************************************************************
ok: [info-service] => {
    "msg": "Package installation block completed"
}

TASK [common : Create completion timestamp] **************************************************************************************************************************
changed: [info-service]

TASK [common : Create application user] ******************************************************************************************************************************
ok: [info-service]

TASK [common : Ensure SSH directory exists for app user] *************************************************************************************************************
ok: [info-service]

TASK [common : Add users to sudo group] ******************************************************************************************************************************
skipping: [info-service]

TASK [common : User management completed] ****************************************************************************************************************************
ok: [info-service] => {
    "msg": "User management block finished"
}

TASK [common : Set timezone] *****************************************************************************************************************************************
ok: [info-service]

TASK [common : Configure hostname] ***********************************************************************************************************************************
ok: [info-service]

TASK [common : Configure SSH hardening] ******************************************************************************************************************************
ok: [info-service] => (item={'key': 'PasswordAuthentication', 'value': 'no'})
ok: [info-service] => (item={'key': 'PermitRootLogin', 'value': 'no'})
ok: [info-service] => (item={'key': 'ClientAliveInterval', 'value': '300'})

TASK [web_app : Login to Docker Hub] *********************************************************************************************************************************
ok: [info-service]

TASK [web_app : Pull Docker image] ***********************************************************************************************************************************
ok: [info-service]

TASK [web_app : Check if container exists] ***************************************************************************************************************************
ok: [info-service]

TASK [web_app : Stop existing container if running] ******************************************************************************************************************
changed: [info-service]

TASK [web_app : Remove old container if exists] **********************************************************************************************************************
changed: [info-service]

TASK [web_app : Create application directory] ************************************************************************************************************************
ok: [info-service]

TASK [web_app : Deploy application container] ************************************************************************************************************************
changed: [info-service]

TASK [web_app : Wait for application to start] ***********************************************************************************************************************
ok: [info-service]

TASK [web_app : Check application health endpoint] *******************************************************************************************************************
ok: [info-service]

TASK [web_app : Display health check result] *************************************************************************************************************************
ok: [info-service] => {
    "msg": "Application is healthy! Response: {'status': 'healthy', 'timestamp': '2026-02-10T13:06:04.889120+00:00', 'uptime_seconds': 13}"
}

TASK [Show running containers] ***************************************************************************************************************************************
changed: [info-service]

TASK [Display container status] **************************************************************************************************************************************
ok: [info-service] => {
    "msg": [
        "NAMES          IMAGE                              STATUS          PORTS",
        "info-service   sayfetik/info-service:latest   Up 17 seconds   0.0.0.0:8000->5000/tcp"
    ]
}

PLAY RECAP ***********************************************************************************************************************************************************
info-service               : ok=34   changed=6    unreachable=0    failed=0    skipped=2    rescued=0    ignored=0
```

### Application running and accessible

```bash
curl http://localhost:8000/health
```

```bash
{"status":"healthy","timestamp":"2026-02-10T13:35:52.669019+00:00","uptime_seconds":1801}
```

### Contents of templated docker compose

```bash
docker-compose.yml.j2
```

```bash
version: '{{ compose_version }}'

services:
  {{ app_name }}:
    image: {{ docker_image }}:{{ docker_tag }}
    container_name: {{ app_name }}_{{ app_name }}
    hostname: {{ app_name }}
    
    ports:
      - "{{ app_port }}:{{ app_internal_port }}"
    
    environment:
      {% for key, value in app_environment.items() %}
      - {{ key }}={{ value }}
      {% endfor %}
      
      - APP_SECRET_KEY={{ app_secret_key | default('change_me_in_production') }}
    
    env_file:
      - .env
    
    volumes:
      - {{ data_volume }}:/app/data
      - {{ log_volume }}:/app/logs
      - ./config:/app/config:ro
    
    networks:
      - {{ network_name }}
    
    restart: {{ service_restart_policy }}
    
    healthcheck:
      test: {{ service_healthcheck.test | to_json }}
      interval: {{ service_healthcheck.interval }}
      timeout: {{ service_healthcheck.timeout }}
      retries: {{ service_healthcheck.retries }}
      start_period: {{ service_healthcheck.start_period }}
    
    deploy:
      resources:
        limits:
          cpus: '0.50'
          memory: 512M
        reservations:
          cpus: '0.25'
          memory: 256M
    
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
    
    labels:
      - "maintainer=DevOps Team"
      - "version={{ app_version }}"
      - "description={{ app_description }}"

networks:
  {{ network_name }}:
    driver: {{ network_driver }}
    name: {{ network_name }}

volumes:
  {{ data_volume }}:
    name: {{ data_volume }}
  {{ log_volume }}:
    name: {{ log_volume }}

```



## Task 3: Wipe Logic (1 pt)

### Output of Scenario 1

```bash
ansible-playbook playbooks/deploy.yml --ask-vault-pass
```

```bash
PLAY [Deploy application] ********************************************************************************************************************************************

TASK [Gathering Facts] ***********************************************************************************************************************************************
ok: [info-service]

TASK [docker : Install Docker prerequisites] *************************************************************************************************************************
ok: [info-service]

TASK [docker : Add Docker GPG key] ***********************************************************************************************************************************
ok: [info-service]

TASK [docker : Add Docker repository] ********************************************************************************************************************************
ok: [info-service]

TASK [docker : Update apt cache after repository setup] **************************************************************************************************************
changed: [info-service]

TASK [docker : Install Docker packages] ******************************************************************************************************************************
ok: [info-service]

TASK [docker : Install Docker Python SDK] ****************************************************************************************************************************
ok: [info-service]

TASK [docker : Ensure Docker service is running] *********************************************************************************************************************
ok: [info-service]

TASK [docker : Add users to docker group] ****************************************************************************************************************************
ok: [info-service] => (item=ubuntu)
ok: [info-service] => (item=appuser)

TASK [docker : Create docker-compose directory] **********************************************************************************************************************
ok: [info-service]

TASK [docker : Verify Docker installation] ***************************************************************************************************************************
ok: [info-service]

TASK [docker : Display Docker version] *******************************************************************************************************************************
ok: [info-service] => {
    "msg": "Docker version: Docker version 29.2.1, build a5c7197"
}

TASK [common : Update apt cache] *************************************************************************************************************************************
ok: [info-service]

TASK [common : Install common packages] ******************************************************************************************************************************
ok: [info-service]

TASK [common : Upgrade system packages] ******************************************************************************************************************************
skipping: [info-service]

TASK [common : Log package installation completion] ******************************************************************************************************************
ok: [info-service] => {
    "msg": "Package installation block completed"
}

TASK [common : Create completion timestamp] **************************************************************************************************************************
changed: [info-service]

TASK [common : Create application user] ******************************************************************************************************************************
ok: [info-service]

TASK [common : Ensure SSH directory exists for app user] *************************************************************************************************************
ok: [info-service]

TASK [common : Add users to sudo group] ******************************************************************************************************************************
skipping: [info-service]

TASK [common : User management completed] ****************************************************************************************************************************
ok: [info-service] => {
    "msg": "User management block finished"
}

TASK [common : Set timezone] *****************************************************************************************************************************************
ok: [info-service]

TASK [common : Configure hostname] ***********************************************************************************************************************************
ok: [info-service]

TASK [common : Configure SSH hardening] ******************************************************************************************************************************
ok: [info-service] => (item={'key': 'PasswordAuthentication', 'value': 'no'})
ok: [info-service] => (item={'key': 'PermitRootLogin', 'value': 'no'})
ok: [info-service] => (item={'key': 'ClientAliveInterval', 'value': '300'})

TASK [web_app : Include wipe tasks] **********************************************************************************************************************************
included: /Users/sayfetik/DevOps-Core-Course/ansible/roles/web_app/tasks/wipe.yml for info-service

TASK [web_app : Wipe web application - confirmation check] ***********************************************************************************************************
skipping: [info-service]

TASK [web_app : Check if Docker Compose project exists] **************************************************************************************************************
ok: [info-service]

TASK [web_app : Stop and remove Docker Compose project] **************************************************************************************************************
skipping: [info-service]

TASK [web_app : Remove application directory] ************************************************************************************************************************
ok: [info-service]

TASK [web_app : Remove Docker images] ********************************************************************************************************************************
skipping: [info-service]

TASK [web_app : Verify wipe completion] ******************************************************************************************************************************
[ERROR]: Task failed: Action failed.
Origin: /Users/sayfetik/DevOps-Core-Course/ansible/roles/web_app/tasks/wipe.yml:65:7

63         - images
64
65     - name: Verify wipe completion
         ^ column 7

fatal: [info-service]: FAILED! => {"changed": false, "cmd": "docker ps -a --filter \"name=info-service\" --format \"{{.Names}}\"\n", "delta": "0:00:00.033141", "end": "2026-02-10 18:46:55.273423", "failed_when_result": true, "msg": "", "rc": 0, "start": "2026-02-10 18:46:55.240282", "stderr": "", "stderr_lines": [], "stdout": "info-service", "stdout_lines": ["info-service"]}

PLAY RECAP ***********************************************************************************************************************************************************
info-service               : ok=25   changed=2    unreachable=0    failed=1    skipped=5    rescued=0    ignored=0
```

### Output of Scenario 2

```bash
ansible-playbook playbooks/deploy.yml --ask-vault-pass \
  -e "web_app_wipe=true" \
  --tags web_app_wipe
```

```bash
PLAY [Deploy application] ********************************************************************************************************************************************

TASK [Gathering Facts] ***********************************************************************************************************************************************
ok: [info-service]

TASK [common : Log package installation completion] ******************************************************************************************************************
ok: [info-service] => {
    "msg": "Package installation block completed"
}

TASK [common : Create completion timestamp] **************************************************************************************************************************
changed: [info-service]

TASK [common : User management completed] ****************************************************************************************************************************
ok: [info-service] => {
    "msg": "User management block finished"
}

TASK [web_app : Include wipe tasks] **********************************************************************************************************************************
included: /Users/sayfetik/DevOps-Core-Course/ansible/roles/web_app/tasks/wipe.yml for info-service

TASK [web_app : Wipe web application - confirmation check] ***********************************************************************************************************
ok: [info-service] => {
    "msg": "===========================================\nWIPE OPERATION INITIATED\n\nThis will remove:\n1. Docker containers for info-service\n2. Docker volumes for info-service\n3. Application directory: /opt/info-service\n4. Docker images (optional)\n\nWipe variable: true\nTag: web_app_wipe\n===========================================\n"
}

TASK [web_app : Check if Docker Compose project exists] **************************************************************************************************************
ok: [info-service]

TASK [web_app : Stop and remove Docker Compose project] **************************************************************************************************************
skipping: [info-service]

TASK [web_app : Remove application directory] ************************************************************************************************************************
ok: [info-service]

TASK [web_app : Remove Docker images] *********************************************************************************************************************
skipping: [info-service]

TASK [web_app : Verify wipe completion] ******************************************************************************************************************************
ok: [info-service]

TASK [web_app : Display wipe results] ********************************************************************************************************************************
ok: [info-service] => {
    "msg": "===========================================\nWIPE OPERATION COMPLETED\n\nCompose file existed: False\nDirectory removed: False\n\nRemaining containers:\nNone - all containers removed successfully\n\nApplication directory exists: False\n===========================================\n"
}

PLAY RECAP ***********************************************************************************************************************************************************
info-service               : ok=10   changed=1    unreachable=0    failed=0    skipped=2    rescued=0    ignored=0
```

### Output of Scenario 3

```bash
ansible-playbook playbooks/deploy.yml --ask-vault-pass \
  -e "web_app_wipe=true"
```

```bash
PLAY [Deploy application] ********************************************************************************************************************************************

TASK [Gathering Facts] ***********************************************************************************************************************************************
ok: [info-service]

TASK [docker : Install Docker prerequisites] *************************************************************************************************************************
ok: [info-service]

TASK [docker : Add Docker GPG key] ***********************************************************************************************************************************
ok: [info-service]

TASK [docker : Add Docker repository] ********************************************************************************************************************************
ok: [info-service]

TASK [docker : Update apt cache after repository setup] **************************************************************************************************************
changed: [info-service]

TASK [docker : Install Docker packages] ******************************************************************************************************************************
ok: [info-service]

TASK [docker : Install Docker Python SDK] ****************************************************************************************************************************
ok: [info-service]

TASK [docker : Ensure Docker service is running] *********************************************************************************************************************
ok: [info-service]

TASK [docker : Add users to docker group] ****************************************************************************************************************************
ok: [info-service] => (item=ubuntu)
ok: [info-service] => (item=appuser)

TASK [docker : Create docker-compose directory] **********************************************************************************************************************
ok: [info-service]

TASK [docker : Verify Docker installation] ***************************************************************************************************************************
ok: [info-service]

TASK [docker : Display Docker version] *******************************************************************************************************************************
ok: [info-service] => {
    "msg": "Docker version: Docker version 29.2.1, build a5c7197"
}

TASK [common : Update apt cache] *************************************************************************************************************************************
ok: [info-service]

TASK [common : Install common packages] ******************************************************************************************************************************
ok: [info-service]

TASK [common : Upgrade system packages] ******************************************************************************************************************************
skipping: [info-service]

TASK [common : Log package installation completion] ******************************************************************************************************************
ok: [info-service] => {
    "msg": "Package installation block completed"
}

TASK [common : Create completion timestamp] **************************************************************************************************************************
changed: [info-service]

TASK [common : Create application user] ******************************************************************************************************************************
ok: [info-service]

TASK [common : Ensure SSH directory exists for app user] *************************************************************************************************************
ok: [info-service]

TASK [common : Add users to sudo group] ******************************************************************************************************************************
skipping: [info-service]

TASK [common : User management completed] ****************************************************************************************************************************
ok: [info-service] => {
    "msg": "User management block finished"
}

TASK [common : Set timezone] *****************************************************************************************************************************************
ok: [info-service]

TASK [common : Configure hostname] ***********************************************************************************************************************************
ok: [info-service]

TASK [common : Configure SSH hardening] ******************************************************************************************************************************
ok: [info-service] => (item={'key': 'PasswordAuthentication', 'value': 'no'})
ok: [info-service] => (item={'key': 'PermitRootLogin', 'value': 'no'})
ok: [info-service] => (item={'key': 'ClientAliveInterval', 'value': '300'})

TASK [web_app : Include wipe tasks] **********************************************************************************************************************************
included: /Users/sayfetik/DevOps-Core-Course/ansible/roles/web_app/tasks/wipe.yml for info-service

TASK [web_app : Wipe web application - confirmation check] ***********************************************************************************************************
ok: [info-service] => {
    "msg": "===========================================\nWIPE OPERATION INITIATED\n\nThis will remove:\n1. Docker containers for info-service\n2. Docker volumes for info-service\n3. Application directory: /opt/info-service\n4. Docker images (optional)\n\nWipe variable: true\nTag: web_app_wipe\n===========================================\n"
}

TASK [web_app : Check if Docker Compose project exists] **************************************************************************************************************
ok: [info-service]

TASK [web_app : Stop and remove Docker Compose project] **************************************************************************************************************
skipping: [info-service]

TASK [web_app : Remove application directory] ************************************************************************************************************************
ok: [info-service]

TASK [web_app : Remove Docker images] ********************************************************************************************************************************
skipping: [info-service]

TASK [web_app : Verify wipe completion] ******************************************************************************************************************************
ok: [info-service]

TASK [web_app : Display wipe results] ********************************************************************************************************************************
ok: [info-service] => {
    "msg": "===========================================\nWIPE OPERATION COMPLETED\n\nCompose file existed: False\nDirectory removed: False\n\nRemaining containers:\nNone - all containers removed successfully\n\nApplication directory exists: False\n===========================================\n"
}

TASK [web_app : Login to Docker Hub] *********************************************************************************************************************************
ok: [info-service]

TASK [web_app : Pull Docker image] ***********************************************************************************************************************************
ok: [info-service]

TASK [web_app : Check if container exists] ***************************************************************************************************************************
ok: [info-service]

TASK [web_app : Stop existing container if running] ******************************************************************************************************************
skipping: [info-service]

TASK [web_app : Remove old container if exists] **********************************************************************************************************************
ok: [info-service]

TASK [web_app : Create application directory] ************************************************************************************************************************
changed: [info-service]

TASK [web_app : Deploy application container] ************************************************************************************************************************
changed: [info-service]

TASK [web_app : Wait for application to start] ***********************************************************************************************************************
ok: [info-service]

TASK [web_app : Check application health endpoint] *******************************************************************************************************************
ok: [info-service]

TASK [web_app : Display health check result] *************************************************************************************************************************
ok: [info-service] => {
    "msg": "Application is healthy! Response: {'status': 'healthy', 'timestamp': '2026-02-10T16:23:37.762844+00:00', 'uptime_seconds': 12}"
}

TASK [Show running containers] ***************************************************************************************************************************************
changed: [info-service]

TASK [Display container status] **************************************************************************************************************************************
ok: [info-service] => {
    "msg": [
        "NAMES          IMAGE                              STATUS          PORTS",
        "info-service   sayfetik/info-service:latest   Up 16 seconds   0.0.0.0:8000->5000/tcp"
    ]
}

PLAY RECAP ***********************************************************************************************************************************************************
info-service               : ok=39   changed=5    unreachable=0    failed=0    skipped=5    rescued=0    ignored=0 
```

### Output of Scenario 4

```bash
ansible-playbook playbooks/deploy.yml --tags web_app_wipe
```

```bash
PLAY [Deploy application] ********************************************************************************************************************************************

TASK [Gathering Facts] ***********************************************************************************************************************************************
ok: [info-service]

TASK [common : Log package installation completion] ******************************************************************************************************************
ok: [info-service] => {
    "msg": "Package installation block completed"
}

TASK [common : Create completion timestamp] **************************************************************************************************************************
changed: [info-service]

TASK [common : User management completed] ****************************************************************************************************************************
ok: [info-service] => {
    "msg": "User management block finished"
}

TASK [web_app : Include wipe tasks] **********************************************************************************************************************************
included: /Users/sayfetik/DevOps-Core-Course/ansible/roles/web_app/tasks/wipe.yml for info-service

TASK [web_app : Wipe web application - confirmation check] ***********************************************************************************************************
ok: [info-service] => {
    "msg": "===========================================\nWIPE OPERATION INITIATED\n\nThis will remove:\n1. Docker containers for info-service\n2. Docker volumes for info-service\n3. Application directory: /opt/info-service\n4. Docker images (optional)\n\nWipe variable: False\nTag: web_app_wipe\n===========================================\n"
}

TASK [web_app : Check if Docker Compose project exists] **************************************************************************************************************
ok: [info-service]

TASK [web_app : Stop and remove Docker Compose project] **************************************************************************************************************
skipping: [info-service]

TASK [web_app : Remove application directory] ************************************************************************************************************************
changed: [info-service]

TASK [web_app : Remove Docker images] ********************************************************************************************************************************
skipping: [info-service]

TASK [web_app : Verify wipe completion] ******************************************************************************************************************************
ok: [info-service]

TASK [web_app : Display wipe results] ********************************************************************************************************************************
ok: [info-service] => {
    "msg": "===========================================\nWIPE OPERATION COMPLETED\n\nCompose file existed: False\nDirectory removed: True\n\nRemaining containers:\ne765a2ecee53   sayfetik/info-service:latest   \"python app.py\"   4 minutes ago   Up 4 minutes   0.0.0.0:8000->5000/tcp   info-service\n\nApplication directory exists: False\n===========================================\n"
}

PLAY RECAP ***********************************************************************************************************************************************************
info-service               : ok=10   changed=2    unreachable=0    failed=0    skipped=2    rescued=0    ignored=0
```

### Application running after clean reinstall

```bash
curl http://localhost:8000/health
```

```bash
{"status":"healthy","timestamp":"2026-02-10T16:28:44.844433+00:00","uptime_seconds":319}
```

### Research

- Use both variable AND tag (Double safety mechanism)

**Safety and flexibility:** Requiring both a control variable (`web_app_wipe`) and an execution tag (`web_app_wipe`) creates two independent safeguards. The variable enables the wipe logic, while the tag allows task execution — both must be set to actually perform a wipe, which greatly reduces the chance of accidental removals during normal runs.

- Difference between never tag and this approach

**`never` tag:** A task tagged `never` will not run unless explicitly requested with `--tags never`.  
**This approach:** The wipe runs only when `web_app_wipe=true` is provided and the `web_app_wipe` tag is used. That lets operators trigger a wipe from the command line (`-e "web_app_wipe=true"` together with the tag) without editing playbooks, while keeping the action well guarded.

- Wipe logic come BEFORE deployment in main.yml (Clean reinstall scenario)

**Sequence of operations:** Running wipe before deployment guarantees the environment is cleaned prior to installation, enabling a true clean reinstall. If the wipe were executed after deployment it could remove the freshly deployed application, so the order (delete old → install new) matters.

- Clean reinstallation vs. rolling update

**Clean reinstallation:**
- Used for major version changes that require a fresh state
- Useful to fix a corrupted deployment state
- Appropriate when changing application structure
- Helpful for testing from a known clean baseline

**Rolling update:**
- Suitable for small updates with minimal downtime
- Best for hotfixes in production
- Preserves application state and data
- Often implemented with blue/green or canary strategies

- Extend wipe Docker images and volumes

**Add tasks:**
```bash
- name: Clean unused Docker resources
    shell: docker system prune -af
```



## Task 4: CI/CD (3 pts)

### Ansible lint passing

```bash
ansible-lint playbooks/*.yml
```

```bash
Passed: 0 failure(s), 0 warning(s) in 3 files processed of 3 encountered. Last profile that met the validation criteria was 'production'.
```

### App responding

```bash
ansible-playbook ansible/playbooks/deploy.yml\
            --vault-password-file /tmp/vault_pass \
```

```bash
ok: [info-service] => {
    "msg": [
        "NAMES          IMAGE                              STATUS          PORTS",
        "info-service   sayfetik/info-service:latest   Up 16 seconds   0.0.0.0:8000->5000/tcp"
    ]
}
```

### What are the security implications of storing SSH keys in GitHub Secrets?

- Secrets are encrypted while stored, but they are exposed to any workflow that uses them at runtime
- There is no built-in automatic rotation for secrets; you must rotate keys yourself
- If a GitHub token or account is compromised, attackers may access stored secrets
- Auditability is limited compared to dedicated secret managers
- Secrets can leak if accidentally printed in logs or output

### How would you implement a staging → production deployment pipeline?

1. Automatically deploy builds to a staging environment on merges to the main branch
2. Execute integration and smoke tests against the staging deployment
3. Require a manual approval step before promoting to production
4. Promote the exact same artifacts to production to ensure parity
5. Run health checks and verification after production deployment
6. Trigger an automated rollback when predefined failure thresholds are exceeded

### What would you add to make rollbacks possible?

- Keep versioned, immutable artifacts for easy re-deployment
- Use blue/green or canary deployments with traffic switching to revert quickly
- Ensure database migrations are backward compatible or include rollback scripts
- Use feature flags to disable problematic features without redeploying
- Make Ansible playbooks idempotent and capable of restoring prior known-good state
- Tag releases in Git so a specific deployable state can be referenced

### How does self-hosted runner improve security compared to GitHub-hosted?

- You avoid exposing your infrastructure to GitHub's public runner IP ranges
- Sensitive keys and certificates can remain on your network and never leave it
- Easier to enforce internal compliance and access controls
- Execution happens in an isolated environment you control
- Eliminates multi-tenant risks present on hosted runners
- Provides richer audit and logging under your control

## Task 5: Documentation
[This file serves as documentation]


## Multi-App Deployment

## Bonus Part 1: Multi-App (1.5 pts)

Multi-app deployment uses a single Ansible role deployed multiple times with different variables. This follows the DRY principle and provides:

- **Single source of truth** for deployment logic
- **Consistent configuration** across applications
- **Reduced maintenance** overhead
- **Tested and proven** deployment patterns

### Variable file strategy

```bash
vars/
├── app_python.yml # Python-specific configuration
└── app_bonus.yml # Go-specific configuration
```

### Role reusability benefits

```yaml
# Single role, multiple invocations
- include_role:
    name: web_app
  vars:
    app_name: devops-python  # Different each time
    docker_image: python-app # Different each time
    app_port: 8000          # Different each time
```

### Port conflict resolution

| Application | Host Port | Container Port | Purpose |
|------------|-----------|----------------|---------|
| Python App | 8000 | 8000 | Main Python service |
| Go App | 8001 | 8080 | High-performance Go service |

### Independent vs. combined deployment trade-offs

| Approach | Pros | Cons | Best For |
|------------|-----------|----------------|---------|
| Independent | Granular control, Faster single app updates, clear responsibility | More commands, potential drift| Development, testing |
| Combined | One command, consistent state, simple orchestration | Slower, all or nothing | Production, staging |



## Bonus Part 2: Multi-App CI/CD (1 pt)

### Multi-app CI/CD architecture

```bash
┌─────────────────┐     ┌──────────────────┐
│  Python App     │     │  Go App          │
│  Workflow       │     │  Workflow        │
├─────────────────┤     ├──────────────────┤
│ • deploy-python │     │ • deploy-bonus   │
│ • vars_python   │     │ • vars_bonus     │
│ • port: 8000    │     │ • port: 8001     │
└────────┬────────┘     └────────┬─────────┘
         │                       │
         └───────────┬───────────┘
                     │
            ┌────────▼────────┐
            │  Target VM      │
            │  • 2 containers │
            │  • 2 ports      │
            └─────────────────┘
```

### Workflow triggering logic

```bash
on:
  push:
    paths:
      - 'ansible/vars/app_python.yml'
      - 'ansible/playbooks/deploy_python.yml'
      - 'ansible/roles/web_app/**'
```

```bash
on:
  push:
    paths:
      - 'ansible/vars/app_bonus.yml'
      - 'ansible/playbooks/deploy_bonus.yml'
      - 'ansible/roles/web_app/**'
```

### Path filter strategy

```yaml
# Prevent unnecessary runs
paths-ignore:
  - '**.md'           # Documentation
  - 'docs/**'         # Docs directory
  - '.gitignore'      # Git files
  - 'LICENSE'         # License file
```

### Matrix vs separate workflows comparison

| Aspect             | Separate Workflows        | Matrix Strategy        |
|--------------------|--------------------------|------------------------|
| Files              | 2 workflow files         | 1 workflow file        |
| Trigger Control    | Granular per app       | All or nothing      |
| Parallel Execution | Native                 | Matrix strategy     |
| Readability        | Clear purpose          | More complex        |
| Maintenance        | Two files to update    | Single source       |
| Failure Isolation  | One app fails, other works | Matrix may fail partially |
| Debugging          | Simple logs            | Nested logs         |


### Evidence of independent deployments

1. Python-Only Change
    - Python workflow: RUNNING
    - Go workflow: SKIPPED (path filter)

2. Go-Only Change
    - Python workflow: SKIPPED
    - Go workflow: RUNNING

3. Shared Role Change
    - Python workflow: RUNNING
    - Go workflow: RUNNING