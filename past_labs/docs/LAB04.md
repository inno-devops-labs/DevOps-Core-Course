# Lab 4

## Cloud Provider & Infrasrtucture

**Cloud provider chosen:** Yandex Cloud  
**Rationale:** free-tier, simple console + good Terraform provider support, suitable for quick VM+VPC lab.

**Region/zone selected:** `ru-central1-a`

**Instance type/size (smallest practical):**
- Platform: `standard-v1`
- vCPU: `2`
- RAM: `2 GB`
- Core fraction: `20%`
- Boot disk: `20 GB` (`network-hdd`)
Reason: minimal resources while still stable for SSH + future app/Ansible.

**Total cost:** at the time of work the console balance showed `0 ₽` (lab run). 

**Resources created (Terraform + Pulumi, equivalent set):**
- VPC Network: `lab-vm-net`
- Subnet: `lab-vm-subnet` (`10.10.0.0/24`, zone `ru-central1-a`)
- Security Group: `lab-vm-sg`
  - Ingress: SSH `22/tcp` from **my IP /32**
  - Ingress: HTTP `80/tcp` from `0.0.0.0/0`
  - Ingress: Custom `5000/tcp` from `0.0.0.0/0`
  - Egress: `ANY` to `0.0.0.0/0`
- Static Public IPv4 address: `lab-vm-ip`
- Compute instance: `lab-vm` (NAT enabled, static public IP attached)


## Terraform Implementation

**Terraform version used:** Terraform v1.14.x (HashiCorp package)  
**Provider:** `yandex-cloud/yandex` (used version seen during init: `v0.186.0`)

**Project structure (terraform/):**
- `versions.tf` (required providers)
- `main.tf` (network/subnet/sg/address/compute)
- `variables.tf` (cloud_id, folder_id, zone, sizes, paths, CIDR, labels)
- `outputs.tf` (public_ip, ssh_command)
- `terraform.tfvars` (values; no secrets committed)
- `.gitignore` (excludes state + key.json)

**Key configuration decisions:**
- Authentication via Service Account JSON key (`key.json`) and variables `cloud_id`, `folder_id`, `zone`.
- Ubuntu 24.04 image via `data.yandex_compute_image` family `ubuntu-2404-lts`.
- Security Group implements required firewall rules 22/80/5000.
- Labels: `project=lab04` for identification.

**Challenges encountered (Terraform):**
- Initially WSL could not download providers from Terraform Registry (`Invalid provider registry host`), so Terraform commands were executed from Ubuntu VM where registry access worked.
- `ssh_public_key_path` issue: using wrong path on the VM (`/home/zagur/...`), fixed by pointing to the actual key on the VM (`/home/liza/...`).
- Service Account key issues: `key.json` must be valid JSON and placed in the terraform directory (and must not be committed).

**Terminal output (key commands):**

- `terraform init`

  ```bash
  liza@liza-VirtualBox:/media/sf_shared_with_VB/DevOps/DevOps-Core-Course/terraform$ terraform init
  Initializing the backend...
  Initializing provider plugins...
  - Reusing previous version of yandex-cloud/yandex from the dependency lock file
  - Using previously-installed yandex-cloud/yandex v0.186.0

  Terraform has been successfully initialized!

  You may now begin working with Terraform. Try running "terraform plan" to see
  any changes that are required for your infrastructure. All Terraform commands
  should now work.

  If you ever set or change modules or backend configuration for Terraform,
  rerun this command to reinitialize your working directory. If you forget, other
  commands will detect it and remind you to do so if necessary.
  ```
- `terraform plan`

  ```bash
  liza@liza-VirtualBox:/media/sf_shared_with_VB/DevOps/DevOps-Core-Course/terraform$ terraform plan
  data.yandex_compute_image.ubuntu: Reading...
  data.yandex_compute_image.ubuntu: Read complete after 1s [id=fd8p685sjqdraf7mpkuc]

  Terraform used the selected providers to generate the following execution plan.
  Resource actions are indicated with the following symbols:
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
        + labels                    = {
            + "project" = "lab04"
          }
        + maintenance_grace_period  = (known after apply)
        + maintenance_policy        = (known after apply)
        + metadata                  = {
            + "ssh-keys" = <<-EOT
                  ubuntu:ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIL/Nz/lUWA58Ungm2qW9p4o+IHT5W+R0aQ3wWUIkr34j liza@liza-VirtualBox
              EOT
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
                + image_id    = "fd8p685sjqdraf7mpkuc"
                + name        = (known after apply)
                + size        = 20
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

    # yandex_vpc_address.public_ip will be created
    + resource "yandex_vpc_address" "public_ip" {
        + created_at          = (known after apply)
        + deletion_protection = (known after apply)
        + folder_id           = (known after apply)
        + id                  = (known after apply)
        + labels              = (known after apply)
        + name                = "lab-vm-ip"
        + reserved            = (known after apply)
        + used                = (known after apply)

        + external_ipv4_address {
            + address                  = (known after apply)
            + ddos_protection_provider = (known after apply)
            + outgoing_smtp_capability = (known after apply)
            + zone_id                  = "ru-central1-a"
          }
      }

    # yandex_vpc_network.net will be created
    + resource "yandex_vpc_network" "net" {
        + created_at                = (known after apply)
        + default_security_group_id = (known after apply)
        + folder_id                 = (known after apply)
        + id                        = (known after apply)
        + labels                    = {
            + "project" = "lab04"
          }
        + name                      = "lab-vm-net"
        + subnet_ids                = (known after apply)
      }

    # yandex_vpc_security_group.sg will be created
    + resource "yandex_vpc_security_group" "sg" {
        + created_at = (known after apply)
        + folder_id  = (known after apply)
        + id         = (known after apply)
        + labels     = {
            + "project" = "lab04"
          }
        + name       = "lab-vm-sg"
        + network_id = (known after apply)
        + status     = (known after apply)

        + egress {
            + description       = "Allow all egress"
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
            + description       = "SSH from my IP"
            + from_port         = -1
            + id                = (known after apply)
            + labels            = (known after apply)
            + port              = 22
            + protocol          = "TCP"
            + to_port           = -1
            + v4_cidr_blocks    = [
                + "188.130.155.177/32",
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
        + labels         = {
            + "project" = "lab04"
          }
        + name           = "lab-vm-subnet"
        + network_id     = (known after apply)
        + v4_cidr_blocks = [
            + "10.10.0.0/24",
          ]
        + v6_cidr_blocks = (known after apply)
        + zone           = "ru-central1-a"
      }

  Plan: 5 to add, 0 to change, 0 to destroy.

  Changes to Outputs:
    + public_ip   = (known after apply)
    + ssh_command = (known after apply)

  ──────────────────────────────────────────────────────────────────────────────────────

  Note: You didn't use the -out option to save this plan, so Terraform can't guarantee
  to take exactly these actions if you run "terraform apply" now.
  ```
- `terraform apply`

  ```bash
  liza@liza-VirtualBox:/media/sf_shared_with_VB/DevOps/DevOps-Core-Course/terraform$ terraform apply
  data.yandex_compute_image.ubuntu: Reading...
  data.yandex_compute_image.ubuntu: Read complete after 1s [id=fd8p685sjqdraf7mpkuc]

  Terraform used the selected providers to generate the following execution plan.
  Resource actions are indicated with the following symbols:
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
        + labels                    = {
            + "project" = "lab04"
          }
        + maintenance_grace_period  = (known after apply)
        + maintenance_policy        = (known after apply)
        + metadata                  = {
            + "ssh-keys" = <<-EOT
                  ubuntu:ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIL/Nz/lUWA58Ungm2qW9p4o+IHT5W+R0aQ3wWUIkr34j liza@liza-VirtualBox
              EOT
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
                + image_id    = "fd8p685sjqdraf7mpkuc"
                + name        = (known after apply)
                + size        = 20
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

    # yandex_vpc_address.public_ip will be created
    + resource "yandex_vpc_address" "public_ip" {
        + created_at          = (known after apply)
        + deletion_protection = (known after apply)
        + folder_id           = (known after apply)
        + id                  = (known after apply)
        + labels              = (known after apply)
        + name                = "lab-vm-ip"
        + reserved            = (known after apply)
        + used                = (known after apply)

        + external_ipv4_address {
            + address                  = (known after apply)
            + ddos_protection_provider = (known after apply)
            + outgoing_smtp_capability = (known after apply)
            + zone_id                  = "ru-central1-a"
          }
      }

    # yandex_vpc_network.net will be created
    + resource "yandex_vpc_network" "net" {
        + created_at                = (known after apply)
        + default_security_group_id = (known after apply)
        + folder_id                 = (known after apply)
        + id                        = (known after apply)
        + labels                    = {
            + "project" = "lab04"
          }
        + name                      = "lab-vm-net"
        + subnet_ids                = (known after apply)
      }

    # yandex_vpc_security_group.sg will be created
    + resource "yandex_vpc_security_group" "sg" {
        + created_at = (known after apply)
        + folder_id  = (known after apply)
        + id         = (known after apply)
        + labels     = {
            + "project" = "lab04"
          }
        + name       = "lab-vm-sg"
        + network_id = (known after apply)
        + status     = (known after apply)

        + egress {
            + description       = "Allow all egress"
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
            + description       = "SSH from my IP"
            + from_port         = -1
            + id                = (known after apply)
            + labels            = (known after apply)
            + port              = 22
            + protocol          = "TCP"
            + to_port           = -1
            + v4_cidr_blocks    = [
                + "188.130.155.177/32",
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
        + labels         = {
            + "project" = "lab04"
          }
        + name           = "lab-vm-subnet"
        + network_id     = (known after apply)
        + v4_cidr_blocks = [
            + "10.10.0.0/24",
          ]
        + v6_cidr_blocks = (known after apply)
        + zone           = "ru-central1-a"
      }

  Plan: 5 to add, 0 to change, 0 to destroy.

  Changes to Outputs:
    + public_ip   = (known after apply)
    + ssh_command = (known after apply)

  Do you want to perform these actions?
    Terraform will perform the actions described above.
    Only 'yes' will be accepted to approve.

    Enter a value: yes

  yandex_vpc_address.public_ip: Creating...
  yandex_vpc_network.net: Creating...
  yandex_vpc_address.public_ip: Creation complete after 2s [id=e9bpa7ofbfbj4i4jg067]
  yandex_vpc_network.net: Creation complete after 3s [id=enpqagvtk5g4ne5lnlv5]
  yandex_vpc_subnet.subnet: Creating...
  yandex_vpc_security_group.sg: Creating...
  yandex_vpc_subnet.subnet: Creation complete after 1s [id=e9bvvrbqalt0rvkrombc]
  yandex_vpc_security_group.sg: Creation complete after 3s [id=enpb3nevkhedg2m9mess]
  yandex_compute_instance.vm: Creating...
  yandex_compute_instance.vm: Still creating... [00m10s elapsed]
  yandex_compute_instance.vm: Still creating... [00m20s elapsed]
  yandex_compute_instance.vm: Still creating... [00m30s elapsed]
  yandex_compute_instance.vm: Still creating... [00m40s elapsed]
  yandex_compute_instance.vm: Creation complete after 43s [id=fhmp143am01jk4mp8l5t]

  Apply complete! Resources: 5 added, 0 changed, 0 destroyed.

  Outputs:

  public_ip = "93.77.187.114"
  ssh_command = "ssh -i ~/.ssh/id_ed25519 ubuntu@93.77.187.114"
  ```
- `SSH connection to VM`

  ```bash
  liza@liza-VirtualBox:/media/sf_shared_with_VB/DevOps/DevOps-Core-Course/terraform$ ssh -i ~/.ssh/id_ed25519 ubuntu@93.77.187.114
  The authenticity of host '93.77.187.114 (93.77.187.114)' can't be established.
  ED25519 key fingerprint is SHA256:O4bQHhkR0EvL+sATJS3LhfXhGzPdlfoKHfg6ItBFccA.
  This key is not known by any other names.
  Are you sure you want to continue connecting (yes/no/[fingerprint])? yes
  Warning: Permanently added '93.77.187.114' (ED25519) to the list of known hosts.
  Welcome to Ubuntu 24.04.3 LTS (GNU/Linux 6.8.0-100-generic x86_64)

  * Documentation:  https://help.ubuntu.com
  * Management:     https://landscape.canonical.com
  * Support:        https://ubuntu.com/pro

  System information as of Sun Feb 15 18:34:08 UTC 2026

    System load:  0.16               Processes:             100
    Usage of /:   11.2% of 18.72GB   Users logged in:       0
    Memory usage: 9%                 IPv4 address for eth0: 10.10.0.9
    Swap usage:   0%


  Expanded Security Maintenance for Applications is not enabled.

  0 updates can be applied immediately.

  Enable ESM Apps to receive additional future security updates.
  See https://ubuntu.com/esm or run: sudo pro status


  The list of available updates is more than a week old.
  To check for new updates run: sudo apt update


  The programs included with the Ubuntu system are free software;
  the exact distribution terms for each program are described in the
  individual files in /usr/share/doc/*/copyright.

  Ubuntu comes with ABSOLUTELY NO WARRANTY, to the extent permitted by
  applicable law.

  To run a command as administrator (user "root"), use "sudo <command>".
  See "man sudo_root" for details.

  ubuntu@fhmp143am01jk4mp8l5t:~$ sudo ss -tulpn | grep -E '(:22|:80|:5000)\s'
  tcp   LISTEN 0      4096          0.0.0.0:22        0.0.0.0:*    users:(("sshd",pid=1007,fd=3),("systemd",pid=1,fd=60))
  tcp   LISTEN 0      4096             [::]:22           [::]:*    users:(("sshd",pid=1007,fd=4),("systemd",pid=1,fd=61))
  ubuntu@fhmp143am01jk4mp8l5t:~$ 
  ```

## Pulumi Implementation

**Pulumi version and language:** Pulumi CLI (Python project), language = Python.
**Provider/library:** `pulumi-yandex`

**How code differs from Terraform:**
- Terraform: declarative HCL resources.
- Pulumi: imperative Python program (variables, read SSH key via Python, export outputs).

**Challenges encountered (Pulumi):**
- VirtualBox shared folder restrictions prevented creating Python venv in `/media/sf_*` (symlink permissions). Solution: run Pulumi project from `~/pulumi-yc` (home dir).
- `pulumi_yandex` imports `pkg_resources`; setuptools 82 removed it → pinned setuptools to a version that still provides `pkg_resources`.
- Wrong config key initially (`serviceAccountKeyFilePath`), fixed to `yandex:serviceAccountKeyFile`.
- `~` was not expanded inside Python `open()` for SSH public key path → fixed to absolute path `/home/liza/.ssh/id_ed25519.pub`.
- Pulumi secrets passphrase required for `pulumi stack output ...` → solved via `PULUMI_CONFIG_PASSPHRASE_FILE`.

**Terminal output from:**

- pulumi preview

  ```bash
  (venv) liza@liza-VirtualBox:~/pulumi-yc$ pulumi preview
  Enter your passphrase to unlock config/secrets
      (set PULUMI_CONFIG_PASSPHRASE or PULUMI_CONFIG_PASSPHRASE_FILE to remember):  
  Enter your passphrase to unlock config/secrets
  Previewing update (dev):
      Type                              Name           Plan       Info
  +   pulumi:pulumi:Stack               pulumi-yc-dev  create     1 error; 2 messages
  +   ├─ yandex:index:VpcAddress        lab-vm-ip      create     
  +   ├─ yandex:index:VpcNetwork        lab-vm-net     create     
  +   ├─ yandex:index:VpcSubnet         lab-vm-subnet  create     
  +   └─ yandex:index:VpcSecurityGroup  lab-vm-sg      create     

  Diagnostics:
    pulumi:pulumi:Stack (pulumi-yc-dev):
      /home/liza/pulumi-yc/venv/lib/python3.12/site-packages/pulumi_yandex/_utilities.py:10: UserWarning: pkg_resources is deprecated as an API. See https://setuptools.pypa.io/en/latest/pkg_resources.html. The pkg_resources package is slated for removal as early as 2025-11-30. Refrain from using this package or pin to Setuptools<81.
        import pkg_resources

      error: Program failed with an unhandled exception:
      Traceback (most recent call last):
        File "/home/liza/pulumi-yc/__main__.py", line 87, in <module>
          with open(ssh_public_key_path, "r", encoding="utf-8") as f:
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
      FileNotFoundError: [Errno 2] No such file or directory: '~/.ssh/id_ed25519.pub'

  Resources:
      + 5 to create
      1 errored

  (venv) liza@liza-VirtualBox:~/pulumi-yc$ pulumi config set sshPublicKeyPath "home/liza/.ssh/id_ed25519.pub"
  (venv) liza@liza-VirtualBox:~/pulumi-yc$ pulumi preview
  Enter your passphrase to unlock config/secrets
      (set PULUMI_CONFIG_PASSPHRASE or PULUMI_CONFIG_PASSPHRASE_FILE to remember):  
  Enter your passphrase to unlock config/secrets
  Previewing update (dev):
      Type                              Name           Plan       Info
  +   pulumi:pulumi:Stack               pulumi-yc-dev  create     1 error; 2 messages
  +   ├─ yandex:index:VpcNetwork        lab-vm-net     create     
  +   ├─ yandex:index:VpcAddress        lab-vm-ip      create     
  +   ├─ yandex:index:VpcSecurityGroup  lab-vm-sg      create     
  +   └─ yandex:index:VpcSubnet         lab-vm-subnet  create     

  Diagnostics:
    pulumi:pulumi:Stack (pulumi-yc-dev):
      /home/liza/pulumi-yc/venv/lib/python3.12/site-packages/pulumi_yandex/_utilities.py:10: UserWarning: pkg_resources is deprecated as an API. See https://setuptools.pypa.io/en/latest/pkg_resources.html. The pkg_resources package is slated for removal as early as 2025-11-30. Refrain from using this package or pin to Setuptools<81.
        import pkg_resources

      error: Program failed with an unhandled exception:
      Traceback (most recent call last):
        File "/home/liza/pulumi-yc/__main__.py", line 87, in <module>
          with open(ssh_public_key_path, "r", encoding="utf-8") as f:
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
      FileNotFoundError: [Errno 2] No such file or directory: 'home/liza/.ssh/id_ed25519.pub'

  Resources:
      + 5 to create
      1 errored

  (venv) liza@liza-VirtualBox:~/pulumi-yc$ pulumi config set sshPublicKeyPath "/home/liza/.ssh/id_ed25519.pub"
  (venv) liza@liza-VirtualBox:~/pulumi-yc$ pulumi preview
  Enter your passphrase to unlock config/secrets
      (set PULUMI_CONFIG_PASSPHRASE or PULUMI_CONFIG_PASSPHRASE_FILE to remember):  
  Enter your passphrase to unlock config/secrets
  Previewing update (dev):
      Type                              Name           Plan       Info
  +   pulumi:pulumi:Stack               pulumi-yc-dev  create     2 messages
  +   ├─ yandex:index:VpcNetwork        lab-vm-net     create     
  +   ├─ yandex:index:VpcAddress        lab-vm-ip      create     
  +   ├─ yandex:index:VpcSecurityGroup  lab-vm-sg      create     
  +   ├─ yandex:index:VpcSubnet         lab-vm-subnet  create     
  +   └─ yandex:index:ComputeInstance   lab-vm         create     

  Diagnostics:
    pulumi:pulumi:Stack (pulumi-yc-dev):
      /home/liza/pulumi-yc/venv/lib/python3.12/site-packages/pulumi_yandex/_utilities.py:10: UserWarning: pkg_resources is deprecated as an API. See https://setuptools.pypa.io/en/latest/pkg_resources.html. The pkg_resources package is slated for removal as early as 2025-11-30. Refrain from using this package or pin to Setuptools<81.
        import pkg_resources

  Outputs:
      public_ip  : [unknown]
      ssh_command: [unknown]

  Resources:
      + 6 to create
  ```
- pulumi up

  ```bash
  (venv) liza@liza-VirtualBox:~/pulumi-yc$ pulumi up
  Enter your passphrase to unlock config/secrets
      (set PULUMI_CONFIG_PASSPHRASE or PULUMI_CONFIG_PASSPHRASE_FILE to remember):  
  Enter your passphrase to unlock config/secrets
  Previewing update (dev):
      Type                              Name           Plan       Info
  +   pulumi:pulumi:Stack               pulumi-yc-dev  create     2 messages
  +   ├─ yandex:index:VpcAddress        lab-vm-ip      create     
  +   ├─ yandex:index:VpcNetwork        lab-vm-net     create     
  +   ├─ yandex:index:VpcSubnet         lab-vm-subnet  create     
  +   ├─ yandex:index:VpcSecurityGroup  lab-vm-sg      create     
  +   └─ yandex:index:ComputeInstance   lab-vm         create     

  Diagnostics:
    pulumi:pulumi:Stack (pulumi-yc-dev):
      /home/liza/pulumi-yc/venv/lib/python3.12/site-packages/pulumi_yandex/_utilities.py:10: UserWarning: pkg_resources is deprecated as an API. See https://setuptools.pypa.io/en/latest/pkg_resources.html. The pkg_resources package is slated for removal as early as 2025-11-30. Refrain from using this package or pin to Setuptools<81.
        import pkg_resources

  Outputs:
      public_ip  : [unknown]
      ssh_command: [unknown]

  Resources:
      + 6 to create

  Do you want to perform this update? yes
  Updating (dev):
      Type                              Name           Status                       Inf
  +   pulumi:pulumi:Stack               pulumi-yc-dev  **creating failed (6s)**     1 e
  +   ├─ yandex:index:VpcAddress        lab-vm-ip      created (1s)                 
  +   ├─ yandex:index:VpcNetwork        lab-vm-net     created (3s)                 
  +   ├─ yandex:index:VpcSecurityGroup  lab-vm-sg      **creating failed**          1 e
  +   └─ yandex:index:VpcSubnet         lab-vm-subnet  created (0.69s)              

  Diagnostics:
    pulumi:pulumi:Stack (pulumi-yc-dev):
      /home/liza/pulumi-yc/venv/lib/python3.12/site-packages/pulumi_yandex/_utilities.py:10: UserWarning: pkg_resources is deprecated as an API. See https://setuptools.pypa.io/en/latest/pkg_resources.html. The pkg_resources package is slated for removal as early as 2025-11-30. Refrain from using this package or pin to Setuptools<81.
        import pkg_resources

      error: update failed

    yandex:index:VpcSecurityGroup (lab-vm-sg):
      error: 1 error occurred:
        * error while requesting API to create security group: client-request-id = a8cd88af-ef76-426a-b251-256186350269 client-trace-id = 90223eb4-77e7-4081-b256-ab7658e6b66f rpc error: code = InvalidArgument desc = Illegal argument Cannot parse CIDR: 103.112.171.163
      /32

  Outputs:
      public_ip  : "89.169.128.133"
      ssh_command: "ssh -i ~/.ssh/id_ed25519 ubuntu@89.169.128.133"

  Resources:
      + 4 created
      2 errored

  Duration: 8s

  (venv) liza@liza-VirtualBox:~/pulumi-yc$ pulumi config get sshAllowCidr
  103.112.171.163
  /32

  (venv) liza@liza-VirtualBox:~/pulumi-yc$ pulumi config set sshAllowCidr "103.112.171.163/32"
  (venv) liza@liza-VirtualBox:~/pulumi-yc$ pulumi up
  Enter your passphrase to unlock config/secrets
      (set PULUMI_CONFIG_PASSPHRASE or PULUMI_CONFIG_PASSPHRASE_FILE to remember):  
  Enter your passphrase to unlock config/secrets
  Previewing update (dev):
      Type                              Name           Plan       Info
      pulumi:pulumi:Stack               pulumi-yc-dev             2 messages
  +   ├─ yandex:index:VpcSecurityGroup  lab-vm-sg      create     
  +   └─ yandex:index:ComputeInstance   lab-vm         create     

  Diagnostics:
    pulumi:pulumi:Stack (pulumi-yc-dev):
      /home/liza/pulumi-yc/venv/lib/python3.12/site-packages/pulumi_yandex/_utilities.py:10: UserWarning: pkg_resources is deprecated as an API. See https://setuptools.pypa.io/en/latest/pkg_resources.html. The pkg_resources package is slated for removal as early as 2025-11-30. Refrain from using this package or pin to Setuptools<81.
        import pkg_resources

  Resources:
      + 2 to create
      4 unchanged

  Do you want to perform this update? yes
  Updating (dev):
      Type                              Name           Status            Info
      pulumi:pulumi:Stack               pulumi-yc-dev                    2 messages
  +   ├─ yandex:index:VpcSecurityGroup  lab-vm-sg      created (2s)      
  +   └─ yandex:index:ComputeInstance   lab-vm         created (46s)     

  Diagnostics:
    pulumi:pulumi:Stack (pulumi-yc-dev):
      /home/liza/pulumi-yc/venv/lib/python3.12/site-packages/pulumi_yandex/_utilities.py:10: UserWarning: pkg_resources is deprecated as an API. See https://setuptools.pypa.io/en/latest/pkg_resources.html. The pkg_resources package is slated for removal as early as 2025-11-30. Refrain from using this package or pin to Setuptools<81.
        import pkg_resources

  Outputs:
      public_ip  : "89.169.128.133"
      ssh_command: "ssh -i ~/.ssh/id_ed25519 ubuntu@89.169.128.133"

  Resources:
      + 2 created
      4 unchanged

  Duration: 54s
  ```
- SSH connection to VM

  ```bash
  (venv) liza@liza-VirtualBox:~/pulumi-yc$ pulumi stack output public_ip
  89.169.128.133
  (venv) liza@liza-VirtualBox:~/pulumi-yc$ ssh -i ~/.ssh/id_ed25519 ubuntu@$(pulumi stack output public_ip) "uname -a"
  The authenticity of host '89.169.128.133 (89.169.128.133)' can't be established.
  ED25519 key fingerprint is SHA256:sAzx95etFkjGRS3naJOJ6JT47tTfPFZoe7ZLtrtuwd0.
  This key is not known by any other names.
  Are you sure you want to continue connecting (yes/no/[fingerprint])? yes
  Warning: Permanently added '89.169.128.133' (ED25519) to the list of known hosts.
  Linux fhm6qjabrghet3gtdam5 6.8.0-100-generic #100-Ubuntu SMP PREEMPT_DYNAMIC Tue Jan 13 16:40:06 UTC 2026 x86_64 x86_64 x86_64 GNU/Linux
  (venv) liza@liza-VirtualBox:~/pulumi-yc$ pulumi stack output ssh_command
  ssh -i ~/.ssh/id_ed25519 ubuntu@89.169.128.133
  ```

## Terraform vs Pulumi Comparison

**Ease of Learning:**
Terraform was easier to start: HCL is simple for typical infra and plan/apply is very clear. Pulumi required extra Python environment setup (venv, deps) and config secrets management.

**Code Readability:**
Terraform is very readable for standard infra blocks. Pulumi becomes more readable when logic/abstractions are needed (reusing code, loops, conditionals), but adds Python complexity.

**Debugging:**
Terraform debugging is straightforward via terraform plan diffs and provider errors. Pulumi debugging was harder due to Python runtime errors (file paths, missing modules) and provider configuration keys.

**Documentation:**
Terraform + provider examples were easier to follow for the exact resources. Pulumi docs are good, but provider configuration key naming is less obvious and errors can be less direct.

**Use Case:**
Use Terraform for standard infrastructure provisioning and predictable declarative changes. Use Pulumi when infrastructure needs real programming constructs, reusable components, or complex logic in code.

## Lab 5 Preparation & Cleanup

Are you keeping your VM for Lab 5? (Yes/No): No
If no: What will you use for Lab 5? (Local VM/Will recreate cloud VM): local VM

Cleanup Status:

If destroying everything: Terminal output showing both tools' resources destroyed
Cloud console screenshot showing resource status (optional but recommended): already deleted, as well as paying account.

```bash
liza@liza-VirtualBox:/media/sf_shared_with_VB/DevOps/DevOps-Core-Course/terraform$ terraform destroy
data.yandex_compute_image.ubuntu: Reading...
yandex_vpc_address.public_ip: Refreshing state... [id=e9bpa7ofbfbj4i4jg067]
yandex_vpc_network.net: Refreshing state... [id=enpqagvtk5g4ne5lnlv5]
data.yandex_compute_image.ubuntu: Read complete after 1s [id=fd8p685sjqdraf7mpkuc]
yandex_vpc_subnet.subnet: Refreshing state... [id=e9bvvrbqalt0rvkrombc]
yandex_vpc_security_group.sg: Refreshing state... [id=enpb3nevkhedg2m9mess]
yandex_compute_instance.vm: Refreshing state... [id=fhmp143am01jk4mp8l5t]

Terraform used the selected providers to generate the following execution plan.
Resource actions are indicated with the following symbols:
  - destroy

Terraform will perform the following actions:

  # yandex_compute_instance.vm will be destroyed
  - resource "yandex_compute_instance" "vm" {
      - created_at                = "2026-02-15T18:32:06Z" -> null
      - folder_id                 = "b1grll246n43md1tgbl4" -> null
      - fqdn                      = "fhmp143am01jk4mp8l5t.auto.internal" -> null
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
      - id                        = "fhmp143am01jk4mp8l5t" -> null
      - labels                    = {
          - "project" = "lab04"
        } -> null
      - metadata                  = {
          - "ssh-keys" = <<-EOT
                ubuntu:ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIL/Nz/lUWA58Ungm2qW9p4o+IHT5W+R0aQ3wWUIkr34j liza@liza-VirtualBox
            EOT
        } -> null
      - name                      = "lab-vm" -> null
      - network_acceleration_type = "standard" -> null
      - platform_id               = "standard-v1" -> null
      - status                    = "running" -> null
      - zone                      = "ru-central1-a" -> null
        # (5 unchanged attributes hidden)

      - boot_disk {
          - auto_delete = true -> null
          - device_name = "fhma95uovclrvhk04rr5" -> null
          - disk_id     = "fhma95uovclrvhk04rr5" -> null
          - mode        = "READ_WRITE" -> null

          - initialize_params {
              - block_size  = 4096 -> null
              - image_id    = "fd8p685sjqdraf7mpkuc" -> null
                name        = null
              - size        = 20 -> null
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
          - ip_address         = "10.10.0.9" -> null
          - ipv4               = true -> null
          - ipv6               = false -> null
          - mac_address        = "d0:0d:19:09:06:ab" -> null
          - nat                = true -> null
          - nat_ip_address     = "93.77.187.114" -> null
          - nat_ip_version     = "IPV4" -> null
          - security_group_ids = [
              - "enpb3nevkhedg2m9mess",
            ] -> null
          - subnet_id          = "e9bvvrbqalt0rvkrombc" -> null
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

  # yandex_vpc_address.public_ip will be destroyed
  - resource "yandex_vpc_address" "public_ip" {
      - created_at          = "2026-02-15T18:32:00Z" -> null
      - deletion_protection = false -> null
      - folder_id           = "b1grll246n43md1tgbl4" -> null
      - id                  = "e9bpa7ofbfbj4i4jg067" -> null
      - labels              = {} -> null
      - name                = "lab-vm-ip" -> null
      - reserved            = true -> null
      - used                = true -> null
        # (1 unchanged attribute hidden)

      - external_ipv4_address {
          - address                  = "93.77.187.114" -> null
          - zone_id                  = "ru-central1-a" -> null
            # (2 unchanged attributes hidden)
        }
    }

  # yandex_vpc_network.net will be destroyed
  - resource "yandex_vpc_network" "net" {
      - created_at                = "2026-02-15T18:31:59Z" -> null
      - default_security_group_id = "enpue623uci0thhopdls" -> null
      - folder_id                 = "b1grll246n43md1tgbl4" -> null
      - id                        = "enpqagvtk5g4ne5lnlv5" -> null
      - labels                    = {
          - "project" = "lab04"
        } -> null
      - name                      = "lab-vm-net" -> null
      - subnet_ids                = [
          - "e9bvvrbqalt0rvkrombc",
        ] -> null
        # (1 unchanged attribute hidden)
    }

  # yandex_vpc_security_group.sg will be destroyed
  - resource "yandex_vpc_security_group" "sg" {
      - created_at  = "2026-02-15T18:32:04Z" -> null
      - folder_id   = "b1grll246n43md1tgbl4" -> null
      - id          = "enpb3nevkhedg2m9mess" -> null
      - labels      = {
          - "project" = "lab04"
        } -> null
      - name        = "lab-vm-sg" -> null
      - network_id  = "enpqagvtk5g4ne5lnlv5" -> null
      - status      = "ACTIVE" -> null
        # (1 unchanged attribute hidden)

      - egress {
          - description       = "Allow all egress" -> null
          - from_port         = -1 -> null
          - id                = "enp6av08k6d1ca6fnkeg" -> null
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
          - description       = "App port 5000" -> null
          - from_port         = -1 -> null
          - id                = "enpg2i04845lsbdjtp0c" -> null
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
          - id                = "enprf7fiofoobj3u2in8" -> null
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
          - description       = "SSH from my IP" -> null
          - from_port         = -1 -> null
          - id                = "enplvdni38239u0hd9c4" -> null
          - labels            = {} -> null
          - port              = 22 -> null
          - protocol          = "TCP" -> null
          - to_port           = -1 -> null
          - v4_cidr_blocks    = [
              - "188.130.155.177/32",
            ] -> null
          - v6_cidr_blocks    = [] -> null
            # (2 unchanged attributes hidden)
        }
    }

  # yandex_vpc_subnet.subnet will be destroyed
  - resource "yandex_vpc_subnet" "subnet" {
      - created_at     = "2026-02-15T18:32:02Z" -> null
      - folder_id      = "b1grll246n43md1tgbl4" -> null
      - id             = "e9bvvrbqalt0rvkrombc" -> null
      - labels         = {
          - "project" = "lab04"
        } -> null
      - name           = "lab-vm-subnet" -> null
      - network_id     = "enpqagvtk5g4ne5lnlv5" -> null
      - v4_cidr_blocks = [
          - "10.10.0.0/24",
        ] -> null
      - v6_cidr_blocks = [] -> null
      - zone           = "ru-central1-a" -> null
        # (2 unchanged attributes hidden)
    }

Plan: 0 to add, 0 to change, 5 to destroy.

Changes to Outputs:
  - public_ip   = "93.77.187.114" -> null
  - ssh_command = "ssh -i ~/.ssh/id_ed25519 ubuntu@93.77.187.114" -> null

Do you really want to destroy all resources?
  Terraform will destroy all your managed infrastructure, as shown above.
  There is no undo. Only 'yes' will be accepted to confirm.

  Enter a value: yes

yandex_compute_instance.vm: Destroying... [id=fhmp143am01jk4mp8l5t]
yandex_compute_instance.vm: Still destroying... [id=fhmp143am01jk4mp8l5t, 00m10s elapsed]
yandex_compute_instance.vm: Still destroying... [id=fhmp143am01jk4mp8l5t, 00m20s elapsed]
yandex_compute_instance.vm: Still destroying... [id=fhmp143am01jk4mp8l5t, 00m30s elapsed]
yandex_compute_instance.vm: Destruction complete after 33s
yandex_vpc_security_group.sg: Destroying... [id=enpb3nevkhedg2m9mess]
yandex_vpc_subnet.subnet: Destroying... [id=e9bvvrbqalt0rvkrombc]
yandex_vpc_address.public_ip: Destroying... [id=e9bpa7ofbfbj4i4jg067]
yandex_vpc_security_group.sg: Destruction complete after 1s
yandex_vpc_address.public_ip: Destruction complete after 1s
yandex_vpc_subnet.subnet: Destruction complete after 5s
yandex_vpc_network.net: Destroying... [id=enpqagvtk5g4ne5lnlv5]
yandex_vpc_network.net: Destruction complete after 1s

Destroy complete! Resources: 5 destroyed.
```

![pulumi destroy](/docs/screenshots/pulumi_destroy.png)
