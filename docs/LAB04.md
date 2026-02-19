# Lab 4 — Infrastructure as Code (Terraform & Pulumi)

## 1. Cloud Provider & Infrastructure

**Provider:** Yandex Cloud
**Rationale:** Free tier available, accessible in Russia, native Terraform/Pulumi providers.

**Instance:** standard-v2, 2 vCPU (20%), 2 GB RAM, 10 GB HDD
**Region/Zone:** ru-central1-a
**OS:** Ubuntu 24.04 LTS
**Cost:** $0 (free tier)

**Resources created:**
- VPC network (`lab4-network`)
- Subnet (`lab4-subnet`, 10.0.1.0/24)
- Security group (`lab4-sg`): SSH (22), HTTP (80), App (5000)
- Compute instance (`lab4-vm`) with public IP

## 2. Terraform Implementation

**Terraform version:** >= 1.9
**Provider:** yandex-cloud/yandex >= 0.129.0

### Project Structure

```
terraform/
├── main.tf          # Provider, data sources, resources
├── variables.tf     # Input variables with defaults
├── outputs.tf       # VM IP, SSH command
├── terraform.tfvars # Credentials (gitignored)
├── .gitignore
└── README.md
```

### Key Decisions
- Variables for all configurable values (cloud_id, folder_id, zone, SSH key path)
- Outputs for public IP and SSH connection command
- Security group with minimal required ports
- Ubuntu 24.04 LTS image via data source (always latest)

### Commands & Output

```bash
$ terraform init
Initializing the backend...
Initializing provider plugins...
- Reusing previous version of yandex-cloud/yandex from the dependency lock file
- Using previously-installed yandex-cloud/yandex v0.187.0

Terraform has been successfully initialized!

You may now begin working with Terraform. Try running "terraform plan" to see
any changes that are required for your infrastructure. All Terraform commands
should now work.

If you ever set or change modules or backend configuration for Terraform,
rerun this command to reinitialize your working directory. If you forget, other
commands will detect it and remind you to do so if necessary.
```

```bash
$ terraform plan
data.yandex_compute_image.ubuntu: Reading...
data.yandex_compute_image.ubuntu: Read complete after 1s [id=fd8q1krrgc5pncjckeht]

Terraform used the selected providers to generate the following execution plan. Resource actions are indicated with
the following symbols:
  + create

Terraform will perform the following actions:

  # yandex_compute_instance.lab_vm will be created
  + resource "yandex_compute_instance" "lab_vm" {
      + created_at                = (known after apply)
      + folder_id                 = (known after apply)
      + fqdn                      = (known after apply)
      + gpu_cluster_id            = (known after apply)
      + hardware_generation       = (known after apply)
      + hostname                  = (known after apply)
      + id                        = (known after apply)
      + labels                    = {
          + "env"     = "dev"
          + "project" = "devops-lab4"
        }
      + maintenance_grace_period  = (known after apply)
      + maintenance_policy        = (known after apply)
      + metadata                  = {
          + "ssh-keys" = <<-EOT
                ubuntu:ssh-rsa <redacted>
            EOT
        }
      + name                      = "lab4-vm"
      + network_acceleration_type = "standard"
      + platform_id               = "standard-v2"
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
              + image_id    = "fd8q1krrgc5pncjckeht"
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
          + memory        = 2
        }

      + scheduling_policy (known after apply)
    }

  # yandex_vpc_network.lab_network will be created
  + resource "yandex_vpc_network" "lab_network" {
      + created_at                = (known after apply)
      + default_security_group_id = (known after apply)
      + folder_id                 = (known after apply)
      + id                        = (known after apply)
      + labels                    = (known after apply)
      + name                      = "lab4-network"
      + subnet_ids                = (known after apply)
    }

  # yandex_vpc_security_group.lab_sg will be created
  + resource "yandex_vpc_security_group" "lab_sg" {
      + created_at = (known after apply)
      + folder_id  = (known after apply)
      + id         = (known after apply)
      + labels     = (known after apply)
      + name       = "lab4-sg"
      + network_id = (known after apply)
      + status     = (known after apply)

      + egress {
          + description       = "Allow all outbound traffic"
          + from_port         = -1
          + id                = (known after apply)
          + labels            = (known after apply)
          + port              = -1
          + protocol          = "ANY"
          + to_port           = -1
          + v4_cidr_blocks    = [
              + "0.0.0.0/0",
            ]
          + v6_cidr_blocks    = []
            # (2 unchanged attributes hidden)
        }

      + ingress {
          + description       = "App port for future deployment"
          + from_port         = -1
          + id                = (known after apply)
          + labels            = (known after apply)
          + port              = 5000
          + protocol          = "TCP"
          + to_port           = -1
          + v4_cidr_blocks    = [
              + "0.0.0.0/0",
            ]
          + v6_cidr_blocks    = []
            # (2 unchanged attributes hidden)
        }
      + ingress {
          + description       = "HTTP access"
          + from_port         = -1
          + id                = (known after apply)
          + labels            = (known after apply)
          + port              = 80
          + protocol          = "TCP"
          + to_port           = -1
          + v4_cidr_blocks    = [
              + "0.0.0.0/0",
            ]
          + v6_cidr_blocks    = []
            # (2 unchanged attributes hidden)
        }
      + ingress {
          + description       = "SSH access"
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

  # yandex_vpc_subnet.lab_subnet will be created
  + resource "yandex_vpc_subnet" "lab_subnet" {
      + created_at     = (known after apply)
      + folder_id      = (known after apply)
      + id             = (known after apply)
      + labels         = (known after apply)
      + name           = "lab4-subnet"
      + network_id     = (known after apply)
      + v4_cidr_blocks = [
          + "10.0.1.0/24",
        ]
      + v6_cidr_blocks = (known after apply)
      + zone           = "ru-central1-a"
    }

Plan: 4 to add, 0 to change, 0 to destroy.

Changes to Outputs:
  + ssh_connection = (known after apply)
  + subnet_id      = (known after apply)
  + vm_name        = "lab4-vm"
  + vm_public_ip   = (known after apply)

───────────────────────────────────────────────────────────────────────────────────────────────────────────────────

Note: You didn't use the -out option to save this plan, so Terraform can't guarantee to take exactly these actions
if you run "terraform apply" now.
```

```bash
$ terraform apply
data.yandex_compute_image.ubuntu: Reading...
data.yandex_compute_image.ubuntu: Read complete after 1s [id=fd8q1krrgc5pncjckeht]

Terraform used the selected providers to generate the following execution plan. Resource actions are indicated with the following symbols:
  + create

Terraform will perform the following actions:

  # yandex_compute_instance.lab_vm will be created
  + resource "yandex_compute_instance" "lab_vm" {
      + created_at                = (known after apply)
      + folder_id                 = (known after apply)
      + fqdn                      = (known after apply)
      + gpu_cluster_id            = (known after apply)
      + hardware_generation       = (known after apply)
      + hostname                  = (known after apply)
      + id                        = (known after apply)
      + labels                    = {
          + "env"     = "dev"
          + "project" = "devops-lab4"
        }
      + maintenance_grace_period  = (known after apply)
      + maintenance_policy        = (known after apply)
      + metadata                  = {
          + "ssh-keys" = <<-EOT
                ubuntu:ssh-rsa <redacted>
            EOT
        }
      + name                      = "lab4-vm"
      + network_acceleration_type = "standard"
      + platform_id               = "standard-v2"
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
              + image_id    = "fd8q1krrgc5pncjckeht"
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
          + memory        = 2
        }

      + scheduling_policy (known after apply)
    }

  # yandex_vpc_network.lab_network will be created
  + resource "yandex_vpc_network" "lab_network" {
      + created_at                = (known after apply)
      + default_security_group_id = (known after apply)
      + folder_id                 = (known after apply)
      + id                        = (known after apply)
      + labels                    = (known after apply)
      + name                      = "lab4-network"
      + subnet_ids                = (known after apply)
    }

  # yandex_vpc_security_group.lab_sg will be created
  + resource "yandex_vpc_security_group" "lab_sg" {
      + created_at = (known after apply)
      + folder_id  = (known after apply)
      + id         = (known after apply)
      + labels     = (known after apply)
      + name       = "lab4-sg"
      + network_id = (known after apply)
      + status     = (known after apply)

      + egress {
          + description       = "Allow all outbound traffic"
          + from_port         = -1
          + id                = (known after apply)
          + labels            = (known after apply)
          + port              = -1
          + protocol          = "ANY"
          + to_port           = -1
          + v4_cidr_blocks    = [
              + "0.0.0.0/0",
            ]
          + v6_cidr_blocks    = []
            # (2 unchanged attributes hidden)
        }

      + ingress {
          + description       = "App port for future deployment"
          + from_port         = -1
          + id                = (known after apply)
          + labels            = (known after apply)
          + port              = 5000
          + protocol          = "TCP"
          + to_port           = -1
          + v4_cidr_blocks    = [
              + "0.0.0.0/0",
            ]
          + v6_cidr_blocks    = []
            # (2 unchanged attributes hidden)
        }
      + ingress {
          + description       = "HTTP access"
          + from_port         = -1
          + id                = (known after apply)
          + labels            = (known after apply)
          + port              = 80
          + protocol          = "TCP"
          + to_port           = -1
          + v4_cidr_blocks    = [
              + "0.0.0.0/0",
            ]
          + v6_cidr_blocks    = []
            # (2 unchanged attributes hidden)
        }
      + ingress {
          + description       = "SSH access"
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

  # yandex_vpc_subnet.lab_subnet will be created
  + resource "yandex_vpc_subnet" "lab_subnet" {
      + created_at     = (known after apply)
      + folder_id      = (known after apply)
      + id             = (known after apply)
      + labels         = (known after apply)
      + name           = "lab4-subnet"
      + network_id     = (known after apply)
      + v4_cidr_blocks = [
          + "10.0.1.0/24",
        ]
      + v6_cidr_blocks = (known after apply)
      + zone           = "ru-central1-a"
    }

Plan: 4 to add, 0 to change, 0 to destroy.

Changes to Outputs:
  + ssh_connection = (known after apply)
  + subnet_id      = (known after apply)
  + vm_name        = "lab4-vm"
  + vm_public_ip   = (known after apply)

Do you want to perform these actions?
  Terraform will perform the actions described above.
  Only 'yes' will be accepted to approve.

  Enter a value: yes

yandex_vpc_network.lab_network: Creating...
yandex_vpc_network.lab_network: Creation complete after 4s [id=enpi6c3bfshidl78ktg2]
yandex_vpc_subnet.lab_subnet: Creating...
yandex_vpc_security_group.lab_sg: Creating...
yandex_vpc_subnet.lab_subnet: Creation complete after 2s [id=e9br16rup649vajlpgek]
yandex_vpc_security_group.lab_sg: Creation complete after 3s [id=enpf49kg6q044fohi36p]
yandex_compute_instance.lab_vm: Creating...
yandex_compute_instance.lab_vm: Still creating... [00m10s elapsed]
yandex_compute_instance.lab_vm: Still creating... [00m20s elapsed]
yandex_compute_instance.lab_vm: Still creating... [00m30s elapsed]
yandex_compute_instance.lab_vm: Still creating... [00m40s elapsed]
yandex_compute_instance.lab_vm: Still creating... [00m50s elapsed]
yandex_compute_instance.lab_vm: Creation complete after 50s [id=fhml2snm9o8irug0ve7r]

Apply complete! Resources: 4 added, 0 changed, 0 destroyed.

Outputs:

ssh_connection = "ssh ubuntu@84.252.131.210"
subnet_id = "e9br16rup649vajlpgek"
vm_name = "lab4-vm"
vm_public_ip = "84.252.131.210"
```

```bash
$ ssh ubuntu@84.252.131.210
Welcome to Ubuntu 24.04.4 LTS (GNU/Linux 6.8.0-100-generic x86_64)

 * Documentation:  https://help.ubuntu.com
 * Management:     https://landscape.canonical.com
 * Support:        https://ubuntu.com/pro

 System information as of Thu Feb 19 10:00:40 UTC 2026

  System load:  0.0               Processes:             102
  Usage of /:   23.3% of 9.04GB   Users logged in:       1
  Memory usage: 9%                IPv4 address for eth0: 10.0.1.6
  Swap usage:   0%


Expanded Security Maintenance for Applications is not enabled.

0 updates can be applied immediately.

Enable ESM Apps to receive additional future security updates.
See https://ubuntu.com/esm or run: sudo pro status


Last login: Thu Feb 19 09:48:13 2026 from <redacted>
To run a command as administrator (user "root"), use "sudo <command>".
See "man sudo_root" for details.

ubuntu@fhml2snm9o8irug0ve7r:~$ hostname
fhml2snm9o8irug0ve7r
ubuntu@fhml2snm9o8irug0ve7r:~$ exit
logout
Connection to 84.252.131.210 closed.
```

### Challenges
- Yandex Cloud service account setup requires correct IAM roles (editor on folder).
- The `ubuntu-2404-lts-oslogin` image family may change — using data source ensures latest.

## 3. Pulumi Implementation

**Pulumi version:** >= 3.x
**Language:** Python
**Provider:** pulumi-yandex

### How Code Differs from Terraform
- Python instead of HCL — full language features (variables, functions, string formatting).
- Resources are objects with constructors, not declarative blocks.
- Configuration via `pulumi.Config()` instead of `.tfvars`.
- Outputs via `pulumi.export()`.

### Commands & Output

```bash
$ terraform destroy
yandex_vpc_network.lab_network: Refreshing state... [id=enpi6c3bfshidl78ktg2]
data.yandex_compute_image.ubuntu: Reading...
data.yandex_compute_image.ubuntu: Read complete after 1s [id=fd8q1krrgc5pncjckeht]
yandex_vpc_subnet.lab_subnet: Refreshing state... [id=e9br16rup649vajlpgek]
yandex_vpc_security_group.lab_sg: Refreshing state... [id=enpf49kg6q044fohi36p]
yandex_compute_instance.lab_vm: Refreshing state... [id=fhml2snm9o8irug0ve7r]

Terraform used the selected providers to generate the following execution plan. Resource actions are indicated with the following symbols:
  - destroy

Terraform will perform the following actions:

  # yandex_compute_instance.lab_vm will be destroyed
  - resource "yandex_compute_instance" "lab_vm" {
      - created_at                = "2026-02-19T09:45:08Z" -> null
      - folder_id                 = "<folder_id>" -> null
      - fqdn                      = "fhml2snm9o8irug0ve7r.auto.internal" -> null
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
      - id                        = "fhml2snm9o8irug0ve7r" -> null
      - labels                    = {
          - "env"     = "dev"
          - "project" = "devops-lab4"
        } -> null
      - metadata                  = {
          - "ssh-keys" = <<-EOT
                ubuntu:ssh-rsa <redacted>
            EOT
        } -> null
      - name                      = "lab4-vm" -> null
      - network_acceleration_type = "standard" -> null
      - platform_id               = "standard-v2" -> null
      - status                    = "running" -> null
      - zone                      = "ru-central1-a" -> null
        # (5 unchanged attributes hidden)

      - boot_disk {
          - auto_delete = true -> null
          - device_name = "fhm48v39li8l0is95gdb" -> null
          - disk_id     = "fhm48v39li8l0is95gdb" -> null
          - mode        = "READ_WRITE" -> null

          - initialize_params {
              - block_size  = 4096 -> null
              - image_id    = "fd8q1krrgc5pncjckeht" -> null
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
          - ip_address         = "10.0.1.6" -> null
          - ipv4               = true -> null
          - ipv6               = false -> null
          - mac_address        = "d0:0d:15:17:2f:64" -> null
          - nat                = true -> null
          - nat_ip_address     = "84.252.131.210" -> null
          - nat_ip_version     = "IPV4" -> null
          - security_group_ids = [
              - "enpf49kg6q044fohi36p",
            ] -> null
          - subnet_id          = "e9br16rup649vajlpgek" -> null
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
          - memory        = 2 -> null
        }

      - scheduling_policy {
          - preemptible = false -> null
        }
    }

  # yandex_vpc_network.lab_network will be destroyed
  - resource "yandex_vpc_network" "lab_network" {
      - created_at                = "2026-02-19T09:45:01Z" -> null
      - default_security_group_id = "enpsi4e397r5ao482dmi" -> null
      - folder_id                 = "<folder_id>" -> null
      - id                        = "enpi6c3bfshidl78ktg2" -> null
      - labels                    = {} -> null
      - name                      = "lab4-network" -> null
      - subnet_ids                = [
          - "e9br16rup649vajlpgek",
        ] -> null
        # (1 unchanged attribute hidden)
    }

  # yandex_vpc_security_group.lab_sg will be destroyed
  - resource "yandex_vpc_security_group" "lab_sg" {
      - created_at  = "2026-02-19T09:45:06Z" -> null
      - folder_id   = "<folder_id>" -> null
      - id          = "enpf49kg6q044fohi36p" -> null
      - labels      = {} -> null
      - name        = "lab4-sg" -> null
      - network_id  = "enpi6c3bfshidl78ktg2" -> null
      - status      = "ACTIVE" -> null
        # (1 unchanged attribute hidden)

      - egress {
          - description       = "Allow all outbound traffic" -> null
          - from_port         = -1 -> null
          - id                = "enpbret8gb2ipr32h836" -> null
          - labels            = {} -> null
          - port              = -1 -> null
          - protocol          = "ANY" -> null
          - to_port           = -1 -> null
          - v4_cidr_blocks    = [
              - "0.0.0.0/0",
            ] -> null
          - v6_cidr_blocks    = [] -> null
            # (2 unchanged attributes hidden)
        }

      - ingress {
          - description       = "App port for future deployment" -> null
          - from_port         = -1 -> null
          - id                = "enpe0ptu3evfkp5ook4d" -> null
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
          - description       = "HTTP access" -> null
          - from_port         = -1 -> null
          - id                = "enp14thpr9a2qfd1737n" -> null
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
          - description       = "SSH access" -> null
          - from_port         = -1 -> null
          - id                = "enppv8qhcr12i4jv2klu" -> null
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

  # yandex_vpc_subnet.lab_subnet will be destroyed
  - resource "yandex_vpc_subnet" "lab_subnet" {
      - created_at     = "2026-02-19T09:45:05Z" -> null
      - folder_id      = "<folder_id>" -> null
      - id             = "e9br16rup649vajlpgek" -> null
      - labels         = {} -> null
      - name           = "lab4-subnet" -> null
      - network_id     = "enpi6c3bfshidl78ktg2" -> null
      - v4_cidr_blocks = [
          - "10.0.1.0/24",
        ] -> null
      - v6_cidr_blocks = [] -> null
      - zone           = "ru-central1-a" -> null
        # (2 unchanged attributes hidden)
    }

Plan: 0 to add, 0 to change, 4 to destroy.

Changes to Outputs:
  - ssh_connection = "ssh ubuntu@84.252.131.210" -> null
  - subnet_id      = "e9br16rup649vajlpgek" -> null
  - vm_name        = "lab4-vm" -> null
  - vm_public_ip   = "84.252.131.210" -> null

Do you really want to destroy all resources?
  Terraform will destroy all your managed infrastructure, as shown above.
  There is no undo. Only 'yes' will be accepted to confirm.

  Enter a value: yes

yandex_compute_instance.lab_vm: Destroying... [id=fhml2snm9o8irug0ve7r]
yandex_compute_instance.lab_vm: Still destroying... [id=fhml2snm9o8irug0ve7r, 00m10s elapsed]
yandex_compute_instance.lab_vm: Still destroying... [id=fhml2snm9o8irug0ve7r, 00m20s elapsed]
yandex_compute_instance.lab_vm: Still destroying... [id=fhml2snm9o8irug0ve7r, 00m30s elapsed]
yandex_compute_instance.lab_vm: Still destroying... [id=fhml2snm9o8irug0ve7r, 00m40s elapsed]
yandex_compute_instance.lab_vm: Still destroying... [id=fhml2snm9o8irug0ve7r, 00m50s elapsed]
yandex_compute_instance.lab_vm: Still destroying... [id=fhml2snm9o8irug0ve7r, 01m00s elapsed]
yandex_compute_instance.lab_vm: Still destroying... [id=fhml2snm9o8irug0ve7r, 01m10s elapsed]
yandex_compute_instance.lab_vm: Destruction complete after 1m13s
yandex_vpc_subnet.lab_subnet: Destroying... [id=e9br16rup649vajlpgek]
yandex_vpc_security_group.lab_sg: Destroying... [id=enpf49kg6q044fohi36p]
yandex_vpc_security_group.lab_sg: Destruction complete after 1s
yandex_vpc_subnet.lab_subnet: Destruction complete after 2s
yandex_vpc_network.lab_network: Destroying... [id=enpi6c3bfshidl78ktg2]
yandex_vpc_network.lab_network: Destruction complete after 1s

Destroy complete! Resources: 4 destroyed.
```

```bash
$ pulumi preview
Previewing update (dev):
     Type                              Name             Plan       
 +   pulumi:pulumi:Stack               lab4-pulumi-dev  create     
 +   ├─ yandex:index:VpcNetwork        lab4-network     create     
 +   ├─ yandex:index:VpcSecurityGroup  lab4-sg          create     
 +   ├─ yandex:index:ComputeInstance   lab4-vm          create     
 +   └─ yandex:index:VpcSubnet         lab4-subnet      create     

Outputs:
    ssh_connection: [unknown]
    vm_name       : "lab4-vm-47c9e72"
    vm_public_ip  : [unknown]

Resources:
    + 5 to create
```

```bash
$ pulumi up
Previewing update (dev):
     Type                              Name             Plan       
 +   pulumi:pulumi:Stack               lab4-pulumi-dev  create     
 +   ├─ yandex:index:VpcNetwork        lab4-network     create     
 +   ├─ yandex:index:VpcSubnet         lab4-subnet      create     
 +   ├─ yandex:index:VpcSecurityGroup  lab4-sg          create     
 +   └─ yandex:index:ComputeInstance   lab4-vm          create     

Outputs:
    ssh_connection: [unknown]
    vm_name       : "lab4-vm-1d021b7"
    vm_public_ip  : [unknown]

Resources:
    + 5 to create

Do you want to perform this update? yes
Updating (dev):
     Type                              Name             Status              
 +   pulumi:pulumi:Stack               lab4-pulumi-dev  created (56s)       
 +   ├─ yandex:index:VpcNetwork        lab4-network     created (3s)        
 +   ├─ yandex:index:VpcSubnet         lab4-subnet      created (0.92s)     
 +   ├─ yandex:index:VpcSecurityGroup  lab4-sg          created (3s)        
 +   └─ yandex:index:ComputeInstance   lab4-vm          created (47s)       

Outputs:
    ssh_connection: "ssh ubuntu@93.77.177.175"
    vm_name       : "lab4-vm-68284ec"
    vm_public_ip  : "93.77.177.175"

Resources:
    + 5 created

Duration: 57s
```

```bash
$ ssh ubuntu@93.77.177.175
The authenticity of host '93.77.177.175 (93.77.177.175)' can't be established.
ED25519 key fingerprint is: SHA256:fLD63x2OFBExJCvxeq5+BwDuogdgCcuEqzxs/9Wf+NE
This key is not known by any other names.
Are you sure you want to continue connecting (yes/no/[fingerprint])? yes
Warning: Permanently added '93.77.177.175' (ED25519) to the list of known hosts.
Welcome to Ubuntu 24.04.4 LTS (GNU/Linux 6.8.0-100-generic x86_64)

 * Documentation:  https://help.ubuntu.com
 * Management:     https://landscape.canonical.com
 * Support:        https://ubuntu.com/pro

 System information as of Thu Feb 19 10:23:25 UTC 2026

  System load:  0.63              Processes:             101
  Usage of /:   22.1% of 9.04GB   Users logged in:       0
  Memory usage: 9%                IPv4 address for eth0: 10.0.1.20
  Swap usage:   0%


Expanded Security Maintenance for Applications is not enabled.

0 updates can be applied immediately.

Enable ESM Apps to receive additional future security updates.
See https://ubuntu.com/esm or run: sudo pro status



The programs included with the Ubuntu system are free software;
the exact distribution terms for each program are described in the
individual files in /usr/share/doc/*/copyright.

Ubuntu comes with ABSOLUTELY NO WARRANTY, to the extent permitted by
applicable law.

To run a command as administrator (user "root"), use "sudo <command>".
See "man sudo_root" for details.

ubuntu@fhmiam82ij31aj2r282u:~$ hostname
fhmiam82ij31aj2r282u
ubuntu@fhmiam82ij31aj2r282u:~$ exit
logout
Connection to 93.77.177.175 closed.
```

### Advantages
- IDE autocomplete and type checking for resource arguments.
- Native Python logic for dynamic values (e.g., reading SSH key from file).
- Secrets encrypted by default in Pulumi state.

### Challenges
- `pulumi-yandex` documentation is sparser than the Terraform provider's.
- Requires Python virtual environment management.

## 4. Terraform vs Pulumi Comparison

**Code differences (HCL vs Python):** Terraform uses HCL — a declarative DSL with blocks and expressions. Pulumi uses a general-purpose language (here, Python): resources are object constructors, config is `pulumi.Config()`, and you get full language features (loops, file I/O, string formatting). The same infrastructure is expressed as declarations (Terraform) vs imperative code (Pulumi).

**Ease of Learning:** Terraform is simpler to start with — HCL is straightforward and the docs are excellent. Pulumi requires knowing both the IaC concepts and a programming language.

**Code Readability:** For small infra, Terraform's declarative blocks are cleaner. Pulumi shines when you need conditionals, loops, or complex logic.

**Debugging:** Terraform errors are clear with line numbers in HCL. Pulumi errors mix Python tracebacks with infrastructure errors, which can be confusing.

**Documentation:** Terraform has far better docs and community examples. Pulumi's Yandex provider docs are minimal.

**Use Case:** Terraform for standard infrastructure with clear resource definitions. Pulumi when you need dynamic configurations or want to share logic between infra and app code.

**Which tool I prefer and why:** For standard infrastructure like this lab, I prefer Terraform: simpler setup, no venv, better documentation and plan output. I would choose Pulumi when the project needs a lot of logic, reuse from app code, or type safety in a familiar language.

## 5. Lab 5 Preparation & Cleanup

**Recommendation:** Since Lab 5 is planned for the next few days, it is better to **keep one VM** and not destroy everything. That way you do not need to bring the infrastructure back up (terraform apply / pulumi up) and wait for VM creation when starting Lab 5 — you can connect via SSH and start working right away. The other stack (Terraform or Pulumi) should be destroyed so you do not pay for two VMs and avoid confusion about which one to use.

**VM for Lab 5:**
- **Are you keeping your VM for Lab 5?** Yes.
- **If yes: Which VM (Terraform or Pulumi created)?** Pulumi-created VM (`lab4-vm-...`). Terraform stack already destroyed.
- **If no:** — (not applicable)

**Cleanup status:**
- Terraform: all resources destroyed via `terraform destroy` (in the `terraform/` directory).
- Pulumi: VM kept running for Lab 5, accessible via SSH.
- No secrets or keys committed; state and credentials are in `.gitignore`.

**Commands used and useful before Lab 5:**

1. **Destroy Terraform only (keep Pulumi VM):**
   ```bash
   cd terraform
   terraform destroy   # confirm with yes
   ```

2. **Verify Pulumi VM is still running and accessible (before starting Lab 5):**
   ```bash
   cd pulumi
   pulumi stack output ssh_connection   # e.g. "ssh ubuntu@93.77.177.175"
   pulumi stack output vm_public_ip     # VM public IP
   ssh ubuntu@<vm_public_ip>            # connect (replace with IP from output)
   # on the VM: hostname; exit
   ```

3. **When finished with all labs and want to destroy Pulumi resources too:**
   ```bash
   cd pulumi
   pulumi destroy   # confirm with yes
   ```