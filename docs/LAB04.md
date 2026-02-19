# `terraform plan` output

```bash
✔ ~/IU/DevOps/DevOps-Core-Course/terraform [lab03 L|✚ 1…1] 
✔ ~/IU/DevOps/DevOps-Core-Course/terraform [lab03 L|✚ 1…2] 
19:15 $ terraform plan
data.yandex_vpc_network.default: Reading...
yandex_compute_disk.boot-disk-1: Refreshing state... [id=fhm4gga0vvd9g93iuo1f]
data.yandex_vpc_network.default: Read complete after 0s [id=enpmijufk1nqbpkj5bl4]

Terraform used the selected providers to generate the following execution plan. Resource actions are indicated with the following symbols:
  + create

Terraform will perform the following actions:

  # yandex_compute_instance.vm-1 will be created
  + resource "yandex_compute_instance" "vm-1" {
      + created_at                = (known after apply)
      + folder_id                 = (known after apply)
      + fqdn                      = (known after apply)
      + gpu_cluster_id            = (known after apply)
      + hardware_generation       = (known after apply)
      + hostname                  = (known after apply)
      + id                        = (known after apply)
      + maintenance_grace_period  = (known after apply)
      + maintenance_policy        = (known after apply)
      + metadata                  = {
          + "ssh-keys" = (sensitive value)
        }
      + name                      = "limbo16-yc-vm-name"
      + network_acceleration_type = "standard"
      + platform_id               = "standard-v1"
      + status                    = (known after apply)
      + zone                      = "ru-central1-a"

      + boot_disk {
          + auto_delete = true
          + device_name = (known after apply)
          + disk_id     = "fhm4gga0vvd9g93iuo1f"
          + mode        = (known after apply)

          + initialize_params (known after apply)
        }

      + metadata_options (known after apply)

      + network_interface {
          + index          = (known after apply)
          + ip_address     = (known after apply)
          + ipv4           = true
          + ipv6           = (known after apply)
          + ipv6_address   = (known after apply)
          + mac_address    = (known after apply)
          + nat            = true
          + nat_ip_address = (known after apply)
          + nat_ip_version = (known after apply)
          + subnet_id      = (known after apply)
        }

      + placement_policy (known after apply)

      + resources {
          + core_fraction = 100
          + cores         = 2
          + memory        = 2
        }

      + scheduling_policy (known after apply)
    }

  # yandex_vpc_subnet.default-subnet will be created
  + resource "yandex_vpc_subnet" "default-subnet" {
      + created_at     = (known after apply)
      + folder_id      = (known after apply)
      + id             = (known after apply)
      + labels         = (known after apply)
      + name           = "subnet-terraform"
      + network_id     = "enpmijufk1nqbpkj5bl4"
      + v4_cidr_blocks = [
          + "192.168.10.0/24",
        ]
      + v6_cidr_blocks = (known after apply)
      + zone           = "ru-central1-a"
    }

Plan: 2 to add, 0 to change, 0 to destroy.

Changes to Outputs:
  + external_ip_address_vm_1 = (known after apply)
  + internal_ip_address_vm_1 = (known after apply)

──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

Note: You didn't use the -out option to save this plan, so Terraform can't guarantee to take exactly these actions if you run "terraform apply" now.
```
# `terraform apply` output

```bash
✔ ~/IU/DevOps/DevOps-Core-Course/terraform [lab03 L|✚ 1…2] 
19:15 $ terraform apply
data.yandex_vpc_network.default: Reading...
yandex_compute_disk.boot-disk-1: Refreshing state... [id=fhm4gga0vvd9g93iuo1f]
data.yandex_vpc_network.default: Read complete after 0s [id=enpmijufk1nqbpkj5bl4]

Terraform used the selected providers to generate the following execution plan. Resource actions are indicated with the following symbols:
  + create

Terraform will perform the following actions:

  # yandex_compute_instance.vm-1 will be created
  + resource "yandex_compute_instance" "vm-1" {
      + created_at                = (known after apply)
      + folder_id                 = (known after apply)
      + fqdn                      = (known after apply)
      + gpu_cluster_id            = (known after apply)
      + hardware_generation       = (known after apply)
      + hostname                  = (known after apply)
      + id                        = (known after apply)
      + maintenance_grace_period  = (known after apply)
      + maintenance_policy        = (known after apply)
      + metadata                  = {
          + "ssh-keys" = (sensitive value)
        }
      + name                      = "limbo16-yc-vm-name"
      + network_acceleration_type = "standard"
      + platform_id               = "standard-v1"
      + status                    = (known after apply)
      + zone                      = "ru-central1-a"

      + boot_disk {
          + auto_delete = true
          + device_name = (known after apply)
          + disk_id     = "fhm4gga0vvd9g93iuo1f"
          + mode        = (known after apply)

          + initialize_params (known after apply)
        }

      + metadata_options (known after apply)

      + network_interface {
          + index          = (known after apply)
          + ip_address     = (known after apply)
          + ipv4           = true
          + ipv6           = (known after apply)
          + ipv6_address   = (known after apply)
          + mac_address    = (known after apply)
          + nat            = true
          + nat_ip_address = (known after apply)
          + nat_ip_version = (known after apply)
          + subnet_id      = (known after apply)
        }

      + placement_policy (known after apply)

      + resources {
          + core_fraction = 100
          + cores         = 2
          + memory        = 2
        }

      + scheduling_policy (known after apply)
    }

  # yandex_vpc_subnet.default-subnet will be created
  + resource "yandex_vpc_subnet" "default-subnet" {
      + created_at     = (known after apply)
      + folder_id      = (known after apply)
      + id             = (known after apply)
      + labels         = (known after apply)
      + name           = "subnet-terraform"
      + network_id     = "enpmijufk1nqbpkj5bl4"
      + v4_cidr_blocks = [
          + "192.168.10.0/24",
        ]
      + v6_cidr_blocks = (known after apply)
      + zone           = "ru-central1-a"
    }

Plan: 2 to add, 0 to change, 0 to destroy.

Changes to Outputs:
  + external_ip_address_vm_1 = (known after apply)
  + internal_ip_address_vm_1 = (known after apply)

Do you want to perform these actions?
  Terraform will perform the actions described above.
  Only 'yes' will be accepted to approve.

  Enter a value: yes

yandex_vpc_subnet.default-subnet: Creating...
yandex_vpc_subnet.default-subnet: Creation complete after 1s [id=e9b6b6rhinijmtk1jp0a]
yandex_compute_instance.vm-1: Creating...
yandex_compute_instance.vm-1: Still creating... [00m10s elapsed]
yandex_compute_instance.vm-1: Still creating... [00m20s elapsed]
yandex_compute_instance.vm-1: Still creating... [00m30s elapsed]
yandex_compute_instance.vm-1: Creation complete after 39s [id=fhmh7kjp0l2prr6usfo0]

Apply complete! Resources: 2 added, 0 changed, 0 destroyed.

Outputs:

external_ip_address_vm_1 = "93.77.191.77"
internal_ip_address_vm_1 = "192.168.10.17"
```

# `pulumi preview` output
```bash
(venv) ✘-255 ~/IU/DevOps/DevOps-Core-Course/pulumi [lab03 L|✚ 1…3] 
19:51 $ pulumi preview
Previewing update (dev)

View in Browser (Ctrl+O): https://app.pulumi.com/ebortsov-org/pulumni_lab04/dev/previews/53aa1f8a-8734-45db-b0ce-eb48cac66377

     Type                                  Name               Plan       
     pulumi:pulumi:Stack                   pulumni_lab04-dev             
 +   ├─ yandex:index:VpcNetwork            main-network       create     
 +   ├─ yandex:index:VpcSubnet             main-subnet        create     
 +   ├─ yandex:index:VpcSecurityGroup      web-sg             create     
 +   ├─ yandex:index:VpcSecurityGroupRule  ssh-rule           create     
 +   ├─ yandex:index:VpcSecurityGroupRule  http-rule          create     
 +   ├─ yandex:index:VpcSecurityGroupRule  egress-rule        create     
 +   └─ yandex:index:ComputeInstance       web-server         create     

Outputs:
  + instance_id: [unknown]
  + public_ip  : [unknown]

Resources:
    + 7 to create
    1 unchanged
```

# `pulumi up` output
```bash
(venv) ✔ ~/IU/DevOps/DevOps-Core-Course/pulumi [lab03 L|✚ 1…3] 
19:52 $ pulumi up
Previewing update (dev)

View in Browser (Ctrl+O): https://app.pulumi.com/ebortsov-org/pulumni_lab04/dev/previews/4eddbb51-8c6d-4b85-a4ab-686f263368f0

     Type                                  Name               Plan       
     pulumi:pulumi:Stack                   pulumni_lab04-dev             
 +   ├─ yandex:index:VpcNetwork            main-network       create     
 +   ├─ yandex:index:VpcSubnet             main-subnet        create     
 +   ├─ yandex:index:VpcSecurityGroup      web-sg             create     
 +   ├─ yandex:index:VpcSecurityGroupRule  ssh-rule           create     
 +   ├─ yandex:index:VpcSecurityGroupRule  http-rule          create     
 +   ├─ yandex:index:VpcSecurityGroupRule  egress-rule        create     
 +   └─ yandex:index:ComputeInstance       web-server         create     

Outputs:
  + instance_id: [unknown]
  + public_ip  : [unknown]

Resources:
    + 7 to create
    1 unchanged

Do you want to perform this update? yes
Updating (dev)

View in Browser (Ctrl+O): https://app.pulumi.com/ebortsov-org/pulumni_lab04/dev/updates/2

     Type                                  Name               Status              
     pulumi:pulumi:Stack                   pulumni_lab04-dev                      
 +   ├─ yandex:index:VpcNetwork            main-network       created (4s)        
 +   ├─ yandex:index:VpcSubnet             main-subnet        created (1s)        
 +   ├─ yandex:index:VpcSecurityGroup      web-sg             created (3s)        
 +   ├─ yandex:index:ComputeInstance       web-server         created (45s)       
 +   ├─ yandex:index:VpcSecurityGroupRule  egress-rule        created (2s)        
 +   ├─ yandex:index:VpcSecurityGroupRule  ssh-rule           created (0.90s)     
 +   └─ yandex:index:VpcSecurityGroupRule  http-rule          created (1s)        

Outputs:
  + instance_id: "fhm8u1csqi6p67a3drr2"
  + public_ip  : "89.169.149.12"

Resources:
    + 7 created
    1 unchanged

Duration: 57s
```

# `pulumi down` output
```bash
(venv) ✔ ~/IU/DevOps/DevOps-Core-Course/pulumi [lab03 L|✚ 1…3] 
19:54 $ pulumi down
Previewing destroy (dev)

View in Browser (Ctrl+O): https://app.pulumi.com/ebortsov-org/pulumni_lab04/dev/previews/8e25c043-5540-49dc-824f-4a5dea94fed0

     Type                                  Name               Plan       
 -   pulumi:pulumi:Stack                   pulumni_lab04-dev  delete     
 -   ├─ yandex:index:VpcSecurityGroupRule  egress-rule        delete     
 -   ├─ yandex:index:ComputeInstance       web-server         delete     
 -   ├─ yandex:index:VpcSecurityGroup      web-sg             delete     
 -   ├─ yandex:index:VpcSubnet             main-subnet        delete     
 -   ├─ yandex:index:VpcSecurityGroupRule  ssh-rule           delete     
 -   ├─ yandex:index:VpcSecurityGroupRule  http-rule          delete     
 -   └─ yandex:index:VpcNetwork            main-network       delete     

Outputs:
  - instance_id: "fhm8u1csqi6p67a3drr2"
  - public_ip  : "89.169.149.12"

Resources:
    - 8 to delete

Do you want to perform this destroy? yes
Destroying (dev)

View in Browser (Ctrl+O): https://app.pulumi.com/ebortsov-org/pulumni_lab04/dev/updates/3

     Type                                  Name               Status              
 -   pulumi:pulumi:Stack                   pulumni_lab04-dev  deleted (0.29s)     
 -   ├─ yandex:index:VpcSecurityGroupRule  ssh-rule           deleted (2s)        
 -   ├─ yandex:index:VpcSecurityGroupRule  http-rule          deleted (3s)        
 -   ├─ yandex:index:VpcSecurityGroupRule  egress-rule        deleted (3s)        
 -   ├─ yandex:index:ComputeInstance       web-server         deleted (33s)       
 -   ├─ yandex:index:VpcSecurityGroup      web-sg             deleted (0.68s)     
 -   ├─ yandex:index:VpcSubnet             main-subnet        deleted (5s)        
 -   └─ yandex:index:VpcNetwork            main-network       deleted (1s)        

Outputs:
  - instance_id: "fhm8u1csqi6p67a3drr2"
  - public_ip  : "89.169.149.12"

Resources:
    - 8 deleted

Duration: 43s

The resources in the stack have been deleted, but the history and configuration associated with the stack are still maintained. 
If you want to remove the stack completely, run `pulumi stack rm dev`.
```

---

## 1. Cloud Provider & Infrastructure

- Cloud provider: `Yandex Cloud`
- Why this provider: available and convenient for this lab setup, with a small-instance workflow suitable for learning IaC.
- Region/zone: `ru-central1-a`
- Instance size used: `2 vCPU`, `2 GB RAM`, `20 GB` boot disk.
- Cost note: lab performed with small resources and cleaned up after verification.

Resources created:
- Terraform part: VM instance, subnet, NAT/public IP (and default network usage).
- Pulumi part: VPC network, subnet, security group, ingress rules (`22`, `80`), egress rule, VM instance, NAT/public IP.

Observed public IPs from run logs:
- Terraform VM: `93.77.191.77`
- Pulumi VM: `89.169.149.12`

## 2. Terraform Implementation

- Terraform version used: `v1.14.5`
- Main files: `terraform/main.tf`, `terraform/variables.tf`, `terraform/outputs.tf`
- Sensitive values handled via variables (`yc_token`, `ssh_public_key` marked sensitive).
- Outputs used for internal/external IP exposure.

Key decisions:
- Reused existing default VPC via data source.
- Parameterized values (zone, VM name, credentials, SSH key).
- Injected SSH key through instance metadata.

Challenges encountered:
- Correct cloud/provider credentials setup and variable wiring.
- Keeping sensitive values out of Git and using `.gitignore` properly.

Required command evidence:
- `terraform plan` output: included above.
- `terraform apply` output: included above.
- `terraform init`: initialization was completed before plan/apply in workflow.
- SSH connection method used: `ssh limbo16@93.77.191.77`

## 3. Pulumi Implementation

- Pulumi version: `v3.221.0`
- Language: `Python`
- Main files: `pulumi/__main__.py`, `pulumi/Pulumi.yaml`, `pulumi/requirements.txt`
- Provider package: `pulumi-yandex`

How code differs from Terraform:
- Terraform uses declarative HCL.
- Pulumi uses Python resource objects and references.
- Security group and each security rule are explicit resources in Pulumi code.

Advantages discovered:
- Native language constructs for logic and reuse.
- Easy file handling for SSH key loading.
- Clear export of outputs (`public_ip`, `instance_id`).

Challenges encountered:
- Managing Python environment/dependencies (`venv`, package versions).
- Additional Pulumi stack/project metadata and state workflow.

Required command evidence:
- `pulumi preview` output: included above.
- `pulumi up` output: included above.
- `pulumi down` output: included above.
- SSH connection method used: `ssh ubuntu@89.169.149.12`

## 4. Terraform vs Pulumi Comparison

Ease of learning:
- Terraform was faster to start for basic VM provisioning.
- Pulumi setup required more initial tooling steps.
- After setup, Pulumi flow felt natural because it is Python code.

Code readability:
- Terraform is compact and clear for straightforward infra.
- Pulumi is more expressive when logic/reuse is needed.
- For larger projects, Pulumi structure can be easier to scale.

Debugging:
- Terraform debugging is very direct through `plan` diff output.
- Pulumi debugging includes provider plus runtime context.
- For small labs, Terraform troubleshooting felt more linear.

Documentation:
- Terraform has broader ecosystem examples and references.
- Pulumi docs are good, but examples are more language-specific.
- For quick issue lookup, Terraform material was easier to find.

Use case preference:
- Terraform: preferred for standard declarative infrastructure.
- Pulumi: preferred when infrastructure needs programming abstractions.
- Practical choice depends on team skills and expected complexity.

## 5. Lab 5 Preparation & Cleanup

VM plan for Lab 5:
- Keeping VM running: `No`
- Plan: recreate required VM from IaC code for Lab 5 when needed.

Cleanup status:
- Pulumi cleanup proof is included above (`pulumi down` shows `8 deleted`).
- Final state for this lab: resources were not intentionally left running.
