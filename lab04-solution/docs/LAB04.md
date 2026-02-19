# Lab 04 Solution — Infrastructure as Code (Terraform & Pulumi)

## Overview

This solution demonstrates Infrastructure as Code (IaC) using two complementary approaches:
1. **Terraform** - Declarative IaC with HCL configuration language
2. **Pulumi** - Imperative IaC using Python programming language

Both tools create identical infrastructure on AWS, but using different philosophies and paradigms.

## Solution Artifacts

```
lab04-solution/
├── terraform/              # Terraform HCL configuration
│   ├── main.tf            # VPC, subnet, security group, EC2 instance
│   ├── variables.tf       # Input variable definitions
│   ├── outputs.tf         # Output value definitions
│   ├── terraform.tfvars   # Variable values (secrets - .gitignored)
│   ├── .gitignore         # Files to exclude from Git
│   └── README.md          # Terraform setup and usage guide
├── pulumi/                # Pulumi Python configuration
│   ├── __main__.py        # Infrastructure code in Python
│   ├── requirements.txt    # Python dependencies
│   ├── Pulumi.yaml        # Project metadata
│   ├── Pulumi.dev.yaml    # Stack configuration
│   ├── .gitignore         # Files to exclude from Git
│   └── README.md          # Pulumi setup and usage guide
├── .github/workflows/     # GitHub Actions for CI/CD
│   └── terraform-validate.yml
└── docs/LAB04.md          # This comprehensive documentation
```

---

## 1. Cloud Provider & Infrastructure

### Provider Selection: AWS

**Why AWS?**
- Widely available globally
- 750 hours/month free tier for 12 months (t2.micro)
- Extensive documentation and community support
- Most popular cloud platform for learning
- Easy to integrate with CI/CD workflows

### Alternative Providers in Solution

The Terraform and Pulumi configurations can easily be adapted for:
- **Yandex Cloud** (recommended for Russia)
- **GCP** (Google Cloud Platform)
- **Azure** (Microsoft)
- **DigitalOcean** (simplest interface)

### Instance Configuration

**Instance Type:** `t2.micro`
- **Free Tier:** Yes (750 hours/month for 12 months, then charged $0.0116/hour)
- **vCPUs:** 1 (burstable)
- **Memory:** 1 GB RAM
- **Network Performance:** Low to moderate

**Operating System:** Ubuntu 24.04 LTS
- Long-term support (until April 2029)
- Pre-configured with Docker, Python, Ansible
- Actively maintained and widely used

**Region:** us-east-1 (default)
- Lowest latency for US users
- Rich availability zones for HA designs
- Easily changeable in configuration

### Resources Created

| Resource | Description | Cost |
|----------|-------------|------|
| **VPC** | Virtual Private Cloud (10.0.0.0/16) | Free |
| **Subnet** | Public subnet (10.0.1.0/24) | Free |
| **Internet Gateway** | Route internet traffic | Free |
| **Route Table** | Network routing rules | Free |
| **Security Group** | Firewall rules (SSH, HTTP, HTTPS) | Free |
| **EC2 Instance** | t2.micro Ubuntu 24.04 LTS | Free (12 months) |
| **Elastic IP** | Static public IP address | Free (while in use) |
| **Key Pair** | SSH authentication | Free |

**Total Monthly Cost:** ~$0 (within free tier)

---

## 2. Terraform Implementation

### Terraform Version

**Minimum Version:** 1.0+  
**Tested Version:** 1.5+

### Project Structure

```
terraform/
├── main.tf              # Core infrastructure resources
├── variables.tf         # Input variable declarations and descriptions
├── outputs.tf           # Output value definitions
├── terraform.tfvars     # Variable values (IN .gitignore)
├── .gitignore          # Files to exclude from version control
└── README.md           # Setup and usage documentation
```

### Key Configuration Decisions

#### 1. **Declarative vs Imperative**
- **Decision:** Declarative approach with HCL
- **Rationale:** Focus on desired end state, not steps to achieve it
- **Benefit:** Simpler for infrastructure description, easier to review changes

#### 2. **State Management**
- **Decision:** Local state file (terraform.tfstate)
- **Note:** In production, use remote state (Terraform Cloud, S3, etc.)
- **Security:** State file contains sensitive data - must be in .gitignore

#### 3. **Separate Files**
- **main.tf:** Resource definitions (cleaner and more maintainable)
- **variables.tf:** All variable declarations in one place
- **outputs.tf:** All exports in one file (easier to discover available outputs)

#### 4. **Variable Values**
- **terraform.tfvars:** Contains actual values and passwords
- **Security:** Added to .gitignore to prevent committing secrets
- **.gitignore patterns:**
  - `*.tfstate*` - State files with sensitive data
  - `*.tfvars` - Variable files with credentials
  - `.terraform/` - Provider plugins
  - `*.pem`, `*.key` - SSH and TLS keys

#### 5. **Module-Like Structure**
- **Not using Terraform modules:** Solution is simple enough without them
- **Future improvement:** Could package into reusable modules

#### 6. **Data Sources**
- **aws_ami data source:** Dynamically find latest Ubuntu image
  - Advantages: Doesn't require manual AMI ID lookup
  - More maintainable: Automatically updates to latest patch version

### Workflow Demonstration

#### Step 1: Initialize Terraform
```bash
cd terraform/
terraform init

# Output:
# Initializing the backend...
# Initializing provider plugins...
# Terraform has been successfully configured!
```

**What happens:**
- Downloads AWS provider plugin
- Creates `.terraform/` directory with plugins
- Creates `.terraform.lock.hcl` file for version pinning

#### Step 2: Validate Configuration
```bash
terraform validate

# Output:
# Success! The configuration is valid.
```

**What it checks:**
- HCL syntax correctness
- Resource argument validity
- Variable type matching
- Internal consistency

#### Step 3: Format Code (Best Practice)
```bash
terraform fmt -recursive
```

**What it does:**
- Normalizes indentation and formatting
- Ensures consistent style across team
- No functional changes

#### Step 4: Plan Changes
```bash
terraform plan -out=tfplan

# Output:
# Terraform will perform the following actions:
# 
#   # aws_vpc.main will be created
#   + resource "aws_vpc" "main" {
#       + assign_generated_ipv6_cidr_block = false
#       + cidr_block                      = "10.0.0.0/16"
#       ~ ...
#
# Plan: 8 to add, 0 to change, 0 to destroy.
# Saved the plan to: tfplan
```

**What it shows:**
- **+** Resources to be created
- **~** Resources to be modified
- **-** Resources to be destroyed
- **-/+** Resources to be replaced

#### Step 5: Apply Configuration
```bash
terraform apply tfplan

# Output:
# aws_vpc.main: Creating...
# aws_key_pair.deployer: Creating...
# aws_internet_gateway.main: Creating...
# ...
# aws_instance.main: Creating...
# aws_eip.main: Creating...
#
# Apply complete! Resources: 8 added, 0 changed, 0 destroyed.
#
# Outputs:
#
# instance_id = "i-0abc123def456g789"
# instance_public_ip = "203.0.113.42"
# ssh_connection_command = "ssh -i ~/.ssh/id_rsa ubuntu@203.0.113.42"
```

#### Step 6: Verify SSH Access
```bash
terraform output ssh_connection_command
# Output: ssh -i ~/.ssh/id_rsa ubuntu@203.0.113.42

ssh -i ~/.ssh/id_rsa ubuntu@203.0.113.42
# Welcome to Ubuntu 24.04 LTS (GNU/Linux ...)
# ubuntu@ip-10-0-1-xxx:~$ 
```

### Terraform-Specific Features Used

#### 1. **Count-Based Logic**
Not used in this solution because:
- Resources don't need to be created conditionally
- For_each would be overkill for single-instance setup
- Could be added if creating multiple instances

#### 2. **Depends On**
```hcl
depends_on = [
  aws_internet_gateway.main,
  aws_route_table_association.public
]
```
- Explicit dependency declaration
- Ensures resources created in correct order
- Not always necessary but improves readability

#### 3. **Data Sources**
```hcl
data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"]
  filter { ... }
}
```
- Queries existing AWS resources
- Dynamically finds latest Ubuntu AMI
- More maintainable than hardcoded AMI IDs

#### 4. **String Interpolation**
```hcl
tags = {
  Name = "${var.environment}-vm"
}
```
- Interpolates variable values into strings
- Creates consistent naming conventions
- Makes bulk updates easier

### Challenges Encountered & Solutions

#### Challenge 1: SSH Public Key File Path
**Problem:** Different paths on Windows, macOS, Linux  
**Solution:** Use variable with `~/.ssh/id_rsa.pub` which Terraform expands

#### Challenge 2: Security Group Ingress Rules
**Problem:** Should SSH be open to 0.0.0.0/0?  
**Solution:** Made configurable via `ssh_allowed_cidr` variable
```hcl
variable "ssh_allowed_cidr" {
  default = "0.0.0.0/0"  # Change to "YOUR_IP/32" for security
}
```

#### Challenge 3: Elastic IP Management
**Problem:** Costs money if instance is stopped but EIP still allocated  
**Solution:** EIP is associated with running instance, auto-deallocates on destroy

#### Challenge 4: State File Security
**Problem:** `terraform.tfstate` contains plaintext secrets  
**Solution:** Added comprehensive `.gitignore` with all sensitive patterns

### Security Best Practices Implemented

✅ **Credentials Management**
- No hardcoded AWS keys in code
- Use AWS CLI credentials or environment variables
- Terraform automatically detects credentials

✅ **VPC Isolation**
- Custom VPC instead of default
- Public/private subnet structure (extensible)
- Security group with explicit allow rules

✅ **SSH Key Management**
- SSH key pair created locally
- Public key only stored in AWS
- Private key kept secure locally

✅ **State File Protection**
- State file added to .gitignore
- Contains sensitive data (passwords, tokens)
- Should use remote state in production (Terraform Cloud/S3)

✅ **Principle of Least Privilege**
- Security group rules are explicit
- SSH can be restricted to specific IP
- HTTP/HTTPS open to world (configurable)

---

## 3. Pulumi Implementation

### Pulumi Version

**Version:** 3.x+ (tested with 3.50+)  
**Language:** Python 3.8+  
**Runtime:** python

### Project Structure

```
pulumi/
├── __main__.py          # Main infrastructure code
├── requirements.txt     # Python dependencies
├── Pulumi.yaml         # Project configuration
├── Pulumi.dev.yaml     # Development stack config
├── .gitignore          # Files to exclude from Git
└── README.md           # Setup and usage documentation
```

### Key Configuration Decisions

#### 1. **Programming Language: Python**
- **Decision:** Use Python instead of TypeScript or Go
- **Rationale:** 
  - Easier to learn for DevOps engineers
  - Large standard library
  - Better for scripting and automation
- **Trade-off:** Requires Python 3.8+ runtime

#### 2. **Imperative vs Declarative**
- **Decision:** Imperative approach using Python code
- **Rationale:**
  - Handle complex logic naturally
  - Use loops to create multiple instances
  - Leverage full Python language power
- **Benefit:** More flexible than HCL for complex scenarios

#### 3. **State Management**
- **Default:** Pulumi Cloud (free tier, 2 stacks)
- **Alternative:** `pulumi login --local` for local state
- **Production:** Self-hosted Pulumi backend

#### 4. **Configuration Management**
- **Pulumi.yaml:** Project metadata and default config
- **Pulumi.dev.yaml:** Stack-specific (development) values
- **Runtime config:** `pulumi config set` commands
- **Secrets:** `pulumi config set --secret` for encrypted values

#### 5. **Stack Management**
```bash
pulumi stack ls      # List stacks
pulumi stack init    # Create new stack
pulumi stack select  # Switch stack
```
- Stacks are like Terraform workspaces
- Each stack has separate state and config
- Good for multi-environment (dev/staging/prod)

### Comparing Terraform and Pulumi Approaches

**Same Infrastructure, Different Paradigms:**

#### Creating VPC in Terraform (HCL)
```hcl
resource "aws_vpc" "main" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  tags = {
    Name = "${var.environment}-vpc"
  }
}
```

#### Creating VPC in Pulumi (Python)
```python
vpc = aws.ec2.Vpc(
    f"{environment}-vpc",
    cidr_block=vpc_cidr,
    enable_dns_hostnames=True,
    tags={
        "Name": f"{environment}-vpc",
    },
)
```

**Key Differences:**

| Aspect | Terraform | Pulumi |
|--------|-----------|--------|
| **Syntax** | Block-based (block headers) | Function calls with kwargs |
| **Naming** | Separate name ("main") | Single name ("lab04-vpc") |
| **Variables** | `var.vpc_cidr` | Direct Python variable |
| **Logic** | Limited (count, for_each) | Full Python (loops, functions, imports) |
| **Type Safety** | Dynamic typing | Can use type hints |
| **IDE Support** | Basic (HCL extensions) | Full Python support |

### Code Structure Overview

#### Configuration Reading
```python
config = pulumi.Config()
aws_region = config.get("aws_region") or "us-east-1"
```
- Gets values from `Pulumi.dev.yaml`
- Provides defaults if not set
- Can override with `pulumi config set`

#### Reading SSH Public Key
```python
import os
expanded_key_path = os.path.expanduser(ssh_public_key_path)
with open(expanded_key_path, "r") as f:
    ssh_public_key = f.read().strip()
```
- Real Python file operations
- Flexible error handling
- Type safe (no quoting issues)

#### Finding Latest Ubuntu AMI
```python
ami_filter = aws.ec2.get_ami(
    filters=[
        aws.ec2.GetAmiFilterArgs(
            name="name",
            values=["ubuntu/images/hvm-ssd/ubuntu-noble-24.04-amd64-server-*"],
        ),
    ],
    most_recent=True,
    owners=["099720109477"],
)
```
- Data source equivalent
- Returns most recent matching AMI
- Type-safe parameters

#### Creating Resources
```python
instance = aws.ec2.Instance(
    f"{environment}-vm",
    ami=ami_filter.id,
    instance_type=instance_type,
    # ... more parameters
)
```
- Resource objects stored as variables
- Can be referenced by other resources
- Automatic dependency tracking

#### Exporting Outputs
```python
pulumi.export("instance_public_ip", eip.public_ip)
pulumi.export(
    "ssh_connection_command",
    pulumi.concat("ssh -i ~/.ssh/id_rsa ubuntu@", eip.public_ip),
)
```
- Returns values after deployment
- Can combine multiple values
- Equivalent to Terraform outputs

### Workflow Demonstration

#### Step 1: Create Virtual Environment
```bash
cd pulumi/
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

#### Step 2: Install Dependencies
```bash
pip install -r requirements.txt

# Output:
# Collecting pulumi==3.92.0
# Collecting pulumi-aws==6.31.0
# ...
# Successfully installed pulumi-3.92.0 pulumi-aws-6.31.0
```

#### Step 3: Initialize Pulumi (First Time)
```bash
pulumi login --local  # Or just "pulumi login" for Pulumi Cloud

# Output:
# Logged in to local backend
```

#### Step 4: Select or Create Stack
```bash
pulumi stack select dev

# Output:
# Created stack 'dev'
# Access the Pulumi dashboard at https://...
```

#### Step 5: Configure Settings
```bash
pulumi config set aws:region us-east-1
pulumi config set ssh_public_key_path ~/.ssh/id_rsa.pub
```

#### Step 6: Preview Changes
```bash
pulumi preview

# Output:
# Previewing update (dev)
# 
#      Type                 Name              Plan
#  +   pulumi:pulumi:Stack  lab04-pulumi-dev  create
#  +   ├─  aws:ec2:Vpc      lab04-vpc         create
#  +   ├─  aws:ec2:Subnet   lab04-subnet      create
#  +   ├─  aws:ec2:SecurityGroup  lab04-sg  create
#  ...
# 
# Outputs:
#   instance_public_ip: output<string>
#   ssh_connection_command: output<string>
```

#### Step 7: Deploy Infrastructure
```bash
pulumi up

# Output:
# Updating (dev)
# 
#      Type                 Name              Status
#  +   pulumi:pulumi:Stack  lab04-pulumi-dev  created
#  +   ├─  aws:ec2:Vpc      lab04-vpc         created
#  ...
#  +   └─  aws:ec2:Eip      lab04-eip         created
# 
# Outputs:
#   instance_id: "i-0abc123..."
#   instance_public_ip: "203.0.113.42"
#   ssh_connection_command: "ssh -i ~/.ssh/id_rsa ubuntu@203.0.113.42"
# 
# Resources: 8 created
# Duration: 45s
```

#### Step 8: Access Instance
```bash
# Using output
ssh -i ~/.ssh/id_rsa ubuntu@$(pulumi stack output instance_public_ip)

# Or copy the full command
pulumi stack output ssh_connection_command
```

#### Step 9: Cleanup
```bash
pulumi destroy

# Output:
# This will permanently destroy all stack resources!
# Destroying (dev)
# 
# Resources: 8 destroyed
# Duration: 25s
```

### Advanced Python Features Used

#### 1. **String Formatting**
```python
f"{environment}-vpc"  # F-string
pulumi.concat("ssh -i ~/.ssh/id_rsa ubuntu@", eip.public_ip)
```
- F-strings for simple interpolation
- pulumi.concat() for Pulumi outputs

#### 2. **Type Hints (Optional)**
Could be added for better IDE support:
```python
def create_security_group(name: str, vpc_id: pulumi.Output[str]) -> aws.ec2.SecurityGroup:
    return aws.ec2.SecurityGroup(...)
```

#### 3. **Helper Functions (Extensible)**
Could abstract common patterns:
```python
def create_ec2_with_monitoring(name: str, ...) -> tuple[aws.ec2.Instance, aws.ec2.Eip]:
    # Combines instance creation with monitoring setup
    pass
```

#### 4. **Loops (Advantages Over Terraform)**
Create multiple instances naturally:
```python
instances = []
for i in range(3):
    instance = aws.ec2.Instance(
        f"web-{i}",
        ami=ami_filter.id,
        instance_type="t2.micro",
    )
    instances.append(instance)
```

#### 5. **List Comprehensions**
```python
instance_ips = [instance.public_ip for instance in instances]
pulumi.export("instance_ips", instance_ips)
```

### Challenges Encountered & Solutions

#### Challenge 1: Pulumi State Backend
**Problem:** First-time users unsure about cloud vs local state  
**Solution:** Provide `pulumi login --local` option in documentation
- Better for learning and testing
- No Pulumi Cloud account required
- Can migrate to cloud later

#### Challenge 2: SSH Key Path Handling
**Problem:** Python file operations need expanded paths  
**Solution:** Use `os.path.expanduser()` to expand `~`
```python
import os
expanded_path = os.path.expanduser(ssh_public_key_path)
```

#### Challenge 3: Async Output Values
**Problem:** Outputs from resources are Promise/Output objects  
**Solution:** Understand Pulumi Outputs
```python
# This works (Pulumi knows how to combine):
ssh_command = pulumi.concat("ssh ubuntu@", eip.public_ip)

# This DON'T work (trying to string-format Outputs):
ssh_command = f"ssh ubuntu@{eip.public_ip}"  # ❌ Won't work as expected
```

#### Challenge 4: Stack Selection
**Problem:** First `pulumi up` confusing without stack  
**Solution:** Document stack creation clearly
```bash
pulumi stack init dev  # Create and select dev stack
pulumi up              # Deploy to selected stack
```

### Security Best Practices Implemented

✅ **Configuration Management**
- Sensitive values use `--secret` flag
- Encrypted at rest and in transit
- Separate from code

✅ **State Security**
- Local state with `pulumi login --local`
- Or Pulumi Cloud (encrypted remote state)
- Never commit state files to Git

✅ **Code Organization**
- __main__.py is main entry point
- Can split into multiple modules as grows
- Follows Python conventions

✅ **Virtual Environment**
- Python venv isolates dependencies
- Prevents version conflicts
- requirements.txt pins versions

✅ **Secret Handling**
```bash
pulumi config set --secret database_password "secure_password"
config.require_secret("database_password")
```
- Secrets encrypted by default
- Won't appear in logs or outputs

---

## 4. Terraform vs Pulumi Comparison

### Ease of Learning

**Winner: Terraform (for beginners)**

**Terraform:**
- Minimal syntax to learn (just HCL)
- Declarative: describe desired state
- Less prior programming knowledge required
- Great for pure infrastructure people

**Pulumi:**
- Requires Python programming knowledge
- More concept overhead (stacks, projects, etc.)
- Better if you already know Python
- Steeper learning curve initially

**Verdict:** Terraform easier to learn, but Pulumi worth learning if doing DevOps long-term

### Code Readability

**Winner: Tie (depends on background)**

**Terraform Pros:**
- HCL looks like English (blocks are clear)
- Smaller files, focused syntax
- Easy to skim and understand at a glance

**Terraform Cons:**
- Limited to what HCL supports
- for_each and count hard to understand initially
- Lots of boilerplate for complex logic

**Pulumi Pros:**
- Familiar Python syntax if you know Python
- Can extract reusable functions
- Comments and documentation in code
- IDE autocomplete and type hints available

**Pulumi Cons:**
- More lines of code generally
- Indentation matters (Python gotcha)
- Type mixing with Output types confusing initially

**Verdict:** Terraform more readable for infra; Pulumi more readable for programmers

### Debugging

**Winner: Pulumi (slightly)**

**Terraform Debugging:**
- Error messages reference resource blocks
- terraform plan shows exact changes
- Must trace through code to find issue
- Limited by HCL language constructs

**Pulumi Debugging:**
- Python stack traces with line numbers
- IDE breakpoint debugging supported
- Can print/log intermediate values
- Full Python debugging tools available

**Terraform Example Error:**
```
Error: Error creating security group: InvalidGroup.InValid: The security group 'my-sg' already exists for VPC 'vpc-123'
```

**Pulumi Example Error:**
```
Traceback (most recent call last):
  File "__main__.py", line 45, in <module>
    security_group = aws.ec2.SecurityGroup(...)
  ...
```
- Stack trace shows exact line
- Can add print statements above error

**Verdict:** Pulumi's Python debugging is more powerful; Terraform requires more investigation

### Documentation Quality

**Winner: Terraform**

**Terraform:**
- Massive community (been around longer)
- Official Terraform Registry with tons of examples
- HashiCorp provides excellent docs
- Stack Overflow has thousands of answers
- Large ecosystem of modules

**Pulumi:**
- Getting better documentation
- Good official docs but less complete
- Smaller community = fewer Stack Overflow answers
- Registry with examples but not as extensive
- Many examples require TypeScript knowledge

**Verdict:** Terraform docs significantly better for learning, but Pulumi catching up

### Use Cases

**When to Use Terraform:**

✅ **Traditional Infrastructure**
- VM, databases, networking
- Simple, well-defined resources
- Team without programming background

✅ **Multi-Cloud**
- Terraform providers for all clouds
- Write once, deploy to AWS/Azure/GCP, etc.

✅ **Simple Automation**
- Straightforward provisioning
- Limited complex logic needed

✅ **Team Collaboration**
- Easy code review (smaller diffs)
- Non-programmers can understand changes

**When to Use Pulumi:**

✅ **Complex Infrastructure Patterns**
- Nested loop structures
- Conditional resource creation
- Custom business logic

✅ **Software Engineers Building Infrastructure**
- Leverage programming skills
- Use libraries for abstraction
- Write unit tests for infrastructure

✅ **Multi-Environment Patterns**
- Share code across dev/staging/prod
- Use functions creatively
- Conditional regions/components

✅ **Rapid Prototyping**
- Quickly iterate infrastructure
- Leverage existing Python libraries
- Script complex deployments

### Tool Strengths

| Feature | Terraform | Pulumi |
|---------|-----------|--------|
| **Learning Curve** | Easier | Steeper |
| **Documentation** | Excellent | Good |
| **Community Size** | Massive | Growing |
| **Programming** | Limited | Full language |
| **State Files** | Flexible backends | Cloud/local/custom |
| **Modules** | Extensive ecosystem | Growing |
| **Testing** | External tools | Native Python tests |
| **IDE Support** | Basic | Excellent |
| **Multi-Cloud** | Native | Cloud-agnostic |
| **Team Adoption** | Easier | Requires Python skills |

### Side-by-Side Code Comparison

#### Creating Security Group

**Terraform:**
```hcl
resource "aws_security_group" "main" {
  name_prefix = "${var.environment}-sg-"
  vpc_id      = aws_vpc.main.id
  
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [var.ssh_allowed_cidr]
  }
  
  tags = {
    Name = "${var.environment}-sg"
  }
}
```

**Pulumi:**
```python
security_group = aws.ec2.SecurityGroup(
    f"{environment}-sg",
    vpc_id=vpc.id,
    ingress=[
        aws.ec2.SecurityGroupIngressArgs(
            protocol="tcp",
            from_port=22,
            to_port=22,
            cidr_blocks=[ssh_allowed_cidr],
        ),
    ],
    tags={
        "Name": f"{environment}-sg",
    },
)
```

**Observations:**
- Terraform is terser (no `Args` suffix)
- Pulumi is more verbose but explicit argument types
- Both equally readable for this simple case

#### Creating Multiple Instances

**Terraform:**
```hcl
resource "aws_instance" "web" {
  count           = var.instance_count
  ami             = data.aws_ami.ubuntu.id
  instance_type   = "t2.micro"
  
  tags = {
    Name = "web-${count.index}"
  }
}

output "instance_ips" {
  value = [for i in aws_instance.web : i.public_ip]
}
```

**Pulumi:**
```python
instances = []
for i in range(instance_count):
    instance = aws.ec2.Instance(
        f"web-{i}",
        ami=ami.id,
        instance_type="t2.micro",
        tags={"Name": f"web-{i}"},
    )
    instances.append(instance)

instance_ips = [instance.public_ip for instance in instances]
pulumi.export("instance_ips", instance_ips)
```

**Observations:**
- Terraform's count syntax is cryptic to newcomers
- Pulumi's loops are natural for programmers
- Pulumi is more lines but clearer intent

### Cost Comparison

**Terraform:**
- 100% free and open source
- No recurring costs

**Pulumi:**
- Free tier: 2 stacks, local backend, 50GB storage
- Paid: Team features, unlimited stacks
- Self-hosted backend: Free but requires infrastructure

**Winner:** Both free for individuals and small teams

### Team Adoption

**Terraform Advantages:**
- Easier onboarding for infrastructure people
- Less programming knowledge required
- Smaller learning curve
- More widely known in industry

**Pulumi Advantages:**
- Better for teams with strong engineering culture
- Easier code reuse through functions/classes
- Better IDE support and debugging
- More powerful for complex scenarios

---

## 5. Lab 5 Preparation & Cleanup

### VM Status

**Keep VM for Lab 5? YES (Recommended)**

#### Why Keep Running?
- **Lab 5 Requirement:** Needs active VM with SSH access
- **Setup Cost:** Initial setup takes ~2-3 minutes
- **Minimal Cost:** t2.micro free tier won't incur charges for 12 months
- **Convenience:** Avoid recreating infrastructure

#### Infrastructure Ready for Lab 5?

✅ **Operating System**
- Ubuntu 24.04 LTS installed
- System updates applied
- All required packages pre-installed

✅ **Docker Installation**
- Docker Engine installed and configured
- Docker Compose available
- Ready for container deployments

✅ **Ansible Installation**
- Python 3 installed
- Ansible package available
- Ready for configuration management

✅ **SSH Configuration**
- SSH server running
- Public key authentication enabled
- Static IP available (Elastic IP)

✅ **Network Configuration**
- Instance in public subnet
- Internet Gateway configured
- SSH port (22) open in security group

### Keeping VM Running to Lab 5

If keeping VM:
```bash
# Document VM details
terraform output instance_public_ip      # e.g., 203.0.113.42
terraform output ssh_connection_command  # Save this command

# Verify connectivity
ssh -i ~/.ssh/id_rsa ubuntu@203.0.113.42
# Welcome to Ubuntu 24.04 LTS
ubuntu@ip-10-0-1-xxx:~$
```

**Next Steps for Lab 5:**
1. Note the public IP address
2. Keep this Terraform/Pulumi code (for destroying later)
3. In Lab 5, use this VM for Ansible playbooks

### VM Cleanup After Lab 5

If no longer needed after Lab 5:

#### Terraform Cleanup
```bash
cd terraform/
terraform destroy

# Output:
# Destroy complete! Resources: 8 destroyed.
# Duration: 30s
```

#### Pulumi Cleanup
```bash
cd pulumi/
pulumi destroy

# Output:
# Destroy complete! Resources: 8 destroyed.
# Duration: 25s
```

#### Remaining Cleanup
- Delete local Terraform/Pulumi state files
- Remove SSH keys if created specifically for this lab
- Check AWS billing to confirm no active resources

**Important:** Don't delete the Terraform/Pulumi code itself - you might need to recreate the VM later!

### Cost Management Verification

#### Check AWS Billing

1. Go to AWS Console → Billing Dashboard
2. Look for "Estimated Monthly Charge"
   - Should be **$0.00** with free tier
   - If any charges: Identify and stop resource

3. Monitor these resources:
   - t2.micro instance: Free for 12 months
   - Elastic IP: Free while associated
   - Data transfer: Free within region

#### Estimated Costs (if charged)

| Item | Free Tier | If Charged |
|------|-----------|-----------|
| **t2.micro EC2** | First 750 hours/month × 12 months | $0.0116/hour after free tier |
| **Elastic IP** | Free while in use | $0.005/hour if unassociated |
| **Data transfer** | 15GB out/month | $0.09 per GB after free tier |
| **Storage (EBS)** | 30GB/month | $0.10 per GB-month |

**Total estimated:** ~$0 with free tier (first year)

#### Billing Alert Setup

Recommended (optional but helpful):
1. AWS Console → Billing → Billing Preferences
2. Set SNS alert at $1.00
3. Receive email if charges incurred

---

## 6. Solution Testing & Validation

### Terraform Validation

```bash
cd terraform/

# 1. Format check
terraform fmt -check -recursive
# Output: No changes

# 2. Validation
terraform validate
# Output: Success! The configuration is valid.

# 3. Linting (optional, requires tflint)
tflint
# Output: 0 errors
```

### Pulumi Validation

```bash
cd pulumi/
source venv/bin/activate

# 1. Python syntax check
python -m py_compile __main__.py
# Output: (no output = success)

# 2. Import check
python -c "import __main__; print('✅ Code loading success')"
# Output: ✅ Code loading success

# 3. Pulumi preview
pulumi preview
# Output: (shows resource changes)
```

### Manual Testing

#### Test 1: Terraform Apply & SSH
```bash
cd terraform/
terraform apply -auto-approve
# Output: Apply complete!

# Test SSH access
INSTANCE_IP=$(terraform output -raw instance_public_ip)
ssh -i ~/.ssh/id_rsa -o StrictHostKeyChecking=no ubuntu@$INSTANCE_IP \
  "echo 'SSH Access Successful'; uname -a"
# Output: 
# SSH Access Successful
# Linux ip-10-0-1-xxx 6.8.0-xx-generic ...
```

#### Test 2: Pulumi Deploy & SSH
```bash
cd pulumi/
pulumi up -y
# Output: Deployment successful

# Test SSH access
INSTANCE_IP=$(pulumi stack output instance_public_ip)
ssh -i ~/.ssh/id_rsa -o StrictHostKeyChecking=no ubuntu@$INSTANCE_IP \
  "docker ps; ansible --version"
# Output:
# CONTAINER ID IMAGE COMMAND CREATED STATUS NAMES
# 
# ansible 2.x.x
# (shows Docker and Ansible working)
```

#### Test 3: Docker & Ansible Installation
```bash
ssh ubuntu@<instance-ip>

# Check Docker
ubuntu@vm:~$ docker --version
# Docker version 26.x.x

# Check Ansible
ubuntu@vm:~$ ansible --version
# ansible 2.x [core 2.17.x]

# Check Python
ubuntu@vm:~$ python3 --version
# Python 3.12.x
```

---

## 7. Bonus: GitHub Actions CI/CD for IaC

### Terraform Validation Workflow

See [.github/workflows/terraform-validate.yml](.github/workflows/terraform-validate.yml)

**What It Does:**
1. Triggers on pull requests to main branch
2. Runs `terraform fmt -check` (code formatting)
3. Runs `terraform validate` (syntax check)
4. Runs `tflint` (best practice linting)
5. Shows results in PR

**Example Workflow Run:**
```
✅ terraform fmt
✅ terraform validate
✅ tflint
```

### GitHub Provider Setup (Bonus)

To manage your course repository with Terraform (import and manage):

#### Step 1: Create GitHub Personal Access Token
1. GitHub.com → Settings → Developer Settings → Personal Access Tokens
2. Generate new token (classic)
3. Scopes: `admin:repo`, `admin:org`
4. Save token (copy carefully!)

#### Step 2: Configure Terraform
```hcl
terraform {
  required_providers {
    github = {
      source  = "integrations/github"
      version = "~> 6.0"
    }
  }
}

provider "github" {
  token = var.github_token
  owner = "your-github-username"
}
```

#### Step 3: Import Existing Repository
```bash
# First, write the resource block (empty)
# resource "github_repository" "course_repo" { }

# Then import
terraform import github_repository.course_repo DevOps-Core-Course

# Terraform will link the existing repository to your code
```

#### Step 4: Manage Repository Settings
```hcl
resource "github_repository" "course_repo" {
  name        = "DevOps-Core-Course"
  description = "DevOps Core Course Labs"
  private     = false
  
  # Branch protection
  has_issues      = true
  has_projects    = true
  has_downloads   = true
  has_wiki        = false
  
  # Auto-init
  auto_init = false
  
  topics = ["devops", "infrastructure-as-code", "terraform", "pulumi"]
}
```

#### Why Import Existing Resources?

**Problem:** Setting up cloud resources manually creates deployment gap
**Solution:** Import existing resources into Terraform
**Benefit:** Version control, PR reviews, CI/CD validation

**Use Cases:**
- Brownfield infrastructure (migrate existing to IaC)
- Compliance tracking (all changes in Git)
- Disaster recovery (can recreate from code)
- Team synchronization (single source of truth)

---

## 8. Key Learnings & Takeaways

### Infrastructure as Code Philosophy

**Core Principles:**
1. **Declarative > Imperative:** Describe desired state, not steps
2. **Version Control:** All infrastructure changes tracked
3. **Reproducibility:** Same code = same infrastructure
4. **Repeatability:** Destroy and recreate reliably
5. **Automation:** Eliminate manual configuration

### Tools Comparison Summary

| Aspect | Terraform | Pulumi | Winner |
|--------|-----------|--------|--------|
| **Ease** | Easier | Steeper curve | Terraform |
| **Flexibility** | Good | Excellent | Pulumi |
| **Community** | Massive | Growing | Terraform |
| **Documentation** | Excellent | Good | Terraform |
| **Testing** | External | Native | Pulumi |
| **Learning Value** | Essential | Advanced | Both |

### Practical Recommendations

**Choose Terraform If:**
- Team is new to IaC
- Working with non-programmers
- Need widely available knowledge
- Multi-cloud strategy important
- Simple infrastructure

**Choose Pulumi If:**
- Team has strong engineering culture
- Need complex infrastructure logic
- Comfortable with programming
- Want native testing
- Rapid iteration needed

**Best Practice: Know Both**
- Terraform dominates industry (learn first)
- Pulumi growing in adoption (learn second)
- Understand strengths/trade-offs
- Choose best tool per project

### Security Lessons

✅ **Always Do:**
- Never commit secrets to Git
- Use .gitignore aggressively
- Use cloud provider credentials properly
- Encrypt sensitive outputs
- Audit state files for sensitive data

❌ **Never Do:**
- Hardcode AWS keys in code
- Use 0.0.0.0/0 for SSH in production
- Share state files
- Commit credentials, tokens, keys
- Use shared cloud accounts

### Cost Management Lessons

✅ **Always Do:**
- Know free tier limits for chosen provider
- Set billing alerts
- Monitor resource usage
- Destroy test infrastructure after use
- Document per-resource costs

❌ **Never Do:**
- Leave resources running indefinitely
- Assume free tier covers everything
- Ignore billing notifications
- Over-provision for learning labs
- Forget to run destroy/cleanup

---

## 9. Next Steps & Further Learning

### Immediate Next Steps

1. **Lab 5 Preparation**
   - Ensure VM is still running
   - Note public IP address
   - Verify SSH access works
   - Ready for Ansible in Lab 5

2. **Code Review**
   - Review Terraform and Pulumi code
   - Run validation locally
   - Compare HCL vs Python approaches
   - Note differences in resource naming

3. **Try Variations**
   - Change instance type to t2.small
   - Add second subnet (private)
   - Create multiple instances with loop
   - Restrict SSH to your IP

### Advanced Topics to Explore

**Terraform:**
- Remote state (Terraform Cloud/S3 backend)
- Modules (reusable infrastructure components)
- Workspaces (developer environment isolation)
- Testing with Terratest
- Complex for_each patterns

**Pulumi:**
- Stacks (dev/staging/prod separation)
- Automation API (programmatic deployments)
- Pulumi Cloud backend (team collaboration)
- Unit testing infrastructure
- Custom components (reusable abstractions)

**General DevOps:**
- CI/CD pipelines for infrastructure
- Infrastructure testing strategies
- Configuration drift detection
- Multi-region deployment patterns
- Disaster recovery automation

### Recommended Reading

**Terraform:**
- [Terraform Up & Running](https://www.terraform.io/docs)
- [The Terraform Book](https://terraformbook.com/)
- [AWS Provider Documentation](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)

**Pulumi:**
- [Pulumi: Infrastructure as Software](https://www.pulumi.com/docs/)
- [Python SDK Documentation](https://www.pulumi.com/docs/languages-sdks/python/)
- [Infrastructure as Code Best Practices](https://www.pulumi.com/docs/using-pulumi/best-practices/)

**General IaC:**
- "Infrastructure as Code" book by Kief Morris
- "The DevOps Handbook" (touches on IaC)
- Cloud provider documentation (AWS, Azure, GCP)

### Practice Exercises

1. **Modify Infrastructure**
   - Change instance type
   - Add additional security rules
   - Create multiple instances
   - Add load balancer

2. **Test Both Approaches**
   - Create VM with Terraform
   - Destroy with Terraform
   - Create same VM with Pulumi
   - Verify identical

3. **Explore Other Providers**
   - Set up AWS infrastructure with Terraform
   - Recreate same infrastructure on GCP
   - Test multi-cloud deployment

4. **Continuous Learning**
   - Read others' Terraform code (GitHub)
   - Study infrastructure examples
   - Practice IaC patterns
   - Stay updated with new features

---

## Conclusion

This solution demonstrates that:

1. **IaC is Essential** - Modern infrastructure must be code-driven
2. **Multiple Tools Solve Same Problem** - Terraform and Pulumi both work, different approaches
3. **Trade-offs Exist** - No perfect tool, choose based on team/project context
4. **Learning Value is High** - Understanding IaC concepts transcends specific tools
5. **Lab 5 Ready** - Created infrastructure ready for Ansible configuration management

The infrastructure created can:
- Be destroyed and recreated reliably
- Be version controlled in Git
- Be reviewed before deployment
- Be extended with additional resources
- Be used as foundation for production systems

Both Terraform and Pulumi demonstrate professional infrastructure practices - choose based on your team's context and comfort level.

---

**Lab 04 Complete!** ✨

Next: Lab 05 (Ansible) - Use this VM for configuration management!
