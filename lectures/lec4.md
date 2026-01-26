# 📌 Lecture 4 — Infrastructure as Code: From Snowflakes to Cattle

## 📍 Slide 1 – 🚀 Welcome to Infrastructure as Code

* 🌍 **Infrastructure used to be physical** — racks, cables, manual configuration
* 😰 Manual setup leads to inconsistency, drift, and undocumented "snowflakes"
* 🏗️ **Infrastructure as Code (IaC)** treats infrastructure like software
* 🎯 This lecture: learn to define, version, and automate your infrastructure

```mermaid
flowchart LR
  Manual[🔧 Manual Setup] -->|IaC| Code[📝 Code-Defined]
  Code --> Reproducible[🔄 Reproducible Infrastructure]
```

---

## 📍 Slide 2 – 🎯 What You Will Learn

* ✅ Understand Infrastructure as Code principles
* ✅ Compare declarative vs imperative IaC approaches
* ✅ Apply Terraform workflows to real cloud infrastructure
* ✅ Manage infrastructure state securely

**🎓 Learning Outcomes:**
| # | Outcome |
|---|---------|
| 1 | 🧠 Define IaC and explain its benefits |
| 2 | 🔍 Distinguish between Terraform and Pulumi |
| 3 | 🛠️ Write basic Terraform configurations |
| 4 | 🗺️ Understand state management and security |

---

## 📍 Slide 3 – 📋 How This Lecture Works

* 📚 **Concepts + Code examples** — hands-on focus
* 🎮 **Real-world scenarios** — cloud provisioning challenges
* 📝 **3 quiz checkpoints**: PRE / MID / POST
* 🛠️ **Tool comparison**: Terraform vs Pulumi

**⏱️ Lecture Structure:**
```
Section 0: Introduction (now)     → 📝 PRE Quiz
Section 1: The Infrastructure Problem
Section 2: IaC Fundamentals
Section 3: Terraform Deep Dive    → 📝 MID Quiz
Section 4: State & Security
Section 5: Real World IaC
Section 6: Reflection             → 📝 POST Quiz
```

---

## 📍 Slide 4 – ❓ The Big Question

* 📊 **73%** of organizations report configuration drift as a major issue
* ⏱️ Average time to provision a server manually: **hours to days**
* 💥 Most outages caused by **configuration changes**

> 💬 *"It works in staging but not production"* — Every ops engineer, ever

**🤔 Think about it:**
* How do you recreate your production environment?
* What happens when the person who set it up leaves?
* Can you spin up a new environment in minutes?

---

## 📍 Slide 5 – 📝 QUIZ — DEVOPS_L4_PRE

---

## 📍 Slide 6 – 🔥 Section 1: The Infrastructure Problem

* 🐶 **Pet Servers** = unique, hand-crafted, irreplaceable
* 🔧 Manual configuration via SSH and console clicks
* 📋 Documentation gets outdated immediately
* 💥 Result: **snowflake infrastructure** — no two servers are the same

```mermaid
flowchart LR
  Server1[🖥️ Server 1: Ubuntu 20 + patches]
  Server2[🖥️ Server 2: Ubuntu 22 + different patches]
  Server3[🖥️ Server 3: ???]
  Server1 --> Chaos[😱 Configuration Chaos]
  Server2 --> Chaos
  Server3 --> Chaos
```

---

## 📍 Slide 7 – 🐶 Pets vs Cattle

* 🐶 **Pets**: Named servers, nursed back to health when sick
* 🐄 **Cattle**: Numbered, identical, replaced when broken
* 🌍 Cloud-native = cattle mindset

```mermaid
flowchart TD
  subgraph 🐶 Pets
    P1[web-prod-01]
    P2[db-master]
    P3[app-legacy]
  end
  subgraph 🐄 Cattle
    C1[instance-001]
    C2[instance-002]
    C3[instance-003]
  end
  Pets -->|😰 Unique, fragile| Problem[Hard to scale]
  Cattle -->|🔄 Identical, disposable| Solution[Easy to scale]
```

> 🤔 **Think:** Are your servers pets or cattle?

---

## 📍 Slide 8 – 😱 Configuration Drift

* 📅 Server configured once, modified many times
* 🔧 "Quick fixes" applied directly in production
* 📋 No record of what changed
* 💀 Disaster recovery = guesswork

```mermaid
flowchart TD
  Initial[✅ Initial Setup] --> Month1[📅 Month 1: Hotfix applied]
  Month1 --> Month3[📅 Month 3: Security patch]
  Month3 --> Month6[📅 Month 6: Unknown changes]
  Month6 --> Drift[😱 Configuration Drift]
  Drift --> Unknown[❓ What's actually running?]
```

**📊 The Numbers:**
* 🔍 **65%** of downtime caused by configuration issues
* ⏱️ Average recovery time: **4+ hours**
* 💰 Cost per hour of downtime: **$300,000** (enterprise)

---

## 📍 Slide 9 – 😨 The Bus Factor

* 👤 One person knows how the infrastructure works
* 🚌 They leave, get sick, or go on vacation
* 🙈 Nobody can recreate or fix the environment
* 💀 Business continuity at risk

> ⚠️ **Bus Factor = 1** means your infrastructure is fragile

**😰 Signs of Low Bus Factor:**
* 🔇 "Ask John, he set that up"
* 📝 Documentation is outdated or missing
* 🐌 Changes require specific people
* 🚪 Knowledge walks out the door

**💬 Discussion:** What's your infrastructure bus factor?

---

## 📍 Slide 10 – 💸 The Cost of Manual Infrastructure

| 🔥 Problem | 💥 Impact |
|------------|-----------|
| 🐢 Slow provisioning | Days to spin up new environments |
| 📋 Manual processes | Human error, inconsistency |
| 👉 No audit trail | Compliance violations |
| 🙈 Configuration drift | Unpredictable behavior |

**📈 Real Numbers:**
* 🏢 **Manual provisioning**: 2-4 hours per server
* 🚀 **With IaC**: 2-4 minutes per server
* 🔄 **Environment recreation**: hours vs seconds

**💰 Time Cost:**
* 👨‍💻 Engineer time: **$75-150/hour**
* 🖥️ 10 servers manually: **$1,500-3,000**
* 🤖 10 servers with IaC: **$15-30**

---

## 📍 Slide 11 – 💡 Section 2: What Infrastructure as Code Is

* 📝 **IaC** = defining infrastructure in version-controlled files
* 🔄 Infrastructure becomes **reproducible** and **auditable**
* 🚫 No more clicking through consoles
* 🎯 Same infrastructure, every time

```mermaid
flowchart LR
  Code[📝 Code] -->|🔄 Apply| Cloud[☁️ Cloud]
  Cloud --> Infra[🏗️ Infrastructure]
  Code -->|📜 Git| Version[Version Control]
```

**📖 Definition:**
> *Infrastructure as Code is the practice of managing and provisioning infrastructure through machine-readable configuration files rather than through manual processes or interactive tools.*

---

## 📍 Slide 12 – 🚫 What IaC is NOT

| ❌ Myth | ✅ Reality |
|---------|-----------|
| "Just automation scripts" | 📝 Declarative desired state |
| "Only for cloud" | 🖥️ Works for any infrastructure |
| "Replaces ops people" | 🤝 Empowers ops teams |
| "Too complex for small teams" | 🎯 Benefits scale to any size |
| "One-time setup" | 🔄 Continuous lifecycle management |

> 🔥 **Hot take:** If you can't recreate your infrastructure from code, you don't have IaC.

**🎯 IaC is about:**
* 🧠 Declarative definitions
* 🤝 Team collaboration on infrastructure
* 🔄 Repeatable, consistent environments
* 📊 Audit trails and compliance

---

## 📍 Slide 13 – 🔀 Declarative vs Imperative

```mermaid
flowchart TD
  subgraph Declarative
    D1[📝 Define desired state]
    D2[🤖 Tool figures out how]
    D1 --> D2
  end
  subgraph Imperative
    I1[📝 Define exact steps]
    I2[🔧 Execute step by step]
    I1 --> I2
  end
```

| 📋 Aspect | 🌍 Declarative | 🔧 Imperative |
|-----------|---------------|---------------|
| 📝 What you write | Desired end state | Exact steps |
| 🛠️ Tool | Terraform, CloudFormation | Pulumi, Scripts |
| 🔄 Idempotency | Built-in | You implement |
| 📚 Example | "3 VMs exist" | "Create VM 1, 2, 3" |

**📚 Source:** Terraform documentation

---

## 📍 Slide 14 – 🛠️ IaC Tool Landscape

```mermaid
graph TD
  IaC[🏗️ Infrastructure as Code]
  IaC --> Prov[📦 Provisioning]
  IaC --> Config[⚙️ Configuration]
  Prov --> Terraform[🌍 Terraform]
  Prov --> Pulumi[📦 Pulumi]
  Prov --> Cloud[☁️ CloudFormation/ARM]
  Config --> Ansible[🔧 Ansible]
  Config --> Chef[👨‍🍳 Chef]
  Config --> Puppet[🎭 Puppet]
```

| 🛠️ Tool | 🎯 Focus | 📝 Language |
|---------|---------|------------|
| 🌍 **Terraform** | Provisioning | HCL (declarative) |
| 📦 **Pulumi** | Provisioning | Python, TS, Go |
| 🔧 **Ansible** | Configuration | YAML |
| ☁️ **CloudFormation** | AWS only | YAML/JSON |

---

## 📍 Slide 15 – ⚡ Before vs After IaC

| 😰 Before | 🚀 After |
|----------|---------|
| 📅 Days to provision | ⚡ Minutes to provision |
| 📋 Manual documentation | 📝 Code IS documentation |
| 👉 "Who changed that?" | 📜 Git history shows all |
| 😨 Fear of recreation | 💪 Confident rebuilds |
| 🐶 Unique snowflakes | 🐄 Identical cattle |
| 🙅 "Don't touch prod" | 🔄 Infrastructure is disposable |

> 🤔 How confident are you in recreating your infrastructure?

---

## 📍 Slide 16 – 🎮 Section 3: Terraform Deep Dive

## 🌍 Why Terraform?

* 🌐 **Multi-cloud**: AWS, GCP, Azure, Yandex, and 3000+ providers
* 📝 **HCL**: Human-readable configuration language
* 🔄 **State management**: Tracks what exists
* 🏢 **Industry standard**: Most widely adopted IaC tool

**🎮 Let's build infrastructure.**

---

## 📍 Slide 17 – 📝 Terraform Workflow

```mermaid
flowchart LR
  Write[📝 Write] --> Init[🔧 Init]
  Init --> Plan[📋 Plan]
  Plan --> Apply[🚀 Apply]
  Apply --> Destroy[💥 Destroy]
```

* 📝 **Write**: Define resources in `.tf` files
* 🔧 **Init**: Download provider plugins
* 📋 **Plan**: Preview changes (dry run)
* 🚀 **Apply**: Create/update infrastructure
* 💥 **Destroy**: Remove all resources

**🛠️ Commands:**
```bash
terraform init      # Download providers
terraform plan      # Preview changes
terraform apply     # Apply changes
terraform destroy   # Remove everything
```

---

## 📍 Slide 18 – 🧱 Terraform Building Blocks

```mermaid
flowchart TD
  Config[📁 Configuration]
  Config --> Provider[☁️ Provider]
  Config --> Resource[🏗️ Resource]
  Config --> Variable[📊 Variable]
  Config --> Output[📤 Output]
  Config --> Data[🔍 Data Source]
```

* ☁️ **Provider**: Cloud API connection (AWS, GCP, Yandex)
* 🏗️ **Resource**: Infrastructure component (VM, network, firewall)
* 📊 **Variable**: Configurable inputs
* 📤 **Output**: Values to display/export
* 🔍 **Data Source**: Query existing infrastructure

---

## 📍 Slide 19 – 💻 Terraform Example: VM Creation

```hcl
# ☁️ Provider configuration
provider "yandex" {
  zone = "ru-central1-a"
}

# 🏗️ Virtual machine resource
resource "yandex_compute_instance" "web" {
  name        = "web-server"
  platform_id = "standard-v2"

  resources {
    cores  = 2
    memory = 2
  }

  boot_disk {
    initialize_params {
      image_id = "fd8vmcue7aajqdge3bp0"  # Ubuntu 22.04
    }
  }
}
```

**🎯 Result:** One command creates a VM in the cloud

---

## 📍 Slide 20 – 📊 Variables and Outputs

```hcl
# 📊 Input variables
variable "instance_count" {
  description = "Number of VMs to create"
  type        = number
  default     = 1
}

variable "environment" {
  description = "Environment name"
  type        = string
}

# 📤 Output values
output "vm_ip" {
  description = "Public IP of the VM"
  value       = yandex_compute_instance.web.network_interface.0.nat_ip_address
}
```

**🛠️ Usage:**
```bash
terraform apply -var="instance_count=3" -var="environment=prod"
```

---

## 📍 Slide 21 – 🔄 Terraform Plan

```mermaid
flowchart LR
  Code[📝 Config] --> Plan[📋 terraform plan]
  State[📦 State] --> Plan
  Plan --> Diff[🔍 Difference]
  Diff --> Preview[👀 What will change?]
```

**📋 Plan Output Example:**
```
# yandex_compute_instance.web will be created
+ resource "yandex_compute_instance" "web" {
    + name        = "web-server"
    + platform_id = "standard-v2"
    + status      = (known after apply)

    + resources {
        + cores  = 2
        + memory = 2
      }
  }

Plan: 1 to add, 0 to change, 0 to destroy.
```

**🎯 Always review the plan before applying!**

---

## 📍 Slide 22 – 📦 Pulumi Alternative

```mermaid
flowchart LR
  Terraform[🌍 Terraform] -->|HCL| Declarative[📝 Declarative]
  Pulumi[📦 Pulumi] -->|Python/TS/Go| Imperative[💻 Imperative]
```

**📦 Pulumi Python Example:**
```python
import pulumi
import pulumi_yandex as yandex

# 🏗️ Create VM using Python
vm = yandex.ComputeInstance("web",
    name="web-server",
    platform_id="standard-v2",
    resources=yandex.ComputeInstanceResourcesArgs(
        cores=2,
        memory=2,
    ))

# 📤 Export IP address
pulumi.export("ip", vm.network_interfaces[0].nat_ip_address)
```

**🎯 Same result, real programming language**

---

## 📍 Slide 23 – ⚖️ Terraform vs Pulumi

| 📋 Aspect | 🌍 Terraform | 📦 Pulumi |
|-----------|-------------|----------|
| 📝 Language | HCL (domain-specific) | Python, TS, Go, C# |
| 📚 Learning curve | New syntax to learn | Familiar languages |
| 🔄 Logic | Limited (count, for_each) | Full programming |
| 🧪 Testing | External tools | Native unit tests |
| 📦 State | Local or S3 | Pulumi Cloud (free tier) |
| 🔐 Secrets | Plain in state | Encrypted by default |

> ❓ **When to use which?**
> * 🌍 **Terraform**: Larger community, more examples, declarative simplicity
> * 📦 **Pulumi**: Complex logic, existing codebase, testing requirements

---

## 📍 Slide 24 – 🔐 Security Best Practices

```yaml
# ❌ NEVER do this
provider "aws" {
  access_key = "AKIAIOSFODNN7EXAMPLE"    # 💀 Hardcoded secret!
  secret_key = "wJalrXUtnFEMI/..."       # 💀 Hardcoded secret!
}

# ✅ Use environment variables
# export AWS_ACCESS_KEY_ID="..."
# export AWS_SECRET_ACCESS_KEY="..."
provider "aws" {
  # Automatically uses env vars
}
```

**🔐 Security Rules:**
* 🚫 Never commit secrets to Git
* 📁 Use `.gitignore` for state and tfvars
* 🔑 Use environment variables or secret managers
* 🔒 Encrypt state file at rest

---

## 📍 Slide 25 – 📝 QUIZ — DEVOPS_L4_MID

---

## 📍 Slide 26 – 📦 Section 4: State Management

## 🗃️ What is Terraform State?

* 📝 Maps configuration to real-world resources
* 🔍 Tracks what Terraform manages
* 🔄 Determines what changes are needed
* ⚠️ Contains sensitive data

```mermaid
flowchart LR
  Config[📝 Config Files] --> TF[🌍 Terraform]
  State[📦 State File] --> TF
  TF --> Cloud[☁️ Real Infrastructure]
  Cloud --> State
```

---

## 📍 Slide 27 – 📁 State File Contents

```json
{
  "version": 4,
  "terraform_version": "1.9.0",
  "resources": [
    {
      "type": "yandex_compute_instance",
      "name": "web",
      "instances": [
        {
          "attributes": {
            "id": "fhm1234567890",
            "name": "web-server",
            "network_interface": [
              {
                "ip_address": "192.168.1.10",
                "nat_ip_address": "51.250.1.100"
              }
            ]
          }
        }
      ]
    }
  ]
}
```

**⚠️ Never edit state manually!**

---

## 📍 Slide 28 – 🌐 Remote State

```mermaid
flowchart TD
  Dev1[👨‍💻 Developer 1] --> Remote[🌐 Remote State]
  Dev2[👨‍💻 Developer 2] --> Remote
  Dev3[👨‍💻 Developer 3] --> Remote
  Remote --> Cloud[☁️ Cloud Infrastructure]
```

**🌐 Remote State Benefits:**
* 🤝 Team collaboration
* 🔒 Locking prevents conflicts
* 🔐 Encrypted at rest
* 📜 Versioning and backup

**📦 Backend Options:**
* ☁️ **S3/GCS**: Object storage
* 🏢 **Terraform Cloud**: HashiCorp managed
* 🔐 **Consul**: HashiCorp Consul

---

## 📍 Slide 29 – 📊 IaC Metrics

| 📊 Metric | 📏 Measures | 🏆 Target |
|-----------|------------|---------|
| ⏱️ **Provisioning Time** | Time to create env | < 15 minutes |
| 🔄 **Environment Parity** | Dev = Staging = Prod | 100% |
| ❌ **Drift Detection** | Config drift incidents | 0 per month |
| 📜 **Audit Compliance** | Changes tracked in Git | 100% |

> 📚 These metrics indicate IaC maturity.

**🤔 Question:** How long does it take to spin up a new environment?

---

## 📍 Slide 30 – 🌊 From Snowflakes to Cattle

```mermaid
flowchart LR
  subgraph 😱 Snowflakes
    Manual[🔧 Manual Setup]
    Unique[❄️ Unique Servers]
    Drift[📋 Configuration Drift]
  end
  subgraph 🐄 Cattle
    Code[📝 Code-Defined]
    Identical[🔄 Identical Servers]
    Reproducible[✅ Reproducible]
  end
  Snowflakes -->|🚀 IaC| Cattle
```

**🎯 Goal State:**
* ⚡ Any environment recreatable in minutes
* 🔄 All changes through code review
* 📈 Teams deploy infrastructure confidently

---

## 📍 Slide 31 – 🏢 Section 5: IaC in Real Life

## 📅 A Day with IaC

**☀️ Morning:**
* 📊 Review infrastructure PR
* 👀 Check `terraform plan` output
* ✅ Approve and merge

**🌤️ Afternoon:**
* 🚨 Need new test environment
* 🔧 Copy `terraform.tfvars`
* 🚀 `terraform apply` — **done in 10 minutes**

**🌙 Evening:**
* 🗑️ `terraform destroy` test environment
* 💰 No resources running overnight

---

## 📍 Slide 32 – 👥 IaC Team Workflow

| 👤 Role | 🎯 IaC Responsibility |
|---------|----------------------|
| 🔧 **DevOps/Platform** | Write and maintain IaC modules |
| 👨‍💻 **Developer** | Use modules, request infrastructure |
| 🛡️ **Security** | Review IaC for compliance |
| 📊 **FinOps** | Monitor infrastructure costs |

**🔗 Common Workflow:**
* 📝 Create branch with IaC changes
* 🔍 CI runs `terraform plan`
* 👀 Team reviews the plan
* ✅ Merge triggers `terraform apply`

---

## 📍 Slide 33 – 🤝 GitOps for Infrastructure

```mermaid
flowchart TD
  Dev[👨‍💻 Developer] -->|📝 PR| Git[🐙 Git Repository]
  Git -->|🔄 CI/CD| Plan[📋 Terraform Plan]
  Plan -->|👀 Review| Approve[✅ Approve]
  Approve -->|🚀 Merge| Apply[🌍 Terraform Apply]
  Apply --> Cloud[☁️ Infrastructure]
```

**🤝 GitOps Practices:**
* 📟 All changes through pull requests
* 📝 Plan output in PR comments
* 👥 Required approvals
* 🔓 Protected main branch

---

## 📍 Slide 34 – 📈 Career Path: IaC Skills

```mermaid
flowchart LR
  Junior[🌱 Junior: Basic Terraform] --> Mid[💼 Mid: Modules & CI/CD]
  Mid --> Senior[⭐ Senior: Multi-cloud & Architecture]
  Senior --> Principal[🏆 Principal: Platform Strategy]
```

**🛠️ Skills to Build:**
* 🌍 Terraform HCL fluency
* ☁️ Cloud provider APIs
* 🔐 Security best practices
* 📦 Module design
* 🔄 CI/CD integration

---

## 📍 Slide 35 – 🌍 Real Company Examples

**🏢 HashiCorp Customers:**
* 🏦 **Stripe**: Terraform for AWS infrastructure
* 🎮 **Riot Games**: Multi-cloud with Terraform
* 🛒 **Shopify**: Thousands of resources managed

**☁️ Cloud Native:**
* 🔍 **Google**: Uses Terraform internally
* 📦 **Spotify**: IaC for Kubernetes infrastructure
* 🎬 **Netflix**: Custom tooling built on IaC principles

**📊 Stats:**
* 🌍 **2M+** Terraform users worldwide
* 📦 **3000+** providers available
* 🏢 **Fortune 500**: 85% use IaC

---

## 📍 Slide 36 – 🎯 Section 6: Reflection

## 📝 Key Takeaways

1. 🏗️ **IaC = Infrastructure defined in code**
2. 🐄 **Cattle not pets** — servers are disposable
3. 📝 **Version control everything** — Git for infrastructure
4. 📋 **Plan before apply** — always review changes
5. 🔐 **Never commit secrets** — use environment variables

> 💡 If you can't recreate it from code, it's not really infrastructure as code.

---

## 📍 Slide 37 – 🧠 The Mindset Shift

| 😰 Old Mindset | 🚀 IaC Mindset |
|---------------|------------------|
| 🙅 "SSH and fix it" | 📝 "Change the code" |
| 🚫 "Don't touch that server" | 💪 "Destroy and recreate" |
| 👉 "Who set this up?" | 📜 "Git blame shows history" |
| 😨 "Manual is faster" | ⚡ "Automation is faster at scale" |
| 💻 "Works on my cloud" | 🌍 "Works on any cloud" |

> ❓ Which mindset describes your team?

---

## 📍 Slide 38 – ✅ Your Progress

## 🎓 What You Now Understand

* ✅ Why IaC is essential for modern infrastructure
* ✅ The difference between declarative and imperative
* ✅ How Terraform and Pulumi work
* ✅ State management and security practices
* ✅ Real-world IaC workflows

> 🚀 **You're ready for Lab 4: Terraform & Pulumi**

---

## 📍 Slide 39 – 📝 QUIZ — DEVOPS_L4_POST

---

## 📍 Slide 40 – 🚀 What Comes Next

## 📚 Next Lecture: Configuration Management with Ansible

* 🔧 Ansible fundamentals
* 📦 Roles and playbooks
* 🤖 Automating server configuration
* 💻 Hands-on: Deploying Docker with Ansible

**🎉 Your IaC journey begins.**

> 🐄 From snowflakes to cattle — one terraform apply at a time.

```mermaid
flowchart LR
  You[👤 You] --> IaC[🏗️ IaC Skills]
  IaC --> Reproducible[🔄 Reproducible Infra]
  Reproducible --> Career[🚀 Career Growth]
```

**👋 See you in the next lecture!**

---

## 📚 Resources & Further Reading

**📕 Books:**
* 📖 *Terraform: Up & Running* — Yevgeniy Brikman
* 📖 *Infrastructure as Code* — Kief Morris
* 📖 *The DevOps Handbook* — Gene Kim et al.

**🔗 Links:**
* 🌐 [Terraform Documentation](https://developer.hashicorp.com/terraform/docs)
* 🌐 [Pulumi Documentation](https://www.pulumi.com/docs/)
* 🌐 [Terraform Registry](https://registry.terraform.io/)

---
