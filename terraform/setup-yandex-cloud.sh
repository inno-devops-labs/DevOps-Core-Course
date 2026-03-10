#!/bin/bash
# Script to setup Yandex Cloud for Terraform
set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Yandex Cloud Setup for Terraform ===${NC}\n"

# Use yc from the installation path
YC="/Users/macbook_leonid/yandex-cloud/bin/yc"

# Your Cloud and Folder IDs from the screenshot
CLOUD_ID="b1g5j96nedr4nscj4tgp"
FOLDER_ID="b1ggslr285ass6at43mg"
ZONE="ru-central1-a"

echo -e "${YELLOW}Step 1: Initialize Yandex Cloud CLI${NC}"
echo "You need to get an OAuth token."
echo "1. Open this URL in your browser: https://oauth.yandex.ru/authorize?response_type=token&client_id=1a6990aa636648e9b2ef855fa7bec2fb"
echo "2. Grant permissions"
echo "3. Copy the OAuth token from the URL"
echo ""
read -p "Enter your OAuth token: " OAUTH_TOKEN

# Configure yc
$YC config set token "$OAUTH_TOKEN"
$YC config set cloud-id "$CLOUD_ID"
$YC config set folder-id "$FOLDER_ID"

echo -e "\n${GREEN}✓ CLI configured${NC}\n"

echo -e "${YELLOW}Step 2: Create Service Account${NC}"
# Check if service account already exists
if $YC iam service-account get terraform-sa &>/dev/null; then
    echo "Service account 'terraform-sa' already exists"
    SA_ID=$($YC iam service-account get terraform-sa --format json | grep '"id":' | cut -d'"' -f4)
else
    # Create service account
    $YC iam service-account create \
        --name terraform-sa \
        --description "Service account for Terraform Lab04"

    SA_ID=$($YC iam service-account get terraform-sa --format json | grep '"id":' | cut -d'"' -f4)
    echo -e "${GREEN}✓ Service account created${NC}"
fi

echo "Service Account ID: $SA_ID"

echo -e "\n${YELLOW}Step 3: Assign Editor Role${NC}"
# Assign editor role to service account
$YC resource-manager folder add-access-binding "$FOLDER_ID" \
    --role editor \
    --subject serviceAccount:"$SA_ID" \
    || echo "Role already assigned"

echo -e "${GREEN}✓ Role assigned${NC}\n"

echo -e "${YELLOW}Step 4: Create Authorized Key${NC}"
# Create authorized key for service account
KEY_FILE="./service-account-key.json"
if [ -f "$KEY_FILE" ]; then
    read -p "Key file already exists. Overwrite? (y/n): " OVERWRITE
    if [ "$OVERWRITE" != "y" ]; then
        echo "Using existing key file"
    else
        $YC iam key create \
            --service-account-name terraform-sa \
            --output "$KEY_FILE" \
            --description "Key for Terraform Lab04"
        echo -e "${GREEN}✓ New key created${NC}"
    fi
else
    $YC iam key create \
        --service-account-name terraform-sa \
        --output "$KEY_FILE" \
        --description "Key for Terraform Lab04"
    echo -e "${GREEN}✓ Key created: $KEY_FILE${NC}"
fi

echo -e "\n${YELLOW}Step 5: Create terraform.tfvars${NC}"
cat > terraform.tfvars <<EOF
# Yandex Cloud Configuration
cloud_id  = "$CLOUD_ID"
folder_id = "$FOLDER_ID"
zone      = "$ZONE"

# Path to service account key file
service_account_key_file = "./service-account-key.json"

# SSH Configuration
ssh_user            = "ubuntu"
ssh_public_key_path = "~/.ssh/yandex_cloud_key.pub"
EOF

echo -e "${GREEN}✓ terraform.tfvars created${NC}\n"

echo -e "${GREEN}=== Setup Complete! ===${NC}\n"
echo "Next steps:"
echo "1. cd terraform/"
echo "2. terraform init"
echo "3. terraform plan"
echo "4. terraform apply"
echo ""
echo -e "${YELLOW}Important: Files 'service-account-key.json' and 'terraform.tfvars' are in .gitignore${NC}"
