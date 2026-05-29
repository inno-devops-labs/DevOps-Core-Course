# Lab 4 — Infrastructure as Code (Terraform & Pulumi)

![difficulty](https://img.shields.io/badge/difficulty-beginner-success)
![topic](https://img.shields.io/badge/topic-Infrastructure%20as%20Code-blue)
![points](https://img.shields.io/badge/points-10%2B2-orange)
![tech](https://img.shields.io/badge/tech-Terraform%20%7C%20Pulumi-informational)

> **Goal:** Provision the *same* small VM twice — once in **Terraform** HCL, once in **Pulumi** Python — and feel the trade-offs in your hands.
> **Deliverable:** A PR from `lab04` with `terraform/`, `pulumi/`, `docs/LAB04.md`, and (bonus) `.github/workflows/terraform-ci.yml`.

---

## Overview

In this lab you will practice:
- The **`init → plan → apply → destroy`** lifecycle (and reading the plan like a diff)
- Writing the four HCL primitives — `provider`, `resource`, `variable`, `output` — and one `data` source
- Recreating the same infrastructure in Pulumi Python (real loops, real types, real imports)
- **State management** — what's in `terraform.tfstate`, why it's a secret, why locking matters

> ⚠️ **Scope:** one cloud VM (or one docker-provider stand-in — see note below). No Kubernetes, no app deploy yet. Lab 5 will SSH into whatever you build here.

**Cloud or docker-provider?** Pick a free-tier cloud (recommended — that's the real skill), but if you can't open a card-protected account, the `kreuzwerker/docker` provider runs the *exact same lifecycle* locally against a container. **Lab 5 cross-ref for docker users:** the container has no sshd; Lab 5 will use `ansible_connection: community.docker.docker` (or run Ansible with `connection: local` against `docker exec`) instead of SSH — same roles, different connection plugin. Either path scores full marks; document which you picked.

---

## Project State

**You should have from previous labs:**
- Lab 1: `app_python/` (and maybe `app_go/`) — the service you'll run on the VM
- Lab 2: a multi-stage Docker image pushed to GHCR
- Lab 3: GitHub Actions building/pushing on every PR

**This lab adds:**
- `terraform/` — HCL you wrote yourself, provisioning **one VM** (or one container)
- `pulumi/` — Python that recreates the *same* infrastructure
- `docs/LAB04.md` — your run notes + the Terraform-vs-Pulumi comparison

By Lab 5 you SSH into this host and Ansible-configure it. By Lab 9 you replace it with k3d, but the IaC mindset is the same.

---

## Tech Stack & Versions

| Tool | Version | Notes |
|------|---------|-------|
| **Terraform** | **1.15.3** | BSL-1.1 since **2023-08-10**. Lock at `>= 1.15.0`. |
| **OpenTofu** | **1.12.0** | MPL-2.0, Linux Foundation. 1:1 drop-in — `tofu` works for every command below. |
| **Pulumi** | **3.243.0** | Apache-2.0 throughout. |
| **AWS provider** | `~> 5.0` | Most-documented cloud path. |
| **GCP provider** | `~> 6.0` | Alternative. |
| **Yandex provider** | `~> 0.115` | Russia-friendly, no card initially. |
| **Docker provider** | `kreuzwerker/docker ~> 3.0` | Free local stand-in if no cloud account. |

> **OpenTofu note:** the August 10 2023 BSL re-licensing made OpenTofu necessary; today's 1.12.0 runs identical HCL against the same registry. The grader accepts either CLI.

---

## Setup

```bash
terraform -version   # or: tofu -version
pulumi version

# Generate an SSH keypair for the VM if you don't have one
ssh-keygen -t ed25519 -f ~/.ssh/lab04 -C "lab04@$(hostname)"
chmod 600 ~/.ssh/lab04
cat  ~/.ssh/lab04.pub          # this is what your IaC will inject
```

Pick **one** target and stick with it for both tools:

| Target | Smallest free unit | Provider |
|--------|---------------------|----------|
| **AWS** | `t3.micro` (12 mo free) | `hashicorp/aws` |
| **GCP** | `e2-micro` (always-free zone) | `hashicorp/google` |
| **Yandex** | 2 vCPU @ 20%, 1 GB | `yandex-cloud/yandex` |
| **DigitalOcean** | `$200` student credit | `digitalocean/digitalocean` |
| **Docker (local)** | a container | `kreuzwerker/docker` |

> **No credentials in code.** Use env vars (`AWS_ACCESS_KEY_ID`, `GOOGLE_APPLICATION_CREDENTIALS`, `YC_TOKEN`, …) or a shared profile. Never inline them in `provider {}`.

Directory layout (you'll fill the files yourself):

```
terraform/
├── main.tf          # provider + resources
├── variables.tf     # inputs
├── outputs.tf       # public IP, ssh command
├── terraform.tfvars # values — GITIGNORED
├── .gitignore
└── README.md

pulumi/
├── __main__.py
├── Pulumi.yaml
├── Pulumi.dev.yaml  # GITIGNORED if it holds secrets
├── requirements.txt
└── .gitignore

docs/LAB04.md
```

---

## Task 1 — Terraform VM (4 pts)

**Goal:** a reachable VM, written in your own HCL, with clean state hygiene.

### 1.1 — Write the HCL building blocks

Lecture 4 told you HCL has the six primitives you'll meet today: `terraform {}`, `provider`, `variable`, `data`, `resource`, `output`. This task is where you write them.

`YOUR TASK`: produce `terraform/main.tf` covering **all** of the following. Don't pull a copy off Stack Overflow — that's how secrets end up in tfstate.

Required HCL **shape** (fill every `___` and every `# YOUR TASK:` comment with real values; do **not** copy a full solution from elsewhere):

```hcl
# main.tf
terraform {
  required_version = ">= ___"                          # YOUR TASK: pin TF/OpenTofu floor
  required_providers {
    ___ = {                                             # YOUR TASK: provider local name
      source  = "___/___"                               # YOUR TASK: registry source
      version = "~> ___"                                # YOUR TASK: pin a major
    }
  }
}

provider "___" {
  region = var.region    # AWS shape; GCP needs `project` + `region` or `zone`,
                         # Yandex needs `zone`, kreuzwerker/docker takes no region.
                         # Adapt to your chosen provider — see Resources block.
  # ⛔ no inline credentials (access_key/secret_key, JSON SA key body, etc.) — env vars or profile only
}

# YOUR TASK: a data source that returns the latest Ubuntu 24.04 image ID
# (Hint per cloud: aws_ami / google_compute_image / yandex_compute_image).
# Hardcoded AMI IDs go stale within months — that's why this is a data source.
data "___" "ubuntu" {
  # filters / owners / family — YOUR TASK
}

# YOUR TASK: a security group / firewall named "lab4-sg" that allows:
#   - inbound 22/tcp from var.my_ip/32 only        (NEVER 0.0.0.0/0 for SSH)
#   - inbound 80/tcp and 5000/tcp from anywhere   (your app port)
#   - egress all
# Tag it { Name = "lab4-sg", Env = "lab4" }.
resource "___" "lab" {
  # name, description, ingress blocks, egress block, tags — YOUR TASK
}

# YOUR TASK: an SSH key resource — public key from var.ssh_public_key.
resource "___" "lab" {
  # name + public_key — YOUR TASK
}

# YOUR TASK: the VM itself. Required wiring:
#   - ami / image  ← from your data source above
#   - instance_type / machine_type ← var.instance_type
#   - key_name / metadata.ssh-keys ← your key resource
#   - vpc_security_group_ids / network_interface ← your SG/firewall
#   - user_data: a one-liner that runs on first boot and prints
#       "hello from $(hostname)" into /var/log/lab4-boot.log
#   - tags: { Name = "lab4-web", Env = "lab4" }
resource "___" "web" {
  # YOUR TASK
}
```

```hcl
# variables.tf
# YOUR TASK: declare 4 variables — region, instance_type, my_ip, ssh_public_key.
# Use real HCL types (string / number / bool / list). Reminder: `int` is NOT a
# valid HCL type — use `number`. Mark ssh_public_key sensitive = true.
```

```hcl
# outputs.tf
output "public_ip" {
  value = ___                                           # YOUR TASK: resource ref
}

output "ssh_command" {
  value = ___                                           # YOUR TASK: copy-paste-ready string
                                                        # e.g. "ssh -i ~/.ssh/lab04 ubuntu@<ip>"
}
```

```gitignore
# terraform/.gitignore
# YOUR TASK: ignore everything that holds state, secrets, or local downloads.
# Hint: tfstate, tfstate.backup, the .terraform/ dir, *.tfvars, *.pem, *.key.
# DO commit .terraform.lock.hcl — it pins provider versions for reproducibility.
```

### 1.2 — Run the lifecycle (and read the plan)

```bash
terraform fmt -recursive
terraform init
terraform validate
terraform plan -out=tfplan      # READ THIS. + create / ~ update / - destroy / -/+ replace
terraform apply tfplan
```

`YOUR TASK`: after `apply`, **SSH in and prove the user_data ran**:

```bash
ssh -i ~/.ssh/lab04 ubuntu@<public_ip> "cat /var/log/lab4-boot.log; hostname"
```

(If you picked the docker-provider stand-in: `docker exec` instead and `curl` the app port — the reference submission shows the equivalent capture.)

### 1.3 — State management — the failure-mode focus

This is where students and pros both lose hours. Lecture 4 slides 15–17 are the theory; this is the practice.

`YOUR TASK`: in `docs/LAB04.md`, paste the output of `terraform state list` and answer in **3 sentences total**:

1. What does `terraform.tfstate` contain that makes it a secret? (Look at it. Don't commit it.)
2. Why is local state catastrophic for a team of two engineers?
3. What does `.terraform.lock.hcl` do, and why do you commit *it* but never the tfstate?

### 1.4 — Proof of work

**Paste into `docs/LAB04.md`:**

- `terraform plan` output (sanitized — strip ARNs/account IDs)
- `terraform apply` summary line (`N to add, M to change, K to destroy`)
- `terraform state list` output
- The SSH session showing `cat /var/log/lab4-boot.log` and `hostname`
- Output of `find terraform -maxdepth 2 -type f | sort` proving `.tfstate` is **not** in the tree

---

## Task 2 — Pulumi VM (4 pts)

**Goal:** recreate the *same* infrastructure in Pulumi Python so you can compare it.

### 2.1 — Tear down or keep the Terraform VM

`YOUR TASK`: pick one path and document it:

- **Path A** (recommended): `terraform destroy` first, build the Pulumi VM, keep that one for Lab 5. Paste the `destroy` output.
- **Path B**: keep the Terraform VM for Lab 5, build the Pulumi VM, `pulumi destroy` it after the screenshot. Don't leave two VMs running undocumented — that's how billing alerts fire at 3 a.m.

### 2.2 — Write the Pulumi program

```python
# pulumi/__main__.py
# YOUR TASK: imports — pulumi + your provider package (pulumi_aws / pulumi_gcp / …)
import ___
import ___ as ___

# YOUR TASK: read the same three inputs you used in TF, via pulumi.Config().
# pulumi config set myIp $(curl -s ifconfig.me)
# pulumi config set sshPublicKey "$(cat ~/.ssh/lab04.pub)"
# pulumi config set instanceType t3.micro
cfg = ___
my_ip       = ___
ssh_pub     = ___
instance_ty = ___

# YOUR TASK: the same Ubuntu lookup as your TF data source,
# but using the provider's get_<image> function (e.g. aws.ec2.get_ami(...)).
ubuntu = ___

# YOUR TASK: the security group / firewall — same rules as TF.
sg = ___

# YOUR TASK: the key pair — same public key.
key = ___

# YOUR TASK: the instance itself. Pass the same user_data string.
web = ___

# YOUR TASK: two exports — public_ip and a ready-to-paste ssh command.
pulumi.export("public_ip", ___)
pulumi.export("ssh_command", ___)         # hint: .apply(lambda ip: f"ssh ...")
```

```ini
# pulumi/Pulumi.yaml
# YOUR TASK: project name lab04, runtime python, description one line.
```

```text
# pulumi/requirements.txt
# YOUR TASK: pin pulumi >= 3.243 and your provider package
# (pulumi-aws / pulumi-gcp / pulumi-yandex / pulumi-docker).
```

```gitignore
# pulumi/.gitignore
# YOUR TASK: ignore venv/, __pycache__/, and any Pulumi.<stack>.yaml that
# contains plaintext secrets. The stack name itself (Pulumi.dev.yaml) may be
# committed if all values are `pulumi config set --secret`-encrypted.
```

### 2.3 — Run the lifecycle

```bash
pulumi login --local                             # or `pulumi login` for Pulumi Cloud
pulumi stack init dev
pulumi config set aws:region eu-central-1        # adapt to your provider
pulumi config set myIp $(curl -s ifconfig.me)
pulumi config set --secret sshPublicKey "$(cat ~/.ssh/lab04.pub)"

pulumi preview                                   # ≈ terraform plan
pulumi up --yes
# ... ssh in and verify ...
pulumi destroy --yes                             # if Path B above, or before Lab 5 if Path A
```

### 2.4 — Proof of work

**Paste into `docs/LAB04.md`:**

- `pulumi preview` output (sanitized)
- `pulumi up` summary line
- The SSH session against the Pulumi VM (or the equivalent on the docker stand-in)
- Either the `terraform destroy` proof (Path A) or the `pulumi destroy` proof (Path B)

### 2.5 — The comparison (this is the point of doing both)

`YOUR TASK`: in `docs/LAB04.md`, write 3–5 sentences for each of:

1. **Readability** — which file was easier to skim a week later?
2. **Logic & loops** — imagine deploying the same VM × `["dev","staging","prod"]`. Which tool did you find more natural for that?
3. **Debugging** — when your `apply`/`up` failed, which tool's error message pointed you at the fix faster?
4. **State + secrets** — where does each tool put state? Which one encrypts secrets by default?
5. **When you'd pick each** — one concrete scenario per tool, drawn from your own experience this week.

---

## Task 3 — Documentation (2 pts)

`docs/LAB04.md` must contain, in order:

1. **Provider & target** — which cloud (or docker stand-in), which region/zone, instance size, and a one-line cost note (should be `$0`).
2. **Terraform implementation** — version used, file layout, the 3-sentence state-management answer from 1.3, sanitized lifecycle output, SSH proof.
3. **Pulumi implementation** — language + version, lifecycle output, SSH proof.
4. **Terraform vs Pulumi** — the 5-bullet comparison from 2.5.
5. **Lab 5 prep & cleanup** — which VM (if any) is staying alive, or how Lab 5 will recreate one from your IaC. Plus `destroy` proof for everything you tore down.

> All terminal output must be sanitized: no full account IDs, no access keys, no API tokens. Mark anything reconstructed `(illustrative)`.

---

## Bonus Task — IaC CI/CD + Remote State (2 pts)

### Part 1 — GitHub Actions validation (1 pt)

`YOUR TASK`: create `.github/workflows/terraform-ci.yml` that runs on PRs touching `terraform/**` and runs `fmt -check -recursive`, `init -backend=false`, `validate`, and `tflint`. Use **first-party** actions only — `hashicorp/setup-terraform` (or `opentofu/setup-opentofu`) and `terraform-linters/setup-tflint`. No long-lived cloud creds: `-backend=false` skips state.

Skeleton — fill the blanks:

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
      - uses: ___                                       # YOUR TASK: setup-terraform action + version pin
        with:
          terraform_version: "___"                      # YOUR TASK: the version from the table above
      # YOUR TASK: 4 steps — fmt -check -recursive, init -backend=false, validate, tflint.
      # tflint needs its own setup action; add a minimal terraform/.tflint.hcl too.
```

**Prove it:**
- Open a PR touching `terraform/` — the workflow runs and stays green.
- Push a `fmt`-violating commit on top — the workflow goes **red** at the `fmt -check` step. Screenshot or paste the failing log.
- Touch a non-`terraform/**` file — the workflow does **not** trigger.

### Part 2 — Migrate to remote, locked state (1 pt)

`YOUR TASK`:

1. Create a state bucket: S3 with **versioning + encryption**, or GCS with versioning, or Yandex Object Storage. By hand or by a tiny separate Terraform config — document which.
2. Add a `backend "s3"` / `backend "gcs"` block to your `terraform/` config:
   - For S3, use `use_lockfile = true` (TF 1.10+ native state locking — no more DynamoDB table).
   - For GCS, locking is native and automatic.
   - **Always** set `encrypt = true`.
3. `terraform init -migrate-state` and confirm the local `terraform.tfstate` moved to the bucket.
4. Run `terraform plan` again — it must report **No changes** (proves the state migrated cleanly, not re-imported).
5. In `docs/LAB04.md`, explain in 2–3 sentences **why locking prevents two engineers from corrupting state** and what the failure mode looks like without it.

---

## How to Submit

```bash
git switch -c lab04
git add terraform/ pulumi/ docs/LAB04.md
git add .github/workflows/terraform-ci.yml      # bonus only
git commit -m "feat(lab04): IaC with Terraform + Pulumi"
git push -u origin lab04
```

Open **two** PRs:

- `your-fork:lab04` → `course-repo:master` *(reviewed)*
- `your-fork:lab04` → `your-fork:master`

PR checklist:

```text
- [ ] terraform/ provisions a VM end-to-end; SSH proven
- [ ] pulumi/ recreates the same infra; SSH proven
- [ ] No *.tfstate, *.tfvars, .terraform/, or Pulumi secret stack file in the diff
- [ ] .terraform.lock.hcl IS committed
- [ ] docs/LAB04.md has all 5 sections + the TF-vs-Pulumi comparison
- [ ] At most ONE VM left running, and it's named in docs (for Lab 5)
- [ ] Bonus (optional): terraform-ci.yml proven green+red; remote state migrated
```

---

## Acceptance Criteria

### Task 1 — Terraform (4 pts)
- ✅ Provider chosen, authenticated via env/profile (no inline creds)
- ✅ `data` source for the Ubuntu image (not a hardcoded AMI/ID)
- ✅ Security group / firewall restricts **SSH 22 to your IP/32** only
- ✅ All six primitives present: `terraform{}`, `provider`, `variable`, `resource`, `data`, `output`
- ✅ `user_data` runs on first boot and writes to `/var/log/lab4-boot.log`
- ✅ SSH session in `docs/LAB04.md` shows the boot log line + hostname
- ✅ `.gitignore` correct: tfstate ignored, `.terraform.lock.hcl` committed
- ✅ 3-sentence state-management answer present

### Task 2 — Pulumi (4 pts)
- ✅ Same infra recreated in Pulumi Python (or TS/Go/Java — Python recommended)
- ✅ `pulumi preview` + `pulumi up` succeed; SSH proven
- ✅ At most one of the two VMs is left running and it's documented
- ✅ 5-bullet TF-vs-Pulumi comparison

### Task 3 — Docs (2 pts)
- ✅ All 5 sections in `docs/LAB04.md`
- ✅ Outputs sanitized; cleanup proof included

### Bonus (2 pts)
- ✅ `terraform-ci.yml` runs `fmt`/`init`/`validate`/`tflint`, gated to `terraform/**`, proven green + red — **1 pt**
- ✅ Remote, encrypted, **locked** backend; migration confirmed; locking rationale explained — **1 pt**

---

## Rubric

| Task | Points | Criteria |
|------|-------:|----------|
| **Task 1** — Terraform VM | **4** | Working infra, data source, restricted SSH, vars/outputs, clean state hygiene |
| **Task 2** — Pulumi VM | **4** | Same infra in Pulumi, SSH proven, comparison written |
| **Task 3** — Documentation | **2** | All 5 sections, sanitized output, cleanup proof |
| **Bonus** — CI for IaC | **1** | Path-filtered fmt/validate/lint workflow, green-and-red proof |
| **Bonus** — Remote state | **1** | Encrypted + locked backend, migration proven, rationale explained |
| **Total** | **10 + 2** | 10 main + 2 bonus |

**Non-negotiables:** free-tier only · no secrets or state in Git · SSH proof required · at most one VM left for Lab 5.

---

## Resources

<details>
<summary>📚 Terraform / OpenTofu</summary>

- [Terraform docs](https://developer.hashicorp.com/terraform/docs) · [Registry](https://registry.terraform.io/)
- [OpenTofu](https://opentofu.org) — drop-in fork; migration guide
- [S3 backend](https://developer.hashicorp.com/terraform/language/settings/backends/s3) · [State locking](https://developer.hashicorp.com/terraform/language/state/locking) · [`terraform import`](https://developer.hashicorp.com/terraform/cli/import)
- [tflint](https://github.com/terraform-linters/tflint)
- *Terraform: Up & Running* — Brikman (4e, 2024 — covers OpenTofu)

</details>

<details>
<summary>📦 Pulumi</summary>

- [Pulumi docs](https://www.pulumi.com/docs/) · [Registry](https://www.pulumi.com/registry/)
- [Pulumi vs Terraform](https://www.pulumi.com/docs/concepts/vs/terraform/) · [Secrets](https://www.pulumi.com/docs/concepts/secrets/)

</details>

<details>
<summary>☁️ Provider quick-references</summary>

- **AWS** — [provider docs](https://registry.terraform.io/providers/hashicorp/aws/latest/docs); auth via `AWS_ACCESS_KEY_ID` / `~/.aws/credentials`. Ubuntu owner ID: `099720109477`.
- **GCP** — [provider docs](https://registry.terraform.io/providers/hashicorp/google/latest/docs); auth via `gcloud auth application-default login`. Enable Compute Engine API. SSH key in instance `metadata = { ssh-keys = "ubuntu:${var.ssh_public_key}" }`.
- **Yandex** — [provider docs](https://registry.terraform.io/providers/yandex-cloud/yandex/latest/docs); service-account JSON key. Free-tier shape: `standard-v3`, `core_fraction = 20`, 1 GB RAM.
- **Docker stand-in** — `kreuzwerker/docker ~> 3.0`; `docker_image` + `docker_container`. No SSH; `docker exec` + curl the published port.

</details>

<details>
<summary>⚠️ Common Pitfalls (from real dry-runs)</summary>

- **`type = int` is invalid HCL.** Variable types are `string`, `number`, `bool`, `list`, `map`, `set`, `object`, `tuple`, `any`. `int` will fail `terraform validate` with a "Invalid type specification" — use `number`.
- **Committed `terraform.tfstate`.** Holds resource IDs, private IPs, sometimes plaintext secrets, and merge conflicts on JSON are *unrecoverable*. `.gitignore` line 1.
- **Forgetting `.terraform.lock.hcl`.** This one **you DO commit** — it pins provider hashes so a teammate's `init` resolves to the same `aws ~> 5.x` patch you used. Without it, two engineers can apply with subtly different provider versions and produce different infra.
- **Credentials in `provider {}`.** Code Spaces (2014) was deleted in 12 hours because of this exact pattern. Env vars or shared profile, never inline. Don't put them in `.tfvars` either — that's another file students commit by accident.
- **Default-deny egress on a new AWS security group.** Terraform's `aws_security_group` resource has *no implicit egress* unlike the AWS console — you must write the `egress` block yourself or the VM can't reach the internet for `apt`, the user_data hangs, and `apply` "succeeds" with a broken host.
- **Relying on the default VPC.** It exists on day-one AWS accounts but new orgs delete it for compliance. Either look it up via `data "aws_vpc" "default" { default = true }` or create your own — never assume.
- **SSH wide open.** `0.0.0.0/0` on port 22 = your VM is in a botnet within hours. `var.my_ip/32` only. (`curl -s ifconfig.me` to find your IP.)
- **Hardcoded AMI ID.** `ami-0c55b159cbfafe1f0` was the Ubuntu 22.04 AMI in eu-central-1 *once*. AMIs rotate as Canonical ships patches; hardcoded IDs go 404 in months. Use a `data "aws_ami"` filter on the name pattern.
- **Two simultaneous `apply`s with local state.** State JSON gets half-written, Terraform can't parse it, recovery is hand-editing — which itself is forbidden. This is the whole reason the bonus task exists.

</details>

---

## Looking Ahead

| Lab | What it does with your Lab 4 VM |
|---:|---|
| 5 | Ansible roles SSH in and install Docker + your Lab 1–3 app |
| 6 | Ansible blocks/rescue, tags, Compose deploy via the same SSH path |
| 9 | k3d replaces the hand-VM model — same IaC mindset, different unit |
| 13 | ArgoCD takes over deploys; your IaC still defines the cluster |

> **Remember:** if you can't `git clone && terraform apply` from scratch, it's not IaC — it's a history of console clicks. No secrets in code, no state in Git. The five rules from lecture 4 slide 22 are paid for in real money (slide 23).
