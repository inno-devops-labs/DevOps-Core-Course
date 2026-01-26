# 📌 Lecture 11 — Secret Management: Protecting Your Crown Jewels

## 📍 Slide 1 – 🔐 Welcome to Secret Management

* 🌍 **Your Helm charts are beautiful** — but where do passwords go?
* 😰 Hardcoded secrets in code = ticking time bomb
* 🔐 **Secret management** = keeping credentials safe AND accessible
* 🎯 This lecture: from base64 encoding to enterprise-grade Vault

```mermaid
flowchart LR
  Bad[😱 Hardcoded] -->|🔐 Secrets| K8s[☸️ K8s Secrets]
  K8s -->|🏰 Enterprise| Vault[🔒 HashiCorp Vault]
  Vault --> Secure[✅ Secure Apps]
```

---

## 📍 Slide 2 – 🎯 What You Will Learn

* ✅ Understand why secret management matters
* ✅ Create and consume Kubernetes Secrets
* ✅ Recognize encoding vs encryption difference
* ✅ Integrate HashiCorp Vault with Kubernetes

**🎓 Learning Outcomes:**
| # | Outcome |
|---|---------|
| 1 | 🧠 Explain the risks of poor secret management |
| 2 | 🔍 Create K8s Secrets via kubectl and Helm |
| 3 | 🛠️ Configure Vault sidecar injection |
| 4 | 🗺️ Choose appropriate secret management strategy |

---

## 📍 Slide 3 – 📋 How This Lecture Works

* 🔐 **Security-first mindset** — think like an attacker
* 🎮 **Real breach scenarios** — learn from others' mistakes
* 📝 **3 quiz checkpoints**: PRE / MID / POST
* 🛠️ **Hands-on patterns**: Secrets, Vault, injection

**⏱️ Lecture Structure:**
```
Section 0: Introduction           → 📝 PRE Quiz
Section 1: The Secrets Problem
Section 2: Kubernetes Secrets
Section 3: Encoding vs Encryption → 📝 MID Quiz
Section 4: HashiCorp Vault
Section 5: Production Patterns    → 📝 POST Quiz
```

---

## 📍 Slide 4 – 💀 The Big Question

> 💬 *"The only truly secure system is one that is powered off, cast in a block of concrete and sealed in a lead-lined room with armed guards."* — Gene Spafford

**🔥 Shocking Stats:**
* 😱 **83%** of organizations have experienced credential theft
* 💸 Average cost of data breach: **$4.45 million** (2023)
* ⏱️ Average time to detect breach: **277 days**

> 🤔 **Think:** How many passwords are hardcoded in YOUR projects right now?

---

## 📍 Slide 5 – 📝 QUIZ — DEVOPS_L11_PRE

---

## 📍 Slide 6 – 🔥 Section 1: The Secrets Problem

* 🎯 **The Challenge:** Apps need credentials to function
* ⚔️ **The Conflict:** Security vs Convenience

```mermaid
flowchart LR
  subgraph 😰 Developer
    D1[🚀 Ship Fast]
    D2[🔧 Easy Access]
  end
  subgraph 🔐 Security
    S1[🛡️ Protect Data]
    S2[📋 Audit Access]
  end
  D1 <-->|⚔️ Tension| S1
  D2 <-->|⚔️ Tension| S2
```

> 🤔 **Discussion:** Have you ever committed a password to git?

---

## 📍 Slide 7 – 😱 The Hardcoding Horror

**❌ What developers actually do:**

```python
# ❌ BAD: Hardcoded in code
DATABASE_URL = "postgres://admin:SuperSecret123@db.prod.com/myapp"
API_KEY = "sk-1234567890abcdef"

# ❌ BAD: In docker-compose.yml committed to git
environment:
  - DB_PASSWORD=MyPassword123
```

**💥 What can go wrong:**
* 🔍 Git history is forever (even after deletion)
* 🌍 Public repos = public secrets
* 👥 Every developer has production passwords
* 📝 No audit trail of who accessed what

---

## 📍 Slide 8 – 💥 Real Breach: Uber 2016

**📰 What Happened:**
* 😱 Developers hardcoded AWS credentials in GitHub repo
* 🔓 Attackers found credentials, accessed S3 bucket
* 💾 **57 million** user records stolen
* 💸 **$148 million** settlement

```mermaid
flowchart LR
  A[👨‍💻 Dev commits AWS keys] --> B[🔍 Attacker finds repo]
  B --> C[🔓 Access S3 bucket]
  C --> D[💾 57M records stolen]
  D --> E[💸 $148M settlement]
```

> ⚠️ **Lesson:** Secrets in code = breach waiting to happen

---

## 📍 Slide 9 – 🔓 Environment Variables: Better but Not Enough

**✅ Better than hardcoding:**
```bash
export DATABASE_PASSWORD="secret123"
```

**❌ Still problematic:**
* 📋 `ps aux` can expose env vars
* 🐳 Docker inspect shows environment
* 📝 No encryption at rest
* 🔄 No rotation mechanism
* 👥 No access control

```bash
# Anyone on the system can see:
$ docker inspect myapp | grep -A 10 "Env"
```

> 🤔 **Think:** Where do YOUR environment variables come from?

---

## 📍 Slide 10 – 📊 The Cost of Poor Secret Management

| 🔥 Problem | 💥 Impact | 📊 Stats |
|------------|-----------|----------|
| 😱 Leaked credentials | 🔓 Unauthorized access | 83% of breaches |
| 🔄 No rotation | 📅 Stale passwords | Avg age: 2+ years |
| 👥 Shared secrets | 🕵️ No accountability | 65% share creds |
| 📝 No audit | 🤷 Unknown access | 70% can't audit |

**💡 The Solution Spectrum:**

```mermaid
flowchart LR
  A[😱 Hardcoded] --> B[🔧 Env Vars]
  B --> C[☸️ K8s Secrets]
  C --> D[🔒 Vault]
  style A fill:#ff6b6b
  style B fill:#ffd93d
  style C fill:#6bcb77
  style D fill:#4d96ff
```

---

## 📍 Slide 11 – ☸️ Section 2: Kubernetes Secrets

**🎯 What are K8s Secrets?**
* 📦 First-class Kubernetes objects for sensitive data
* 🔐 Separate from ConfigMaps (security-focused)
* 🚀 Native integration with pods

```mermaid
flowchart TD
  Secret[🔐 Secret] --> |Volume| Pod1[📦 Pod]
  Secret --> |Env Var| Pod2[📦 Pod]
  Secret --> |API| Pod3[📦 Pod]
```

**📋 Secret Types:**
* 🔑 `Opaque` — generic key-value
* 🐳 `docker-registry` — image pull credentials
* 🔒 `tls` — TLS certificates

---

## 📍 Slide 12 – 🛠️ Creating Secrets with kubectl

**📝 From literals:**
```bash
kubectl create secret generic db-creds \
  --from-literal=username=admin \
  --from-literal=password=SuperSecret123
```

**📁 From files:**
```bash
kubectl create secret generic tls-cert \
  --from-file=cert.pem \
  --from-file=key.pem
```

**👀 Viewing secrets:**
```bash
kubectl get secret db-creds -o yaml
# Data is base64 encoded

# Decode:
echo "U3VwZXJTZWNyZXQxMjM=" | base64 -d
# Output: SuperSecret123
```

---

## 📍 Slide 13 – ⚠️ The Base64 Trap

> ⚠️ **Critical Understanding:** Base64 is ENCODING, not ENCRYPTION!

```bash
# Encoding (reversible by anyone):
echo "password123" | base64
# cGFzc3dvcmQxMjMK

# Decoding (no key needed):
echo "cGFzc3dvcmQxMjMK" | base64 -d
# password123
```

**🔐 Encryption vs Encoding:**

| 🔄 Encoding | 🔐 Encryption |
|-------------|---------------|
| ✅ Reversible by anyone | 🔑 Needs key to decrypt |
| 📝 Not secure | 🔒 Mathematically secure |
| 🚀 Fast, no overhead | ⚡ Computational cost |
| 📦 Data format change | 🛡️ Confidentiality |

---

## 📍 Slide 14 – 📦 Consuming Secrets in Pods

**🔧 As environment variables:**
```yaml
env:
  - name: DB_PASSWORD
    valueFrom:
      secretKeyRef:
        name: db-creds
        key: password
```

**📁 As volume mount:**
```yaml
volumes:
  - name: secret-volume
    secret:
      secretName: db-creds
containers:
  - volumeMounts:
      - name: secret-volume
        mountPath: /etc/secrets
        readOnly: true
```

> 💡 **Best Practice:** Volume mounts are more secure than env vars (not visible in `docker inspect`)

---

## 📍 Slide 15 – 📊 Before vs After: Basic Secret Management

| 😱 Before (Hardcoded) | ✅ After (K8s Secrets) |
|-----------------------|------------------------|
| 📝 Secrets in code | 📦 Secrets in K8s API |
| 🌍 Visible in git history | 🔐 Separate from code |
| 👥 Everyone has access | 🛡️ RBAC controls |
| 🔄 Change = redeploy code | 🔧 Change secret only |
| 📋 No audit trail | 📝 K8s audit logs |

> 🤔 **Question:** Is K8s Secrets enough for production?

---

## 📍 Slide 16 – 🔒 Section 3: etcd Encryption

**😰 The Problem:**
* 🗄️ K8s stores secrets in etcd
* 📝 By default: base64 encoded only
* 🔓 etcd access = all secrets exposed

**✅ The Solution: Encryption at Rest**
```yaml
apiVersion: apiserver.config.k8s.io/v1
kind: EncryptionConfiguration
resources:
  - resources:
      - secrets
    providers:
      - aescbc:
          keys:
            - name: key1
              secret: <base64-encoded-key>
      - identity: {}
```

---

## 📍 Slide 17 – 🔐 K8s Secrets Limitations

**⚠️ Still Missing:**
* 🔄 **No automatic rotation** — manual process
* 📊 **Limited audit** — who accessed what?
* 🌍 **K8s-only** — what about non-K8s apps?
* 🔑 **Static secrets** — no dynamic generation
* 🏢 **No centralization** — per-cluster management

```mermaid
flowchart TD
  subgraph 😰 Limitations
    A[🔄 No Rotation]
    B[📊 Limited Audit]
    C[🌍 K8s Only]
    D[🔑 Static Only]
  end
  E[🏰 Need: Enterprise Solution] --> F[🔒 HashiCorp Vault]
```

---

## 📍 Slide 18 – 📝 QUIZ — DEVOPS_L11_MID

---

## 📍 Slide 19 – 🏰 Section 4: HashiCorp Vault

**🎯 What is Vault?**
* 🔐 Enterprise-grade secret management
* 🔑 Dynamic secret generation
* 📊 Complete audit logging
* 🔄 Automatic rotation
* 🌍 Platform agnostic

```mermaid
flowchart LR
  subgraph 🏰 Vault
    A[🔐 Secret Engine]
    B[🔑 Auth Methods]
    C[📋 Policies]
    D[📊 Audit]
  end
  K8s[☸️ Kubernetes] --> B
  B --> A
  A --> Apps[📦 Applications]
  D --> Logs[📝 Audit Logs]
```

---

## 📍 Slide 20 – 🏗️ Vault Architecture

```mermaid
flowchart TD
  subgraph 👥 Clients
    K8s[☸️ K8s Pods]
    CLI[💻 CLI]
    API[🔌 API]
  end
  subgraph 🏰 Vault Server
    Auth[🔑 Auth Methods]
    Policy[📋 Policies]
    Secrets[🔐 Secret Engines]
    Audit[📊 Audit Device]
  end
  subgraph 💾 Storage
    Backend[🗄️ Storage Backend]
  end
  K8s --> Auth
  CLI --> Auth
  API --> Auth
  Auth --> Policy
  Policy --> Secrets
  Secrets --> Backend
  Auth --> Audit
```

**🔑 Key Concepts:**
* 🔐 **Secret Engines** — where secrets live (KV, database, PKI)
* 🔑 **Auth Methods** — how clients authenticate
* 📋 **Policies** — who can access what

---

## 📍 Slide 21 – 🔑 Vault Auth Methods

| 🔑 Method | 📝 Description | 🎯 Use Case |
|-----------|----------------|-------------|
| ☸️ Kubernetes | Service account JWT | K8s pods |
| 🔐 AppRole | Role ID + Secret ID | CI/CD pipelines |
| 👤 Userpass | Username/password | Humans |
| 🌐 OIDC | SSO integration | Enterprise SSO |
| ☁️ AWS/GCP/Azure | Cloud IAM | Cloud workloads |

**☸️ Kubernetes Auth Flow:**
```mermaid
sequenceDiagram
  Pod->>Vault: JWT token (ServiceAccount)
  Vault->>K8s API: Validate token
  K8s API->>Vault: Token valid ✅
  Vault->>Pod: Vault token + secrets
```

---

## 📍 Slide 22 – 📋 Vault Policies

**🎯 Policies control access:**
```hcl
# Allow read on specific path
path "secret/data/myapp/*" {
  capabilities = ["read", "list"]
}

# Deny access to admin secrets
path "secret/data/admin/*" {
  capabilities = ["deny"]
}
```

**🛡️ Principle of Least Privilege:**
* ✅ Apps only access their secrets
* ✅ Read-only where possible
* ✅ Separate policies per environment

---

## 📍 Slide 23 – 💉 Vault Agent Sidecar Injection

**🎯 The Pattern:**
* 📦 Vault Agent runs as sidecar container
* 🔄 Automatically fetches and renews secrets
* 📁 Writes secrets to shared volume
* 🚀 App reads from filesystem

```mermaid
flowchart LR
  subgraph 📦 Pod
    App[🚀 App Container]
    Agent[🔐 Vault Agent]
    Vol[📁 Shared Volume]
  end
  Vault[🏰 Vault Server]
  Agent -->|🔑 Auth| Vault
  Vault -->|🔐 Secrets| Agent
  Agent -->|📝 Write| Vol
  App -->|📖 Read| Vol
```

---

## 📍 Slide 24 – 🏷️ Vault Annotations

**📝 Enable injection:**
```yaml
metadata:
  annotations:
    vault.hashicorp.com/agent-inject: "true"
    vault.hashicorp.com/role: "myapp"
    vault.hashicorp.com/agent-inject-secret-config: "secret/data/myapp/config"
```

**📁 Secrets appear at:**
```
/vault/secrets/config
```

**🔧 Template for custom format:**
```yaml
vault.hashicorp.com/agent-inject-template-config: |
  {{- with secret "secret/data/myapp/config" -}}
  DB_PASSWORD={{ .Data.data.password }}
  {{- end -}}
```

---

## 📍 Slide 25 – 🚀 Vault in Kubernetes: Full Flow

```mermaid
sequenceDiagram
  participant Pod
  participant Injector as Vault Injector
  participant Agent as Vault Agent
  participant Vault

  Pod->>Injector: Pod created with annotations
  Injector->>Pod: Inject sidecar container
  Agent->>Vault: Authenticate (K8s JWT)
  Vault->>Agent: Return Vault token
  Agent->>Vault: Request secrets
  Vault->>Agent: Return secrets
  Agent->>Pod: Write to /vault/secrets/
  Pod->>Pod: App reads secrets
```

---

## 📍 Slide 26 – 🔄 Section 5: Dynamic Secrets

**🎯 Static vs Dynamic:**

| 🔑 Static Secrets | 🔄 Dynamic Secrets |
|-------------------|-------------------|
| 📝 Created manually | 🤖 Generated on-demand |
| ♾️ Live forever | ⏱️ Short TTL |
| 👥 Shared | 👤 Unique per request |
| 🔄 Manual rotation | 🔄 Auto-expires |

**💡 Example: Database credentials**
```bash
vault read database/creds/readonly
# Key             Value
# lease_id        database/creds/readonly/abc123
# lease_duration  1h
# username        v-kubernetes-readonly-xyz789
# password        A1b2C3d4E5f6G7h8
```

---

## 📍 Slide 27 – 📊 Secret Management Comparison

| 🔧 Feature | 🔓 Env Vars | ☸️ K8s Secrets | 🏰 Vault |
|------------|-------------|----------------|----------|
| 🔐 Encryption | ❌ None | ⚠️ Optional | ✅ Always |
| 🔄 Rotation | ❌ Manual | ❌ Manual | ✅ Auto |
| 📊 Audit | ❌ None | ⚠️ Basic | ✅ Full |
| 🔑 Dynamic | ❌ No | ❌ No | ✅ Yes |
| 🌍 Multi-platform | ✅ Yes | ❌ K8s only | ✅ Yes |
| 📈 Complexity | 🟢 Low | 🟡 Medium | 🔴 High |

---

## 📍 Slide 28 – 🗺️ Course Context: Where Secrets Fit

```mermaid
flowchart TD
  subgraph 🏗️ Foundation
    L2[📦 Lab 2: Docker]
    L10[⛵ Lab 10: Helm]
  end
  subgraph 🔐 Security
    L11[🔒 Lab 11: Secrets]
  end
  subgraph 📋 Config
    L12[📁 Lab 12: ConfigMaps]
  end
  subgraph 🚀 Deployment
    L13[🔄 Lab 13: ArgoCD]
  end
  L2 --> L10
  L10 --> L11
  L11 --> L12
  L12 --> L13
  style L11 fill:#4d96ff
```

---

## 📍 Slide 29 – 📈 Security Metrics

| 📊 Metric | 📝 Description | 🎯 Target |
|-----------|----------------|-----------|
| 🔄 Secret Age | Time since rotation | < 90 days |
| 📊 Access Audit | % of accesses logged | 100% |
| 🔐 Encryption | % secrets encrypted | 100% |
| 👥 Shared Secrets | Secrets used by >1 app | 0 |
| ⏱️ TTL Compliance | Secrets with TTL | > 80% |

> 🤔 **Question:** How would you measure secret security in your organization?

---

## 📍 Slide 30 – ✅ Secret Management Best Practices

**🛡️ The Golden Rules:**

1. 🚫 **Never commit secrets** to version control
2. 🔄 **Rotate regularly** — automate where possible
3. 📋 **Audit everything** — know who accessed what
4. 🔐 **Encrypt at rest** — etcd encryption minimum
5. 👤 **Least privilege** — only what's needed
6. ⏱️ **Short-lived** — dynamic secrets when possible

```mermaid
flowchart LR
  A[🔐 Encrypt] --> B[🔄 Rotate]
  B --> C[📋 Audit]
  C --> D[👤 Least Privilege]
  D --> A
```

---

## 📍 Slide 31 – 👨‍💻 Day in the Life: Secret Management

**☀️ Morning:**
* ☕ Check Vault audit logs for anomalies
* 🔄 Review expiring secrets dashboard
* 📋 Approve new secret access requests

**🌤️ Afternoon:**
* 🛠️ Help dev team configure Vault injection
* 📝 Update policies for new microservice
* 🔐 Rotate database credentials (automated)

**🌙 Evening:**
* 📊 Review daily access report
* 🔔 Set up alerts for unusual patterns
* 📚 Document new secret paths

---

## 📍 Slide 32 – 👥 Roles & Secret Management

| 👤 Role | 🔐 Secret Responsibilities |
|---------|---------------------------|
| 🧑‍💻 Developer | Use secrets correctly, never commit |
| 🔧 DevOps | Configure injection, manage policies |
| 🛡️ Security | Audit access, define requirements |
| 🏗️ Platform | Maintain Vault infrastructure |
| 📋 Compliance | Ensure rotation, audit trails |

> 💡 **Common Thread:** Everyone shares responsibility for secrets

---

## 📍 Slide 33 – 🏢 Real-World: How Companies Handle Secrets

**🎬 Netflix:**
* 🔐 Custom secret management platform
* 🔄 Automatic rotation every 24 hours
* 📊 Real-time access monitoring

**📦 Shopify:**
* 🏰 HashiCorp Vault at scale
* 🔑 Dynamic database credentials
* 👤 Per-service unique credentials

**🚗 Uber:**
* 📚 Learned from 2016 breach
* 🔐 Zero hardcoded secrets policy
* 🤖 Automated secret scanning in CI

---

## 📍 Slide 34 – 🎯 Decision Framework: Choosing a Solution

```mermaid
flowchart TD
  Start[🤔 Need Secret Management] --> Q1{Small team?<br/>Simple app?}
  Q1 -->|Yes| K8s[☸️ K8s Secrets + etcd encryption]
  Q1 -->|No| Q2{Multi-platform?<br/>Compliance needs?}
  Q2 -->|Yes| Vault[🏰 HashiCorp Vault]
  Q2 -->|No| Q3{Cloud-native only?}
  Q3 -->|Yes| Cloud[☁️ Cloud Secret Manager]
  Q3 -->|No| Vault
```

---

## 📍 Slide 35 – 📝 Key Takeaways

1. 🚫 **Never hardcode secrets** — it's a breach waiting to happen
2. 🔄 **Base64 ≠ encryption** — K8s Secrets need etcd encryption
3. 🏰 **Vault for enterprise** — when you need rotation, audit, dynamic
4. 💉 **Sidecar injection** — cleanest pattern for K8s + Vault
5. 📋 **Audit everything** — you can't secure what you can't see

> 💬 *"Security is not a product, but a process."* — Bruce Schneier

---

## 📍 Slide 36 – 🔄 Mindset Shift

| 😰 Old Mindset | 🚀 New Mindset |
|----------------|----------------|
| "Hardcode for convenience" | "Secrets are separate from code" |
| "Base64 is secure enough" | "Encryption at rest is mandatory" |
| "Rotate when breached" | "Rotate proactively and automatically" |
| "Trust developers" | "Least privilege for everyone" |
| "Hope nobody finds it" | "Assume breach, audit everything" |

> 🤔 **Which mindset do you currently have?**

---

## 📍 Slide 37 – ✅ Your Progress

**🎓 You can now:**
- [x] 🧠 Explain why secret management matters
- [x] 🔍 Create K8s Secrets via kubectl and Helm
- [x] ⚠️ Recognize encoding vs encryption
- [x] 🛠️ Configure Vault sidecar injection
- [x] 🗺️ Choose appropriate secret management strategy

**🚀 Ready for:** Lab 11 — Kubernetes Secrets & HashiCorp Vault

---

## 📍 Slide 38 – 📝 QUIZ — DEVOPS_L11_POST

---

## 📍 Slide 39 – 🚀 What's Next

**📅 Next Lecture:** Configuration & Persistent Storage
* 📁 ConfigMaps for non-sensitive config
* 💾 Persistent Volumes for data
* 🔧 Mounting strategies

```mermaid
flowchart LR
  Now[🔐 Secrets] --> Next[📁 ConfigMaps]
  Next --> Storage[💾 Storage]
  Storage --> GitOps[🔄 GitOps]
```

> 💪 *"You've secured the secrets. Now let's configure everything else!"*

---

## 📚 Resources

**📖 Books:**
* "HashiCorp Vault: Securing Secrets" — by various authors
* "Kubernetes Security" — by Liz Rice
* "Zero Trust Networks" — by Evan Gilman

**🔗 Links:**
* [Vault Documentation](https://developer.hashicorp.com/vault/docs)
* [K8s Secrets Best Practices](https://kubernetes.io/docs/concepts/security/secrets-good-practices/)
* [OWASP Secrets Management](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html)
