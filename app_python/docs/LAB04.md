# LAB04 — Infrastructure as Code (Terraform & Pulumi)

## 1. Cloud Provider & Infrastructure

**Provider:** Yandex Cloud
**Why:** accessible in Russia, has a free tier (1 VM with 20% vCPU, 1 GB RAM), good Terraform provider.

**Instance:** standard-v2, 2 cores at 20% (`core_fraction = 20`), 1 GB RAM — free tier eligible.
**Zone:** `ru-central1-a`.
**OS:** Ubuntu 24.04 LTS (family `ubuntu-2404-lts`).
**Total cost:** $0 (free tier).

**Resources created:**

| Resource | Type | Notes |
|----------|------|-------|
| VPC Network | `data.yandex_vpc_network` | Reused existing "default" network (cloud quota limit) |
| Subnet | `yandex_vpc_subnet` — 10.0.1.0/24, ru-central1-a | Created |
| Security Group | `yandex_vpc_security_group` — SSH (22), HTTP (80), App (5000) | Created |
| Compute Instance | `yandex_compute_instance` — standard-v2, 2 cores @ 20%, 1 GB, 10 GB HDD | Created |

## 2. Terraform Implementation

**Terraform version:** 1.14.5 (`windows_amd64`)
**Yandex Cloud provider version:** 0.187.0

**Project structure:**

```
terraform/
├── main.tf          # Provider, data sources, all resources
├── variables.tf     # Input variables with defaults
├── outputs.tf       # Public IP, instance ID, SSH command
├── tflint.hcl       # TFLint configuration
└── .gitignore       # State files, credentials, .terraform/
```

**Key decisions:**

- Used `data "yandex_compute_image"` with `family = "ubuntu-2404-lts"` to always get the latest Ubuntu 24.04 image.
- SSH key is injected via `metadata.ssh-keys` field as required by Yandex Cloud, using `file(pathexpand(...))` to expand the `~` in the path.
- Public IP is obtained via `nat = true` on the network interface.
- Sensitive values (token, cloud_id, folder_id) are kept in `terraform.tfvars` (gitignored).

**Challenges:**

- The cloud-level `vpc.networks.count` quota was exhausted. Fixed by reusing the existing "default" network via a data source instead of creating a new one.
- Terraform's `file()` function does not expand `~`. Had to wrap with `pathexpand()`: `file(pathexpand(var.ssh_public_key_path))`.


### Terminal output

![Terraform init](screenshots/terraform-apply.png)

### VM is accessible via SSH:

![Terraform SSH](screenshots/terraform-ssh.png)

### terraform destroy (before switching to Pulumi):

![Terraform Destroy](screenshots/terraform-destroy.png)

## 3. Pulumi Implementation

**Pulumi version:** 3.221.0
**Language:** Python 3.13

**Project structure:**

```
pulumi/
├── __main__.py       # All infrastructure in Python
├── Pulumi.yaml       # Project metadata
├── requirements.txt  # pulumi, pulumi-yandex
└── .gitignore        # venv/, stack configs with secrets
```

**How code differs from Terraform:**

- Resources are Python objects — `yandex.ComputeInstance(...)` instead of `resource "yandex_compute_instance" "vm" { ... }`.
- Existing network is looked up with `yandex.get_vpc_network(name=...)` instead of `data "yandex_vpc_network"` block.
- No separate `variables.tf` — config values are read with `pulumi.Config()` or are just Python variables.
- Outputs use `pulumi.export()` instead of `output` blocks.
- The SSH public key is read with native Python `open()` / `os.path.expanduser()`.
- Full Python language is available for loops, conditionals, string formatting.

**Advantages discovered:**

- IDE autocomplete for resource properties was helpful.
- Reading the SSH key and building metadata felt natural in Python.
- Error messages with Python tracebacks were easier to understand.

**Challenges:**

- The `pulumi-yandex` package (v0.13.0) is community-maintained and uses the deprecated `pkg_resources` module. With Python 3.14, `setuptools` removed `pkg_resources` entirely. Fixed by downgrading to Python 3.13 and pinning `setuptools<78`.

### Terminal output

### Pulumi up:

![Pulumi Up](screenshots/pulumi-up.png)

###SSH access proof:

![Pulumi SSH](screenshots/pulumi-ssh.png)

## 4. Terraform vs Pulumi Comparison

**Ease of Learning:** Terraform was easier to pick up. HCL is simple and the Yandex Cloud docs have copy-paste examples. Pulumi needed knowledge of both the cloud API and the Python SDK.

**Code Readability:** Terraform is cleaner for small configs — one block per resource. Pulumi works fine too but needs more imports and setup code.

**Debugging:** Pulumi was easier to fix when things broke — Python errors are clear and IDE shows mistakes early. Terraform errors can be hard to read.

**Documentation:** Terraform has more docs and examples for Yandex Cloud. Pulumi's Yandex provider is community-made, so less help is available online.

**Use Case:** Terraform fits simple setups and mixed-skill teams. Pulumi is better when you need loops, conditions, or reusable code.

## 5. Lab 5 Preparation & Cleanup

**Keeping VM for Lab 5:** Yes — keeping the Pulumi-created VM.
The Terraform resources were destroyed with `terraform destroy` before creating equivalent infrastructure with Pulumi.

**Cleanup status:**

- Terraform: all resources destroyed (`terraform destroy` completed successfully).
- Pulumi: VM is running and accessible via SSH.
- No secrets committed to Git; `.gitignore` covers state files, `terraform.tfvars`, and service account keys.

## Bonus — IaC CI/CD

### Workflow file

Located at `.github/workflows/terraform-ci.yml`.
Triggers on `pull_request` when files in `terraform/**` change.

**Steps:**
1. Checkout code
2. Setup Terraform 1.9.x
3. `terraform fmt -check -recursive` — formatting validation
4. `terraform init -backend=false` — initialize without backend
5. `terraform validate` — syntax validation
6. Setup TFLint + init plugins
7. `tflint --format compact` — linting for best practices

**Path filter config:** the workflow only runs when `terraform/**` or the workflow file itself changes, avoiding unnecessary runs for Python/Go changes.

**tflint config** (`terraform/tflint.hcl`): enables the Terraform recommended preset. No Yandex-specific tflint plugin exists, so only generic Terraform rules are checked.

### Workflow evidence

![CI Workflow](screenshots/bonus-1.png)

## Bonus — GitHub Repository Import

### Import process

1. Created `terraform-github/` with GitHub provider (`integrations/github ~> 6.0`) and a `github_repository` resource.
2. Generated a GitHub Personal Access Token (classic) with `repo` scope.
3. Ran `terraform init` to install the GitHub provider.
4. Imported the existing repo:

```bash
cd terraform-github
export GITHUB_TOKEN="ghp_..."
terraform init
terraform import github_repository.course_repo DevOps-Core-Course
```

5. Ran `terraform plan` — it showed drift (description, wiki, issues, merge settings differed).
6. Updated the resource config to match reality (actual description, `has_wiki = true`, `has_issues = false`, etc.).
7. Final `terraform plan` showed no changes — state matches the actual repo.

![GitHub Import](screenshots/bonus-2.png)

### Why importing matters

Importing lets you bring manually created resources under IaC management. Benefits:

- **Version control:** all config changes are tracked in Git.
- **Consistency:** prevents configuration drift between what you think exists and what actually exists.
- **Automation:** future changes go through code review and CI validation.
- **Disaster recovery:** you can recreate resources from code if something breaks.
- **Team collaboration:** everyone sees the current state in code, no tribal knowledge required.
