# Lab 4 — Infrastructure as Code

## Cloud Provider & Infrastructure

- Provider: Yandex Cloud
    - Chosen because it's accessible in Russia, offers a generous free tier, and has good integration with Terraform.

- Region/Zone: ru-central1-a – closest to my location, ensuring low latency.

- Instance Type: standard-v2 with 2 vCPUs, 1 GB RAM, 20% core fraction (free tier).

- OS Image: Ubuntu 22.04 LTS – fetched using Yandex Cloud CLI (yc compute image get-latest-from-family ubuntu-2204-lts --folder-id standard-images) to get the latest image ID, then hardcoded in the Terraform configuration.

- Resources Created:
    - yandex_vpc_network – a virtual network for the VM.
    - yandex_vpc_subnet – a subnet within the network.
    - yandex_vpc_security_group – firewall rules allowing SSH (22), HTTP (80), and port 5000.
    - yandex_compute_instance – the virtual machine with a public IP.

- Security Group Rules:
    - SSH (22) – restricted to my public IP only.
    - HTTP (80) – open to all (0.0.0.0/0).
    - Port 5000 – open to all (for future application deployment).

- Public IP of VM: 91.108.189.144 (temporary; will be released when VM is destroyed).

- Variables Used: folder_id, key_file (path to service account JSON key), public_key_path (path to SSH public key). All defined in terraform.tfvars (gitignored).

- Outputs Defined:
    - vm_public_ip – the public IP address of the VM.
    - ssh_command – the full SSH command to connect.

---

## Terraform Implementation

### Version

```bash
 󰘧 terraform version
Terraform v1.14.3
on linux_amd64
```

### Project Structure

```
terraform/
├── authorized_key.json      # Service account key (gitignored)
├── main.tf                   # Main resources (network, security group, VM)
├── outputs.tf                # Output definitions
├── terraform.tfstate         # State file (gitignored)
├── terraform.tfstate.backup  # Backup state (gitignored)
├── terraform.tfvars          # Variable values (gitignored)
└── variables.tf              # Input variable declarations
```

- .gitignore configured to exclude *.tfstate, *.tfstate.*, .terraform/, terraform.tfvars, *.json, and other sensitive files.

### Key Configuration Decisions

- Free tier instance – to avoid costs while meeting lab requirements.
- Region ru-central1-a – proximity and free tier availability.
- Security group – SSH locked to my IP for security; HTTP and port 5000 open for future labs.
- Image ID – obtained via yc CLI to ensure the latest Ubuntu 22.04 LTS, then hardcoded in main.tf (no data source used).

### Challenges Encountered
- Terraform registry blocked in Russia – The default provider registry at registry.terraform.io was inaccessible.
    - Solution: Configured a local .terraformrc file to use the Yandex Cloud mirror:

```hcl
    provider_installation {
      network_mirror {
        url = "https://terraform-mirror.yandexcloud.net/"
        include = ["yandex-cloud/yandex"]
      }
      direct {
        exclude = ["yandex-cloud/yandex"]
      }
    }
```

This allowed terraform init to succeed (with a warning about lock file checksums, which is expected when using a mirror).

### Terminal Outputs

```bash
 󰘧 terraform init
Initializing the backend...
Initializing provider plugins...
- Finding latest version of yandex-cloud/yandex...
- Installing yandex-cloud/yandex v0.187.0...
- Installed yandex-cloud/yandex v0.187.0 (unauthenticated)
Terraform has created a lock file .terraform.lock.hcl to record the provider
selections it made above. Include this file in your version control repository
so that Terraform can guarantee to make the same selections by default when
you run "terraform init" in the future.

╷
│ Warning: Incomplete lock file information for providers
│
│ Due to your customized provider installation methods, Terraform was forced to calculate
│ lock file checksums locally for the following providers:
│   - yandex-cloud/yandex
│
│ The current .terraform.lock.hcl file only includes checksums for linux_amd64, so Terraform
│ running on another platform will fail to install these providers.
│
│ To calculate additional checksums for another platform, run:
│   terraform providers lock -platform=linux_amd64
│ (where linux_amd64 is the platform to generate)
╵
Terraform has been successfully initialized!
```

```bash
 󰘧 terraform plan
yandex_vpc_network.lab_network: Refreshing state... [id=enp**********]
yandex_vpc_subnet.lab_subnet: Refreshing state... [id=e9b**********]
yandex_vpc_security_group.lab_sg: Refreshing state... [id=enp**********]

Terraform will perform the following actions:

  # yandex_compute_instance.lab_vm will be created
  + resource "yandex_compute_instance" "lab_vm" {
      + name                      = "lab-vm"
      + platform_id               = "standard-v2"
      + zone                      = "ru-central1-a"
      ...
      + boot_disk {
          + initialize_params {
              + image_id    = "fd88m3uah9t47loeseir"   # Ubuntu 22.04 LTS
              + size        = 10
            }
        }
      + network_interface {
          + nat                = true
          + security_group_ids = ["enp**********"]
          + subnet_id          = "e9b**********"
        }
      + resources {
          + core_fraction = 20
          + cores         = 2
          + memory        = 1
        }
    }

Plan: 1 to add, 0 to change, 0 to destroy.

Changes to Outputs:
  + ssh_command  = (known after apply)
  + vm_public_ip = (known after apply)
```

```bash
 󰘧 terraform apply
yandex_vpc_network.lab_network: Refreshing state... [id=enp**********]
yandex_vpc_subnet.lab_subnet: Refreshing state... [id=e9b**********]
yandex_vpc_security_group.lab_sg: Refreshing state... [id=enp*********]

Terraform used the selected providers to generate the following execution plan...
Plan: 1 to add, 0 to change, 0 to destroy.

Do you want to perform these actions?
  Terraform will perform the actions described above.
  Only 'yes' will be accepted to approve.

  Enter a value: yes

yandex_compute_instance.lab_vm: Creating...
yandex_compute_instance.lab_vm: Still creating... [10s elapsed]
yandex_compute_instance.lab_vm: Still creating... [20s elapsed]
yandex_compute_instance.lab_vm: Still creating... [30s elapsed]
yandex_compute_instance.lab_vm: Still creating... [40s elapsed]
yandex_compute_instance.lab_vm: Creation complete after 40s [id=fhm**********]

Apply complete! Resources: 1 added, 0 changed, 0 destroyed.

Outputs:

ssh_command = "ssh ubuntu@93.77.186.188"
vm_public_ip = "93.77.186.188"

SSH Access Verification
```

```bash
 󰘧 ssh ubuntu@93.77.186.188
Welcome to Ubuntu 22.04.5 LTS (GNU/Linux 5.15.0-170-generic x86_64)

 * Documentation:  https://help.ubuntu.com
 * Management:     https://landscape.canonical.com
 * Support:        https://ubuntu.com/pro

 System information as of Tue Feb 17 21:23:04 UTC 2026

  System load:  0.0               Processes:             91
  Usage of /:   19.6% of 9.04GB   Users logged in:       0
  Memory usage: 17%               IPv4 address for eth0: 192.168.10.18
  Swap usage:   0%

...
Last login: Tue Feb 17 21:11:50 2026 from 188.130.155.186
ubuntu@lab-vm:~$
```

- The VM is accessible and the security group correctly restricts SSH to my IP.

---

## Pulumi Implementation

### Version & Language

```bash
$ pulumi version
v3.148.0
$ python --version
Python 3.12.9  # Had to downgrade from 3.13 due to library compatibility issues
```

### Project Structure

```text
pulumi/
├── __main__.py          # Main infrastructure code
├── requirements.txt     # Python dependencies (pulumi, pulumi-yandex)
├── Pulumi.yaml         # Project metadata
├── Pulumi.lab4.yaml    # Stack configuration (gitignored)
└── .venv/               # Python virtual environment
```

### Key Differences from Terraform
- Imperative approach – Resources are created in code order using Python
- Separate rule resources – Security group rules must be defined as individual resources
- Data sources – Use yandex.get_compute_image() instead of data blocks

### Challenges Encountered
- Python 3.13 incompatibility – The pulumi-yandex library did not work with Python 3.13. Had to downgrade to Python 3.12.
- NixOS dynamic linking issues – libstdc++.so.6 was missing, requiring LD_LIBRARY_PATH workaround.
- Imperative paradigm frustration – As a NixOS user who values declarative configuration, Pulumi's imperative approach felt counterintuitive for infrastructure.

### Terminal Outputs

```bash
$ pulumi preview
Previewing update (lab4)

     Type                                  Name              Plan
 +   pulumi:pulumi:Stack                   lab4-pulumi-lab4  create
 +   ├─ yandex:index:VpcNetwork            lab-network       create
 +   ├─ yandex:index:VpcSubnet             lab-subnet        create
 +   ├─ yandex:index:VpcSecurityGroup      lab-sg            create
 +   ├─ yandex:index:VpcSecurityGroupRule  ssh-rule          create
 +   ├─ yandex:index:VpcSecurityGroupRule  http-rule         create
 +   ├─ yandex:index:VpcSecurityGroupRule  app-rule          create
 +   ├─ yandex:index:VpcSecurityGroupRule  egress-rule       create
 +   └─ yandex:index:ComputeInstance       lab-vm            create

Resources:
    + 9 to create
```

```bash
$ pulumi up -y
Updating (lab4)

     Type                                  Name              Status
 +   pulumi:pulumi:Stack                   lab4-pulumi-lab4  created (69s)
 +   ├─ yandex:index:VpcNetwork            lab-network       created (3s)
 +   ├─ yandex:index:VpcSubnet             lab-subnet        created (1s)
 +   ├─ yandex:index:VpcSecurityGroup      lab-sg            created (3s)
 +   ├─ yandex:index:VpcSecurityGroupRule  ssh-rule          created (0.62s)
 +   ├─ yandex:index:VpcSecurityGroupRule  egress-rule       created (2s)
 +   ├─ yandex:index:ComputeInstance       lab-vm            created (60s)
 +   ├─ yandex:index:VpcSecurityGroupRule  http-rule         created (1s)
 +   └─ yandex:index:VpcSecurityGroupRule  app-rule          created (3s)

Outputs:
    ssh_command : "ssh ubuntu@89.169.129.134"
    vm_public_ip: "89.169.129.134"

Resources:
    + 9 created

SSH Verification
```

```bash
$ ssh ubuntu@89.169.129.134
Welcome to Ubuntu 22.04.5 LTS...
ubuntu@fhm99g1r2e3jtaitilb2:~$
```

---

## Terraform vs Pulumi Comparison

| Aspect | Terraform | Pulumi |
|--------|-----------|--------|
| **Ease of Learning** | Straightforward – HCL is simple and purpose-built for infrastructure | Steep learning curve – requires programming knowledge and understanding of provider API differences |
| **Code Readability** | Clear declarative syntax – what you see is what you get | Mixed – Python logic interspersed with resource definitions makes it harder to parse |
| **Debugging** | Clear error messages pointing to specific HCL lines | Python stack traces that often lead into provider internals |
| **Documentation** | Excellent – comprehensive provider docs with examples | Adequate but examples often lag behind API changes |
| **Setup Complexity** | Minor – just need to configure provider mirror | Significant – Python version compatibility, dynamic linking issues on NixOS |
| **Philosophy** | **Declarative** – you describe the end state | **Imperative** – you write code to achieve the state |

### Personal Experience & Verdict

As a NixOS user who values declarative configuration and reproducibility, Pulumi was a frustrating experience:
- Imperative by nature – Infrastructure as Code should describe what you want, not how to create it. Pulumi's imperative approach mixes infrastructure logic with programming constructs, making configurations harder to reason about.
- Python version hell – The Yandex provider didn't work with Python 3.13, forcing a downgrade. This is exactly the kind of dependency management I expect from application code, not infrastructure tooling.
- System integration issues – On NixOS, Pulumi's dynamic linking required libstdc++.so.6 workarounds. Terraform, being a statically compiled Go binary, just works.
- Unnecessary complexity – I see no compelling reason for Pulumi to exist. It solves problems that don't need solving and creates new ones in the process.

Final Verdict: Terraform is the clear winner. It's purpose-built, declarative, and "just works." Pulumi feels like solving infrastructure problems with application development tools – a square peg in a round hole.

---

## Lab 5 Preparation & Cleanup

### VM for Lab 5

- Plan: I will **not** keep this VM running continuously. To avoid unnecessary costs, I will destroy it after completing Lab 4.
- Before Lab 5 (Ansible), I will recreate the VM using the same Terraform code. This demonstrates the reproducibility of infrastructure as code.
- Current Status: The VM is still running and accessible (as shown above).

### Cleanup Status
- I have not destroyed the resources yet because I want to keep them for the documentation and to show the VM is functional.
- Before moving on, I will run terraform destroy to remove all resources. The output of terraform destroy will be similar to the apply but with - destroy actions.

### Summary
- Successfully provisioned a VM on Yandex Cloud using Terraform.
- Overcame the challenge of a blocked Terraform registry by using the Yandex mirror.
- Verified SSH connectivity with proper security restrictions.
- Documented the entire process and prepared for Lab 5 by planning to recreate the infrastructure on demand.
