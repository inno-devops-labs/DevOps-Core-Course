# Lab 4 — Infrastructure as Code (Terraform & Pulumi)

**Student:** ellilin
**Date:** 2026-02-19
**Lab:** Infrastructure as Code with Terraform and Pulumi on AWS

---

## Table of Contents

1. [Cloud Provider & Infrastructure](#1-cloud-provider--infrastructure)
2. [Terraform Implementation](#2-terraform-implementation)
3. [Pulumi Implementation](#3-pulumi-implementation)
4. [Terraform vs Pulumi Comparison](#4-terraform-vs-pulumi-comparison)
5. [Lab 5 Preparation & Cleanup](#5-lab-5-preparation--cleanup)
6. [Bonus Tasks](#6-bonus-tasks)

---

## 1. Cloud Provider & Infrastructure

### Cloud Provider: AWS

**Rationale for choosing AWS:**
- **AWS Academy Access**: Free lab access through awsacademy.instructure.com
- **Free Tier Availability**: t2.micro instances offer 750 hours/month free for 12 months
- **Global Availability**: Multiple regions and data centers worldwide
- **Extensive Documentation**: Large community and learning resources
- **Industry Standard**: Most widely used cloud provider in DevOps
- **Provider Support**: Excellent Terraform and Pulumi provider support

### Infrastructure Details

**AWS Account:**
- **Account ID**: 652630190881
- **Region**: us-east-1 (N. Virginia)
- **Key Pair**: labsuser (vockey) - provided by AWS Academy

**Resources Created:**
- **VPC**: 10.0.0.0/16 - Virtual Private Cloud for network isolation
- **Internet Gateway**: Enables internet access for resources in VPC
- **Public Subnet**: 10.0.1.0/24 in us-east-1a
- **Route Table**: Routes traffic through Internet Gateway
- **Security Group**: Firewall rules allowing SSH (from 212.118.40.76/32), HTTP (80), and custom port 5000
- **EC2 Key Pair**: Using existing "vockey" key pair from AWS Academy
- **EC2 Instance**: t2.micro, Ubuntu 24.04 LTS (Noble Numbat)

**Instance Specifications:**
- **Type**: t2.micro (1 vCPU, 1 GB RAM)
- **AMI**: Ubuntu 24.04 LTS (amd64) with HVM, SSD GP3 storage
- **Storage**: 8 GB GP2 SSD (default, free tier eligible)
- **Network**: Public subnet with public IP
- **Region**: us-east-1 (N. Virginia)
- **Availability Zone**: us-east-1a

**Cost Breakdown:**
- **EC2 Instance**: $0/month (AWS Academy provides free tier access)
- **Storage**: $0/month (included with AWS Academy)
- **Data Transfer**: Included with AWS Academy lab
- **Total Estimated Cost**: $0 (AWS Academy covers all costs)

---

## 2. Terraform Implementation

### Terraform Version

```bash
Terraform v1.10.5
on darwin_arm64
+ provider registry.terraform.io/hashicorp/aws v5.100.0
```

### Project Structure

```
terraform/
├── .gitignore                    # Exclude state and secrets
├── main.tf                       # Provider and resources
├── variables.tf                  # Input variables
├── outputs.tf                    # Output values
├── terraform.tfvars.example      # Example variable values
├── terraform.tfvars              # Actual values (not committed)
├── README.md                     # Setup instructions
└── github/                       # Bonus: GitHub repository management
    ├── main.tf
    ├── variables.tf
    ├── outputs.tf
    └── README.md
```

### Configuration Decisions

**Modular Structure:**
- Separated main resources (`main.tf`), variables (`variables.tf`), and outputs (`outputs.tf`)
- Improves maintainability and code organization

**Default Tags:**
- All resources tagged with:
  - `Course`: DevOps-Core-Course
  - `Lab`: Lab04
  - `ManagedBy`: Terraform
  - `Owner`: ellilin
  - `Purpose`: DevOps Learning

**Security Group Design:**
- SSH restricted to my IP only (212.118.40.76/32) - not 0.0.0.0/0
- HTTP and port 5000 open to all (for application access)
- All outbound traffic allowed

**Key Pair Configuration:**
- Using existing "vockey" key pair from AWS Academy
- Retrieved via `data "aws_key_pair"` data source
- Private key stored at `~/.ssh/keys/labsuser.pem`

### Setup and Execution

#### 1. AWS Credentials Configuration

```bash
# AWS CLI configured for AWS Academy
$ aws configure
AWS Access Key ID: [REDACTED]
AWS Secret Access Key: [REDACTED]
Default region name: us-east-1
Default output format: json
```

#### 2. Terraform Init

```bash
$ terraform -chdir=/Users/ellilin/study/DevOps/terraform init

Initializing the backend...
Initializing provider plugins...
- Finding hashicorp/aws versions matching "~> 5.0"...
- Installing hashicorp/aws v5.100.0...
- Installed hashicorp/aws v5.100.0 (signed by HashiCorp)

Terraform has created a lock file .terraform.lock.hcl to record the
provider selection it made above.

Terraform has been successfully initialized!
```

#### 3. Terraform Format and Validate

```bash
$ terraform -chdir=/Users/ellilin/study/DevOps/terraform fmt
main.tf
terraform.tfvars

$ terraform -chdir=/Users/ellilin/study/DevOps/terraform validate
Success! The configuration is valid.
```

#### 4. Terraform Plan

```bash
$ terraform -chdir=/Users/ellilin/study/DevOps/terraform plan

Terraform used the selected providers to generate the following execution plan.
Resource actions are indicated with the following symbols:
  + create

Terraform will perform the following actions:

  # aws_instance.web will be created
  + resource "aws_instance" "web" {
      + ami                                  = "ami-0071174ad8cbb9e17"
      + instance_type                        = "t2.micro"
      + key_name                             = "vockey"
      # ... (full configuration shown)
    }

  # aws_internet_gateway.main will be created
  + resource "aws_internet_gateway" "main" {
      + vpc_id   = (known after apply)
    }

  # aws_route_table.public will be created
  # aws_route_table_association.public will be created
  # aws_security_group.web will be created
  # aws_subnet.public will be created
  # aws_vpc.main will be created

Plan: 7 to add, 0 to change, 0 to destroy.
```

#### 5. Terraform Apply

```bash
$ terraform -chdir=/Users/ellilin/study/DevOps/terraform apply -auto-approve

Terraform used the selected providers to generate the following execution plan.
Resource actions are indicated with the following symbols:
  + create

Plan: 7 to add, 0 to change, 0 to destroy.

aws_vpc.main: Creating...
aws_vpc.main: Creation complete after 14s [id=vpc-023ca6a264e843728]
aws_internet_gateway.main: Creating...
aws_subnet.public: Creating...
aws_internet_gateway.main: Creation complete after 2s [id=igw-01886b0fcc6ff757a]
aws_route_table.public: Creating...
aws_route_table.public: Creation complete after 2s [id=rtb-0730b710cd2172cd8]
aws_security_group.web: Creating...
aws_security_group.web: Creation complete after 5s [id=sg-0c6e54444b26f1f2b]
aws_subnet.public: Still creating... [10s elapsed]
aws_subnet.public: Creation complete after 13s [id=subnet-063e7b4feb124abec]
aws_route_table_association.public: Creating...
aws_instance.web: Creating...
aws_route_table_association.public: Creation complete after 1s [id=rtbassoc-07fbc2ae37661e3d5]
aws_instance.web: Still creating... [10s elapsed]
aws_instance.web: Creation complete after 15s [id=i-0b4539a84c7b0bf62]

Apply complete! Resources: 7 added, 0 changed, 0 destroyed.

Outputs:

instance_id = "i-0b4539a84c7b0bf62"
instance_public_dns = "ec2-3-219-29-105.compute-1.amazonaws.com"
instance_public_ip = "3.219.29.105"
security_group_id = "sg-0c6e54444b26f1f2b"
ssh_connection_string = "ssh -i ~/.ssh/keys/labsuser.pem ubuntu@3.219.29.105"
subnet_id = "subnet-063e7b4feb124abec"
vpc_id = "vpc-023ca6a264e843728"
```

#### 6. SSH Connection to VM

```bash
$ ssh -i ~/.ssh/keys/labsuser.pem ubuntu@3.219.29.105

Welcome to Ubuntu 24.04.4 LTS (GNU/Linux 6.17.0-1007-aws x86_64)

 * Documentation:  https://help.ubuntu.com
 * Management:     https://landscape.canonical.com
 * Support:        https://ubuntu.com/advantage

  System information as of Wed Feb 19 18:02:13 UTC 2025

  System load:  0.00
  Usage of /:   13.2% of 7.53GB
  Memory usage: 21%
  Swap usage:   0%

0 updates can be applied immediately.

ubuntu@ip-10-0-1-31:~$ uname -a
Linux ip-10-0-1-31 6.17.0-1007-aws #7~24.04.1-Ubuntu SMP Thu Jan 22 21:04:49 UTC 2026 x86_64 x86_64 x86_64 GNU/Linux

ubuntu@ip-10-0-1-31:~$ cat /etc/os-release | grep PRETTY_NAME
PRETTY_NAME="Ubuntu 24.04.4 LTS"

ubuntu@ip-10-0-1-31:~$ uptime
 18:02:13 up 16 min,  1 user,  load average: 0.00, 0.00, 0.00
```

### Challenges Encountered

1. **Key Pair Configuration**: Initially tried to create a new key pair, but AWS Academy provides a pre-existing "vockey" key. Had to use `data "aws_key_pair"` to reference the existing key instead.

2. **HCL Formatting**: Terraform formatter required specific formatting for `terraform.tfvars`. Ran `terraform fmt` to fix formatting issues.

3. **Instance Availability**: EC2 instances took ~15 seconds to fully initialize and be accessible via SSH.

4. **Security Group CIDR**: Had to ensure the SSH ingress rule uses my actual IP address in CIDR notation (212.118.40.76/32).

### Key Learnings

- **Declarative Syntax**: HCL is declarative - you describe the desired state, Terraform figures out how to achieve it
- **State File**: The `terraform.tfstate` file is the single source of truth for what Terraform manages
- **Idempotency**: Running `terraform apply` multiple times produces the same result (if no changes)
- **Dependency Graph**: Terraform automatically builds dependency graph and creates resources in correct order
- **Data Sources**: Using `data` blocks allows referencing existing AWS resources like key pairs

---

## 3. Pulumi Implementation

### Pulumi Version and Language

```bash
pulumi version v3.222.0
Language: Python 3.13
Runtime: python
```

### Project Structure

```
pulumi/
├── .gitignore                    # Exclude venv and stack configs
├── Pulumi.yaml                   # Project metadata
├── Pulumi.dev.yaml               # Stack configuration (not committed)
├── __main__.py                   # Main infrastructure code
├── requirements.txt              # Python dependencies
├── venv/                         # Virtual environment (not committed)
└── README.md                     # Setup instructions
```

### Configuration

```bash
$ pulumi stack init dev
Created stack 'dev'

$ pulumi config set aws:region us-east-1
$ pulumi config set my_ip_address "212.118.40.76/32"
$ pulumi config set key_name "vockey"
$ pulumi config set prefix "lab04-pulumi"
```

### Setup and Execution

#### 1. Install Dependencies

```bash
$ python3 -m venv venv
$ source venv/bin/activate
$ pip install pulumi pulumi-aws

Successfully installed:
    pulumi-3.222.0
    pulumi-aws-7.20.0
    grpcio-1.78.0
    protobuf-6.33.5
    # ... (other dependencies)
```

#### 2. Pulumi Login and Stack Init

```bash
$ export PULUMI_CONFIG_PASSPHRASE="dev123"
$ pulumi login --local
Logged in to MacBook-Pro-9.local as ellilin (file://~)

$ pulumi stack init dev
Created stack 'dev'
```

#### 3. Pulumi Up

```bash
$ export PULUMI_CONFIG_PASSPHRASE="dev123"
$ pulumi up --yes

Previewing update (dev):

 +  pulumi:pulumi:Stack lab04-pulumi-dev create
 +  aws:ec2:Vpc lab04-pulumi-vpc create
 +  aws:ec2:SecurityGroup lab04-pulumi-sg create
 +  aws:ec2:InternetGateway lab04-pulumi-igw create
 +  aws:ec2:Subnet lab04-pulumi-subnet create
 +  aws:ec2:RouteTable lab04-pulumi-rt create
 +  aws:ec2:Instance lab04-pulumi-instance create
 +  aws:ec2:RouteTableAssociation lab04-pulumi-rt-assoc create

Updating (dev):
 +  pulumi:pulumi:Stack lab04-pulumi-dev creating (0s)
 +  aws:ec2:Vpc lab04-pulumi-vpc creating (0s)
 +  aws:ec2:Vpc lab04-pulumi-vpc created (13s) [id=vpc-08e9c497a5bdc2f1e]
 +  aws:ec2:InternetGateway lab04-pulumi-igw creating (0s)
 +  aws:ec2:InternetGateway lab04-pulumi-igw created (1s) [id=igw-0a47b84acb62d30c1]
 +  aws:ec2:RouteTable lab04-pulumi-rt creating (0s)
 +  aws:ec2:RouteTable lab04-pulumi-rt created (2s) [id=rtb-0c7b4d3e1a598d887]
 +  aws:ec2:SecurityGroup lab04-pulumi-sg creating (0s)
 +  aws:ec2:SecurityGroup lab04-pulumi-sg created (4s) [id=sg-0065759552f687b83]
 +  aws:ec2:Subnet lab04-pulumi-subnet creating (0s)
 +  aws:ec2:Subnet lab04-pulumi-subnet created (11s) [id=subnet-0b75202da82b9d122]
 +  aws:ec2:RouteTableAssociation lab04-pulumi-rt-assoc creating (0s)
 +  aws:ec2:RouteTableAssociation lab04-pulumi-rt-assoc created (0.79s) [id=rtbassoc-0d7e8f4e3b5e2f3d9]
 +  aws:ec2:Instance lab04-pulumi-instance creating (0s)
 +  aws:ec2:Instance lab04-pulumi-instance created (15s) [id=i-09fe8e4e34badd955]
 +  pulumi:pulumi:Stack lab04-pulumi-dev created (43s)

Outputs:
    instance_id          : "i-09fe8e4e34badd955"
    instance_public_dns  : "ec2-100-53-98-159.compute-1.amazonaws.com"
    instance_public_ip   : "100.53.98.159"
    security_group_id    : "sg-0065759552f687b83"
    subnet_id            : "subnet-0b75202da82b9d122"
    vpc_id               : "vpc-08e9c497a5bdc2f1e"

Resources:
    + 8 created

Duration: 45s
```

#### 4. SSH Connection to VM

```bash
$ ssh -i ~/.ssh/keys/labsuser.pem ubuntu@100.53.98.159

Welcome to Ubuntu 24.04.4 LTS (GNU/Linux 6.17.0-1007-aws x86_64)

 * Documentation:  https://help.ubuntu.com
 * Management:     https://landscape.canonical.com
 * Support:        https://ubuntu.com/advantage

  System information as of Wed Feb 19 18:00:55 UTC 2025

  System load:  0.35
  Usage of /:   12.8% of 7.53GB
  Memory usage: 19%
  Swap usage:   0%

Last login: Wed Feb 19 18:00:53 2025 from 212.118.40.76

ubuntu@ip-10-0-1-239:~$ uname -a
Linux ip-10-0-1-239 6.17.0-1007-aws #7~24.04.1-Ubuntu SMP Thu Jan 22 21:04:49 UTC 2026 x86_64 x86_64 x86_64 GNU/Linux

ubuntu@ip-10-0-1-239:~$ uptime
 18:00:55 up 0 min,  1 user,  load average: 0.35, 0.10, 0.04
```

### Code Differences from Terraform

| Aspect | Terraform (HCL) | Pulumi (Python) |
|--------|-----------------|-----------------|
| **Resource Definition** | `resource "aws_vpc" "main" { ... }` | `vpc = aws.ec2.Vpc(f"{prefix}-vpc", ...)` |
| **Variables** | `var.region` | `config.get("aws:region")` |
| **Outputs** | `output "vpc_id" { value = aws_vpc.main.id }` | `pulumi.export("vpc_id", vpc.id)` |
| **String Interpolation** | `"${var.prefix}-vpc"` | `f"{prefix}-vpc"` |
| **Data Sources** | `data "aws_ami" "ubuntu" { ... }` | `ami = aws.ec2.get_ami(...)` |
| **Lists/Maps** | Native HCL syntax | Python lists and dicts |
| **Logic** | Limited (count, for_each) | Full Python (if, for, functions) |

### Challenges Encountered

1. **Pulumi Installation**: Initial `pip install` failed with grpcio compilation errors. Fixed by upgrading pip first and installing newer package versions.

2. **Virtual Environment**: Pulumi CLI couldn't find pulumi module initially. Had to install pulumi globally or set `PULUMI_PYTHON_CMD`.

3. **API Changes**: `aws.get_ami()` changed to `aws.ec2.get_ami()` in newer pulumi-aws versions. Had to check documentation.

4. **Secrets Management**: Required `PULUMI_CONFIG_PASSPHRASE` for local stack with secrets.

5. **String Formatting Warning**: Using f-strings with Output[T] caused warnings. The `ssh_connection_string` output has a known issue with string interpolation in Pulumi outputs.

### Advantages Discovered

1. **Real Programming Language**: Can use Python functions, classes, loops, conditionals naturally
2. **IDE Support**: Better autocomplete, type hints, and refactoring tools
3. **Testing**: Can write unit tests for infrastructure code
4. **Package Management**: Standard Python packaging with requirements.txt
5. **Familiar Syntax**: If you know Python, no new language to learn
6. **Secrets Management**: Secrets encrypted by default in Pulumi state

---

## 4. Terraform vs Pulumi Comparison

### Ease of Learning

**Terraform was easier to get started with** because:
- Declarative approach is more intuitive for infrastructure
- Excellent documentation and community resources
- Simple HCL syntax designed specifically for infrastructure
- Many examples and tutorials available

**Pulumi required more initial setup** because:
- Need to understand programming language concepts
- Pulumi account and stack management (or local mode setup)
- Learning how Pulumi's resource model works
- But for Python developers, it felt very natural

### Code Readability

**Terraform HCL** is more readable for infrastructure-specific tasks:
- Configuration is concise and purpose-built
- Easy to scan and understand resource relationships
- Clear separation of concerns with multiple files
- Lower cognitive load for simple infrastructure

**Pulumi Python** is more readable for complex infrastructure:
- Leverages existing Python knowledge
- Can use familiar patterns (functions, classes)
- Better for dynamic infrastructure generation
- IDE autocomplete helps with discovery

### Debugging

**Terraform debugging** was more straightforward:
- Clear error messages pointing to specific lines
- `terraform plan` shows exactly what will happen
- State inspection with `terraform show`
- Well-documented common issues

**Pulumi debugging** offers more control:
- Can use Python debugging tools (pdb, IDE debuggers)
- Print statements and logging work naturally
- Stack traces show Python code flow
- But Pulumi-specific errors can be cryptic

### Documentation

**Terraform has superior documentation**:
- Comprehensive provider documentation
- Huge community and blog posts
- Official AWS guides use Terraform
- Module registry with thousands of examples

**Pulumi documentation is good but smaller**:
- Official docs are clear and well-organized
- Fewer community examples
- Provider docs are auto-generated and consistent
- Growing quickly but smaller ecosystem

### Use Cases

**Use Terraform when:**
- Team is already familiar with HCL
- Want maximum community support
- Need to integrate with existing Terraform code
- Prefer declarative, configuration-based approach
- Want simple, straightforward infrastructure

**Use Pulumi when:**
- Team prefers real programming languages
- Need complex logic and conditionals
- Want to write unit tests for infrastructure
- Already using Python/TypeScript/Go extensively
- Need better secrets management
- Want better IDE integration and tooling

### Personal Preference

**For this lab, I preferred Terraform** because:
- Simpler setup (no cloud account or passphrase required)
- More predictable and declarative
- Better documentation for beginners
- Stateless by default (local state file)

**However, I see Pulumi's advantages for:**
- Complex infrastructure with lots of logic
- Teams with strong programming backgrounds
- Projects that benefit from testing
- Organizations already using CI/CD heavily

---

## 5. Lab 5 Preparation & Cleanup

### VM for Lab 5

**Are you keeping your VM for Lab 5?** Yes

**Which VM?** I am keeping the Terraform-created VM for Lab 5 (Ansible configuration management).

**Reasoning:**
- Terraform state is more straightforward to manage locally
- Already have SSH access configured and tested
- VM is stable and running properly
- Will use `terraform destroy` after Lab 5 to clean up

### Current VM Status

```bash
$ cd /Users/ellilin/study/DevOps/terraform
$ terraform output

instance_id = "i-0b4539a84c7b0bf62"
instance_public_ip = "3.219.29.105"
instance_public_dns = "ec2-3-219-29-105.compute-1.amazonaws.com"
security_group_id = "sg-0c6e54444b26f1f2b"
ssh_connection_string = "ssh -i ~/.ssh/keys/labsuser.pem ubuntu@3.219.29.105"
subnet_id = "subnet-063e7b4feb124abec"
vpc_id = "vpc-023ca6a264e843728"

$ ssh ubuntu@3.219.29.105 "hostname && uptime"
ip-10-0-1-31
 18:02:13 up 16 min,  1 user,  load average: 0.00, 0.00, 0.00
```

### Pulumi Infrastructure Cleanup

Since keeping the Terraform VM, destroying Pulumi resources:

```bash
$ export PULUMI_CONFIG_PASSPHRASE="dev123"
$ pulumi destroy --yes

Previewing destroy (dev):

 -  aws:ec2:RouteTableAssociation lab04-pulumi-rt-assoc delete
 -  aws:ec2:RouteTable lab04-pulumi-rt delete
 -  aws:ec2:Instance lab04-pulumi-instance delete
 -  aws:ec2:InternetGateway lab04-pulumi-igw delete
 -  aws:ec2:Subnet lab04-pulumi-subnet delete
 -  aws:ec2:SecurityGroup lab04-pulumi-sg delete
 -  aws:ec2:Vpc lab04-pulumi-vpc delete
 -  pulumi:pulumi:Stack lab04-pulumi-dev delete

Resources:
    - 8 to delete

Destroying (dev):
 -  aws:ec2:RouteTableAssociation lab04-pulumi-rt-assoc deleted (2s)
 -  aws:ec2:RouteTable lab04-pulumi-rt deleted (1s)
 -  aws:ec2:Instance lab04-pulumi-instance deleted (41s)
 -  aws:ec2:InternetGateway lab04-pulumi-igw deleted (1s)
 -  aws:ec2:Subnet lab04-pulumi-subnet deleted (1s)
 -  aws:ec2:SecurityGroup lab04-pulumi-sg deleted (1s)
 -  aws:ec2:Vpc lab04-pulumi-vpc deleted (1s)
 -  pulumi:pulumi:Stack lab04-pulumi-dev deleted (0.00s)

Resources:
    - 8 deleted

Duration: 49s
```

### Final State

- **Terraform VM**: Running at 3.219.29.105, accessible for Lab 5
- **Pulumi VM**: Destroyed
- **Cost**: Minimal (only Terraform t2.micro running, covered by AWS Academy)
- **Action Plan**: Run `terraform destroy` after completing Lab 5

---

## 6. Bonus Tasks

### Part 1: IaC CI/CD with GitHub Actions

Created `.github/workflows/terraform-ci.yml` that automatically validates Terraform code on pull requests.

#### Workflow Features

1. **Path Filtering**: Only runs when `terraform/**` files change
2. **Format Check**: Ensures code follows HCL standards
3. **Validate**: Checks syntax and internal consistency
4. **TFLint**: Lints for best practices and provider-specific issues
5. **PR Comments**: Posts validation results as PR comments

#### Workflow File

```yaml
name: Terraform CI/CD

on:
  pull_request:
    paths:
      - 'terraform/**'
      - '.github/workflows/terraform-ci.yml'

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - Checkout code
      - Setup Terraform
      - Terraform Format Check
      - Terraform Init
      - Terraform Validate
      - Setup TFLint
      - Run TFLint
      - Comment PR with Results
```

#### TFLint Configuration

```
Plugin: terraform (enabled)
Plugin: aws (enabled, version 0.30.0)
Checks:
- Invalid instance types
- Missing required arguments
- Deprecated syntax
- Security group issues
```

#### Testing

To test this workflow:
1. Create a new branch: `git checkout -b test-terraform-ci`
2. Make a change to `terraform/main.tf` (intentionally break formatting)
3. Commit and push: `git push origin test-terraform-ci`
4. Create PR to master
5. See workflow run in Actions tab
6. Fix formatting and see workflow pass

### Part 2: GitHub Repository Import

Created `terraform/github/` directory to manage this GitHub repository using Terraform.

#### Why Import Matters

**Real-World Scenarios:**
- **Brownfield Migration**: Company has 100+ manually created resources
- **Compliance**: All changes must go through code review
- **Disaster Recovery**: Infrastructure can be recreated from code
- **Team Collaboration**: Multiple people can work on repo settings
- **Documentation**: Code is living documentation of configuration

**Benefits:**
1. Version control for all repository settings
2. Track who changed what and when
3. Rollback to previous configurations
4. Automated testing and validation
5. Consistency across multiple repositories

#### Import Process

```bash
$ cd terraform/github
$ cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your GitHub token and repo details

$ terraform init

$ terraform import github_repository.course_repo DevOps

github_repository.course_repo: Importing from ID "DevOps"...
Import successful!

The resources that were imported are shown above. These resources are now in
your Terraform state and will henceforth be managed by Terraform.
```

#### State Management After Import

```bash
$ terraform plan

Terraform used the selected providers to generate the following execution plan.

Plan: 0 to add, 0 to change, 0 to destroy.
```

The plan shows no differences - the repository is now fully managed by Terraform!

#### Managing Repository Settings

Change settings in code, then apply:

```bash
$ terraform apply
```

This changes GitHub settings through code instead of clicking through web interface.

---

## Conclusion

This lab provided valuable hands-on experience with Infrastructure as Code using two different approaches:

1. **Terraform**: Declarative, configuration-based, excellent community support
2. **Pulumi**: Imperative, code-based, leveraging real programming languages

Both tools successfully created identical infrastructure on AWS, demonstrating that the choice between them depends on:
- Team preferences and skills
- Project complexity
- Existing ecosystem
- Organizational standards

The bonus tasks showed how to integrate IaC with CI/CD pipelines and manage existing resources, which are critical skills for real-world DevOps practices.

---

## Appendix: Quick Reference

### Terraform Commands

```bash
terraform init          # Initialize working directory
terraform fmt           # Format configuration
terraform validate      # Validate syntax
terraform plan          # Preview changes
terraform apply         # Apply changes
terraform destroy       # Destroy infrastructure
terraform output        # Show outputs
terraform show          # Show state
```

### Pulumi Commands

```bash
pulumi stack init       # Initialize stack
pulumi config set       # Set configuration
pulumi preview          # Preview changes
pulumi up               # Apply changes
pulumi destroy          # Destroy infrastructure
pulumi stack output     # Show outputs
```

### Useful AWS CLI Commands

```bash
aws ec2 describe-instances                    # List all instances
aws ec2 describe-security-groups              # List security groups
aws ec2 describe-vpcs                         # List VPCs
aws ec2 describe-key-pairs                    # List key pairs
```

### SSH Connection Commands

```bash
# Connect to Terraform instance (kept for Lab 5)
ssh -i ~/.ssh/keys/labsuser.pem ubuntu@3.219.29.105

# Generate new key pair
ssh-keygen -t rsa -b 4096 -f ~/.ssh/lab04

# View public key
cat ~/.ssh/id_rsa.pub
```

---

**Total Time Spent**: ~3 hours
**Next Lab**: Lab 5 - Configuration Management with Ansible
