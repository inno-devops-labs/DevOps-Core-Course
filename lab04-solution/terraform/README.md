# Terraform AWS Lab 04 Solution

This directory contains Terraform configuration to provision a virtual machine on AWS.

## Prerequisites

1. **Terraform installed** (version 1.0+)
   ```bash
   terraform --version
   ```

2. **AWS CLI configured** with your credentials
   ```bash
   aws configure
   ```
   
   Or set environment variables:
   ```bash
   export AWS_ACCESS_KEY_ID=your-key-id
   export AWS_SECRET_ACCESS_KEY=your-secret-key
   export AWS_DEFAULT_REGION=us-east-1
   ```

3. **SSH key pair generated**
   ```bash
   ssh-keygen -t rsa -b 4096 -f ~/.ssh/id_rsa
   ```
   
   On Windows with Git Bash:
   ```bash
   ssh-keygen -t rsa -b 4096 -f $HOME/.ssh/id_rsa
   ```

## Setup

1. **Update `terraform.tfvars`** with your configuration:
   - Set `aws_region` if you want to use a different region
   - Set `ssh_public_key_path` to your public key path
   - Optionally set `ssh_allowed_cidr` to restrict SSH access to your IP

   Example for security:
   ```hcl
   ssh_allowed_cidr = "203.0.113.45/32"  # Replace with your public IP
   ```

## Workflow

### 1. Initialize Terraform
```bash
terraform init
```

This downloads the AWS provider and initializes the working directory.

### 2. Validate Configuration
```bash
terraform validate
```

Checks for syntax errors and consistency.

### 3. Format Code (Optional)
```bash
terraform fmt
```

Formats HCL code to canonical style.

### 4. Preview Changes
```bash
terraform plan
```

Shows what resources will be created.

### 5. Apply Configuration
```bash
terraform apply
```

Creates the infrastructure. Type `yes` to confirm.

### 6. Get Outputs
```bash
terraform output
```

Shows important values like:
- Elastic IP address
- SSH connection command
- Instance ID

### 7. Connect to Instance
```bash
ssh -i ~/.ssh/id_rsa ubuntu@<public-ip>
```

Or use the output:
```bash
terraform output ssh_connection_command
ssh -i ~/.ssh/id_rsa $(terraform output -raw instance_public_ip)
```

## Cleanup

To destroy all resources and avoid costs:

```bash
terraform destroy
```

Type `yes` to confirm.
