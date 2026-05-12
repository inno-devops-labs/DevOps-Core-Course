# Lab 4 — Terraform Documentation

## 1. Cloud Provider & Infrastructure
- **Cloud provider chosen:** Yandex Cloud — chosen because it offers free tier, works in Russia without VPN issues, and has good Terraform/Pulumi provider support.
- **Instance type/size and why:** 
  - Platform: standard-v2
  - Resources: 2 vCPUs, 1 GB RAM, core_fraction=20%
  - Disk: 10 GB network-hdd
  - Reason: This matches Yandex Cloud free tier limits, costs $0, and is sufficient for running Docker containers and testing.
- **Region/zone selected:** ru-central1-a (Moscow region) — lowest latency for users in Russia/Europe.
- **Total cost:** $0 (free tier, within limits)
- **Resources created:**
  - VPC Network (lab4-vm-network)
  - Subnet (lab4-vm-subnet, CIDR: 192.168.10.0/24)
  - Security Group (lab4-vm-security-group) with rules for ports 22, 80, 5000
  - Compute Instance (lab4-vm) running Ubuntu 22.04 LTS
  - Public IP address (assigned via NAT)

## 2. Terraform Implementation
- Terraform version used - 1.9.8
- Project structure explanation - root dir terraform containing main.tf, variables.tf, outputs.tf, terraform.tfvars and inno-key.json
- Key configuration decisions - Used service account key instead of short-lived IAM token
- **Challenges encountered**
    - SSH public key path issue — Terraform doesn't expand `~`, fixed by using absolute path

### terraform init
- ![terraform init](../artifacts/terraform-init.png)

### terraform plan
- ![terraform plan start](../artifacts/terraform-plan-1.png)
- ![terraform plan end](../artifacts/terraform-plan-9.png)

### terraform apply
- ![terraform apply start](../artifacts/terraform-apply-1.png)
- ![terraform apply end](../artifacts/terraform-apply-10.png)

### SSH connection to VM
- ![SSH connection](../artifacts/ssh.png)

## 3. Pulumi Implementation
- **Pulumi version and language used:** 
  - Pulumi v3.142.0
  - Language: Python 3.12
  - Provider: pulumi-yandex 0.13.0

- **How code differs from Terraform:**
  - Terraform uses declarative HCL and Pulumi uses imperative Python
  - Pulumi requires explicit virtual environment management
  - Resource arguments often need plural forms (`ingresses` vs `ingress`, `network_interfaces` vs `network_interface`)
  - Pulumi uses `pulumi.export()` for outputs instead of Terraform's `output` blocks
  - Configuration in Pulumi uses `pulumi.Config()` object; Terraform uses `variable` blocks
  - Pulumi stores state in Pulumi Cloud (optional) while Terraform uses local `.tfstate` files

- **Advantages you discovered:**
  - Full Python language features (loops, variables, etc.)
  - Better IDE support — autocomplete, type checking, and linting
  - Secrets encrypted by default in state files (no manual `.gitignore` needed for credentials)
  - Cleaner syntax for dynamic resource creation (e.g., generating multiple resources with `for` loops and generators)

- **Challenges encountered:**
  - `pkg_resources` missing in Python 3.12 — fixed by installing `setuptools` in venv
  - Configuration namespace issues — had to use `pulumi.Config()` without arguments to match stack config
  - Network quota limits — had to destroy Terraform VM first to free up VPC limit

### pulumi preview
- ![pulumi preview](../../pulumi/artifacts/pulumi-preview.png)

### pulumi up
- ![pulumi up](../../pulumi/artifacts/pulumi-up-1.png)

### SSH connection to VM
- ![pulumi up](../../pulumi/artifacts/pulumi-ssh.png)

## 4. Terraform vs Pulumi Comparison

- **Ease of Learning:** Terraform definetely is easier. HCL is purpose-built for infrastructure and has fewer edge cases. Pulumi requires Python knowledge

- **Code Readability:** Terraform is more readable for infrastructure-only tasks. HCL is declarative and self-documenting — you can look at a `.tf` file and immediately understand what resources will be created. Pulumi's Python code is clean but requires understanding imperative logic flow 

- **Debugging:** Terraform has clearer error messages. When something goes wrong, Terraform points directly to the issue (e.g., "file not found at path X"). Pulumi's error messages can be cryptic — for example, "Attribute must be a list" doesn't tell you which attribute or what value caused the problem, requiring trial and error to fix.

- **Documentation:** Terraform's documentation is more mature. The Terraform Registry has extensive examples for every resource, and community resources are abundant. Pulumi's documentation exists but sometimes shows outdated argument names (e.g., `family` instead of `source_family` in examples), causing frustration.

- **Use Case:** 
  - **Choose Terraform when:** You need pure infrastructure provisioning, your team doesn't have extensive programming background, or you want simplicity and battle-tested stability.
  - **Choose Pulumi when:** You need complex infrastructure logic (loops, conditionals, custom functions)

**Conclusion:** For this lab and typical DevOps infrastructure tasks, Terraform is the easier and more practical choice. Its declarative model, clearer error messages, and mature documentation make it more accessible

## 5. Lab 5 Preparation & Cleanup
- Are you keeping your VM for Lab 5? - Yes
- If yes, which VM? - Terraform
