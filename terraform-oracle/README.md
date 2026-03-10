# Lab 04 - Terraform with Oracle Cloud (Always Free Tier)

This directory contains Terraform configuration for creating a VM in Oracle Cloud Infrastructure (OCI) using the **Always Free Tier** (永久免费).

## Why Oracle Cloud?

- ✅ **Always Free** - не trial, а навсегда бесплатно
- ✅ **Не требует карты** для Free Tier ресурсов
- ✅ **Щедрые лимиты**: 2 AMD VM или 4 ARM VM, 200GB storage
- ✅ **Отличная поддержка Terraform**

## Prerequisites

1. **Oracle Cloud Account**: Register at https://www.oracle.com/cloud/free/
2. **Terraform**: Installed (v1.5.7+)
3. **SSH Key**: Generated for VM access

## Oracle Cloud Setup

### Step 1: Create Oracle Cloud Account

1. Go to: https://www.oracle.com/cloud/free/
2. Click "Start for free"
3. Fill in the registration form:
   - Email address
   - Country/Territory: Russia (or your country)
   - First/Last name
4. Verify your email
5. Complete additional information:
   - **Home Region**: Choose closest (e.g., `eu-frankfurt-1`, `us-phoenix-1`)
   - **Cloud Account Name**: Choose unique name (will be part of your login)
6. Verify phone number (SMS code)
7. **No credit card required** for Always Free resources!

### Step 2: Get Required OCIDs and Setup API Key

After registration, you need to collect:

#### 2.1 Get OCIDs from Console

Login to: https://cloud.oracle.com/

**Get Tenancy OCID:**
1. Click on Profile icon (top right) → Tenancy: `<your-tenancy-name>`
2. Copy **OCID** (starts with `ocid1.tenancy.oc1..`)

**Get User OCID:**
1. Click on Profile icon → User Settings
2. Copy **OCID** (starts with `ocid1.user.oc1..`)

**Get Compartment OCID:**
1. Menu → Identity & Security → Compartments
2. Click on `root` compartment (or create new one)
3. Copy **OCID** (starts with `ocid1.compartment.oc1..` or same as tenancy for root)

**Get Region:**
- See the region in top right corner (e.g., `EU Frankfurt`)
- Region identifier: `eu-frankfurt-1` (or `us-phoenix-1`, etc.)

#### 2.2 Create API Key Pair

Oracle Cloud uses API keys for authentication. Create them:

```bash
# Create directory for OCI config
mkdir -p ~/.oci

# Generate API key pair
openssl genrsa -out ~/.oci/oci_api_key.pem 2048
openssl rsa -pubout -in ~/.oci/oci_api_key.pem -out ~/.oci/oci_api_key_public.pem

# Set correct permissions
chmod 600 ~/.oci/oci_api_key.pem
chmod 644 ~/.oci/oci_api_key_public.pem

# Display public key (you'll need to add it to OCI)
cat ~/.oci/oci_api_key_public.pem
```

#### 2.3 Add Public Key to Oracle Cloud

1. In OCI Console: Profile icon → User Settings
2. Scroll down to **API Keys** section
3. Click **Add API Key**
4. Select **Paste Public Key**
5. Paste the contents of `~/.oci/oci_api_key_public.pem`
6. Click **Add**
7. **Copy the fingerprint** shown (format: `xx:xx:xx:xx:...`)

### Step 3: Generate SSH Key for VM Access

```bash
# Generate SSH key for VM access
ssh-keygen -t rsa -b 2048 -f ~/.ssh/oracle_cloud_key -N "" -C "oracle-cloud-vm"

# Display public key
cat ~/.ssh/oracle_cloud_key.pub
```

### Step 4: Configure Terraform

```bash
cd terraform-oracle/

# Copy example variables file
cp terraform.tfvars.example terraform.tfvars

# Edit terraform.tfvars with your values
# Replace with your actual OCIDs and fingerprint
```

**Example `terraform.tfvars`:**
```hcl
tenancy_ocid     = "ocid1.tenancy.oc1..aaaaaaaa..."
user_ocid        = "ocid1.user.oc1..aaaaaaaa..."
compartment_ocid = "ocid1.compartment.oc1..aaaaaaaa..."  # or same as tenancy_ocid for root
fingerprint      = "a1:b2:c3:d4:e5:f6:g7:h8:i9:j0:k1:l2:m3:n4:o5:p6"
region           = "eu-frankfurt-1"

private_key_path    = "~/.oci/oci_api_key.pem"
ssh_user            = "ubuntu"
ssh_public_key_path = "~/.ssh/oracle_cloud_key.pub"
```

## Infrastructure Resources

This configuration creates (all in **Always Free Tier**):

- **VCN** (Virtual Cloud Network): `lab04-vcn` (10.0.0.0/16)
- **Internet Gateway**: For public internet access
- **Route Table**: Routes traffic to internet gateway
- **Security List**: Firewall rules
  - SSH (22)
  - HTTP (80)
  - App port (5000)
  - ICMP (ping)
- **Subnet**: `lab04-subnet` (10.0.1.0/24)
- **Compute Instance**: 
  - Shape: `VM.Standard.E2.1.Micro` (Always Free)
  - CPU: 1 OCPU (1/8 physical core)
  - RAM: 1 GB
  - Disk: 50 GB (can be up to 200GB free)
  - OS: Ubuntu 22.04 LTS
  - Public IP: Yes

## Usage

### Initialize Terraform

```bash
cd terraform-oracle/
terraform init
```

### Validate Configuration

```bash
terraform fmt      # Format code
terraform validate # Check syntax
```

### Preview Changes

```bash
terraform plan
```

### Apply Infrastructure

```bash
terraform apply

# Type 'yes' when prompted
# Wait ~2-3 minutes for VM to be created
```

### Get Outputs

```bash
terraform output
terraform output public_ip
terraform output ssh_connection_string
```

### Connect to VM

```bash
# Get SSH command from output
terraform output -raw ssh_connection_string

# Or manually
ssh -i ~/.ssh/oracle_cloud_key ubuntu@<PUBLIC_IP>

# First connection may take a few minutes as cloud-init completes
```

### Destroy Infrastructure

```bash
terraform destroy

# Type 'yes' when prompted
```

## File Structure

```
terraform-oracle/
├── main.tf                    # Main resources (VM, network, security)
├── variables.tf               # Input variables
├── outputs.tf                 # Output values
├── terraform.tfvars.example   # Example configuration (commit this)
├── terraform.tfvars           # Actual values (DO NOT COMMIT)
└── README.md                  # This file
```

## Security Notes

### Files to NEVER commit to Git:
- `terraform.tfvars` - Contains sensitive OCIDs
- `*.tfstate*` - Contains infrastructure state
- `~/.oci/*.pem` - Private API keys
- `~/.ssh/oracle_cloud_key` - SSH private key

These are already in `.gitignore`.

## Free Tier Limits

Oracle Cloud Always Free Tier includes:

**Compute:**
- 2x AMD VM.Standard.E2.1.Micro (1/8 OCPU, 1GB RAM each)
- OR 4x ARM Ampere A1 cores + 24GB RAM (can split into multiple VMs)

**Storage:**
- 2x Block Volumes (200GB total)
- 10GB Object Storage

**Network:**
- 10TB outbound data transfer/month

**This configuration uses: 1 AMD VM (50% of free compute)**

## Troubleshooting

### "Out of host capacity"

If you get capacity errors:
1. Try different availability domain
2. Try different region
3. ARM instances (Ampere A1) have better availability

Change shape in `main.tf`:
```hcl
shape = "VM.Standard.A1.Flex"  # ARM instance
shape_config {
  memory_in_gbs = 6   # Up to 24GB free
  ocpus         = 1   # Up to 4 OCPUs free
}
```

### SSH Connection Refused

```bash
# Check if VM is running
terraform output vm_state

# Check cloud-init status (after first SSH)
ssh -i ~/.ssh/oracle_cloud_key ubuntu@<IP>
cloud-init status

# Wait if cloud-init is still running
```

### API Authentication Issues

```bash
# Verify fingerprint matches
openssl rsa -pubout -outform DER -in ~/.oci/oci_api_key.pem | \
  openssl md5 -c | \
  awk '{print $2}'

# Should match the fingerprint in OCI Console and terraform.tfvars
```

## Cost Management

This configuration uses **Always Free Tier** resources:
- ✅ **$0/month forever** when using free tier resources
- ✅ No automatic upgrades to paid resources
- ✅ You can't accidentally exceed free tier limits for these VMs

**Always run `terraform destroy` when done testing to free up resources!**

## Next Steps

After successful VM creation:
1. Verify SSH access
2. Document public IP and connection details
3. Keep VM running for Lab 5 (Ansible) OR
4. Run `terraform destroy` and recreate later

## Resources

- [Oracle Cloud Free Tier](https://www.oracle.com/cloud/free/)
- [OCI Terraform Provider](https://registry.terraform.io/providers/oracle/oci/latest/docs)
- [OCI Documentation](https://docs.oracle.com/en-us/iaas/Content/home.htm)
- [Always Free Resources](https://docs.oracle.com/en-us/iaas/Content/FreeTier/freetier_topic-Always_Free_Resources.htm)
