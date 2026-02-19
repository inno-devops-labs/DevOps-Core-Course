# Terraform Configuration for Lab 4

This directory contains Terraform configuration to provision AWS infrastructure for Lab 4.

## Setup Instructions

### 1. Configure AWS Credentials

Choose one of these methods:

**Option A: AWS CLI (Recommended)**
```bash
# Install AWS CLI if not already installed
brew install awscli

# Configure your credentials
aws configure
# Enter your AWS Access Key ID
# Enter your AWS Secret Access Key
# Enter region: us-east-1
# Enter output format: json
```

**Option B: Environment Variables**
```bash
export AWS_ACCESS_KEY_ID="your-access-key-id"
export AWS_SECRET_ACCESS_KEY="your-secret-access-key"
export AWS_DEFAULT_REGION="us-east-1"
```

### 2. Find Your IP Address

```bash
curl https://ifconfig.me
```

### 3. Get Your SSH Public Key

```bash
cat ~/.ssh/id_rsa.pub
# Or generate a new key pair:
ssh-keygen -t rsa -b 4096 -f ~/.ssh/lab04-key
```

### 4. Create terraform.tfvars

```bash
# Copy the example file
cp terraform.tfvars.example terraform.tfvars

# Edit terraform.tfvars and fill in:
# - my_ip_address with your IP (e.g., "1.2.3.4/32")
# - ssh_public_key with your public key content
```

### 5. Initialize and Apply

```bash
# Initialize Terraform (downloads providers)
terraform init

# Format and validate
terraform fmt
terraform validate

# Preview changes
terraform plan

# Apply infrastructure
terraform apply
# Type 'yes' when prompted
```

### 6. Connect to Your Instance

After `terraform apply` completes, you'll see the SSH connection string in the outputs:

```bash
ssh -i ~/.ssh/lab04-key ubuntu@<PUBLIC_IP>
```

Or use the connection command from the outputs:
```bash
terraform output ssh_connection_string
```

## Cost Management

This configuration uses:
- **t2.micro** instance (free tier eligible: 750 hours/month for 12 months)
- **10 GB** GP2 SSD (free tier eligible)
- **Data transfer** (1 GB/month free)

**To avoid charges:**
- Use free tier only
- Destroy resources when not needed: `terraform destroy`
- Check your AWS billing dashboard regularly

## Cleanup

```bash
# Destroy all infrastructure
terraform destroy

# Verify cleanup in AWS Console
# https://console.aws.amazon.com/
```

## Troubleshooting

**SSH Connection Refused:**
- Wait 1-2 minutes after instance creation
- Check security group allows your IP
- Verify you're using the correct key

**Instance Not Starting:**
- Check AWS Console for instance status
- Verify subnet has internet gateway
- Check IAM permissions

**Permission Denied:**
- Ensure your AWS credentials have EC2 full access
- Verify credentials are correctly configured

## Resources Created

- VPC (10.0.0.0/16)
- Internet Gateway
- Public Subnet (10.0.1.0/24)
- Route Table
- Security Group (SSH, HTTP, port 5000)
- EC2 Key Pair
- t2.micro EC2 Instance (Ubuntu 24.04 LTS)
