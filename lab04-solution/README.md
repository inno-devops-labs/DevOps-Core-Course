# Lab 04 Solution — Infrastructure as Code (Terraform & Pulumi)

Complete solution for Lab 04, demonstrating Infrastructure as Code using two complementary tools: Terraform (declarative, HCL) and Pulumi (imperative, Python).

## 📚 Contents

```
lab04-solution/
├── terraform/                          # Terraform HCL configuration
│   ├── main.tf                         # Core infrastructure resources
│   ├── variables.tf                    # Input variable definitions
│   ├── outputs.tf                      # Output value definitions
│   ├── github.tf                       # GitHub provider (bonus task)
│   ├── terraform.tfvars                # Variable values (secrets)
│   ├── .gitignore                      # Files to exclude from Git
│   └── README.md                       # Terraform setup guide
│
├── pulumi/                             # Pulumi Python configuration
│   ├── __main__.py                     # Infrastructure code in Python
│   ├── requirements.txt                # Python dependencies
│   ├── Pulumi.yaml                     # Project metadata
│   ├── Pulumi.dev.yaml                 # Development stack config
│   ├── .gitignore                      # Files to exclude from Git
│   └── README.md                       # Pulumi setup guide
│
├── .github/workflows/                  # GitHub Actions CI/CD
│   └── terraform-validate.yml          # Terraform & Pulumi validation
│
├── docs/                               # Documentation
│   └── LAB04.md                        # Comprehensive implementation guide
│
└── README.md                           # This file
```

## 🎯 Quick Start

### Option 1: Terraform (Recommended for beginners)

```bash
cd terraform/

# Prerequisites
# 1. Install Terraform: https://developer.hashicorp.com/terraform/downloads
# 2. Configure AWS: aws configure
# 3. Generate SSH key: ssh-keygen -t rsa -b 4096 -f ~/.ssh/id_rsa

# Deploy infrastructure
terraform init
terraform plan
terraform apply

# Connect to instance
ssh -i ~/.ssh/id_rsa ubuntu@$(terraform output -raw instance_public_ip)

# Cleanup when done
terraform destroy
```

### Option 2: Pulumi (Use if you prefer Python)

```bash
cd pulumi/

# Prerequisites
# 1. Install Pulumi: https://www.pulumi.com/docs/install/
# 2. Configure AWS: aws configure
# 3. Generate SSH key: ssh-keygen -t rsa -b 4096 -f ~/.ssh/id_rsa

# Deploy infrastructure
python3 -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt

pulumi login --local
pulumi stack init dev
pulumi config set aws:region us-east-1
pulumi config set ssh_public_key_path ~/.ssh/id_rsa.pub

pulumi preview
pulumi up

# Connect to instance
ssh -i ~/.ssh/id_rsa ubuntu@$(pulumi stack output instance_public_ip)

# Cleanup when done
pulumi destroy
```
