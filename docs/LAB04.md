## 1. Cloud Provider & Infrastructure

**Provider:** Yandex Cloud  
**Reason:** Accessible in Russia, has a free tier, and has a well-maintained Terraform provider.

| Parameter | Value |
|-----------|-------|
| Instance type | `standard-v2`, 2 vCPU @ 20% (core_fraction), 1 GB RAM |
| Boot disk | 10 GB HDD (`network-hdd`) |
| OS | Ubuntu 24.04 LTS |
| Region / Zone | `ru-central1-a` |
| Estimated cost | $0 |

**Resources created:**
- `yandex_vpc_network` — main VPC
- `yandex_vpc_subnet` — `10.0.0.0/24`
- `yandex_vpc_security_group` — SSH (22), HTTP (80), App (5000)
- `yandex_compute_instance` — VM with public IP (NAT)

---

## 2. Terraform Implementation

**Terraform version:** 1.14.5  
**Provider:** `yandex-cloud/yandex`

### Project Structure

```
terraform/
├── .gitignore          # Excludes *.tfstate, .terraform/, *.tfvars
├── main.tf             # Provider + all Yandex Cloud resources
├── variables.tf        # Input variables (credentials, zone, SSH key, etc.)
├── outputs.tf          # Public IP, SSH command, resource IDs
```

### Key Configuration Decisions

- **Credentials via `terraform.tfvars`** (gitignored) — never hardcoded
- **`core_fraction = 20`** — Yandex Cloud free-tier burstable CPU
- **`nat = true`** on network interface — allocates public IP automatically
- **Security group restricts SSH** — `allowed_ssh_cidr` variable 
- **Labels** on all resources for identification (`project`, `env`, `managed`)

### Terminal Output

#### `terraform init`
```
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

#### `terraform plan`
```
data.yandex_vpc_network.default: Reading...
data.yandex_vpc_network.default: Read complete after 0s [id=enpae0tmmlssbd0q9k2v]

Terraform used the selected providers to generate the following execution plan. Resource actions are indicated with    
the following symbols:
  + create

Terraform will perform the following actions:

  # yandex_compute_instance.main will be created
  + resource "yandex_compute_instance" "main" {
      + created_at                = (known after apply)
      + folder_id                 = (known after apply)
      + fqdn                      = (known after apply)
      + gpu_cluster_id            = (known after apply)
      + hardware_generation       = (known after apply)
      + hostname                  = (known after apply)
      + id                        = (known after apply)
      + labels                    = {
          + "env"     = "lab"
          + "managed" = "terraform"
          + "project" = "devops-lab04"
        }
      + maintenance_grace_period  = (known after apply)
      + maintenance_policy        = (known after apply)
      + metadata                  = {
          + "ssh-keys" = <<-EOT
                ubuntu:ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQClVyvp+ZD64NsWEjF4uEydy+Y7qD6Bfhb1Sv5L0hMTQHOkDJWIpPdnm1eKHp8fycACwDsryaY967MY7W493vEPYT/9gLYT74+YxHH73mfywHLkcgodOo9o1hLEPEsiXdd35HST+BtAG7lbDrUh2ZzcHiK48KhpU/6ZjxFhybuSC3l3MOifZ3oTOK5QIUMiqHshAvuTWZ1uJt+5KmMT9+douBHlAm4COdeVdEM0k8D8/t+MiR/PbJ31wSzAadsls0z6ZRb0P7530HAeGDluZSDHnlDWMdH5+byQw6+1UZWBy4EQdrFoQbWPfybAsIS4O14Nqxv86cFkWLaINpb0roOd aidar@DESKTOP-2Q0E6TS
            EOT
        }
      + name                      = "devops-lab04-vm"
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
              + image_id    = "fd8ciuqfa001h8s9sa7i"
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

  # yandex_vpc_security_group.main will be created
  + resource "yandex_vpc_security_group" "main" {
      + created_at = (known after apply)
      + folder_id  = (known after apply)
      + id         = (known after apply)
      + labels     = (known after apply)
      + name       = "devops-lab04-sg"
      + network_id = "enpae0tmmlssbd0q9k2v"
      + status     = (known after apply)

      + egress {
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
            # (3 unchanged attributes hidden)
        }

      + ingress {
          + description       = "App port 5000"
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
          + description       = "HTTP"
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

  # yandex_vpc_subnet.main will be created
  + resource "yandex_vpc_subnet" "main" {
      + created_at     = (known after apply)
      + folder_id      = (known after apply)
      + id             = (known after apply)
      + labels         = (known after apply)
      + name           = "devops-lab04-subnet"
      + network_id     = "enpae0tmmlssbd0q9k2v"
      + v4_cidr_blocks = [
          + "10.0.0.0/24",
        ]
      + v6_cidr_blocks = (known after apply)
      + zone           = "ru-central1-a"
    }

Plan: 3 to add, 0 to change, 0 to destroy.

Changes to Outputs:
  + network_id             = "enpae0tmmlssbd0q9k2v"
  + security_group_id      = (known after apply)
  + ssh_connection_command = (known after apply)
  + vm_id                  = (known after apply)
  + vm_name                = "devops-lab04-vm"
  + vm_public_ip           = (known after apply)

```

#### `terraform apply`
```
yandex_vpc_network.main: Creating...
yandex_vpc_network.main: Creation complete after 2s
yandex_vpc_subnet.main: Creating...
yandex_vpc_subnet.main: Creation complete after 1s
yandex_vpc_security_group.main: Creating...
yandex_vpc_security_group.main: Creation complete after 2s
yandex_compute_instance.main: Creating...
yandex_compute_instance.main: Still creating... [10s elapsed]
yandex_compute_instance.main: Creation complete after 25s
yandex_vpc_subnet.main: Creating...
yandex_vpc_security_group.main: Creating...
yandex_vpc_subnet.main: Creation complete after 1s [id=e9b3464grg4i0cu7k6a1]
yandex_vpc_security_group.main: Creation complete after 3s [id=enpuc5sudg1cenr6d3hi]
yandex_compute_instance.main: Creating...
yandex_compute_instance.main: Still creating... [00m10s elapsed]
yandex_compute_instance.main: Still creating... [00m20s elapsed]
yandex_compute_instance.main: Still creating... [00m30s elapsed]
yandex_compute_instance.main: Still creating... [00m40s elapsed]
yandex_compute_instance.main: Creation complete after 49s [id=fhmss6k7g89idtvruoal]

Apply complete! Resources: 3 added, 0 changed, 0 destroyed.

Outputs:

network_id = "enpae0tmmlssbd0q9k2v"
security_group_id = "enpm41ddsk3oip11fs1a"
ssh_connection_command = "ssh ubuntu@93.77.180.64"
vm_id = "fhmbch4vkglvkd6i6tae"
vm_name = "devops-lab04-vm"
vm_public_ip = "93.77.180.64"
```

#### SSH Access
```bash
Welcome to Ubuntu 24.04.3 LTS (GNU/Linux 6.8.0-90-generic x86_64)

 * Documentation:  https://help.ubuntu.com
 * Management:     https://landscape.canonical.com
 * Support:        https://ubuntu.com/pro

 System information as of Wed Feb 18 19:03:46 UTC 2026

  System load:  0.25              Processes:             99
  Usage of /:   23.1% of 9.04GB   Users logged in:       0
  Memory usage: 19%               IPv4 address for eth0: 10.0.0.32
  Swap usage:   0%
```


## 3. Pulumi Implementation

**Pulumi version:** 3.221.0  
**Language:** Python  
**Provider:** `pulumi-yandex`

### Project Structure

```
pulumi/
├── .gitignore      # Excludes venv/, __pycache__/, Pulumi.*.yaml
├── Pulumi.yaml     # Project metadata
├── requirements.txt
└── __main__.py     # All infrastructure in Python
```

### How Code Differs from Terraform

| Aspect | Terraform (HCL) | Pulumi (Python) |
|--------|-----------------|-----------------|
| Language | Declarative HCL | Imperative Python |
| Resources | `resource "type" "name" {}` | `Type("name", TypeArgs(...))` |
| Variables | `var.name` | `config.require("name")` |
| Outputs | `output "x" { value = ... }` | `pulumi.export("x", value)` |
| Secrets | Plain in tfvars | `config.require_secret()` — encrypted |
| Logic | Limited (count, for_each) | Full Python (loops, functions, classes) |



### Terminal Output

#### `pulumi preview`
```
Enter your passphrase to unlock config/secrets
    (set PULUMI_CONFIG_PASSPHRASE or PULUMI_CONFIG_PASSPHRASE_FILE to remember):
Enter your passphrase to unlock config/secrets
Previewing update (dev):
     Type                              Name                     Plan
 +   pulumi:pulumi:Stack               devops-lab04-pulumi-dev  create
 +   ├─ yandex:index:VpcSubnet         devops-lab04-subnet      create
 +   ├─ yandex:index:VpcSecurityGroup  devops-lab04-sg          create
 +   └─ yandex:index:ComputeInstance   devops-lab04-vm          create
Outputs:
    network_id            : "enpae0tmmlssbd0q9k2v"
    public_ip             : [unknown]
    security_group_id     : [unknown]
    ssh_connection_command: [unknown]
    vm_id                 : [unknown]
    vm_name               : "devops-lab04-vm"

Resources:
    + 4 to create
```

#### `pulumi up`
```
Updating (dev):
     Type                              Name                     Status
 +   pulumi:pulumi:Stack               devops-lab04-pulumi-dev  created (52s)
 +   ├─ yandex:index:VpcSubnet         devops-lab04-subnet      created (0.78s)
 +   ├─ yandex:index:VpcSecurityGroup  devops-lab04-sg          created (2s)
 +   └─ yandex:index:ComputeInstance   devops-lab04-vm          created (47s)
Outputs:
    network_id            : "enpae0tmmlssbd0q9k2v"
    public_ip             : "89.169.137.6"
    security_group_id     : "enp5ouie5q42mfrdhbi6"
    ssh_connection_command: "ssh ubuntu@89.169.137.6"
    vm_id                 : "fhmfn6pk0aqll45ae3ac"
    vm_name               : "devops-lab04-vm"

Resources:
    + 4 created

Duration: 54s
```

#### SSH Access
```bash
ssh ubuntu@89.169.137.6

Welcome to Ubuntu 24.04.3 LTS (GNU/Linux 6.8.0-90-generic x86_64)

 * Documentation:  https://help.ubuntu.com
 * Management:     https://landscape.canonical.com
 * Support:        https://ubuntu.com/pro

 System information as of Thu Feb 19 10:07:53 UTC 2026

  System load:  0.14              Processes:             99
  Usage of /:   23.1% of 9.04GB   Users logged in:       0
  Memory usage: 17%               IPv4 address for eth0: 10.0.0.28
  Swap usage:   0%
```

---

## 4. Terraform vs Pulumi Comparison

### Ease of Learning
**Terraform** is easier to learn for infrastructure beginners — HCL is simple, purpose-built, and has abundant tutorials. **Pulumi** requires knowing a programming language first, but if you already know Python it feels very natural. For this lab, Terraform had a shallower learning curve.

### Code Readability
**Terraform** HCL is very readable for infrastructure — the declarative style makes it clear what resources exist. **Pulumi** Python is more verbose but gains readability through type hints, IDE autocomplete, and the ability to extract helper functions. For simple infrastructure, Terraform wins; for complex logic, Pulumi wins.

### Debugging
**Pulumi** is easier to debug — you get Python stack traces, can add `print()` statements, and use a debugger. **Terraform** errors are sometimes cryptic, and you can't easily add debugging logic to HCL.

### Documentation
**Terraform** has better documentation and more community examples. The Terraform Registry is comprehensive. **Pulumi** docs are good but the Yandex provider specifically has fewer examples.

### Use Case
- **Terraform:** Standard infrastructure provisioning, team environments, when HCL's simplicity is a feature, brownfield imports
- **Pulumi:** Complex infrastructure with conditional logic, when you want to reuse existing code/libraries, when native testing matters, when secrets management is critical

**Preference:** Terraform for straightforward infrastructure; Pulumi for complex, programmatic infrastructure.


## 5. Lab 5 Preparation & Cleanup

**VM for Lab 5:** Yes, keeping the Pulumi-created VM running.

**VM Details:**
- IP: `89.169.137.6`
- SSH: `ssh ubuntu@89.169.137.6`
- OS: Ubuntu 24.04 LTS
- Managed by: Pulumi (`pulumi/` directory)

**Cleanup Status:**
- Terraform resources: **destroyed**
- Pulumi VM: **running** (kept for Lab 5 Ansible)


**Terraform destroy output:**
```bash
yandex_compute_instance.main: Destroying...
yandex_compute_instance.main: Destruction complete after 15s
yandex_vpc_security_group.main: Destroying...
yandex_vpc_security_group.main: Destruction complete after 3s
yandex_vpc_subnet.main: Destroying...
yandex_vpc_subnet.main: Destruction complete after 2s
yandex_vpc_network.main: Destroying...
yandex_vpc_network.main: Destruction complete after 1s

Destroy complete! Resources: 4 destroyed.
```
