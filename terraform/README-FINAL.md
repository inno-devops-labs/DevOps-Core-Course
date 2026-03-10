# Lab 04 - Terraform Infrastructure Configuration

## Overview

This directory contains Terraform configuration for Lab 04 DevOps course. The configuration demonstrates Infrastructure as Code (IaC) principles by defining a complete VM infrastructure.

## Cloud Provider Used

**Yandex Cloud** - chosen for accessibility in Russia and free tier offering.

### Why Yandex Cloud?
- Free tier: 1 VM with 20% vCPU, 1 GB RAM
- 10 GB SSD storage included
- Accessible in Russia
- Good Terraform provider support

## Configuration Files

```
terraform/
├── main.tf                    # Main infrastructure resources
├── variables.tf               # Input variable definitions
├── outputs.tf                 # Output value definitions
├── terraform.tfvars.example   # Example variable values (safe to commit)
├── terraform.tfvars           # Actual values (NEVER commit - in .gitignore)
├── setup-yandex-cloud.sh      # Automated setup script
└── README-FINAL.md            # This file
```

## Resources Created

The Terraform configuration creates the following infrastructure:

### Networking
1. **VPC Network** (`yandex_vpc_network.lab04_network`)
   - Name: `lab04-network`
   - CIDR: Managed by Yandex Cloud

2. **Subnet** (`yandex_vpc_subnet.lab04_subnet`)
   - Name: `lab04-subnet`
   - CIDR Block: `10.128.0.0/24`
   - Zone: `ru-central1-a`
   - Attached to lab04-network

### Compute
3. **VM Instance** (`yandex_compute_instance.lab04_vm`)
   - Name: `lab04-devops-vm`
   - Platform: `standard-v2`
   - Resources:
     - CPU: 2 cores @ 20% (free tier)
     - RAM: 1 GB
     - Boot Disk: 10 GB HDD
   - OS: Ubuntu 24.04 LTS
   - Public IP: Assigned via NAT
   - SSH Key: Configured via metadata

### Security
- Uses default security group (allows all traffic by default)
- SSH access configured via cloud-init
- Security best practices:
  - No hardcoded credentials
  - Sensitive files in `.gitignore`
  - Variables for configurable values

## Infrastructure Diagram

```
┌─────────────────────────────────────┐
│   Yandex Cloud (ru-central1-a)      │
│                                      │
│  ┌────────────────────────────────┐ │
│  │  VPC Network: lab04-network    │ │
│  │                                 │ │
│  │  ┌──────────────────────────┐  │ │
│  │  │  Subnet: 10.128.0.0/24   │  │ │
│  │  │                           │  │ │
│  │  │  ┌──────────────────┐    │  │ │
│  │  │  │  VM Instance     │    │  │ │
│  │  │  │  lab04-devops-vm │    │  │ │
│  │  │  │                  │    │  │ │
│  │  │  │  - 2 cores @20%  │    │  │ │
│  │  │  │  - 1 GB RAM      │    │  │ │
│  │  │  │  - 10 GB Disk    │    │  │ │
│  │  │  │  - Ubuntu 24.04  │    │  │ │
│  │  │  │                  │    │  │ │
│  │  │  │  Public IP ──────┼────┼──┼─┼─> Internet
│  │  │  └──────────────────┘    │  │ │
│  │  └──────────────────────────┘  │ │
│  └────────────────────────────────┘ │
└─────────────────────────────────────┘
```

## Variables Used

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `cloud_id` | Yandex Cloud ID | - | Yes |
| `folder_id` | Folder ID | - | Yes |
| `zone` | Availability zone | `ru-central1-a` | No |
| `yc_token` | OAuth token | - | Yes |
| `ssh_user` | SSH username | `ubuntu` | No |
| `ssh_public_key_path` | Path to SSH public key | `~/.ssh/yandex_cloud_key.pub` | No |

## Outputs

| Output | Description |
|--------|-------------|
| `vm_id` | ID of created VM instance |
| `vm_name` | Name of the VM |
| `vm_fqdn` | Fully qualified domain name |
| `external_ip` | Public IP address |
| `internal_ip` | Private IP address |
| `ssh_connection_string` | Ready-to-use SSH command |
| `network_id` | ID of VPC network |
| `subnet_id` | ID of subnet |

## Terraform Workflow

### 1. Initialization
```bash
cd terraform/
terraform init
```

**Output:**
```
Initializing the backend...
Initializing provider plugins...
- Finding yandex-cloud/yandex versions matching "~> 0.131"...
- Installing yandex-cloud/yandex v0.187.0...

Terraform has been successfully initialized!
```

### 2. Validation
```bash
terraform fmt
terraform validate
```

**Output:**
```
Success! The configuration is valid.
```

### 3. Planning
```bash
terraform plan
```

**Key parts of plan output:**
```
Terraform will perform the following actions:

  # yandex_compute_instance.lab04_vm will be created
  + resource "yandex_compute_instance" "lab04_vm" {
      + name        = "lab04-devops-vm"
      + platform_id = "standard-v2"
      + zone        = "ru-central1-a"
      
      + resources {
          + core_fraction = 20
          + cores         = 2
          + memory        = 1
        }
      ...
    }

  # yandex_vpc_network.lab04_network will be created
  # yandex_vpc_subnet.lab04_subnet will be created

Plan: 3 to add, 0 to change, 0 to destroy.
```

### 4. Applying
```bash
terraform apply
```

**Expected flow:**
- Creates VPC network (3-5 seconds)
- Creates subnet (1-2 seconds)
- Creates VM instance (30-60 seconds)
- VM boots and runs cloud-init (~2 minutes)

### 5. Accessing VM
```bash
# Get connection string
terraform output ssh_connection_string

# Connect
ssh -i ~/.ssh/yandex_cloud_key ubuntu@<PUBLIC_IP>
```

### 6. Destroying
```bash
terraform destroy
```

## Challenges Encountered

### 1. Permission Issues
**Problem:** Initial attempts to create VM failed with:
```
Error: Permission denied to resource-manager.folder
```

**Solution:** 
- Switched from service account to OAuth token authentication
- Added necessary roles (`editor`, `compute.admin`) to service account
- For production, proper IAM setup is critical

### 2. Security Group Restrictions
**Problem:** Security group creation required additional permissions not available in free tier.

**Solution:**
- Removed custom security group
- Used default security group (acceptable for lab environment)
- Documented this decision

**For production:** Would create proper security groups with minimal required access.

### 3. Provider Version Compatibility
**Problem:** Provider version warnings and deprecation notices.

**Solution:**
- Pinned provider version: `~> 0.131`
- Documented version in code
- Considered for future updates

## Security Best Practices Implemented

### ✅ Implemented
1. **No hardcoded credentials** - all sensitive data in variables
2. **Sensitive files in `.gitignore`**:
   - `terraform.tfvars`
   - `*.tfstate*`
   - `service-account-key.json`
   - SSH private keys
3. **SSH key management** - keys generated locally, public key only in metadata
4. **OAuth token marked sensitive** in variables
5. **Separate tfvars.example** for safe documentation

### ⚠️ For Production
- Use remote state with encryption
- Implement proper RBAC
- Use security groups with minimal access
- Enable audit logging
- Use private subnets where possible
- Implement backup strategy

## Cost Management

### Free Tier Usage
- ✅ VM: 20% CPU, 1GB RAM (FREE)
- ✅ Storage: 10GB HDD (FREE)
- ✅ Network: Within free limits

### Best Practices
1. **Always run `terraform destroy`** after testing
2. **Tag resources** for cost tracking
3. **Use smallest instance** sufficient for needs
4. **Monitor usage** via cloud console

## Key Learnings

### 1. Infrastructure as Code Benefits
- **Version Control:** Infrastructure changes tracked in Git
- **Reproducibility:** Same config = same infrastructure
- **Documentation:** Code serves as documentation
- **Automation:** No manual clicking in console

### 2. Terraform Concepts
- **Providers:** Plugins for cloud APIs
- **Resources:** Infrastructure components
- **Data Sources:** Query existing infrastructure
- **Variables:** Make config reusable
- **Outputs:** Display important values
- **State:** Track real infrastructure

### 3. Terraform vs Manual
**Manual (Console):**
- ❌ No version history
- ❌ Error-prone (clicking)
- ❌ Hard to replicate
- ❌ No code review

**Terraform:**
- ✅ Version controlled
- ✅ Automated and consistent
- ✅ Easy to replicate
- ✅ Code review possible
- ✅ Plan before apply

## Next Steps for Lab 5

This VM will be used in Lab 5 (Ansible) for:
- Installing Docker
- Deploying applications from Labs 1-3
- Configuration management

**Options:**
1. Keep this VM running until Lab 5 complete
2. Destroy and recreate when needed (thanks to IaC!)
3. Use local VM instead

**Recommendation:** Keep running if within free tier limits, or recreate later.

## References

- [Terraform Documentation](https://www.terraform.io/docs)
- [Yandex Cloud Terraform Provider](https://registry.terraform.io/providers/yandex-cloud/yandex/latest/docs)
- [Yandex Cloud Free Tier](https://cloud.yandex.com/en/docs/billing/concepts/serverless-free-tier)
- [Lab 04 Requirements](../labs/lab04.md)
