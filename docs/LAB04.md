# LAB04 — Infrastructure as Code (AWS) with Terraform & Pulumi

## 1. Cloud Provider & Infrastructure

- **Provider**: AWS (VocLabs / assumed role)
- **Region**: `us-east-1`
- **Instance type**: `t2.micro` (smallest/free-tier eligible)
- **Cost**: expected $0 for free tier (EIP is free **only while attached** to a running instance)

**Resources created (both tools):**

- VPC (`10.0.0.0/16`)
- Public subnet (`10.0.1.0/24`) + Internet Gateway + route table/association
- Security group rules:
  - SSH `22/tcp` **from my public IP (/32)**
  - HTTP `80/tcp` from `0.0.0.0/0`
  - App `5000/tcp` from `0.0.0.0/0`
- EC2 instance (Ubuntu 24.04 LTS)
- Elastic IP + association
- EC2 key pair (from local public key)

---

## 2. Terraform Implementation

- **Terraform version**: `Terraform v1.14.5`
- **Code location**: `terraform/`

**Key files:**

- `terraform/main.tf`: VPC, subnet, IGW, route table, SG, EC2, EIP
- `terraform/variables.tf`: configurable values
- `terraform/outputs.tf`: public IP + SSH command
- `terraform/keys/lab04_terraform_key(.pub)`: SSH keypair (private key is gitignored)

### Key commands (sanitized output)

**Init / Validate:**

```bash
cd terraform
terraform init
terraform validate
```

Output (excerpt):

```text
Terraform has been successfully initialized!
Success! The configuration is valid.
```

**Plan:**

```bash
terraform plan -out tfplan
```

Output (excerpt):

```text
Plan: 10 to add, 0 to change, 0 to destroy.
```

**Apply:**

```bash
terraform apply -auto-approve tfplan
```

Output (excerpt):

```text
Apply complete! Resources: 10 added, 0 changed, 0 destroyed.
Outputs:
  public_ip = "18.206.105.101"
  ssh_command = "ssh -i ./keys/lab04_terraform_key ubuntu@18.206.105.101"
```

### SSH proof

```bash
ssh -i keys/lab04_terraform_key ubuntu@18.206.105.101
```

Output (excerpt):

```text
OK
ip-10-0-1-29
Linux ip-10-0-1-29 ... Ubuntu ... x86_64 GNU/Linux
```

---

## 3. Pulumi Implementation

- **Pulumi version**: `v3.220.0`
- **Language**: Python
- **Code location**: `pulumi/`
- **Backend**: local (`pulumi login --local`) with `PULUMI_CONFIG_PASSPHRASE`

### Key commands (sanitized output)

**Preview:**

```bash
export PATH="/home/linh/.pulumi/bin:$PATH"
cd pulumi
export PULUMI_CONFIG_PASSPHRASE="***"
pulumi preview
```

Output (excerpt):

```text
Resources:
    + 11 to create
```

### Terraform cleanup (required by Task 2)

```bash
cd terraform
terraform destroy -auto-approve
```

Output (excerpt):

```text
Destroy complete! Resources: 10 destroyed.
```

**Up:**

```bash
cd pulumi
export PULUMI_CONFIG_PASSPHRASE="***"
pulumi up --yes
```

Output (excerpt):

```text
Resources:
    + 11 created

Outputs:
    public_ip: "54.237.106.34"
    ssh_command: "ssh -i terraform/keys/lab04_terraform_key ubuntu@54.237.106.34"
```

### SSH proof

```bash
ssh -i terraform/keys/lab04_terraform_key ubuntu@54.237.106.34
```

Output (excerpt):

```text
OK
ip-10-0-1-67
Linux ip-10-0-1-67 ... Ubuntu ... x86_64 GNU/Linux
```

---

## 4. Terraform vs Pulumi Comparison

- **Ease of learning**: Terraform felt simpler at first (HCL, very standard examples). Pulumi required more “coding mindset” but is still straightforward.
- **Code readability**: Pulumi is easier to refactor (functions/variables), Terraform is clearer for pure infra description.
- **Debugging**: Terraform errors are often very direct. Pulumi debugging is normal Python debugging, but you also need to understand Outputs and async values.
- **Documentation**: Terraform provider docs are extremely comprehensive. Pulumi examples are great, but you still often reference the underlying provider semantics.
- **Use cases**: Terraform for standard IaC and teams; Pulumi when you need strong reuse/abstractions and want full-language power.

---

## 5. Lab 5 Preparation & Cleanup

- **Keeping VM for Lab 5**: **Yes** (Pulumi-created VM)
- **VM public IP**: `54.237.106.34`
- **SSH**:

```bash
ssh -i terraform/keys/lab04_terraform_key ubuntu@54.237.106.34
```

If I decide not to keep it running, cleanup is:

```bash
cd pulumi
export PULUMI_CONFIG_PASSPHRASE="***"
pulumi destroy --yes
```

