# Lab 04 — Infrastructure as Code (Terraform & Pulumi)

## 1. Cloud Provider & Infrastructure

**Provider:** Yandex Cloud — free tier, accessible in Russia, native Terraform/Pulumi support.

**Instance:** standard-v2, 2 vCPU (20%), 1 GB RAM, 10 GB HDD, Ubuntu 24.04 LTS.

**Region:** ru-central1-a.

**Cost:** $0 (free tier grant).

**Resources created:**

| Resource | Name | Purpose |
|----------|------|---------|
| VPC Network | lab04-network | Isolated network |
| Subnet | lab04-subnet | 10.0.1.0/24 |
| Security Group | lab04-sg | SSH(22), HTTP(80), App(5000) |
| Compute Instance | lab04-vm | Main VM |

## 2. Terraform Implementation

**Version:** Terraform 1.5.7, Yandex Cloud provider v0.187.0.

**Project structure:**

```
terraform/
├── main.tf              # Provider + all resources
├── variables.tf         # Input variables with defaults
├── outputs.tf           # VM IP, SSH command, IDs
├── terraform.tfvars     # Actual secrets (gitignored)
├── terraform.tfvars.example
├── .tflint.hcl          # Linter config
├── .gitignore
└── README.md
```

**Key decisions:**
- Service account key auth instead of OAuth token — more reliable for automation
- Variables with empty defaults — allows CI validation without credentials
- SSH public key passed as variable content — CI-friendly
- All resources labeled with `project = "devops-lab04"`
- YC provider mirror (`terraform-mirror.yandexcloud.net`) — registry.terraform.io inaccessible from Russia

**Challenges:**
- `registry.terraform.io` not accessible — resolved with `~/.terraformrc` network mirror
- "Permission denied to resource-manager.folder" — billing account was not linked; resolved after linking
- Security group creation initially failed before billing activation

<details>
<summary>terraform init</summary>

```
Initializing the backend...
Initializing provider plugins...
- Finding latest version of yandex-cloud/yandex...
- Installing yandex-cloud/yandex v0.187.0 (unauthenticated)
Terraform has been successfully initialized!
```

</details>

<details>
<summary>terraform plan</summary>

```
Plan: 4 to add, 0 to change, 0 to destroy.

Changes to Outputs:
  + security_group_id = (known after apply)
  + ssh_command       = (known after apply)
  + subnet_id         = (known after apply)
  + vm_name           = "lab04-vm"
  + vm_public_ip      = (known after apply)
```

</details>

<details>
<summary>terraform apply</summary>

```
yandex_vpc_network.lab04: Creating...
yandex_vpc_network.lab04: Creation complete after 3s
yandex_vpc_subnet.lab04: Creating...
yandex_vpc_security_group.lab04: Creating...
yandex_vpc_subnet.lab04: Creation complete after 0s
yandex_vpc_security_group.lab04: Creation complete after 1s
yandex_compute_instance.lab04: Creating...
yandex_compute_instance.lab04: Creation complete after 40s

Apply complete! Resources: 4 added, 0 changed, 0 destroyed.

Outputs:
  security_group_id = "enp8ughv6u025h126jdu"
  ssh_command       = "ssh ubuntu@93.77.184.123"
  subnet_id         = "e9bj9tsdlk5l00cvbivl"
  vm_name           = "lab04-vm"
  vm_public_ip      = "93.77.184.123"
```

</details>

<details>
<summary>SSH connection proof</summary>

```
$ ssh ubuntu@93.77.184.123 "hostname && uname -a"
fhmvh5a6rb2v0hkooftk
Linux fhmvh5a6rb2v0hkooftk 6.8.0-100-generic #100-Ubuntu SMP PREEMPT_DYNAMIC Tue Jan 13 16:40:06 UTC 2026 x86_64 x86_64 x86_64 GNU/Linux
```

</details>

## 3. Pulumi Implementation

**Version:** Pulumi 3.220.0, Python 3.11, pulumi-yandex 0.13.0.

**How code differs from Terraform:**
- Python instead of HCL — real programming language with full IDE support
- Resources are Python objects with typed arguments
- Configuration via `pulumi config` instead of `.tfvars`
- Secrets encrypted by default with passphrase
- Outputs via `pulumi.export()` instead of `output` blocks
- Local backend with `pulumi login --local`

**Advantages discovered:**
- Autocomplete and type checking in IDE
- Familiar Python syntax
- Better error messages with Python stack traces
- Native loops, functions, conditionals

**Challenges:**
- `pulumi-yandex` 0.13.0 uses deprecated `pkg_resources` — resolved by pinning `setuptools<70`
- API differences: `ingresses`/`egresses` instead of `ingress`/`egress` (plural form)
- Pulumi installs its own venv — need to manage dependencies through `pulumi install`

<details>
<summary>terraform destroy (cleanup before Pulumi)</summary>

```
yandex_compute_instance.lab04: Destroying...
yandex_compute_instance.lab04: Destruction complete after 33s
yandex_vpc_subnet.lab04: Destroying...
yandex_vpc_security_group.lab04: Destroying...
yandex_vpc_security_group.lab04: Destruction complete after 1s
yandex_vpc_subnet.lab04: Destruction complete after 2s
yandex_vpc_network.lab04: Destroying...
yandex_vpc_network.lab04: Destruction complete after 1s

Destroy complete! Resources: 4 destroyed.
```

</details>

<details>
<summary>pulumi preview</summary>

```
Previewing update (dev):
  + pulumi:pulumi:Stack lab04-infra-dev create
  + yandex:index:VpcNetwork lab04-network create
  + yandex:index:VpcSubnet lab04-subnet create
  + yandex:index:VpcSecurityGroup lab04-sg create
  + yandex:index:ComputeInstance lab04-vm create

Resources:
    + 5 to create
```

</details>

<details>
<summary>pulumi up</summary>

```
Updating (dev):
  + yandex:index:VpcNetwork lab04-network created (2s)
  + yandex:index:VpcSubnet lab04-subnet created (0.37s)
  + yandex:index:VpcSecurityGroup lab04-sg created (1s)
  + yandex:index:ComputeInstance lab04-vm created (43s)
  + pulumi:pulumi:Stack lab04-infra-dev created (47s)

Outputs:
    ssh_command : "ssh ubuntu@89.169.134.171"
    vm_name     : "lab04-vm"
    vm_public_ip: "89.169.134.171"

Resources:
    + 5 created
Duration: 48s
```

</details>

<details>
<summary>SSH connection proof</summary>

```
$ ssh ubuntu@89.169.134.171 "hostname && uname -a"
fhmps7t0s3qa1rih6vot
Linux fhmps7t0s3qa1rih6vot 6.8.0-100-generic #100-Ubuntu SMP PREEMPT_DYNAMIC Tue Jan 13 16:40:06 UTC 2026 x86_64 x86_64 x86_64 GNU/Linux
```

</details>

## 4. Terraform vs Pulumi Comparison

**Ease of Learning:** Terraform is simpler to start with — HCL is concise and docs are extensive. Pulumi requires programming knowledge but feels more natural for developers.

**Code Readability:** HCL is more declarative and easy to scan. Python code is more verbose but benefits from IDE autocomplete and type checking.

**Debugging:** Pulumi has better error messages (Python tracebacks with line numbers). Terraform errors can be cryptic, especially with complex expressions.

**Documentation:** Terraform has a larger community and more examples. The `pulumi-yandex` package is poorly maintained (deprecated deps, sparse docs). Terraform YC provider is much more mature.

**Use Case:** Terraform for ops/SRE teams and simple infra. Pulumi when infra logic is complex or the team is developer-heavy. For Yandex Cloud specifically, Terraform is the clear winner due to provider maturity.

## 5. Lab 5 Preparation & Cleanup

**VM for Lab 5:** Yes, keeping Pulumi-created VM (`89.169.134.171`).

**Cleanup status:**
- Terraform resources: fully destroyed (`terraform destroy` — 4 resources)
- Pulumi VM: kept running for Lab 5
- Cloud console verified — only Pulumi resources remain

## Bonus: IaC CI/CD

**Workflow:** `.github/workflows/terraform-ci.yml`

Runs on PRs/pushes affecting `terraform/**`:
1. `terraform fmt -check` — formatting
2. `terraform init -backend=false` — provider download
3. `terraform validate` — syntax check
4. `tflint` — best practice linting

Path filters ensure workflow only triggers on Terraform changes.

## Bonus: GitHub Repository Import

**Purpose:** Managing existing resources with Terraform demonstrates brownfield IaC adoption — bringing manually created infrastructure under IaC management.

**Why importing matters:**
- **Version control:** All configuration changes tracked in Git
- **Code review:** PR-based review prevents unauthorized modifications
- **Prevents drift:** Terraform detects manual changes
- **Living documentation:** Code reflects actual infrastructure state
- **Disaster recovery:** Recreate infrastructure from code
- **Team collaboration:** No conflicting manual changes

**Real-world use case:** Organizations with 100s of manually created resources gradually import them into Terraform to gain full IaC benefits without disrupting existing services.

---

### Import Process

**1. Setup:**
```bash
cd terraform/github
terraform init
export GITHUB_TOKEN="your-personal-access-token"
export TF_VAR_github_owner="AEZuraa"
```

**2. Import existing repository:**
```bash
terraform import github_repository.course_repo DevOps-Core-Course
```

**Output:**
```
github_repository.course_repo: Importing from ID "DevOps-Core-Course"...
github_repository.course_repo: Import prepared!
  Prepared github_repository for import
github_repository.course_repo: Refreshing state... [id=DevOps-Core-Course]

Import successful!

Resources:
  1 imported
  0 added
  0 changed
  0 destroyed
```

**3. Check for drift:**
```bash
terraform plan
```

The first `terraform plan` after import showed **configuration drift** — differences between Terraform config and actual GitHub state:

- `has_issues`: config had `true`, reality was `false`
- `has_wiki`: config had `false`, reality was `true`  
- `has_projects`: config had `false`, reality was `true`
- Merge settings didn't match
- Description was much longer in reality

**4. Fix drift by updating config to match reality:**

Updated `main.tf` to reflect actual GitHub settings (description, has_issues, has_wiki, has_projects, merge settings).

**5. Verify no changes needed:**
```bash
terraform plan
```

Expected output:
```
No changes. Your infrastructure matches the configuration.
```

**Result:** Repository is now under Terraform management. Any future changes must go through code, enabling PR reviews, CI validation, and audit trails.

---

### Benefits Observed

**Before import:** Repository settings could be changed manually by anyone with access, no audit trail.

**After import:** All changes must be:
1. Written in code (`main.tf`)
2. Reviewed via PR
3. Validated by CI/CD
4. Applied through Terraform
5. Tracked in Git history

This prevents accidental misconfiguration and provides full visibility into infrastructure changes.
