# Pulumi AWS Lab 04 Solution

This directory contains a Pulumi program (Python) to provision the same virtual machine infrastructure as the Terraform solution, but using an imperative approach.

## Key Differences from Terraform

| Aspect | Terraform | Pulumi |
|--------|-----------|--------|
| **Language** | HCL (declarative) | Python (imperative) |
| **Code Style** | Configuration blocks | Function calls |
| **Logic** | Limited (count, for_each) | Full Python language |
| **State Management** | Local or remote backend | Pulumi Cloud (free) or self-hosted |
| **Secrets** | Plain in state | Encrypted by default |

## Prerequisites

1. **Pulumi CLI installed** (version 3.0+)
   ```bash
   pulumi version
   ```
   
   Install from: https://www.pulumi.com/docs/install/

2. **Python 3.7+** with pip
   ```bash
   python3 --version
   pip3 --version
   ```

3. **AWS CLI configured** with credentials
   ```bash
   aws configure
   ```
   
   Or set environment variables:
   ```bash
   export AWS_ACCESS_KEY_ID=your-key
   export AWS_SECRET_ACCESS_KEY=your-secret
   export AWS_DEFAULT_REGION=us-east-1
   ```

4. **SSH key pair generated**
   ```bash
   ssh-keygen -t rsa -b 4096 -f ~/.ssh/id_rsa
   ```

## Setup

### 1. Create Python Virtual Environment

**On Linux/macOS:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**On Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**On Windows (cmd):**
```cmd
python -m venv venv
venv\Scripts\activate.bat
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Set Pulumi Configuration

Configure the Pulumi stack with your settings:

```bash
# AWS region (change if needed)
pulumi config set aws:region us-east-1

# SSH public key path (change if different)
pulumi config set ssh_public_key_path ~/.ssh/id_rsa.pub

# Optional: Restrict SSH access to your IP for security
pulumi config set ssh_allowed_cidr "203.0.113.45/32"  # Replace with your IP
```

## Workflow

### 1. Select or Create Stack

View available stacks:
```bash
pulumi stack ls
```

Create a new stack (if needed):
```bash
pulumi stack init dev
```

Select a stack:
```bash
pulumi stack select dev
```

### 2. Preview Changes

```bash
pulumi preview
```

Shows what resources will be created/modified/destroyed.

### 3. Deploy Infrastructure

```bash
pulumi up
```

Reviews the preview and prompts for confirmation before deploying.

### 4. Get Outputs

```bash
# All outputs
pulumi stack output

# Specific output
pulumi stack output instance_public_ip

# SSH connection command
pulumi stack output ssh_connection_command
```

### 5. Connect to Instance

```bash
ssh -i ~/.ssh/id_rsa ubuntu@$(pulumi stack output instance_public_ip)
```

## Cleanup

To destroy all resources:

```bash
pulumi destroy
```

Pulumi will show what will be deleted and ask for confirmation.

To delete the stack entirely:
```bash
pulumi stack rm
```

## Code Overview

### `__main__.py`

The main infrastructure code demonstrating Pulumi's imperative style:

**Advantages of using Python:**
- Use loops, conditionals, and functions naturally
- Import external libraries for processing
- Better IDE support with autocomplete
- Type hints for better code quality
- Unit testing with standard Python frameworks

**Key Points:**
1. **Configuration**: Using Pulumi Config to get settings
2. **Data Sources**: Finding the latest Ubuntu AMI dynamically
3. **Resource Creation**: Creating VPC, subnet, security group, etc.
4. **Dependencies**: Using `opts=pulumi.ResourceOptions()` to manage dependencies
5. **Exports**: Using `pulumi.export()` for outputs

### `requirements.txt`

Python dependencies:
- `pulumi`: Core Pulumi SDK
- `pulumi-aws`: AWS resource provider

### `Pulumi.yaml`

Project metadata and default configuration values.

### `Pulumi.dev.yaml`

Stack-specific configuration for the 'dev' stack.

## Comparing with Terraform

### Terraform Approach (HCL)
```hcl
resource "aws_instance" "main" {
  ami             = data.aws_ami.ubuntu.id
  instance_type   = var.instance_type
  subnet_id       = aws_subnet.public.id
  security_groups = [aws_security_group.main.id]
  key_name        = aws_key_pair.deployer.key_name

  tags = {
    Name = "lab04-vm"
  }
}
```

### Pulumi Approach (Python)
```python
instance = aws.ec2.Instance(
    f"{environment}-vm",
    ami=ami_filter.id,
    instance_type=instance_type,
    subnet_id=subnet.id,
    vpc_security_group_ids=[security_group.id],
    key_name=key_pair.key_name,
    tags={
        "Name": f"{environment}-vm",
    },
)
```

**Pulumi Advantages:**
- Can loop to create multiple instances
- Can use conditional logic
- Access environment variables naturally
- Better IDE support
- Familiar Python syntax

## Managing Secrets

### Setting Secrets
```bash
pulumi config set --secret aws_access_key <your-key>
```

### Using Secrets in Code
```python
config = pulumi.Config()
secret_value = config.require_secret("my_secret")
```

Secrets are encrypted at rest and in transit.

## Advanced Features

### Autoscaling Example
```python
for i in range(3):
    instance = aws.ec2.Instance(f"web-{i}", ami=ami, ...)
```

### Conditional Logic
```python
if environment == "prod":
    instance_type = "t2.large"
else:
    instance_type = "t2.micro"
```

### Reference Other Stack Outputs
```python
other_stack = pulumi.StackReference(f"organization/project/{stack_name}")
other_vpc_id = other_stack.get_output("vpc_id")
```

## Troubleshooting

### Error: "Module not found"
```bash
source venv/bin/activate  # Activate virtual environment
pip install -r requirements.txt
```

### Error: "AWS credentials not configured"
```bash
aws configure
# or
export AWS_ACCESS_KEY_ID=your-key
export AWS_SECRET_ACCESS_KEY=your-secret
```

### Error: "SSH public key file not found"
- Generate key: `ssh-keygen -t rsa -b 4096 -f ~/.ssh/id_rsa`
- Update config: `pulumi config set ssh_public_key_path ~/.ssh/id_rsa.pub`

### Error: "Not authenticated with Pulumi Cloud"
First run:
```bash
pulumi login
# or
pulumi login --local  # Uses local filesystem for state
```

### View Logs
```bash
pulumi logs -f
```

## Best Practices

1. **Version Control**: Commit `__main__.py`, `Pulumi.yaml`, `requirements.txt`
   - Don't commit: `Pulumi.*.yaml` (contains secrets), `.env`, `venv/`

2. **State Management**: Use Pulumi Cloud (free tier) or self-hosted backend
   - Default: Pulumi Cloud for easy team collaboration
   - Local: `pulumi login --local`

3. **Automation**: Use in CI/CD pipelines
   ```bash
   pulumi up --yes  # Skip confirmation
   ```

4. **Testing**: Unit test with pytest
   ```python
   # test_main.py
   import unittest
   import __main__
   
   class TestInfrastructure(unittest.TestCase):
       def test_instance_type(self):
           # Test instance configuration
           pass
   ```
