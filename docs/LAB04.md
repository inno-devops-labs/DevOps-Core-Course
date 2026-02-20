# Lab 04 — Infrastructure as Code (Terraform & Pulumi)

## 1. Cloud Provider & Infrastructure

**Cloud provider:** Google Cloud Platform (GCP)

**Rationale:** Already had an account and familiar interface. GCP offers free tier (e2-micro), good documentation, and integration with Terraform/Pulumi.

**Instance type:** e2-micro (free tier) — 2 vCPU (shared), 1 GB RAM

**Region/Zone:** us-central1-a — zone is part of GCP always-free tier

**Cost:** $0 (free tier)

**Resources created:**

- VM instance (lab04-vm)
- Firewall (lab04-vm-firewall) — ports 22, 80, 5000
- Public IP (via access_config)

---

## 2. Terraform Implementation

**Terraform version:** v1.14.5

**Project structure:**

```
terraform/
├── main.tf          # Provider, firewall, VM
├── variables.tf     # project_id, region, zone, machine_type, ssh_public_key_path
├── outputs.tf       # instance_public_ip, ssh_command
├── terraform.tfvars # Values (gitignored)
└── Outputs/         # Command outputs
```

**Key decisions:** Variables for project_id, zone, machine_type. Firewall with source_ranges 0.0.0.0/0 (dynamic IP). SSH key via metadata.

**Challenges:** None.

**Public IP :** 35.193.180.39

**Terminal output:**

- [terraform init](terraform/Outputs/terraform-init.txt)
- [terraform plan](terraform/Outputs/terraform-plan.txt)
- [terraform apply](terraform/Outputs/terraform-apply.txt)
- [SSH connection](terraform/Outputs/ssh-connect.png)

---

## 3. Pulumi Implementation

**Pulumi version:** v3.222.0

**Language:** Python

**How code differs from Terraform:** Imperative approach — Python instead of HCL. Config via `pulumi config set`. Resources created by function calls (gcp.compute.Firewall, gcp.compute.Instance).

**Advantages:** Familiar language, can use loops and functions. Pulumi Cloud for state (free tier).

**Challenges:** CLI installation — Chocolatey did not see pulumi in PATH, had to download archive and specify full path (or add to PATH). Pulumi Cloud login on first config set.

**Public IP:** 136.119.173.134

**Terminal output:**

- [pulumi preview](pulumi/Outputs/pului-preview.txt)
- [pulumi up](pulumi/Outputs/pulumi-up.rxt)
- [SSH connection](pulumi/Outputs/ssh-conntection.png)

---

## 4. Terraform vs Pulumi Comparison

**Ease of Learning:** Terraform — installation via choco/download. Pulumi — requires CLI, login, pip install. HCL is easier for simple infrastructure.

**Code Readability:** Terraform HCL — declarative, structured. Pulumi Python — familiar for developers. For this task both are readable.

**Debugging:** Roughly the same. Terraform — plan shows changes, clear errors. Pulumi — Python traceback, preview is similar. Both tools provide enough information for debugging.

**Documentation:** Roughly the same. Terraform — Registry, many examples. Pulumi — good official documentation, Registry. For basic tasks both are well documented.

**Use Case:** Terraform — standard choice for IaC, large teams, multi-cloud. Pulumi — when Python/TS logic, tests, or complex dynamics are needed.

---

## 5. Lab 5 Preparation & Cleanup

**VM for Lab 5:** No

**Plan:** Recreate cloud VM in Lab 5 via Terraform or Pulumi (code is ready).

**Cleanup status:** Terraform and Pulumi resources destroyed.

- [terraform destroy](terraform/Outputs/terraform-destroy.txt)
- [pulumi destroy](pulumi/Outputs/pulumi-destroy.txt)
