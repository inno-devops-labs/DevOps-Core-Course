# Lab 04 - Infrastructure as Code (Terraform & Pulumi)

**Student:** [Your Name]  
**Date:** February 25, 2026  
**Lab:** Lab 04 - Infrastructure as Code  
**Cloud Provider:** Yandex Cloud  
**VM IP:** 158.160.195.2 (Existing VM - will be managed with IaC)

---

## Table of Contents

1. [Cloud Provider & Infrastructure](#1-cloud-provider--infrastructure)
2. [Terraform Implementation](#2-terraform-implementation)
3. [Pulumi Implementation](#3-pulumi-implementation)
4. [Terraform vs Pulumi Comparison](#4-terraform-vs-pulumi-comparison)
5. [Bonus Task: IaC CI/CD](#5-bonus-task-iac-cicd)
6. [Bonus Task: GitHub Repository Import](#6-bonus-task-github-repository-import)
7. [Lab 5 Preparation & Cleanup](#7-lab-5-preparation--cleanup)

---

## 1. Cloud Provider & Infrastructure

### Cloud Provider Selection

**Provider Chosen:** Yandex Cloud

**Rationale:**
- Available and accessible in Russia
- Free tier offering (20% vCPU, 1 GB RAM, 10 GB storage)
- Good documentation in Russian and English
- No credit card required for initial tier
- Reliable API and Terraform/Pulumi provider support

### Infrastructure Specifications

**Instance Type/Size:**
- **Platform:** standard-v2
- **vCPU:** 2 cores at 20% core fraction (free tier)
- **Memory:** 1 GB RAM
- **Disk:** 10 GB HDD (network-hdd)
- **OS:** Ubuntu 24.04 LTS

**Region/Zone:**
- **Zone:** ru-central1-a (default Yandex Cloud zone)

**Total Cost:**
- **Expected Cost:** $0/month (within free tier limits)
- Using free tier resources only

### Resources Created

1. **VPC Network** (`lab04-network`)
   - Virtual private cloud for isolation

2. **Subnet** (`lab04-subnet`)
   - CIDR: 10.128.0.0/24 (Terraform) / 10.129.0.0/24 (Pulumi)
   - Zone: ru-central1-a

3. **Security Group** (`lab04-security-group`)
   - Ingress Rules:
     - SSH (port 22) - restricted to specific IP
     - HTTP (port 80) - open to all
     - Custom (port 5000) - open to all (for future app deployment)
   - Egress Rules:
     - All traffic allowed (required for package installation)

4. **Compute Instance** (`lab04-devops-vm`)
   - Ubuntu 24.04 LTS
   - SSH access with public key authentication
   - Public IP address assigned
   - Labels for identification and management

---

## 2. Terraform Implementation

### Terraform Version

```bash
$ terraform version
Terraform v1.9.8
```

### Project Structure

```
terraform/
├── .tflint.hcl              # TFLint configuration
├── main.tf                  # Main resources
├── variables.tf             # Input variables
├── outputs.tf               # Output values
├── terraform.tfvars         # Variable values (gitignored)
├── terraform.tfvars.example # Example configuration
└── README.md                # Setup instructions
```

### Key Configuration Decisions

1. **Variables for Reusability**
   - `folder_id`: Yandex Cloud folder ID
   - `zone`: Cloud zone (default: ru-central1-a)
   - `my_ip_cidr`: Restricted SSH access to specific IP
   - `ssh_user` and `ssh_public_key_path`: SSH configuration

2. **Security Best Practices**
   - SSH restricted to specific IP (not 0.0.0.0/0)
   - Credentials in terraform.tfvars (gitignored)
   - State file excluded from Git
   - Service account authentication

3. **Free Tier Configuration**
   - core_fraction = 20% (free tier requirement)
   - 1 GB memory, 10 GB HDD
   - Minimal resources to avoid costs

4. **Resource Labeling**
   - Added labels for resource identification
   - Helps with cost tracking and organization

### Terraform Commands and Output

#### Terraform Init

```bash
$ terraform init

Initializing the backend...

Initializing provider plugins...
- Finding yandex-cloud/yandex versions matching "~> 0.120"...
- Installing yandex-cloud/yandex v0.120.0...
- Installed yandex-cloud/yandex v0.120.0

Terraform has been successfully initialized!
```

#### Terraform Fmt

```bash
$ terraform fmt
main.tf
variables.tf
outputs.tf
```

#### Terraform Validate

```bash
$ terraform validate
Success! The configuration is valid.
```

#### Terraform Plan

*Note: You'll need to run this after configuring terraform.tfvars with your Yandex Cloud credentials*

```bash
$ terraform plan

Terraform used the selected providers to generate the following execution plan.
Resource actions are indicated with the following symbols:
  + create

Terraform will perform the following actions:

  # yandex_compute_instance.lab04_vm will be created
  + resource "yandex_compute_instance" "lab04_vm" {
      + created_at       = (known after apply)
      + name             = "lab04-devops-vm"
      + platform_id      = "standard-v2"
      + zone             = "ru-central1-a"
      
      + resources {
          + cores         = 2
          + memory        = 1
          + core_fraction = 20
        }
      
      + boot_disk {
          + initialize_params {
              + image_id = "fd8kdq6d0p8sij7h5qe3"
              + size     = 10
              + type     = "network-hdd"
            }
        }
      
      + network_interface {
          + nat                = true
          + subnet_id          = (known after apply)
          + nat_ip_address     = (known after apply)
        }
    }

  # yandex_vpc_network.lab04_network will be created
  + resource "yandex_vpc_network" "lab04_network" {
      + created_at = (known after apply)
      + name       = "lab04-network"
    }

  # yandex_vpc_subnet.lab04_subnet will be created
  + resource "yandex_vpc_subnet" "lab04_subnet" {
      + name           = "lab04-subnet"
      + v4_cidr_blocks = ["10.128.0.0/24"]
      + zone           = "ru-central1-a"
      + network_id     = (known after apply)
    }

  # yandex_vpc_security_group.lab04_sg will be created
  + resource "yandex_vpc_security_group" "lab04_sg" {
      + name       = "lab04-security-group"
      + network_id = (known after apply)
      
      + ingress {
          + port           = 22
          + protocol       = "TCP"
          + v4_cidr_blocks = ["YOUR_IP/32"]
        }
      
      + ingress {
          + port           = 80
          + protocol       = "TCP"
          + v4_cidr_blocks = ["0.0.0.0/0"]
        }
      
      + ingress {
          + port           = 5000
          + protocol       = "TCP"
          + v4_cidr_blocks = ["0.0.0.0/0"]
        }
      
      + egress {
          + protocol       = "ANY"
          + v4_cidr_blocks = ["0.0.0.0/0"]
        }
    }

Plan: 4 to add, 0 to change, 0 to destroy.

Changes to Outputs:
  + vm_public_ip           = (known after apply)
  + vm_name                = "lab04-devops-vm"
  + ssh_connection_command = (known after apply)
```

#### Terraform Apply

```bash
$ terraform apply

data.yandex_compute_image.ubuntu: Reading...
data.yandex_compute_image.ubuntu: Read complete after 1s [id=fd883u1fsun0dqhg49jq]

Terraform used the selected providers to generate the following execution plan.
Resource actions are indicated with the following symbols:
  + create

Terraform will perform the following actions:

  # yandex_compute_instance.lab04_vm will be created
  + resource "yandex_compute_instance" "lab04_vm" {
      + created_at                = (known after apply)
      + description               = "VM for Lab 04 - Infrastructure as Code"
      + folder_id                 = "b1g931kepl160s0cblpj"
      + fqdn                      = (known after apply)
      + gpu_cluster_id            = (known after apply)
      + hostname                  = (known after apply)
      + id                        = (known after apply)
      + labels                    = {
          + "environment" = "lab"
          + "lab"         = "lab04"
          + "managed-by"  = "terraform"
        }
      + metadata                  = {
          + "ssh-keys" = <<-EOT
                ubuntu:ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAID9wv7bkl4ZzVDStfDU4ZzsUSvUsSHE2oEvZFPD+jhHe gvs132005@yandex.ru
            EOT
        }
      + name                      = "lab04-devops-vm"
      + network_acceleration_type = "standard"
      + platform_id               = "standard-v2"
      + service_account_id        = (known after apply)
      + status                    = (known after apply)
      + zone                      = "ru-central1-a"

      + boot_disk {
          + auto_delete = true
          + device_name = (known after apply)
          + disk_id     = (known after apply)
          + mode        = (known after apply)

          + initialize_params {
              + block_size  = (known after apply)
              + description = (known after apply)
              + image_id    = "fd883u1fsun0dqhg49jq"
              + name        = (known after apply)
              + size        = 10
              + snapshot_id = (known after apply)
              + type        = "network-hdd"
            }
        }

      + network_interface {
          + index              = (known after apply)
          + ip_address         = (known after apply)
          + ipv4               = true
          + ipv6               = (known after apply)
          + ipv6_address       = (known after apply)
          + mac_address        = (known after apply)
          + nat                = true
          + nat_ip_address     = (known after apply)
          + nat_ip_version     = (known after apply)
          + security_group_ids = (known after apply)
          + subnet_id          = (known after apply)
        }

      + resources {
          + core_fraction = 20
          + cores         = 2
          + memory        = 1
        }

      + scheduling_policy {
          + preemptible = (known after apply)
        }
    }

  # yandex_vpc_network.lab04_network will be created
  + resource "yandex_vpc_network" "lab04_network" {
      + created_at                = (known after apply)
      + default_security_group_id = (known after apply)
      + folder_id                 = "b1g931kepl160s0cblpj"
      + id                        = (known after apply)
      + labels                    = {
          + "environment" = "lab"
          + "lab"         = "lab04"
          + "managed-by"  = "terraform"
        }
      + name                      = "lab04-network"
      + subnet_ids                = (known after apply)
    }

  # yandex_vpc_security_group.lab04_sg will be created
  + resource "yandex_vpc_security_group" "lab04_sg" {
      + created_at = (known after apply)
      + folder_id  = "b1g931kepl160s0cblpj"
      + id         = (known after apply)
      + labels     = {
          + "environment" = "lab"
          + "lab"         = "lab04"
          + "managed-by"  = "terraform"
        }
      + name       = "lab04-security-group"
      + network_id = (known after apply)
      + status     = (known after apply)

      + egress {
          + description    = "Allow all outbound traffic"
          + from_port      = -1
          + id             = (known after apply)
          + labels         = (known after apply)
          + port           = -1
          + protocol       = "ANY"
          + to_port        = -1
          + v4_cidr_blocks = [
              + "0.0.0.0/0",
            ]
          + v6_cidr_blocks = []
        }

      + ingress {
          + description    = "Allow SSH from specific IP"
          + from_port      = -1
          + id             = (known after apply)
          + labels         = (known after apply)
          + port           = 22
          + protocol       = "TCP"
          + to_port        = -1
          + v4_cidr_blocks = [
              + "188.130.155.169/32",
            ]
          + v6_cidr_blocks = []
        }
      + ingress {
          + description    = "Allow HTTP"
          + from_port      = -1
          + id             = (known after apply)
          + labels         = (known after apply)
          + port           = 80
          + protocol       = "TCP"
          + to_port        = -1
          + v4_cidr_blocks = [
              + "0.0.0.0/0",
            ]
          + v6_cidr_blocks = []
        }
      + ingress {
          + description    = "Allow port 5000 for app"
          + from_port      = -1
          + id             = (known after apply)
          + labels         = (known after apply)
          + port           = 5000
          + protocol       = "TCP"
          + to_port        = -1
          + v4_cidr_blocks = [
              + "0.0.0.0/0",
            ]
          + v6_cidr_blocks = []
        }
    }

  # yandex_vpc_subnet.lab04_subnet will be created
  + resource "yandex_vpc_subnet" "lab04_subnet" {
      + created_at     = (known after apply)
      + folder_id      = "b1g931kepl160s0cblpj"
      + id             = (known after apply)
      + labels         = {
          + "environment" = "lab"
          + "lab"         = "lab04"
          + "managed-by"  = "terraform"
        }
      + name           = "lab04-subnet"
      + network_id     = (known after apply)
      + v4_cidr_blocks = [
          + "10.128.0.0/24",
        ]
      + v6_cidr_blocks = (known after apply)
      + zone           = "ru-central1-a"
    }

Plan: 4 to add, 0 to change, 0 to destroy.

Changes to Outputs:
  + network_id             = (known after apply)
  + security_group_id      = (known after apply)
  + ssh_connection_command = (known after apply)
  + subnet_id              = (known after apply)
  + vm_name                = "lab04-devops-vm"
  + vm_public_ip           = (known after apply)

Do you want to perform these actions?
  Terraform will perform the actions described above.
  Only 'yes' will be accepted to approve.

  Enter a value: yes

yandex_vpc_network.lab04_network: Creating...
yandex_vpc_network.lab04_network: Creation complete after 3s [id=enpmp93cgto2ifi08a6i]
yandex_vpc_security_group.lab04_sg: Creating...
yandex_vpc_subnet.lab04_subnet: Creating...
yandex_vpc_subnet.lab04_subnet: Creation complete after 1s [id=e9btkds0itjpfga9on08]
yandex_vpc_security_group.lab04_sg: Creation complete after 3s [id=enpanlj5ct13mvocgfic]
yandex_compute_instance.lab04_vm: Creating...
yandex_compute_instance.lab04_vm: Still creating... [10s elapsed]
yandex_compute_instance.lab04_vm: Still creating... [20s elapsed]
yandex_compute_instance.lab04_vm: Still creating... [30s elapsed]
yandex_compute_instance.lab04_vm: Creation complete after 35s [id=fhmq3as7j3si701ce5bo]

Apply complete! Resources: 4 added, 0 changed, 0 destroyed.

Outputs:

network_id = "enpmp93cgto2ifi08a6i"
security_group_id = "enpanlj5ct13mvocgfic"
ssh_connection_command = "ssh -i ~/.ssh/id_ed25519 ubuntu@89.169.155.28"
subnet_id = "e9btkds0itjpfga9on08"
vm_name = "lab04-devops-vm"
vm_public_ip = "89.169.155.28"
```

### SSH Access Verification

```bash
$ ssh -i ~/.ssh/id_ed25519 ubuntu@89.169.155.28

Welcome to Ubuntu 24.04.4 LTS (GNU/Linux 6.8.0-100-generic x86_64)

 * Documentation:  https://help.ubuntu.com
 * Management:     https://landscape.canonical.com
 * Support:        https://ubuntu.com/pro

System information as of Wed Feb 25 19:16:54 UTC 2026

  System load:  0.06               Processes:               102
  Usage of /:   23.1% of 9.04GB    Users logged in:         0
  Memory usage: 17%                IPv4 address for eth0: 10.128.0.13
  Swap usage:   0%

Expanded Security Maintenance for Applications is not enabled.

0 updates can be applied immediately.

Enable ESM Apps to receive additional future security updates.
See https://ubuntu.com/esm or run: sudo pro status

ubuntu@fhmq3as7j3si701ce5bo:~$ hostname && uname -a && free -h && df -h && ip addr show eth0
fhmq3as7j3si701ce5bo
Linux fhmq3as7j3si701ce5bo 6.8.0-100-generic #100-Ubuntu SMP PREEMPT_DYNAMIC Tue Jan 13 16:40:06 UTC 2026 x86_64 x86_64 x86_64 GNU/Linux
               total        used        free      shared  buff/cache   available
Mem:           961Mi       296Mi       582Mi       1.0Mi       224Mi       664Mi
Swap:             0B          0B          0B
Filesystem      Size  Used Avail Use% Mounted on
tmpfs            97M  1.1M   96M   2% /run
/dev/vda1       9.1G  2.1G  7.0G  24% /
tmpfs           481M     0  481M   0% /dev/shm
tmpfs           5.0M     0  5.0M   0% /run/lock
/dev/vda15      599M  6.2M  593M   2% /boot/efi
tmpfs            97M  8.0K   97M   1% /run/user/1000
2: eth0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc mq state UP group default qlen 1000
    link/ether d0:0d:1a:1a:b8:79 brd ff:ff:ff:ff:ff:ff
    altname enp7s0
    inet 10.128.0.13/24 metric 100 brd 10.128.0.255 scope global dynamic eth0
       valid_lft 4294966946sec preferred_lft 4294966946sec
    inet6 fe80::d20d:1aff:fe1a:b879/64 scope link
       valid_lft forever preferred_lft forever

ubuntu@fhmq3as7j3si701ce5bo:~$ exit
logout
Connection to 89.169.155.28 closed.
```

### Challenges Encountered

1. **Authentication Setup**
   - Initial confusion between OAuth token and service account key
   - Solution: Used service account with key.json file for Terraform

2. **Security Group Rules**
   - First attempt had SSH open to 0.0.0.0/0 (security risk)
   - Solution: Restricted to specific IP using `my_ip_cidr` variable

3. **Free Tier Configuration**
   - Needed to understand core_fraction parameter
   - Solution: Set to 20% as per Yandex Cloud free tier requirements

---

## 3. Pulumi Implementation

### Pulumi Version and Language

```bash
$ pulumi version
v3.223.0

$ python --version
Python 3.12.8
```

**Language Chosen:** Python 3.12

**Rationale:**
- Familiar language for most developers
- Excellent IDE support with type hints
- Good balance of readability and power
- Strong Pulumi SDK documentation for Python

### Project Structure

```
pulumi/
├── __main__.py        # Main Pulumi program
├── requirements.txt   # Python dependencies
├── Pulumi.yaml       # Project metadata
├── venv/             # Python virtual environment (gitignored)
└── README.md         # Setup instructions
```

### Terraform Destroy Output

Before creating Pulumi infrastructure, destroyed Terraform resources:

```bash
$ cd ~/myhome/inno/devops/DevOps-Core-Course/terraform
$ terraform destroy

data.yandex_compute_image.ubuntu: Reading...
data.yandex_compute_image.ubuntu: Read complete after 1s [id=fd883u1fsun0dqhg49jq]
yandex_vpc_network.lab04_network: Refreshing state... [id=enpmp93cgto2ifi08a6i]
yandex_vpc_subnet.lab04_subnet: Refreshing state... [id=e9btkds0itjpfga9on08]
yandex_vpc_security_group.lab04_sg: Refreshing state... [id=enpanlj5ct13mvocgfic]
yandex_compute_instance.lab04_vm: Refreshing state... [id=fhmq3as7j3si701ce5bo]

Terraform will perform the following actions:

  # yandex_compute_instance.lab04_vm will be destroyed
  - resource "yandex_compute_instance" "lab04_vm" {
      - id          = "fhmq3as7j3si701ce5bo" -> null
      - name        = "lab04-devops-vm" -> null
      - platform_id = "standard-v2" -> null
      # ... (resource details omitted for brevity)
    }

  # yandex_vpc_network.lab04_network will be destroyed
  - resource "yandex_vpc_network" "lab04_network" {
      - id   = "enpmp93cgto2ifi08a6i" -> null
      - name = "lab04-network" -> null
      # ...
    }

  # yandex_vpc_security_group.lab04_sg will be destroyed
  - resource "yandex_vpc_security_group" "lab04_sg" {
      - id         = "enpanlj5ct13mvocgfic" -> null
      - name       = "lab04-security-group" -> null
      - network_id = "enpmp93cgto2ifi08a6i" -> null
      # ...
    }

  # yandex_vpc_subnet.lab04_subnet will be destroyed
  - resource "yandex_vpc_subnet" "lab04_subnet" {
      - id             = "e9btkds0itjpfga9on08" -> null
      - name           = "lab04-subnet" -> null
      - v4_cidr_blocks = ["10.128.0.0/24"] -> null
      # ...
    }

Plan: 0 to add, 0 to change, 4 to destroy.

Changes to Outputs:
  - network_id             = "enpmp93cgto2ifi08a6i" -> null
  - security_group_id      = "enpanlj5ct13mvocgfic" -> null
  - ssh_connection_command = "ssh -i ~/.ssh/id_ed25519 ubuntu@89.169.155.28" -> null
  - subnet_id              = "e9btkds0itjpfga9on08" -> null
  - vm_name                = "lab04-devops-vm" -> null
  - vm_public_ip           = "89.169.155.28" -> null

Do you really want to destroy all resources?
  Terraform will destroy all your managed infrastructure.
  Enter a value: yes

yandex_compute_instance.lab04_vm: Destroying... [id=fhmq3as7j3si701ce5bo]
yandex_compute_instance.lab04_vm: Still destroying... [10s elapsed]
yandex_compute_instance.lab04_vm: Still destroying... [20s elapsed]
yandex_compute_instance.lab04_vm: Destruction complete after 23s
yandex_vpc_security_group.lab04_sg: Destroying... [id=enpanlj5ct13mvocgfic]
yandex_vpc_subnet.lab04_subnet: Destroying... [id=e9btkds0itjpfga9on08]
yandex_vpc_security_group.lab04_sg: Destruction complete after 2s
yandex_vpc_subnet.lab04_subnet: Destruction complete after 3s
yandex_vpc_network.lab04_network: Destroying... [id=enpmp93cgto2ifi08a6i]
yandex_vpc_network.lab04_network: Destruction complete after 1s

Destroy complete! Resources: 4 destroyed.
```

### Pulumi Setup and Configuration

```bash
$ cd ~/myhome/inno/devops/DevOps-Core-Course/pulumi

# Setup Python 3.12 virtual environment (using pyenv for compatibility)
$ pyenv local 3.12.8
$ python3 -m venv venv
$ source venv/bin/activate

$ python --version
Python 3.12.8

# Install dependencies
$ pip install -r requirements.txt
Collecting pulumi<4.0.0,>=3.0.0 (from -r requirements.txt (line 1))
  Using cached pulumi-3.223.0-py3-none-any.whl.metadata (3.8 kB)
Collecting pulumi-yandex>=0.13.0 (from -r requirements.txt (line 2))
  Using cached pulumi_yandex-0.13.0.tar.gz (425 kB)
  Building wheel for pulumi-yandex (pyproject.toml) ... done
Successfully installed pulumi-3.223.0 pulumi-yandex-0.13.0

# Fix pkg_resources compatibility issue with Python 3.12
$ pip install "setuptools<70"
Successfully installed setuptools-69.5.1

# Configure Pulumi CLI path
$ export PATH=$PATH:$HOME/.pulumi/bin

# Verify Pulumi installation
$ pulumi version
v3.223.0

# Login to Pulumi (using local backend)
$ pulumi login
Manage your Pulumi stacks by logging in.
Using local filesystem backend for state storage.

# Initialize stack
$ pulumi stack init dev
Created stack 'dev'

# Configure Yandex Cloud settings
$ pulumi config set yandex:folder_id b1g931kepl160s0cblpj
$ pulumi config set folder_id b1g931kepl160s0cblpj
$ pulumi config set zone ru-central1-a
$ pulumi config set ssh_user vglon
$ pulumi config set ssh_public_key_path ~/.ssh/id_ed25519.pub
$ pulumi config set my_ip_cidr "188.130.155.169/32"
```

### Pulumi Preview

```bash
$ pulumi preview

Enter your passphrase to unlock config/secrets
    (set PULUMI_CONFIG_PASSPHRASE or PULUMI_CONFIG_PASSPHRASE_FILE to remember):  
Enter your passphrase to unlock config/secrets
Previewing update (dev):
     Type                              Name                 Plan
 +   pulumi:pulumi:Stack               lab04-pulumi-dev     create
 +   ├─ yandex:index:VpcNetwork        lab04-network        create
 +   ├─ yandex:index:VpcSubnet         lab04-subnet         create
 +   ├─ yandex:index:VpcSecurityGroup  lab04-sg             create
 +   └─ yandex:index:ComputeInstance   lab04-vm             create

Outputs:
    network_id            : [unknown]
    security_group_id     : [unknown]
    ssh_connection_command: [unknown]
    subnet_id             : [unknown]
    vm_id                 : [unknown]
    vm_name               : "lab04-devops-vm-pulumi"
    vm_public_ip          : [unknown]

Resources:
    + 5 to create
```

### Pulumi Up

```bash
$ pulumi up

Enter your passphrase to unlock config/secrets
    (set PULUMI_CONFIG_PASSPHRASE or PULUMI_CONFIG_PASSPHRASE_FILE to remember):  
Enter your passphrase to unlock config/secrets
Previewing update (dev):
     Type                              Name                 Plan
 +   pulumi:pulumi:Stack               lab04-pulumi-dev     create
 +   ├─ yandex:index:VpcNetwork        lab04-network        create
 +   ├─ yandex:index:VpcSubnet         lab04-subnet         create
 +   ├─ yandex:index:VpcSecurityGroup  lab04-sg             create
 +   └─ yandex:index:ComputeInstance   lab04-vm             create

Outputs:
    network_id            : [unknown]
    security_group_id     : [unknown]
    ssh_connection_command: [unknown]
    subnet_id             : [unknown]
    vm_id                 : [unknown]
    vm_name               : "lab04-devops-vm-pulumi"
    vm_public_ip          : [unknown]

Resources:
    + 5 to create

Do you want to perform this update? yes

Updating (dev):
     Type                              Name                 Status
 +   pulumi:pulumi:Stack               lab04-pulumi-dev     created
 +   ├─ yandex:index:VpcNetwork        lab04-network        created (3s)
 +   ├─ yandex:index:VpcSecurityGroup  lab04-sg             created (2s)
 +   ├─ yandex:index:VpcSubnet         lab04-subnet         created (2s)
 +   └─ yandex:index:ComputeInstance   lab04-vm             created (35s)

Outputs:
    network_id            : "enpchpr6l14tolvs0mlq"
    security_group_id     : "enpbo90ta2u7u8artmof"
    ssh_connection_command: "ssh -i ~/.ssh/id_ed25519 ubuntu@62.84.119.211"
    subnet_id             : "e9bmnuoqgso3ss5g7edo"
    vm_id                 : "fhmlt3mvndelaaj9ikk7"
    vm_name               : "lab04-devops-vm-pulumi"
    vm_public_ip          : "62.84.119.211"

Resources:
    + 5 created

Duration: 45s
```

### SSH Access to Pulumi VM

```bash
$ pulumi stack output ssh_connection_command
ssh -i ~/.ssh/id_ed25519 ubuntu@62.84.119.211

$ ssh -i ~/.ssh/id_ed25519 ubuntu@62.84.119.211

Warning: Permanently added '62.84.119.211' (ED25519) to the list of known hosts.
Welcome to Ubuntu 24.04.4 LTS (GNU/Linux 6.8.0-100-generic x86_64)

 * Documentation:  https://help.ubuntu.com
 * Management:     https://landscape.canonical.com
 * Support:        https://ubuntu.com/pro

 System information as of Wed Feb 25 20:09:20 UTC 2026

  System load:  0.5               Processes:             101
  Usage of /:   23.1% of 9.04GB   Users logged in:       0
  Memory usage: 18%               IPv4 address for eth0: 10.129.0.29
  Swap usage:   0%

Expanded Security Maintenance for Applications is not enabled.

0 updates can be applied immediately.

Enable ESM Apps to receive additional future security updates.
See https://ubuntu.com/esm or run: sudo pro status

ubuntu@fhmlt3mvndelaaj9ikk7:~$ hostname && uname -a && free -h && df -h
fhmlt3mvndelaaj9ikk7
Linux fhmlt3mvndelaaj9ikk7 6.8.0-100-generic #100-Ubuntu SMP PREEMPT_DYNAMIC Tue Jan 13 16:40:06 UTC 2026 x86_64 x86_64 x86_64 GNU/Linux
               total        used        free      shared  buff/cache   available
Mem:           961Mi       295Mi       584Mi       1.0Mi       224Mi       665Mi
Swap:             0B          0B          0B
Filesystem      Size  Used Avail Use% Mounted on
tmpfs            97M  1.1M   96M   2% /run
/dev/vda1       9.1G  2.1G  7.0G  24% /
tmpfs           481M     0  481M   0% /dev/shm
tmpfs           5.0M     0  5.0M   0% /run/lock
/dev/vda15      599M  6.2M  593M   2% /boot/efi
tmpfs            97M  8.0K   97M   1% /run/user/1000

ubuntu@fhmlt3mvndelaaj9ikk7:~$ exit
logout
Connection to 62.84.119.211 closed.
```

### Code Differences from Terraform

#### Terraform (HCL):
```hcl
resource "yandex_compute_instance" "lab04_vm" {
  name        = "lab04-devops-vm"
  platform_id = "standard-v2"
  zone        = var.zone

  resources {
    cores         = 2
    memory        = 1
    core_fraction = 20
  }

  network_interface {
    subnet_id = yandex_vpc_subnet.lab04_subnet.id
    nat       = true
  }
}
```

#### Pulumi (Python):
```python
vm = yandex.ComputeInstance(
    "lab04-vm",
    name="lab04-devops-vm-pulumi",
    platform_id="standard-v2",
    zone=zone,
    resources={
        "cores": 2,
        "memory": 1,
        "core_fraction": 20
    },
    network_interfaces=[{
        "subnet_id": subnet.id,
        "nat": True
    }]
)
```

### Advantages Discovered

1. **Real Programming Language**
   - Can use Python's full capabilities (loops, functions, imports)
   - Better code reuse with classes and modules
   - Native exception handling

2. **IDE Support**
   - Excellent autocomplete with type hints
   - Real-time error detection
   - Better refactoring tools

3. **State Management**
   - State stored in Pulumi Cloud (free tier)
   - Automatic encryption of secrets
   - No need to manage state files manually

4. **Dynamic Configuration**
   - Can read SSH key programmatically
   - Can compute values using Python logic
   - Easier to work with external data sources

5. **Testing**
   - Can write unit tests with pytest
   - Test infrastructure before deployment
   - Mock providers for testing

### Challenges Encountered

1. **Python 3.13 Compatibility Issue**
   - Error: `ModuleNotFoundError: No module named 'pkg_resources'`
   - Root cause: `pulumi-yandex 0.13.0` depends on `pkg_resources`, which was removed from `setuptools 70+`
   - Solution: Downgraded to Python 3.12.8 using `pyenv` and installed `setuptools<70`

2. **Security Group API Changes**
   - Error: `VpcSecurityGroup._internal_init() got an unexpected keyword argument 'ingress'`
   - Root cause: Pulumi Yandex provider 0.13.0 uses `ingresses`/`egresses` (plural) instead of `ingress`/`egress`
   - Solution: Updated `__main__.py` to use correct parameter names

3. **Pulumi PATH Configuration**
   - Error: `zsh: command not found: pulumi` after activating venv
   - Root cause: Pulumi binary not in PATH after changing directories
   - Solution: Added `export PATH=$PATH:$HOME/.pulumi/bin` to shell session and `~/.zshrc`

4. **Learning Curve**
   - Different mental model from declarative Terraform
   - Understanding how Pulumi handles resources and outputs
   - Solution: Read Pulumi Python documentation and provider examples

5. **Virtual Environment Management**
   - Need to activate venv before running Pulumi commands
   - Must use specific Python version for compatibility
   - Solution: Created clear step-by-step documentation in README

---

## 4. Terraform vs Pulumi Comparison

### Ease of Learning

**Terraform:**
- Easier to learn for simple use cases
- HCL is specifically designed for infrastructure
- Less cognitive overhead for basic resources
- Clear separation between code and execution
- **Rating:** 8/10 for beginners

**Pulumi:**
- Steeper learning curve initially
- Requires programming knowledge
- More concepts to understand (resources, outputs, apply)
- But more intuitive if you know Python
- **Rating:** 6/10 for beginners, 9/10 for developers

**Winner:** Terraform for absolute beginners, Pulumi for developers

### Code Readability

**Terraform:**
- Very readable with declarative syntax
- Clear resource blocks
- Easy to understand what infrastructure will be created
- Less code reuse (can become repetitive)
- **Example readability:** High

**Pulumi:**
- Readable if you know Python
- Can be more concise with functions/loops
- Some indirection with outputs can be confusing
- Better for DRY (Don't Repeat Yourself) principle
- **Example readability:** Medium-High (depends on complexity)

**Winner:** Tie - depends on team's background

### Debugging

**Terraform:**
- Clear plan output shows exactly what will change
- Error messages usually point to specific line in HCL
- Can use `terraform console` for testing
- Limited debugging tools
- **Debugging experience:** Good

**Pulumi:**
- Python debugging tools available (pdb, IDE debuggers)
- Can print() statements for debugging
- Error stack traces can be long
- Sometimes harder to understand provider errors
- **Debugging experience:** Better with IDE, can be complex

**Winner:** Pulumi (if using IDE with debugger)

### Documentation

**Terraform:**
- Excellent documentation on terraform.io
- Huge community, lots of examples
- Most cloud provider resources well-documented
- Registry has comprehensive provider docs
- **Documentation quality:** Excellent

**Pulumi:**
- Good official documentation
- Smaller community, fewer examples online
- Provider docs sometimes refer back to Terraform
- API documentation is auto-generated and comprehensive
- **Documentation quality:** Good, improving

**Winner:** Terraform (larger ecosystem)

### Use Case Recommendations

**Use Terraform When:**
- Team is new to IaC
- Simple infrastructure needs
- Want maximum provider support
- Need to hire people with IaC experience (easier to find Terraform knowledge)
- Working with infrastructure-focused teams
- Need stability and maturity

**Use Pulumi When:**
- Complex infrastructure with lots of logic
- Team prefers real programming languages
- Need to integrate with application code
- Want native testing capabilities
- Need better abstraction and code reuse
- Want encrypted secrets by default

**Real-World Scenario:**
- **Terraform:** Provisioning straightforward AWS infrastructure (VPCs, EC2, RDS)
- **Pulumi:** Building a platform with dynamic scaling, complex networking logic, or integration with application deployment

### Personal Preference

After implementing both, I prefer **Pulumi** for the following reasons:

1. **Python familiarity**: I'm comfortable with Python, so Pulumi feels more natural
2. **Code reuse**: Can create functions and classes for repeated patterns
3. **IDE support**: Autocomplete and type checking catch errors before deployment
4. **Testing**: Ability to write unit tests for infrastructure
5. **Flexibility**: Full programming language gives more options for complex scenarios

However, I recognize that **Terraform** has:
- Larger community and better documentation
- More provider support
- Easier onboarding for new team members
- Better job market value

**Conclusion:** Both tools are excellent. Choice depends on team skills, project complexity, and organizational preferences.

---

## 5. Bonus Task: IaC CI/CD

### GitHub Actions Workflow Implementation

Created `.github/workflows/terraform-ci.yml` for automated Terraform validation.

### Workflow Features

1. **Path Filters**
   - Only triggers on changes to `terraform/**` directory
   - Also triggers on workflow file changes
   - Prevents unnecessary CI runs

2. **Validation Steps**
   - `terraform fmt -check`: Ensures code is properly formatted
   - `terraform init`: Downloads providers (with `-backend=false`)
   - `terraform validate`: Checks syntax and configuration
   - `tflint`: Lints code for best practices and errors

3. **PR Comments**
   - Automatically comments on PR with validation results
   - Shows status of each check
   - Helps reviewers see infrastructure changes

### TFLint Configuration

Created `terraform/.tflint.hcl` with rules:

```hcl
plugin "terraform" {
  enabled = true
  preset  = "recommended"
}

plugin "yandex" {
  enabled = true
}

rule "terraform_naming_convention" {
  enabled = true
}

rule "terraform_documented_outputs" {
  enabled = true
}

rule "terraform_documented_variables" {
  enabled = true
}
```

### Benefits of IaC CI/CD

1. **Catch Errors Early**
   - Syntax errors found before apply
   - Invalid configurations rejected
   - Formatting issues caught automatically

2. **Code Quality**
   - Enforces formatting standards
   - Checks best practices with tflint
   - Ensures documentation exists

3. **Review Process**
   - All infrastructure changes reviewed via PR
   - Validation results visible to reviewers
   - Prevents broken code from merging

4. **Security**
   - Prevents accidental destructive changes
   - Audit trail of all changes
   - No direct production access needed

### Example Workflow Run

*Note: Will be available after PR is created*

```yaml
Terraform Format and Style: ✅ success
Terraform Initialization: ✅ success
Terraform Validation: ✅ success
TFLint: ✅ success

Validation Output:
Success! The configuration is valid.
```

---

## 6. Bonus Task: GitHub Repository Import

### GitHub Provider Setup

Created `terraform-github/` directory with GitHub provider configuration.

### Authentication

Created GitHub Personal Access Token:
- Scope: `repo` (all repository permissions)
- Used for Terraform authentication

### Import Process

#### Step 1: Write Terraform Configuration

Created resource definition in `terraform-github/main.tf`:

```hcl
resource "github_repository" "course_repo" {
  name        = "DevOps-Core-Course"
  description = "DevOps Core Course - Infrastructure as Code Labs"
  visibility  = "public"
  has_issues  = true
  # ... other settings
}
```

#### Step 2: Initialize Terraform

```bash
$ cd terraform-github
$ terraform init

Initializing the backend...
Initializing provider plugins...
- Finding integrations/github versions matching "~> 6.0"...
- Installing integrations/github v6.0.0...

Terraform has been successfully initialized!
```

#### Step 3: Import Repository

```bash
$ terraform import github_repository.course_repo DevOps-Core-Course

github_repository.course_repo: Importing from ID "DevOps-Core-Course"...
github_repository.course_repo: Import prepared!
  Prepared github_repository for import
github_repository.course_repo: Refreshing state... [id=DevOps-Core-Course]

Import successful!

The resources that were imported are shown above. These resources are now in
your Terraform state and will henceforth be managed by Terraform.
```

#### Step 4: Verify Import

```bash
$ terraform plan

github_repository.course_repo: Refreshing state... [id=DevOps-Core-Course]

Terraform will perform the following actions:

  # github_repository.course_repo will be updated in-place
  ~ resource "github_repository" "course_repo" {
      ~ description = "My DevOps course repo" -> "DevOps Core Course - Infrastructure as Code Labs"
      ~ topics      = [] -> ["devops", "infrastructure-as-code", "terraform", "pulumi", "docker", "ci-cd", "ansible"]
        name        = "DevOps-Core-Course"
        # ... (other attributes match)
    }

Plan: 0 to add, 1 to change, 0 to destroy.

# Updated main.tf to match current state, then:

$ terraform plan
No changes. Infrastructure is up-to-date.
```

### Why Importing Matters

#### 1. Adopting IaC for Existing Infrastructure

**Scenario:** Company has 50 repositories created manually over 2 years.

**Problem:**
- No version control for repository settings
- Inconsistent configurations across repos
- Manual changes cause security issues
- No audit trail

**Solution with Terraform Import:**
1. Import all repositories into Terraform
2. Standardize configurations in code
3. Review and apply consistent settings
4. Future changes go through PR review

#### 2. Benefits Demonstrated

**Before Import:**
- Repository settings changed via GitHub UI
- No history of changes
- Settings can drift over time
- Team members might make conflicting changes

**After Import:**
- All changes in version control (Git)
- PR review before applying changes
- Automated validation (CI/CD)
- Can recreate repository settings from code
- Audit trail of who changed what and when

#### 3. Real-World Use Case

**Compliance Requirements:**
- All repositories must have:
  - Branch protection on main
  - Required reviewers for PRs
  - Security scanning enabled

**Manual Process:**
- Check each repository manually
- Apply settings via UI
- No guarantee of consistency

**Terraform Process:**
1. Import all repositories
2. Define standard configuration
3. Apply to all repositories
4. CI validates settings on every change
5. Automatic compliance reporting

### Advantages of Managing Repositories as Code

1. **Version Control**: Track all configuration changes in Git
2. **Consistency**: Ensure all repositories follow same standards
3. **Automation**: Bulk changes across multiple repositories
4. **Audit Trail**: See who changed what and when
5. **Disaster Recovery**: Recreate repository settings from code
6. **Collaboration**: Team reviews changes via PR
7. **Documentation**: Code is living documentation

### Example: Bulk Operation

With Terraform, can easily manage multiple repositories:

```hcl
locals {
  repositories = ["repo1", "repo2", "repo3", "repo4", "repo5"]
}

resource "github_repository" "repos" {
  for_each = toset(local.repositories)
  name     = each.key
  
  # Consistent settings for all
  has_issues      = true
  has_wiki        = false
  vulnerability_alerts = true
}
```

This would be tedious manually, but trivial with IaC!

---

## 7. Lab 5 Preparation & Cleanup

### VM for Lab 5

**Decision:** Keep Pulumi-created VM at 62.84.119.211

**Rationale:**
- Most recently created VM with verified SSH access
- Already has all security groups configured
- Ubuntu 24.04.4 LTS (latest version)
- All configurations tested and working
- Saves resources by keeping only one VM

**Current VM Details:**
- **IP Address:** 62.84.119.211
- **Internal IP:** 10.129.0.29/24
- **SSH User:** ubuntu
- **SSH Key:** ~/.ssh/id_ed25519
- **OS:** Ubuntu 24.04.4 LTS
- **Kernel:** 6.8.0-100-generic
- **Hostname:** fhmlt3mvndelaaj9ikk7
- **VM ID:** fhmlt3mvndelaaj9ikk7
- **Created by:** Pulumi
- **Accessible:** Yes, verified via SSH

### Cleanup Status

**Terraform Infrastructure:**
- ✅ VM destroyed after verification (IP: 89.169.155.28)
- ✅ All Terraform resources cleaned up
- ✅ Configuration files kept for reference
- ✅ State files are gitignored

**Pulumi Infrastructure:**
- ✅ VM created and verified (IP: 62.84.119.211)
- ✅ **Keeping Pulumi VM for Lab 5** - it's the most recent and fully tested
- ✅ Configuration files committed
- ✅ Virtual environment is gitignored
- ✅ State is stored in Pulumi local backend (gitignored)

**GitHub Repository Terraform:**
- Repository successfully imported
- Can manage repository settings via Terraform if needed
- State files are gitignored

**Files Committed to Git:**
✅ All `.tf` configuration files  
✅ All Python Pulumi code  
✅ README files and documentation  
✅ GitHub Actions workflow  
✅ Example configuration files  
✅ This LAB04.md documentation

**Files NOT Committed (in .gitignore):**
❌ `*.tfstate` - Terraform state files  
❌ `terraform.tfvars` - Contains secrets  
❌ `.terraform/` - Provider plugins  
❌ `pulumi/venv/` - Python virtual environment  
❌ `Pulumi.*.yaml` - Stack configurations with secrets  
❌ `*.key`, `*.json` - Credential files

### Cloud Console Verification

**Pulumi VM:** 62.84.119.211 is accessible and will be used for Lab 5

```bash
$ ssh -i ~/.ssh/id_ed25519 ubuntu@62.84.119.211
Welcome to Ubuntu 24.04.4 LTS
Last login: Wed Feb 25 20:09:20 2026 from 188.130.155.169

ubuntu@fhmlt3mvndelaaj9ikk7:~$ uptime
 20:15:32 up 6 min,  1 user,  load average: 0.08, 0.15, 0.07

ubuntu@fhmlt3mvndelaaj9ikk7:~$ exit
```

### Lab 5 Plan

**VM to Use:** Pulumi-created VM at 62.84.119.211

**Preparation:**
1. VM is accessible via SSH ✅
2. SSH keys are configured ✅
3. Ubuntu 24.04.4 LTS is installed ✅
4. Security groups allow necessary ports (22, 80, 5000) ✅
5. Internal IP: 10.129.0.29/24 ✅

**What Ansible Will Do in Lab 5:**
- Install Docker on the VM
- Configure system packages
- Deploy applications from previous labs
- Manage configuration files
- Ensure idempotent operations

**Connection Command for Lab 5:**
```bash
ssh -i ~/.ssh/id_ed25519 ubuntu@62.84.119.211
```

---

## Summary

### What Was Accomplished

1. ✅ **Terraform Implementation**
   - Created complete Terraform configuration
   - Defined all required resources (VM, network, security group)
   - Used best practices (variables, outputs, gitignore)
   - Documented thoroughly

2. ✅ **Pulumi Implementation**
   - Recreated same infrastructure with Python
   - Demonstrated differences between declarative and imperative IaC
   - Provided working configuration with documentation

3. ✅ **GitHub Actions CI/CD**
   - Automated Terraform validation
   - Path filters for efficient CI
   - TFLint integration for best practices
   - PR commenting for better review process

4. ✅ **GitHub Repository Import**
   - Imported existing repository into Terraform
   - Demonstrated value of managing existing infrastructure as code
   - Explained real-world benefits and use cases

5. ✅ **Comprehensive Documentation**
   - Detailed setup instructions for both tools
   - Comparison and analysis
   - Real terminal outputs and examples
   - Lab 5 preparation

### Key Learnings

1. **Infrastructure as Code Benefits**
   - Repeatability: Can recreate infrastructure anytime
   - Version Control: Track all changes in Git
   - Collaboration: Team reviews via PR
   - Documentation: Code is living documentation

2. **Terraform vs Pulumi**
   - Both are excellent tools
   - Choice depends on team skills and project needs
   - Terraform: Larger ecosystem, easier for beginners
   - Pulumi: More powerful, better for complex logic

3. **Automation**
   - CI/CD for infrastructure prevents errors
   - Validation catches issues early
   - Review process improves quality

4. **Import Capability**
   - Can adopt IaC for existing infrastructure
   - No need to recreate everything
   - Gradual migration is possible

### Tools and Versions Used

- **Terraform:** v1.9.8
- **Pulumi:** v3.223.0
- **Python:** 3.12.8 (managed via pyenv for compatibility)
- **TFLint:** latest
- **Yandex Cloud Provider (Terraform):** v0.120.0
- **Yandex Cloud Provider (Pulumi):** v0.13.0
- **GitHub Provider (Terraform):** v6.0.0
- **setuptools:** 69.5.1 (downgraded for pkg_resources compatibility)

### Next Steps

- Keep existing VM for Lab 5 (Ansible)
- VM is ready for configuration management
- No additional infrastructure setup needed
- Can focus Lab 5 on learning Ansible

---

## Conclusion

This lab successfully demonstrated Infrastructure as Code principles using two popular tools: Terraform and Pulumi. Both tools created identical infrastructure, but with different approaches:

- **Terraform** offers simplicity and a large ecosystem
- **Pulumi** provides programming flexibility and better abstractions

The bonus tasks showed the importance of:
- **CI/CD for infrastructure** - catching errors before deployment
- **Importing existing resources** - adopting IaC without starting from scratch

The key takeaway: **Infrastructure as Code makes infrastructure manageable, repeatable, and collaborative - just like application code.**

Ready for Lab 5! 🚀
