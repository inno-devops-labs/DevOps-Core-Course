# Lab 4 — Infrastructure as Code (Terraform & Pulumi)

![difficulty](https://img.shields.io/badge/difficulty-beginner-success)
![topic](https://img.shields.io/badge/topic-Infrastructure%20as%20Code-blue)
![points](https://img.shields.io/badge/points-10%2B2.5-orange)
![tech](https://img.shields.io/badge/tech-Terraform%20%7C%20Pulumi-informational)

> Provision cloud infrastructure using code with Terraform and Pulumi, comparing both approaches.

## Overview

Learn Infrastructure as Code (IaC) by creating virtual machines in the cloud using two popular tools: Terraform (declarative, HCL) and Pulumi (imperative, real programming languages).

**What You'll Learn:**
- Terraform fundamentals and HCL syntax
- Pulumi fundamentals and infrastructure with code
- Cloud provider APIs and resources
- Infrastructure lifecycle management
- IaC best practices and validation
- Comparing IaC tools and approaches

**Connection to Previous Labs:**
- **Lab 2:** Created Docker images - now we'll provision infrastructure to run them
- **Lab 3:** CI/CD for applications - now we'll add CI/CD for infrastructure
- **Lab 5:** Ansible will provision software on these VMs (you'll need a VM ready!)

**Tech Stack:** Terraform 1.9+ | Pulumi 3.x | Yandex Cloud / AWS

**Why Two Tools?**
By using both Terraform and Pulumi for the same task, you'll understand:
- Different IaC philosophies (declarative vs imperative)
- Tool trade-offs and use cases
- How to evaluate IaC tools for your needs

**Important for Lab 5:**
The VM you create in this lab will be used in **Lab 5 (Ansible)** for configuration management.

Recommended approach:
- Keep **one** cloud VM running until you complete Lab 5 (to avoid re-creating it).
- If you destroy it after Lab 4, recreate it later from your Terraform/Pulumi code.

---

## Important: Cloud Provider Selection

### Recommended for Russia: Yandex Cloud

Yandex Cloud offers free tier and is accessible in Russia:
- 1 VM with 20% vCPU, 1 GB RAM (free tier)
- 10 GB SSD storage
- No credit card required initially

### Alternative Cloud Providers

If Yandex Cloud is unavailable, choose any of these:

**VK Cloud (Russia):**
- Russian cloud provider
- Free trial with bonus credits
- Good documentation in Russian

**AWS (Amazon Web Services):**
- 750 hours/month free tier (t2.micro)
- Most popular globally
- Extensive documentation

**GCP (Google Cloud Platform):**
- $300 free credits for 90 days
- Always-free tier for e2-micro
- Modern interface

**Azure (Microsoft):**
- $200 free credits for 30 days
- Free tier for B1s instances
- Good Windows support

**DigitalOcean:**
- Simple pricing and interface
- $200 free credits with GitHub Student Pack
- Beginner-friendly

### Cost Management 🚨

**IMPORTANT - Read This:**
- ✅ **Use smallest/free tier instances only**
- ✅ **Run `terraform destroy` when done testing**
- ✅ **Consider keeping VM for Lab 5 to avoid recreation**
- ✅ **Set billing alerts if available**
- ✅ **If not using for Lab 5, delete resources after lab completion**
- ❌ **Never commit cloud credentials to Git**

---

## Tasks

### Task 1 — Terraform VM Creation (4 pts)

**Objective:** Create a virtual machine using Terraform on your chosen cloud provider.

**Requirements:**

1. **Setup Terraform**
   - Install Terraform CLI
   - Choose and configure your cloud provider
   - Set up authentication (access keys, service accounts, etc.)
   - Initialize Terraform

2. **Define Infrastructure**

   Create a `terraform/` directory with the following resources:

   **Minimum Required Resources:**
   - **VM/Compute Instance** (smallest free tier size)
   - **Network/VPC** (if required by provider)
   - **Security Group/Firewall Rules:**
     - Allow SSH (port 22) from your IP
     - Allow HTTP (port 80)
     - Allow custom port 5000 (for future app deployment)
   - **Public IP Address** (to access VM remotely)

3. **Configuration Best Practices**
   - Use variables for configurable values (region, instance type, etc.)
   - Use outputs to display important information (public IP, etc.)
   - Add appropriate tags/labels for resource identification
   - Use `.gitignore` for sensitive files

4. **Apply Infrastructure**
   - Run `terraform plan` to preview changes
   - Review the plan carefully
   - Apply infrastructure
   - Verify VM is accessible via SSH
   - Document the public IP and connection method

5. **State Management**
   - Keep state file local (for now)
   - Understand what the state file contains
   - **Never commit `terraform.tfstate` to Git**

<details>
<summary>💡 Terraform Fundamentals</summary>

**What is Terraform?**

Terraform is a declarative IaC tool that lets you define infrastructure in configuration files (HCL - HashiCorp Configuration Language).

**Key Concepts:**

**Providers:**
- Plugins that interact with cloud APIs
- Each cloud has its own provider (yandex, aws, google, azurerm)
- Configure authentication and region

**Resources:**
- Infrastructure components (VMs, networks, firewalls)
- Format: `resource "type" "name" { ... }`
- Each resource has required and optional arguments

**Data Sources:**
- Query existing infrastructure
- Example: Find latest Ubuntu image ID
- Format: `data "type" "name" { ... }`

**Variables:**
- Make configurations reusable
- Define in `variables.tf`
- Set values in `terraform.tfvars` (gitignored!)
- Reference: `var.variable_name`

**Outputs:**
- Display important values after apply
- Example: VM public IP
- Define in `outputs.tf`

**State File:**
- Tracks real infrastructure
- Maps config to reality
- **Never commit to Git** (contains sensitive data)
- Add to `.gitignore`

**Typical Workflow:**
```bash
terraform init      # Initialize provider plugins
terraform fmt       # Format code
terraform validate  # Check syntax
terraform plan      # Preview changes
terraform apply     # Create/update infrastructure
terraform destroy   # Delete all infrastructure
```

**Resources:**
- [Terraform Documentation](https://developer.hashicorp.com/terraform/docs)
- [Terraform Registry](https://registry.terraform.io/) - Provider docs
- [HCL Syntax](https://developer.hashicorp.com/terraform/language/syntax)

</details>

<details>
<summary>☁️ Yandex Cloud Terraform Guide</summary>

**Yandex Cloud Setup:**

**Authentication:**
- Create service account in Yandex Cloud Console
- Generate authorized key (JSON)
- Set key file path or use environment variables

**Provider Configuration Pattern:**
```hcl
terraform {
  required_providers {
    yandex = {
      source = "yandex-cloud/yandex"
    }
  }
}

provider "yandex" {
  # Configuration here (zone, folder_id, etc.)
}
```

**Key Resources:**
- `yandex_compute_instance` - Virtual machine
- `yandex_vpc_network` - Virtual private cloud
- `yandex_vpc_subnet` - Subnet within VPC
- `yandex_vpc_security_group` - Firewall rules

**Free Tier Instance:**
- Platform: standard-v2
- Cores: 2 (core_fraction = 20%)
- Memory: 1 GB
- Boot disk: 10 GB HDD

**SSH Access:**
- Add SSH public key to `metadata`
- Use `ssh-keys` metadata field
- Connect: `ssh <username>@<public_ip>`

**Resources:**
- [Yandex Cloud Terraform Provider](https://registry.terraform.io/providers/yandex-cloud/yandex/latest/docs)
- [Getting Started Guide](https://cloud.yandex.com/en/docs/tutorials/infrastructure-management/terraform-quickstart)
- [Compute Instance Example](https://registry.terraform.io/providers/yandex-cloud/yandex/latest/docs/resources/compute_instance)

</details>

<details>
<summary>☁️ AWS Terraform Guide</summary>

**AWS Setup:**

**Authentication:**
- Create IAM user with EC2 permissions
- Generate access key ID and secret access key
- Configure AWS CLI or use environment variables
- Never hardcode credentials

**Provider Configuration Pattern:**
```hcl
terraform {
  required_providers {
    aws = {
      source = "hashicorp/aws"
    }
  }
}

provider "aws" {
  region = var.region  # e.g., "us-east-1"
}
```

**Key Resources:**
- `aws_instance` - EC2 instance
- `aws_vpc` - Virtual Private Cloud
- `aws_subnet` - Subnet within VPC
- `aws_security_group` - Firewall rules
- `aws_key_pair` - SSH key

**Free Tier Instance:**
- Instance type: t2.micro
- AMI: Amazon Linux 2 or Ubuntu (find with data source)
- 750 hours/month free for 12 months
- 30 GB storage included

**Data Source for AMI:**
Use `aws_ami` data source to find latest Ubuntu image dynamically

**Resources:**
- [AWS Provider Documentation](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
- [EC2 Instance Resource](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/instance)
- [AWS Free Tier](https://aws.amazon.com/free/)

</details>

<details>
<summary>☁️ GCP Terraform Guide</summary>

**GCP Setup:**

**Authentication:**
- Create service account in Google Cloud Console
- Download JSON key file
- Set `GOOGLE_APPLICATION_CREDENTIALS` environment variable
- Enable Compute Engine API

**Provider Configuration Pattern:**
```hcl
terraform {
  required_providers {
    google = {
      source = "hashicorp/google"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}
```

**Key Resources:**
- `google_compute_instance` - VM instance
- `google_compute_network` - VPC network
- `google_compute_subnetwork` - Subnet
- `google_compute_firewall` - Firewall rules

**Free Tier Instance:**
- Machine type: e2-micro
- Zone: us-central1-a (or other free tier zone)
- Always free (within limits)
- Boot disk: 30 GB standard persistent disk

**Resources:**
- [Google Provider Documentation](https://registry.terraform.io/providers/hashicorp/google/latest/docs)
- [Compute Instance Resource](https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/compute_instance)
- [GCP Free Tier](https://cloud.google.com/free)

</details>

<details>
<summary>☁️ Other Cloud Providers</summary>

**Azure:**
- Provider: `azurerm`
- Resource: `azurerm_linux_virtual_machine`
- Free tier: B1s instance
- [Azure Provider Docs](https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs)

**VK Cloud:**
- Based on OpenStack
- Provider: OpenStack provider
- [VK Cloud Documentation](https://mcs.mail.ru/help/)

**DigitalOcean:**
- Provider: `digitalocean`
- Resource: `digitalocean_droplet`
- Simple and beginner-friendly
- [DigitalOcean Provider Docs](https://registry.terraform.io/providers/digitalocean/digitalocean/latest/docs)

**Questions to Explore:**
- What's the smallest instance size for your provider?
- How do you find the right OS image ID?
- What authentication method does your provider use?
- How do you add SSH keys to instances?

</details>

<details>
<summary>🔒 Security Best Practices</summary>

**Credentials Management:**

**❌ NEVER DO THIS:**
```hcl
provider "aws" {
  access_key = "AKIAIOSFODNN7EXAMPLE"  # NEVER!
  secret_key = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"  # NEVER!
}
```

**✅ DO THIS INSTEAD:**

**Option 1: Environment Variables**
```bash
export AWS_ACCESS_KEY_ID="your-key"
export AWS_SECRET_ACCESS_KEY="your-secret"
# Provider will auto-detect
```

**Option 2: Credentials File**
```bash
# ~/.aws/credentials (for AWS)
[default]
aws_access_key_id = your-key
aws_secret_access_key = your-secret
```

**Option 3: terraform.tfvars (gitignored)**
```hcl
# terraform.tfvars (add to .gitignore!)
access_key = "your-key"
secret_key = "your-secret"
```

**Files to Add to .gitignore:**
```
# Terraform
*.tfstate
*.tfstate.*
.terraform/
terraform.tfvars
*.tfvars
.terraform.lock.hcl

# Cloud credentials
*.pem
*.key
*.json  # Service account keys
credentials
```

**SSH Key Management:**
- Generate SSH key pair locally
- Add public key to cloud provider
- Keep private key secure (never commit)
- Use `chmod 600` on private key file

**Security Group Rules:**
- Restrict SSH to your IP only (not 0.0.0.0/0)
- Only open ports you need
- Document why each port is open

</details>

<details>
<summary>📁 Terraform Project Structure</summary>

**Recommended Structure:**

```
terraform/
├── .gitignore           # Ignore state, credentials
├── main.tf              # Main resources
├── variables.tf         # Input variables
├── outputs.tf           # Output values
├── terraform.tfvars     # Variable values (gitignored!)
└── README.md            # Setup instructions
```

**What Goes in Each File:**

**main.tf:**
- Provider configuration
- Resource definitions
- Data sources

**variables.tf:**
- Variable declarations
- Descriptions
- Default values (non-sensitive only)

**outputs.tf:**
- Important values to display
- VM IP addresses
- Connection strings

**terraform.tfvars:**
- Actual variable values
- Secrets and credentials
- **MUST be in .gitignore**

**Alternative: Single File**
For small projects, you can put everything in `main.tf`, but multi-file is more maintainable.

</details>

**What to Document:**
- Cloud provider chosen and why
- Terraform version used
- Resources created (VM size, region, etc.)
- Public IP address of created VM
- SSH connection command
- Terminal output from `terraform plan` and `terraform apply`
- Proof of SSH access to VM

---

### Task 2 — Pulumi VM Creation (4 pts)

**Objective:** Destroy the Terraform VM and recreate the same infrastructure using Pulumi.

**Requirements:**

1. **Cleanup Terraform Infrastructure**
   - Run `terraform destroy` to delete all resources
   - Verify all resources are deleted in cloud console
   - Document the cleanup process

2. **Setup Pulumi**
   - Install Pulumi CLI
   - Choose a programming language (Python recommended, or TypeScript, Go, C#, Java)
   - Initialize a new Pulumi project
   - Configure cloud provider

3. **Recreate Same Infrastructure**

   Create a `pulumi/` directory with equivalent resources:

   **Same Resources as Task 1:**
   - VM/Compute Instance (same size)
   - Network/VPC
   - Security Group/Firewall (same rules)
   - Public IP Address

   **Goal:** Functionally identical infrastructure, different tool

4. **Apply Infrastructure**
   - Run `pulumi preview` to see planned changes
   - Apply infrastructure with `pulumi up`
   - Verify VM is accessible via SSH
   - Document the public IP

5. **Compare Experience**
   - What was easier/harder than Terraform?
   - How does the code differ?
   - Which approach do you prefer and why?

<details>
<summary>💡 Pulumi Fundamentals</summary>

**What is Pulumi?**

Pulumi is an imperative IaC tool that lets you write infrastructure using real programming languages (Python, TypeScript, Go, etc.).

**Key Differences from Terraform:**

| Aspect | Terraform | Pulumi |
|--------|-----------|--------|
| **Language** | HCL (declarative) | Python, JS, Go, etc. (imperative) |
| **State** | Local or remote state file | Pulumi Cloud (free tier) or self-hosted |
| **Logic** | Limited (count, for_each) | Full programming language |
| **Testing** | External tools | Native unit tests |
| **Secrets** | Plain in state | Encrypted by default |

**Key Concepts:**

**Resources:**
- Similar to Terraform, but defined in code
- Example (Python): `vm = compute.Instance("my-vm", ...)`

**Stacks:**
- Like Terraform workspaces
- Separate environments (dev, staging, prod)
- Each has its own config and state

**Outputs:**
- Return values from your program
- Example: `pulumi.export("ip", vm.public_ip)`

**Config:**
- Per-stack configuration
- Set with: `pulumi config set key value`
- Access in code: `config.get("key")`

**Typical Workflow:**
```bash
pulumi new <template>   # Create new project
pulumi config set ...   # Configure settings
pulumi preview          # Preview changes (like terraform plan)
pulumi up               # Create/update infrastructure
pulumi destroy          # Delete all infrastructure
pulumi stack output     # View outputs
```

**Advantages of Pulumi:**
- Use familiar programming languages
- Full language features (loops, functions, classes)
- Better IDE support (autocomplete, type checking)
- Native testing capabilities
- Secrets encrypted by default

**Disadvantages of Pulumi:**
- Smaller community than Terraform
- More complex for simple tasks
- Requires programming knowledge
- Pulumi Cloud dependency (or self-hosted backend)

**Resources:**
- [Pulumi Documentation](https://www.pulumi.com/docs/)
- [Pulumi Registry](https://www.pulumi.com/registry/) - Provider docs
- [Python Examples](https://www.pulumi.com/docs/languages-sdks/python/)

</details>

<details>
<summary>🐍 Pulumi with Python</summary>

**Project Setup:**

```bash
pulumi new python
# Follow prompts for project name, stack name
```

**Project Structure:**
```
pulumi/
├── __main__.py          # Main infrastructure code
├── requirements.txt     # Python dependencies
├── Pulumi.yaml         # Project metadata
├── Pulumi.dev.yaml     # Stack configuration
└── venv/               # Python virtual environment
```

**Basic Pattern (AWS Example):**

```python
import pulumi
import pulumi_aws as aws

# Create a security group
security_group = aws.ec2.SecurityGroup("web-sg",
    description="Allow SSH and HTTP",
    ingress=[
        {"protocol": "tcp", "from_port": 22, "to_port": 22, "cidr_blocks": ["0.0.0.0/0"]},
        {"protocol": "tcp", "from_port": 80, "to_port": 80, "cidr_blocks": ["0.0.0.0/0"]},
    ])

# Create an EC2 instance
instance = aws.ec2.Instance("my-vm",
    instance_type="t2.micro",
    ami="ami-0c55b159cbfafe1f0",  # Ubuntu
    security_groups=[security_group.name])

# Export the instance's public IP
pulumi.export("public_ip", instance.public_ip)
```

**Configuration:**
```bash
pulumi config set aws:region us-east-1
pulumi config set --secret aws:accessKey YOUR_KEY
pulumi config set --secret aws:secretKey YOUR_SECRET
```

**Running:**
```bash
# Activate venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Install dependencies
pip install -r requirements.txt

# Preview and apply
pulumi preview
pulumi up
```

**Resources:**
- [Pulumi Python SDK](https://www.pulumi.com/docs/languages-sdks/python/)
- [Pulumi AWS Examples](https://github.com/pulumi/examples/tree/master/aws-py-webserver)

</details>

<details>
<summary>📦 Pulumi with TypeScript</summary>

**Project Setup:**

```bash
pulumi new typescript
```

**Basic Pattern (AWS Example):**

```typescript
import * as pulumi from "@pulumi/pulumi";
import * as aws from "@pulumi/aws";

// Create a security group
const securityGroup = new aws.ec2.SecurityGroup("web-sg", {
    description: "Allow SSH and HTTP",
    ingress: [
        { protocol: "tcp", fromPort: 22, toPort: 22, cidrBlocks: ["0.0.0.0/0"] },
        { protocol: "tcp", fromPort: 80, toPort: 80, cidrBlocks: ["0.0.0.0/0"] },
    ],
});

// Create an EC2 instance
const instance = new aws.ec2.Instance("my-vm", {
    instanceType: "t2.micro",
    ami: "ami-0c55b159cbfafe1f0",
    securityGroups: [securityGroup.name],
});

// Export the instance's public IP
export const publicIp = instance.publicIp;
```

**Running:**
```bash
npm install
pulumi preview
pulumi up
```

</details>

<details>
<summary>☁️ Pulumi Cloud Providers</summary>

**Installing Provider Packages:**

**Yandex Cloud (Python):**
```bash
pip install pulumi-yandex
```

**AWS (Python):**
```bash
pip install pulumi-aws
```

**GCP (Python):**
```bash
pip install pulumi-gcp
```

**Azure (Python):**
```bash
pip install pulumi-azure-native
```

**Provider Documentation:**
- [Pulumi Yandex](https://www.pulumi.com/registry/packages/yandex/)
- [Pulumi AWS](https://www.pulumi.com/registry/packages/aws/)
- [Pulumi GCP](https://www.pulumi.com/registry/packages/gcp/)
- [Pulumi Azure](https://www.pulumi.com/registry/packages/azure-native/)

**Authentication:**
- Same as Terraform (environment variables, config files)
- Pulumi can also use `pulumi config set --secret` for secure credential storage

</details>

<details>
<summary>🔄 Migrating from Terraform to Pulumi</summary>

**Key Differences:**

**Resource Names:**
- Terraform: `resource "aws_instance" "web" { ... }`
- Pulumi: `const web = new aws.ec2.Instance("web", { ... })`

**Variables:**
- Terraform: `var.instance_type`
- Pulumi: `config.require("instanceType")` or just regular variables

**Outputs:**
- Terraform: `output "ip" { value = aws_instance.web.public_ip }`
- Pulumi: `export const ip = web.publicIp` (TS) or `pulumi.export("ip", web.public_ip)` (Python)

**Benefits of Real Programming Language:**
- Use loops, conditionals, functions naturally
- Import external libraries
- Better code reuse (functions, classes)
- Type checking and IDE support

**Conversion Tips:**
1. Start with Terraform docs to understand resources needed
2. Find equivalent Pulumi resources in registry
3. Convert HCL blocks to function calls
4. Use language features for logic

**Pulumi Can Import Terraform State:**
```bash
pulumi import ...
```
But for this lab, start fresh with Pulumi.

</details>

**What to Document:**
- Programming language chosen for Pulumi
- Terraform destroy output
- Pulumi preview and up output
- Public IP of Pulumi-created VM
- Comparison: Terraform vs Pulumi experience
- Code differences (HCL vs Python/TypeScript)
- Which tool you prefer and why

---

### Task 3 — Documentation (2 pts)

**Objective:** Document your IaC implementation, decisions, and learnings.

Create `terraform/docs/LAB04.md` (or `docs/LAB04.md` at root) with these sections:

### 1. Cloud Provider & Infrastructure
- Cloud provider chosen and rationale
- Instance type/size and why
- Region/zone selected
- Total cost (should be $0 with free tier)
- Resources created (list all)

### 2. Terraform Implementation
- Terraform version used
- Project structure explanation
- Key configuration decisions
- Challenges encountered
- Terminal output from key commands:
  - `terraform init`
  - `terraform plan` (sanitized, no secrets)
  - `terraform apply`
  - SSH connection to VM

### 3. Pulumi Implementation
- Pulumi version and language used
- How code differs from Terraform
- Advantages you discovered
- Challenges encountered
- Terminal output from:
  - `pulumi preview`
  - `pulumi up`
  - SSH connection to VM

### 4. Terraform vs Pulumi Comparison

Brief comparison (3-5 sentences each):
- **Ease of Learning:** Which was easier to learn and why?
- **Code Readability:** Which is more readable for you?
- **Debugging:** Which was easier to debug when things went wrong?
- **Documentation:** Which has better docs and examples?
- **Use Case:** When would you use Terraform? When Pulumi?

### 5. Lab 5 Preparation & Cleanup

**VM for Lab 5:**
- Are you keeping your VM for Lab 5? (Yes/No)
- If yes: Which VM (Terraform or Pulumi created)?
- If no: How will you recreate the VM for Lab 5? (Terraform/Pulumi + steps)

**Cleanup Status:**
- If keeping VM for Lab 5: Show VM is still running and accessible
- If destroying everything: Terminal output showing both tools' resources destroyed
- Cloud console screenshot showing resource status (optional but recommended)

---

## Bonus Task — IaC CI/CD + Infrastructure Import (2.5 pts)

**Objective:** Add automated validation for infrastructure code and learn to import existing resources into Terraform.

### Part 1: GitHub Actions for IaC Validation (1.5 pts)

**Objective:** Automatically validate Terraform code on pull requests.

**Requirements:**

1. **Create Validation Workflow**

   Create `.github/workflows/terraform-ci.yml` that:
   - Triggers only on changes to `terraform/**` files
   - Runs `terraform fmt -check` (code formatting validation)
   - Runs `terraform init`
   - Runs `terraform validate` (syntax validation)
   - Runs `tflint` (Terraform linter for best practices)

2. **Workflow Setup**
   - Install Terraform in workflow
   - Install tflint
   - Configure path filters (similar to Lab 3)
   - Show validation results in workflow logs

3. **Testing**
   - Create a PR with Terraform changes
   - Verify workflow runs only for Terraform changes
   - Show passing and failing validation examples

<details>
<summary>💡 Terraform CI/CD Concepts</summary>

**Why Validate Infrastructure Code in CI?**

- Catch syntax errors before apply
- Enforce code formatting standards
- Check for security issues and bad practices
- Prevent broken configurations from merging
- Review infrastructure changes before deployment

**Terraform CI Steps:**

**terraform fmt:**
- Formats code to canonical style
- Use `-check` flag to verify without changing files
- Ensures consistency across team

**terraform validate:**
- Checks syntax and internal consistency
- Validates resource configurations
- Doesn't access provider APIs (fast)

**tflint:**
- Linter for Terraform code
- Finds possible errors (invalid instance types, etc.)
- Checks best practices
- Provider-specific rules

**Path Filters:**
- Only run workflow when IaC files change
- Same concept as Lab 3 path filters
- Prevents unnecessary CI runs

**Pattern for Workflow:**
```yaml
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
      - Install tflint
      - Run terraform fmt -check
      - Run terraform init
      - Run terraform validate
      - Run tflint
```

**Advanced: Terraform Plan in PR**

You can also add `terraform plan` to show what would change:
- Requires cloud credentials (use GitHub Secrets)
- Shows plan output as PR comment
- Helps reviewers understand impact
- Use `terraform plan -no-color` for readable output

**Security Considerations:**
- Be careful with secrets in CI
- Don't expose sensitive outputs
- Use `-backend=false` for init if not using state
- Consider using Terraform Cloud for plan sharing

**Resources:**
- [GitHub Actions for Terraform](https://developer.hashicorp.com/terraform/tutorials/automation/github-actions)
- [tflint Documentation](https://github.com/terraform-linters/tflint)
- [Setup Terraform Action](https://github.com/hashicorp/setup-terraform)

</details>

<details>
<summary>🔧 tflint Setup</summary>

**What is tflint?**

A linter for Terraform that finds:
- Possible errors (invalid instance types, deprecated syntax)
- Best practice violations
- Provider-specific issues

**Installation in CI:**
```yaml
- name: Setup TFLint
  uses: terraform-linters/setup-tflint@v3
  with:
    tflint_version: latest

- name: Run TFLint
  run: tflint --format compact
  working-directory: terraform/
```

**Local Installation:**
```bash
# macOS
brew install tflint

# Linux
curl -s https://raw.githubusercontent.com/terraform-linters/tflint/master/install_linux.sh | bash

# Windows
choco install tflint
```

**Configuration (.tflint.hcl):**
```hcl
plugin "terraform" {
  enabled = true
}

plugin "aws" {  # Or your cloud provider
  enabled = true
}
```

**Running Locally:**
```bash
cd terraform/
tflint --init  # Download plugins
tflint         # Run linting
```

**Common Issues Found:**
- Invalid instance types
- Missing required arguments
- Deprecated syntax
- Security group issues
- Invalid AMI IDs

</details>

### Part 2: Import GitHub Repository to Terraform (1 pt)

**Objective:** Learn to manage existing infrastructure with Terraform by importing your course repository.

**Requirements:**

1. **Import GitHub Repository**
   - Create Terraform configuration for GitHub provider
   - Define a `github_repository` resource for your course repo
   - Use `terraform import` to bring existing repo under Terraform management
   - Verify state matches reality

2. **Manage Repository Settings**
   - Add Terraform code to manage repository settings:
     - Description
     - Visibility (public/private)
     - Has issues enabled
     - Has wiki enabled
     - Branch protection rules (optional)
   - Apply changes and verify in GitHub

3. **Documentation**
   - Explain the import process
   - Show terminal output of import command
   - Document why importing existing resources matters

<details>
<summary>💡 Why Import Existing Resources?</summary>

**The Problem:**

In real world, you often have:
- Infrastructure created manually (before IaC adoption)
- Resources created by other tools or people
- Legacy systems that need to be managed with code

You can't just run `terraform apply` - resources already exist!

**The Solution: terraform import**

Import brings existing resources into Terraform management:
1. Write Terraform config describing the resource
2. Run `terraform import` to link config to real resource
3. Terraform now manages that resource
4. Future changes go through Terraform

**Advantages of Managing Existing Resources with IaC:**

**1. Version Control:**
- Track configuration changes over time
- See who changed what and when
- Rollback to previous configurations

**2. Consistency:**
- Standardize configuration across resources
- Prevent configuration drift
- Ensure compliance with policies

**3. Automation:**
- Changes require code review
- CI/CD validation
- Automated testing

**4. Documentation:**
- Code is living documentation
- Anyone can see current configuration
- No "tribal knowledge" needed

**5. Disaster Recovery:**
- Quickly recreate infrastructure from code
- No manual steps to remember
- Tested recovery process

**6. Team Collaboration:**
- Multiple people can work on infrastructure
- PR-based workflow
- No conflicting manual changes

**Real-World Use Cases:**

**Brownfield Infrastructure:**
- Company has 100s of manually created resources
- Import them gradually into Terraform
- Eventually all infrastructure is code-managed

**Migrating Between Tools:**
- Moving from CloudFormation to Terraform
- Moving from manual management to IaC
- Gradual transition without downtime

**Compliance and Governance:**
- All changes must go through code review
- Audit trail of who changed what
- Prevent unauthorized changes

**Cost Management:**
- Review infrastructure changes before apply
- Prevent accidental expensive resources
- Track infrastructure costs in code

**The Import Process:**

```bash
# 1. Write the resource config (empty or partial)
resource "github_repository" "course_repo" {
  name = "DevOps-Core-Course"
  # ... other settings
}

# 2. Import the existing resource
terraform import github_repository.course_repo DevOps-Core-Course

# 3. Terraform now tracks this resource in state
# 4. Run terraform plan to see any drift
# 5. Update config to match reality
# 6. Apply to bring under full management
```

**Challenges:**

- Config must match reality exactly
- May need to import many related resources
- Some resources don't support import
- Requires careful planning

**Best Practices:**

- Import one resource at a time
- Test in non-production first
- Use `terraform plan` to verify match
- Document the import process
- Keep manual backups before import

**Resources:**
- [Terraform Import Command](https://developer.hashicorp.com/terraform/cli/import)
- [Import Usage Examples](https://developer.hashicorp.com/terraform/cli/import/usage)

</details>

<details>
<summary>🐙 GitHub Provider Setup</summary>

**Installing GitHub Provider:**

```hcl
terraform {
  required_providers {
    github = {
      source  = "integrations/github"
      version = "~> 5.0"
    }
  }
}

provider "github" {
  token = var.github_token  # Personal access token
}
```

**Authentication:**

**Create Personal Access Token:**
1. GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Generate new token
3. Select scopes: `repo` (all repo permissions)
4. Copy token (shown once!)

**Configure Token:**
```bash
# Environment variable (recommended)
export GITHUB_TOKEN="your-token-here"

# Or in terraform.tfvars (gitignored!)
github_token = "your-token-here"
```

**Repository Resource:**

```hcl
resource "github_repository" "course_repo" {
  name        = "DevOps-Core-Course"
  description = "DevOps course lab assignments"
  visibility  = "public"

  has_issues   = true
  has_wiki     = false
  has_projects = false

  # Other settings...
}
```

**Import Command:**

```bash
# Format: terraform import <resource_type>.<name> <repo_name>
terraform import github_repository.course_repo DevOps-Core-Course
```

**After Import:**
1. Run `terraform plan` - shows differences between code and reality
2. Update your config to match reality (eliminate differences)
3. Run `terraform plan` again - should show "No changes"
4. Now you can manage the repo with Terraform!

**What You Can Manage:**
- Repository settings
- Branch protection rules
- Collaborators and teams
- Webhooks
- Deploy keys
- Repository secrets

**Resources:**
- [GitHub Provider Documentation](https://registry.terraform.io/providers/integrations/github/latest/docs)
- [Repository Resource](https://registry.terraform.io/providers/integrations/github/latest/docs/resources/repository)
- [Import Guide](https://registry.terraform.io/providers/integrations/github/latest/docs/resources/repository#import)

</details>

**What to Document:**
- Workflow file implementation
- Path filter configuration
- tflint results and any issues found
- Example of workflow running on PR
- GitHub repository import process
- Terminal output of import command
- Why importing matters (brief explanation)
- Benefits you see for managing repos with IaC

---

## How to Submit

1. **Create Branch:**
   - Create a new branch called `lab04`
   - Work on this branch

2. **Commit Work:**
   - Add Terraform code (`terraform/` directory)
   - Add Pulumi code (`pulumi/` directory)
   - Add documentation (`docs/LAB04.md` or `terraform/docs/LAB04.md`)
   - Add GitHub workflow (`.github/workflows/terraform-ci.yml` if doing bonus)
   - **IMPORTANT:** Ensure `.gitignore` excludes:
     - `*.tfstate`, `*.tfstate.*`, `.terraform/`, `terraform.tfvars`
     - `pulumi/venv/`, `Pulumi.*.yaml` (stack configs with secrets)
     - Any credential files
   - Commit with conventional commits format

3. **CLEANUP BEFORE COMMITTING:**

   **If keeping VM for Lab 5:**
   - ✅ Keep one VM running (Terraform or Pulumi - your choice)
   - ✅ Destroy the other tool's resources
   - ✅ Document which VM you're keeping in LAB04.md
   - ✅ Check no secrets in code
   - ✅ Review .gitignore is correct

	   **If NOT keeping VM for Lab 5:**
	   - ✅ Run `terraform destroy`
	   - ✅ Run `pulumi destroy`
	   - ✅ Verify no resources in cloud console
	   - ✅ Check no secrets in code
	   - ✅ Review .gitignore is correct
	   - ✅ Document your Lab 5 plan (how you'll recreate the cloud VM from IaC)

4. **Create Pull Requests:**
   - **PR #1:** `your-fork:lab04` → `course-repo:master`
   - **PR #2:** `your-fork:lab04` → `your-fork:master`
   - Bonus workflow will validate Terraform code automatically

---

## Acceptance Criteria

### Main Tasks (10 points)

**Terraform VM Creation (4 pts):**
- [ ] Cloud provider chosen and configured
- [ ] Terraform project created in `terraform/` directory
- [ ] All required resources defined (VM, network, security group, public IP)
- [ ] Free tier instance used
- [ ] Variables and outputs used appropriately
- [ ] `.gitignore` configured correctly
- [ ] Infrastructure applied successfully
- [ ] VM accessible via SSH (proof provided)
- [ ] Terminal output from `terraform plan` and `terraform apply` provided
- [ ] No secrets committed to Git

**Pulumi VM Recreation (4 pts):**
- [ ] Terraform resources destroyed (proof provided)
- [ ] Pulumi project created in `pulumi/` directory
- [ ] Programming language chosen
- [ ] Same infrastructure recreated with Pulumi
- [ ] Infrastructure applied successfully
- [ ] VM accessible via SSH (proof provided)
- [ ] Terminal output from `pulumi preview` and `pulumi up` provided
- [ ] Comparison with Terraform documented

**Documentation (2 pts):**
- [ ] `docs/LAB04.md` complete with all required sections
- [ ] Cloud provider choice justified
- [ ] Terraform implementation documented
- [ ] Pulumi implementation documented
- [ ] Terraform vs Pulumi comparison provided
	- [ ] Lab 5 preparation documented (keeping VM or recreating it from IaC)
- [ ] Cleanup status documented (what's kept, what's destroyed)
- [ ] Terminal outputs provided (sanitized, no secrets)

### Bonus Task (2.5 points)

**Part 1: IaC CI/CD (1.5 pts)**
- [ ] GitHub Actions workflow created (`.github/workflows/terraform-ci.yml`)
- [ ] Path filters configured for `terraform/**`
- [ ] Workflow runs `terraform fmt -check`
- [ ] Workflow runs `terraform validate`
- [ ] Workflow runs `tflint`
- [ ] Workflow triggers only on Terraform changes (proof provided)
- [ ] Documentation includes workflow implementation details

**Part 2: GitHub Repository Import (1 pt)**
- [ ] GitHub provider configured in Terraform
- [ ] Repository resource defined
- [ ] `terraform import` executed successfully
- [ ] State matches reality (terraform plan shows no changes)
- [ ] Terminal output of import process provided
- [ ] Documentation explains why importing matters
- [ ] Benefits of managing existing resources documented

---

## Rubric

| Criteria | Points | Description |
|----------|--------|-------------|
| **Terraform Implementation** | 4 pts | Working infrastructure, best practices, documentation |
| **Pulumi Implementation** | 4 pts | Working infrastructure, comparison provided |
| **Documentation** | 2 pts | Complete, clear, includes cleanup proof |
| **Bonus: IaC CI/CD** | 1.5 pts | Automated validation, path filters working |
| **Bonus: Import** | 1 pt | Successful import, benefits explained |
| **Total** | 12.5 pts | 10 pts required + 2.5 pts bonus |

**Grading:**
- **10/10:** Both tools working perfectly, excellent comparison, comprehensive documentation, proper cleanup
- **8-9/10:** Infrastructure works, good documentation, minor issues or missing comparisons
- **6-7/10:** One tool works well, other has issues, minimal comparison, incomplete docs
- **<6/10:** Infrastructure doesn't work, major issues, secrets committed, no cleanup

**Critical Requirements:**
- ✅ MUST use free tier resources only
- ✅ MUST document Lab 5 VM plan (keeping one VM or recreating it from IaC)
- ✅ MUST NOT commit secrets or state files
- ✅ MUST provide SSH access proof
- ⚠️ Keeping ONE VM for Lab 5 is acceptable (document it!)
- ❌ Multiple VMs running without documentation = point deduction

---

## Resources

<details>
<summary>📚 Terraform Documentation</summary>

- [Terraform Documentation](https://developer.hashicorp.com/terraform/docs)
- [Terraform Registry](https://registry.terraform.io/) - All providers
- [Terraform Best Practices](https://www.terraform-best-practices.com/)
- [HCL Configuration Language](https://developer.hashicorp.com/terraform/language)

</details>

<details>
<summary>📚 Pulumi Documentation</summary>

- [Pulumi Documentation](https://www.pulumi.com/docs/)
- [Pulumi Registry](https://www.pulumi.com/registry/)
- [Pulumi Examples](https://github.com/pulumi/examples)
- [Pulumi vs Terraform](https://www.pulumi.com/docs/concepts/vs/terraform/)

</details>

<details>
<summary>☁️ Cloud Provider Documentation</summary>

- [Yandex Cloud Docs](https://cloud.yandex.com/en/docs)
- [AWS Documentation](https://docs.aws.amazon.com/)
- [GCP Documentation](https://cloud.google.com/docs)
- [Azure Documentation](https://learn.microsoft.com/azure/)
- [VK Cloud Docs](https://mcs.mail.ru/help/)

</details>

<details>
<summary>🔒 Security & Best Practices</summary>

- [Terraform Security Best Practices](https://spacelift.io/blog/terraform-security-best-practices)
- [Managing Secrets in Terraform](https://developer.hashicorp.com/terraform/tutorials/configuration-language/sensitive-variables)
- [Pulumi Secrets Management](https://www.pulumi.com/docs/concepts/secrets/)
- [Git Secrets Prevention](https://github.com/awslabs/git-secrets)

</details>

<details>
<summary>🛠️ Tools</summary>

- [Terraform CLI](https://developer.hashicorp.com/terraform/downloads)
- [Pulumi CLI](https://www.pulumi.com/docs/install/)
- [tflint](https://github.com/terraform-linters/tflint) - Terraform linter
- [terraform-docs](https://terraform-docs.io/) - Generate docs from code
- [Infracost](https://www.infracost.io/) - Cost estimation for Terraform

</details>

---

## Looking Ahead

- **Lab 5:** Ansible will provision software on your VM (install Docker, deploy your app from Labs 1-3)
  - **You'll need a VM ready** - keep your cloud VM from this lab or recreate later from your IaC code
- **Lab 6:** Ansible + Terraform integration (provision and configure in one workflow)
- **Lab 9:** Kubernetes will replace individual VMs (but concepts are same)
- **Lab 13:** ArgoCD will manage infrastructure changes (GitOps for infrastructure)

---

**Good luck!** 🚀

> **Remember:** Infrastructure as Code is about automation, repeatability, and collaboration. Focus on understanding WHY we define infrastructure in code, not just HOW. Consider keeping one VM for Lab 5 (Ansible). If destroying resources, document how you'll recreate the VM from your IaC code. Never commit secrets!
