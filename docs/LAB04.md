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