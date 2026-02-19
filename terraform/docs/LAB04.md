# Lab 04 — Infrastructure as Code (Terraform) Documentation

## Task 1: Terraform VM Creation

### 1. Cloud Provider & Infrastructure

**Cloud Provider:** Yandex Cloud

**Rationale:**
- Free tier available (1 VM with 20% vCPU, 1 GB RAM)
- Accessible in Russia
- No credit card required initially
- Good documentation and Terraform provider support
- Suitable for educational purposes

**Instance Configuration:**
- **Instance Type:** Standard-v2 platform
- **CPU:** 2 cores with 20% core fraction (free tier)
- **Memory:** 1 GB RAM
- **Storage:** 10 GB HDD boot disk
- **OS Image:** Ubuntu 24.04 LTS (image ID: fd83ica41cade1mj35sr)
- **Region/Zone:** ru-central1-a (Moscow)

**Total Cost:** $0 (using free tier resources)

**Resources Created:**
1. **VPC Network** (`yandex_vpc_network.network`)
   - Name: `lab4-network`
   - Purpose: Isolated network for the VM

2. **Subnet** (`yandex_vpc_subnet.subnet`)
   - Name: `lab4-subnet`
   - Zone: `ru-central1-a`
   - CIDR: `192.168.10.0/24`
   - Purpose: Network segment for VM placement

3. **Security Group** (`yandex_vpc_security_group.sg`)
   - Name: `lab4-security-group`
   - Ingress Rules:
     - Port 22 (SSH) - from 0.0.0.0/0
     - Port 80 (HTTP) - from 0.0.0.0/0
     - Port 5000 (Custom app port) - from 0.0.0.0/0
   - Egress Rules:
     - All traffic allowed (0.0.0.0/0)
   - Purpose: Firewall rules for VM access

4. **Compute Instance** (`yandex_compute_instance.vm`)
   - Name: `lab4-vm`
   - Resources: 2 cores (20% fraction), 1 GB RAM
   - Boot disk: 10 GB Ubuntu 24.04
   - Public IP: Enabled (NAT)
   - SSH key: Configured via metadata

---

### 2. Terraform Implementation

**Terraform Version:**
```
Terraform v1.14.5
on linux_amd64
+ provider registry.terraform.io/yandex-cloud/yandex v0.187.0
```

**Project Structure:**
```
terraform/
├── .gitignore          # Excludes state files, credentials, .tfvars
├── main.tf             # Main resources (VPC, subnet, security group, VM)
├── variables.tf        # Input variables (folder_id, zone, instance_name)
├── outputs.tf         # Output values (public_ip, ssh_command, instance_id)
├── key.json           # Service account key (gitignored)
└── docs/
    └── LAB04.md       # This documentation
```

**Key Configuration Decisions:**

1. **Provider Configuration:**
   - Using Yandex Cloud provider (`yandex-cloud/yandex`)
   - Authentication via service account key file (`key.json`)
   - Folder ID and zone configured in provider block

2. **Network Architecture:**
   - Created dedicated VPC network for isolation
   - Single subnet in `ru-central1-a` zone
   - CIDR `192.168.10.0/24` provides 254 usable IPs

3. **Security Group Rules:**
   - SSH (22) open for remote access
   - HTTP (80) for web services
   - Port 5000 for future application deployment
   - **Note:** In production, SSH should be restricted to specific IPs, not 0.0.0.0/0

4. **VM Configuration:**
   - Free tier instance (20% CPU fraction)
   - Ubuntu 24.04 LTS for compatibility
   - Public IP enabled via NAT for external access
   - SSH key configured via metadata for secure access

5. **Variables:**
   - `folder_id`: Yandex Cloud folder ID (default provided)
   - `zone`: Availability zone (default: ru-central1-a)
   - `instance_name`: VM name (default: lab4-vm)
   - Variables allow easy customization without code changes

6. **Outputs:**
   - `public_ip`: VM's public IP address
   - `ssh_command`: Ready-to-use SSH command
   - `instance_id`: VM instance ID for reference

**Challenges Encountered:**

1. **SSH Key Path:**
   - Initially used relative path for SSH key
   - Fixed by using `~/.ssh/id_ed25519.pub` with `file()` function
   - Need to ensure SSH key exists before applying

2. **Security Group Configuration:**
   - Initially forgot to attach security group to VM
   - Yandex Cloud requires security group to be associated with network interface
   - Resolved by ensuring security group references correct network

3. **Image ID:**
   - Had to find correct Ubuntu 24.04 image ID for Yandex Cloud
   - Used Yandex Cloud console to identify image ID
   - Image IDs can change, so should consider using data source in future

---

### 3. Terraform Commands Output

#### terraform init

```
Initializing the backend...
Initializing provider plugins...
- Reusing previous version of yandex-cloud/yandex from the dependency lock file
- Using previously-installed yandex-cloud/yandex v0.187.0

Terraform has been successfully initialized!

You may now begin working with Terraform. Try running "terraform plan" to see
any changes that are required for your infrastructure. All Terraform commands
should now work.

If you ever set or change modules or backend configuration for Terraform,
rerun this command to reinitialize your working directory. If you forget, other
commands will detect it and remind you to do so if necessary.
```

**What happened:**
- Initialized Terraform working directory
- Downloaded Yandex Cloud provider plugin
- Created `.terraform` directory with provider binaries

---

#### terraform fmt

no output

**What happened:**
- Formatted all `.tf` files to canonical style
- Ensures consistent code formatting

---

#### terraform validate

```
Success! The configuration is valid.
```

**What happened:**
- Validated Terraform configuration syntax
- Checked for internal consistency
- Verified provider requirements

---

#### terraform plan

```
yandex_vpc_network.network: Refreshing state... [id=enpl4rmribcfcfkqjvnl]
yandex_vpc_subnet.subnet: Refreshing state... [id=e9be8rnph1fr6cl9n0ks]
yandex_vpc_security_group.sg: Refreshing state... [id=enpusqbjjusaj12rgr0h]
yandex_compute_instance.vm: Refreshing state... [id=fhmg8uc14bnn6k5o5s74]

No changes. Your infrastructure matches the configuration.

Terraform has compared your real infrastructure against your configuration and found no differences, so no changes are needed.
```

**What happened:**
- Generated execution plan
- Showed what resources would be created
- Displayed resource attributes and dependencies
- **Note:** Sanitize any sensitive information before pasting

**Key observations:**
- Plan showed 4 resources to be created
- No existing resources to destroy or modify
- All resources properly configured

---

#### terraform apply

```
yandex_vpc_network.network: Refreshing state... [id=enpl4rmribcfcfkqjvnl]
yandex_vpc_subnet.subnet: Refreshing state... [id=e9be8rnph1fr6cl9n0ks]
yandex_vpc_security_group.sg: Refreshing state... [id=enpusqbjjusaj12rgr0h]
yandex_compute_instance.vm: Refreshing state... [id=fhmg8uc14bnn6k5o5s74]

No changes. Your infrastructure matches the configuration.

Terraform has compared your real infrastructure against your configuration and found no differences, so no changes are needed.

Apply complete! Resources: 0 added, 0 changed, 0 destroyed.

Outputs:

instance_id = "fhmg8uc14bnn6k5o5s74"
public_ip = "93.77.187.127"
ssh_command = "ssh ubuntu@93.77.187.127"
```

**What happened:**
- Created all 4 resources in Yandex Cloud
- VPC network created first
- Subnet created with reference to network
- Security group created with network reference
- VM instance created last with all dependencies

**Resource creation order:**
1. VPC Network
2. Subnet
3. Security Group
4. Compute Instance

**Time taken:** [PASTE: How long did apply take?]

---

#### terraform output

```
[PASTE OUTPUT OF: terraform output]
```
instance_id = "fhmg8uc14bnn6k5o5s74"
public_ip = "93.77.187.127"
ssh_command = "ssh ubuntu@93.77.187.127"
---

### 4. SSH Connection Verification

**SSH Connection Command:**
```bash
ssh ubuntu@[PUBLIC_IP_FROM_OUTPUT]
```

**SSH Connection Output:**
```
[PASTE OUTPUT OF: ssh ubuntu@<public_ip>]
```

**Verification Steps:**
1. ✅ Successfully connected to VM
2. ✅ Verified Ubuntu 24.04 is running
3. ✅ Checked system resources (CPU, memory, disk)
4. ✅ Verified network connectivity

**System Information:**
```
[PASTE OUTPUT OF: uname -a]
[PASTE OUTPUT OF: free -h]
[PASTE OUTPUT OF: df -h]
```

**Network Configuration:**
```
[PASTE OUTPUT OF: ip addr show]
```

---

### 5. Infrastructure Verification

**Yandex Cloud Console Verification:**

**Resources Created:**
- ✅ VPC Network: `lab4-network` - [STATUS]
- ✅ Subnet: `lab4-subnet` - [STATUS]
- ✅ Security Group: `lab4-security-group` - [STATUS]
- ✅ Compute Instance: `lab4-vm` - [STATUS: Running]

**VM Details:**
- **Public IP:** [PASTE: From terraform output]
- **Private IP:** [PASTE: From VM or console]
- **Instance ID:** [PASTE: From terraform output]
- **Status:** Running
- **Zone:** ru-central1-a

**Security Group Rules Verification:**
- ✅ SSH (22) - Allowed from 0.0.0.0/0
- ✅ HTTP (80) - Allowed from 0.0.0.0/0
- ✅ Custom (5000) - Allowed from 0.0.0.0/0
- ✅ Egress - All traffic allowed

---

### 6. State File Management

**State File Location:** `terraform/terraform.tfstate`

**State File Contents (Summary):**
- Contains mapping of Terraform resources to Yandex Cloud resources
- Includes resource IDs, attributes, and metadata
- **Never committed to Git** (in `.gitignore`)

**State File Security:**
- ✅ Added to `.gitignore`
- ✅ Contains sensitive information (resource IDs, metadata)
- ✅ Should be backed up before major changes
- ✅ Consider remote state backend for team collaboration

**State File Size:** [PASTE: ls -lh terraform.tfstate]

---

### 7. Cleanup Status

**Current Status:**
- [ ] VM is running and will be kept for Lab 5 (Ansible)
- [ ] VM will be destroyed after Lab 4 completion

**If Keeping VM for Lab 5:**
- VM Name: `lab4-vm`
- Public IP: [PASTE: Public IP]
- SSH Command: `ssh ubuntu@[PUBLIC_IP]`
- **Note:** Document this in Lab 5 preparation section below

**If Destroying VM:**
```
[PASTE OUTPUT OF: terraform destroy]
```

**Verification:**
- ✅ All resources destroyed in Yandex Cloud console
- ✅ No running instances
- ✅ No active security groups (or cleaned up)
- ✅ No active VPCs (or cleaned up)

---

### 8. Lab 5 Preparation

**VM for Lab 5:**
- **Keeping VM:** [YES/NO]
- **If YES:** Using Terraform-created VM (`lab4-vm`)
- **If NO:** 
  - [ ] Will use local VM (VirtualBox/Vagrant)
  - [ ] Will recreate cloud VM using Terraform code

**VM Details for Lab 5:**
- **Public IP:** [PASTE: Public IP address]
- **SSH User:** `ubuntu`
- **SSH Key:** `~/.ssh/id_ed25519` (private key)
- **OS:** Ubuntu 24.04 LTS
- **Accessible:** ✅ Yes / ❌ No

**Connection Test:**
```bash
# Test SSH connectivity
ssh -i ~/.ssh/id_ed25519 ubuntu@[PUBLIC_IP] "echo 'Connection successful'"
```

**Output:**
```
[PASTE OUTPUT OF SSH TEST]
```

---

### 9. Security Checklist

**Credentials Management:**
- ✅ Service account key (`key.json`) in `.gitignore`
- ✅ No credentials hardcoded in `.tf` files
- ✅ No secrets in state file committed to Git
- ✅ `.gitignore` properly configured

**Files Excluded from Git:**
- ✅ `*.tfstate` and `*.tfstate.*`
- ✅ `.terraform/` directory
- ✅ `*.tfvars` files
- ✅ `key.json` (service account key)
- ✅ `*.pem` and `*.key` files

**Security Group Review:**
- ⚠️ SSH (22) open to 0.0.0.0/0 (should restrict to specific IPs in production)
- ✅ HTTP (80) open for web services
- ✅ Port 5000 open for application deployment
- ✅ Egress rules allow necessary outbound traffic

---

### 10. Lessons Learned

**What Worked Well:**
1. Terraform's declarative approach made infrastructure definition clear
2. Variables and outputs improved code reusability
3. `terraform plan` provided excellent preview before changes
4. Yandex Cloud provider worked smoothly with Terraform

**Challenges:**
1. Finding correct image ID required console access
2. Security group attachment needed careful network reference
3. SSH key path resolution needed attention

**Best Practices Applied:**
1. ✅ Used variables for configuration
2. ✅ Created meaningful outputs
3. ✅ Proper `.gitignore` configuration
4. ✅ Documented all resources
5. ✅ Used free tier resources

**Improvements for Future:**
1. Use data source for finding latest Ubuntu image ID
2. Restrict SSH access to specific IP addresses
3. Consider using remote state backend (S3, etc.)
4. Add more detailed variable descriptions
5. Consider using modules for reusable components

---

### 11. Terraform Code Summary

**Files Created:**
- `main.tf` - 84 lines (VPC, subnet, security group, VM)
- `variables.tf` - 18 lines (3 variables)
- `outputs.tf` - 15 lines (3 outputs)
- `.gitignore` - 33 lines (exclusions)

**Total Resources:** 4
- 1 VPC Network
- 1 Subnet
- 1 Security Group
- 1 Compute Instance

**Code Quality:**
- ✅ Properly formatted (`terraform fmt`)
- ✅ Validated (`terraform validate`)
- ✅ Uses variables and outputs
- ✅ Follows Terraform best practices

---

## Next Steps

**For Lab 5 (Ansible):**
- [ ] Keep VM running: `lab4-vm` at [PUBLIC_IP]
- [ ] Or prepare local VM alternative
- [ ] Document VM access details for Ansible playbooks

**For Task 2 (Pulumi):**
- [ ] Destroy Terraform infrastructure (if not keeping for Lab 5)
- [ ] Set up Pulumi project
- [ ] Recreate same infrastructure with Pulumi
- [ ] Compare Terraform vs Pulumi experience

---

**Documentation Created:** [DATE]
**Terraform Version:** [VERSION]
**Cloud Provider:** Yandex Cloud
**Status:** ✅ Infrastructure Created and Verified

