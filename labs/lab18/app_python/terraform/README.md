## SETUP INSTRUCTIONS: TERRAFORM

### Set environment variables
```bash
export YC_TOKEN=$(yc iam create-token --impersonate-service-account-id <SERVICE_ACCOUNT_ID>)
export YC_CLOUD_ID=$(yc config get cloud-id)
export YC_FOLDER_ID=$(yc config get folder-id)
```

### Initialize Terraform
```bash
terraform init
```

### Plan infrastructure
```bash
terraform plan
```

### Apply infrastructure
```bash
terraform apply
```

### Access VM via SSH
```bash
ssh -i /path/to/terraform-vm-key ubuntu@<EXTERNAL_IP>
```

### Destroy resources
```bash
terraform destroy
```
