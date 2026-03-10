# Lab 04 - Pulumi Infrastructure with Python

## Overview

This directory contains Pulumi configuration for Lab 04, recreating the same infrastructure as Terraform but using Python as the programming language.

## Why Pulumi?

**Advantages over Terraform:**
- ✅ Use real programming language (Python, TypeScript, Go, etc.)
- ✅ Full language features: loops, conditionals, functions, classes
- ✅ Better IDE support (autocomplete, type checking)
- ✅ Native testing capabilities
- ✅ Secrets encrypted by default
- ✅ Easier to write complex logic

**When to use Pulumi vs Terraform:**
- **Pulumi:** Complex logic, need programming features, team knows Python/JS
- **Terraform:** Simpler declarative approach, larger community, more providers

## Project Structure

```
pulumi/
├── __main__.py              # Main Pulumi program (Python)
├── Pulumi.yaml             # Project metadata
├── requirements.txt        # Python dependencies
├── Pulumi.dev.yaml.example # Example configuration (safe to commit)
├── Pulumi.dev.yaml         # Actual config (NEVER commit - in .gitignore)
└── README.md               # This file
```

## Resources Created

Same as Terraform configuration:

1. **VPC Network** - `lab04-network-pulumi`
2. **Subnet** - `lab04-subnet-pulumi` (10.128.0.0/24)
3. **VM Instance** - `lab04-devops-vm-pulumi`
   - Platform: standard-v2
   - CPU: 2 cores @ 20%
   - RAM: 1 GB
   - Disk: 10 GB HDD
   - OS: Ubuntu 24.04 LTS
   - Public IP: Yes

## Setup

### 1. Install Pulumi

```bash
# macOS
brew install pulumi

# Or use install script
curl -fsSL https://get.pulumi.com | sh
```

### 2. Login to Pulumi

```bash
# Option 1: Use Pulumi Cloud (free for individuals)
pulumi login

# Option 2: Use local backend (no account needed)
pulumi login --local
```

### 3. Create Python Virtual Environment

```bash
cd pulumi/

# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate  # macOS/Linux
# or
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
```

### 4. Configure Stack

```bash
# Copy example config
cp Pulumi.dev.yaml.example Pulumi.dev.yaml

# Set configuration values
pulumi config set lab04-pulumi:cloud_id "b1g5j96nedr4nscj4tgp"
pulumi config set lab04-pulumi:folder_id "b1ggslr285ass6at43mg"
pulumi config set lab04-pulumi:zone "ru-central1-a"

# Set Yandex Cloud token (encrypted automatically)
pulumi config set yandex:token "YOUR_OAUTH_TOKEN" --secret

# Optional: customize SSH settings
pulumi config set lab04-pulumi:ssh_user "ubuntu"
pulumi config set lab04-pulumi:ssh_public_key_path "~/.ssh/yandex_cloud_key.pub"
```

## Usage

### Preview Changes

```bash
pulumi preview
```

**Expected output:**
```
Previewing update (dev)

     Type                         Name                  Plan       
 +   pulumi:pulumi:Stack          lab04-pulumi-dev      create     
 +   ├─ yandex:index:VpcNetwork   lab04-network         create     
 +   ├─ yandex:index:VpcSubnet    lab04-subnet          create     
 +   └─ yandex:index:ComputeInstance  lab04-vm          create     

Resources:
    + 4 to create
```

### Apply Infrastructure

```bash
pulumi up
```

Pulumi will:
1. Show preview
2. Ask for confirmation
3. Create resources
4. Display outputs

### View Outputs

```bash
# All outputs
pulumi stack output

# Specific output
pulumi stack output external_ip
pulumi stack output ssh_connection_string
```

### Connect to VM

```bash
# Get SSH command
pulumi stack output ssh_connection_string

# Or manually
ssh -i ~/.ssh/yandex_cloud_key ubuntu@$(pulumi stack output external_ip)
```

### Destroy Infrastructure

```bash
pulumi destroy
```

## Code Comparison: Terraform vs Pulumi

### Terraform (HCL)
```hcl
resource "yandex_vpc_network" "lab04_network" {
  name        = "lab04-network"
  description = "Network for Lab04"
}

resource "yandex_compute_instance" "lab04_vm" {
  name        = "lab04-vm"
  platform_id = "standard-v2"
  
  resources {
    cores         = 2
    memory        = 1
    core_fraction = 20
  }
}
```

### Pulumi (Python)
```python
network = yandex.VpcNetwork(
    "lab04-network",
    name="lab04-network",
    description="Network for Lab04",
)

vm = yandex.ComputeInstance(
    "lab04-vm",
    name="lab04-vm",
    platform_id="standard-v2",
    resources=yandex.ComputeInstanceResourcesArgs(
        cores=2,
        memory=1,
        core_fraction=20,
    ),
)
```

## Key Differences

| Aspect | Terraform | Pulumi |
|--------|-----------|--------|
| **Language** | HCL (declarative) | Python, JS, Go, etc. (imperative) |
| **Learning Curve** | Learn HCL syntax | Use familiar language |
| **Logic** | Limited (count, for_each) | Full programming language |
| **Type Safety** | Basic | Full (with TypeScript) |
| **Testing** | External tools | Native unit tests |
| **State** | Local or remote file | Pulumi Cloud or local |
| **Secrets** | Plain in state | Encrypted automatically |
| **Community** | Larger | Growing |
| **Providers** | More available | Most major clouds supported |

## Advantages of Python with Pulumi

### 1. Familiar Syntax
```python
# Use Python features naturally
for i in range(3):
    bucket = s3.Bucket(f"bucket-{i}")

# Conditionals
if config.require_bool("production"):
    instance_type = "t3.large"
else:
    instance_type = "t3.micro"

# Functions
def create_subnet(cidr):
    return vpc.Subnet(f"subnet-{cidr}", cidr_block=cidr)
```

### 2. Better IDE Support
- Autocomplete for all resources
- Type hints and checking
- Inline documentation
- Refactoring tools

### 3. Reusability
```python
def create_vm(name, size):
    return yandex.ComputeInstance(
        name,
        resources=yandex.ComputeInstanceResourcesArgs(
            cores=size["cores"],
            memory=size["memory"],
        ),
    )

# Reuse function
web_vm = create_vm("web", {"cores": 2, "memory": 4})
db_vm = create_vm("db", {"cores": 4, "memory": 8})
```

### 4. Testing
```python
# Unit tests with pytest
@pytest.fixture
def resources():
    return create_infrastructure()

def test_vm_has_correct_size(resources):
    assert resources.vm.resources.memory == 1
```

## Terraform vs Pulumi Comparison (Lab 04 Experience)

### Ease of Learning
**Terraform:** 
- ⚠️ Need to learn HCL syntax
- ✅ Clear documentation
- ✅ Many examples online

**Pulumi:**
- ✅ Already know Python!
- ✅ IDE helps a lot
- ⚠️ Fewer community examples

**Winner:** Pulumi (if you know Python)

### Code Readability
**Terraform:**
- ✅ Declarative - clear what will be created
- ✅ Consistent syntax across providers
- ⚠️ Verbose for complex logic

**Pulumi:**
- ✅ Looks like normal Python code
- ✅ Can add comments and structure freely
- ⚠️ May be too flexible (less standardized)

**Winner:** Tie (depends on preference)

### Debugging
**Terraform:**
- ⚠️ Error messages can be cryptic
- ✅ `terraform plan` shows exactly what changes
- ⚠️ No debugger

**Pulumi:**
- ✅ Can use Python debugger
- ✅ Better error messages
- ✅ Can add print statements
- ✅ IDE highlights errors

**Winner:** Pulumi

### State Management
**Terraform:**
- ⚠️ State file management can be tricky
- ⚠️ Secrets in plain text in state
- ✅ Well understood

**Pulumi:**
- ✅ Pulumi Cloud handles state
- ✅ Secrets encrypted automatically
- ✅ Can use local backend

**Winner:** Pulumi

### When to Use Each?

**Use Terraform when:**
- Team prefers declarative approach
- Need maximum provider support
- Following industry standards
- Simple infrastructure
- Large community matters

**Use Pulumi when:**
- Team knows Python/TypeScript/Go
- Need complex logic
- Want to write tests
- Better IDE support important
- Secrets management critical

**Use Both when:**
- Different teams have different preferences
- Migrating between tools
- Learning both approaches

## Example Workflow

### Starting from Terraform

```bash
# 1. Destroy Terraform infrastructure
cd terraform/
terraform destroy

# 2. Setup Pulumi
cd ../pulumi/
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. Configure
pulumi config set yandex:token "YOUR_TOKEN" --secret

# 4. Preview
pulumi preview

# 5. Create infrastructure
pulumi up

# 6. Verify it's the same
pulumi stack output
# Compare with terraform output
```

## Challenges Encountered

### 1. Provider Installation
**Problem:** Pulumi Yandex provider needed to be installed.

**Solution:** Added `pulumi-yandex` to `requirements.txt`.

### 2. Configuration Differences
**Problem:** Pulumi uses different config system than Terraform.

**Solution:** 
- Used `pulumi config` command
- Created example config file
- Documented all required settings

### 3. Python Path for SSH Key
**Problem:** `~` expansion doesn't work in Python.

**Solution:** Replace `~` with actual home directory path.

## Key Learnings

### 1. Programming Language Power
Using Python allowed:
- Reading SSH key from file easily
- String interpolation for cloud-init
- Clear variable naming
- Better code organization

### 2. State Management is Easier
- Pulumi Cloud handles state automatically
- No need to manage state files manually
- Secrets encrypted by default

### 3. Outputs are Interactive
- `pulumi stack output` is more user-friendly
- Can query specific outputs easily
- JSON export available

### 4. Preview is Similar to Plan
- `pulumi preview` ≈ `terraform plan`
- Shows what will change
- Interactive confirmation

## Comparison Summary

For this lab, both tools accomplished the same goal, but:

**Terraform pros:**
- ✅ More mature ecosystem
- ✅ Larger community
- ✅ More learning resources
- ✅ Industry standard

**Pulumi pros:**
- ✅ More comfortable (Python!)
- ✅ Better IDE experience
- ✅ Easier to write complex logic
- ✅ Built-in secrets management

**Personal preference:** Pulumi for this lab because:
1. Python is familiar
2. IDE autocomplete is helpful
3. Code feels more natural
4. State management is simpler

But for production, would consider:
- Team skills
- Existing tools
- Provider support
- Company standards

## References

- [Pulumi Documentation](https://www.pulumi.com/docs/)
- [Pulumi Yandex Provider](https://www.pulumi.com/registry/packages/yandex/)
- [Pulumi Python Guide](https://www.pulumi.com/docs/languages-sdks/python/)
- [Pulumi vs Terraform](https://www.pulumi.com/docs/concepts/vs/terraform/)
