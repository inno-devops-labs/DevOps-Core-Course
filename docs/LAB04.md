# Lab 4 — Infrastructure as Code (Terraform & Pulumi)

## 1. Cloud Provider & Infrastructure

- **Cloud provider:** Yandex Cloud  
- **Why chosen:** Available in Russia, has a free tier, straightforward setup via OAuth and service account. 
- **Instance type:** 2 vCPU, 2 GB RAM (platform: standard-v1). Size chosen to be sufficient for a lab VM and future application deployment.  
- **Region/zone:** `ru-central1-a` (default in variables; `yc` default zone was `ru-central1-b`).  
- **Cost:** Within free tier / minimum tariff — 0 ₽ with correct usage.  
- **Created resources:**
  - `yandex_vpc_network.network` — network (terraform-network)
  - `yandex_vpc_subnet.subnet` — subnet 10.0.0.0/24 in zone ru-central1-a
  - `yandex_vpc_security_group.sg` — security group (SSH 22, HTTP 80, app 5000)
  - `yandex_compute_instance.vm` — VM (Ubuntu 24.04 LTS, public IP)

---

## 2. Terraform Implementation

- **Terraform version:** v1.14.5 (darwin_arm64)  
- **Provider:** yandex-cloud/yandex v0.187.0  

### Project structure (directory `ydb_terraform/`)

```
ydb_terraform/
├── .gitignore      # state, .terraform/, terraform.tfvars, keys
├── main.tf          # Network, subnet, security group, VM
├── provider.tf      # required_providers, provider yandex
├── variables.tf     # cloud_id, folder_id, zone, vm_name, image_id, ssh_user, public_key_path
├── outputs.tf       # vm_public_ip
└── terraform.tfvars # variable values (not committed)
```

### Key decisions

- Authentication via variables `cloud_id`, `folder_id`, and (optionally) environment variables or service account key file; secrets are not stored in code.  
- Variables used for zone, VM name, `image_id`, SSH key path — configuration is reusable.  
- Output `vm_public_ip` for quick SSH access.  
- Security group: inbound SSH (22), HTTP (80), app port (5000); outbound traffic allowed.  
- Added to `.gitignore`: `*.tfstate`, `*.tfstate.*`, `.terraform/`, `terraform.tfvars`, `*.pem`, `*.key`.

### Challenges

- Finding the right `image_id` for Ubuntu (used image list via `yc compute image list --folder-id standard-images`).  
- Warning on `terraform init` about lock file for darwin_arm64 only — for CI on linux_amd64 run `terraform providers lock -platform=linux_amd64`.  
- The plan includes the public SSH key in metadata — in this doc the plan output is shown in shortened/sanitized form.

### Command output 

#### terraform init

```
Initializing the backend...
Initializing provider plugins...
- Finding latest version of yandex-cloud/yandex...
- Installing yandex-cloud/yandex v0.187.0...
- Installed yandex-cloud/yandex v0.187.0 (unauthenticated)
Terraform has created a lock file .terraform.lock.hcl to record the provider
selections it made above. Include this file in your version control repository
so that Terraform can guarantee to make the same selections by default when
you run "terraform init" in the future.

Terraform has been successfully initialized!

You may now begin working with Terraform. Try running "terraform plan" to see
any changes that are required for your infrastructure.
```

#### terraform plan (abbreviated; secrets and full SSH key removed)

```
Terraform used the selected providers to generate the following execution plan. Resource actions are indicated with the following symbols:
  + create

Terraform will perform the following actions:

  # yandex_compute_instance.vm will be created
  + resource "yandex_compute_instance" "vm" {
      + name = "terraform-vm"
      + metadata = {
          + "ssh-keys" = "ubuntu:<redacted-public-key>"
        }
      + boot_disk { ... image_id = "fd80293ig2816a78q276" (ubuntu-2404-lts-oslogin) ... }
      + network_interface { + nat = true ... }
      + resources { + cores = 2, + memory = 2 }
    }

  # yandex_vpc_network.network will be created
  + resource "yandex_vpc_network" "network" { + name = "terraform-network" }

  # yandex_vpc_security_group.sg will be created
  + resource "yandex_vpc_security_group" "sg" {
      + name = "terraform-sg"
      + ingress { description = "SSH", port = 22, protocol = "TCP", v4_cidr_blocks = ["0.0.0.0/0"] }
      + ingress { description = "HTTP", port = 80, protocol = "TCP", v4_cidr_blocks = ["0.0.0.0/0"] }
      + ingress { description = "App 5000", port = 5000, protocol = "TCP", v4_cidr_blocks = ["0.0.0.0/0"] }
      + egress { protocol = "ANY", v4_cidr_blocks = ["0.0.0.0/0"] }
    }

  # yandex_vpc_subnet.subnet will be created
  + resource "yandex_vpc_subnet" "subnet" {
      + name = "terraform-subnet"
      + v4_cidr_blocks = ["10.0.0.0/24"]
      + zone = "ru-central1-a"
    }

Plan: 4 to add, 0 to change, 0 to destroy.

Changes to Outputs:
  + vm_public_ip = (known after apply)
```

#### terraform apply (final output)

```
yandex_compute_instance.vm: Creation complete after 47s [id=fhm6b6ej125ta0nle31i]

Apply complete! Resources: 4 added, 0 changed, 0 destroyed.

Outputs:

vm_public_ip = "84.201.132.65"
```

#### SSH connection to VM

```bash
$ ssh ubuntu@84.201.132.65
The authenticity of host '84.201.132.65 (84.201.132.65)' can't be established.
ED25519 key fingerprint is: SHA256:P/rIThvGihUqVuwtOIy9dr0c0UVuG3ZsimisnG1qHGs
Are you sure you want to continue connecting (yes/no/[fingerprint])? yes
Warning: Permanently added '84.201.132.65' (ED25519) to the list of known hosts.
Welcome to Ubuntu 24.04.1 LTS (GNU/Linux 6.8.0-41-generic x86_64)
...
ubuntu@fhm6b6ej125ta0nle31i:~$ whoami
ubuntu
ubuntu@fhm6b6ej125ta0nle31i:~$ hostname
fhm6b6ej125ta0nle31i
ubuntu@fhm6b6ej125ta0nle31i:~$ exit
logout
Connection to 84.201.132.65 closed.
```

**Connection command:** `ssh ubuntu@84.201.132.65` (IP may change after recreating resources; current value in `terraform output vm_public_ip`).

---

## 3. Pulumi Implementation

- **Pulumi version and language:** Pulumi 3.x, Python (runtime: python, virtualenv: venv).  
- **Provider:** pulumi-yandex (Yandex Cloud).

### Project structure (directory `pulumi/`)

```
pulumi/
├── __main__.py       # Network, subnet, security group, rules, VM, outputs
├── Pulumi.yaml       # name, runtime (python + venv), config tags
├── requirements.txt  # pulumi>=3.0.0,<4.0.0, pulumi-yandex
├── venv/             # virtual environment (in .gitignore)
└── Pulumi.dev.yaml  # stack config for dev (folderId, serviceAccountKeyFile, sshPublicKey — do not commit secrets)
```

### How the code differs from Terraform

- Infrastructure is described imperatively in Python: calls like `yandex.VpcNetwork(...)`, `yandex.VpcSubnet(...)`, etc.; dependencies are expressed via `network.id`, `subnet.id`, `sg.id`.
- Configuration: `pulumi.Config("yandex")` for `folderId` and service account key; SSH key in project config (`pulumi.Config().get("sshPublicKey")`) so the custom key is not passed to the provider (otherwise “Invalid or unknown key”).
- For security group rules in Pulumi Yandex the required parameter is `security_group_binding=sg.id` (not `security_group_id`).
- Same resources: VPC, subnet 10.0.0.0/24, security group (SSH 22, HTTP 80, app 5000), VM 2 vCPU / 2 GB RAM, Ubuntu 22.04 LTS, public IP. Output `public_ip` via `pulumi.export(...)`.

### Advantages of Pulumi

- Familiar language (Python): loops, conditionals, functions, types, and IDE autocomplete.
- Single file `__main__.py` for the whole infrastructure — convenient for a small lab.
- Secrets and stack config can be stored in Pulumi (including encrypted) and kept separate from provider code.

### Challenges

- Must explicitly pass `folder_id` to all Yandex resources (network, subnet, security group, VM); when missing — error “cannot determine folder_id”.
- Yandex quota on VPC count per folder: when hitting “Quota limit vpc.networks.count exceeded” — use an existing network or free up quota.
- SSH key for VM is set via `metadata={"ssh-keys": "ubuntu:<key>"}`; without it — “Permission denied (publickey)”. Key is in project config, not under `yandex:`, so the provider does not fail on the unknown key.
- After first boot the VM may respond with “System is booting up...” on SSH — wait 1–2 minutes and retry the connection.

### Output of `pulumi preview` and `pulumi up`, SSH connection

#### pulumi preview (abbreviated)

```
Previewing update (dev)

     Type                                  Name               Plan
 +   pulumi:pulumi:Stack                   python_pulumi-dev  create
 +   ├─ yandex:index:VpcNetwork            lab-network        create
 +   ├─ yandex:index:VpcSubnet             lab-subnet         create
 +   ├─ yandex:index:VpcSecurityGroup      lab-sg             create
 +   ├─ yandex:index:VpcSecurityGroupRule  ssh-rule           create
 +   ├─ yandex:index:VpcSecurityGroupRule  http-rule          create
 +   ├─ yandex:index:VpcSecurityGroupRule  app-rule           create
 +   └─ yandex:index:ComputeInstance       lab-vm             create

Outputs:
    public_ip: [unknown]

Resources: + 8 to create
```

#### pulumi up (final output)

```
Do you want to perform this update? yes
Updating (dev)

     Type                        Name               Status
 +   pulumi:pulumi:Stack         python_pulumi-dev  created
 +   ├─ yandex:index:VpcNetwork  lab-network        created
 +   ├─ yandex:index:VpcSubnet   lab-subnet         created
 ...

Outputs:
    public_ip: "93.77.176.17"

Resources: + 8 created
```

#### SSH connection to VM

```bash
$ ssh ubuntu@93.77.176.17
...
ubuntu@<vm-id>:~$ whoami
ubuntu
ubuntu@<vm-id>:~$ exit
```

**Connection command:** `ssh ubuntu@<public_ip>` (current IP in `pulumi stack output public_ip`).

---

## 4. Terraform vs Pulumi Comparison

- **Ease of Learning:** Terraform is easier to get started with: one HCL syntax, few concepts. Pulumi requires knowing a language (e.g. Python) but gives a familiar dev environment and types.
- **Code Readability:** For a linear set of resources both are readable. Terraform is declarative by blocks; Pulumi reads like a sequence of API calls, convenient for loops and conditional logic.
- **Debugging:** Pulumi is easier to debug: stack traces in the native language, logic in code. In Terraform errors come from the provider and state; debugging is often via plan/apply and documentation.
- **Documentation:** Terraform and its providers (including Yandex) are well documented; Pulumi Registry and provider examples exist, but the community and guides are smaller than Terraform’s.
- **Use Case (when Terraform, when Pulumi):** Terraform is the standard for “infrastructure as config”, large teams, multi-cloud, and many ready-made modules. Pulumi fits when you want to write infrastructure as code (loops, tests, reuse), integrate with application code in the same language, or handle complex resource logic.

---

## 5. Lab 5 Preparation & Cleanup

**VM for Lab 5:**  
- Am I keeping the VM for Lab 5: **No** (all VMs stopped; will recreate from code when needed)  
- Which VM I’m keeping: **recreate the cloud VM via Pulumi** (same `pulumi/` project).

**Cleanup:**  
- All resources destroyed on Yandex Cloud: `pulumi destroy`, and `terraform destroy`.  
- No VMs running. State and code are kept locally so infrastructure can be recreated anytime.

**How to bring infrastructure back (from existing files):**

- **Pulumi:**
  ```bash
  cd pulumi
  source venv/bin/activate
  # Ensure config is set: yandex:folderId, yandex:serviceAccountKeyFile (or token), sshPublicKey
  pulumi up
  ```
  Then connect: `ssh ubuntu@$(pulumi stack output public_ip)`.

- **Terraform:**
  ```bash
  cd ydb_terraform
  terraform init
  terraform apply
  ```
  Then connect: `ssh ubuntu@$(terraform output -raw vm_public_ip)`.


