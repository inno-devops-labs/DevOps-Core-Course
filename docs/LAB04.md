# LAB04 — Infrastructure as Code (Terraform & Pulmi)

For this lab, I chose to use a local VM installation (WSL). I tried third-party services, but faced with the limitations of these services.

## Task 1 — Terraform VM Creation

### Attempt to Use Yandex Cloud

I initially attempted to create infrastructure using Terraform with Yandex Cloud provider.

#### 1. Terraform Configuration

I created the following Terraform files in `terraform/` directory:

- **`versions.tf`** — Terraform and provider version constraints (`>= 1.9`, `yandex-cloud/yandex ~> 0.100`)
- **`provider.tf`** — Yandex Cloud provider configuration using service account key file
- **`main.tf`** — Infrastructure resources:
  - Data source for Ubuntu 22.04 LTS image (`yandex_compute_image`)
  - Data source for existing VPC network (`yandex_vpc_network`)
  - Subnet resource (`yandex_vpc_subnet`) — 10.10.0.0/24 in ru-central1-a zone
  - VM instance (`yandex_compute_instance`) — standard-v2 platform, 2 vCPU @ 20%, 1 GB RAM, 10 GB disk
- **`variables.tf`** — Input variables (cloud_id, folder_id, zone, project_name, SSH key path, etc.)
- **`outputs.tf`** — Output values (instance IP, SSH command)

#### 2. Terraform Setup and Validation

I initialized and validated the Terraform configuration:

```bash
cd terraform
terraform init
terraform fmt
terraform validate
terraform plan
```

**Terraform Init Output:**
```
Initializing the backend...
Initializing provider plugins...
- Finding yandex-cloud/yandex versions matching "~> 0.100"...
- Installing yandex-cloud/yandex v0.100.0...
...
Terraform has been successfully initialized!
```

**Terraform Validate:**
```
Success! The configuration is valid.
```

**Terraform Plan:**
The plan showed that Terraform would create:
- 1 VPC subnet (`iac-lab4-subnet`)
- 1 compute instance (`iac-lab4-vm`) with public IP via NAT

#### 3. Encountered Limitations

When attempting to apply the infrastructure (`terraform apply`), I encountered permission errors:

**First Error (Security Group):**
```
Error: error while requesting API to create security group: 
client-request-id = e3c58798-55ce-4b47-94d6-f7f18ea7ac43 
rpc error: code = PermissionDenied 
desc = Permission denied to add ingress rule to security group

  with yandex_vpc_security_group.secure_group,
  on main.tf line 18
```

Tried to remove it and stay only with vm.

**Second Error (Resource Manager):**
```
Error: Error while requesting API to create instance: 
client-request-id = 20941370-5807-3393-636e-963fb99339f5 client-trace-id = d141ejja-aafb-4c0d-1aca-b47334b56jh7 
rpc error: code = PermissionDenied 
desc = Permission denied to resource-manager.folder bjagvko590d5hs1p9qh2

  with yandex_compute_instance.vm,
  on main.tf line 19
```

Despite having appropriate IAM roles assigned to the service account (`vpc.admin`, `compute.admin`, `editor`, `vpc.user` and other, more powerful roles), the organization's security policies prevented creation of security groups and compute instances in Yandex Cloud.

### Local VM (WSL2)

Due to the cloud provider limitations, I used my existing **WSL2 (Windows Subsystem for Linux)** environment running Ubuntu as the local VM for this lab.

#### 1. WSL2 Environment

WSL2 with Ubuntu had been installed on my system previously. I verified the installation:

```bash
wsl --list --verbose
```

**Output:**
```
  NAME           STATE           VERSION
* Ubuntu24.04    Running         2
```

#### 2. System Information

```bash
uname -a
```

**Output:**
```
Linux chale 5.15.167.4-microsoft-standard-WSL2 #1 SMP Tue Nov 5 00:21:55 UTC 2024 x86_64 x86_64 x86_64 GNU/Linux
```

---

```bash
lsb_release -a
```

**Output:**
```
No LSB modules are available.
Distributor ID: Ubuntu
Description:    Ubuntu 24.04.4 LTS
Release:        24.04
Codename:       noble
```

#### 3. SSH Configuration

**a. Generated SSH key pair on Windows host:**

```powershell
ssh-keygen -t ed25519 -C "lab4-wsl" -f "$env:USERPROFILE\.ssh\id_ed25519"
```

**b. Configured SSH server in WSL:**

```bash
ssh-keygen -t ed25519 -C "lab4-wsl" -f "$env:USERPROFILE\.ssh\id_ed25519"
chmod 700 ~/.ssh
echo 'ssh-ed25519 <id_ed25519.pub> lab4-wsl' >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
```
id_ed25519.pub - generated public ssh key in widnows.

**c. Verified SSH access from Windows host:**

```powershell
ssh -i $env:USERPROFILE\.ssh\id_ed25519 andpe@localhost
```

**SSH Connection Successful:**
```
Welcome to Ubuntu 24.04.4 LTS (GNU/Linux 5.15.167.4-microsoft-standard-WSL2 x86_64)
...
andpe@chale:~$
```

### VM Specifications

| **Property** | **Value** |
| --- | --- |
| **Type** | WSL2 (Windows Subsystem for Linux) |
| **OS** | Ubuntu 24.04.4 LTS |
| **Kernel** | 5.15.167.4-microsoft-standard-WSL2 |
| **Host Access** | `localhost` (SSH port 22) |
| **SSH Key** | Ed25519 key pair |
| **User** | andpe |



## Task 3 — Documentation

#### Setup documentation

- **Virtualization software**: WSL2 (Windows Subsystem for Linux)
- **Guest OS**: Ubuntu 24.04.4 LTS
- **Virtual Hardware**:

| **Property**  | **Value** |
| ---           | ---       |
| Storage space | 1007 G (size of `/dev/sdc` from df -h) |
| RAM Volume    | 7.4 Gi + 2.0 Gi (swap)   |
| CPU Cores     | 12       |

- **SSH Access**:

| **Host Address** | **Guest Address** |
| ---              | ---               |
| localhost:22     | localhost:22      |

- **Guest Software**: OpenSSH_9.6p1 Ubuntu-3ubuntu13.14, OpenSSL 3.0.13 30 Jan 2024

#### Terraform Configuration

I attempted to use Yandex Cloud with Terraform but encountered organization-level security policy restrictions that prevented resource creation despite having appropriate IAM roles. I created Terraform configuration files in `terraform/` directory demonstrating Infrastructure as Code principles:

- **Project Structure**: `versions.tf`, `provider.tf`, `main.tf`, `variables.tf`, `outputs.tf`
- **Resources Defined**: VPC subnet, compute instance with free-tier specs (2 vCPU @ 20%, 1 GB RAM, 10 GB disk)
- **Configuration**: Used data sources for Ubuntu image and existing VPC network, variables for all configurable values, outputs for instance IP and SSH command

**Terraform Commands Executed:**
- `terraform init` — Successfully initialized provider plugins
- `terraform validate` — Configuration is valid
- `terraform plan` — Showed planned creation of subnet and VM instance
- `terraform apply` — Failed with `PermissionDenied` error due to organization security policies

**Error Encountered:**
```
Error: Error while requesting API to create instance: 
rpc error: code = PermissionDenied 
desc = Permission denied to resource-manager.folder
```

Due to these limitations, I used my existing WSL2 Ubuntu environment as the local VM for Lab 5 (and we don't need to cleanup anything).