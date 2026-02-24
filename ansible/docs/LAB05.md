# Lab 5 report

## Ansible version

For this task used ansible version 2.20.0

## Target VM OS 

Ubuntu 24.04

## Why Roles instead of monolithic playooks?

For better control of all stages of deploing

# Role documentation

## Common 

Base setups. Timezone setup, apt update

## Docker

Installing Docker and all nesseccary packages 

## app_deploy

Pull docker image from docker hub and run it in server

## Ansible vault usage

Vault used for keeping docker hub credentials

## Encrypted file example


```yml
$ANSIBLE_VAULT;1.1;AES256
33656465386534376631303537636462303435396437313631643266363261646330303962353731
6531383261633466366233343561623833333739353762640a353562313334313539356236356232
65313962623935663138393131633035376539323432316233663932666131613435383739306165
3739316264633630370a363431613431623165316265346462353036616130636465383330633766
38303464313738383163333732623166613265303839656662313635653034373336613835343261
34313630363961353837653730656432626631396539636135356332356139376538613133393864
35363065613537643566343466336336363337373262363766666361393834346236616235313262
66396662613934363534323966373238663131306532666233613832336665353838663332386332
36363231386639383438336565393130306565613735393138333832333966666130393735643639
61326630373165396437613938663131376238313333633866663536306234363266386634323165
66386534386233313161666233633737633732366230636561326664643930356364336264653439
62663133376465336662663030393435343937656639663363333961666634306337653764356533
39613362373961356436646239663633613932323239616565366165393032363261366665303839
39363935373034636461653532353331666534376466653234613662376137396138626133353032
30356231616338326137313638386132663438356363343862643730386433313634303763343066
36626237363832366631363538383236393066346135633266636633363763646263353436653164
35636332343132313730666330616238643139666533353333363638363131353533343235303965
39393339623265643732376633373733343766316463666361353361353164646461373164653234
30353632326365633161343831633134353530373931666562316562623063306338386335353663
36316235633061623839

```

# Task 1

## IP address of the server 

Server created in yandex cloud using terraform IP address taken from the `terraform apply` command output and putten in to `inventory/hosts.ini`

## `ansible all -m ping` output

```bash
(.venv) ➜  ansible git:(lab5) ✗ ansible all -m ping
vm1 | SUCCESS => {
    "changed": false,
    "ping": "pong"
}
```

## `ansible webservers -a "uname -a"` output

```bash
(.venv) ➜  ansible git:(lab5) ✗ ansible webservers -a "uname -a" 
vm1 | CHANGED | rc=0 >>
Linux fhmhkilh9qgcge3bqm5n 6.8.0-47-generic #47-Ubuntu SMP PREEMPT_DYNAMIC Fri Sep 27 21:40:26 UTC 2024 x86_64 x86_64 x86_64 GNU/Linux
```

# Task 2 

## `ansible-playbook playbooks/provision.yml` first run

```bash
(venv) ➜  ansible git:(lab5) ✗ ansible-playbook playbooks/provision.yml

PLAY [Provision web server] ************************************************************************

TASK [Gathering Facts] *****************************************************************************
ok: [vm1]

TASK [common : Update apt cache] *******************************************************************
ok: [vm1]

TASK [common : Install essential package] **********************************************************
ok: [vm1]

TASK [common : Set time zone] **********************************************************************
ok: [vm1]

TASK [docker : Install prerequisites for Docker] ***************************************************
ok: [vm1]

TASK [docker : Create directory for keyrings] ******************************************************
ok: [vm1]

TASK [docker : Add Docker GPG key] *****************************************************************
changed: [vm1]

TASK [docker : Add Docker repository] **************************************************************
changed: [vm1]

TASK [docker : Update apt cache after adding docker repo] ******************************************
changed: [vm1]

TASK [docker : Install Docker packages] ************************************************************
changed: [vm1]

TASK [docker : Ensure Docker service is running and enabled] ***************************************
ok: [vm1]

TASK [docker : Add user to docker group] ***********************************************************
changed: [vm1]

TASK [docker : Install python3-docker for Ansible modules] *****************************************
changed: [vm1]

RUNNING HANDLER [docker : Restart Docker] **********************************************************
changed: [vm1]

RUNNING HANDLER [docker : Update apt cache] ********************************************************
changed: [vm1]

PLAY RECAP *****************************************************************************************
vm1                        : ok=15   changed=8    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0   
```

## `ansible-playbook playbooks/provision.yml` second run run

```bash
(venv) ➜  ansible git:(lab5) ✗ ansible-playbook playbooks/provision.yml

PLAY [Provision web server] *******************************************************************************************************************

TASK [Gathering Facts] ************************************************************************************************************************
ok: [vm1]

TASK [common : Update apt cache] **************************************************************************************************************
ok: [vm1]

TASK [common : Install essential package] *****************************************************************************************************
ok: [vm1]

TASK [common : Set time zone] *****************************************************************************************************************
ok: [vm1]

TASK [docker : Install prerequisites for Docker] **********************************************************************************************
ok: [vm1]

TASK [docker : Create directory for keyrings] *************************************************************************************************
ok: [vm1]

TASK [docker : Add Docker GPG key] ************************************************************************************************************
ok: [vm1]

TASK [docker : Add Docker repository] *********************************************************************************************************
ok: [vm1]

TASK [docker : Update apt cache after adding docker repo] *************************************************************************************
changed: [vm1]

TASK [docker : Install Docker packages] *******************************************************************************************************
ok: [vm1]

TASK [docker : Ensure Docker service is running and enabled] **********************************************************************************
ok: [vm1]

TASK [docker : Add user to docker group] ******************************************************************************************************
ok: [vm1]

TASK [docker : Install python3-docker for Ansible modules] ************************************************************************************
ok: [vm1]

PLAY RECAP ************************************************************************************************************************************
vm1                        : ok=13   changed=1    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0   

(venv) ➜  ansible git:(lab5) ✗ 
```

## Which tasks changed first time?

In first time we can see what task like a add GPG, add docker repo, add user to docker group in in change state but in second run all this jobs in ok state. Because ansible to task if it does not in this state so if task in needed state it does not do anything.

# Task 3

## deployment Terminal output

```bash
(venv) ➜  ansible git:(lab5) ✗ ansible-playbook playbooks/deploy.yml --ask-vault-pass
Vault password: 

PLAY [Deploy application] **************************************************************************

TASK [Gathering Facts] *****************************************************************************
ok: [vm1]

TASK [app_deploy : Validate deployment variables] **************************************************
ok: [vm1] => {
    "changed": false,
    "msg": "All assertions passed"
}

TASK [app_deploy : Log in to Docker Hub] ***********************************************************
ok: [vm1]

TASK [app_deploy : Pull Docker image] **************************************************************
ok: [vm1]

TASK [app_deploy : Stop existing container (if running)] *******************************************
ok: [vm1]

TASK [app_deploy : Remove old container (if exists)] ***********************************************
ok: [vm1]

TASK [app_deploy : Run new container] **************************************************************
changed: [vm1]

TASK [app_deploy : Wait for application port to be ready] ******************************************
ok: [vm1]

TASK [app_deploy : Verify health endpoint] *********************************************************
ok: [vm1]

RUNNING HANDLER [app_deploy : Verify deployment] ***************************************************
ok: [vm1] => {
    "msg": "Deployment of devops-info-service-python completed successfully. Port 5000 is open."
}

PLAY RECAP *****************************************************************************************
vm1                        : ok=10   changed=1    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0   

(venv) ➜  ansible git:(lab5) ✗ 
```


## Server `docker ps -a` output

```bash
(venv) ➜  ansible git:(lab5) ✗ ssh ubuntu@84.201.175.196
Welcome to Ubuntu 24.04.1 LTS (GNU/Linux 6.8.0-47-generic x86_64)

 * Documentation:  https://help.ubuntu.com
 * Management:     https://landscape.canonical.com
 * Support:        https://ubuntu.com/pro

 System information as of Tue Feb 24 09:15:52 PM UTC 2026

  System load:  0.09               Processes:             142
  Usage of /:   20.4% of 19.59GB   Users logged in:       0
  Memory usage: 22%                IPv4 address for eth0: 192.168.10.19
  Swap usage:   0%

 * Strictly confined Kubernetes makes edge and IoT secure. Learn how MicroK8s
   just raised the bar for easy, resilient and secure K8s cluster deployment.

   https://ubuntu.com/engage/secure-kubernetes-at-the-edge

Expanded Security Maintenance for Applications is not enabled.

152 updates can be applied immediately.
To see these additional updates run: apt list --upgradable

Enable ESM Apps to receive additional future security updates.
See https://ubuntu.com/esm or run: sudo pro status


*** System restart required ***
Last login: Tue Feb 24 21:15:21 2026 from 185.207.133.14
ubuntu@fhmhkilh9qgcge3bqm5n:~$ docker ps -a
CONTAINER ID   IMAGE                                        COMMAND           CREATED          STATUS          PORTS                    NAMES
562cc1167b12   zsalavat/devops-info-service-python:latest   "python app.py"   47 seconds ago   Up 47 seconds   0.0.0.0:5000->5000/tcp   devops-info-service-python
ubuntu@fhmhkilh9qgcge3bqm5n:~$ 
```

## Curl check

```bash
(venv) ➜  ansible git:(lab5) ✗ curl 84.201.175.196:5000/health                 
{"status":"healthy","timestamp":"2026-02-24T21:17:00.273047+00:00","uptime_seconds":108}
(venv) ➜  ansible git:(lab5) ✗ 
```


```bash
(venv) ➜  ansible git:(lab5) ✗ curl 84.201.175.196:5000/      
{"endpoints":[{"description":"Service information","method":"GET","path":"/"},{"description":"Health check","method":"GET","path":"/health"}],"request":{"client_ip":"185.207.133.14","method":"GET","path":"/","user_agent":"curl/8.18.0"},"runtime":{"current-time":"2026-02-24T21:17:51.400530+00:00","timezone":"UTC","uptime_human":"0 hours, 2 minutes","uptime_seconds":160},"service":{"description":"DevOps course info service","name":"devops-info-service","version":"1.0.0"},"system":{"architecture":"x86_64","cpu_count":2,"hostname":"562cc1167b12","platform":"Linux","platform_version":"#47-Ubuntu SMP PREEMPT_DYNAMIC Fri Sep 27 21:40:26 UTC 2024","python_version":"3.13.12"}}
(venv) ➜  ansible git:(lab5) ✗ 
```

# Key decisions

We use roles instead of plain manalite for better deployment process. Also we can use this roles in over playbooks in we needed it in the future. Ansible vault is necessary because we need keep credentials in secure