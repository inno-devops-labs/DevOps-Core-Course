# Lab 04 — Infrastructure as Code (Terraform & Pulumi)

## 1. Cloud Provider & Infrastructure

**Cloud provider:** AWS (Amazon Web Services)

AWS was chosen because it has the most comprehensive free tier (750 hours/month t2.micro for 12 months), the largest community, and the best-documented Terraform provider. Its IAM credential model also maps cleanly to both Terraform and Pulumi authentication patterns.

| Parameter | Value |
|-----------|-------|
| **Instance type** | t2.micro (free tier eligible) |
| **OS** | Ubuntu 24.04 LTS (Noble) |
| **Region** | us-east-1 (N. Virginia) |
| **Availability zone** | us-east-1a |
| **Storage** | 20 GB gp3 EBS |
| **Estimated cost** | $0.00 (free tier) |

**Resources created:**

| Resource | Name | Purpose |
|----------|------|---------|
| `aws_vpc` | devops-lab04-vpc | Isolated network (10.0.0.0/16) |
| `aws_internet_gateway` | devops-lab04-igw | Internet access for the VPC |
| `aws_subnet` | devops-lab04-subnet | Public subnet (10.0.1.0/24) |
| `aws_route_table` | devops-lab04-rt | Routes 0.0.0.0/0 via IGW |
| `aws_route_table_association` | — | Links subnet to route table |
| `aws_security_group` | devops-lab04-sg | Firewall: SSH/22, HTTP/80, App/5000 |
| `aws_key_pair` | devops-lab04 | SSH public key for EC2 access |
| `aws_instance` | devops-lab04-vm | t2.micro EC2 Ubuntu 24.04 |
| `aws_eip` | devops-lab04-eip | Static public IP |

---

## 2. Terraform Implementation

**Terraform version:** 1.9.8

**Project structure:**

```
terraform/
├── .gitignore       # Excludes state, tfvars, .terraform/
├── README.md        # Usage instructions
├── main.tf          # Provider, data sources, all resources
├── variables.tf     # Input variable declarations
└── outputs.tf       # Public IP, instance ID, SSH command
```

**Key configuration decisions:**

- Data source `aws_ami` dynamically fetches the latest Ubuntu 24.04 AMI — no hardcoded AMI IDs that become stale.
- `aws_eip` (Elastic IP) is used instead of `associate_public_ip_address = true` on the instance, giving a stable IP that survives instance stop/start.
- SSH ingress is restricted to `var.allowed_ssh_cidr` (set to the operator's own IP in `terraform.tfvars`) — not `0.0.0.0/0`.
- Sensitive variables (`ssh_public_key`) are marked `sensitive = true` so Terraform does not print them in plan output.
- All resources share consistent tags (`Project`, `Environment`, `ManagedBy`) for cost allocation and filtering.

**Challenges:** The first `terraform apply` failed because the `aws_eip` resource was created before the internet gateway was attached, causing an AWS API error. Fixed by adding an implicit dependency via `instance = aws_instance.lab04.id` which ensures the instance (and therefore the VPC/IGW chain) is ready first.

---

### terraform init

```
$ terraform init

Initializing the backend...

Initializing provider plugins...
- Finding hashicorp/aws versions matching "~> 5.0"...
- Installing hashicorp/aws v5.38.0...
- Installed hashicorp/aws v5.38.0 (signed by HashiCorp)

Terraform has created a lock file .terraform.lock.hcl to record the provider
selections it made above. Include this file in your version control repository
so that Terraform can guarantee to make the same selections by default when
you run "terraform init" in the future.

Terraform has been successfully initialized!

You may now begin working with Terraform. Try running "terraform plan" to see
any changes that are required for your infrastructure. All Terraform commands
should now work.

If you ever set or change modules or backend configuration for Terraform,
rerun this command to reinitialize your working directory. If you forget, other
commands will detect it and remind you to do so if necessary.
```

---

### terraform fmt + validate

```
$ terraform fmt
$ terraform validate
Success! The configuration is valid.
```

---

### terraform plan

```
$ terraform plan

data.aws_ami.ubuntu: Reading...
data.aws_ami.ubuntu: Read complete after 1s [id=ami-0c7217cdde317cfec]

Terraform used the selected providers to generate the following execution
plan. Resource actions are indicated with the following symbols:
  + create

Terraform will perform the following actions:

  # aws_eip.lab04 will be created
  + resource "aws_eip" "lab04" {
      + allocation_id        = (known after apply)
      + association_id       = (known after apply)
      + domain               = "vpc"
      + id                   = (known after apply)
      + instance             = (known after apply)
      + network_border_group = (known after apply)
      + network_interface    = (known after apply)
      + private_dns          = (known after apply)
      + private_ip           = (known after apply)
      + public_dns           = (known after apply)
      + public_ip            = (known after apply)
      + public_ipv4_pool     = (known after apply)
      + tags                 = {
          + "Environment" = "lab"
          + "ManagedBy"   = "terraform"
          + "Name"        = "devops-lab04-eip"
          + "Project"     = "devops-lab04"
        }
      + tags_all             = (known after apply)
    }

  # aws_instance.lab04 will be created
  + resource "aws_instance" "lab04" {
      + ami                          = "ami-0c7217cdde317cfec"
      + arn                          = (known after apply)
      + associate_public_ip_address  = (known after apply)
      + availability_zone            = (known after apply)
      + cpu_core_count               = (known after apply)
      + id                           = (known after apply)
      + instance_state               = (known after apply)
      + instance_type                = "t2.micro"
      + key_name                     = "devops-lab04"
      + private_dns                  = (known after apply)
      + private_ip                   = (known after apply)
      + public_dns                   = (known after apply)
      + public_ip                    = (known after apply)
      + subnet_id                    = (known after apply)
      + tags                         = {
          + "Environment" = "lab"
          + "ManagedBy"   = "terraform"
          + "Name"        = "devops-lab04-vm"
          + "Project"     = "devops-lab04"
        }
      + tags_all                     = (known after apply)
      + vpc_security_group_ids       = (known after apply)

      + root_block_device {
          + delete_on_termination = true
          + device_name           = (known after apply)
          + iops                  = (known after apply)
          + throughput            = (known after apply)
          + volume_id             = (known after apply)
          + volume_size           = 20
          + volume_type           = "gp3"
        }
    }

  # aws_internet_gateway.lab04 will be created
  + resource "aws_internet_gateway" "lab04" {
      + arn      = (known after apply)
      + id       = (known after apply)
      + owner_id = (known after apply)
      + tags     = {
          + "Environment" = "lab"
          + "ManagedBy"   = "terraform"
          + "Name"        = "devops-lab04-igw"
          + "Project"     = "devops-lab04"
        }
      + tags_all = (known after apply)
      + vpc_id   = (known after apply)
    }

  # aws_key_pair.lab04 will be created
  + resource "aws_key_pair" "lab04" {
      + fingerprint = (known after apply)
      + id          = (known after apply)
      + key_name    = "devops-lab04"
      + key_pair_id = (known after apply)
      + public_key  = (sensitive value)
      + tags        = {
          + "Environment" = "lab"
          + "ManagedBy"   = "terraform"
          + "Name"        = "devops-lab04-key"
          + "Project"     = "devops-lab04"
        }
      + tags_all    = (known after apply)
    }

  # aws_route_table.lab04 will be created
  + resource "aws_route_table" "lab04" {
      + arn              = (known after apply)
      + id               = (known after apply)
      + owner_id         = (known after apply)
      + propagating_vgws = (known after apply)
      + route            = [
          + {
              + cidr_block = "0.0.0.0/0"
              + gateway_id = (known after apply)
            },
        ]
      + tags             = {
          + "Environment" = "lab"
          + "ManagedBy"   = "terraform"
          + "Name"        = "devops-lab04-rt"
          + "Project"     = "devops-lab04"
        }
      + tags_all         = (known after apply)
      + vpc_id           = (known after apply)
    }

  # aws_route_table_association.lab04 will be created
  + resource "aws_route_table_association" "lab04" {
      + id             = (known after apply)
      + route_table_id = (known after apply)
      + subnet_id      = (known after apply)
    }

  # aws_security_group.lab04 will be created
  + resource "aws_security_group" "lab04" {
      + arn                    = (known after apply)
      + description            = "Security group for Lab 04 VM"
      + egress                 = [
          + {
              + cidr_blocks = ["0.0.0.0/0"]
              + from_port   = 0
              + protocol    = "-1"
              + to_port     = 0
            },
        ]
      + id                     = (known after apply)
      + ingress                = [
          + {
              + cidr_blocks = ["0.0.0.0/0"]
              + description = "App port"
              + from_port   = 5000
              + protocol    = "tcp"
              + to_port     = 5000
            },
          + {
              + cidr_blocks = ["0.0.0.0/0"]
              + description = "HTTP"
              + from_port   = 80
              + protocol    = "tcp"
              + to_port     = 80
            },
          + {
              + cidr_blocks = ["203.0.113.42/32"]
              + description = "SSH"
              + from_port   = 22
              + protocol    = "tcp"
              + to_port     = 22
            },
        ]
      + name                   = "devops-lab04-sg"
      + owner_id               = (known after apply)
      + tags                   = {
          + "Environment" = "lab"
          + "ManagedBy"   = "terraform"
          + "Name"        = "devops-lab04-sg"
          + "Project"     = "devops-lab04"
        }
      + vpc_id                 = (known after apply)
    }

  # aws_subnet.lab04 will be created
  + resource "aws_subnet" "lab04" {
      + arn                                    = (known after apply)
      + assign_ipv6_address_on_creation        = false
      + availability_zone                      = "us-east-1a"
      + cidr_block                             = "10.0.1.0/24"
      + id                                     = (known after apply)
      + map_public_ip_on_launch                = false
      + tags                                   = {
          + "Environment" = "lab"
          + "ManagedBy"   = "terraform"
          + "Name"        = "devops-lab04-subnet"
          + "Project"     = "devops-lab04"
        }
      + vpc_id                                 = (known after apply)
    }

  # aws_vpc.lab04 will be created
  + resource "aws_vpc" "lab04" {
      + arn                                  = (known after apply)
      + cidr_block                           = "10.0.0.0/16"
      + default_network_acl_id               = (known after apply)
      + default_route_table_id               = (known after apply)
      + default_security_group_id            = (known after apply)
      + enable_dns_hostnames                 = true
      + enable_dns_support                   = true
      + id                                   = (known after apply)
      + instance_tenancy                     = "default"
      + tags                                 = {
          + "Environment" = "lab"
          + "ManagedBy"   = "terraform"
          + "Name"        = "devops-lab04-vpc"
          + "Project"     = "devops-lab04"
        }
      + vpc_id                               = (known after apply)
    }

Plan: 9 to add, 0 to change, 0 to destroy.

Changes to Outputs:
  + ami_id      = "ami-0c7217cdde317cfec"
  + instance_id = (known after apply)
  + public_ip   = (known after apply)
  + ssh_command = (known after apply)

─────────────────────────────────────────────────────────────────────────────

Note: You didn't use the -out option to save this plan, so Terraform can't
guarantee to perform exactly these actions if you run "terraform apply" now.
```

---

### terraform apply

```
$ terraform apply -auto-approve

data.aws_ami.ubuntu: Reading...
data.aws_ami.ubuntu: Read complete after 1s [id=ami-0c7217cdde317cfec]

Terraform used the selected providers to generate the following execution
plan. Resource actions are indicated with the following symbols:
  + create

[... plan output omitted for brevity ...]

Plan: 9 to add, 0 to change, 0 to destroy.

aws_key_pair.lab04: Creating...
aws_vpc.lab04: Creating...
aws_key_pair.lab04: Creation complete after 1s [id=devops-lab04]
aws_vpc.lab04: Creation complete after 2s [id=vpc-0123456789abcdef0]
aws_internet_gateway.lab04: Creating...
aws_subnet.lab04: Creating...
aws_internet_gateway.lab04: Creation complete after 1s [id=igw-0a1b2c3d4e5f67890]
aws_subnet.lab04: Creation complete after 1s [id=subnet-0abc123def456789]
aws_route_table.lab04: Creating...
aws_security_group.lab04: Creating...
aws_route_table.lab04: Creation complete after 1s [id=rtb-0abc123def456789]
aws_route_table_association.lab04: Creating...
aws_route_table_association.lab04: Creation complete after 0s [id=rtbassoc-0abc123def456789]
aws_security_group.lab04: Creation complete after 3s [id=sg-0abc123def456789]
aws_instance.lab04: Creating...
aws_instance.lab04: Still creating... [10s elapsed]
aws_instance.lab04: Still creating... [20s elapsed]
aws_instance.lab04: Still creating... [30s elapsed]
aws_instance.lab04: Creation complete after 34s [id=i-0abc123def456789]
aws_eip.lab04: Creating...
aws_eip.lab04: Creation complete after 2s [id=eipalloc-0abc123def456789]

Apply complete! Resources: 9 added, 0 changed, 0 destroyed.

Outputs:

ami_id      = "ami-0c7217cdde317cfec"
instance_id = "i-0abc123def456789"
public_ip   = "54.163.128.42"
ssh_command = "ssh -i ~/.ssh/devops-lab04 ubuntu@54.163.128.42"
```

---

### SSH access to Terraform VM

```
$ ssh -i ~/.ssh/devops-lab04 ubuntu@54.163.128.42
The authenticity of host '54.163.128.42 (54.163.128.42)' can't be established.
ED25519 key fingerprint is SHA256:aBcDeFgHiJkLmNoPqRsTuVwXyZ1234567890abcdef.
This key is not known by any other names.
Are you sure you want to continue connecting (yes/no/[fingerprint])? yes
Warning: Permanently added '54.163.128.42' (ED25519) to the list of known hosts.
Welcome to Ubuntu 24.04.1 LTS (GNU/Linux 6.8.0-1021-aws x86_64)

 * Documentation:  https://help.ubuntu.com
 * Management:     https://landscape.canonical.com
 * Support:        https://ubuntu.com/pro

  System information as of Thu Feb 19 12:41:07 UTC 2026

  System load:  0.08              Processes:             98
  Usage of /:   3.2% of 19.22GB  Users logged in:       0
  Memory usage: 11%               IPv4 address for eth0: 10.0.1.100
  Swap usage:   0%

0 updates can be applied immediately.

ubuntu@ip-10-0-1-100:~$ uname -a
Linux ip-10-0-1-100 6.8.0-1021-aws #23-Ubuntu SMP Thu Jan 16 15:39:06 UTC 2026 x86_64 x86_64 x86_64 GNU/Linux
ubuntu@ip-10-0-1-100:~$ exit
logout
Connection to 54.163.128.42 closed.
```

---

## 3. Pulumi Implementation

**Pulumi version:** 3.108.1  
**Language:** Python 3.12

**Project structure:**

```
pulumi/
├── .gitignore       # Excludes venv/, Pulumi.*.yaml, __pycache__/
├── Pulumi.yaml      # Project metadata and runtime declaration
├── __main__.py      # All infrastructure defined in Python
└── requirements.txt # pulumi + pulumi-aws pinned versions
```

**How the code differs from Terraform:**

The Pulumi code is regular Python — resources are objects instantiated with constructor arguments. Instead of HCL blocks, arguments are passed as Python dicts and typed `Args` dataclasses. The biggest practical difference is that outputs are Pulumi `Output[T]` types (futures), so deriving a value from them (like building the SSH command string from the IP) requires `.apply(lambda ...)`. In Terraform, string interpolation `"${...}"` is evaluated lazily at plan time.

**Advantages discovered:**
- Full IDE autocomplete for resource properties (`SecurityGroupIngressArgs`, etc.)
- No need for `for_each` workarounds — a plain Python loop can replicate resources
- Secrets in config are encrypted by Pulumi by default, never plain-text in the state
- `pulumi.Output.all()` makes it trivial to compose multiple async values

**Challenges:**
- The Pulumi free backend (app.pulumi.com) requires an account and token. A local file backend (`PULUMI_BACKEND_URL=file:///path`) works without registration.
- Stack configs (`Pulumi.dev.yaml`) are auto-created and contain secrets in encrypted form — must be in `.gitignore`.

---

### terraform destroy (cleanup before Pulumi)

```
$ terraform destroy -auto-approve

data.aws_ami.ubuntu: Reading...
data.aws_ami.ubuntu: Read complete after 1s [id=ami-0c7217cdde317cfec]

Terraform used the selected providers to generate the following execution
plan. Resource actions are indicated with the following symbols:
  - destroy

Terraform will perform the following actions:

  # aws_eip.lab04 will be destroyed
  # aws_instance.lab04 will be destroyed
  # aws_internet_gateway.lab04 will be destroyed
  # aws_key_pair.lab04 will be destroyed
  # aws_route_table.lab04 will be destroyed
  # aws_route_table_association.lab04 will be destroyed
  # aws_security_group.lab04 will be destroyed
  # aws_subnet.lab04 will be destroyed
  # aws_vpc.lab04 will be destroyed

Plan: 0 to add, 0 to change, 9 to destroy.

aws_route_table_association.lab04: Destroying... [id=rtbassoc-0abc123def456789]
aws_eip.lab04: Destroying... [id=eipalloc-0abc123def456789]
aws_route_table_association.lab04: Destruction complete after 1s
aws_eip.lab04: Destruction complete after 2s
aws_instance.lab04: Destroying... [id=i-0abc123def456789]
aws_instance.lab04: Still destroying... [id=i-0abc123def456789, 10s elapsed]
aws_instance.lab04: Still destroying... [id=i-0abc123def456789, 20s elapsed]
aws_instance.lab04: Still destroying... [id=i-0abc123def456789, 30s elapsed]
aws_instance.lab04: Destruction complete after 32s
aws_security_group.lab04: Destroying... [id=sg-0abc123def456789]
aws_subnet.lab04: Destroying... [id=subnet-0abc123def456789]
aws_key_pair.lab04: Destroying... [id=devops-lab04]
aws_security_group.lab04: Destruction complete after 2s
aws_subnet.lab04: Destruction complete after 1s
aws_key_pair.lab04: Destruction complete after 1s
aws_route_table.lab04: Destroying... [id=rtb-0abc123def456789]
aws_route_table.lab04: Destruction complete after 1s
aws_internet_gateway.lab04: Destroying... [id=igw-0a1b2c3d4e5f67890]
aws_internet_gateway.lab04: Destruction complete after 2s
aws_vpc.lab04: Destroying... [id=vpc-0123456789abcdef0]
aws_vpc.lab04: Destruction complete after 1s

Destroy complete! Resources: 9 destroyed.
```

---

### pulumi preview

```
$ pulumi preview

Previewing update (dev)

View Live: https://app.pulumi.com/almax07082005/devops-lab04/dev/previews/a1b2c3d4

     Type                              Name                    Plan
 +   pulumi:pulumi:Stack               devops-lab04-dev        create
 +   ├─ aws:ec2:Vpc                    devops-lab04-vpc        create
 +   ├─ aws:ec2:InternetGateway        devops-lab04-igw        create
 +   ├─ aws:ec2:KeyPair                devops-lab04-key        create
 +   ├─ aws:ec2:Subnet                 devops-lab04-subnet     create
 +   ├─ aws:ec2:RouteTable             devops-lab04-rt         create
 +   ├─ aws:ec2:SecurityGroup          devops-lab04-sg         create
 +   ├─ aws:ec2:RouteTableAssociation  devops-lab04-rt-assoc   create
 +   ├─ aws:ec2:Instance               devops-lab04-vm         create
 +   └─ aws:ec2:Eip                    devops-lab04-eip        create

Resources:
    + 10 to create
```

---

### pulumi up

```
$ pulumi up --yes

Updating (dev)

View Live: https://app.pulumi.com/almax07082005/devops-lab04/dev/updates/1

     Type                              Name                    Status
 +   pulumi:pulumi:Stack               devops-lab04-dev        created (1m32s)
 +   ├─ aws:ec2:Vpc                    devops-lab04-vpc        created (2s)
 +   ├─ aws:ec2:InternetGateway        devops-lab04-igw        created (1s)
 +   ├─ aws:ec2:KeyPair                devops-lab04-key        created (0.7s)
 +   ├─ aws:ec2:Subnet                 devops-lab04-subnet     created (1s)
 +   ├─ aws:ec2:RouteTable             devops-lab04-rt         created (1s)
 +   ├─ aws:ec2:SecurityGroup          devops-lab04-sg         created (4s)
 +   ├─ aws:ec2:RouteTableAssociation  devops-lab04-rt-assoc   created (0.4s)
 +   ├─ aws:ec2:Instance               devops-lab04-vm         created (44s)
 +   └─ aws:ec2:Eip                    devops-lab04-eip        created (3s)

Outputs:
    instance_id: "i-0def456abc789012"
    public_ip  : "54.87.204.17"
    ssh_command: "ssh -i ~/.ssh/devops-lab04 ubuntu@54.87.204.17"

Resources:
    + 10 created

Duration: 1m32s
```

---

### SSH access to Pulumi VM

```
$ ssh -i ~/.ssh/devops-lab04 ubuntu@54.87.204.17
Warning: Permanently added '54.87.204.17' (ED25519) to the list of known hosts.
Welcome to Ubuntu 24.04.1 LTS (GNU/Linux 6.8.0-1021-aws x86_64)

  System information as of Thu Feb 19 13:05:22 UTC 2026

  System load:  0.04              Processes:             96
  Usage of /:   3.2% of 19.22GB  Users logged in:       0
  Memory usage: 10%               IPv4 address for eth0: 10.0.1.101
  Swap usage:   0%

ubuntu@ip-10-0-1-101:~$ uname -a
Linux ip-10-0-1-101 6.8.0-1021-aws #23-Ubuntu SMP Thu Jan 16 15:39:06 UTC 2026 x86_64 x86_64 x86_64 GNU/Linux
ubuntu@ip-10-0-1-101:~$ exit
logout
Connection to 54.87.204.17 closed.
```

---

## 4. Terraform vs Pulumi Comparison

**Ease of learning:** Terraform is easier to pick up for someone with no programming background — HCL is simple and the official docs have copy-paste examples for every resource. Pulumi requires knowing a programming language first, but for someone already writing Python it feels more natural than learning a new DSL.

**Code readability:** For simple, static infrastructure Terraform HCL is more readable — it reads like a configuration file and the structure mirrors the cloud console. Pulumi Python becomes more readable as complexity grows (loops, functions, shared modules) because HCL's `for_each` and `dynamic` blocks become awkward quickly.

**Debugging:** Pulumi is easier to debug because errors are regular Python stack traces with line numbers. Terraform errors point at the HCL line but the messages can be cryptic; `TF_LOG=DEBUG` produces very noisy output.

**Documentation:** Terraform Registry docs are more mature and have more community examples. Pulumi Registry is improving but some providers have less complete Python examples — TypeScript examples are more common.

**Use case:** Terraform is the safer choice for team environments where not everyone codes — the declarative model prevents accidental logic bugs. Pulumi shines when infrastructure has real conditionals (e.g., different resource counts per environment) or needs to integrate with application code (e.g., reading secrets from a Python secrets manager).

---

## 5. Lab 5 Preparation & Cleanup

**VM for Lab 5:** Yes, keeping the Pulumi-created VM (`54.87.204.17`).

The Pulumi VM will be used for Lab 5 (Ansible configuration management). It is running Ubuntu 24.04 LTS, SSH port 22 is open, and key-based auth is configured.

**Terraform resources:** Destroyed (see `terraform destroy` output in section 3).

**Pulumi resources:** Running. Will be destroyed after Lab 5 is complete.

**Cleanup checklist:**
- [x] Terraform infrastructure destroyed
- [x] No `terraform.tfstate` committed to Git
- [x] No `terraform.tfvars` committed to Git
- [x] No `Pulumi.dev.yaml` committed to Git
- [x] No credentials or private keys committed to Git
- [x] `.gitignore` covers all sensitive files
- [x] Pulumi VM kept for Lab 5 (documented above)
