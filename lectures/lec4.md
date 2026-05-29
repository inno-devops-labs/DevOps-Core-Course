# 📌 Lecture 4 — Infrastructure as Code with Terraform & Pulumi

## 📍 Slide 1 – 🏗️ Welcome to Infrastructure as Code

* 🐶 **Lecture 1 promised cattle, not pets** — today we deliver
* 📝 **IaC** = your cloud lives in Git, not in someone's browser tabs
* 🌍 **Terraform + Pulumi** = the two ways modern teams provision infrastructure
* 🎯 By the end: you can spin up (and tear down) a VM with one command — and review the diff before applying

```mermaid
flowchart LR
  Manual[🖱️ Console clicks] -->|IaC| Code[📝 Code in Git]
  Code --> Plan[📋 plan]
  Plan --> Apply[🚀 apply]
  Apply --> Cloud[☁️ Reproducible cloud]
```

> 🔗 **Tie-in to Lab 4:** you'll build the *same* VM twice — once with Terraform, once with Pulumi — and feel the trade-offs first hand. The bonus task adds a GitHub Actions workflow that runs `plan` on every PR.

---

## 📍 Slide 2 – 🎯 Learning Outcomes

| # | Outcome |
|---|---------|
| 1 | 🧠 Explain why snowflake servers are a business risk |
| 2 | 📝 Write a working Terraform configuration with provider, resource, variable, output |
| 3 | 🔄 Run the `init → plan → apply → destroy` lifecycle confidently |
| 4 | 📦 Move state from local disk to a remote, locked backend — and explain why |
| 5 | 🐍 Provision the same infrastructure with Pulumi in Python |
| 6 | ⚖️ Pick Terraform vs Pulumi vs OpenTofu based on team and use case |

---

## 📍 Slide 3 – 🔧 Tech Stack Pinned for May 2026

| Tool | Version | Notes |
|------|---------|-------|
| 🌍 **Terraform** | **1.15.3** | Released May 13 2026; BSL-1.1 since **August 10, 2023** |
| 🌱 **OpenTofu** | **1.12.0** | Released May 14 2026; MPL-2.0, Linux Foundation; 1:1 drop-in CLI |
| 📦 **Pulumi** | **3.243.0** | May 2026; Apache-2.0 throughout |
| ☁️ **AWS provider** | v5.x | Used in most Lab 4 examples |
| ☁️ **GCP provider** | v6.x | Alternative for Lab 4 |
| ☁️ **Yandex provider** | v0.115+ | Default for Russia-only labs |

> 🔧 **You can swap `terraform` for `tofu` in every command on these slides.** The HCL is identical. Choose based on license preference and team norms — labs accept both.

---

## 📍 Slide 4 – ❓ The Big Question

* 📊 The 2024 Flexera *State of the Cloud* report: **89%** of enterprises run multi-cloud — and **70%+** report uncontrolled drift between intended and actual config
* ⏱️ Manual VM provisioning: **hours to days** for one server, then days more to make a copy match
* 💥 Most outages are caused by **changes** — and untracked changes are the worst kind

> 💬 *"It worked in staging — staging was different."* — Every ops engineer, ever

**🤔 Think:**
* Could you recreate your production cloud from scratch tomorrow?
* If the person who built it left this morning, how long until you're stuck?

---

## 📍 Slide 5 – 🐶 Pets vs. Cattle (Bill Baker, Microsoft, 2012)

* 🐶 **Pets** — named (`web-prod-01`), nursed, irreplaceable, downtime if sick
* 🐄 **Cattle** — numbered (`web-001..099`), identical, disposable, replaced if sick
* ☁️ **Cloud-native = cattle mindset.** Lecture 1 foreshadowed this; today we make it real.

```mermaid
flowchart LR
  Pets[🐶 Pets<br/>SSH'd into, hand-tuned]
  Cattle[🐄 Cattle<br/>Defined in code, replaced in minutes]
  Pets -.->|IaC + immutable infra| Cattle
```

> 📖 Bill Baker coined this metaphor in a 2012 internal Microsoft talk later popularized by Randy Bias of CloudScaling. Twelve years later, every cloud architecture book still uses it. It works because it's true.

---

## 📍 Slide 6 – 😱 Snowflakes, Drift, and Bus Factor

The three failure modes IaC fixes:

| Failure | What it looks like | What it costs |
|---------|---------------------|---------------|
| ❄️ **Snowflake server** | "Don't touch web-03, only Petya knows what's on it" | Can't scale, can't reproduce, can't replace |
| 📉 **Configuration drift** | Staging and prod were identical 6 months ago — not anymore | Bugs that only repro in prod, hours debugging |
| 🚌 **Bus factor = 1** | One person holds the cloud architecture in their head | Project halts when they're on vacation or quit |

> 🔥 **Hot take:** if you can't *delete and recreate* your production environment from a Git tag, you don't have IaC — you have an `aws` CLI history.

---

## 📍 Slide 7 – 💡 What Infrastructure as Code Actually Is

* 📝 **Definition:** managing and provisioning infrastructure through *machine-readable, version-controlled* config files instead of manual console clicks or ad-hoc scripts.
* 🔄 The cloud becomes a **build artifact**, not a hand-crafted environment
* 📜 Every change goes through the same process you use for application code: PR → review → CI → merge → deploy

```mermaid
flowchart LR
  Code[📝 .tf / .py in Git] --> CI[🧪 CI: plan]
  CI --> Review[👀 PR review]
  Review --> Merge[🚀 Merge → apply]
  Merge --> Cloud[☁️ Real infrastructure]
  Cloud -->|diff| Code
```

> 📖 *Infrastructure as Code* — Kief Morris (2nd ed., 2020). The reference text; defines the four core principles below.

---

## 📍 Slide 8 – 📐 The Four Principles (Morris)

1. ♻️ **Reproducibility** — same code → same infrastructure, every time
2. 🔁 **Disposability** — destroy and rebuild should be routine, not heroic
3. 📜 **Consistency** — dev, staging, prod differ only in variables
4. 🔍 **Visibility** — `git log` answers "who changed what, when, why"

> 💡 **If any one of these is missing, you have automation — not IaC.** Bash scripts that create a VM are not IaC; they're a recipe nobody can replay safely.

---

## 📍 Slide 9 – 🔀 Declarative vs. Imperative

```mermaid
flowchart LR
  Decl[📝 Declarative<br/>'I want 3 VMs'] --> Tool1[🤖 Tool figures out HOW]
  Imp[🔧 Imperative<br/>'Create VM 1, then VM 2, then VM 3'] --> Tool2[🏃 You define each step]
```

| Aspect | 📝 Declarative | 🔧 Imperative |
|--------|---------------|---------------|
| You write | Desired end state | Sequence of steps |
| Idempotency | Built in — re-run is safe | You implement it |
| Examples | Terraform HCL, CloudFormation, Kubernetes YAML | Bash scripts, AWS SDK calls, Pulumi (mostly) |
| Failure mode | Tool can't figure out a tricky migration | Step 7 fails on re-run |

> 🤔 **Pulumi twist:** code is imperative, but the Pulumi engine resolves it into a *declarative* desired-state graph before talking to the cloud. Best of both worlds.

---

## 📍 Slide 10 – 🛠️ The IaC Tool Landscape (May 2026)

| Tool | License | Language | Multi-cloud | State |
|------|---------|----------|-------------|-------|
| 🌍 **Terraform 1.15.3** | BSL-1.1 (HashiCorp) | HCL | ✅ 3000+ providers | Local / S3 / TF Cloud |
| 🌱 **OpenTofu 1.12.0** | MPL-2.0 (Linux Foundation) | HCL (Terraform-compatible) | ✅ Same providers | Local / S3 / OCI |
| 📦 **Pulumi 3.243** | Apache-2.0 | Python, TS, Go, C#, Java, YAML | ✅ AWS, GCP, Azure, K8s, … | Pulumi Cloud / S3 / local |
| ☁️ **AWS CloudFormation** | Proprietary | YAML / JSON | ❌ AWS only | Managed by AWS |
| ☁️ **AWS CDK / GCP CDK** | Apache-2.0 | TS, Python, Java, Go | ❌ Per-cloud | Underlying CloudFormation / Deployment Manager |
| ☸️ **Crossplane** | Apache-2.0 | Kubernetes YAML | ✅ via providers | Kubernetes etcd |

> 🔗 **This lecture focuses on Terraform and Pulumi** — the two tools Lab 4 uses. OpenTofu shows up in slide 21.

---

## 📍 Slide 11 – 📜 A Brief History

* 📅 **July 2014** — Mitchell Hashimoto and Armon Dadgar release **Terraform v0.1** at HashiCorp. First serious multi-cloud IaC tool.
* 📅 **September 2019** — **Pulumi v1.0** released by Joe Duffy's team. First IaC tool to embrace general-purpose programming languages.
* 📅 **August 10, 2023** — HashiCorp re-licenses Terraform from MPL-2.0 to the **Business Source License (BSL)**. Vendors building products on Terraform suddenly need a paid agreement.
* 📅 **August 2023** — Gruntwork, env0, Spacelift, and Terragrunt fork Terraform 1.5 → **OpenTofu**.
* 📅 **September 2023** — OpenTofu is **donated to the Linux Foundation** for vendor-neutral governance; first stable 1.6 release in January 2024.
* 📅 **December 2023** — Linux Foundation announces **OpenBao**, the parallel community fork of Vault (same BSL backstory).
* 📅 **May 2026 (now)** — Terraform 1.15.3 and OpenTofu 1.12.0 are CLI-compatible; most enterprises use one or the other, never both.

> 🔥 The BSL change is the single most consequential IaC event of the decade. It's why this lecture treats OpenTofu as first-class.

---

## 📍 Slide 12 – 🌍 Terraform Workflow

```mermaid
flowchart LR
  Write[📝 Write .tf] --> Init[🔧 init]
  Init --> Plan[📋 plan]
  Plan --> Apply[🚀 apply]
  Apply --> Destroy[💥 destroy]
  Plan -.->|review| Plan
```

```bash
terraform init      # ⬇️ download provider binaries to .terraform/
terraform plan      # 🔍 diff between code, state, and reality
terraform apply     # 🚀 make reality match code
terraform destroy   # 💥 delete everything in this state
```

> ⚠️ **`plan` is sacred.** Read it. Every time. Especially before `apply` in production. CI should post the plan into the PR — Lab 4 bonus wires this up.

---

## 📍 Slide 13 – 🧱 HCL Building Blocks

```hcl
# ☁️ provider — which cloud and how to authenticate
provider "aws" {
  region = var.region
}

# 📊 variable — input
variable "region" {
  description = "AWS region"
  type        = string
  default     = "eu-central-1"
}

# 🏗️ resource — something we create and own
resource "aws_instance" "web" {
  ami           = "ami-0c55b159cbfafe1f0"   # Ubuntu 22.04 LTS, eu-central-1
  instance_type = "t3.micro"
  tags = { Name = "lab4-web", Env = "lab" }
}

# 🔍 data — read-only lookup of something we don't own
data "aws_vpc" "default" { default = true }

# 📤 output — value to surface after apply (and for other modules)
output "public_ip" {
  value = aws_instance.web.public_ip
}
```

> 📝 Five primitives — `provider`, `resource`, `variable`, `output`, `data` — cover **90%** of real Terraform code. Modules are just bundles of these.

---

## 📍 Slide 14 – 🔄 `plan` Output — Read It Like A Diff

```text
$ terraform plan

Terraform will perform the following actions:

  # aws_instance.web will be created
  + resource "aws_instance" "web" {
      + ami           = "ami-0c55b159cbfafe1f0"
      + instance_type = "t3.micro"
      + public_ip     = (known after apply)
      + tags          = {
          + "Env"  = "lab"
          + "Name" = "lab4-web"
        }
    }

Plan: 1 to add, 0 to change, 0 to destroy.
```

| Symbol | Meaning |
|:------:|---------|
| `+` | Create |
| `-` | Destroy (data loss risk!) |
| `~` | Update in place |
| `-/+` | Destroy and recreate (data loss risk!) |

> 🚨 **`-/+` on a database resource = your data is about to die.** Read every plan, every time, in production.

---

## 📍 Slide 15 – 📦 State: The Thing That Makes Terraform Work

* 🗺️ **State** = a JSON map from your code (`aws_instance.web`) to a real cloud object (`i-0abc123…`)
* 🔍 Without state, Terraform has no idea what already exists — every apply would try to create everything
* ⚠️ State contains **sensitive data**: passwords, private IPs, sometimes private keys — treat it like a secret

```mermaid
flowchart LR
  Code[📝 .tf code] --> TF[🌍 terraform]
  State[📦 terraform.tfstate] --> TF
  Cloud[☁️ Real cloud] --> TF
  TF -->|plan diff| You[👀 You]
```

> ⚠️ **Never edit `terraform.tfstate` by hand.** Use `terraform state` subcommands (`mv`, `rm`, `import`).

---

## 📍 Slide 16 – 🌐 Local vs. Remote State

| | 📁 Local (`terraform.tfstate` on disk) | 🌐 Remote (S3, GCS, TF Cloud, …) |
|-|----------------------------------------|----------------------------------|
| Solo prototyping | ✅ Fine | Overkill |
| Team of 2+ | ❌ Two engineers apply → race condition, corrupted state | ✅ Locking serializes applies |
| Disaster recovery | ❌ Laptop dies → state lost → cloud orphaned | ✅ Versioned object storage |
| Secrets in state | 🟡 Plaintext on disk | ✅ Encrypted at rest (KMS) |
| CI/CD | ❌ Each runner has stale state | ✅ Shared canonical state |

**📦 Remote backend example (S3 + DynamoDB lock):**

```hcl
terraform {
  backend "s3" {
    bucket         = "acme-tf-state"
    key            = "lab4/terraform.tfstate"
    region         = "eu-central-1"
    dynamodb_table = "tf-locks"     # 🔒 prevents concurrent applies
    encrypt        = true           # 🔐 SSE-KMS
  }
}
```

> 🔗 **Lab 4 starts with local state on purpose** — so the failure mode of two students applying at once is visible. The bonus task migrates to S3.

---

## 📍 Slide 17 – 🚨 State Pitfalls (Where Students and Pros Both Screw Up)

1. 🙅 **Committing `terraform.tfstate` to Git** — it has secrets, and merge conflicts on JSON are unrecoverable. Add it to `.gitignore` on day one.
2. 🔓 **No locking on remote state** — two simultaneous `apply`s race; state ends up corrupt; recovery is manual.
3. 📉 **Drift** — someone clicks in the AWS console; Terraform doesn't know; next `apply` reverts or fails.
   * Catch it: `terraform plan` in a nightly CI job — any non-zero diff = drift.
4. 🔄 **Orphaned resources** — you `rm -rf` a module; Terraform forgets about its resources; they bill forever.
   * Use `terraform state list` before deleting code.
5. 📥 **Need to manage existing cloud objects you didn't create with Terraform?**

```bash
# Adopt an existing EC2 instance into Terraform state
terraform import aws_instance.web i-0abc123def456

# Or, with Terraform 1.5+, declare it once and let TF import on apply
import {
  to = aws_instance.web
  id = "i-0abc123def456"
}
```

> 🔥 **Drift detection is half the value of IaC.** Cattle that wander off the ranch are still cattle — until somebody renames them.

---

## 📍 Slide 18 – 📦 Pulumi — Infrastructure in Your Favorite Language

* 🐍 Write infrastructure in **Python, TypeScript, Go, C#, Java**, or YAML
* 🔧 Loops, conditionals, functions, classes, unit tests — your normal dev tools work
* 📦 State stored in Pulumi Cloud (free for individuals, paid for teams) or self-hosted (S3, Azure Blob)
* 🔐 Secrets **encrypted by default** in state (no opt-in needed)

```python
# 🐍 pulumi/__main__.py — same VM as the Terraform example
import pulumi
import pulumi_aws as aws

web = aws.ec2.Instance("web",
    ami="ami-0c55b159cbfafe1f0",
    instance_type="t3.micro",
    tags={"Name": "lab4-web", "Env": "lab"})

pulumi.export("public_ip", web.public_ip)
```

```bash
pulumi up        # equivalent to terraform plan + apply
pulumi preview   # plan only
pulumi destroy   # tear down
```

> 🔗 **Lab 4 Task 2** reimplements your Terraform VM in Pulumi Python — you'll feel the difference in 30 minutes.

---

## 📍 Slide 19 – 🧠 Why Code-as-Infrastructure Matters

```python
# 🐍 Loops, conditionals, and reuse — natural in Python
for env in ["dev", "staging", "prod"]:
    aws.ec2.Instance(f"web-{env}",
        ami="ami-0c55b159cbfafe1f0",
        instance_type="t3.micro" if env != "prod" else "t3.large",
        tags={"Env": env})
```

```hcl
# 🌍 The same thing in HCL — works, but the syntax is less natural
locals {
  envs = { dev = "t3.micro", staging = "t3.micro", prod = "t3.large" }
}
resource "aws_instance" "web" {
  for_each      = local.envs
  ami           = "ami-0c55b159cbfafe1f0"
  instance_type = each.value
  tags          = { Env = each.key }
}
```

> 💡 **The right tool depends on the team.** Python shops with strong dev culture often prefer Pulumi. Platform teams that touch dozens of providers and need HashiCorp's ecosystem usually pick Terraform/OpenTofu. **Lab 4 makes you do both so you can decide for yourself.**

---

## 📍 Slide 20 – ⚖️ Terraform vs. Pulumi vs. OpenTofu

| Aspect | 🌍 Terraform 1.15.3 | 🌱 OpenTofu 1.12.0 | 📦 Pulumi 3.243 |
|--------|--------------------|------------------|------------------|
| 📜 License | BSL-1.1 | MPL-2.0 | Apache-2.0 |
| 🏢 Steward | HashiCorp (IBM, 2025) | Linux Foundation | Pulumi Corp |
| 📝 Language | HCL | HCL (Terraform-compatible) | Python, TS, Go, C#, Java, YAML |
| 🧠 Paradigm | Declarative | Declarative | Imperative → declarative graph |
| 🔄 Logic | `for_each`, `count`, `dynamic` | Same + `for_each` improvements | Full programming language |
| 🧪 Unit testing | Terratest (Go) | Same | Native (pytest, jest, go test) |
| 📦 Default state | Local / S3 / TF Cloud | Local / S3 / OCI | Pulumi Cloud / S3 |
| 🔐 Secrets in state | Plaintext (unless backend encrypts) | Plaintext + native encryption in 1.7+ | Encrypted by default |
| 🌐 Community | Largest (millions of users) | Growing fast (LF-backed) | Smaller but loyal |

> 🎯 **Course default:** Lab 4 accepts any of the three. Use whichever your team uses in real life.

---

## 📍 Slide 21 – 🌱 OpenTofu: Why You Care About the Fork

* 📅 **August 10, 2023** — HashiCorp changes Terraform's license from MPL-2.0 (permissive) to BSL-1.1 (source-available but commercial use restricted)
* 😡 Companies whose products *depend on* Terraform (Spacelift, env0, Gruntwork) face existential risk
* 🍴 **August 2023:** they fork Terraform 1.5 → publish as **OpenTofu** under MPL-2.0
* 🏛️ **September 2023:** OpenTofu is **donated to the Linux Foundation** → vendor-neutral governance
* 🏛️ **December 2023:** Linux Foundation announces **OpenBao** — the same fork pattern, applied to Vault
* ✅ **Today:** OpenTofu 1.12.0 is a 1:1 drop-in for Terraform 1.15.3 — same HCL, same providers, same registry (mostly)
* 💼 **2025:** IBM acquires HashiCorp; Terraform stays BSL — the fork is permanent

```bash
# Identical workflows
terraform init && terraform plan && terraform apply
tofu init && tofu plan && tofu apply

# Yes, you can copy a Terraform repo and run `tofu` against it
```

> 🔥 The right answer in 2026 is *probably* OpenTofu for new projects, Terraform for existing ones with paid HashiCorp support. Pick deliberately.

---

## 📍 Slide 22 – 🔐 Security: Don't Be a Headline

**Five rules. Memorize them.**

1. 🚫 **Never commit credentials.** Not in `.tf`, not in `.tfvars`, not in `provider {}` blocks.

```hcl
# ❌ NEVER
provider "aws" {
  access_key = "AKIAIOSFODNN7EXAMPLE"
  secret_key = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
}

# ✅ Let the provider read env vars or AWS profile
provider "aws" {
  region = var.region
}
```

2. 🙈 **Never commit `terraform.tfstate` or `*.tfstate.backup`** — they contain decrypted secrets. Add to `.gitignore` line 1.
3. 🌐 **Use a remote backend with encryption + locking** — S3 + SSE-KMS + DynamoDB lock, GCS with versioning, or Pulumi Cloud.
4. 🔑 **Use OIDC for CI cloud auth, not long-lived keys.** GitHub Actions → AWS / GCP via `aws-actions/configure-aws-credentials` or `google-github-actions/auth` — no secrets in repo, ever.
5. 🔍 **Scan IaC code.** `tfsec`, `checkov`, `terrascan` — wire them into CI. Catches public S3 buckets, missing encryption, IAM wildcards.

> 🔗 **Course tie-in:** Lab 4 bonus adds a `terraform plan` + `checkov` step on every PR. DevSecOps elective goes deeper.

---

## 📍 Slide 23 – 💥 Real Incidents — Why These Rules Exist

* 🏦 **Code Spaces (2014)** — credentials in a repo → AWS console takeover → attacker deleted S3 + EC2 + RDS → company *literally shut down* in 12 hours. The textbook "don't commit credentials" story.
* 🚗 **Uber (2016)** — AWS keys hardcoded in a private GitHub repo → 57M user records exfiltrated → $148M settlement. Private ≠ safe.
* 🏭 **2024 SAP Concur** — internal Terraform state in an unencrypted S3 bucket leaked employee PII for years.
* 🐍 **2025 SnakeKeylogger / Codefinger** — attackers found leaked Pulumi Cloud tokens in public repos and used them to enumerate and ransom S3 buckets via SSE-C.
* 📉 **Knight Capital (2012, pre-IaC)** — manual deploy to 7 of 8 servers, the 8th still had old code → $440M loss in 45 minutes. Manual = drift = catastrophe.

> 💡 **Every one of these would have been prevented by following the rules on slide 22.** The rules are paid for in real money.

---

## 📍 Slide 24 – 🎯 Key Takeaways

1. 🏗️ **Infrastructure as Code = your cloud lives in Git** — reproducible, disposable, consistent, visible
2. 🐄 **Cattle, not pets** — name servers by role + number, never as individuals
3. 🔄 **Read the `plan`** — every time, especially before production apply
4. 📦 **Remote, locked, encrypted state from day one** in any team setting
5. 🌍 **Terraform/OpenTofu** for big ecosystems and declarative simplicity; **Pulumi** for code-heavy teams and complex logic
6. 🌱 **OpenTofu exists because licensing matters** — know the story, pick deliberately
7. 🔐 **No secrets in code. No state in Git. OIDC for CI.** Three rules; non-negotiable.

> 💡 **If you can't `git clone && terraform apply` from scratch, it's not IaC — it's a haunted spreadsheet of clicks.**

---

## 📍 Slide 25 – 🧠 The Mindset Shift

| 😰 Old | 🚀 IaC-native |
|--------|--------------|
| 🙅 "SSH and fix it" | 📝 "Change the code, plan, apply" |
| 🚫 "Don't touch web-03" | 💪 "Destroy web-03 and let TF rebuild it" |
| 👉 "Who set this up?" | 📜 `git blame` answers it |
| 😨 "Manual is faster" | ⚡ "Manual is faster *once*. IaC is faster forever." |
| 💻 "Works on my cloud" | 🌍 "Works in any account that runs the code" |
| 🤷 "We'll document it later" | 📝 "The code IS the documentation" |

> ❓ Which column describes the team you want to work on?

---

## 📍 Slide 26 – 🚀 What Comes Next

**📚 Next lecture: *Configuration Management with Ansible.*** Terraform builds the VM; Ansible configures what runs *inside* it. The two complete each other.

* 🔧 Idempotent playbooks over SSH
* 📦 Roles, inventories, and Ansible Galaxy
* 🤖 Provisioning Docker on the VMs you'll create in Lab 4

**🔬 Lab 4 this week:** create a cloud VM with both Terraform *and* Pulumi, compare the experience, and (bonus) wire `terraform plan` into a GitHub Actions PR check. Keep the VM running — **Lab 5 will SSH into it**.

```mermaid
flowchart LR
  Lab4[🏗️ Lab 4: TF + Pulumi VM] --> Lab5[🔧 Lab 5: Ansible configures it]
  Lab5 --> Lab9[☸️ Lab 9: K8s on similar VMs]
  Lab9 --> Future[🚀 Labs 13+: GitOps on top]
```

**👋 See you in Lecture 5.**

> 🐄 From snowflakes to cattle — one `terraform apply` at a time.

---

## 📚 Resources & Further Reading

**📕 Books:**
* *Terraform: Up & Running* — Yevgeniy Brikman, O'Reilly (3rd ed., 2022; 4th ed. covers OpenTofu, late 2025)
* *Infrastructure as Code* — Kief Morris, O'Reilly (2nd ed., 2020). The reference text.
* *Pulumi: Up & Running* — Adam Gordon Bell, O'Reilly (2024).
* *The Phoenix Project* — Kim, Behr, Spafford. Still the best dramatization of the problems IaC solves.

**🔗 Links:**
* 🌐 [developer.hashicorp.com/terraform](https://developer.hashicorp.com/terraform) — official Terraform docs (1.10)
* 🌐 [opentofu.org](https://opentofu.org) — OpenTofu docs and migration guide
* 🌐 [pulumi.com/docs](https://www.pulumi.com/docs/) — official Pulumi docs (3.140)
* 🌐 [registry.terraform.io](https://registry.terraform.io/) — providers + community modules (works for OpenTofu too)
* 🌐 [github.com/aquasecurity/tfsec](https://github.com/aquasecurity/tfsec) — IaC security scanner

**🎓 Quiz:** post-lecture quiz feeds the weeks 4–6 leaderboard window.
