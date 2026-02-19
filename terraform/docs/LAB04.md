# LAB04 — Infrastructure as Code (Terraform & Pulumi)

## 1. Cloud Provider & Infrastructure

**Cloud Provider:** Yandex Cloud  
**Folder ID:** b1g1cmmbss046n25oln3  
**Region / Zone:** ru-central1-a  
**Instance Type:** standard-v2 (2 vCPU with 20% core fraction, 1 GB RAM)  
**Disk:** 10 GB HDD  
**Operating System:** Ubuntu 24.04 LTS  

The smallest available instance type compatible with Yandex Cloud free tier was selected to minimize cost.

### Security Configuration

The following ports are opened in the security group:

- TCP 22 — SSH (restricted access for remote management)
- TCP 80 — HTTP (future deployment)
- TCP 5000 — Application port (DevOps Info Service from previous labs)

### Created Resources

- VPC Network (`lab-network`)
- Subnet (`lab-subnet`)
- Security Group (`lab-sg`)
- Virtual Machine (`lab-vm`)
- Public IP Address

Estimated cost: **0 RUB** (free tier usage).
Terraform Version: 1.9.8
Pulumi Version: 3.222.0

---

## 2. Terraform Implementation

### Terraform Version
Terraform CLI 1.9.x (Ubuntu Linux)

### Project Structure

terraform/
├── main.tf
├── variables.tf
├── outputs.tf
└── docs/LAB04.md


### Authentication

Authentication was configured using a Yandex Cloud service account JSON key:
~/.yc/terraform-key.json


Provider configuration:

```hcl
provider "yandex" {
  service_account_key_file = pathexpand("~/.yc/terraform-key.json")
  folder_id                = var.folder_id
  zone                     = var.zone
}
```

### Workflow

```
terraform init
terraform fmt
terraform validate
terraform plan
terraform apply
```


Example output from terraform plan:
Plan: 3 to add, 0 to change, 0 to destroy.

Example output from terraform apply:
Apply complete! Resources: 3 added, 0 changed, 0 destroyed.

Outputs:

external_ip = "X.X.X.X"


SSH Verification
ssh ubuntu@<external_ip>


SSH connection was successful.

Cleanup

After verifying functionality, Terraform resources were destroyed:

terraform destroy


All resources created by Terraform were removed successfully to avoid duplication and unnecessary usage.

## 3. Pulumi Implementation
Pulumi Version

Pulumi CLI v3.222.0

Language

Python

Project Structure
pulumi/lab04-yc/
 ├── Pulumi.yaml
 ├── Pulumi.dev.yaml
 ├── requirements.txt
 ├── __main__.py
 └── venv/

Authentication

Pulumi uses the same Yandex Cloud service account key:

export YC_SERVICE_ACCOUNT_KEY_FILE=/home/vboxuser/.yc/terraform-key.json

Resources Created

The same infrastructure was recreated using Pulumi:

VpcNetwork

VpcSubnet

VpcSecurityGroup

ComputeInstance

Public IP

Pulumi Commands
pulumi preview
pulumi up


Preview example:

+ yandex:index:VpcNetwork
+ yandex:index:VpcSubnet
+ yandex:index:VpcSecurityGroup
+ yandex:index:ComputeInstance


Apply output:

Outputs:
  external_ip : "93.77.190.119"
  zone        : "ru-central1-a"

SSH Verification
ssh ubuntu@93.77.190.119


SSH access was successful.

## 4. Terraform vs Pulumi Comparison
Ease of Learning

Terraform was easier to start with due to extensive documentation and straightforward declarative syntax. Pulumi required more setup (virtual environments, Python dependencies).

Code Readability

Terraform configurations are compact and declarative, making them easy to read for simple infrastructure. Pulumi provides more flexibility but adds programming complexity.

Debugging

Terraform errors are generally clear during plan and apply. Pulumi provides Python stack traces, which can be more detailed but sometimes harder to interpret.

Documentation

Terraform has broader documentation and community examples. Pulumi documentation is solid but less extensive for Yandex Cloud specifically.

Use Case Preference

Terraform is preferable for straightforward infrastructure definitions.
Pulumi is more powerful when complex logic, loops, or programming constructs are required.

## 5. Lab 5 Preparation & Cleanup

For Lab 5 (Ansible), the VM created using Pulumi will be kept active.

Active VM:

IP Address: 93.77.190.119
Zone: ru-central1-a
User: ubuntu

Terraform resources were destroyed.
Pulumi-managed VM remains running for future configuration management tasks.

No secrets or state files were committed to Git.

Infrastructure can be recreated at any time using:

terraform apply


or

pulumi up

Terraform state was stored locally. The file terraform.tfstate was added to .gitignore and not committed to the repository.

