# Lab 04 — Infrastructure as Code (Terraform & Pulumi)

## 1. Cloud Provider & Infrastructure

**Provider:** Local VirtualBox (7.2.6) — no cloud provider used.  
Reason: avoid cloud costs, meet deadline quickly, keep everything reproducible on a local machine.

**Instance details:**

| Parameter | Value |
|-----------|-------|
| OS | Ubuntu 22.04 LTS (bento/ubuntu-22.04 Vagrant box) |
| CPUs | 2 |
| RAM | 1 024 MB |
| Disk | ~10 GB (Vagrant box default) |
| Network | NIC 1 — NAT (SSH port-forwarded), NIC 2 — Host-only |
| Cost | $0 |

**Resources created (per tool):**

- Virtual machine (VBoxManage import + modifyvm + startvm)
- NAT adapter with SSH port forwarding
- Host-only adapter for direct host⟷guest access

---

## 2. Terraform Implementation

**Terraform version:** 1.14.5  
**Provider:** `hashicorp/null ~> 3.0` (null_resource + local-exec)

> The official `terra-farm/virtualbox` provider is incompatible with
> VirtualBox 7.x (Guest Additions mismatch), so VMs are managed through
> `VBoxManage` CLI invocations wrapped in `null_resource` provisioners.

### Project structure

```
terraform/
├── main.tf          # null_resource with local-exec (create + destroy)
├── variables.tf     # vm_name, vm_image_url, vm_cpus, vm_memory, host_only_adapter
├── outputs.tf       # vm_name, ssh_command, host_only_ip
└── .gitignore       # *.tfstate, .terraform/, *.box, *.ova, terraform.tfvars
```

### Key configuration decisions

1. **null_resource** — downloads the Vagrant `.box`, extracts OVF, and imports via `VBoxManage`.
2. **NAT + Host-Only dual NIC** — NAT on NIC 1 gives internet + port-forwarded SSH (`localhost:2222` → VM `22`), host-only on NIC 2 allows direct IP access.
3. **VBoxManage in `local-exec`** — all commands run locally in PowerShell.
4. **Destroy provisioner** — cleanly powers off and unregisters the VM.

### Terminal output (key commands)

```
> terraform init
Initializing the backend...
Initializing provider plugins...
- Finding hashicorp/null versions matching "~> 3.0"...
- Installing hashicorp/null v3.2.4...
- Installed hashicorp/null v3.2.4
Terraform has been successfully initialized!

> terraform plan
Plan: 1 to add, 0 to change, 0 to destroy.

> terraform apply -auto-approve
null_resource.ubuntu_vm: Creating...
null_resource.ubuntu_vm: Still creating... [10s elapsed]
...
null_resource.ubuntu_vm: Creation complete
Apply complete! Resources: 1 added, 0 changed, 0 destroyed.

Outputs:
  ssh_command    = "ssh -p 2222 vagrant@127.0.0.1"
  vm_name        = "ubuntu-devops"
```

### SSH verification

```
> ssh -p 2222 vagrant@127.0.0.1
vagrant@vagrant:~$ uname -a
Linux vagrant 5.15.0-116-generic ... x86_64 GNU/Linux
```

### Challenges

- `terra-farm/virtualbox` provider: "can't convert vbox network" error → switched to `null_resource`.
- Host-only DHCP was disabled → had to enable it via `VBoxManage dhcpserver modify --enable`.
- Cyrillic characters in workspace path (`Рабочий стол`) caused encoding issues with PowerShell's `-File` parameter.

---

## 3. Pulumi Implementation

**Pulumi version:** 3.221.0  
**Language:** Python 3.12  
**Provider package:** `pulumi-command` (`local.Command`)

### Project structure

```
pulumi/
├── __main__.py        # Pulumi program (local.Command)
├── scripts/
│   ├── create_vm.ps1  # VBoxManage create/start script
│   └── destroy_vm.ps1 # VBoxManage destroy script
├── Pulumi.yaml        # Project metadata
├── Pulumi.dev.yaml    # Stack config (vm_name, cpus, memory, …)
├── requirements.txt   # pulumi, pulumi-command
├── venv/              # Python virtual environment
└── .gitignore         # .pulumi/, venv/, __pycache__/
```

### How code differs from Terraform

| Aspect | Terraform | Pulumi |
|--------|-----------|--------|
| Resource definition | HCL `null_resource` block with `provisioner "local-exec"` | Python `local.Command(create=…, delete=…, environment=…)` |
| Variables | `variables.tf` + `var.name` | `pulumi.Config().get("key")` |
| Outputs | `output "name" { value = … }` | `pulumi.export("name", value)` |
| State | `terraform.tfstate` (local file) | Pulumi local backend (`file://~`) with encrypted secrets |
| Execution | `terraform apply` | `pulumi up` |

### Challenges

- Pulumi passphrase & `encryptionsalt` mismatch when recreating the stack → had to remove old `encryptionsalt` from `Pulumi.dev.yaml`.
- Inline multiline PowerShell strings caused `TerminatorExpectedAtEndOfString` errors → extracted scripts into external `.ps1` files.
- Cyrillic in workspace path broke `powershell -File "path"` → scripts are copied to `%TEMP%` at runtime and parameters passed via environment variables.

### Terminal output

```
> pulumi preview
     Type                      Name                   Plan
     pulumi:pulumi:Stack       devops-virtualbox-dev
 +   └─ command:local:Command  ubuntu-vm              create
Resources:
    + 1 to create
    1 unchanged

> pulumi up --yes
Updating (dev):
     Type                      Name                   Status
     pulumi:pulumi:Stack       devops-virtualbox-dev
 +   └─ command:local:Command  ubuntu-vm              created
Outputs:
    ssh_command : "ssh -p 2223 vagrant@127.0.0.1"
    vm_name     : "ubuntu-pulumi"
Resources:
    + 1 created
    1 unchanged
```

### SSH verification

```
> ssh -p 2223 vagrant@127.0.0.1
vagrant@vagrant:~$ uname -a
Linux vagrant 5.15.0-116-generic ... x86_64 GNU/Linux
```

---

## 4. Terraform vs Pulumi Comparison

### Ease of Learning

Terraform was easier to start with — HCL is simple and the documentation ecosystem is larger. Pulumi required understanding both the SDK and the underlying programming language (Python), and setting up a virtual environment with dependencies. For a beginner, Terraform's `init → plan → apply` cycle is more straightforward.

### Code Readability

Terraform's declarative HCL reads more like a config file, which is ideal for simple infrastructure. Pulumi's Python code is more verbose but allows real programming logic (loops, conditionals, imports). For this small project, Terraform is more readable; for larger projects with dynamic infrastructure, Pulumi would win.

### Debugging

Terraform's error messages are generally clearer and more actionable. Pulumi's errors (especially from `pulumi_command`) were opaque — exit codes like `0xfffd0000` and garbled Cyrillic error text made debugging harder. Terraform's `plan` output is also easier to parse than Pulumi's `preview`.

### Documentation

Terraform has a much larger community and more documented examples. Pulumi has excellent official docs, but the community is smaller. When using uncommon providers like `pulumi_command`, finding solutions to edge cases was harder.

### Use Case

Use **Terraform** when you want a stable, well-documented, declarative tool for standard cloud architectures. Use **Pulumi** when you need complex logic, type safety, or want to leverage existing programming skills — it shines in dynamic, multi-environment setups.

---

## 5. Lab 5 Preparation & Cleanup

**VM for Lab 5:** Yes — keeping the Pulumi-created VM (`ubuntu-pulumi`) running.  
**Connection:** `ssh -p 2223 vagrant@127.0.0.1` (password: `vagrant`).

**Cleanup status:**

| Item | Status |
|------|--------|
| Terraform VM (`ubuntu-devops`) | Destroyed (`terraform destroy`) |
| Pulumi VM (`ubuntu-pulumi`) | **Running** — kept for Lab 5 |
| Terraform state file | Removed (no `terraform.tfstate` in repo) |
| Cloud resources | N/A (local VirtualBox only) |
| Secrets in code | None committed |

---

## Bonus: IaC CI/CD (terraform-ci.yml)

A GitHub Actions workflow [.github/workflows/terraform-ci.yml](../.github/workflows/terraform-ci.yml) was created that:

- Triggers on PRs and pushes touching `terraform/**`
- Runs `terraform fmt -check` for formatting
- Runs `terraform init -backend=false` + `terraform validate` for syntax
- Runs `tflint` for best-practice linting

## Bonus: GitHub Repository Import

A Terraform configuration for importing the course repository into Terraform management was created in [`terraform/github-import/`](../terraform/github-import/).

**Why importing matters:**
Managing existing resources (repos, infra) with IaC brings version control, auditability, consistency, and automated validation to previously manual configurations. It eliminates "tribal knowledge" and enables safe, reviewable changes.
