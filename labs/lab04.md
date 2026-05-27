# Lab 4 — Infrastructure as Code (Terraform & Pulumi)

![difficulty](https://img.shields.io/badge/difficulty-beginner-success)
![topic](https://img.shields.io/badge/topic-Infrastructure%20as%20Code-blue)
![points](https://img.shields.io/badge/points-10%2B2-orange)
![tech](https://img.shields.io/badge/tech-Terraform%20%7C%20Pulumi-informational)

> Provision the **same** cloud VM twice — once with Terraform, once with Pulumi — and feel the trade-offs first hand.

## Overview

Infrastructure as Code (IaC) means your cloud lives in Git, not in someone's browser tabs. In this lab you build one small VM with **Terraform** (declarative HCL) and then rebuild the identical thing with **Pulumi** (a real programming language). Doing both is the point: you learn the workflow, the failure modes, and how to pick a tool.

**What you'll learn:**
- The `init → plan → apply → destroy` lifecycle
- Writing providers, resources, variables, and outputs
- **State management** — local vs remote, why locking matters (this is where people fail)
- The same infrastructure expressed declaratively (Terraform) and imperatively (Pulumi)
- Keeping credentials and state out of Git

**Connection to other labs:**
- **Lab 2/3:** you built and CI'd an app — now you provision a host for it
- **Lab 5 (Ansible):** will SSH into the VM you create here, so **keep one VM running**

**Tech Stack:** Terraform **1.15.3** (or OpenTofu **1.12**, a drop-in replacement) · Pulumi **3.243** · AWS provider v5.x / GCP provider v6.x / Yandex provider v0.115+

> **OpenTofu note:** OpenTofu is the MPL-2.0, Linux-Foundation fork of Terraform created after HashiCorp moved Terraform to the Business Source License on **August 10, 2023**. The HCL and providers are identical — you may run `tofu` instead of `terraform` for every command in this lab. The grader accepts either.

---

## Cloud Provider Selection

Pick **one** provider and stick with it for both tools. Use the smallest free-tier instance.

| Provider | Free tier (smallest) | Provider plugin | Notes |
|----------|----------------------|-----------------|-------|
| **Yandex Cloud** | 2 vCPU @ 20%, 1 GB RAM, 10 GB | `yandex-cloud/yandex` | Recommended in Russia; no card initially |
| **AWS** | `t3.micro`, 750 h/mo for 12 mo | `hashicorp/aws` (v5.x) | Most documented globally |
| **GCP** | `e2-micro`, always-free zones | `hashicorp/google` (v6.x) | `$300` credit for 90 days |
| **Azure** | `B1s` | `hashicorp/azurerm` | `$200` credit, 30 days |
| **VK Cloud** | trial credits | OpenStack provider | Russian, OpenStack-based |
| **DigitalOcean** | `$200` w/ Student Pack | `digitalocean/digitalocean` | Simple, beginner-friendly |

### Cost & safety — read this
- Use **free-tier / smallest** instances only.
- Run `destroy` when you finish testing; keep **one** VM for Lab 5.
- Set a billing alert if your provider offers one.
- **Never commit credentials or state files to Git.**

---

## Tasks

### Task 1 — Terraform VM (4 pts)

**Goal:** Provision a reachable VM with Terraform, manage its state correctly.

Create a `terraform/` directory with this layout (single-file `main.tf` is acceptable, but split is cleaner):

```
terraform/
├── main.tf          # provider + resources
├── variables.tf     # inputs
├── outputs.tf       # public IP, ssh command
├── terraform.tfvars # values — GITIGNORED
├── .gitignore
└── README.md
```

**Required resources** (names vary by provider — see the guides below):
- **Compute instance** — smallest free-tier size, Ubuntu image found via a **data source** (not a hardcoded ID)
- **Network / VPC + subnet** if your provider needs one
- **Security group / firewall** allowing: SSH **22 from your IP only**, HTTP **80**, app port **5000**
- **Public IP** so you can SSH in
- **SSH key** wired into the instance (e.g. AWS `key_pair`, Yandex/GCP `metadata` `ssh-keys`)

**You must:**
1. Use **variables** for region/zone, instance type, and your SSH public key — no magic strings.
2. Use **outputs** for the public IP and a ready-to-paste `ssh` command.
3. Run the full lifecycle: `terraform fmt` → `validate` → `plan` → `apply`, then **SSH in to prove it works**.
4. Keep `terraform.tfstate` **local for now**, and **never commit it**. Understand what it contains (see State Management below).

#### Skeleton (AWS — adapt for your provider)

Fill every `YOUR-TASK` marker. Do **not** copy a complete solution from elsewhere; the point is that you write the HCL.

```hcl
# main.tf
terraform {
  required_version = ">= 1.15.0"           # OpenTofu 1.12 also satisfies this
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.region
  # ✅ credentials come from env vars / shared profile — NEVER inline here
}

# Find the latest Ubuntu image dynamically (data source, not a hardcoded AMI)
data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"] # Canonical
  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd-gp3/ubuntu-noble-24.04-amd64-server-*"]
  }
}

resource "aws_security_group" "lab" {
  name        = "lab4-sg"
  description = "SSH from my IP, HTTP, app port"
  # YOUR-TASK: ingress 22 from var.my_ip/32 only, 80 and 5000 as needed,
  #            egress all. Document why each port is open.
}

resource "aws_key_pair" "lab" {
  key_name   = "lab4-key"
  public_key = var.ssh_public_key
}

resource "aws_instance" "web" {
  ami           = data.aws_ami.ubuntu.id
  instance_type = var.instance_type        # free tier, e.g. t3.micro
  key_name      = aws_key_pair.lab.key_name
  # YOUR-TASK: attach the security group; add tags { Name, Env="lab4" }
}
```

```hcl
# variables.tf
variable "region"         { type = string  default = "eu-central-1" }
variable "instance_type"  { type = string  default = "t3.micro" }
variable "my_ip"          { type = string  description = "Your public IP for SSH (curl ifconfig.me)" }
variable "ssh_public_key" { type = string  description = "Contents of ~/.ssh/id_ed25519.pub" }
```

```hcl
# outputs.tf
output "public_ip" {
  value = aws_instance.web.public_ip
}
output "ssh_command" {
  value = "ssh ubuntu@${aws_instance.web.public_ip}"
}
```

```gitignore
# terraform/.gitignore
*.tfstate
*.tfstate.*
.terraform/
.terraform.lock.hcl
*.tfvars
*.pem
*.key
```

> The `.terraform.lock.hcl` is normally **committed** to pin provider versions. This lab gitignores it only to keep submissions clean — in real projects, commit it.

#### Lifecycle commands (Terraform 1.15 / OpenTofu 1.12)

```bash
terraform init       # download providers into .terraform/
terraform fmt        # canonical formatting
terraform validate   # syntax + internal consistency (no cloud calls)
terraform plan        # diff: code vs state vs reality — READ IT
terraform apply       # make reality match code
# ... ssh in, verify ...
terraform destroy    # tear down (skip if keeping VM for Lab 5)
```

> Read the `plan` every single time. `+` create, `~` update in place, `-` destroy, `-/+` replace (data-loss risk).

<details>
<summary>☁️ Provider quick-reference (Yandex / GCP)</summary>

**Yandex Cloud** — source `yandex-cloud/yandex`. Auth: service account → authorized key (JSON), set via env or `service_account_key_file`. Resources: `yandex_compute_instance`, `yandex_vpc_network`, `yandex_vpc_subnet`, `yandex_vpc_security_group`. Free tier: `standard-v3`, `core_fraction = 20`, 1 GB RAM, 10 GB disk. SSH via `metadata = { ssh-keys = "ubuntu:${var.ssh_public_key}" }`.
[Provider docs](https://registry.terraform.io/providers/yandex-cloud/yandex/latest/docs)

**GCP** — source `hashicorp/google` (`~> 6.0`). Auth: `gcloud auth application-default login` or `GOOGLE_APPLICATION_CREDENTIALS`. Enable Compute Engine API. Resources: `google_compute_instance`, `google_compute_network`, `google_compute_subnetwork`, `google_compute_firewall`. Free tier: `e2-micro` in a free zone (e.g. `us-central1-a`). SSH via `metadata = { ssh-keys = "ubuntu:${var.ssh_public_key}" }`.
[Provider docs](https://registry.terraform.io/providers/hashicorp/google/latest/docs)

</details>

<details>
<summary>🔐 Credentials — the rules that keep you out of the headlines</summary>

1. **Never put keys in `.tf`, `.tfvars`, or a `provider {}` block.** Let the provider read environment variables or your shared profile:

```bash
# AWS
export AWS_ACCESS_KEY_ID="…" AWS_SECRET_ACCESS_KEY="…"
# or `aws configure` → ~/.aws/credentials, then provider "aws" { region = var.region }
```

```hcl
# ❌ NEVER do this — Code Spaces (2014) was shut down in 12 hours for exactly this
provider "aws" {
  access_key = "AKIA…"
  secret_key = "wJalr…"
}
```

2. **Never commit `*.tfstate` or `*.tfstate.backup`** — they hold decrypted secrets.
3. **Restrict SSH to your IP** (`var.my_ip/32`), not `0.0.0.0/0`. Open only the ports you use.
4. **Generate an SSH keypair locally** (`ssh-keygen -t ed25519`), push only the `.pub`, `chmod 600` the private key, never commit it.
5. **For CI, prefer OIDC over long-lived keys** (covered in the bonus / DevSecOps elective).

</details>

**Document in `docs/LAB04.md`:** provider chosen + why, Terraform/OpenTofu version, resources created, public IP, SSH command, and **sanitized** terminal output of `plan`, `apply`, and the SSH session.

---

### State Management (read before you `apply`)

This is where students and pros both lose hours.

**What the state file is:** a JSON map from your code (`aws_instance.web`) to a real cloud object (`i-0abc123…`). Without it, Terraform has no idea what already exists. It also contains **secrets** — IPs, generated passwords, sometimes keys.

**Rules:**
1. **Never commit `terraform.tfstate` / `*.tfstate.backup`.** They hold decrypted secrets and JSON merge conflicts are unrecoverable. `.gitignore` on day one.
2. **Never hand-edit state.** Use `terraform state mv|rm|list` and `terraform import`.
3. **In any team, use a remote, locked, encrypted backend** — not local disk. Local state means two engineers applying at once corrupt it, and a dead laptop orphans your cloud.

**Local vs remote — the trade-off:**

| | Local (`*.tfstate` on disk) | Remote (S3 / GCS / TF Cloud) |
|-|------------------------------|------------------------------|
| Solo prototyping | ✅ fine | overkill |
| Team of 2+ | ❌ race → corruption | ✅ locking serializes applies |
| Laptop dies | ❌ state lost, cloud orphaned | ✅ versioned object storage |
| Secrets at rest | 🟡 plaintext on disk | ✅ encrypted (KMS) |

**Remote backend example (illustrative — used in the bonus):**

```hcl
terraform {
  backend "s3" {
    bucket       = "your-tf-state-bucket"
    key          = "lab4/terraform.tfstate"
    region       = "eu-central-1"
    encrypt      = true        # 🔐 SSE
    use_lockfile = true        # 🔒 native S3 state locking (TF 1.10+)
  }
}
```

> This lab **starts with local state on purpose** so the failure mode is visible. The bonus migrates to a remote, locked backend.

**Adopting things you didn't create with Terraform** — in the real world you inherit resources that already exist. Rather than recreate them, you `import` them into state:

```bash
# Imperative form — adopt an existing instance into state
terraform import aws_instance.web i-0abc123def456

# Or, Terraform 1.5+ / OpenTofu — declarative import that runs on the next apply
import {
  to = aws_instance.web
  id = "i-0abc123def456"
}
```

After import, run `terraform plan`; a non-empty diff means your HCL doesn't yet match reality. Edit the config until `plan` reports **no changes** — only then is the resource truly managed by code. You don't need to import anything for this lab, but knowing the workflow is half the value of IaC.

---

### Task 2 — Pulumi VM (4 pts)

**Goal:** Recreate the **same** infrastructure with Pulumi, then compare the experience.

1. **Destroy the Terraform VM first** (`terraform destroy`) so you don't run two VMs. Keep the proof. *(If you'd rather keep the Terraform VM for Lab 5, build the Pulumi version, screenshot it working, then `pulumi destroy` instead — just don't leave two VMs running undocumented.)*
2. **Set up Pulumi:** install the CLI, `pulumi new <lang>` (Python recommended; TypeScript/Go/C#/Java also fine), pick a state backend (Pulumi Cloud free tier, or `pulumi login --local` / S3).
3. **Recreate** the VM, network, firewall/security-group (same rules), public IP — functionally identical to Task 1.
4. Run `pulumi preview` → `pulumi up`, **SSH in to prove it works**, then compare.

```
pulumi/
├── __main__.py       # infrastructure code
├── requirements.txt  # e.g. pulumi>=3.243, pulumi-aws (or -gcp / -yandex)
├── Pulumi.yaml       # project metadata
├── Pulumi.dev.yaml   # stack config — GITIGNORE if it holds secrets
└── .gitignore        # venv/, Pulumi.*.yaml with secrets
```

#### Skeleton (Pulumi Python, AWS — adapt for your provider)

```python
# __main__.py — same VM as Task 1, in Python
import pulumi
import pulumi_aws as aws

config = pulumi.Config()
my_ip = config.require("myIp")              # set: pulumi config set myIp x.x.x.x
ssh_pub = config.require("sshPublicKey")

ubuntu = aws.ec2.get_ami(
    most_recent=True,
    owners=["099720109477"],
    filters=[{"name": "name",
              "values": ["ubuntu/images/hvm-ssd-gp3/ubuntu-noble-24.04-amd64-server-*"]}],
)

sg = aws.ec2.SecurityGroup("lab4-sg",
    description="SSH from my IP, HTTP, app port",
    # YOUR-TASK: ingress 22 from f"{my_ip}/32", 80, 5000; egress all
)

key = aws.ec2.KeyPair("lab4-key", public_key=ssh_pub)

web = aws.ec2.Instance("web",
    ami=ubuntu.id,
    instance_type="t3.micro",
    key_name=key.key_name,
    # YOUR-TASK: attach sg via vpc_security_group_ids; tags={"Name": "lab4-web"}
)

pulumi.export("public_ip", web.public_ip)
pulumi.export("ssh_command", web.public_ip.apply(lambda ip: f"ssh ubuntu@{ip}"))
```

```bash
pulumi config set aws:region eu-central-1
pulumi config set myIp $(curl -s ifconfig.me)
pulumi config set sshPublicKey "$(cat ~/.ssh/id_ed25519.pub)"

pulumi preview     # like terraform plan
pulumi up          # create / update
# ... ssh in, verify ...
pulumi destroy     # tear down
```

> **State in Pulumi:** stored in your chosen backend (Pulumi Cloud / S3 / local) and **secrets are encrypted by default** — a notable difference from Terraform's plaintext-on-disk local state.

<details>
<summary>📦 Terraform → Pulumi cheatsheet</summary>

| Concept | Terraform | Pulumi (Python) |
|---------|-----------|-----------------|
| Resource | `resource "aws_instance" "web" { ... }` | `web = aws.ec2.Instance("web", ...)` |
| Input | `var.instance_type` | `config.require("instanceType")` |
| Output | `output "ip" { value = ... }` | `pulumi.export("ip", web.public_ip)` |
| Data lookup | `data "aws_ami" "x" {}` | `aws.ec2.get_ami(...)` |
| Plan / apply | `plan` / `apply` | `preview` / `up` |
| Loops | `for_each`, `count` | native `for` loops |

Provider packages: `pip install pulumi-aws` (or `pulumi-gcp`, `pulumi-yandex`). [Pulumi registry](https://www.pulumi.com/registry/).

</details>

**Document in `docs/LAB04.md`:** language chosen, `terraform destroy` proof, `pulumi preview`/`up` output, public IP, SSH proof, and the comparison below.

---

### Task 3 — Documentation (2 pts)

Create `docs/LAB04.md` (or `terraform/docs/LAB04.md`) with these sections:

1. **Cloud & infrastructure** — provider + rationale, instance size, region/zone, resources created, cost (should be `$0`).
2. **Terraform implementation** — version, structure, key decisions, challenges, sanitized output of `init` / `plan` / `apply` / SSH.
3. **Pulumi implementation** — version + language, how the code differs, advantages found, sanitized output of `preview` / `up` / SSH.
4. **Terraform vs Pulumi** — 3–5 sentences each on: ease of learning, readability, debugging, docs quality, and *when you'd pick each*.
5. **Lab 5 prep & cleanup** — which VM (if any) you're keeping, or exactly how you'll recreate one from your IaC; plus `destroy` proof for whatever you tore down.

> All terminal output must be **sanitized** (no keys, no full account IDs). Mark any reconstructed examples as illustrative.

---

## Bonus Task — IaC CI/CD + Remote State (2 pts)

**Goal:** Validate IaC automatically on PRs and move Terraform state to a remote, locked backend.

### Part 1 — GitHub Actions validation (1 pt)

Create `.github/workflows/terraform-ci.yml` that, on changes under `terraform/**`, runs `fmt -check`, `init -backend=false`, `validate`, and a linter (`tflint`). Use **first-party / official** actions only — `hashicorp/setup-terraform` (or `opentofu/setup-opentofu`) and `terraform-linters/setup-tflint`. No long-lived cloud credentials needed for validate.

```yaml
# .github/workflows/terraform-ci.yml
name: terraform-ci
on:
  pull_request:
    paths:
      - 'terraform/**'
      - '.github/workflows/terraform-ci.yml'

jobs:
  validate:
    runs-on: ubuntu-24.04
    defaults:
      run: { working-directory: terraform }
    steps:
      - uses: actions/checkout@v4
      - uses: hashicorp/setup-terraform@v3
        with:
          terraform_version: "1.15.3"   # or use opentofu/setup-opentofu
      - run: terraform fmt -check -recursive
      - run: terraform init -backend=false
      - run: terraform validate
      # YOUR-TASK: add a tflint step (terraform-linters/setup-tflint@v4 + `tflint`)
```

A minimal `terraform/.tflint.hcl`:

```hcl
plugin "terraform" { enabled = true }
plugin "aws"       { enabled = true, version = "0.40.0", source = "github.com/terraform-linters/tflint-ruleset-aws" }
```

**Prove it:** open a PR touching `terraform/`, show the workflow runs (and that it stays green on a clean diff / red on a `fmt` violation), and confirm it does **not** trigger on unrelated changes.

### Part 2 — Migrate to remote, locked state (1 pt)

Take your Task 1 Terraform and move state off your laptop:

1. Create a state bucket (S3 with versioning + encryption, or GCS with versioning).
2. Add the `backend "s3"` (or `"gcs"`) block with **encryption and locking** (the S3 example uses `use_lockfile = true`; GCS locks natively).
3. Run `terraform init -migrate-state` and confirm the local state moved.
4. Show that a second `plan` reports **no changes** (state matched correctly) and explain, in `docs/LAB04.md`, why locking prevents two simultaneous applies from corrupting state.

> The bucket itself can be created by hand or by a tiny separate Terraform config — either is fine, just document which.

<details>
<summary>💡 Why remote state + locking matters</summary>

Local state breaks the moment a second person (or CI runner) touches it: concurrent `apply`s race and corrupt the JSON, and a lost laptop orphans every resource it tracked. A remote backend gives you a single canonical state, encryption at rest, version history for recovery, and a **lock** that serializes applies so only one runs at a time. This is the single most important operational habit in IaC — get it right early.

[Terraform backends](https://developer.hashicorp.com/terraform/language/settings/backends/s3) · [State locking](https://developer.hashicorp.com/terraform/language/state/locking)

</details>

---

## How to Submit

1. **Branch:** `git checkout -b lab04`
2. **Commit:** `terraform/`, `pulumi/`, `docs/LAB04.md`, and (bonus) `.github/workflows/terraform-ci.yml`.
   Confirm `.gitignore` excludes **`*.tfstate*`, `.terraform/`, `*.tfvars`, `pulumi/venv/`, `Pulumi.*.yaml` with secrets**, and any credential files.
3. **Clean up before committing** — keep **at most one** VM (for Lab 5) and `destroy` the rest; verify nothing is left in the cloud console; double-check no secrets or state files are staged.
4. **Open PRs:**
   - PR #1: `your-fork:lab04` → `course-repo:master`
   - PR #2: `your-fork:lab04` → `your-fork:master`

---

## Acceptance Criteria

### Main Tasks (10 points)

**Terraform VM (4 pts)**
- [ ] Provider chosen, configured, authenticated (no inline creds)
- [ ] `terraform/` with VM + network/firewall + public IP, free-tier size
- [ ] Ubuntu image found via a **data source**, not hardcoded
- [ ] SSH 22 restricted to your IP; variables + outputs used
- [ ] `fmt`/`validate`/`plan`/`apply` run; **SSH access proven**
- [ ] `.gitignore` correct; no state or secrets committed

**Pulumi VM (4 pts)**
- [ ] Terraform resources destroyed (proof) — no two VMs left undocumented
- [ ] `pulumi/` recreates the same infra in a real language
- [ ] `preview` / `up` run; **SSH access proven**
- [ ] Comparison with Terraform documented

**Documentation (2 pts)**
- [ ] `docs/LAB04.md` complete with all 5 sections
- [ ] Provider choice justified; both implementations documented
- [ ] Terraform vs Pulumi comparison present
- [ ] Lab 5 plan + cleanup proof; outputs sanitized

### Bonus Task (2 points)
- [ ] `terraform-ci.yml` runs `fmt -check`, `validate`, and a linter, gated to `terraform/**` (proof it triggers correctly) — **1 pt**
- [ ] State migrated to a remote backend with **encryption + locking**; second `plan` shows no changes; locking rationale explained — **1 pt**

---

## Rubric

| Criteria | Points | Description |
|----------|--------|-------------|
| **Terraform implementation** | 4 | Working infra, data source, restricted SSH, vars/outputs, clean state hygiene |
| **Pulumi implementation** | 4 | Same infra recreated, SSH proven, comparison written |
| **Documentation** | 2 | All sections, sanitized output, Lab 5 + cleanup |
| **Bonus: IaC CI** | 1 | Path-filtered fmt/validate/lint workflow, proven |
| **Bonus: Remote state** | 1 | Encrypted, locked backend; migration verified |
| **Total** | **10 + 2** | 10 required + 2 bonus |

**Grading guide**
- **10/10:** both tools work, clean state hygiene, strong comparison, full docs, proper cleanup
- **8–9:** infra works, good docs, minor gaps
- **6–7:** one tool solid, the other shaky, thin comparison/docs
- **<6:** infra broken, secrets/state committed, or no cleanup

**Non-negotiable:** free-tier only · no secrets or state in Git · SSH proof required · keep at most one VM (document it).

---

## Resources

<details>
<summary>📚 Terraform / OpenTofu</summary>

- [Terraform docs](https://developer.hashicorp.com/terraform/docs) · [Registry](https://registry.terraform.io/)
- [OpenTofu](https://opentofu.org) — drop-in fork, migration guide
- [Backends (S3)](https://developer.hashicorp.com/terraform/language/settings/backends/s3) · [State locking](https://developer.hashicorp.com/terraform/language/state/locking)
- [tflint](https://github.com/terraform-linters/tflint) · [Import](https://developer.hashicorp.com/terraform/cli/import)
- *Terraform: Up & Running* — Brikman (4e, 2024)

</details>

<details>
<summary>📦 Pulumi</summary>

- [Pulumi docs](https://www.pulumi.com/docs/) · [Registry](https://www.pulumi.com/registry/) · [Examples](https://github.com/pulumi/examples)
- [Pulumi vs Terraform](https://www.pulumi.com/docs/concepts/vs/terraform/) · [Secrets](https://www.pulumi.com/docs/concepts/secrets/)

</details>

<details>
<summary>☁️ Cloud providers & security</summary>

- [AWS](https://registry.terraform.io/providers/hashicorp/aws/latest/docs) · [GCP](https://registry.terraform.io/providers/hashicorp/google/latest/docs) · [Yandex](https://registry.terraform.io/providers/yandex-cloud/yandex/latest/docs)
- [Sensitive variables](https://developer.hashicorp.com/terraform/tutorials/configuration-language/sensitive-variables) · [git-secrets](https://github.com/awslabs/git-secrets)

</details>

---

## Looking Ahead

- **Lab 5 (Ansible):** SSH into this VM, install Docker, deploy your Lab 1–3 app — **keep a VM ready** or recreate it from your IaC.
- **Lab 6:** Ansible + Terraform together (provision and configure in one flow).
- **Lab 9:** Kubernetes replaces hand-managed VMs — same IaC mindset.
- **Lab 13:** GitOps (ArgoCD) drives infrastructure changes.

---

**Good luck!** 🚀

> **Remember:** IaC is about reproducibility, disposability, and visibility. If you can't `git clone && terraform apply` from scratch, it's not IaC — it's a history of console clicks. No secrets in code, no state in Git.
