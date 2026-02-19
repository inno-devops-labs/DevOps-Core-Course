# LAB04 — Infrastructure as Code (Terraform & Pulumi)

## 1. Cloud Provider & Infrastructure

- **Cloud provider:** AWS  
  **Rationale:** Widely used, strong Terraform/Pulumi support, free tier (t2.micro, 750 hrs/month for 12 months).
- **Instance type/size:** `t2.micro` (1 vCPU, 1 GiB RAM) — AWS free tier.
- **Region/zone:** `us-east-1` (default; change via `aws_region` / `aws:region`).
- **Estimated cost:** $0 within free tier (ensure no other paid resources).
- **Resources created:**
  - EC2 instance (Ubuntu 22.04 LTS)
  - Security group (SSH 22, HTTP 80, app 5000)
  - Key pair (from your SSH public key)
  - Public IP (assigned by default to the instance)

---

## 2. Terraform Implementation

- **Terraform version:** 1.9+
- **Project structure:**
  - `main.tf` — provider, data source (AMI), key pair, security group, EC2 instance
  - `variables.tf` — region, project name, instance type, SSH key path, allowed CIDR, tags
  - `outputs.tf` — public IP, instance ID, SSH command
  - `terraform.tfvars.example` — example variable values (copy to `terraform.tfvars`, gitignored)
- **Decisions:** Use default VPC; Ubuntu 22.04 AMI via data source; single security group for all rules.
- **Challenges:** (Document any you hit: e.g. AMI ownership, key path, region.)
- **Terminal output:** (Add your own sanitized output.)
  - `terraform init`
  - `terraform plan` (no secrets)
  - `terraform apply`
  - SSH connection (e.g. `ssh ubuntu@<public_ip>`)

---

## 3. Pulumi Implementation

- **Pulumi version:** 3.x | **Language:** Python
- **Differences from Terraform:** Same resources expressed in Python (imperative style); config via `pulumi config`; outputs via `pulumi.export()`.
- **Advantages:** Full Python (loops, conditionals, reuse); IDE support; encrypted secrets in Pulumi Cloud.
- **Challenges:** (Document any: e.g. SSH key path at startup, config vs Terraform variables.)
- **Terminal output:** (Add your own.)
  - `pulumi preview`
  - `pulumi up`
  - SSH connection to Pulumi-created VM

---

## 4. Terraform vs Pulumi Comparison

| Aspect        | Terraform                         | Pulumi                          |
|---------------|-----------------------------------|----------------------------------|
| **Ease of learning** | HCL is small and focused; good for simple infra. | Easier if you already know Python/TS. |
| **Readability** | Declarative; structure is clear.  | Code can be more compact; logic is explicit. |
| **Debugging**  | Plan/output and provider docs.   | Stack traces and IDE help.      |
| **Documentation** | Large community and registry.  | Good docs; smaller ecosystem.    |
| **Use case**   | Standard choice for multi-cloud IaC, teams. | Strong when you want code reuse and tests. |

**When to use Terraform:** Multi-cloud, team standardization, lots of examples and modules.  
**When to use Pulumi:** Prefer coding in Python/TS, need loops/functions or testing in the same language.

---

## 5. Lab 5 Preparation & Cleanup

**VM for Lab 5:**
- [ ] Keeping VM for Lab 5? (Yes / No)
- [ ] If yes: Which one? (Terraform / Pulumi)
- [ ] If no: Plan for Lab 5? (Local VM / Recreate cloud VM later)

**Cleanup status:**
- If keeping one VM: Note which tool created it and that the other stack has been destroyed.
- If destroying all: Run `terraform destroy` and `pulumi destroy`; add short terminal output (no secrets).
- Optional: Screenshot of cloud console showing no (or only intended) resources.

---

## 6. Bonus: IaC CI/CD

- **Workflow:** `.github/workflows/terraform-ci.yml` runs on changes to `terraform/**`.
- **Steps:** `terraform fmt -check`, `terraform init -backend=false`, `terraform validate`, `tflint --init` then `tflint`.
- **Path filters:** Only when `terraform/**` or the workflow file changes.
- A dummy SSH public key is created in CI so `file()` in Terraform does not fail during validate.
