# Lab04 — Infrastructure as Code with Terraform and Pulumi (AWS EC2 + nginx)

## Objective

The goal of this lab is to provision cloud infrastructure using two Infrastructure as Code (IaC) tools:

- Terraform
- Pulumi (Python)

The infrastructure consists of:

- AWS EC2 instance (Ubuntu 22.04)
- Security Group allowing SSH (22) and HTTP (80)
- SSH key pair for secure access
- nginx automatically installed and started via user_data
- Verification of nginx accessibility
- Proper destruction of infrastructure

---

# Part 1 — Terraform

## Step 1 — Initialize Terraform

```bash
cd terraform
terraform init
```

Result:

```
Terraform has been successfully initialized!
```

---

## Step 2 — Terraform configuration

main.tf defines:

- provider aws
- aws_security_group
- aws_key_pair
- aws_instance
- nginx installation via user_data

user_data script:

```bash
#!/bin/bash
set -eux
apt-get update -y
apt-get install -y nginx
systemctl enable nginx
systemctl start nginx
echo "lab04 nginx ok" > /var/www/html/index.html
```

---

## Step 3 — Create infrastructure

```bash
terraform apply
```

Result:

```
Apply complete! Resources: 3 added.

Outputs:
public_ip = "52.90.21.144"
```

Created resources:

- EC2 instance
- Security group
- Key pair

---

## Step 4 — Connect to instance

```bash
ssh -i ~/.ssh/id_ed25519 ubuntu@52.90.21.144
```

Connection successful.

---

## Step 5 — Verify nginx inside VM

```bash
curl -i http://localhost
```

Result:

```
HTTP/1.1 200 OK

lab04 nginx ok
```

nginx is running successfully.

---

## Step 6 — Verify access using SSH tunnel

External port 80 was restricted in the AWS Learner Lab environment.

SSH port forwarding was used:

```bash
ssh -N -L 8080:localhost:80 ubuntu@52.90.21.144
```

Verification from local machine:

```bash
curl -i http://127.0.0.1:8080
```

Result:

```
HTTP/1.1 200 OK

lab04 nginx ok
```

This confirms nginx is accessible.

---

## Step 7 — Destroy Terraform infrastructure

```bash
terraform destroy
```

Result:

```
Destroy complete! Resources: 3 destroyed.
```

Verification:

```bash
terraform show
```

Result:

```
No resources are represented.
```

Terraform part completed successfully.

---

# Part 2 — Pulumi (Python)

## Step 8 — Initialize Pulumi project

```bash
pulumi login --local
pulumi new aws-python
```

Stack created:

```
lab04-pulumi-dev
```

---

## Step 9 — Pulumi implementation

__main__.py defines:

- aws.ec2.SecurityGroup
- aws.ec2.KeyPair
- aws.ec2.Instance
- nginx installation via user_data

user_data:

```bash
#!/bin/bash
set -eux
apt-get update -y
apt-get install -y nginx
systemctl enable nginx
systemctl start nginx
echo "lab04 nginx ok" > /var/www/html/index.html
```

---

## Step 10 — Deploy infrastructure

```bash
pulumi up
```

Result:

```
Outputs:
public_ip  : "3.86.232.69"
ssh_command: "ssh -i ~/.ssh/id_ed25519 ubuntu@3.86.232.69"

Resources:
+ 4 created
```

Created resources:

- EC2 instance
- Security group
- Key pair
- Pulumi stack

---

## Step 11 — Verify nginx

Connect:

```bash
ssh -i ~/.ssh/id_ed25519 ubuntu@3.86.232.69
```

Check nginx:

```bash
curl -i http://localhost
```

Result:

```
HTTP/1.1 200 OK

lab04 nginx ok
```

Verify via SSH tunnel:

```bash
ssh -N -L 8080:localhost:80 ubuntu@3.86.232.69
```

Local verification:

```bash
curl -i http://127.0.0.1:8080
```

Result:

```
HTTP/1.1 200 OK

lab04 nginx ok
```

Pulumi deployment works correctly.

---

## Step 12 — Destroy Pulumi infrastructure

```bash
pulumi destroy
```

Verification:

```bash
pulumi stack
```

Result:

```
No resources currently in this stack
```

Pulumi infrastructure destroyed successfully.

---

# Final Result

Both Terraform and Pulumi successfully:

- Provisioned EC2 instance
- Configured Security Group
- Installed nginx automatically
- Verified nginx operation
- Destroyed infrastructure cleanly

Infrastructure lifecycle was fully managed using IaC tools.

---

# Conclusion

This lab demonstrates practical Infrastructure as Code usage with Terraform and Pulumi.

Key achievements:

- Automated cloud provisioning
- Automated software configuration
- Secure SSH access
- Infrastructure reproducibility
- Clean resource destruction

Both tools provide reliable and repeatable infrastructure management.

Lab04 completed successfully.

