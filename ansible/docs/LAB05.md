# Zavadskii Peter lab05 

### 1. Architecture Overview

 - Ansible version used

```bash
abraham_barrett@Abrahams-MacBook-Air ansible % ansible --version
ansible [core 2.20.3]
```

 - Target VM OS and version
 
    - I have reused terraform yamls to create VM on ubuntu 24.04 using Yandex cloud.
 
 - Role structure diagram or explanation
 
    - ```ansible/``` — main project directory
    - ```group_vars/all.yml``` — global variables, including those encrypted with Ansible Vault
    - ```inventory/hosts.ini``` — static inventory file containing the webservers group
    - ```playbooks/deploy.yml``` — playbook for deploying the application (app_deploy role)
    - ```playbooks/provision.yml``` — playbook for initial server setup (common + docker roles)
    - ```roles/app_deploy``` — manages containerized application deployment
    - ```roles/docker``` — installs Docker and the Python SDK required for Ansible modules
    - ```roles/common``` — handles basic OS configuration (apt updates, package installation, timezone settings)
 
 - Why roles instead of monolithic playbooks?
    - Roles allow you to organize reusable code, maintain a clean structure, and keep responsibilities separate. This approach keeps individual playbooks compact while making roles simpler to test and update.


### 2. Roles Documentation

There are several roles: 
- app_deploy (application deployment, docker auth, pulling images)
- common (basic system configuration related to packages installation and etc.)
- docker (docker installation, adding user to a docker group, docker service starting) 

### 3. Idempotency Demonstration

```bash
abraham_barrett@Abrahams-MacBook-Air ansible % ansible-playbook playbooks/provision.yml --ask-vault-pass -i inventory/hosts.ini\ 
Vault password: 

PLAY [Provision web servers] *************************************************************************************************************************************

TASK [Gathering Facts] *******************************************************************************************************************************************
ok: [abraham-vm]

TASK [common : Update apt cache] *********************************************************************************************************************************
ok: [abraham-vm]

TASK [common : Install common packages] **************************************************************************************************************************
ok: [abraham-vm]

TASK [docker : Install dependencies for Docker repo] *************************************************************************************************************
ok: [abraham-vm]

TASK [docker : Add Docker GPG key] *******************************************************************************************************************************
ok: [abraham-vm]

TASK [docker : Add Docker APT repository] ************************************************************************************************************************
[WARNING]: Deprecation warnings can be disabled by setting `deprecation_warnings=False` in ansible.cfg.
[DEPRECATION WARNING]: INJECT_FACTS_AS_VARS default to `True` is deprecated, top-level facts will not be auto injected after the change. This feature will be removed from ansible-core version 2.24.
Origin: /Users/abraham_barrett/Documents/devops/DevOps-Core-Course/ansible/roles/docker/defaults/main.yml:10:18

 8
 9 docker_user: "{{ ansible_user | default('ubuntu') }}"
10 docker_apt_repo: "deb [arch=amd64] https://download.docker.com/linux/ubuntu {{ ansible_distribution_release }} sta...
                    ^ column 18

Use `ansible_facts["fact_name"]` (no `ansible_` prefix) instead.

changed: [abraham-vm]

TASK [docker : Install Docker packages] **************************************************************************************************************************
ok: [abraham-vm]

TASK [docker : Ensure Docker service is running and enabled] *****************************************************************************************************
ok: [abraham-vm]

TASK [docker : Add user to docker group] *************************************************************************************************************************
ok: [abraham-vm]

TASK [docker : Install python3-docker (for Ansible docker modules)] **********************************************************************************************
changed: [abraham-vm]

PLAY RECAP *******************************************************************************************************************************************************
abraham-vm                 : ok=10   changed=2    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0   

abraham_barrett@Abrahams-MacBook-Air ansible % ansible-playbook playbooks/provision.yml --ask-vault-pass -i inventory/hosts.ini\ 
Vault password: 

PLAY [Provision web servers] *************************************************************************************************************************************

TASK [Gathering Facts] *******************************************************************************************************************************************
ok: [abraham-vm]

TASK [common : Update apt cache] *********************************************************************************************************************************
ok: [abraham-vm]

TASK [common : Install common packages] **************************************************************************************************************************
ok: [abraham-vm]

TASK [docker : Install dependencies for Docker repo] *************************************************************************************************************
ok: [abraham-vm]

TASK [docker : Add Docker GPG key] *******************************************************************************************************************************
ok: [abraham-vm]

TASK [docker : Add Docker APT repository] ************************************************************************************************************************
[WARNING]: Deprecation warnings can be disabled by setting `deprecation_warnings=False` in ansible.cfg.
[DEPRECATION WARNING]: INJECT_FACTS_AS_VARS default to `True` is deprecated, top-level facts will not be auto injected after the change. This feature will be removed from ansible-core version 2.24.
Origin: /Users/abraham_barrett/Documents/devops/DevOps-Core-Course/ansible/roles/docker/defaults/main.yml:10:18

 8
 9 docker_user: "{{ ansible_user | default('ubuntu') }}"
10 docker_apt_repo: "deb [arch=amd64] https://download.docker.com/linux/ubuntu {{ ansible_distribution_release }} sta...
                    ^ column 18

Use `ansible_facts["fact_name"]` (no `ansible_` prefix) instead.

ok: [abraham-vm]

TASK [docker : Install Docker packages] **************************************************************************************************************************
ok: [abraham-vm]

TASK [docker : Ensure Docker service is running and enabled] *****************************************************************************************************
ok: [abraham-vm]

TASK [docker : Add user to docker group] *************************************************************************************************************************
ok: [abraham-vm]

TASK [docker : Install python3-docker (for Ansible docker modules)] **********************************************************************************************
ok: [abraham-vm]

PLAY RECAP *******************************************************************************************************************************************************
abraham-vm                 : ok=10   changed=0    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0   

abraham_barrett@Abrahams-MacBook-Air ansible % 
```

#### Analysis

- **What changed first time?** All the packages were installed, docker was started.
- **What didn't change second time?** All tasks reported ok, since no modifications were made.

#### Explanation: What makes your roles idempotent?
The implementation relies on declarative modules that enforce a target system state rather than executing procedural commands. For example, ```apt``` uses ```state: present``` to ensure packages are installed, ```service``` applies ```state: started``` to verify services are running, and ```file``` sets ```state: directory``` to confirm paths exist. When these tasks run again, they simply verify the current state matches the desired one and take no action if it already does.

### 4. Ansible Vault Usage

For secure credentials storing I am using ansible vault.

It manages all the secrets by several ways. To my mind, I typically use flag ```--ask-vault-pass``` 

This is an encrypted file 
```bash
$ANSIBLE_VAULT;1.1;AES256
38333465613265343763613963613837643462326132343534643735386431336434613866663432
3866313165333638356666383664643264663463623666620a656265373261373464333864633133
30383938653633363466323331323333386339353639396638646430333963653635636633323933
6431336339333231370a636537336538313964636438636463323633333134616535323037386134
63343135333137313535303761623266323330306330386433633163643735623430346664386464
37363164363663353361663131653839623261643662613234336362613766613739646532376134
37353862316533313333303366636237383764393136653566303731353135373138386130356362
31336362666263373536306633373766366664626231663438663233643665613533613035356230
31346534653035376464303434616137343865316336653162303566353662363839363131346537
61386365313164343834386537373231373934373336633037653262323162363530646432643235
63643231663765626130386230643533656166323135373333366163633866333238626535353030
31303065363237396537326534626462313330626164336436643661383561363139376635646661
36373332363763643530396539323465326431366161666265656231616561363433356339306666
36623862323830303935626338316265346664333430666636633061653735383463613966613730
33313861333461366336626665643937393566353136376262656132393535646532656263313465
34643662316435386630653934333332633764336330656233663339346435366461646263306137
32626230383933386635616234653263623830373734343136313661303336623436
```

Ansible vault is important for secure credentials usage, not to share the access to you private servers to everyone, who has an opportunity to execute ansible commands and watch command history, to obtain the password if it was used previously directly in the command line.

#### Vault creation
```bash
abraham_barrett@Abrahams-MacBook-Air ansible % ansible-vault create group_vars/all.yml               
New Vault password: 
Confirm New Vault password: 
[WARNING]: group_vars does not exist, creating...
abraham_barrett@Abrahams-MacBook-Air ansible %
```

### 5. Deployment Verification

#### Application deployment
```bash
abraham_barrett@Abrahams-MacBook-Air ansible % ansible-playbook playbooks/deploy.yml --ask-vault-pass -i inventory/hosts.ini\ 
Vault password: 

PLAY [Deploy application] ****************************************************************************************************************************************

TASK [Gathering Facts] *******************************************************************************************************************************************
ok: [abraham-vm]

TASK [app_deploy : restart app container] ************************************************************************************************************************
changed: [abraham-vm]

PLAY RECAP *******************************************************************************************************************************************************
abraham-vm                 : ok=2    changed=1    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0   

```


#### Checking if my application works 
```bash
abraham_barrett@Abrahams-MacBook-Air ansible % ssh ubuntu@158.160.53.7
Welcome to Ubuntu 24.04.4 LTS (GNU/Linux 6.8.0-100-generic x86_64)

 * Documentation:  https://help.ubuntu.com
 * Management:     https://landscape.canonical.com
 * Support:        https://ubuntu.com/pro

 System information as of Thu Feb 26 18:57:43 UTC 2026

  System load:  0.0               Processes:             105
  Usage of /:   34.9% of 9.04GB   Users logged in:       0
  Memory usage: 32%               IPv4 address for eth0: 10.128.0.5
  Swap usage:   0%

 * Strictly confined Kubernetes makes edge and IoT secure. Learn how MicroK8s
   just raised the bar for easy, resilient and secure K8s cluster deployment.

   https://ubuntu.com/engage/secure-kubernetes-at-the-edge

Expanded Security Maintenance for Applications is not enabled.

17 updates can be applied immediately.
15 of these updates are standard security updates.
To see these additional updates run: apt list --upgradable

Enable ESM Apps to receive additional future security updates.
See https://ubuntu.com/esm or run: sudo pro status


Last login: Thu Feb 26 18:57:43 2026 from 188.130.155.187
ubuntu@fhmecnpbrr42gql1lldp:~$ docker ps 
CONTAINER ID   IMAGE                                          COMMAND           CREATED       STATUS       PORTS      NAMES
a953274639ac   abrahambarrett228/devops-info-service:latest   "python app.py"   3 hours ago   Up 3 hours   5000/tcp   devops-info-service
ubuntu@fhmecnpbrr42gql1lldp:~$ PID=$(docker inspect -f '{{.State.Pid}}' a953274639ac)
ubuntu@fhmecnpbrr42gql1lldp:~$ sudo nsenter -t $PID -n curl http://localhost:5000
{"service":{"name":"devops-info-service","version":"1.0.0","description":"DevOps course info service","framework":"FastAPI"},"system":{"hostname":"a953274639ac","platform_name":"Linux","architecture":"x86_64","python_version":"3.13.12"},"runtime":{"seconds":9974,"human":"2 hours, 46 minutes"},"request":{"client_ip":"127.0.0.1","user_agent":"curl/8.5.0","method":"GET","path":"/"},"endpoints":[{"path":"/","method":"GET","description":"Service information"},{"path":"/health","method":"GET","description":"Health check"}]}ubuntu@fhmecnpbrr42gql1lldp:~$ 
```
### 6. Key Decisions

 - Why use roles instead of plain playbooks? Roles create a well-organized framework that promotes code reuse and clear separation of responsibilities (like common configuration, Docker setup, and application deployment). Once a role is defined, it can be applied consistently across various playbooks and projects.
 - How do roles improve reusability? A single role—for Docker installation or basic system setup—can be incorporated into multiple playbooks and applied to different host groups without copying and pasting tasks.
 - What makes a task idempotent? A task achieves idempotency when it uses modules that declare a target state (such as package present, service started, or directory exists) rather than executing imperative commands. Running the task again leaves the system unchanged if the desired state is already in place.
 - How do handlers improve efficiency? Handlers execute only once at the conclusion of a play when notified by tasks that made actual changes. This prevents redundant operations—like restarting a service multiple times when a single restart would suffice.
 - Why is Ansible Vault necessary? Ansible Vault enables secure storage of sensitive data like passwords and access tokens directly in the repository. This keeps credentials encrypted and prevents accidental exposure through logs or version control history.

### 7. Challenges (Optional)
    -