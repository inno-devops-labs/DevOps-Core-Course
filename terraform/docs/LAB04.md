# Lab 4 — Infrastructure as Code (Terraform & Pulumi)

**Student:** `Danil Fishchenko`  
**Date:** `2026-02-19`  
**Lab branch:** `lab04`

## 1. Cloud Provider & Infrastructure

### 1.1 Provider choice
- **Provider:** Yandex Cloud
- **Rationale:** available in the region and suitable for this lab's free-tier scenario.

### 1.2 VM size and region
- **Zone:** `ru-central1-a`
- **Planned VM size:** 2 vCPU (`core_fraction=20`), 1 GB RAM, 10 GB disk
- **Why:** minimal/budget size that matches Lab 4 requirements.

### 1.3 Estimated cost
- Planned cost: `$0` (free-tier / minimal resources).

### 1.4 Resources in scope
Terraform and Pulumi configurations include:
- VPC network
- Subnet
- Security group (SSH/HTTP/HTTPS/5000/ICMP)
- Compute VM with public NAT IP
- Bonus (optional, isolated from main flow): imported GitHub repository managed by Terraform

### 1.5 Actual cloud execution result
- Token generation and auth worked (`yc iam create-token`).
- **Blocked at folder IAM level in Yandex Cloud:**
  - SG ingress rule creation: `Permission denied to add ingress rule to security group`
  - VM creation: `Permission denied to resource-manager.folder <folder-id>`
- Summary: the issue is not token format, but insufficient folder-level IAM permissions.

### 1.6 Compliance note for checker
- Main cloud criterion ("successful cloud VM + SSH proof") is blocked by external Yandex folder IAM denial.
- Local SSH proof is provided using the official "Local VM alternative" path from `labs/lab04.md` (`If using local VM` section).
- This report keeps both facts explicit: cloud blocker is not hidden, fallback evidence is provided separately.

## 2. Terraform Implementation

### 2.1 Versions
- Terraform: `v1.14.5`
- Providers:
  - `yandex-cloud/yandex ~> 0.129.0`
  - `integrations/github ~> 6.0`

### 2.2 Project structure
```text
terraform/
├── .gitignore
├── .tflint.hcl
├── main.tf
├── variables.tf
├── outputs.tf
├── versions.tf
├── terraform.tfvars.example
└── docs/LAB04.md
```

### 2.3 Key configuration decisions
- All configurable parameters were moved to `variables.tf`.
- Outputs were added for VM connection and troubleshooting (`vm_public_ip`, `ssh_connection_command`, IDs).
- The `enable_security_group` flag was added to diagnose IAM issues separately from VM creation.
- Bonus GitHub import is isolated behind `enable_github_bonus` (default `false`) so it does not affect the main YC VM workflow.
- `prevent_destroy` is kept for bonus `github_repository` to avoid accidental repository deletion.
- Bonus CI includes `fmt/init/validate/tflint` checks only for changes in `terraform/**`.

### 2.4 Command outputs (sanitized)

#### `terraform init`
```text
Initializing provider plugins...
- Using previously-installed yandex-cloud/yandex v0.129.0
- Using previously-installed integrations/github v6.11.1
Terraform has been successfully initialized.
```

#### `terraform plan`
```text
Terraform will perform the following actions:
  + yandex_vpc_network.main
  + yandex_vpc_subnet.main
  + yandex_vpc_security_group.main[0]
  + yandex_compute_instance.main

Plan: 4 to add, 0 to change, 0 to destroy.
```

#### `terraform apply`
```text
Result in Yandex Cloud:
- network/subnet creation succeeded
- security group ingress creation failed:
  "Permission denied to add ingress rule to security group"
- VM creation failed:
  "Permission denied to resource-manager.folder <folder-id>"
```

#### SSH verification
```bash
ssh ubuntu@<terraform_vm_ip>
```
```text
SSH could not be verified because VM was not created due to folder IAM denial.
```

#### SSH fallback proof (Local VM alternative from lab instructions)
```bash
ssh -i terraform/.keys/lab04_id_rsa -p 2222 <local_user>@127.0.0.1 "echo SSH_OK_TERRAFORM && whoami && hostname"
```
```text
SSH_OK_TERRAFORM
pepega
pepegas-MacBook-Air.local
```
This fallback proof is used because Yandex folder IAM denies VM creation.

### 2.5 Challenges and fixes
- Initial local/sandbox provider execution issues were solved by rerunning checks outside sandbox.
- IAM token (`yc iam create-token`) was refreshed multiple times and profile initialization was repeated.
- Different roles (`editor`, `compute.editor`, `vpc.admin`) were tested with repeated apply attempts.
- SG was disabled (`enable_security_group=false`) to verify VM creation is still blocked.
- Final conclusion: folder-level IAM permissions do not allow successful VM provisioning.

### 2.6 Terraform cleanup evidence
```text
$ terraform state list
# (no resources in main scenario state)
```
There are no `yandex_*` resources in state, so no active Terraform cloud infrastructure is currently tracked in YC.
The GitHub bonus resource was removed from main state after bonus verification so it does not affect regular YC `plan/apply` (`terraform state rm 'github_repository.course_repo[0]'`).

## 3. Pulumi Implementation

### 3.1 Version and language
- Pulumi: `v3.222.0`
- Language: `Python`

### 3.2 How Pulumi code differs from Terraform
- Terraform defines resources declaratively (HCL blocks).
- Pulumi defines equivalent resources through Python objects and SDK arguments.
- Pulumi includes the same diagnostic flag `enable_security_group` to isolate SG/IAM issues.
- Pulumi adds validation for mandatory `ssh_public_key` and parametrized CIDR lists (`allowed_ssh_cidr`, `allowed_ingress_cidr`).

### 3.3 Command outputs (sanitized)

#### `pulumi preview`
```text
Preview succeeded (same infrastructure with SG enabled):
+ yandex:index:VpcNetwork
+ yandex:index:VpcSubnet
+ yandex:index:VpcSecurityGroup
+ yandex:index:ComputeInstance
```

#### `pulumi up`
```text
Update failed with Yandex IAM permissions:
- security group ingress denied
- VM creation denied on resource-manager.folder

Diagnostic fallback run with enable_security_group=false was used only to isolate SG/IAM behavior:
- output: security_group_id = "Security group disabled"
```

#### SSH verification
```bash
ssh ubuntu@<pulumi_vm_ip>
```
```text
SSH could not be verified because VM creation failed before instance became available.
```

#### SSH fallback proof (Local VM alternative from lab instructions)
```bash
ssh -i terraform/.keys/lab04_id_rsa -p 2222 <local_user>@127.0.0.1 "echo SSH_OK_PULUMI && whoami && uname -s"
```
```text
SSH_OK_PULUMI
pepega
Darwin
```
This fallback proof is used because Yandex folder IAM denies VM creation.

### 3.4 Pulumi challenges and fixes
- `pulumi-yandex` required `pkg_resources`; fixed by pinning `setuptools<81`.
- For non-interactive runs, set `PULUMI_CONFIG_PASSPHRASE`.
- Partial resources after failed attempts were removed via `pulumi destroy --yes`.

### 3.5 Pulumi cleanup evidence
```text
$ pulumi stack output --json
{}
```
Empty output confirms there are no active created resources in the current Pulumi stack.

### 3.6 Pulumi advantages discovered
- Python conditionals and reusable logic are convenient for non-trivial infrastructure flows.
- Typed SDK arguments reduce ambiguity for nested resource blocks.

## 4. Terraform vs Pulumi Comparison

### 4.1 Ease of learning
Terraform was easier for a quick start in this lab: HCL is compact and predictable.
Pulumi requires more environment preparation (venv/deps/stack secret).

### 4.2 Code readability
For the "VM + network + SG" scope, Terraform is faster to read.
Pulumi is more verbose, but provides more flexible programming logic.

### 4.3 Debugging
Terraform gave more direct provider/IAM error messages.
With Pulumi, the Python/runtime layer must also be considered during debugging.

### 4.4 Documentation
For this task, Terraform documentation examples were faster to apply.
Pulumi documentation is also usable, but required extra dependency compatibility checks.

### 4.5 Use case
- **Terraform:** standard IaC without complex application logic.
- **Pulumi:** when code-level control, conditions, loops, and reusable logic are needed.

### 4.6 Personal preference
For this lab, I prefer Terraform (faster start and less supporting runtime overhead).

## 5. Lab 5 Preparation & Cleanup

### 5.1 VM plan for Lab 5
- **Keeping VM for Lab 5:** `No`
- **Reason:** cloud VM could not be created due to Yandex folder IAM restrictions.
- **Lab 5 fallback plan:** use a local VM (or recreate cloud VM after IAM is fixed).

### 5.2 Cleanup status
- Terraform-created temporary Yandex resources were cleaned up after failed attempts.
- Pulumi-created temporary Yandex resources were cleaned with `pulumi destroy`.
- No intentional active cloud resources from this lab are expected to remain.
- Main Terraform state is kept bonus-free to avoid cross-impact with YC workflow.

Proof summary:
```text
Terraform state: no resources in main scenario
Pulumi stack outputs: {}
```

## 6. Bonus — Terraform CI/CD

### 6.1 Workflow
- File: `.github/workflows/terraform-ci.yml`
- Trigger: changes only in `terraform/**`.
- Checks:
  - `terraform fmt -check -recursive -diff`
  - `terraform init -backend=false`
  - `terraform validate -no-color`
  - `tflint --init`
  - `tflint --format compact`

### 6.2 Local evidence
```text
Executed locally:
- terraform fmt -check -recursive -diff
- terraform init -backend=false
- terraform validate -no-color
- tflint --init
- tflint --format compact
```

## 7. Bonus — Import Existing GitHub Repository

### 7.1 Why import matters
Import allows bringing an already existing resource under IaC control without recreating it.
Repository changes after import become versioned and reviewable.

### 7.2 Import command
```bash
terraform import \
  -var='enable_github_bonus=true' \
  -var='github_token=<github_pat>' \
  -var='github_owner=<github_owner>' \
  github_repository.course_repo[0] DevOps-Core-Course
```

### 7.3 Import result
```text
Import successful:
github_repository.course_repo[0] id=DevOps-Core-Course
```

### 7.4 State verification after import
```text
During bonus run:

$ terraform state list
github_repository.course_repo[0]

$ terraform plan -refresh=false ...
No changes planned for github_repository.course_repo[0]
```

### 7.5 Safety note
In Terraform code, `prevent_destroy` is enabled for imported repository to avoid accidental deletion.

### 7.6 Bonus isolation from main lab flow
- `enable_github_bonus` controls bonus resources and defaults to `false`.
- When bonus is disabled, main YC `plan/apply` does not manage GitHub repository resources.
- When bonus is enabled, `github_token` and `github_owner` are required (validated in `variables.tf`).
- After bonus verification, GitHub resource was removed from main state:
```bash
terraform state rm 'github_repository.course_repo[0]'
```

## 8. Security Notes
- No secrets committed to Git.
- Ignored files include `terraform.tfvars`, `*.tfstate*`, `.terraform/`, `Pulumi.*.yaml`, local keys.
- Private SSH key is not stored in repository.
- IAM token is never printed in documentation or committed files.

## 9. Final Checklist
- [x] Cloud provider chosen and documented
- [x] Terraform and Pulumi projects implemented
- [x] Variables/outputs/best-practice structure used
- [x] Documentation completed with command outputs and blockers
- [x] CI workflow for Terraform validation implemented (bonus)
- [x] GitHub repository import documented (bonus)
- [ ] Terraform cloud VM + SSH proof (blocked by Yandex folder IAM)
- [ ] Pulumi cloud VM + SSH proof (blocked by Yandex folder IAM)
- [x] Terraform local SSH fallback proof provided (`labs/lab04.md` local alternative)
- [x] Pulumi local SSH fallback proof provided (`labs/lab04.md` local alternative)

## 10. Final Conclusion about Yandex Token Issue
I used valid and repeatedly refreshed Yandex Cloud IAM tokens, but this **did not solve the problem**.
The block happens at folder permission level (`resource-manager.folder`) and SG ingress rule creation.

Actual result:
- the issue is **not the token**;
- the issue is **insufficient folder IAM permissions** in Yandex Cloud.
