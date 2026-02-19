# lab 04: infrastructure as code (terraform & pulumi)

## 1. cloud provider & infrastructure

### cloud provider chosen

**yandex cloud** was selected for this lab due to:

1. **free tier availability**: offers free tier with 1 VM (2 vCPU at 20%, 1 GB RAM, 10 GB disk) - perfect for lab requirements
2. **accessibility in russia**: works without VPN, which is essential for local development
3. **no credit card required**: can start using without payment method
4. **russian documentation**: comprehensive docs in russian language

### instance configuration

| parameter | value | reason |
|-----------|-------|--------|
| platform | standard-v2 | intel ice lake, free tier eligible |
| cores | 2 | free tier maximum |
| core_fraction | 20% | free tier default (equivalent to 0.4 vCPU) |
| memory | 1 GB | free tier maximum |
| disk | 10 GB network-hdd | free tier default |
| os | ubuntu 22.04 LTS | stable, well-documented |

### region/zone

**zone**: `ru-central1-a` - default availability zone in yandex cloud, closest to user location.

### cost

**total cost**: $0 (free tier)

the instance falls within yandex cloud's free tier limits:
- up to 2 vCPU with 20% performance
- up to 1 GB RAM
- up to 10 GB disk space

### resources created

| resource | name | description |
|----------|------|-------------|
| vpc network | devops-network | virtual private cloud for isolation |
| vpc subnet | devops-subnet | REDDACTED__N6__/24 CIDR block |
| security group | devops-security-group | firewall rules |
| compute instance | devops-vm | ubuntu 22.04 LTS VM |

---

## 2. terraform implementation

### terraform version

```
Terraform v1.5.7
on darwin_arm64
+ provider registry.terraform.io/yandex-cloud/yandex v0.120.0
```

### project structure

```
terraform/
├── .gitignore              # ignores state, credentials
├── main.tf                 # provider and resource definitions
├── outputs.tf              # output values (IP, connection command)
├── terraform.tfvars        # variable values (gitignored)
├── terraform.tfvars.example # example configuration
├── variables.tf            # input variable declarations
└── versions.tf             # terraform and provider version constraints
```

### key configuration decisions

1. **service account authentication**: used `service_account_key_file` for secure authentication instead of hardcoding credentials

2. **variable separation**: sensitive values (cloud_id, folder_id, ssh key) stored in `terraform.tfvars` which is gitignored

3. **output values**: exported public IP and SSH connection command for easy access

4. **security group**: configured rules for SSH (22), HTTP (80), and application port (5000)

### terminal output

#### terraform init

[terraform init output](screenshots/04-terraform-init.png)

#### terraform plan

[terraform plan output](screenshots/06-terraform-plan.png)

#### terraform apply

[terraform apply output](screenshots/05-terraform-apply.png)

#### ssh access proof

[ssh connection to VM](screenshots/07-terraform-ssh.png)

### challenges encountered

1. **terraform registry access**: had to configure yandex cloud mirror in `~/.terraformrc` due to network issues accessing `registry.terraform.io`:
   ```hcl
   provider_installation {
     network_mirror {
       url = "https://terraform-mirror.yandexcloud.net/"
       include = ["registry.terraform.io/*/*"]
     }
   }
   ```

2. **boot disk labels**: the `labels` argument inside `boot_disk.initialize_params` is not supported by yandex provider - had to remove it

3. **ssh key confusion**: initially confused service account key (`authorized_keys.json`) with SSH public key for VM access - they serve different purposes

---

## 3. pulumi implementation

### pulumi version & language

```
pulumi v3.222.0
python 3.14
```

### project structure

```
pulumi/
├── .gitignore              # ignores stack configs, venv
├── Pulumi.yaml             # project metadata
├── Pulumi.dev.yaml         # stack configuration (gitignored)
├── __main__.py             # infrastructure code
├── requirements.txt        # python dependencies
└── venv/                   # virtual environment
```

### how code differs from terraform

| aspect | terraform (HCL) | pulumi (python) |
|--------|-----------------|-----------------|
| syntax | declarative DSL | imperative python |
| variables | `var.name` | `config.get("name")` |
| outputs | `output "ip" { value = ... }` | `pulumi.export("ip", ...)` |
| resources | `resource "type" "name" { }` | `resource = Type("name", ...)` |
| logic | limited (count, for_each) | full python capabilities |

### code comparison example

**terraform (HCL):**
```hcl
resource "yandex_compute_instance" "vm" {
  name        = var.vm_name
  platform_id = var.vm_platform_id

  resources {
    cores         = var.vm_cores
    core_fraction = var.vm_core_fraction
    memory        = var.vm_memory
  }
}
```

**pulumi (python):**
```python
vm = yandex.ComputeInstance(
    "vm",
    name=vm_name,
    platform_id=vm_platform_id,
    resources={
        "cores": vm_cores,
        "core_fraction": vm_core_fraction,
        "memory": vm_memory,
    },
)
```

### terminal output

#### pulumi preview

[pulumi preview output](screenshots/08-pulumi-preview.png)

#### pulumi up

[pulumi up output](screenshots/09-pulumi-up.png)

#### ssh access proof

[ssh connection to VM](screenshots/10-pulumi-ssh.png)

### advantages discovered

1. **familiar syntax**: writing infrastructure in python feels natural, especially for developers already familiar with the language

2. **IDE support**: full autocomplete, type hints, and refactoring capabilities in IDEs

3. **code reuse**: can use python functions, classes, and modules for organizing infrastructure code

4. **testing potential**: can write unit tests for infrastructure using pytest

### challenges encountered

1. **pkg_resources deprecation**: python 3.14 doesn't include `pkg_resources` by default, had to install older setuptools:
   ```
   pip install setuptools==69.0.0
   ```

2. **different parameter names**: pulumi-yandex uses `ingresses`/`egresses` instead of `ingress`/`egress` like terraform

3. **less community support**: pulumi-yandex has less documentation compared to terraform yandex provider

---

## 4. terraform vs pulumi comparison

### ease of learning

**terraform** was easier to learn initially due to simpler HCL syntax and extensive documentation. the declarative approach means you just describe the desired state. **pulumi** requires knowledge of a programming language, but offers more flexibility once you're past the learning curve.

### code readability

**terraform** HCL is very readable for infrastructure definitions - it's purpose-built for this task. however, **pulumi** python code benefits from familiar syntax and IDE features like autocomplete, making it easier to navigate large codebases.

### debugging

**terraform** provides clear error messages and `terraform plan` gives excellent preview of changes. **pulumi** errors can be more cryptic since they come from both pulumi and python runtime. however, pulumi allows using python debuggers and print statements for troubleshooting.

### documentation

**terraform** has significantly better documentation, especially for the yandex cloud provider. the terraform registry provides comprehensive examples. **pulumi** documentation exists but is less mature, and finding examples for less common providers can be challenging.

### use case

**terraform** is ideal for:
- teams without strong programming background
- projects requiring mature tooling and community support
- straightforward infrastructure definitions

**pulumi** is ideal for:
- development teams comfortable with programming
- complex infrastructure requiring logic (conditionals, loops)
- projects benefiting from infrastructure testing
- environments where infrastructure code should follow same patterns as application code

---

## 5. lab 5 preparation & cleanup

### vm for lab 5

**keeping VM for lab 5**: yes

the VM created with pulumi will be kept running for lab 05 (ansible). the terraform infrastructure was destroyed before creating pulumi infrastructure.

### cleanup status

1. **terraform resources**: destroyed with `terraform destroy`
2. **pulumi resources**: kept running for lab 05

### current VM status

| property | value |
|----------|-------|
| created by | pulumi |
| status | running |
| accessible via | SSH |

the VM is ready for lab 05 ansible configuration management.
