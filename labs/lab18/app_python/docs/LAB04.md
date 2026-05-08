# Lab 4 — Infrastructure as Code (Terraform)

## Teraform

### Cloud Provider Selection

For this lab, I selected **Yandex Cloud** as the cloud provider.

The main reasons for this choice were:

* Availability without requiring a credit card
* Free tier support for virtual machines
* Native Terraform provider support
* Fast provisioning in the `ru-central1-a` region
* Compatibility with future labs (Ansible in Lab 5)

Using Yandex Cloud allowed me to provision infrastructure programmatically without manual configuration via a graphical interface, which aligns with the Infrastructure as Code (IaC) paradigm.

### Cost

The infrastructure uses Yandex Cloud free-tier resources.

Total cost: $0

No paid resources were provisioned, and billing alerts were not triggered.

### Terraform Version Used

Terraform was installed using Homebrew on macOS:

```bash
gleb-pp@gleb-mac iu-devops-course % terraform version
Terraform v1.14.5
on darwin_arm64
```

### Terraform Project Structure

The Terraform configuration was implemented in a minimal structure suitable for a small lab project:

terraform/
├── main.tf — contains provider configuration and resource definitions
├── key.json — service account credentials (excluded from Git)
├── terraform.tfstate — local state file (excluded from Git)
└── terraform.tfstate.backup — state backup file

Sensitive files such as credentials and state files are excluded using `.gitignore`.

### Resources Created

The infrastructure was defined in the `terraform/` directory and includes the following resources:

| Resource Type     | Configuration                   |
| ----------------- | ------------------------------- |
| VM Instance       | 2 vCPU (20%), 1 GB RAM          |
| Boot Disk         | 10 GB HDD                       |
| Operating System  | Ubuntu 24.04 LTS                |
| Network           | Custom VPC Network              |
| Subnet            | 10.5.0.0/24                     |
| Security Group    | SSH (22), HTTP (80), App (5000) |
| Public IP Address | NAT enabled                     |
| Region            | ru-central1-a                   |

Firewall rules were configured to allow:

* SSH access (port 22)
* HTTP access (port 80)
* Custom application deployment (port 5000)

### Key Configuration Decisions

* The smallest free-tier VM configuration was selected to avoid costs  
* SSH authentication was configured using public key metadata  
* Security groups were restricted to only required ports (22, 80, 5000)  
* Local state storage was used for simplicity  
* Variables were kept minimal due to the small scope of the lab  


### Terraform Plan

```bash
gleb-pp@gleb-mac terraform-vm % terraform plan

Terraform used the selected providers to generate the following execution plan. Resource actions are indicated with the following
symbols:
  + create

Terraform will perform the following actions:

  # yandex_compute_instance.vm will be created
  + resource "yandex_compute_instance" "vm" {
      + created_at                = (known after apply)
      + folder_id                 = (known after apply)
      + fqdn                      = (known after apply)
      + gpu_cluster_id            = (known after apply)
      + hardware_generation       = (known after apply)
      + hostname                  = (known after apply)
      + id                        = (known after apply)
      + maintenance_grace_period  = (known after apply)
      + maintenance_policy        = (known after apply)
      + metadata                  = {
          + "ssh-keys" = "ubuntu:ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIG8joAWrULmQflRXNMaMWxT1JxZ41Wt78UKL8bUTmWNN gleb-pp@gleb-mac.local"
        }
      + name                      = "lab-vm"
      + network_acceleration_type = "standard"
      + platform_id               = "standard-v1"
      + status                    = (known after apply)
      + zone                      = (known after apply)

      + boot_disk {
          + auto_delete = true
          + device_name = (known after apply)
          + disk_id     = (known after apply)
          + mode        = (known after apply)

          + initialize_params {
              + block_size  = (known after apply)
              + description = (known after apply)
              + image_id    = "fd8b0l0h7h0l6n3qk1n7"
              + name        = (known after apply)
              + size        = 10
              + snapshot_id = (known after apply)
              + type        = "network-hdd"
            }
        }

      + metadata_options (known after apply)

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

      + placement_policy (known after apply)

      + resources {
          + core_fraction = 20
          + cores         = 2
          + memory        = 1
        }

      + scheduling_policy (known after apply)
    }

  # yandex_vpc_network.network will be created
  + resource "yandex_vpc_network" "network" {
      + created_at                = (known after apply)
      + default_security_group_id = (known after apply)
      + folder_id                 = (known after apply)
      + id                        = (known after apply)
      + labels                    = (known after apply)
      + name                      = "lab-network"
      + subnet_ids                = (known after apply)
    }

  # yandex_vpc_security_group.sg will be created
  + resource "yandex_vpc_security_group" "sg" {
      + created_at = (known after apply)
      + folder_id  = (known after apply)
      + id         = (known after apply)
      + labels     = (known after apply)
      + network_id = (known after apply)
      + status     = (known after apply)

      + egress (known after apply)

      + ingress {
          + from_port         = -1
          + id                = (known after apply)
          + labels            = (known after apply)
          + port              = 5000
          + protocol          = "TCP"
          + to_port           = -1
          + v4_cidr_blocks    = []
          + v6_cidr_blocks    = []
            # (3 unchanged attributes hidden)
        }
      + ingress {
          + from_port         = -1
          + id                = (known after apply)
          + labels            = (known after apply)
          + port              = 80
          + protocol          = "TCP"
          + to_port           = -1
          + v4_cidr_blocks    = []
          + v6_cidr_blocks    = []
            # (3 unchanged attributes hidden)
        }
      + ingress {
          + description       = "SSH"
          + from_port         = -1
          + id                = (known after apply)
          + labels            = (known after apply)
          + port              = 22
          + protocol          = "TCP"
          + to_port           = -1
          + v4_cidr_blocks    = [
              + "0.0.0.0/0",
            ]
          + v6_cidr_blocks    = []
            # (2 unchanged attributes hidden)
        }
    }

  # yandex_vpc_subnet.subnet will be created
  + resource "yandex_vpc_subnet" "subnet" {
      + created_at     = (known after apply)
      + folder_id      = (known after apply)
      + id             = (known after apply)
      + labels         = (known after apply)
      + name           = "lab-subnet"
      + network_id     = (known after apply)
      + v4_cidr_blocks = [
          + "10.5.0.0/24",
        ]
      + v6_cidr_blocks = (known after apply)
      + zone           = "ru-central1-a"
    }

Plan: 4 to add, 0 to change, 0 to destroy.

Changes to Outputs:
  + external_ip = (known after apply)

───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

Note: You didn't use the -out option to save this plan, so Terraform can't guarantee to take exactly these actions if you run
"terraform apply" now.
```

### Terraform Apply

```bash
gleb-pp@gleb-mac terraform-vm % terraform apply

Terraform used the selected providers to generate the following execution plan. Resource actions are indicated with the following
symbols:
  + create

Terraform will perform the following actions:

  # yandex_compute_instance.vm will be created
  + resource "yandex_compute_instance" "vm" {
      + created_at                = (known after apply)
      + folder_id                 = (known after apply)
      + fqdn                      = (known after apply)
      + gpu_cluster_id            = (known after apply)
      + hardware_generation       = (known after apply)
      + hostname                  = (known after apply)
      + id                        = (known after apply)
      + maintenance_grace_period  = (known after apply)
      + maintenance_policy        = (known after apply)
      + metadata                  = {
          + "ssh-keys" = "ubuntu:ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIG8joAWrULmQflRXNMaMWxT1JxZ41Wt78UKL8bUTmWNN gleb-pp@gleb-mac.local"
        }
      + name                      = "lab-vm"
      + network_acceleration_type = "standard"
      + platform_id               = "standard-v1"
      + status                    = (known after apply)
      + zone                      = (known after apply)

      + boot_disk {
          + auto_delete = true
          + device_name = (known after apply)
          + disk_id     = (known after apply)
          + mode        = (known after apply)

          + initialize_params {
              + block_size  = (known after apply)
              + description = (known after apply)
              + image_id    = "fd8b0l0h7h0l6n3qk1n7"
              + name        = (known after apply)
              + size        = 10
              + snapshot_id = (known after apply)
              + type        = "network-hdd"
            }
        }

      + metadata_options (known after apply)

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

      + placement_policy (known after apply)

      + resources {
          + core_fraction = 20
          + cores         = 2
          + memory        = 1
        }

      + scheduling_policy (known after apply)
    }

  # yandex_vpc_network.network will be created
  + resource "yandex_vpc_network" "network" {
      + created_at                = (known after apply)
      + default_security_group_id = (known after apply)
      + folder_id                 = (known after apply)
      + id                        = (known after apply)
      + labels                    = (known after apply)
      + name                      = "lab-network"
      + subnet_ids                = (known after apply)
    }

  # yandex_vpc_security_group.sg will be created
  + resource "yandex_vpc_security_group" "sg" {
      + created_at = (known after apply)
      + folder_id  = (known after apply)
      + id         = (known after apply)
      + labels     = (known after apply)
      + network_id = (known after apply)
      + status     = (known after apply)

      + egress (known after apply)

      + ingress {
          + from_port         = -1
          + id                = (known after apply)
          + labels            = (known after apply)
          + port              = 5000
          + protocol          = "TCP"
          + to_port           = -1
          + v4_cidr_blocks    = []
          + v6_cidr_blocks    = []
            # (3 unchanged attributes hidden)
        }
      + ingress {
          + from_port         = -1
          + id                = (known after apply)
          + labels            = (known after apply)
          + port              = 80
          + protocol          = "TCP"
          + to_port           = -1
          + v4_cidr_blocks    = []
          + v6_cidr_blocks    = []
            # (3 unchanged attributes hidden)
        }
      + ingress {
          + description       = "SSH"
          + from_port         = -1
          + id                = (known after apply)
          + labels            = (known after apply)
          + port              = 22
          + protocol          = "TCP"
          + to_port           = -1
          + v4_cidr_blocks    = [
              + "0.0.0.0/0",
            ]
          + v6_cidr_blocks    = []
            # (2 unchanged attributes hidden)
        }
    }

  # yandex_vpc_subnet.subnet will be created
  + resource "yandex_vpc_subnet" "subnet" {
      + created_at     = (known after apply)
      + folder_id      = (known after apply)
      + id             = (known after apply)
      + labels         = (known after apply)
      + name           = "lab-subnet"
      + network_id     = (known after apply)
      + v4_cidr_blocks = [
          + "10.5.0.0/24",
        ]
      + v6_cidr_blocks = (known after apply)
      + zone           = "ru-central1-a"
    }

Plan: 4 to add, 0 to change, 0 to destroy.

Changes to Outputs:
  + external_ip = (known after apply)

Do you want to perform these actions?
  Terraform will perform the actions described above.
  Only 'yes' will be accepted to approve.

  Enter a value: yes

yandex_vpc_security_group.sg: Modifying... [id=enpk7siq0ce4b6bfflsu]
yandex_vpc_security_group.sg: Modifications complete after 0s [id=enpk7siq0ce4b6bfflsu]
yandex_compute_instance.vm: Creating...
yandex_compute_instance.vm: Still creating... [00m10s elapsed]
yandex_compute_instance.vm: Still creating... [00m20s elapsed]
yandex_compute_instance.vm: Still creating... [00m30s elapsed]
yandex_compute_instance.vm: Still creating... [00m40s elapsed]
yandex_compute_instance.vm: Creation complete after 41s [id=fhmrtc3p18korjjkl2dv]

Apply complete! Resources: 1 added, 1 changed, 0 destroyed.

Outputs:

external_ip = "89.169.159.226"
```

### SSH Connection Command

```bash
gleb-pp@gleb-mac terraform-vm % ssh ubuntu@89.169.159.226
Welcome to Ubuntu 24.04.4 LTS (GNU/Linux 6.8.0-100-generic x86_64)

 * Documentation:  https://help.ubuntu.com
 * Management:     https://landscape.canonical.com
 * Support:        https://ubuntu.com/pro

 System information as of Thu Feb 19 17:37:01 UTC 2026

  System load:  0.28              Processes:             102
  Usage of /:   23.1% of 9.04GB   Users logged in:       0
  Memory usage: 17%               IPv4 address for eth0: 10.5.0.7
  Swap usage:   0%


Expanded Security Maintenance for Applications is not enabled.

0 updates can be applied immediately.

Enable ESM Apps to receive additional future security updates.
See https://ubuntu.com/esm or run: sudo pro status


Last login: Thu Feb 19 17:35:36 2026 from 31.56.27.152
To run a command as administrator (user "root"), use "sudo <command>".
See "man sudo_root" for details.

ubuntu@fhmrtc3p18korjjkl2dv:~$ 
```

Successful SSH connection confirms that:

* The VM was provisioned correctly
* Network and firewall rules were applied
* SSH public key was added via metadata
* Public IP address is reachable from the host machine

### Terraform VM Access Information

Public IP Address: 89.169.159.226

The VM was successfully accessed via SSH using key-based authentication.


### Challenges Encountered

Several challenges were encountered during Terraform setup:

* Configuring Yandex Cloud authentication using a service account key  
* Understanding how to properly configure metadata for SSH access  
* Identifying correct Ubuntu image parameters  
* Ensuring firewall rules allowed SSH connectivity  

All issues were resolved using official documentation.

### Security Best Practices

* Cloud credentials (`key.json`) were excluded using `.gitignore`
* Terraform state file (`terraform.tfstate`) was not committed to Git
* SSH access is managed via public key authentication
* Only required ports (22, 80, 5000) were opened


## Pulumi

### Pulumi Version Used

Pulumi was installed in a Python virtual environment using pip:

```bash
gleb-pp@gleb-mac pulumi % pulumi version
Pulumi v3.222.0
```

Python 3.14 in a virtual environment was used for project isolation.

### Pulumi Project and Stack

The Pulumi project was created in the `pulumi/` directory:

```bash
pulumi new python
# Project name: lab4
# Stack name: dev
```

The Pulumi program recreates the same infrastructure previously deployed with Terraform:

* VPC Network
* Subnet
* Security Group with SSH, HTTP, and custom port rules
* Ubuntu 24.04 LTS VM with 2 vCPU, 1 GB RAM, and 10 GB HDD
* Public IP assigned automatically

Secrets such as Yandex Cloud credentials are excluded using `.gitignore`.

### Pulumi Project Structure

The Pulumi project uses a Python-based structure:

pulumi/
├── __main__.py — infrastructure definition
├── requirements.txt — Python dependencies
├── Pulumi.yaml — project metadata
├── Pulumi.dev.yaml — stack configuration (excluded from Git)
└── key.json — service account credentials (excluded from Git)

Sensitive files are excluded using `.gitignore`.


### Terraform Destroy 

```bash
gleb-pp@gleb-mac terraform-vm % terraform destroy                                 
data.yandex_compute_image.ubuntu: Reading...
yandex_vpc_network.network: Refreshing state... [id=enp4b56quatjphoh79ds]
data.yandex_compute_image.ubuntu: Read complete after 0s [id=fd8lt661chfo5i13a40d]
yandex_vpc_subnet.subnet: Refreshing state... [id=e9bedklmpb2dkdbugpil]
yandex_vpc_security_group.sg: Refreshing state... [id=enpk7siq0ce4b6bfflsu]
yandex_compute_instance.vm: Refreshing state... [id=fhmrtc3p18korjjkl2dv]

Terraform used the selected providers to generate the following execution plan. Resource actions are indicated with the following
symbols:
  - destroy

Terraform will perform the following actions:

  # yandex_compute_instance.vm will be destroyed
  - resource "yandex_compute_instance" "vm" {
      - created_at                = "2026-02-19T17:33:50Z" -> null
      - folder_id                 = "b1gpo0jop248pel4prbo" -> null
      - fqdn                      = "fhmrtc3p18korjjkl2dv.auto.internal" -> null
      - hardware_generation       = [
          - {
              - generation2_features = []
              - legacy_features      = [
                  - {
                      - pci_topology = "PCI_TOPOLOGY_V2"
                    },
                ]
            },
        ] -> null
      - id                        = "fhmrtc3p18korjjkl2dv" -> null
      - labels                    = {} -> null
      - metadata                  = {
          - "ssh-keys" = "ubuntu:ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIG8joAWrULmQflRXNMaMWxT1JxZ41Wt78UKL8bUTmWNN gleb-pp@gleb-mac.local"
        } -> null
      - name                      = "lab-vm" -> null
      - network_acceleration_type = "standard" -> null
      - platform_id               = "standard-v1" -> null
      - status                    = "running" -> null
      - zone                      = "ru-central1-a" -> null
        # (5 unchanged attributes hidden)

      - boot_disk {
          - auto_delete = true -> null
          - device_name = "fhmku28p4qjtqfmhhugb" -> null
          - disk_id     = "fhmku28p4qjtqfmhhugb" -> null
          - mode        = "READ_WRITE" -> null

          - initialize_params {
              - block_size  = 4096 -> null
              - image_id    = "fd8lt661chfo5i13a40d" -> null
                name        = null
              - size        = 10 -> null
              - type        = "network-hdd" -> null
                # (3 unchanged attributes hidden)
            }
        }

      - metadata_options {
          - aws_v1_http_endpoint = 1 -> null
          - aws_v1_http_token    = 2 -> null
          - gce_http_endpoint    = 1 -> null
          - gce_http_token       = 1 -> null
        }

      - network_interface {
          - index              = 0 -> null
          - ip_address         = "10.5.0.7" -> null
          - ipv4               = true -> null
          - ipv6               = false -> null
          - mac_address        = "d0:0d:1b:eb:07:90" -> null
          - nat                = true -> null
          - nat_ip_address     = "89.169.159.226" -> null
          - nat_ip_version     = "IPV4" -> null
          - security_group_ids = [
              - "enpk7siq0ce4b6bfflsu",
            ] -> null
          - subnet_id          = "e9bedklmpb2dkdbugpil" -> null
            # (1 unchanged attribute hidden)
        }

      - placement_policy {
          - host_affinity_rules       = [] -> null
          - placement_group_partition = 0 -> null
            # (1 unchanged attribute hidden)
        }

      - resources {
          - core_fraction = 20 -> null
          - cores         = 2 -> null
          - gpus          = 0 -> null
          - memory        = 1 -> null
        }

      - scheduling_policy {
          - preemptible = false -> null
        }
    }

  # yandex_vpc_network.network will be destroyed
  - resource "yandex_vpc_network" "network" {
      - created_at                = "2026-02-19T17:31:04Z" -> null
      - default_security_group_id = "enpgggm5omkiq5o3d3pp" -> null
      - folder_id                 = "b1gpo0jop248pel4prbo" -> null
      - id                        = "enp4b56quatjphoh79ds" -> null
      - labels                    = {} -> null
      - name                      = "lab-network" -> null
      - subnet_ids                = [
          - "e9bedklmpb2dkdbugpil",
        ] -> null
        # (1 unchanged attribute hidden)
    }

  # yandex_vpc_security_group.sg will be destroyed
  - resource "yandex_vpc_security_group" "sg" {
      - created_at  = "2026-02-19T17:32:34Z" -> null
      - folder_id   = "b1gpo0jop248pel4prbo" -> null
      - id          = "enpk7siq0ce4b6bfflsu" -> null
      - labels      = {} -> null
      - name        = "lab-sg" -> null
      - network_id  = "enp4b56quatjphoh79ds" -> null
      - status      = "ACTIVE" -> null
        # (1 unchanged attribute hidden)

      - egress {
          - from_port         = -1 -> null
          - id                = "enptkvqehkegtsk6maji" -> null
          - labels            = {} -> null
          - port              = -1 -> null
          - protocol          = "ANY" -> null
          - to_port           = -1 -> null
          - v4_cidr_blocks    = [
              - "0.0.0.0/0",
            ] -> null
          - v6_cidr_blocks    = [] -> null
            # (3 unchanged attributes hidden)
        }

      - ingress {
          - description       = "APP" -> null
          - from_port         = -1 -> null
          - id                = "enp2eb4m3as8pl6p86dm" -> null
          - labels            = {} -> null
          - port              = 5000 -> null
          - protocol          = "TCP" -> null
          - to_port           = -1 -> null
          - v4_cidr_blocks    = [
              - "0.0.0.0/0",
            ] -> null
          - v6_cidr_blocks    = [] -> null
            # (2 unchanged attributes hidden)
        }
      - ingress {
          - description       = "HTTP" -> null
          - from_port         = -1 -> null
          - id                = "enpv9fc20cqfalfr1jnp" -> null
          - labels            = {} -> null
          - port              = 80 -> null
          - protocol          = "TCP" -> null
          - to_port           = -1 -> null
          - v4_cidr_blocks    = [
              - "0.0.0.0/0",
            ] -> null
          - v6_cidr_blocks    = [] -> null
            # (2 unchanged attributes hidden)
        }
      - ingress {
          - description       = "SSH" -> null
          - from_port         = -1 -> null
          - id                = "enptojpbsccua72r6rg6" -> null
          - labels            = {} -> null
          - port              = 22 -> null
          - protocol          = "TCP" -> null
          - to_port           = -1 -> null
          - v4_cidr_blocks    = [
              - "0.0.0.0/0",
            ] -> null
          - v6_cidr_blocks    = [] -> null
            # (2 unchanged attributes hidden)
        }
    }

  # yandex_vpc_subnet.subnet will be destroyed
  - resource "yandex_vpc_subnet" "subnet" {
      - created_at     = "2026-02-19T17:31:06Z" -> null
      - folder_id      = "b1gpo0jop248pel4prbo" -> null
      - id             = "e9bedklmpb2dkdbugpil" -> null
      - labels         = {} -> null
      - name           = "lab-subnet" -> null
      - network_id     = "enp4b56quatjphoh79ds" -> null
      - v4_cidr_blocks = [
          - "10.5.0.0/24",
        ] -> null
      - v6_cidr_blocks = [] -> null
      - zone           = "ru-central1-a" -> null
        # (2 unchanged attributes hidden)
    }

Plan: 0 to add, 0 to change, 4 to destroy.

Changes to Outputs:
  - external_ip = "89.169.159.226" -> null

Do you really want to destroy all resources?
  Terraform will destroy all your managed infrastructure, as shown above.
  There is no undo. Only 'yes' will be accepted to confirm.

  Enter a value: yes

yandex_compute_instance.vm: Destroying... [id=fhmrtc3p18korjjkl2dv]
yandex_compute_instance.vm: Still destroying... [id=fhmrtc3p18korjjkl2dv, 00m10s elapsed]
yandex_compute_instance.vm: Still destroying... [id=fhmrtc3p18korjjkl2dv, 00m20s elapsed]
yandex_compute_instance.vm: Still destroying... [id=fhmrtc3p18korjjkl2dv, 00m30s elapsed]
yandex_compute_instance.vm: Destruction complete after 32s
yandex_vpc_subnet.subnet: Destroying... [id=e9bedklmpb2dkdbugpil]
yandex_vpc_security_group.sg: Destroying... [id=enpk7siq0ce4b6bfflsu]
yandex_vpc_security_group.sg: Destruction complete after 1s
yandex_vpc_subnet.subnet: Destruction complete after 2s
yandex_vpc_network.network: Destroying... [id=enp4b56quatjphoh79ds]
yandex_vpc_network.network: Destruction complete after 1s

Destroy complete! Resources: 4 destroyed.
gleb-pp@gleb-mac terraform-vm % 
```

### Pulumi Preview

```bash
(venv) gleb-pp@gleb-mac pulumi % pulumi preview                                                    

Previewing update (dev)

View in Browser (Ctrl+O): https://app.pulumi.com/gleb-pp-org/lab4/dev/previews/90805c0a-06ed-47ba-8a3e-c20d804ea820

     Type                              Name      Plan       Info
     pulumi:pulumi:Stack               lab4-dev             
 ~   ├─ yandex:index:VpcSecurityGroup  lab-sg    update     [diff: ~egresses,ingresses]
 +   └─ yandex:index:ComputeInstance   lab-vm    create     

Outputs:
  + external_ip: [unknown]

Resources:
    + 1 to create
    ~ 1 to update
    2 changes. 3 unchanged
```

### Pulumi Up


```bash
(venv) gleb-pp@gleb-mac pulumi % pulumi up                                                         
Previewing update (dev)

View in Browser (Ctrl+O): https://app.pulumi.com/gleb-pp-org/lab4/dev/previews/4079d22a-3795-45be-acbc-35746570b681

     Type                              Name      Plan       Info
     pulumi:pulumi:Stack               lab4-dev             
 ~   ├─ yandex:index:VpcSecurityGroup  lab-sg    update     [diff: ~egresses,ingresses]
 +   └─ yandex:index:ComputeInstance   lab-vm    create     

Outputs:
  + external_ip: [unknown]

Resources:
    + 1 to create
    ~ 1 to update
    2 changes. 3 unchanged

Do you want to perform this update? yes
Updating (dev)

View in Browser (Ctrl+O): https://app.pulumi.com/gleb-pp-org/lab4/dev/updates/2

     Type                              Name      Status            Info
     pulumi:pulumi:Stack               lab4-dev                    
 ~   ├─ yandex:index:VpcSecurityGroup  lab-sg    updated (2s)      [diff: ~egresses,ingresses]
 +   └─ yandex:index:ComputeInstance   lab-vm    created (37s)     

Outputs:
  + external_ip: "89.169.147.14"

Resources:
    + 1 created
    ~ 1 updated
    2 changes. 3 unchanged

Duration: 42s
```

This confirms that the VM, networking, and firewall rules were applied correctly, and that SSH access works with the configured public key.

### SSH Connection Command

```bash
(venv) gleb-pp@gleb-mac pulumi % ssh ubuntu@89.169.147.14
Welcome to Ubuntu 24.04.3 LTS (GNU/Linux 6.8.0-90-generic x86_64)

 * Documentation:  https://help.ubuntu.com
 * Management:     https://landscape.canonical.com
 * Support:        https://ubuntu.com/pro

 System information as of Thu Feb 19 18:27:12 UTC 2026

  System load:  1.27              Processes:             101
  Usage of /:   23.1% of 9.04GB   Users logged in:       0
  Memory usage: 18%               IPv4 address for eth0: 10.5.0.25
  Swap usage:   0%


Expanded Security Maintenance for Applications is not enabled.

0 updates can be applied immediately.

Enable ESM Apps to receive additional future security updates.
See https://ubuntu.com/esm or run: sudo pro status


The list of available updates is more than a week old.
To check for new updates run: sudo apt update

Last login: Thu Feb 19 18:27:13 2026 from 31.56.27.152
To run a command as administrator (user "root"), use "sudo <command>".
See "man sudo_root" for details.

ubuntu@fhmgseufdef05soh8cgp:~$ 
```

### Challenges Encountered

During Pulumi implementation, several challenges occurred:

* Understanding Pulumi stack configuration concepts  
* Mapping Terraform resources to Pulumi SDK classes  
* Managing Python virtual environment dependencies  
* Learning how Pulumi handles implicit resource dependencies  

These challenges were resolved through official Pulumi documentation.

### Pulumi vs Terraform Comparison

**Ease of Learning:** The Pulumi approach was easier to learn because it uses a familiar programming language (Python) instead of a domain-specific language (HCL). This allowed for more intuitive development and debugging.

**Code Readability:** Pulumi's use of Python made the code more concise and easier to understand, especially for those with programming experience. Terraform's HCL can be more verbose and less flexible for complex logic.

**Debugging**: Pulumi's integration with Python's debugging tools made it easier to identify and fix issues. Terraform's debugging relies on interpreting error messages and state files, which can be less straightforward.

**Documentation:** Both Terraform and Pulumi have comprehensive documentation, but Pulumi's examples in Python were more relatable and easier to follow for me.

**Use Case:** I would use Terraform for simpler infrastructure provisioning tasks or when working in a team that prefers a declarative approach. Pulumi would be my choice for more complex scenarios that require programming logic, loops, and conditionals, or when I want to leverage existing programming skills.

### Lab 5 Preparation and Cleanup

**VM for Lab 5:**

I will keep the VM created with Pulumi for Lab 5, as it is already configured with the necessary resources and allows me to focus on Ansible without worrying about infrastructure provisioning.

The Terraform-managed infrastructure was fully destroyed using `terraform destroy`.

Only the Pulumi-managed VM remains active and will be used in Lab 5.


**Cleanup Status:**

```bash
gleb-pp@gleb-mac pulumi % pulumi stack
Current stack is dev:
    Owner: gleb-pp-org
    Last updated: 11 minutes ago (2026-02-19 21:26:19.790145 +0300 MSK)
    Pulumi version used: v3.222.0
Current stack resources (6):
    TYPE                                               NAME
    pulumi:pulumi:Stack                                lab4-dev
    ├─ yandex:index/vpcNetwork:VpcNetwork              lab-network
    ├─ yandex:index/vpcSubnet:VpcSubnet                lab-subnet
    ├─ yandex:index/vpcSecurityGroup:VpcSecurityGroup  lab-sg
    ├─ yandex:index/computeInstance:ComputeInstance    lab-vm
    └─ pulumi:providers:yandex                         default_0_13_0

Current stack outputs (1):
    OUTPUT       VALUE
    external_ip  89.169.147.14

More information at: https://app.pulumi.com/gleb-pp-org/lab4/dev

Use `pulumi stack select` to change stack; `pulumi stack ls` lists known ones
gleb-pp@gleb-mac pulumi % 
```
