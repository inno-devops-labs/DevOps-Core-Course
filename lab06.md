✔ ~/IU/DevOps/DevOps-Core-Course/ansible [lab06 L|✚ 3…1]
23:38 $ ansible-playbook playbooks/provision.yml --list-tags

playbook: playbooks/provision.yml

  play #1 (webservers): Provision web servers   TAGS: []
      TASK TAGS: [common, docker, docker_config, docker_install, packages, users]
✔ ~/IU/DevOps/DevOps-Core-Course/ansible [lab06 L|✚ 4…1]
23:41 $ ansible-playbook playbooks/provision.yml --tags "docker"

PLAY [Provision web servers] **********************************************************************************

TASK [Gathering Facts] ****************************************************************************************
ok: [lab05-vm]

TASK [docker : Install Docker apt prerequisites] **************************************************************
ok: [lab05-vm]

TASK [docker : Create Docker apt keyring directory] ***********************************************************
ok: [lab05-vm]

TASK [docker : Add Docker GPG key] ****************************************************************************
changed: [lab05-vm]

TASK [docker : Add Docker apt repository] *********************************************************************
changed: [lab05-vm]

TASK [docker : Refresh apt cache after repository change] *****************************************************
changed: [lab05-vm]

TASK [docker : Install Docker engine packages] ****************************************************************
changed: [lab05-vm]

TASK [docker : Ensure Docker service is enabled and running] **************************************************
ok: [lab05-vm]

TASK [docker : Add users to docker group] *********************************************************************
changed: [lab05-vm] => (item=ubuntu)

TASK [docker : Install python Docker bindings] ****************************************************************
changed: [lab05-vm]

RUNNING HANDLER [docker : Restart docker] *********************************************************************
changed: [lab05-vm]

PLAY RECAP ****************************************************************************************************
lab05-vm                   : ok=11   changed=7    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0

✔ ~/IU/DevOps/DevOps-Core-Course/ansible [lab06 L|✚ 4…2]
23:43 $ ansible-playbook playbooks/provision.yml --skip-tags "common"

PLAY [Provision web servers] **********************************************************************************

TASK [Gathering Facts] ****************************************************************************************
ok: [lab05-vm]

TASK [docker : Install Docker apt prerequisites] **************************************************************
ok: [lab05-vm]

TASK [docker : Create Docker apt keyring directory] ***********************************************************
ok: [lab05-vm]

TASK [docker : Add Docker GPG key] ****************************************************************************
ok: [lab05-vm]

TASK [docker : Add Docker apt repository] *********************************************************************
ok: [lab05-vm]

TASK [docker : Refresh apt cache after repository change] *****************************************************
skipping: [lab05-vm]

TASK [docker : Install Docker engine packages] ****************************************************************
ok: [lab05-vm]

TASK [docker : Ensure Docker service is enabled and running] **************************************************
ok: [lab05-vm]

TASK [docker : Add users to docker group] *********************************************************************
ok: [lab05-vm] => (item=ubuntu)

TASK [docker : Install python Docker bindings] ****************************************************************
ok: [lab05-vm]

PLAY RECAP ****************************************************************************************************
lab05-vm                   : ok=9    changed=0    unreachable=0    failed=0    skipped=1    rescued=0    ignored=0

✔ ~/IU/DevOps/DevOps-Core-Course/ansible [lab06 L|✚ 4…2]
23:45 $ ansible-playbook playbooks/provision.yml --tags "packages"

PLAY [Provision web servers] **********************************************************************************

TASK [Gathering Facts] ****************************************************************************************
ok: [lab05-vm]

TASK [common : Update apt cache] ******************************************************************************
ok: [lab05-vm]

TASK [common : Install common packages] ***********************************************************************
changed: [lab05-vm]

TASK [common : Log completion of common package block] ********************************************************
changed: [lab05-vm]

PLAY RECAP ****************************************************************************************************
lab05-vm                   : ok=4    changed=2    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0

✔ ~/IU/DevOps/DevOps-Core-Course/ansible [lab06 L|✚ 4…2]
23:46 $ ansible-playbook playbooks/provision.yml --tags "docker_install" --check

PLAY [Provision web servers] **********************************************************************************

TASK [Gathering Facts] ****************************************************************************************
ok: [lab05-vm]

TASK [docker : Install Docker apt prerequisites] **************************************************************
ok: [lab05-vm]

TASK [docker : Create Docker apt keyring directory] ***********************************************************
ok: [lab05-vm]

TASK [docker : Add Docker GPG key] ****************************************************************************
ok: [lab05-vm]

TASK [docker : Add Docker apt repository] *********************************************************************
ok: [lab05-vm]

TASK [docker : Refresh apt cache after repository change] *****************************************************
skipping: [lab05-vm]

TASK [docker : Install Docker engine packages] ****************************************************************
ok: [lab05-vm]

TASK [docker : Ensure Docker service is enabled and running] **************************************************
ok: [lab05-vm]

PLAY RECAP ****************************************************************************************************
lab05-vm                   : ok=7    changed=0    unreachable=0    failed=0    skipped=1    rescued=0    ignored=0

(.venv) ✘-2 ~/IU/DevOps/DevOps-Core-Course/ansible [lab06 L|● 3✚ 6…3]
00:21 $ ansible-playbook playbooks/deploy.yml

PLAY [Deploy application] *************************************************************************************

TASK [Gathering Facts] ****************************************************************************************
ok: [lab05-vm]

TASK [docker : Install Docker apt prerequisites] **************************************************************
ok: [lab05-vm]

TASK [docker : Create Docker apt keyring directory] ***********************************************************
ok: [lab05-vm]

TASK [docker : Add Docker GPG key] ****************************************************************************
ok: [lab05-vm]

TASK [docker : Add Docker apt repository] *********************************************************************
ok: [lab05-vm]

TASK [docker : Refresh apt cache after repository change] *****************************************************
skipping: [lab05-vm]

TASK [docker : Install Docker engine packages] ****************************************************************
ok: [lab05-vm]

TASK [docker : Ensure Docker service is enabled and running] **************************************************
ok: [lab05-vm]

TASK [docker : Add users to docker group] *********************************************************************
ok: [lab05-vm] => (item=ubuntu)

TASK [docker : Install python Docker bindings] ****************************************************************
ok: [lab05-vm]

TASK [web_app : Include wipe logic tasks] *********************************************************************
included: /home/eugene/IU/DevOps/DevOps-Core-Course/ansible/roles/web_app/tasks/wipe.yml for lab05-vm

TASK [web_app : Stop and remove compose stack] ****************************************************************
skipping: [lab05-vm]

TASK [web_app : Remove rendered docker-compose.yml] ***********************************************************
skipping: [lab05-vm]

TASK [web_app : Remove compose project directory] *************************************************************
skipping: [lab05-vm]

TASK [web_app : Report wipe completion] ***********************************************************************
skipping: [lab05-vm]

TASK [web_app : Create compose project directory] *************************************************************
ok: [lab05-vm]

TASK [web_app : Render docker-compose.yml from template] ******************************************************
changed: [lab05-vm]

TASK [web_app : Ensure Docker Hub login for pulling private image (if needed)] ********************************
ok: [lab05-vm]

TASK [web_app : Deploy stack with docker compose v2] **********************************************************
[WARNING]: Cannot parse event from line: 'time="2026-03-04T21:26:03Z" level=warning msg="/opt/devops-
info/docker-compose.yml: the attribute `version` is obsolete, it will be ignored, please remove it to avoid
potential confusion"'. Please report this at https://github.com/ansible-
collections/community.docker/issues/new?assignees=&labels=&projects=&template=bug_report.md
changed: [lab05-vm]

TASK [web_app : Wait for app TCP port] ************************************************************************
ok: [lab05-vm]

TASK [web_app : Verify health endpoint] ***********************************************************************
ok: [lab05-vm]

PLAY RECAP ****************************************************************************************************
lab05-vm                   : ok=16   changed=2    unreachable=0    failed=0    skipped=5    rescued=0    ignored=0

(.venv) ✔ ~/IU/DevOps/DevOps-Core-Course/ansible [lab06 L|● 3✚ 6…3]
00:28 $ curl http://51.250.89.15:5000/health
{"status":"healthy","timestamp":"2026-03-04T21:28:55.824186+00:00","uptime_seconds":160}

(.venv) ✔ ~/IU/DevOps/DevOps-Core-Course/ansible [lab06 L|✔]
19:20 $ ansible-playbook playbooks/deploy.yml -e "web_app_wipe=true" --tags web_app_wipe

PLAY [Deploy application] *************************************************************************************

TASK [Gathering Facts] ****************************************************************************************
ok: [lab05-vm]

TASK [web_app : Include wipe logic tasks] *********************************************************************
included: /home/eugene/IU/DevOps/DevOps-Core-Course/ansible/roles/web_app/tasks/wipe.yml for lab05-vm

TASK [web_app : Stop and remove compose stack] ****************************************************************
[WARNING]: Cannot parse event from line: 'time="2026-03-05T16:41:10Z" level=warning msg="/opt/devops-
info/docker-compose.yml: the attribute `version` is obsolete, it will be ignored, please remove it to avoid
potential confusion"'. Please report this at https://github.com/ansible-
collections/community.docker/issues/new?assignees=&labels=&projects=&template=bug_report.md
changed: [lab05-vm]

TASK [web_app : Remove rendered docker-compose.yml] ***********************************************************
changed: [lab05-vm]

TASK [web_app : Remove compose project directory] *************************************************************
changed: [lab05-vm]

TASK [web_app : Report wipe completion] ***********************************************************************
ok: [lab05-vm] => {
    "msg": "Wipe completed for app devops-info"
}

PLAY RECAP ****************************************************************************************************
lab05-vm                   : ok=6    changed=3    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0

(.venv) ✔ ~/IU/DevOps/DevOps-Core-Course/ansible [lab06 L|✔]
19:41 $ ansible-playbook playbooks/deploy.yml -e "web_app_wipe=true"

PLAY [Deploy application] *************************************************************************************

TASK [Gathering Facts] ****************************************************************************************
ok: [lab05-vm]

TASK [docker : Install Docker apt prerequisites] **************************************************************
ok: [lab05-vm]

TASK [docker : Create Docker apt keyring directory] ***********************************************************
ok: [lab05-vm]

TASK [docker : Add Docker GPG key] ****************************************************************************
ok: [lab05-vm]

TASK [docker : Add Docker apt repository] *********************************************************************
ok: [lab05-vm]

TASK [docker : Refresh apt cache after repository change] *****************************************************
skipping: [lab05-vm]

TASK [docker : Install Docker engine packages] ****************************************************************
ok: [lab05-vm]

TASK [docker : Ensure Docker service is enabled and running] **************************************************
ok: [lab05-vm]

TASK [docker : Add users to docker group] *********************************************************************
ok: [lab05-vm] => (item=ubuntu)

TASK [docker : Install python Docker bindings] ****************************************************************
ok: [lab05-vm]

TASK [web_app : Include wipe logic tasks] *********************************************************************
included: /home/eugene/IU/DevOps/DevOps-Core-Course/ansible/roles/web_app/tasks/wipe.yml for lab05-vm

TASK [web_app : Stop and remove compose stack] ****************************************************************
fatal: [lab05-vm]: FAILED! => {"changed": false, "msg": "\"/opt/devops-info\" is not a directory"}
...ignoring

TASK [web_app : Remove rendered docker-compose.yml] ***********************************************************
ok: [lab05-vm]

TASK [web_app : Remove compose project directory] *************************************************************
ok: [lab05-vm]

TASK [web_app : Report wipe completion] ***********************************************************************
ok: [lab05-vm] => {
    "msg": "Wipe completed for app devops-info"
}

TASK [web_app : Create compose project directory] *************************************************************
changed: [lab05-vm]

TASK [web_app : Render docker-compose.yml from template] ******************************************************
changed: [lab05-vm]

TASK [web_app : Ensure Docker Hub login for pulling private image (if needed)] ********************************
ok: [lab05-vm]

TASK [web_app : Deploy stack with docker compose v2] **********************************************************
[WARNING]: Cannot parse event from line: 'time="2026-03-05T16:42:57Z" level=warning msg="/opt/devops-
info/docker-compose.yml: the attribute `version` is obsolete, it will be ignored, please remove it to avoid
potential confusion"'. Please report this at https://github.com/ansible-
collections/community.docker/issues/new?assignees=&labels=&projects=&template=bug_report.md
changed: [lab05-vm]

TASK [web_app : Wait for app TCP port] ************************************************************************
ok: [lab05-vm]

TASK [web_app : Verify health endpoint] ***********************************************************************
ok: [lab05-vm]

PLAY RECAP ****************************************************************************************************
lab05-vm                   : ok=20   changed=3    unreachable=0    failed=0    skipped=1    rescued=0    ignored=1
