# Lab 5 — Ansible Fundamentals

## 1. Architecture Overview

- **Ansible version:** latest (installed via pip inside Docker container)
- **Control node:** Docker container (`python:3.11-slim` + Ansible), running on Windows
- **Target VM:** Ubuntu 24.04 LTS on Yandex Cloud (provisioned via Pulumi)
- **VM IP:** `89.169.137.6`, SSH user: `ubuntu`

### Role Structure

```
ansible/
├── ansible.cfg
├── Dockerfile                    # Ansible control node (Docker on Windows)
├── inventory/
│   └── hosts.ini                 # Static inventory (Yandex Cloud VM)
├── roles/
│   ├── common/                   # System baseline: packages, timezone
│   │   ├── tasks/main.yml
│   │   └── defaults/main.yml
│   ├── docker/                   # Docker CE installation
│   │   ├── tasks/main.yml
│   │   ├── handlers/main.yml
│   │   └── defaults/main.yml
│   └── app_deploy/               # Application container deployment
│       ├── tasks/main.yml
│       ├── handlers/main.yml
│       └── defaults/main.yml
├── playbooks/
│   ├── site.yml                  # Full: provision + deploy
│   ├── provision.yml             # System provisioning only
│   └── deploy.yml                # App deployment only
├── group_vars/
│   └── all.yml                   # Encrypted variables (Ansible Vault)
└── docs/
    └── LAB05.md                  # This file
```

### Why Roles Instead of Monolithic Playbooks?

Roles provide **modular, reusable, and testable** units of automation. Each role encapsulates a single responsibility (e.g., Docker installation). This makes it easy to reuse the `docker` role in other projects, test each role independently, and maintain clear separation of concerns.

---

## 2. Roles Documentation

### Common Role (`roles/common/`)

| Item | Details |
|------|---------|
| **Purpose** | Install essential system packages, set timezone |
| **Key Variables** | `common_packages` (list of apt packages), `timezone` (default: UTC) |
| **Handlers** | None |
| **Dependencies** | None |

### Docker Role (`roles/docker/`)

| Item | Details |
|------|---------|
| **Purpose** | Install Docker CE from official repository |
| **Key Variables** | `docker_users` (users to add to docker group), `docker_packages` (Docker package list) |
| **Handlers** | `restart docker` — restarts Docker service when package is installed or config changes |
| **Dependencies** | None (prerequisites installed within the role) |

### App Deploy Role (`roles/app_deploy/`)

| Item | Details |
|------|---------|
| **Purpose** | Pull and run containerized Python app from Docker Hub |
| **Key Variables** | `dockerhub_username`, `dockerhub_password` (from Vault), `docker_image`, `docker_image_tag`, `app_port`, `app_container_name`, `app_restart_policy` |
| **Handlers** | `restart app container` — restarts the application container |
| **Dependencies** | Requires Docker to be installed (docker role) |

---

## 3. Idempotency Demonstration

### First Run

```
PLAY [Provision web servers] ******************************************************************************************

TASK [Gathering Facts] **********************************************************************************************
ok: [yc-vm]

TASK [common : Update apt cache] **************************************************************************************
changed: [yc-vm]

TASK [common : Install common packages] *******************************************************************************changed: [yc-vm]

TASK [common : Set timezone] ******************************************************************************************changed: [yc-vm]

TASK [docker : Install Docker prerequisites] **************************************************************************ok: [yc-vm]

TASK [docker : Create keyrings directory] *****************************************************************************ok: [yc-vm]

TASK [docker : Add Docker GPG key] ************************************************************************************changed: [yc-vm]

TASK [docker : Add Docker repository] *********************************************************************************changed: [yc-vm]

TASK [docker : Install Docker packages] *******************************************************************************changed: [yc-vm]

TASK [docker : Ensure Docker service is running and enabled] **********************************************************ok: [yc-vm]

TASK [docker : Add users to docker group] *****************************************************************************changed: [yc-vm] => (item=ubuntu)

TASK [docker : Install python3-docker for Ansible modules] ************************************************************changed: [yc-vm]

RUNNING HANDLER [docker : restart docker] *****************************************************************************changed: [yc-vm]

PLAY RECAP ************************************************************************************************************yc-vm                      : ok=13   changed=9    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0     

```

### Second Run

```
PLAY [Provision web servers] ******************************************************************************************
TASK [Gathering Facts] **********************************************************************************************
ok: [yc-vm]

TASK [common : Update apt cache] **************************************************************************************ok: [yc-vm]

TASK [common : Install common packages] *******************************************************************************ok: [yc-vm]

TASK [common : Set timezone] ******************************************************************************************ok: [yc-vm]

TASK [docker : Install Docker prerequisites] **************************************************************************ok: [yc-vm]

TASK [docker : Create keyrings directory] *****************************************************************************ok: [yc-vm]

TASK [docker : Add Docker GPG key] ************************************************************************************ok: [yc-vm]

TASK [docker : Add Docker repository] *********************************************************************************ok: [yc-vm]

TASK [docker : Install Docker packages] *******************************************************************************ok: [yc-vm]

TASK [docker : Ensure Docker service is running and enabled] **********************************************************ok: [yc-vm]

TASK [docker : Add users to docker group] *****************************************************************************ok: [yc-vm] => (item=ubuntu)

TASK [docker : Install python3-docker for Ansible modules] ************************************************************ok: [yc-vm]

PLAY RECAP ************************************************************************************************************yc-vm                      : ok=12   changed=0    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0     

```

### Analysis

**First run:** Tasks like "Install common packages", "Add Docker GPG key", "Install Docker packages" show `changed` because packages are being installed for the first time.

**Second run:** All tasks show `ok` because:
- `apt` with `state: present` checks if package is already installed
- `service` with `state: started` checks if service is already running
- `file` with `state: directory` checks if directory exists
- `apt_repository` checks if repo is already present

This is **idempotency** — running the same playbook multiple times produces the same end state without making unnecessary changes.

---

## 4. Ansible Vault Usage

### How Credentials Are Stored

Sensitive data (Docker Hub username/password, app configuration) is stored in `group_vars/all.yml`, which is encrypted with `ansible-vault encrypt`.

### Vault Password Management

The vault password is stored in a `.vault_pass` file locally, which is:
- Added to `.gitignore` (never committed)
- Referenced in `ansible.cfg` or passed via `--ask-vault-pass`

### Encrypted File Example

```
$ANSIBLE_VAULT;1.1;AES256
37643638366134366632643037313965636261626130613639373466353633613063356433326334
3831376333363339313631343533663762616432666232620a633937633162303336643962653035
63633764346266386162313665363639333732626630396237653739636131653464616531663662
3065356563626364380a353339323463353934303630376531646466646439616565663734623137
31653139663837613762343431656665346331353064663533653035313538613737623861383137
62326662646136316466336138646563363537353937393534656335363337363839363334333463
34323065613466333838396362633034626332303131396538613563336338326530633364336465
63333962306564336162353764626565303739653934343433633732363139376363326365663765
63303732373535656331633032636139373162343734623261653837353264633565393432313932
64393936636164343735333061623639656634336432353936643565313031303966333739323630
32313162653639613932383637306564666635353164383861323065306133326362353862623361
33323737633833353739373338313732313461393630303665653233333964333039626637333239
35386431386365353762303835646636313531626334373836643866383030656431303432626263
34626132316434643038623930626632353033353638303034663737373437646139363431656236
38656637376134353765343239663262343739663935653763303336346237343231616134383035
38663562646538643432666330633133396465396262316365303439363033373536633630343138
30353766396235303631373039353839343935313038303733333936303763373362

```

### Why Ansible Vault Is Important

Without Vault, credentials would need to be stored in plaintext in version control or passed through environment variables. Vault allows secrets to be committed alongside code (encrypted) while remaining accessible only to authorized users with the vault password.

---

## 5. Deployment Verification

### Deployment Output

```
PLAY [Deploy application] *********************************************************************************************

TASK [Gathering Facts] ************************************************************************************************
ok: [yc-vm]

TASK [app_deploy : Log in to Docker Hub] ******************************************************************************
ok: [yc-vm]

TASK [app_deploy : Pull application Docker image] *********************************************************************
changed: [yc-vm]

TASK [app_deploy : Stop existing application container] ***************************************************************
ok: [yc-vm]

TASK [app_deploy : Run application container] *************************************************************************
changed: [yc-vm]

TASK [app_deploy : Wait for application port to be available] *********************************************************
ok: [yc-vm]

TASK [app_deploy : Verify application health endpoint] ****************************************************************
ok: [yc-vm]

TASK [app_deploy : Display health check result] ***********************************************************************
ok: [yc-vm] => {
    "health_result.json": {
        "status": "healthy",
        "timestamp": "2026-02-26T10:26:18.354036",
        "uptime_seconds": 8
    }
}

RUNNING HANDLER [app_deploy : restart app container] ******************************************************************
changed: [yc-vm]

PLAY RECAP ************************************************************************************************************
yc-vm                      : ok=9    changed=3    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0
```

### Health Check

```bash
$ curl http://89.169.137.6:5000/health
StatusCode        : 200
StatusDescription : OK
Content           : {"status":"healthy","timestamp":"2026-02-26T10:29:49.981915","uptime_seconds":207}
RawContent        : HTTP/1.1 200 OK
                    Content-Length: 82
                    Content-Type: application/json
                    Date: Thu, 26 Feb 2026 10:29:49 GMT
                    Server: uvicorn

                    {"status":"healthy","timestamp":"2026-02-26T10:29:49.981915","uptime_second...
Forms             : {}
Headers           : {[Content-Length, 82], [Content-Type, application/json], [Date, Thu, 26 Feb 2026 10:29:49 GMT], [S 
                    erver, uvicorn]}
Images            : {}
InputFields       : {}
Links             : {}
ParsedHtml        : mshtml.HTMLDocumentClass
RawContentLength  : 82
```


---

## 6. Key Decisions

**Why use roles instead of plain playbooks?**
Roles organize tasks into reusable, self-contained units with standardized structure. This makes code maintainable, shareable (via Ansible Galaxy), and testable independently.

**How do roles improve reusability?**
A role like `docker` can be used across any project that needs Docker installed—simply include it in a playbook. Variables in `defaults/` allow customization without modifying role code.

**What makes a task idempotent?**
Using Ansible modules that check current state before making changes (e.g., `apt: state=present` only installs if not present, `service: state=started` only starts if stopped). Avoid `shell`/`command` when a dedicated module exists.

**How do handlers improve efficiency?**
Handlers run only when notified and only once at the end of a play. This prevents unnecessary service restarts—Docker is restarted only when its packages are actually installed or updated, not on every playbook run.

**Why is Ansible Vault necessary?**
Production deployments require credentials (Docker registry tokens, API keys). Vault encrypts these so they can live in Git safely. Without Vault, teams resort to insecure practices like plaintext secrets or manual credential passing.

---

## 7. Challenges

- **Windows compatibility:** Ansible doesn't run natively on Windows. Solved by creating a Docker container as the control node with Ansible installed.
- **Docker GPG key method:** The `apt_key` module is deprecated. Used `get_url` to download the key to `/etc/apt/keyrings/` instead (modern approach matching Docker's official docs).
- **SSH key permissions in Docker:** Mounting Windows SSH keys into Linux containers yields `0777` permissions, which SSH rejects. Solved with `entrypoint.sh` that copies keys from a read-only mount (`/root/.ssh-mount`) to `/root/.ssh` with `chmod 600`.
- **ansible.cfg world-writable directory:** Docker-mounted `/ansible` is world-writable, so Ansible ignores `ansible.cfg` there. Fixed by copying `ansible.cfg` into `/etc/ansible/` during Docker build and using `ANSIBLE_CONFIG` env var.
