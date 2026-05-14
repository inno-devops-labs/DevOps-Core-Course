# Lab 04 — Infrastructure as Code

## 1. Cloud Provider & Infrastructure

- **Provider:** Yandex Cloud
- **Reason:** Free tier available, accessible without VPN, grant 4000 RUB for new users
- **Instance type:** standard-v2, 2 cores (20% core_fraction), 1 GB RAM
- **Region/Zone:** ru-central1-a
- **Cost:** $0 (free tier)
- **Resources created:**
  - yandex_vpc_network — virtual network
  - yandex_vpc_subnet — subnet 10.0.1.0/24
  - yandex_vpc_security_group — firewall rules (SSH 22, HTTP 80, App 5000)
  - yandex_compute_instance — VM with public IP

---

## 2. Terraform Implementation

- **Terraform version:** 1.9.8
- **Project structure:**
  - `main.tf` — provider configuration and all resources
  - `variables.tf` — input variables (folder_id, zone, ssh_public_key)
  - `outputs.tf` — public IP and SSH command
  - `terraform.tfvars` — variable values (gitignored)

### terraform init output:
Initializing provider plugins found in the configuration...

Finding yandex-cloud/yandex versions matching "~> 0.84"...
Installing yandex-cloud/yandex v0.203.0...
Installed yandex-cloud/yandex v0.203.0 (self-signed, key ID E40F590B50BB8E40)

Terraform has been successfully initialized!

### terraform plan output:
Plan: 4 to add, 0 to change, 0 to destroy.
Changes to Outputs:

ssh_command  = (known after apply)
vm_public_ip = (known after apply)


### terraform apply output:
yandex_vpc_network.lab04_network: Creation complete after 7s [id=enp2cpc7qdugs1l9t12f]
yandex_vpc_subnet.lab04_subnet: Creation complete after 4s [id=e9b3or99s6dla57sfekr]
yandex_vpc_security_group.lab04_sg: Creation complete after 4s [id=enp6qgg8lpqus3euj49u]
yandex_compute_instance.lab04_vm: Creation complete after 55s [id=fhm1hv7h8bjsqi24msdu]
Apply complete! Resources: 4 added, 0 changed, 0 destroyed.
Outputs:
ssh_command  = "ssh ubuntu@51.250.73.116"
vm_public_ip = "51.250.73.116"

### terraform destroy output:
yandex_compute_instance.lab04_vm: Destruction complete after 30s
yandex_vpc_security_group.lab04_sg: Destruction complete after 3s
yandex_vpc_subnet.lab04_subnet: Destruction complete after 7s
yandex_vpc_network.lab04_network: Destruction complete after 1s
Destroy complete! Resources: 4 destroyed.

### SSH access proof:
$ ssh -i ~/.ssh/lab04_key ubuntu@51.250.73.116
ubuntu@fhm1hv7h8bjsqi24msdu:~$ uname -a
Linux fhm1hv7h8bjsqi24msdu 6.8.0-107-generic #107-Ubuntu SMP PREEMPT_DYNAMIC Fri Mar 13 19:51:50 UTC 2026 x86_64 x86_64 x86_64 GNU/Linux
ubuntu@fhm1hv7h8bjsqi24msdu:~$ hostname
fhm1hv7h8bjsqi24msdu

---

## 3. Pulumi Implementation

- **Pulumi version:** 3.239.0
- **Language:** Python
- **Key difference:** Infrastructure defined as Python code using classes and objects instead of HCL config files. Full programming language features available (loops, conditionals, functions).

### pulumi preview output:
Previewing update (dev):
Type                              Name              Plan

pulumi:pulumi:Stack               lab04-pulumi-dev  create
├─ yandex:index:VpcNetwork        lab04-network     create
├─ yandex:index:VpcSubnet         lab04-subnet      create
├─ yandex:index:VpcSecurityGroup  lab04-sg          create
└─ yandex:index:ComputeInstance   lab04-vm          create

Resources:
+ 5 to create

### pulumi up output:
Updating (dev):
Type                              Name              Status

pulumi:pulumi:Stack               lab04-pulumi-dev  created (62s)
├─ yandex:index:VpcNetwork        lab04-network     created (7s)
├─ yandex:index:VpcSubnet         lab04-subnet      created (0.71s)
├─ yandex:index:VpcSecurityGroup  lab04-sg          created (1s)
└─ yandex:index:ComputeInstance   lab04-vm          created (54s)

Outputs:
ssh_command : "ssh ubuntu@93.77.181.6"
vm_public_ip: "93.77.181.6"
Resources:
+ 5 created
Duration: 1m4s

### SSH access proof:
$ ssh -i ~/.ssh/lab04_key ubuntu@93.77.181.6
ubuntu@fhm9vuinvfshd0catqu2:~$ uname -a
Linux fhm9vuinvfshd0catqu2 6.8.0-107-generic #107-Ubuntu SMP PREEMPT_DYNAMIC Fri Mar 13 19:51:50 UTC 2026 x86_64 x86_64 x86_64 GNU/Linux
ubuntu@fhm9vuinvfshd0catqu2:~$ hostname
fhm9vuinvfshd0catqu2

---

## 4. Terraform vs Pulumi Comparison

**Ease of Learning:** Terraform was easier to learn. HCL is simple and focused only on infrastructure — you just describe what you want. Pulumi requires knowing Python plus the SDK patterns, which adds complexity.

**Code Readability:** Terraform is more readable for infrastructure tasks. Each HCL block clearly maps to one resource. Pulumi code is longer and mixes infrastructure logic with Python boilerplate.

**Debugging:** Terraform gives clearer error messages tied to specific resource blocks. Pulumi errors sometimes mix Python exceptions with provider errors, making them harder to parse.

**Documentation:** Terraform has more examples and community resources. Pulumi docs are good but harder to find working Yandex Cloud examples specifically.

**Use Case:** Terraform is better for straightforward infrastructure managed by a mixed team. Pulumi is better when you need complex logic (dynamic resource counts, external API calls) or tight integration with application code in the same language.

---

## 5. Lab 5 Preparation & Cleanup

**VM for Lab 5:** Yes, keeping the Pulumi-created VM.

- **Public IP:** 93.77.181.6
- **SSH command:** `ssh -i ~/.ssh/lab04_key ubuntu@93.77.181.6`
- **SSH user:** ubuntu
- VM is running and accessible (see SSH proof in section 3)

**Terraform resources:** Destroyed after Task 1 (see terraform destroy output in section 2).

**Pulumi resources:** Running, will be used for Lab 5.
