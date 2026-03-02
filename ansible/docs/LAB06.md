zagur@LAPTOP-JONCQBVT:~/projects/ansible$ ansible-playbook -i inventory/hosts.ini playbooks/deploy.yml --vault-password-file .vault_pass.sh

PLAY [Deploy application] ******************************************************************************

TASK [Gathering Facts] *********************************************************************************
ok: [vm1]

TASK [docker : Docker | Install prerequisites] *********************************************************
ok: [vm1]

TASK [docker : Docker | Ensure /etc/apt/keyrings exists] ***********************************************
ok: [vm1]

TASK [docker : Docker | Add Docker GPG key] ************************************************************
ok: [vm1]

TASK [docker : Docker | Add Docker apt repository] *****************************************************
ok: [vm1]

TASK [docker : Docker | Install Docker packages] *******************************************************
ok: [vm1]

TASK [docker : Docker | Ensure Docker service enabled+running (always)] ********************************
ok: [vm1]

TASK [docker : Docker | Add user to docker group] ******************************************************
ok: [vm1]

TASK [docker : Docker | Install python docker SDK for Ansible modules] *********************************
ok: [vm1]

TASK [../roles/web_app : Include wipe tasks] ***********************************************************
included: /home/zagur/projects/ansible/roles/web_app/tasks/wipe.yml for vm1

TASK [../roles/web_app : Remove old container by name if exists] ***************************************
skipping: [vm1]

TASK [../roles/web_app : Find containers publishing app_port] ******************************************
skipping: [vm1]

TASK [../roles/web_app : Remove containers publishing app_port (wipe)] *********************************
skipping: [vm1]

TASK [../roles/web_app : Remove old container by name if exists] ***************************************
skipping: [vm1]

TASK [../roles/web_app : Stop and remove compose stack] ************************************************
skipping: [vm1]

TASK [../roles/web_app : Remove compose default network if exists] *************************************
skipping: [vm1]

TASK [../roles/web_app : Remove docker-compose.yml] ****************************************************
skipping: [vm1]

TASK [../roles/web_app : Remove application directory] *************************************************
skipping: [vm1]

TASK [../roles/web_app : Log wipe completion] **********************************************************
skipping: [vm1]

TASK [../roles/web_app : Login to Docker Hub] **********************************************************
changed: [vm1]

TASK [../roles/web_app : Ensure compose project directory exists] **************************************
ok: [vm1]

TASK [../roles/web_app : Template docker-compose.yml] **************************************************
ok: [vm1]

TASK [../roles/web_app : Deploy via Docker Compose v2] *************************************************
changed: [vm1]

TASK [../roles/web_app : Give app time to start] *******************************************************
Pausing for 5 seconds
(ctrl+C then 'C' = continue early, ctrl+C then 'A' = abort)
ok: [vm1]

TASK [../roles/web_app : Health check] *****************************************************************
ok: [vm1]

TASK [../roles/web_app : Log deploy completion marker] *************************************************
ok: [vm1]

PLAY RECAP *********************************************************************************************
vm1                        : ok=17   changed=2    unreachable=0    failed=0    skipped=9    rescued=0    ignored=0

zagur@LAPTOP-JONCQBVT:~/projects/ansible$ ansible-playbook -i inventory/hosts.ini playbooks/deploy.yml -e "web_app_wipe=true" --tags web_app_wipe --vault-password-file .vault_pass.sh

PLAY [Deploy application] ******************************************************************************

TASK [Gathering Facts] *********************************************************************************
ok: [vm1]

TASK [../roles/web_app : Include wipe tasks] ***********************************************************
included: /home/zagur/projects/ansible/roles/web_app/tasks/wipe.yml for vm1

TASK [../roles/web_app : Remove old container by name if exists] ***************************************
changed: [vm1]

TASK [../roles/web_app : Find containers publishing app_port] ******************************************
ok: [vm1]

TASK [../roles/web_app : Remove containers publishing app_port (wipe)] *********************************
skipping: [vm1]

TASK [../roles/web_app : Remove old container by name if exists] ***************************************
ok: [vm1]

TASK [../roles/web_app : Stop and remove compose stack] ************************************************
changed: [vm1]

TASK [../roles/web_app : Remove compose default network if exists] *************************************
ok: [vm1]

TASK [../roles/web_app : Remove docker-compose.yml] ****************************************************
changed: [vm1]

TASK [../roles/web_app : Remove application directory] *************************************************
changed: [vm1]

TASK [../roles/web_app : Log wipe completion] **********************************************************
ok: [vm1] => {
    "msg": "Application devops-info-service wiped successfully"
}

PLAY RECAP *********************************************************************************************
vm1                        : ok=10   changed=4    unreachable=0    failed=0    skipped=1    rescued=0    ignored=0

zagur@LAPTOP-JONCQBVT:~/projects/ansible$ 
zagur@LAPTOP-JONCQBVT:~/projects/ansible$ ansible-playbook -i inventory/hosts.ini playbooks/deploy.yml -e "web_app_wipe=true" --vault-password-file .vault_pass.sh

PLAY [Deploy application] ******************************************************************************

TASK [Gathering Facts] *********************************************************************************
ok: [vm1]

TASK [docker : Docker | Install prerequisites] *********************************************************
ok: [vm1]

TASK [docker : Docker | Ensure /etc/apt/keyrings exists] ***********************************************
ok: [vm1]

TASK [docker : Docker | Add Docker GPG key] ************************************************************
ok: [vm1]

TASK [docker : Docker | Add Docker apt repository] *****************************************************
ok: [vm1]

TASK [docker : Docker | Install Docker packages] *******************************************************
ok: [vm1]

TASK [docker : Docker | Ensure Docker service enabled+running (always)] ********************************
ok: [vm1]

TASK [docker : Docker | Add user to docker group] ******************************************************
ok: [vm1]

TASK [docker : Docker | Install python docker SDK for Ansible modules] *********************************
ok: [vm1]

TASK [../roles/web_app : Include wipe tasks] ***********************************************************
included: /home/zagur/projects/ansible/roles/web_app/tasks/wipe.yml for vm1

TASK [../roles/web_app : Remove old container by name if exists] ***************************************
ok: [vm1]

TASK [../roles/web_app : Find containers publishing app_port] ******************************************
ok: [vm1]

TASK [../roles/web_app : Remove containers publishing app_port (wipe)] *********************************
skipping: [vm1]

TASK [../roles/web_app : Remove old container by name if exists] ***************************************
ok: [vm1]

TASK [../roles/web_app : Stop and remove compose stack] ************************************************
fatal: [vm1]: FAILED! => {"changed": false, "msg": "\"/opt/devops-info-service\" is not a directory"}
...ignoring

TASK [../roles/web_app : Remove compose default network if exists] *************************************
ok: [vm1]

TASK [../roles/web_app : Remove docker-compose.yml] ****************************************************
ok: [vm1]

TASK [../roles/web_app : Remove application directory] *************************************************
ok: [vm1]

TASK [../roles/web_app : Log wipe completion] **********************************************************
ok: [vm1] => {
    "msg": "Application devops-info-service wiped successfully"
}

TASK [../roles/web_app : Login to Docker Hub] **********************************************************
changed: [vm1]

TASK [../roles/web_app : Ensure compose project directory exists] **************************************
changed: [vm1]

TASK [../roles/web_app : Template docker-compose.yml] **************************************************
changed: [vm1]

TASK [../roles/web_app : Deploy via Docker Compose v2] *************************************************
changed: [vm1]

TASK [../roles/web_app : Give app time to start] *******************************************************
Pausing for 5 seconds
(ctrl+C then 'C' = continue early, ctrl+C then 'A' = abort)
ok: [vm1]

TASK [../roles/web_app : Health check] *****************************************************************
ok: [vm1]

TASK [../roles/web_app : Log deploy completion marker] *************************************************
ok: [vm1]

PLAY RECAP *********************************************************************************************
vm1                        : ok=25   changed=4    unreachable=0    failed=0    skipped=1    rescued=0   
 ignored=1   

zagur@LAPTOP-JONCQBVT:~/projects/ansible$ ansible-playbook -i inventory/hosts.ini playbooks/deploy.yml -
-tags web_app_wipe --vault-password-file .vault_pass.sh

PLAY [Deploy application] ******************************************************************************

TASK [Gathering Facts] *********************************************************************************
ok: [vm1]

TASK [../roles/web_app : Include wipe tasks] ***********************************************************
included: /home/zagur/projects/ansible/roles/web_app/tasks/wipe.yml for vm1

TASK [../roles/web_app : Remove old container by name if exists] ***************************************
skipping: [vm1]

TASK [../roles/web_app : Find containers publishing app_port] ******************************************
skipping: [vm1]

TASK [../roles/web_app : Remove containers publishing app_port (wipe)] *********************************
skipping: [vm1]

TASK [../roles/web_app : Remove old container by name if exists] ***************************************
skipping: [vm1]

TASK [../roles/web_app : Stop and remove compose stack] ************************************************
skipping: [vm1]

TASK [../roles/web_app : Remove compose default network if exists] *************************************
skipping: [vm1]

TASK [../roles/web_app : Remove docker-compose.yml] ****************************************************
skipping: [vm1]

TASK [../roles/web_app : Remove application directory] *************************************************
skipping: [vm1]

TASK [../roles/web_app : Log wipe completion] **********************************************************
skipping: [vm1]

PLAY RECAP *********************************************************************************************
vm1                        : ok=2    changed=0    unreachable=0    failed=0    skipped=9    rescued=0    ignored=0
zagur@LAPTOP-JONCQBVT:~/projects/ansible$ ansible-playbook playbooks/provision.yml --list-tags

playbook: playbooks/provision.yml

  play #1 (webservers): Provision web servers   TAGS: []
      TASK TAGS: [common, docker, docker_config, docker_install, packages, users]
zagur@LAPTOP-JONCQBVT:~/projects/ansible$ ansible-playbook playbooks/provision.yml --tags docker

PLAY [Provision web servers] ***************************************************************************

TASK [Gathering Facts] *********************************************************************************
ok: [vm1]

TASK [docker : Install prerequisites] ******************************************************************
ok: [vm1]

TASK [docker : Ensure /etc/apt/keyrings exists] ********************************************************
ok: [vm1]

TASK [docker : Add Docker GPG key] *********************************************************************
ok: [vm1]

TASK [docker : Add Docker repo] ************************************************************************
ok: [vm1]

TASK [docker : Install Docker packages] ****************************************************************
ok: [vm1]

TASK [docker : Ensure Docker service enabled and running] **********************************************
ok: [vm1]

TASK [docker : Add user to docker group] ***************************************************************
ok: [vm1]

TASK [docker : Install python docker SDK for Ansible docker modules] ***********************************
ok: [vm1]

PLAY RECAP *********************************************************************************************
vm1                        : ok=9    changed=0    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0

zagur@LAPTOP-JONCQBVT:~/projects/ansible$ ansible-playbook playbooks/provision.yml --tags docker_install
 
PLAY [Provision web servers] ***************************************************************************

TASK [Gathering Facts] *********************************************************************************
ok: [vm1]

TASK [docker : Install prerequisites] ******************************************************************
ok: [vm1]

TASK [docker : Ensure /etc/apt/keyrings exists] ********************************************************
ok: [vm1]

TASK [docker : Add Docker GPG key] *********************************************************************
ok: [vm1]

TASK [docker : Add Docker repo] ************************************************************************
ok: [vm1]

TASK [docker : Install Docker packages] ****************************************************************
ok: [vm1]

TASK [docker : Ensure Docker service enabled and running] **********************************************
ok: [vm1]

PLAY RECAP *********************************************************************************************
vm1                        : ok=7    changed=0    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0

zagur@LAPTOP-JONCQBVT:~/projects/ansible$ ansible-playbook playbooks/provision.yml --tags packages

PLAY [Provision web servers] ***************************************************************************

TASK [Gathering Facts] *********************************************************************************
ok: [vm1]

TASK [common : Common | Update apt cache] **************************************************************
ok: [vm1]

TASK [common : Common | Install common packages] *******************************************************
ok: [vm1]

TASK [common : Mark common packages done] **************************************************************
ok: [vm1]

PLAY RECAP *********************************************************************************************
vm1                        : ok=4    changed=0    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0

zagur@LAPTOP-JONCQBVT:~/projects/ansible$ ansible-playbook playbooks/provision.yml --skip-tags common

PLAY [Provision web servers] ***************************************************************************

TASK [Gathering Facts] *********************************************************************************
ok: [vm1]

TASK [docker : Install prerequisites] ******************************************************************
ok: [vm1]

TASK [docker : Ensure /etc/apt/keyrings exists] ********************************************************
ok: [vm1]

TASK [docker : Add Docker GPG key] *********************************************************************
ok: [vm1]

TASK [docker : Add Docker repo] ************************************************************************
ok: [vm1]

TASK [docker : Install Docker packages] ****************************************************************
ok: [vm1]

TASK [docker : Ensure Docker service enabled and running] **********************************************
ok: [vm1]

TASK [docker : Add user to docker group] ***************************************************************
ok: [vm1]

TASK [docker : Install python docker SDK for Ansible docker modules] ***********************************
ok: [vm1]

PLAY RECAP *********************************************************************************************
vm1                        : ok=9    changed=0    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0

zagur@LAPTOP-JONCQBVT:~/projects/ansible$ 