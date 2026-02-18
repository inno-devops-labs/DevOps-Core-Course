## LAB 4 ##


#### Cloud Provider & Infrastructure ####

- Yandex Cloud was chosen as a provider that ssurely will work in Russia.
- Zone: ru-central1-b
- Total cot: 1,5 RUB covered by Yandex Cloud Grant
- Resources:
  1) VM/Compute Instance (smallest free tier size)
  2) Network/VPC (if required by provider)
  3) Security Group/Firewall Rules
  4) Public IP Address (to access VM remotely)


#### Terraform ####

- Version: 1.14.5
- Structure:

```bash
  terraform/
  ├── main.tf          # Provider, network, security group, VM
  ├── variables.tf      # Input variables
  ├── outputs.tf        # Public IP, SSH command
  ├── terraform.tfvars  # Sensitive values
  └── .gitignore        # Exclude state files and .tfvars
```

- Challenge: make this thing work.

```bash
terraform init
```

Result:

```
Initializing the backend...
Initializing provider plugins...
- Finding latest version of yandex-cloud/yandex...
- Installing yandex-cloud/yandex v0.187.0...
- Installed yandex-cloud/yandex v0.187.0 (unauthenticated)
Terraform has created a lock file .terraform.lock.hcl to record the provider  
selections it made above. Include this file in your version control repository
so that Terraform can guarantee to make the same selections by default when   
you run "terraform init" in the future.

╷
│ Warning: Incomplete lock file information for providers
│
│ Due to your customized provider installation methods, Terraform was forced to calculate lock file checksums locally for the following providers:
│   - yandex-cloud/yandex
│
│ The current .terraform.lock.hcl file only includes checksums for windows_amd64, so Terraform running on another platform will fail to install these providers.
│
│ To calculate additional checksums for another platform, run:
│   terraform providers lock -platform=linux_amd64
│ (where linux_amd64 is the platform to generate)
╵
Terraform has been successfully initialized!

You may now begin working with Terraform. Try running "terraform plan" to see
any changes that are required for your infrastructure. All Terraform commands
should now work.

If you ever set or change modules or backend configuration for Terraform,
rerun this command to reinitialize your working directory. If you forget, other
commands will detect it and remind you to do so if necessary.
```

```bash
terraform plan
```

Result:

```bash
data.yandex_compute_image.ubuntu: Reading...
data.yandex_compute_image.ubuntu: Read complete after 0s [id=fd8t9g30r3pc23et5krl]

Terraform used the selected providers to generate the following execution plan. Resource actions are indicated with the following symbols:
  + create

Terraform will perform the following actions:

  # yandex_compute_instance.this will be created
  + resource "yandex_compute_instance" "this" {
      + created_at                = (known after apply)
      + description               = "Smallest free‑tier VM"
      + folder_id                 = (known after apply)
      + fqdn                      = (known after apply)
      + gpu_cluster_id            = (known after apply)
      + hardware_generation       = (known after apply)
      + hostname                  = (known after apply)
      + id                        = (known after apply)
      + labels                    = {
          + "environment" = "dev"
          + "managed_by"  = "terraform"
        }
      + maintenance_grace_period  = (known after apply)
      + maintenance_policy        = (known after apply)
      + metadata                  = {
          + "ssh-keys" = (sensitive value)
        }
      + name                      = "myapp-vm"
      + network_acceleration_type = "standard"
      + platform_id               = "standard-v1"
      + status                    = (known after apply)
      + zone                      = "ru-central1-b"

      + boot_disk {
          + auto_delete = true
          + device_name = (known after apply)
          + disk_id     = (known after apply)
          + mode        = (known after apply)

          + initialize_params {
              + block_size  = (known after apply)
              + description = (known after apply)
              + image_id    = "fd8t9g30r3pc23et5krl"
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
          + core_fraction = 100
          + cores         = 2
          + memory        = 2
        }

      + scheduling_policy (known after apply)
    }

  # yandex_vpc_network.this will be created
  + resource "yandex_vpc_network" "this" {
      + created_at                = (known after apply)
      + default_security_group_id = (known after apply)
      + description               = "VPC for myapp"
      + folder_id                 = (known after apply)
      + id                        = (known after apply)
      + labels                    = {
          + "environment" = "dev"
          + "managed_by"  = "terraform"
        }
      + name                      = "myapp-net"
      + subnet_ids                = (known after apply)
    }

  # yandex_vpc_security_group.this will be created
  + resource "yandex_vpc_security_group" "this" {
      + created_at  = (known after apply)
      + description = "Security group for myapp"
      + folder_id   = (known after apply)
      + id          = (known after apply)
      + labels      = {
          + "environment" = "dev"
          + "managed_by"  = "terraform"
        }
      + name        = "myapp-sg"
      + network_id  = (known after apply)
      + status      = (known after apply)

      + egress {
          + description       = "Allow all outgoing"
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
          + description       = "Custom app port"
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
              + "188.130.155.186/32",
            ]
          + v6_cidr_blocks    = []
            # (2 unchanged attributes hidden)
        }
    }

  # yandex_vpc_subnet.this will be created
  + resource "yandex_vpc_subnet" "this" {
      + created_at     = (known after apply)
      + description    = "Subnet in ru-central1-b"
      + folder_id      = (known after apply)
      + id             = (known after apply)
      + labels         = {
          + "environment" = "dev"
          + "managed_by"  = "terraform"
        }
      + name           = "myapp-subnet"
      + network_id     = (known after apply)
      + v4_cidr_blocks = [
          + "10.0.1.0/24",
        ]
      + v6_cidr_blocks = (known after apply)
      + zone           = "ru-central1-b"
    }

Plan: 4 to add, 0 to change, 0 to destroy.

Changes to Outputs:
  + instance_id            = (known after apply)
  + instance_public_ip     = (known after apply)
  + ssh_connection_command = (known after apply)
```

```bash
terraform apply
```

Result:

```bash
Do you want to perform these actions?
  Terraform will perform the actions described above.
  Only 'yes' will be accepted to approve.

  Enter a value: yes

yandex_vpc_network.this: Creating...
yandex_vpc_network.this: Creation complete after 3s [id=enp0mmof5f46gvujil55]
yandex_vpc_subnet.this: Creating...
yandex_vpc_security_group.this: Creating...
yandex_vpc_subnet.this: Creation complete after 0s [id=e2lfnk9s6b4f46tp6pnt]
yandex_vpc_security_group.this: Creation complete after 2s [id=enp6hadpkime1fp0a1k7]
yandex_compute_instance.this: Creating...
yandex_compute_instance.this: Still creating... [00m10s elapsed]
yandex_compute_instance.this: Still creating... [00m20s elapsed]
yandex_compute_instance.this: Still creating... [00m30s elapsed]
yandex_compute_instance.this: Still creating... [00m40s elapsed]
yandex_compute_instance.this: Still creating... [00m50s elapsed]
yandex_compute_instance.this: Still creating... [01m00s elapsed]
yandex_compute_instance.this: Creation complete after 1m9s [id=epd684bbsfho6rig2t20]

Apply complete! Resources: 4 added, 0 changed, 0 destroyed.

Outputs:

instance_id = "epd684bbsfho6rig2t20"
instance_public_ip = "89.169.165.116"
ssh_connection_command = "ssh ubuntu@89.169.165.116"
```

Connection by ssh:

```bash
PS ...\DevOps-Core-Course\labs\cloud-terraform> ssh ubuntu@89.169.165.116
The authenticity of host '89.169.165.116 (89.169.165.116)' can't be established.
ED25519 key fingerprint is <some_key>
This key is not known by any other names.
Are you sure you want to continue connecting (yes/no/[fingerprint])? yes
Warning: Permanently added '89.169.165.116' (ED25519) to the list of known hosts.
Welcome to Ubuntu 22.04.5 LTS (GNU/Linux 5.15.0-170-generic x86_64)

 * Documentation:  https://help.ubuntu.com
 * Management:     https://landscape.canonical.com
 * Support:        https://ubuntu.com/pro

 System information as of Wed Feb 18 16:17:12 UTC 2026

  System load:  0.03              Processes:             99
  Usage of /:   9.5% of 18.73GB   Users logged in:       0
  Memory usage: 7%                IPv4 address for eth0: 10.0.1.10
  Swap usage:   0%

 * Strictly confined Kubernetes makes edge and IoT secure. Learn how MicroK8s
   just raised the bar for easy, resilient and secure K8s cluster deployment.

   https://ubuntu.com/engage/secure-kubernetes-at-the-edge

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

ubuntu@epd684bbsfho6rig2t20:~$ whoami
ubuntu
ubuntu@epd684bbsfho6rig2t20:~$ exit
logout
Connection to 89.169.165.116 closed.
```

```bash
terraform destroy
```

Result:

```bash
data.yandex_compute_image.ubuntu: Reading...
yandex_vpc_network.this: Refreshing state... [id=enp0mmof5f46gvujil55]
data.yandex_compute_image.ubuntu: Read complete after 0s [id=fd8t9g30r3pc23et5krl]
yandex_vpc_subnet.this: Refreshing state... [id=e2lfnk9s6b4f46tp6pnt]
yandex_vpc_security_group.this: Refreshing state... [id=enp6hadpkime1fp0a1k7]
yandex_compute_instance.this: Refreshing state... [id=epd684bbsfho6rig2t20]

Terraform used the selected providers to generate the following execution plan. Resource actions are indicated with the following symbols:
  - destroy

Terraform will perform the following actions:

  # yandex_compute_instance.this will be destroyed
  - resource "yandex_compute_instance" "this" {
      - created_at                = "2026-02-18T16:13:26Z" -> null
      - description               = "Smallest free‑tier VM" -> null
      - folder_id                 = "b1gvsq0cfkgg9k1g9t5t" -> null
      - fqdn                      = "epd684bbsfho6rig2t20.auto.internal" -> null
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
      - id                        = "epd684bbsfho6rig2t20" -> null
      - labels                    = {
          - "environment" = "dev"
          - "managed_by"  = "terraform"
        } -> null
      - metadata                  = {
          - "ssh-keys" = (sensitive value)
        } -> null
      - name                      = "myapp-vm" -> null
      - network_acceleration_type = "standard" -> null
      - platform_id               = "standard-v1" -> null
      - status                    = "running" -> null
      - zone                      = "ru-central1-b" -> null
        # (4 unchanged attributes hidden)

      - boot_disk {
          - auto_delete = true -> null
          - device_name = "epd2im7fj4nqatjfu79u" -> null
          - disk_id     = "epd2im7fj4nqatjfu79u" -> null
          - mode        = "READ_WRITE" -> null

          - initialize_params {
              - block_size  = 4096 -> null
              - image_id    = "fd8t9g30r3pc23et5krl" -> null
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
          - ip_address         = "10.0.1.10" -> null
          - ipv4               = true -> null
          - ipv6               = false -> null
          - mac_address        = "d0:0d:64:11:6b:e3" -> null
          - nat                = true -> null
          - nat_ip_address     = "89.169.165.116" -> null
          - nat_ip_version     = "IPV4" -> null
          - security_group_ids = [
              - "enp6hadpkime1fp0a1k7",
            ] -> null
          - subnet_id          = "e2lfnk9s6b4f46tp6pnt" -> null
            # (1 unchanged attribute hidden)
        }

      - placement_policy {
          - host_affinity_rules       = [] -> null
          - placement_group_partition = 0 -> null
            # (1 unchanged attribute hidden)
        }

      - resources {
          - core_fraction = 100 -> null
          - cores         = 2 -> null
          - gpus          = 0 -> null
          - memory        = 2 -> null
        }

      - scheduling_policy {
          - preemptible = false -> null
        }
    }

  # yandex_vpc_network.this will be destroyed
  - resource "yandex_vpc_network" "this" {
      - created_at                = "2026-02-18T16:13:21Z" -> null
      - default_security_group_id = "enpj6g0ru29e14ik68fb" -> null
      - description               = "VPC for myapp" -> null
      - folder_id                 = "b1gvsq0cfkgg9k1g9t5t" -> null
      - id                        = "enp0mmof5f46gvujil55" -> null
      - labels                    = {
          - "environment" = "dev"
          - "managed_by"  = "terraform"
        } -> null
      - name                      = "myapp-net" -> null
      - subnet_ids                = [
          - "e2lfnk9s6b4f46tp6pnt",
        ] -> null
    }

  # yandex_vpc_security_group.this will be destroyed
  - resource "yandex_vpc_security_group" "this" {
      - created_at  = "2026-02-18T16:13:25Z" -> null
      - description = "Security group for myapp" -> null
      - folder_id   = "b1gvsq0cfkgg9k1g9t5t" -> null
      - id          = "enp6hadpkime1fp0a1k7" -> null
      - labels      = {
          - "environment" = "dev"
          - "managed_by"  = "terraform"
        } -> null
      - name        = "myapp-sg" -> null
      - network_id  = "enp0mmof5f46gvujil55" -> null
      - status      = "ACTIVE" -> null

      - egress {
          - description       = "Allow all outgoing" -> null
          - from_port         = -1 -> null
          - id                = "enpc2251cj5sk6f5vm9n" -> null
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
          - description       = "Custom app port" -> null
          - from_port         = -1 -> null
          - id                = "enphg12ipfg0umn7idqn" -> null
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
          - id                = "enp3sl31mijjaduo0nen" -> null
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
          - id                = "enp67h46tkh535udmhf8" -> null
          - labels            = {} -> null
          - port              = 22 -> null
          - protocol          = "TCP" -> null
          - to_port           = -1 -> null
          - v4_cidr_blocks    = [
              - "188.130.155.186/32",
            ] -> null
          - v6_cidr_blocks    = [] -> null
            # (2 unchanged attributes hidden)
        }
    }

  # yandex_vpc_subnet.this will be destroyed
  - resource "yandex_vpc_subnet" "this" {
      - created_at     = "2026-02-18T16:13:24Z" -> null
      - description    = "Subnet in ru-central1-b" -> null
      - folder_id      = "b1gvsq0cfkgg9k1g9t5t" -> null
      - id             = "e2lfnk9s6b4f46tp6pnt" -> null
      - labels         = {
          - "environment" = "dev"
          - "managed_by"  = "terraform"
        } -> null
      - name           = "myapp-subnet" -> null
      - network_id     = "enp0mmof5f46gvujil55" -> null
      - v4_cidr_blocks = [
          - "10.0.1.0/24",
        ] -> null
      - v6_cidr_blocks = [] -> null
      - zone           = "ru-central1-b" -> null
        # (1 unchanged attribute hidden)
    }

Plan: 0 to add, 0 to change, 4 to destroy.

Changes to Outputs:
  - instance_id            = "epd684bbsfho6rig2t20" -> null
  - instance_public_ip     = "89.169.165.116" -> null
  - ssh_connection_command = "ssh ubuntu@89.169.165.116" -> null

Do you really want to destroy all resources?
  Terraform will destroy all your managed infrastructure, as shown above.
  There is no undo. Only 'yes' will be accepted to confirm.

  Enter a value: yes

yandex_compute_instance.this: Destroying... [id=epd684bbsfho6rig2t20]
yandex_compute_instance.this: Still destroying... [id=epd684bbsfho6rig2t20, 00m10s elapsed]
yandex_compute_instance.this: Still destroying... [id=epd684bbsfho6rig2t20, 00m20s elapsed]
yandex_compute_instance.this: Still destroying... [id=epd684bbsfho6rig2t20, 00m30s elapsed]
yandex_compute_instance.this: Destruction complete after 35s
yandex_vpc_subnet.this: Destroying... [id=e2lfnk9s6b4f46tp6pnt]        
yandex_vpc_security_group.this: Destroying... [id=enp6hadpkime1fp0a1k7]
yandex_vpc_security_group.this: Destruction complete after 1s
yandex_vpc_subnet.this: Destruction complete after 5s
yandex_vpc_network.this: Destroying... [id=enp0mmof5f46gvujil55]
yandex_vpc_network.this: Destruction complete after 1s

Destroy complete! Resources: 4 destroyed.
```

#### Pulumi ####

- Version: 3.221.0
- Language: Python
- Differences: variables can be stored through command. Uses .yaml instead of .tf
- Advantages: more easy to configure thanks to python
- Challenge: make this thing work


```bash
pulumi preview
```

Result:

```bash
Previewing update (dev)

View in Browser (Ctrl+O): https://app.pulumi.com/TheVex-org/project/dev/previews/93e53f8e-8866-40e5-9e98-5c376263315c

     Type                                  Name             Plan
 +   pulumi:pulumi:Stack                   project-dev      create
 +   ├─ yandex:index:VpcNetwork            myapp-net        create
 +   ├─ yandex:index:VpcSubnet             myapp-subnet     create
 +   ├─ yandex:index:VpcSecurityGroup      myapp-sg         create
 +   ├─ yandex:index:VpcSecurityGroupRule  myapp-sg-ssh     create
 +   ├─ yandex:index:VpcSecurityGroupRule  myapp-sg-http    create
 +   ├─ yandex:index:VpcSecurityGroupRule  myapp-sg-egress  create
 +   ├─ yandex:index:VpcSecurityGroupRule  myapp-sg-custom  create
 +   └─ yandex:index:ComputeInstance       myapp-vm         create
Outputs:
    instance_id           : [unknown]
    instance_public_ip    : [unknown]
    ssh_connection_command: [unknown]

Resources:
    + 9 to create
```

```bash
pulumi up
```
Result:

```bash
Previewing update (dev)

View in Browser (Ctrl+O): https://app.pulumi.com/TheVex-org/project/dev/previews/4254dc97-697e-498f-8e56-5e81fe7e2a69

     Type                                  Name             Plan
     pulumi:pulumi:Stack                   project-dev
 +   ├─ yandex:index:VpcNetwork            myapp-net        create
 +   ├─ yandex:index:VpcSubnet             myapp-subnet     create
 +   ├─ yandex:index:VpcSecurityGroup      myapp-sg         create
 +   ├─ yandex:index:VpcSecurityGroupRule  myapp-sg-ssh     create
 +   ├─ yandex:index:VpcSecurityGroupRule  myapp-sg-http    create
 +   ├─ yandex:index:VpcSecurityGroupRule  myapp-sg-egress  create
 +   ├─ yandex:index:VpcSecurityGroupRule  myapp-sg-custom  create
 +   └─ yandex:index:ComputeInstance       myapp-vm         create
Outputs:
  + instance_id           : [unknown]
  + instance_public_ip    : [unknown]
  + ssh_connection_command: [unknown]

Resources:
    + 8 to create
    1 unchanged

Do you want to perform this update? yes
Updating (dev)

View in Browser (Ctrl+O): https://app.pulumi.com/TheVex-org/project/dev/updates/2

     Type                                  Name             Status
     pulumi:pulumi:Stack                   project-dev
 +   ├─ yandex:index:VpcNetwork            myapp-net        created (3s)
 +   ├─ yandex:index:VpcSubnet             myapp-subnet     created (0.85s)
 +   ├─ yandex:index:VpcSecurityGroup      myapp-sg         created (3s)
 +   ├─ yandex:index:VpcSecurityGroupRule  myapp-sg-ssh     created (0.89s)
 +   ├─ yandex:index:VpcSecurityGroupRule  myapp-sg-http    created (1s)
 +   ├─ yandex:index:VpcSecurityGroupRule  myapp-sg-egress  created (2s)
 +   ├─ yandex:index:VpcSecurityGroupRule  myapp-sg-custom  created (2s)
 +   └─ yandex:index:ComputeInstance       myapp-vm         created (47s)
Outputs:
  + instance_id           : "epdu0f54cs0a458ek1s8"
  + instance_public_ip    : "158.160.30.41"
  + ssh_connection_command: "ssh ubuntu@158.160.30.41"

Resources:
    + 8 created
    1 unchanged

Duration: 1m1s
```

Connection by ssh:

```bash
(venv) C:\Users\Vexell\PycharmProjects\DevOps-Core-Course\labs\app_python\pulumi>ssh ubuntu@158.160.30.41
The authenticity of host '158.160.30.41 (158.160.30.41)' can't be established.
ED25519 key fingerprint is <some_key>.
This key is not known by any other names.
Are you sure you want to continue connecting (yes/no/[fingerprint])? yes
Warning: Permanently added '158.160.30.41' (ED25519) to the list of known hosts.
Welcome to Ubuntu 22.04.5 LTS (GNU/Linux 5.15.0-170-generic x86_64)

 * Documentation:  https://help.ubuntu.com
 * Management:     https://landscape.canonical.com
 * Support:        https://ubuntu.com/pro

 System information as of Wed Feb 18 17:58:32 UTC 2026

  System load:  0.0               Processes:             100
  Usage of /:   9.5% of 18.73GB   Users logged in:       0
  Memory usage: 8%                IPv4 address for eth0: 10.0.1.22
  Swap usage:   0%

 * Strictly confined Kubernetes makes edge and IoT secure. Learn how MicroK8s
   just raised the bar for easy, resilient and secure K8s cluster deployment.

   https://ubuntu.com/engage/secure-kubernetes-at-the-edge

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

ubuntu@epdu0f54cs0a458ek1s8:~$ whoami
ubuntu
ubuntu@epdu0f54cs0a458ek1s8:~$ exit
logout
Connection to 158.160.30.41 closed.
```

```bash
pulumi destroy
```

Result:

```bash
Previewing destroy (dev)

View in Browser (Ctrl+O): https://app.pulumi.com/TheVex-org/project/dev/previews/16e0a6a8-16c9-4990-8b2f-60f7fbd1c713

     Type                                  Name             Plan
     pulumi:pulumi:Stack                   project-dev
 -   pulumi:pulumi:Stack                   project-dev      delete
 -   ├─ yandex:index:VpcSecurityGroupRule  myapp-sg-custom  delete
 -   ├─ yandex:index:VpcSecurityGroupRule  myapp-sg-ssh     delete
 -   ├─ yandex:index:VpcSecurityGroupRule  myapp-sg-egress  delete
 -   ├─ yandex:index:ComputeInstance       myapp-vm         delete
 -   ├─ yandex:index:VpcSubnet             myapp-subnet     delete
 -   ├─ yandex:index:VpcSecurityGroup      myapp-sg         delete
 -   └─ yandex:index:VpcNetwork            myapp-net        delete
Outputs:
  - instance_id           : "epdu0f54cs0a458ek1s8"
  - instance_public_ip    : "158.160.30.41"
  - ssh_connection_command: "ssh ubuntu@158.160.30.41"

Resources:
    - 9 to delete

Do you want to perform this destroy? yes
Destroying (dev)

View in Browser (Ctrl+O): https://app.pulumi.com/TheVex-org/project/dev/updates/3

     Type                                  Name             Status
     pulumi:pulumi:Stack                   project-dev
 -   pulumi:pulumi:Stack                   project-dev      deleted (0.28s)
 -   ├─ yandex:index:VpcSecurityGroupRule  myapp-sg-egress  deleted (8s)
 -   ├─ yandex:index:VpcSecurityGroupRule  myapp-sg-custom  deleted (11s)
 -   ├─ yandex:index:VpcSecurityGroupRule  myapp-sg-http    deleted (13s)
 -   ├─ yandex:index:ComputeInstance       myapp-vm         deleted (41s)
 -   ├─ yandex:index:VpcSecurityGroup      myapp-sg         deleted (0.92s)
 -   ├─ yandex:index:VpcSubnet             myapp-subnet     deleted (20s)
 -   └─ yandex:index:VpcNetwork            myapp-net        deleted (2s)
Outputs:
  - instance_id           : "epdu0f54cs0a458ek1s8"
  - instance_public_ip    : "158.160.30.41"
  - ssh_connection_command: "ssh ubuntu@158.160.30.41"

Resources:
    - 9 deleted

Duration: 1m9s

The resources in the stack have been deleted, but the history and configuration associated with the stack are still maintained. 
If you want to remove the stack completely, run `pulumi stack rm dev`.
```


#### Terraform vs Pulumi ####

- Pulumi easier to learn because it is configurable with python
- However, Terraform is more readable for me
- Terraform was easier to debug
- Yandex Cloud has good guide to work with Terraform
- I will use Terraform always

#### Lab 5 Preparation ####

- I will not keep VM
- I will uses Terraform for Lab 5
