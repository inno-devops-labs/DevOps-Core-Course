## Lab 4 — Infrastructure as Code (Terraform & Pulumi)

### 1. Cloud Provider & Infrastructure
- **Provider:** Yandex Cloud (reason: accessible in Russia, free tier).
- **Instance Type:** 2 vCPU (20% core fraction), 1 GB RAM (free tier).
- **Region:** ru-central1-a.
- **Cost:** $0 (free tier).
- **Resources Created:** VPC network, subnet, security group, VM with public IP.

### 2. Terraform Implementation
- **Version:** 1.9.x
- **Project Structure:** main.tf, variables.tf, outputs.tf, terraform.tfvars (gitignored).
- **Key Decisions:** Used ephemeral public IP for simplicity; security group allows SSH, HTTP, port 5000.
- **Challenges:** Had to adjust Yandex provider authentication; resolved by using service account key file.

### 3. Pulumi Implementation
- **Version:** 3.x
- **Language:** Python 3.13
- **How Code Differs:** Imperative style; used Python to read SSH key file; configuration via `pulumi config`.
- **Advantages:** Could use Python logic (file reading), better IDE support.
- **Challenges:** Had to install provider package manually; resolved by adding to requirements.txt.

### 4. Terraform vs Pulumi Comparison
- **Ease of Learning:** Terraform HCL is simpler for basic cases, but Pulumi is natural for developers.
- **Code Readability:** Terraform is declarative and concise; Pulumi code is more verbose but allows complex logic.
- **Debugging:** Pulumi's Python stack traces are familiar; Terraform's error messages can be cryptic.
- **Documentation:** Both have excellent docs, but Pulumi's examples are more varied due to multiple languages.
- **Use Case:** Terraform is great for pure infrastructure, Pulumi when you need to integrate with application code or reuse logic.

### 5. Lab 5 Preparation & Cleanup
- **VM for Lab 5:** I am keeping the VM created with Terraform because Lab 5 requires a running VM for Ansible.
- **Cleanup Status:** Terraform resources destroyed; Pulumi VM is running (will keep until Lab 5 completed).