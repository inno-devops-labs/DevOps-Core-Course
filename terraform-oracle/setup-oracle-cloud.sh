#!/bin/bash
# Script to setup Oracle Cloud Infrastructure for Terraform
set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Oracle Cloud Setup for Terraform ===${NC}\n"

# Step 1: Create OCI directory
echo -e "${YELLOW}Step 1: Creating ~/.oci directory${NC}"
mkdir -p ~/.oci
echo -e "${GREEN}✓ Directory created${NC}\n"

# Step 2: Generate API Key Pair
echo -e "${YELLOW}Step 2: Generating API Key Pair${NC}"
if [ ! -f ~/.oci/oci_api_key.pem ]; then
    echo "Generating new API key pair..."
    openssl genrsa -out ~/.oci/oci_api_key.pem 2048 2>/dev/null
    openssl rsa -pubout -in ~/.oci/oci_api_key.pem -out ~/.oci/oci_api_key_public.pem 2>/dev/null
    chmod 600 ~/.oci/oci_api_key.pem
    chmod 644 ~/.oci/oci_api_key_public.pem
    echo -e "${GREEN}✓ API key pair generated${NC}"
else
    echo -e "${YELLOW}API key already exists, skipping...${NC}"
fi
echo ""

# Step 3: Generate SSH Key for VM
echo -e "${YELLOW}Step 3: Generating SSH Key for VM${NC}"
if [ ! -f ~/.ssh/oracle_cloud_key ]; then
    echo "Generating SSH key..."
    ssh-keygen -t rsa -b 2048 -f ~/.ssh/oracle_cloud_key -N "" -C "oracle-cloud-vm" >/dev/null 2>&1
    echo -e "${GREEN}✓ SSH key generated${NC}"
else
    echo -e "${YELLOW}SSH key already exists, skipping...${NC}"
fi
echo ""

# Step 4: Display Public Key
echo -e "${YELLOW}Step 4: API Public Key (Add this to OCI Console)${NC}"
echo -e "${GREEN}================================================${NC}"
cat ~/.oci/oci_api_key_public.pem
echo -e "${GREEN}================================================${NC}"
echo ""
echo "Add this key to OCI Console:"
echo "1. Go to: https://cloud.oracle.com/"
echo "2. Profile icon → User Settings"
echo "3. Scroll to 'API Keys' section"
echo "4. Click 'Add API Key' → 'Paste Public Key'"
echo "5. Paste the key above"
echo "6. Copy the fingerprint shown"
echo ""
read -p "Press Enter after adding the key to OCI Console..."
echo ""

# Step 5: Collect OCIDs
echo -e "${YELLOW}Step 5: Collecting Oracle Cloud Information${NC}"
echo "Please provide the following information from OCI Console:"
echo ""

read -p "Enter your Tenancy OCID (ocid1.tenancy.oc1..): " TENANCY_OCID
read -p "Enter your User OCID (ocid1.user.oc1..): " USER_OCID
read -p "Enter your Compartment OCID (or press Enter to use tenancy): " COMPARTMENT_OCID
if [ -z "$COMPARTMENT_OCID" ]; then
    COMPARTMENT_OCID=$TENANCY_OCID
fi
read -p "Enter API Key Fingerprint (xx:xx:xx:..): " FINGERPRINT
read -p "Enter Region (e.g., eu-frankfurt-1): " REGION

echo ""

# Step 6: Create terraform.tfvars
echo -e "${YELLOW}Step 6: Creating terraform.tfvars${NC}"
cat > terraform.tfvars <<EOF
# Oracle Cloud Configuration
tenancy_ocid     = "$TENANCY_OCID"
user_ocid        = "$USER_OCID"
compartment_ocid = "$COMPARTMENT_OCID"
fingerprint      = "$FINGERPRINT"
region           = "$REGION"

# Path to your OCI API private key
private_key_path = "~/.oci/oci_api_key.pem"

# SSH Configuration
ssh_user            = "ubuntu"
ssh_public_key_path = "~/.ssh/oracle_cloud_key.pub"
EOF

echo -e "${GREEN}✓ terraform.tfvars created${NC}\n"

echo -e "${GREEN}=== Setup Complete! ===${NC}\n"
echo "Next steps:"
echo "1. cd terraform-oracle/"
echo "2. terraform init"
echo "3. terraform plan"
echo "4. terraform apply"
echo ""
echo -e "${YELLOW}Important: Files 'terraform.tfvars' and private keys are in .gitignore${NC}"
echo ""
echo "SSH Public Key for reference:"
echo -e "${GREEN}================================================${NC}"
cat ~/.ssh/oracle_cloud_key.pub
echo -e "${GREEN}================================================${NC}"
