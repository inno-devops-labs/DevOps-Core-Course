# Lab 04 - Infrastructure as Code (Terraform and Pulumi)

## 1. Cloud Provider and Infrastructure

### Chosen platform and rationale

- **Platform:** Personal VPS (used as a local VM alternative to public cloud).
- **Why:** This was used because available free-tier cloud options were not practical in my case.
- **Host location:** France.
- **Public IP:** `31.56.176.110`.
- **OS:** Ubuntu 24.04 LTS.

### Instance sizing and cost

- **Instance size:** 1 vCPU, 2 GB RAM, 30 GB NVMe.
- **Cost model:** Existing personal server, no additional Lab 04 spend.

### Resources managed in this lab

Because I used an already running VPS, I did not provision VM/network/firewall objects from a cloud API.  
Instead, IaC code managed server configuration through SSH:

- nginx installation/start (Terraform stage),
- web content update in `/var/www/html/index.html` (Terraform and Pulumi stages),
- service restart and idempotent content overwrite (Pulumi stage).

---

## 2. Terraform Implementation

### Tooling and structure

- **Terraform version:** `v1.14.5`
- **Provider:** `hashicorp/null` (`~> 3.0`)
- **Mirror note:** the original provider is blocked in Russia and mirror was used.

Project structure:

```text
terraform/
├── main.tf
├── variables.tf
├── outputs.tf
└── terraform.tfvars   (gitignored)
```

### What the Terraform code does

`null_resource.vps_setup` connects over SSH and executes:

1. `apt-get update -y`
2. `apt-get install -y nginx`
3. `systemctl enable nginx`
4. `systemctl start nginx`
5. `echo 'Lab04 VPS configured by Terraform' > /var/www/html/index.html`

### Key configuration decisions

- Used variables for host/user/key path.
- Exposed outputs for public IP and ready-to-use SSH command.
- Kept secrets/state files out of Git using `.gitignore`.

### Terraform challenges encountered

- Terraform resource is operational (SSH-driven provisioning), not cloud-resource declarative.
- Public registry connectivity can be problematic, so a mirror was required.

### Terraform terminal output evidence (sanitized)

Full Terraform log file: [`terraform/docs/terraform.logs`](./terraform.logs)

#### `terraform apply`

```bash
Terraform will perform the following actions:
  # null_resource.vps_setup is tainted, so must be replaced
Plan: 1 to add, 0 to change, 1 to destroy.

null_resource.vps_setup: Creation complete after 21s [id=4464433007309882184]

Apply complete! Resources: 1 added, 0 changed, 1 destroyed.

Outputs:
ssh_connection = "ssh root@31.56.176.110"
vm_public_ip   = "31.56.176.110"
```

#### Validation via HTTP

```bash
$ curl http://31.56.176.110
Lab04 VPS configured by Terraform
```

#### `terraform plan` after apply

```bash
No changes. Your infrastructure matches the configuration.
```

#### SSH proof (service status)

```bash
$ ssh -i /Users/mac/.ssh/id_ed25519 root@31.56.176.110 "nginx -v && systemctl status nginx --no-pager | head -5"
nginx version: nginx/1.24.0 (Ubuntu)
● nginx.service - A high performance web server and a reverse proxy server
     Loaded: loaded (...); enabled
     Active: active (running)
```

---

## 3. Pulumi Implementation

### Tooling and approach

- **Pulumi version:** `v3.221.0`
- **Language:** Python
- **Backend:** Local state (`pulumi login --local`)

Project structure:

```text
pulumi/
├── __main__.py
├── requirements.txt
├── Pulumi.yaml
└── venv/              (gitignored)
```

### How Pulumi code differs from Terraform

- Terraform used declarative HCL + `remote-exec`.
- Pulumi used a Python `dynamic.ResourceProvider` that runs SSH commands via `subprocess`.
- Pulumi exports the same operational outputs (`vm_public_ip`, `ssh_connection`).

### What Pulumi does on the VPS

1. `systemctl restart nginx`
2. `echo 'Lab04 VPS configured by Pulumi' > /var/www/html/index.html`

### Advantages discovered

- Full Python language makes custom logic straightforward.
- Easy to reuse local scripting patterns (`subprocess`, loops, conditionals).

### Pulumi challenges encountered

- Dynamic providers are more flexible but less straightforward to debug than plain Terraform logs.
- Pulumi passphrase handling (`PULUMI_CONFIG_PASSPHRASE`) adds one more operational step.

### Pulumi terminal output evidence (sanitized)

Full Pulumi log file: [`terraform/docs/pulumi.logs`](./pulumi.logs)

#### `pulumi preview`

```bash
Previewing update (dev):
 + pulumi:pulumi:Stack                lab04-pulumi-dev  create
 + └─ pulumi-python:dynamic:Resource  vps-setup         create

Outputs:
    ssh_connection: "ssh root@31.56.176.110"
    vm_public_ip  : "31.56.176.110"
Resources:
    + 2 to create
```

#### `pulumi up`

```bash
Do you want to perform this update? yes
Updating (dev):
 + pulumi:pulumi:Stack                lab04-pulumi-dev  created
 + └─ pulumi-python:dynamic:Resource  vps-setup         created

Outputs:
    ssh_connection: "ssh root@31.56.176.110"
    vm_public_ip  : "31.56.176.110"
Resources:
    + 2 created
Duration: 3s
```

#### Validation via HTTP and SSH

```bash
$ curl http://31.56.176.110
Lab04 VPS configured by Pulumi

$ ssh -i /Users/mac/.ssh/id_ed25519 root@31.56.176.110 "nginx -v && cat /var/www/html/index.html"
Lab04 VPS configured by Pulumi
nginx version: nginx/1.24.0 (Ubuntu)
```

---

## 4. Terraform vs Pulumi Comparison

### Ease of learning

Terraform was easier to start with for a simple provisioning task because HCL is focused and concise.  
Pulumi required more understanding of SDK/runtime concepts (especially dynamic resources), but it felt natural with Python experience.

### Code readability

Terraform is clearer for pure infrastructure declarations and quick reviews.  
Pulumi is more verbose in this case, but it scales better when custom program logic is needed.

### Debugging

Terraform logs were easier to interpret for the remote-exec lifecycle.  
Pulumi dynamic provider debugging can be less transparent because behavior is hidden in Python code and provider runtime messages.

### Documentation and examples

Terraform has broader ecosystem docs and many direct examples.  
Pulumi docs are good, but examples for dynamic-provider patterns are narrower than typical Terraform provider examples.

### Use cases

I would choose Terraform for standard, declarative infrastructure workflows.  
I would choose Pulumi when infrastructure logic depends on richer programming constructs and reusable language-native modules.

---

## 5. Lab 5 Preparation and Cleanup

### VM plan for Lab 5

- **Keeping VM for Lab 5:** Yes.
- **Which environment is active:** VPS configured by Pulumi (nginx running, index content updated by Pulumi).
- **Connection:** `ssh root@31.56.176.110`

### Cleanup status

- Terraform-managed resources were destroyed successfully.
- Pulumi-managed configuration remains active on the VPS for next lab steps.

#### `terraform destroy` proof

```bash
$ terraform destroy
Plan: 0 to add, 0 to change, 1 to destroy.
null_resource.vps_setup: Destroying...
null_resource.vps_setup: Destruction complete after 0s
Destroy complete! Resources: 1 destroyed.
```

---

## Notes on sanitization and security

- Command outputs were sanitized to avoid exposing secrets.
- State files, tfvars with credentials, local venv, and Pulumi stack secrets are excluded from Git.
