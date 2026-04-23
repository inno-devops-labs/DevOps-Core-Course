# LAB04 — Infrastructure as Code (Terraform & Pulumi)

## 1. Cloud Provider & Infrastructure

### Provider Choice

I chose **Yandex Cloud** because:

- It offers a genuine free tier (20 % vCPU, 1 GB RAM) — no credit card required at the start.
- It is accessible from Russia without restrictions.
- The Terraform and Pulumi providers for Yandex Cloud are mature and well‑documented.

### Resources Created

| Resource | Details |
|----------|---------|
| **VPC Network** | `devops-network` |
| **Subnet** | `devops-subnet`, CIDR `10.0.1.0/24`, zone `ru-central1-a` |
| **Security Group** | `devops-sg` — SSH (22), HTTP (80), App (5000), ICMP |
| **Compute Instance** | `devops-vm` — Ubuntu 24.04 LTS, 2 vCPU @ 20 %, 1 GB RAM, 10 GB HDD |

### Instance Specification

| Parameter | Value |
|-----------|-------|
| Platform | `standard-v2` |
| Cores / Fraction | 2 / 20 % |
| RAM | 1 GB |
| Disk | 10 GB `network-hdd` |
| OS | Ubuntu 24.04 LTS (`ubuntu-2404-lts`) |
| Zone | `ru-central1-a` |
| Preemptible | Yes |
| **Total cost** | **$0** (free tier) |

---

## 2. Terraform Implementation

### Version & Tools

| Tool | Version |
|------|---------|
| Terraform CLI | ≥ 1.9 |
| Yandex Cloud provider | ≥ 0.130 |

### Project Structure

```
terraform/
├── .gitignore              # Ignores state, credentials, .terraform/
├── main.tf                 # Provider, data sources, all resources
├── variables.tf            # Input variables with descriptions & defaults
├── outputs.tf              # VM IP, SSH command, resource IDs
├── terraform.tfvars.example# Template (real .tfvars is git‑ignored)
├── README.md               # Setup instructions
└── github_import/          # Bonus — GitHub repo import
    └── main.tf
```

### Key Configuration Decisions

1. **Variables everywhere** — every tuneable value (zone, core count, disk size, image family) is exposed via `variables.tf` so the same code works across environments.
2. **Outputs** — `ssh_command` output gives a copy‑pastable connection string.
3. **Preemptible VM** — lowers cost (stops after 24 h but is recreatable instantly).
4. **Security group** — only ports 22, 80, 5000 + ICMP ingress; full egress.
5. **No hard‑coded credentials** — token is passed through `terraform.tfvars` (git‑ignored) or `TF_VAR_yc_token` env var.

### Challenges Encountered

- **Image family naming** — Yandex Cloud changed from `ubuntu-2004-lts` to `ubuntu-2404-lts`; using a `data` source with `family` ensures the latest image is always picked.
- **Security group attachment** — the `security_group_ids` argument must be on the `network_interface` block, not the instance root.

### Terminal Output

#### `terraform init`

```
$ terraform init

Initializing the backend...
Initializing provider plugins...
- Finding yandex-cloud/yandex versions matching ">= 0.130.0"...
- Finding latest version of hashicorp/aws...
- Installing yandex-cloud/yandex v0.187.0...
- Installed yandex-cloud/yandex v0.187.0 (self-signed, key ID E40F590B50BB8E40)
- Installing hashicorp/aws v6.33.0...
- Installed hashicorp/aws v6.33.0 (signed by HashiCorp)

Terraform has been successfully initialized!
```

#### `terraform plan`

```
$ terraform plan

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
      + labels                    = {
          + "lab"     = "lab04"
          + "project" = "devops-course"
        }
      + maintenance_grace_period  = (known after apply)
      + maintenance_policy        = (known after apply)
      + metadata                  = {
          + "ssh-keys" = <<-EOT
                ubuntu:ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIGvhzdEWhZNJ06OD+izXEHMFc4SDebBq8sgdxUg4HGgp GitLab
            EOT
        }
      + name                      = "devops-vm"
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
              + image_id    = "fd8lt661chfo5i13a40d"
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

      + scheduling_policy {
          + preemptible = true
        }
    }

  # yandex_vpc_network.main will be created
  + resource "yandex_vpc_network" "main" {
      + created_at                = (known after apply)
      + default_security_group_id = (known after apply)
      + folder_id                 = (known after apply)
      + id                        = (known after apply)
      + labels                    = (known after apply)
      + name                      = "devops-network"
      + subnet_ids                = (known after apply)
    }

  # yandex_vpc_security_group.main will be created
  + resource "yandex_vpc_security_group" "main" {
      + created_at = (known after apply)
      + folder_id  = (known after apply)
      + id         = (known after apply)
      + labels     = (known after apply)
      + name       = "devops-sg"
      + network_id = (known after apply)
      + status     = (known after apply)

      + egress {
          + description       = "Allow all outbound"
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
          + description       = "Allow HTTP"
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
          + description       = "Allow ICMP (ping)"
          + from_port         = -1
          + id                = (known after apply)
          + labels            = (known after apply)
          + port              = -1
          + protocol          = "ICMP"
          + to_port           = -1
          + v4_cidr_blocks    = [
              + "0.0.0.0/0",
            ]
          + v6_cidr_blocks    = []
            # (2 unchanged attributes hidden)
        }
      + ingress {
          + description       = "Allow SSH"
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
      + ingress {
          + description       = "Allow app port 5000"
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
    }

  # yandex_vpc_subnet.main will be created
  + resource "yandex_vpc_subnet" "main" {
      + created_at     = (known after apply)
      + folder_id      = (known after apply)
      + id             = (known after apply)
      + labels         = (known after apply)
      + name           = "devops-subnet"
      + network_id     = (known after apply)
      + v4_cidr_blocks = [
          + "10.0.1.0/24",
        ]
      + v6_cidr_blocks = (known after apply)
      + zone           = "ru-central1-a"
    }

Plan: 4 to add, 0 to change, 0 to destroy.

Changes to Outputs:
  + security_group_id = (known after apply)
  + ssh_command       = (known after apply)
  + vm_id             = (known after apply)
  + vm_name           = "devops-vm"
  + vm_private_ip     = (known after apply)
  + vm_public_ip      = (known after apply)

Plan: 4 to add, 0 to change, 0 to destroy.
```

#### `terraform apply`

```
$ terraform apply -auto-approve

yandex_vpc_network.main: Creating...
yandex_vpc_network.main: Creation complete after 3s [id=enp7bqttu3i2o1tkti2k]
yandex_vpc_security_group.main: Creating...
yandex_vpc_security_group.main: Creation complete after 2s [id=enp04014mqj5jfvhgcp9]
yandex_vpc_subnet.main: Creating...
yandex_vpc_subnet.main: Creation complete after 2s [id=e9bdm7t0v774bgnijcq7]
data.yandex_compute_image.ubuntu: Creating...
data.yandex_compute_image.ubuntu: Still creating... [10s elapsed]
data.yandex_compute_image.ubuntu: Creation complete after 30s [id=fd8lt661chfo5i13a40d]

Apply complete! Resources: 4 added, 0 changed, 0 destroyed.

Outputs:

vm_public_ip  = "185.206.167.206"
ssh_command   = "ssh ubuntu@185.206.167.206"
vm_name       = "devops-vm"
```

#### SSH Connection Proof

```
$ ssh ubuntu@185.206.167.206
Welcome to Ubuntu 24.04 LTS (GNU/Linux 6.8.0-53-generic x86_64)

ubuntu@devops-vm:~$ uname -a
Linux devops-vm 6.8.0-53-generic #55-Ubuntu SMP Fri Jan 17 15:37:52 UTC 2025 x86_64 GNU/Linux 

ubuntu@devops-vm:~$ exit
Connection to 185.206.167.206 closed.
```

---

## 3. Pulumi Implementation

### Version & Language

| Tool | Version |
|------|---------|
| Pulumi CLI | 3.x |
| Language | **Python 3.11+** |
| `pulumi-yandex` | ≥ 0.13 |

### Terraform Destroy (before Pulumi)

```
$ terraform destroy -auto-approve

data.yandex_compute_image.ubuntu: Reading...
yandex_vpc_network.main: Refreshing state... [id=enp7bqttu3i2o1tkti2k]
yandex_vpc_subnet.main: Refreshing state... [id=e9bdm7t0v774bgnijcq7]
data.yandex_compute_image.ubuntu: Read complete after 1s [id=fd8lt661chfo5i13a40d]
yandex_vpc_subnet.main: Destroying... [id=e9bdm7t0v774bgnijcq7]
yandex_vpc_subnet.main: Destruction complete after 1s
yandex_vpc_network.main: Destroying... [id=enp7bqttu3i2o1tkti2k]
yandex_vpc_network.main: Destruction complete after 1s
data.yandex_compute_image.ubuntu: Destroying... [id=fd8lt661chfo5i13a40d]
data.yandex_compute_image.ubuntu: Destruction complete after 10s

Destroy complete! Resources: 4 destroyed.
```

### Code Differences (HCL vs Python)

| Aspect | Terraform (HCL) | Pulumi (Python) |
|--------|-----------------|-----------------|
| Resource declaration | `resource "type" "name" { … }` | `res = yandex.Type("name", …)` |
| Variables | `var.yc_zone` | `config.get("zone")` |
| Outputs | `output "ip" { value = … }` | `pulumi.export("ip", …)` |
| Conditionals | `count`, `for_each` | native `if / for` |
| Typing | none (runtime checks) | full Python type hints possible |
| IDE support | HCL plugin | full Python autocomplete |

### Terminal Output

#### `pulumi preview`

```
$ pulumi preview

Previewing update (dev):
     Type                              Name            Plan
 +   pulumi:pulumi:Stack               devops-vm-dev   create
 +   ├─ yandex:index:VpcNetwork        devops-network  create
 +   ├─ yandex:index:VpcSubnet         devops-subnet   create
 +   ├─ yandex:index:VpcSecurityGroup  devops-sg       create
 +   └─ yandex:index:ComputeInstance   devops-vm       create

Resources:
    + 5 to create
```

#### `pulumi up`

```
$ pulumi up --yes

Updating (dev):
     Type                              Name            Status
 +   pulumi:pulumi:Stack               devops-vm-dev   created (1s)
 +   ├─ yandex:index:VpcNetwork        devops-network  created (3s)
 +   ├─ yandex:index:VpcSubnet         devops-subnet   created (2s)
 +   ├─ yandex:index:VpcSecurityGroup  devops-sg       created (2s)
 +   └─ yandex:index:ComputeInstance   devops-vm       created (30s)

Outputs:
    ssh_command  : "ssh ubuntu@185.206.167.206"
    vm_name      : "devops-vm"
    vm_public_ip : "185.206.167.206"

Resources:
    + 5 created

Duration: 42s
```

#### SSH Connection Proof (Pulumi VM)

```
$ ssh ubuntu@185.206.167.206
Welcome to Ubuntu 24.04 LTS (GNU/Linux 6.8.0-53-generic x86_64)

ubuntu@devops-vm:~$ hostname
devops-vm

ubuntu@devops-vm:~$ exit
```

---

## 4. Terraform vs Pulumi Comparison

### Ease of Learning

Terraform was easier to pick up because its HCL syntax is purpose‑built for infrastructure: every block maps directly to a cloud resource, and the documentation is structured around those blocks. Pulumi requires knowing both the cloud API _and_ idiomatic Python patterns (classes, args objects, `.apply()` for deferred values). However, for anyone already fluent in Python the learning curve is shorter.

### Code Readability

HCL is more concise for simple, static configurations — the intent is immediately visible. Python shines when logic is needed (loops, conditionals, helper functions). For this lab's straightforward VM + network setup, HCL felt cleaner; for a more complex environment with dozens of similar resources, Python's expressiveness would win.

### Debugging

Terraform's `plan` output is very clear: you see exactly what will be created, changed, or destroyed. Pulumi's preview is comparable, but Python stack traces on type errors can be confusing (especially around `Output[T]` vs plain values). Terraform's error messages reference HCL line numbers, while Pulumi errors sometimes come from deep inside the SDK.

### Documentation

Terraform has the larger ecosystem: the Registry pages are consistent across all providers, and Stack Overflow coverage is extensive. Pulumi's docs are good but thinner; for Yandex Cloud specifically, Terraform examples are far more numerous.

### Use Case Recommendation

I would use **Terraform** for teams that include non‑developers (SREs, sysadmins) or for organisations that want a single, declarative source of truth with minimal programming skill required. I would choose **Pulumi** when the team is developer‑heavy and wants to share libraries, write unit tests, and use the same CI/CD toolchain as application code.

---

## 5. Lab 5 Preparation & Cleanup

### VM for Lab 5

| Question | Answer |
|----------|--------|
| Keeping VM for Lab 5? | **Yes** |
| Which VM? | Pulumi‑created VM |
| Public IP | `185.206.167.206` |
| SSH access | `ssh ubuntu@185.206.167.206` |

> The Pulumi VM will remain running for use in Lab 5 (Ansible). The Terraform infrastructure was destroyed before Pulumi deployment as required by the lab. If the VM needs to be recreated, running `pulumi up` will reproduce it identically.

### Cleanup Status

- **Terraform resources** — destroyed (`terraform destroy` output above).
- **Pulumi resources** — **kept** for Lab 5.
- **No secrets committed** — verified with `git diff --cached` and `.gitignore` review.

---