# Lab 05 docs
```bash
(.venv) ✔ ~/IU/DevOps/DevOps-Core-Course/ansible [lab05 L|✚ 1…1] 
19:01 $ ansible-playbook playbooks/provision.yml

PLAY [Provision web servers] **********************************************************************************

TASK [Gathering Facts] ****************************************************************************************
ok: [lab05-vm]

TASK [common : Update apt cache] ******************************************************************************
changed: [lab05-vm]

TASK [common : Install common packages] ***********************************************************************
changed: [lab05-vm]

TASK [common : Read current timezone] *************************************************************************
ok: [lab05-vm]

TASK [common : Set system timezone] ***************************************************************************
changed: [lab05-vm]

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
lab05-vm                   : ok=15   changed=10   unreachable=0    failed=0    skipped=0    rescued=0    ignored=0   
```

```bash
(.venv) ✔ ~/IU/DevOps/DevOps-Core-Course/ansible [lab05 L|✚ 1…2] 
19:07 $ ansible-playbook playbooks/provision.yml

PLAY [Provision web servers] **********************************************************************************

TASK [Gathering Facts] ****************************************************************************************
ok: [lab05-vm]

TASK [common : Update apt cache] ******************************************************************************
ok: [lab05-vm]

TASK [common : Install common packages] ***********************************************************************
ok: [lab05-vm]

TASK [common : Read current timezone] *************************************************************************
ok: [lab05-vm]

TASK [common : Set system timezone] ***************************************************************************
skipping: [lab05-vm]

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
lab05-vm                   : ok=12   changed=0    unreachable=0    failed=0    skipped=2    rescued=0    ignored=0   
```

```bash
(.venv) ✔ ~/IU/DevOps/DevOps-Core-Course/ansible [lab05 L|● 18✚ 5] 
19:34 $ ansible-playbook playbooks/deploy.yml

PLAY [Deploy application] *************************************************************************************

TASK [Gathering Facts] ****************************************************************************************
ok: [lab05-vm]

TASK [app_deploy : Validate Docker Hub credentials] ***********************************************************
ok: [lab05-vm] => {
    "changed": false,
    "msg": "All assertions passed"
}

TASK [app_deploy : Log in to Docker Hub] **********************************************************************
ok: [lab05-vm]

TASK [app_deploy : Pull application image] ********************************************************************
ok: [lab05-vm]

TASK [app_deploy : Read current container info] ***************************************************************
ok: [lab05-vm]

TASK [app_deploy : Decide whether container recreation is required] *******************************************
ok: [lab05-vm]

TASK [app_deploy : Stop existing container before recreation] *************************************************
skipping: [lab05-vm]

TASK [app_deploy : Remove existing container before recreation] ***********************************************
skipping: [lab05-vm]

TASK [app_deploy : Ensure application container is running] ***************************************************
ok: [lab05-vm]

TASK [app_deploy : Wait for application port] *****************************************************************
ok: [lab05-vm]

TASK [app_deploy : Verify health endpoint] ********************************************************************
ok: [lab05-vm]

TASK [app_deploy : Verify main endpoint] **********************************************************************
ok: [lab05-vm]

TASK [app_deploy : Trigger app restart handler when explicitly requested] *************************************
skipping: [lab05-vm]

PLAY RECAP ****************************************************************************************************
lab05-vm                   : ok=10   changed=0    unreachable=0    failed=0    skipped=3    rescued=0    ignored=0   
```

```bash
19:35 $ curl http://93.77.191.173:5000/health
{"status":"healthy","timestamp":"2026-02-26T16:36:29.694058+00:00","uptime_seconds":227}
```

```bash
(.venv) ✘-127 ~/IU/DevOps/DevOps-Core-Course/ansible [lab05 L|● 18✚ 6] 
19:37 $ ssh ubuntu@93.77.191.173 
Welcome to Ubuntu 24.04.3 LTS (GNU/Linux 6.8.0-85-generic x86_64)

 * Documentation:  https://help.ubuntu.com
 * Management:     https://landscape.canonical.com
 * Support:        https://ubuntu.com/pro

 System information as of Thu Feb 26 16:37:35 UTC 2026

  System load:  0.0                Processes:             135
  Usage of /:   17.0% of 18.72GB   Users logged in:       0
  Memory usage: 20%                IPv4 address for eth0: 192.168.10.6
  Swap usage:   0%


Expanded Security Maintenance for Applications is not enabled.

66 updates can be applied immediately.
To see these additional updates run: apt list --upgradable

Enable ESM Apps to receive additional future security updates.
See https://ubuntu.com/esm or run: sudo pro status


*** System restart required ***
Last login: Thu Feb 26 16:35:21 2026 from 64.188.75.28
ubuntu@fhmf3hj9e8h3s9qsuucs:~$ docker ps -a
CONTAINER ID   IMAGE                         COMMAND           CREATED          STATUS         PORTS                    NAMES
d586ea30b83e   ebortsov/devops-info:latest   "python app.py"   12 minutes ago   Up 5 minutes   0.0.0.0:5000->5000/tcp   devops-info
```


