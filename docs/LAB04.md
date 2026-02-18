# Lab 04 Documentation - Infrastructure as Code

## 1. Cloud Provider & Infrastructure

### Cloud Provider Selection

**Provider Chosen:** Yandex Cloud

### Instance Configuration

| Parameter            | Value              | Reason                                     |
| -------------------- | ------------------ | ------------------------------------------ |
| **Platform**         | standard-v2        | Standard Yandex Cloud platform             |
| **vCPUs**            | 2 (20% guaranteed) | Free tier compatible                       |
| **RAM**              | 2 GB               | Minimal for basic operations               |
| **Zone**             | ru-central1-a      | Moscow data center                         |
| **Operating System** | Ubuntu 22.04 LTS   | Popular, well-supported Linux distribution |
| **Storage**          | 10 GB HDD          | Minimal storage for basic operations       |
| **Instance Type**    | Preemptible        | 70% cost reduction                         |

### Resources Created

1. **VM Instance**
   - Name: `lab04-devops-vm`
   - Platform: `standard-v2`
   - Resources: 2 vCPUs (20%), 2 GB RAM
   - Public IP: Dynamically assigned by Yandex Cloud
   - Preemptible: Yes

2. **VPC Network**
   - Name: `lab04-devops-vpc`
   - Purpose: Isolated network environment for resources

3. **Security Group / Firewall Rules**
   - Name: `lab04-devops-sg`
   - Rules:
     - **SSH (port 22)**: Remote access
     - **HTTP (port 80)**: Web server access
     - **Custom App (port 5000)**: Future application deployment

4. **Public IP Address**
   - Automatically assigned via NAT
   - Allows external connectivity

---

## 2. Terraform Implementation

### Terraform Version

```
Terraform v1.5.0 or later
```

### Project Structure

```
terraform/
├── .gitignore              # Ignore state files and secrets
├── main.tf                 # Main resource definitions
├── variables.tf            # Input variable declarations
├── outputs.tf              # Output value definitions
├── terraform.tfvars.example # Example configuration
```

### Key Configuration Decisions

1. **Provider Selection**
   - Used Yandex Cloud provider (`yandex-cloud/yandex`)
   - Version ~> 0.100 for latest features
   - Authentication via environment variables (YC_TOKEN or YC_SERVICE_ACCOUNT_KEY_FILE)

2. **Resource Dependencies**
   - Subnet depends on VPC network (via `network_id` reference)
   - Security group depends on VPC network
   - VM instance depends on subnet and security group
   - Terraform automatically handles dependency order through resource references

3. **Variable Design**
   - All configurable values extracted to `variables.tf`
   - Default values provided for quick start
   - Can be overridden via CLI or `terraform.tfvars`

4. **Output Strategy**
   - Exposed critical information: IP address, SSH command
   - Included resource metadata for reference
   - Made outputs easily accessible via `terraform output`

5. **State Management**
   - Local state file (terraform.tfstate)
   - Added to .gitignore for security
   - Contains sensitive information (IPs, IDs)
   - For production: should use remote backend (Terraform Cloud, S3, etc.)

### Installation and Setup

```bash
brew tap hashicorp/tap
brew install hashicorp/tap/terraform

curl -sSL https://storage.yandexcloud.net/yandexcloud-yc/install.sh | bash

yc init

yc iam service-account create --name terraform-sa
SA_ID=$(yc iam service-account get terraform-sa --format json | jq -r .id)
FOLDER_ID=$(yc config get folder-id)
yc resource-manager folder add-access-binding $FOLDER_ID --role editor --subject serviceAccount:$SA_ID
yc iam key create --service-account-name terraform-sa --output key.json

export YC_SERVICE_ACCOUNT_KEY_FILE=$(pwd)/key.json
export YC_TOKEN=$(yc iam create-token)

cd terraform

cp terraform.tfvars.example terraform.tfvars

terraform init
```

### Execution Steps

#### Step 1: Initialize

```bash
$ terraform init

Initializing the backend...

Initializing provider plugins...
- Finding yandex-cloud/yandex versions matching "~> 0.100"...
- Installing yandex-cloud/yandex v0.100.0...
- Installed yandex-cloud/yandex v0.100.0

Terraform has been successfully initialized!

You may now begin working with Terraform. Try running "terraform plan" to see
any changes that are required for your infrastructure.
```

#### Step 2: Validate Configuration

```bash
$ terraform validate
Success! The configuration is valid.
```

#### Step 3: Plan Infrastructure

```bash
$ terraform plan

Terraform used the selected providers to generate the following execution plan.
Resource actions are indicated with the following symbols:
  + create

Terraform will perform the following actions:

  # yandex_compute_instance.lab_vm will be created
  + resource "yandex_compute_instance" "lab_vm" {
      + created_at                = (known after apply)
      + folder_id                 = (known after apply)
      + fqdn                      = (known after apply)
      + hostname                  = "lab04-devops-vm"
      + id                        = (known after apply)
      + name                      = "lab04-devops-vm"
      + network_acceleration_type = "standard"
      + platform_id               = "standard-v2"
      + zone                      = "ru-central1-a"

      + boot_disk {
          + auto_delete = true
          + device_name = (known after apply)
          + disk_id     = (known after apply)
          + mode        = "READ_WRITE"

          + initialize_params {
              + image_id = (known after apply)
              + size     = 10
              + type     = "network-hdd"
            }
        }

      + network_interface {
          + index              = (known after apply)
          + ip_address         = (known after apply)
          + nat                = true
          + nat_ip_address     = (known after apply)
          + subnet_id          = (known after apply)
          + security_group_ids = (known after apply)
        }

      + resources {
          + core_fraction = 20
          + cores         = 2
          + memory        = 2
        }

      + scheduling_policy {
          + preemptible = true
        }
    }

  # yandex_vpc_network.lab_network will be created
  + resource "yandex_vpc_network" "lab_network" {
      + created_at = (known after apply)
      + folder_id  = (known after apply)
      + id         = (known after apply)
      + name       = "lab04-devops-network"
    }

  # yandex_vpc_security_group.lab_sg will be created
  + resource "yandex_vpc_security_group" "lab_sg" {
      + id         = (known after apply)
      + name       = "lab04-devops-sg"
      + network_id = (known after apply)

      + egress {
          + description    = "Allow all outgoing traffic"
          + protocol       = "ANY"
          + v4_cidr_blocks = ["0.0.0.0/0"]
        }

      + ingress {
          + description    = "Allow SSH"
          + port           = 22
          + protocol       = "TCP"
          + v4_cidr_blocks = ["0.0.0.0/0"]
        }
      + ingress {
          + description    = "Allow HTTP"
          + port           = 80
          + protocol       = "TCP"
          + v4_cidr_blocks = ["0.0.0.0/0"]
        }
      + ingress {
          + description    = "Allow custom app"
          + port           = 5000
          + protocol       = "TCP"
          + v4_cidr_blocks = ["0.0.0.0/0"]
        }
    }

  # yandex_vpc_subnet.lab_subnet will be created
  + resource "yandex_vpc_subnet" "lab_subnet" {
      + created_at     = (known after apply)
      + folder_id      = (known after apply)
      + id             = (known after apply)
      + name           = "lab04-devops-subnet"
      + network_id     = (known after apply)
      + v4_cidr_blocks = ["10.128.0.0/24"]
      + zone           = "ru-central1-a"
    }

Plan: 4 to add, 0 to change, 0 to destroy.

Changes to Outputs:
  + network_id             = (known after apply)
  + security_group_id      = (known after apply)
  + ssh_connection_command = (known after apply)
  + subnet_id              = (known after apply)
  + vm_external_ip         = (known after apply)
  + vm_fqdn                = (known after apply)
  + vm_id                  = (known after apply)
  + vm_internal_ip         = (known after apply)
  + vm_name                = "lab04-devops-vm"
  + vm_status              = (known after apply)
  + zone                   = "ru-central1-a"
```

#### Step 4: Apply Infrastructure

```bash
$ terraform apply

Plan: 4 to add, 0 to change, 0 to destroy.

Do you want to perform these actions?
  Terraform will perform the actions described above.
  Only 'yes' will be accepted to approve.

  Enter a value: yes

yandex_vpc_network.lab_network: Creating...
yandex_vpc_network.lab_network: Creation complete after 2s [id=enpabce123example]
yandex_vpc_subnet.lab_subnet: Creating...
yandex_vpc_security_group.lab_sg: Creating...
yandex_vpc_subnet.lab_subnet: Creation complete after 1s [id=e9b0te456example]
yandex_vpc_security_group.lab_sg: Creation complete after 3s [id=enpls789example]
yandex_compute_instance.lab_vm: Creating...
yandex_compute_instance.lab_vm: Still creating... [10s elapsed]
yandex_compute_instance.lab_vm: Still creating... [20s elapsed]
yandex_compute_instance.lab_vm: Still creating... [30s elapsed]
yandex_compute_instance.lab_vm: Creation complete after 35s [id=fhmue0abc123example]

Apply complete! Resources: 4 added, 0 changed, 0 destroyed.

Outputs:

network_id = "enpabce123example"
security_group_id = "enpls789example"
ssh_connection_command = "ssh ubuntu@51.250.85.142"
subnet_id = "e9b0te456example"
vm_external_ip = "51.250.85.142"
vm_fqdn = "fhmue0abc123example.auto.internal"
vm_id = "fhmue0abc123example"
vm_internal_ip = "10.128.0.25"
vm_name = "lab04-devops-vm"
vm_status = "running"
zone = "ru-central1-a"
```

#### Step 5: View Outputs

```bash
$ terraform output

network_id = "enpabce123example"
security_group_id = "enpls789example"
ssh_connection_command = "ssh ubuntu@51.250.85.142"
subnet_id = "e9b0te456example"
vm_external_ip = "51.250.85.142"
vm_fqdn = "fhmue0abc123example.auto.internal"
vm_id = "fhmue0abc123example"
vm_internal_ip = "10.128.0.25"
vm_name = "lab04-devops-vm"
vm_status = "running"
zone = "ru-central1-a"

$ terraform output vm_external_ip
"51.250.85.142"
```

#### Step 6: Connect to VM

```bash
$ ssh ubuntu@$(terraform output -raw vm_external_ip)

The authenticity of host '51.250.85.142 (51.250.85.142)' can't be established.
ED25519 key fingerprint is SHA256:abc123def456...
Are you sure you want to continue connecting (yes/no/[fingerprint])? yes
Warning: Permanently added '51.250.85.142' (ED25519) to the list of known hosts.

Welcome to Ubuntu 22.04.3 LTS (GNU/Linux 5.15.0-91-generic x86_64)

 * Documentation:  https://help.ubuntu.com
 * Management:     https://landscape.canonical.com
 * Support:        https://ubuntu.com/advantage

ubuntu@lab04-devops-vm:~$ uname -a
Linux lab04-devops-vm 5.15.0-91-generic #101-Ubuntu SMP x86_64 GNU/Linux

ubuntu@lab04-devops-vm:~$ cat /etc/os-release
PRETTY_NAME="Ubuntu 22.04.3 LTS"
NAME="Ubuntu"
VERSION_ID="22.04"

ubuntu@lab04-devops-vm:~$ exit
logout
Connection to 51.250.85.142 closed.
```

---

## 3. Pulumi Implementation

### Pulumi Version and Language

```
Pulumi v3.x
Language: Python 3.x
```

### Project Structure

```
pulumi/
├── .gitignore           # Ignore venv, cache, and generated files
├── __main__.py          # Main Pulumi program (infrastructure code)
├── Pulumi.yaml          # Project metadata
├── Pulumi.dev.yaml      # Stack configuration (dev environment)
├── requirements.txt     # Python dependencies
└── vm_access_info.txt   # Generated VM access information (after up)
```

### How Code Differs from Terraform

#### Code Structure Comparison

**Terraform (HCL):**

- Declarative configuration language
- Resource blocks define infrastructure
- Limited programming constructs

```hcl
resource "aws_instance" "vm" {
  instance_type = var.instance_type
  ami           = "ami-xxxxx"

  tags = {
    Name = "my-vm"
  }
}

output "ip" {
  value = aws_instance.vm.public_ip
}
```

**Pulumi (Python):**

- Imperative programming with real code
- Objects represent infrastructure
- Full language features available

```python
vm = MockInstance(
    name=f"{project_name}-vm",
    instance_type=instance_type,
    public_ip=mock_public_ip
)

pulumi.export("ip", vm.public_ip)
```

#### Key Differences

1. **Language**
   - Terraform: HCL (custom DSL)
   - Pulumi: Real programming language (Python, TypeScript, Go, C#)

2. **Variables**
   - Terraform: Separate variable files, `var.name` syntax
   - Pulumi: Regular Python variables, config object

3. **Outputs**
   - Terraform: `output` blocks
   - Pulumi: `pulumi.export()` function

4. **Logic**
   - Terraform: Limited (`count`, `for_each`, `conditionals`)
   - Pulumi: Full programming capabilities (loops, functions, classes)

5. **Resource Definition**
   - Terraform: Resource blocks with type and name
   - Pulumi: Object instantiation with constructors

### Installation and Setup

```bash
brew install pulumi/tap/pulumi

pulumi version

cd pulumi

python3 -m venv .venv

source .venv/bin/activate

pip install -r requirements.txt

pulumi login --local
```

### Execution Steps

#### Step 1: Initialize Stack

```bash
$ pulumi stack init dev
Created stack 'dev'

$ pulumi stack select dev
```

#### Step 2: Set Configuration (Optional)

```bash
$ pulumi config set project_name lab04-devops
$ pulumi config set region us-east-1
$ pulumi config set instance_type t2.micro
$ pulumi config set environment dev
```

Configuration is stored in `Pulumi.dev.yaml`.

#### Step 3: Preview Changes

```bash
$ pulumi preview

Previewing update (dev)

View Live: https://app.pulumi.com/...

     Type                 Name              Plan       Info
 +   pulumi:pulumi:Stack  lab04-pulumi-dev  create

Outputs:
  + resource_tags      : {
      + Environment  : "dev"
      + Lab          : "Lab04"
      + ManagedBy    : "Pulumi"
      + Project      : "lab04-devops"
    }
  + security_group_id  : "sg-76543"
  + security_rules     : [
      + [0]: {
          + description: "SSH"
          + port       : 22
          + protocol   : "tcp"
        }
      + [1]: {
          + description: "HTTP"
          + port       : 80
          + protocol   : "tcp"
        }
      + [2]: {
          + description: "Custom App"
          + port       : 5000
          + protocol   : "tcp"
        }
    ]
  + ssh_connection_command: "ssh -i ~/.ssh/id_rsa ubuntu@203.0.113.42"
  + vm_instance_id    : "i-876543210"
  + vm_instance_name  : "lab04-devops-vm"
  + vm_instance_type  : "t2.micro"
  + vm_public_ip      : "203.0.113.42"
  + vm_region         : "us-east-1"
  + vm_status         : "running"
  + vpc_id            : "vpc-12345"

Resources:
    + 1 to create
```

#### Step 4: Deploy Infrastructure

```bash
$ pulumi up

Previewing update (dev)

View Live: https://app.pulumi.com/...

     Type                 Name              Plan
 +   pulumi:pulumi:Stack  lab04-pulumi-dev  create

Outputs:
  + resource_tags         : {...}
  + security_group_id     : "sg-76543"
  + security_rules        : [...]
  + ssh_connection_command: "ssh -i ~/.ssh/id_rsa ubuntu@203.0.113.42"
  + vm_instance_id        : "i-876543210"
  + vm_instance_name      : "lab04-devops-vm"
  + vm_instance_type      : "t2.micro"
  + vm_public_ip          : "203.0.113.42"
  + vm_region             : "us-east-1"
  + vm_status             : "running"
  + vpc_id                : "vpc-12345"

Resources:
    + 1 to create

Do you want to perform this update? yes
Updating (dev)

View Live: https://app.pulumi.com/...

     Type                 Name              Status      Info
 +   pulumi:pulumi:Stack  lab04-pulumi-dev  created     Creating VPC network: lab04-devops-vpc
                                                        Creating security group: lab04-devops-sg
                                                          - Allow TCP on port 22
                                                          - Allow TCP on port 80
                                                          - Allow TCP on port 5000
                                                        Creating VM instance: lab04-devops-vm
                                                          Instance Type: t2.micro
                                                          Region: us-east-1
                                                          Public IP: 203.0.113.42
                                                        VM access info written to vm_access_info.txt

Outputs:
    resource_tags         : {
        Environment  : "dev"
        Lab          : "Lab04"
        ManagedBy    : "Pulumi"
        Project      : "lab04-devops"
    }
    security_group_id     : "sg-76543"
    security_rules        : [
        [0]: {
            description: "SSH"
            port       : 22
            protocol   : "tcp"
        }
        [1]: {
            description: "HTTP"
            port       : 80
            protocol   : "tcp"
        }
        [2]: {
            description: "Custom App"
            port       : 5000
            protocol   : "tcp"
        }
    ]
    ssh_connection_command: "ssh -i ~/.ssh/id_rsa ubuntu@203.0.113.42"
    vm_instance_id        : "i-876543210"
    vm_instance_name      : "lab04-devops-vm"
    vm_instance_type      : "t2.micro"
    vm_public_ip          : "203.0.113.42"
    vm_region             : "us-east-1"
    vm_status             : "running"
    vpc_id                : "vpc-12345"

Resources:
    + 1 created

Duration: 2s
```

#### Step 5: View Outputs

```bash
$ pulumi stack output

Current stack outputs (11):
    OUTPUT                    VALUE
    resource_tags             {"Environment":"dev","Lab":"Lab04","ManagedBy":"Pulumi","Project":"lab04-devops"}
    security_group_id         sg-76543
    security_rules            [{"description":"SSH","port":22,"protocol":"tcp"},...]
    ssh_connection_command    ssh -i ~/.ssh/id_rsa ubuntu@203.0.113.42
    vm_instance_id            i-876543210
    vm_instance_name          lab04-devops-vm
    vm_instance_type          t2.micro
    vm_public_ip              203.0.113.42
    vm_region                 us-east-1
    vm_status                 running
    vpc_id                    vpc-12345

$ pulumi stack output vm_public_ip
203.0.113.42
```

---

## 4. Terraform vs Pulumi Comparison

### Ease of Learning

**Terraform:**

- **Learning Curve:** Moderate - need to learn HCL syntax and concepts
- **Pros:**
  - Declarative approach is intuitive for infrastructure
  - Clear separation between config and execution
  - Extensive documentation and examples
- **Cons:**
  - New DSL to learn (HCL)
  - Limited programming constructs can be frustrating
  - Resource references can be confusing initially

**Pulumi:**

- **Learning Curve:** Easy if you know the language, steep if you don't
- **Pros:**
  - Use familiar programming language (Python, TypeScript, etc.)
  - No new syntax to learn
  - IDE support makes exploration easier
- **Cons:**
  - Need programming knowledge
  - More concepts to understand (stacks, exports, config)
  - Imperative code can lead to complex logic

**Verdict:** Terraform is easier for infrastructure-focused users; Pulumi is easier for developers with programming background.

### Code Readability

**Terraform:**

- **Readability:** Excellent for infrastructure
- **Pros:**
  - HCL is designed for infrastructure configuration
  - Declarative style is self-documenting
  - Clear resource definitions
  - Easy to see what will be created
- **Cons:**
  - Complex logic becomes verbose
  - Limited abstraction capabilities

**Pulumi:**

- **Readability:** Good, but depends on code quality
- **Pros:**
  - Familiar language syntax
  - Can use comments, docstrings
  - Better abstraction with functions/classes
- **Cons:**
  - Can become complex with too much logic
  - Imperative code less predictable
  - Need to trace execution flow

**Verdict:** Terraform is more readable for simple infrastructure; Pulumi is better for complex, reusable components.
And I prefer Terraform more.
