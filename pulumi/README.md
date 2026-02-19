# Pulumi Configuration for Lab 4

This directory contains Pulumi (Python) configuration to provision AWS infrastructure for Lab 4.

## Setup Instructions

### 1. Install Python Dependencies

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Pulumi

```bash
# Configure AWS region
pulumi config set aws:region us-east-1

# Set your prefix (optional)
pulumi config set prefix lab04-pulumi

# Set your IP address (find at https://ifconfig.me)
pulumi config set my_ip_address YOUR_IP/32

# Set your SSH public key (get with: cat ~/.ssh/id_rsa.pub)
pulumi config set ssh_public_key "YOUR_PUBLIC_KEY_CONTENT"
```

### 3. Preview and Apply

```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Preview changes
pulumi preview

# Apply infrastructure
pulumi up
```

### 4. Connect to Your Instance

After `pulumi up` completes, you'll see the public IP in the outputs:

```bash
# Get the IP address
pulumi stack output instance_public_ip

# Connect via SSH
ssh -i ~/.ssh/id_rsa ubuntu@<PUBLIC_IP>
```

## Cleanup

```bash
# Destroy all infrastructure
pulumi destroy

# Remove stack (optional)
pulumi stack rm dev
```

## Pulumi vs Terraform

This Pulumi configuration creates the same infrastructure as the Terraform configuration in `../terraform/`:
- VPC with Internet Gateway
- Public Subnet with Route Table
- Security Group (SSH, HTTP, port 5000)
- EC2 Key Pair
- t2.micro EC2 Instance (Ubuntu 24.04 LTS)

### Key Differences:

**Language:**
- Terraform: HCL (HashiCorp Configuration Language)
- Pulumi: Python (real programming language)

**Configuration:**
- Terraform: Multiple `.tf` files
- Pulumi: Single Python program

**State Management:**
- Terraform: Local or remote state file
- Pulumi: Pulumi Cloud (free) or self-hosted

**Secrets:**
- Terraform: Plain in state (can be encrypted)
- Pulumi: Encrypted by default

## Resources

- [Pulumi AWS Provider](https://www.pulumi.com/registry/packages/aws/)
- [Pulumi Python SDK](https://www.pulumi.com/docs/languages-sdks/python/)
