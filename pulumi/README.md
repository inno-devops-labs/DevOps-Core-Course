# Pulumi Infrastructure for Lab 04

This directory contains Pulumi code (Python) to provision a VM on Yandex Cloud for the DevOps course.

## Prerequisites

1. **Pulumi CLI**: Install from https://www.pulumi.com/docs/install/
2. **Python 3.8+**: Python runtime
3. **Yandex Cloud Account**: Sign up at https://cloud.yandex.com/
4. **Yandex Cloud CLI**: Install from https://cloud.yandex.com/en/docs/cli/quickstart

## Setup Instructions

### 1. Configure Yandex Cloud Authentication

Same as Terraform - see terraform/README.md for details.

```bash
# Set environment variable for authentication
export YC_SERVICE_ACCOUNT_KEY_FILE="/path/to/key.json"

# Or set these environment variables
export YC_TOKEN="your-token"
export YC_CLOUD_ID="your-cloud-id"
export YC_FOLDER_ID="your-folder-id"
```

### 2. Initialize Pulumi Project

```bash
cd pulumi

# Create Python virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Login to Pulumi (use free tier backend)
pulumi login

# Initialize stack (development environment)
pulumi stack init dev

# Configure Yandex Cloud settings
pulumi config set yandex:folder_id <your-folder-id>
pulumi config set folder_id <your-folder-id>

# Get your public IP and set it
curl ifconfig.me
pulumi config set my_ip_cidr "YOUR_IP/32"

# Optional: Set other config
pulumi config set zone ru-central1-a
pulumi config set ssh_user vglon
pulumi config set ssh_public_key_path ~/.ssh/test_vm.pub
```

### 3. Preview and Deploy

```bash
# Preview changes (like terraform plan)
pulumi preview

# Deploy infrastructure (like terraform apply)
pulumi up

# Select 'yes' to confirm

# View outputs
pulumi stack output
pulumi stack output vm_public_ip
pulumi stack output ssh_connection_command
```

### 4. Connect to VM

```bash
# Use the SSH command from output
ssh -i ~/.ssh/test_vm vglon@<public-ip>

# Or get it with:
pulumi stack output ssh_connection_command
```

## Resources Created

Same as Terraform:
- **VPC Network**: Virtual private cloud network
- **Subnet**: 10.129.0.0/24 subnet in ru-central1-a zone
- **Security Group**: Firewall rules for SSH (22), HTTP (80), and port 5000
- **Compute Instance**: 
  - Platform: standard-v2
  - Cores: 2 (20% core fraction - free tier)
  - Memory: 1 GB
  - Disk: 10 GB HDD
  - OS: Ubuntu 24.04 LTS

## Cleanup

```bash
# Destroy all resources (like terraform destroy)
pulumi destroy

# Confirm with 'yes'

# Remove stack (optional)
pulumi stack rm dev
```

## Files

- `__main__.py`: Main Pulumi program (infrastructure code)
- `requirements.txt`: Python dependencies
- `Pulumi.yaml`: Project metadata
- `Pulumi.dev.yaml`: Stack configuration (gitignored if contains secrets)
- `venv/`: Python virtual environment (gitignored)

## Key Differences from Terraform

### Language
- **Terraform**: HCL (declarative configuration language)
- **Pulumi**: Python (full programming language)

### Code Style
- **Terraform**: Resource blocks with HCL syntax
- **Pulumi**: Python objects and classes

### State Management
- **Terraform**: Local state file or remote backend
- **Pulumi**: Pulumi Cloud (free tier) or self-hosted backend

### Benefits of Pulumi
- Use familiar programming language (Python)
- Full language features (loops, functions, imports)
- Better IDE support (autocomplete, type checking)
- Native testing with pytest
- Secrets encrypted by default

### Example Comparison

**Terraform:**
```hcl
resource "yandex_compute_instance" "vm" {
  name = "my-vm"
  resources {
    cores  = 2
    memory = 1
  }
}
```

**Pulumi:**
```python
vm = yandex.ComputeInstance(
    "vm",
    name="my-vm",
    resources={
        "cores": 2,
        "memory": 1
    }
)
```

## Cost

Same as Terraform - uses Yandex Cloud free tier resources.

**Expected cost: $0/month** (within free tier limits)

## Troubleshooting

**Import Error:**
```bash
# Make sure you activated the virtual environment
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

**Authentication Error:**
```bash
# Verify environment variable is set
echo $YC_SERVICE_ACCOUNT_KEY_FILE

# Or configure through pulumi config
pulumi config set yandex:token "your-token"
```

**SSH Connection Failed:**
- Same troubleshooting as Terraform
- Check security group allows your IP
- Verify public key is correct

## Pulumi vs Terraform

Both tools create identical infrastructure. Key differences:

**Terraform Advantages:**
- Larger community and ecosystem
- More provider support
- Simpler for basic use cases
- Declarative approach easier for some

**Pulumi Advantages:**
- Real programming language
- Better code reuse and abstraction
- Native testing capabilities
- Encrypted secrets
- Better for complex logic

**When to Use Which:**
- **Terraform**: Simple infrastructure, need wide provider support, team prefers HCL
- **Pulumi**: Complex logic needed, team prefers real programming, need testing

## Next Steps

This VM will be used in Lab 5 (Ansible) for configuration management.

The benefit of Infrastructure as Code: you can recreate identical infrastructure anytime with either tool!
