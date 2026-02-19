# Lab 4 — Infrastructure as Code (Terraform & Pulumi)

### 1. Cloud Provider & Infrastructure

- Cloud provider chosen and rationale - Aws was chosen as cloud provider because I had everything already setted up to use it.
- Instance type/size and why - Simple tc3.micro was used as it available in free tier (and tc2 isn't accesible at eu-north-1)
- Region/zone selected - eu-north-1
- Total direct cost was 0$
 
### 2. Terraform Implementation

- Terraform version used:
```
terraform -v
Terraform v1.14.5
```
- Project structure explanation: main.tf and terraform.tfvars was placed directly in terraform/
- Challenges encountered: the only challenge was download terraform/aws integration, as the mirror is not working from Russia
- Terminal output from key commands:

1. **Terraform file**

```
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }
  required_version = ">= 1.4.0"
}

provider "aws" {
  region = "eu-north-1"
}

variable "ssh_key_name" {
  description = "Name of the AWS EC2 Key Pair"
  type        = string
}

resource "aws_instance" "vm" {
  ami                    = "ami-0974a2c5ddf10f442"
  instance_type          = "t3.micro"
  key_name               = var.ssh_key_name
  associate_public_ip_address = true

  vpc_security_group_ids = [aws_security_group.ssh.id]

  tags = {
    Name = "ubuntu-vm"
  }
}

resource "aws_security_group" "ssh" {
  name_prefix = "ubuntu-ssh-"

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

output "public_ip" {
  value = aws_instance.vm.public_ip
}
```

- **Terraform plan**

```
$ terraform plan
aws_security_group.ssh: Refreshing state... [id=sg-04997b7f010ca238d]

Terraform used the selected providers to generate the following execution plan. Resource
actions are indicated with the following symbols:
  + create

Terraform will perform the following actions:

  # aws_instance.vm will be created
  + resource "aws_instance" "vm" {
      + ami                                  = "ami-0974a2c5ddf10f442"
      + arn                                  = (known after apply)
      + associate_public_ip_address          = true
      + availability_zone                    = (known after apply)
      + disable_api_stop                     = (known after apply)
      + disable_api_termination              = (known after apply)
      + ebs_optimized                        = (known after apply)
      + enable_primary_ipv6                  = (known after apply)
      + force_destroy                        = false
      + get_password_data                    = false
      + host_id                              = (known after apply)
      + host_resource_group_arn              = (known after apply)
      + iam_instance_profile                 = (known after apply)
      + id                                   = (known after apply)
      + instance_initiated_shutdown_behavior = (known after apply)
      + instance_lifecycle                   = (known after apply)
      + instance_state                       = (known after apply)
      + instance_type                        = "t3.micro"
      + ipv6_address_count                   = (known after apply)
      + ipv6_addresses                       = (known after apply)
      + key_name                             = "my-aws-key"
      + monitoring                           = (known after apply)
      + outpost_arn                          = (known after apply)
      + password_data                        = (known after apply)
      + placement_group                      = (known after apply)
      + placement_group_id                   = (known after apply)
      + placement_partition_number           = (known after apply)
      + primary_network_interface_id         = (known after apply)
      + private_dns                          = (known after apply)
      + private_ip                           = (known after apply)
      + public_dns                           = (known after apply)
      + public_ip                            = (known after apply)
      + region                               = "eu-north-1"
      + secondary_private_ips                = (known after apply)
      + security_groups                      = (known after apply)
      + source_dest_check                    = true
      + spot_instance_request_id             = (known after apply)
      + subnet_id                            = (known after apply)
      + tags                                 = {
          + "Name" = "ubuntu-vm"
        }
      + tags_all                             = {
          + "Name" = "ubuntu-vm"
        }
      + tenancy                              = (known after apply)
      + user_data_base64                     = (known after apply)
      + user_data_replace_on_change          = false
      + vpc_security_group_ids               = [
          + "sg-04997b7f010ca238d",
        ]

      + capacity_reservation_specification (known after apply)

      + cpu_options (known after apply)

      + ebs_block_device (known after apply)

      + enclave_options (known after apply)

      + ephemeral_block_device (known after apply)

      + instance_market_options (known after apply)

      + maintenance_options (known after apply)

      + metadata_options (known after apply)

      + network_interface (known after apply)

      + primary_network_interface (known after apply)

      + private_dns_name_options (known after apply)

      + root_block_device (known after apply)

      + secondary_network_interface (known after apply)
    }

Plan: 1 to add, 0 to change, 0 to destroy.

Changes to Outputs:
  + public_ip = (known after apply)
───────────────────────────────────────────────────────────────────────────────────────────

Note: You didn't use the -out option to save this plan, so Terraform can't guarantee to
take exactly these actions if you run "terraform apply" now.
```

- **Terraform apply**

```
$ terraform apply
aws_security_group.ssh: Refreshing state... [id=sg-04997b7f010ca238d]

Terraform used the selected providers to generate the following execution plan. Resource
actions are indicated with the following symbols:
  + create

Terraform will perform the following actions:

  # aws_instance.vm will be created
  + resource "aws_instance" "vm" {
      + ami                                  = "ami-0974a2c5ddf10f442"
      + arn                                  = (known after apply)
      + associate_public_ip_address          = true
      + availability_zone                    = (known after apply)
      + disable_api_stop                     = (known after apply)
      + disable_api_termination              = (known after apply)
      + ebs_optimized                        = (known after apply)
      + enable_primary_ipv6                  = (known after apply)
      + force_destroy                        = false
      + get_password_data                    = false
      + host_id                              = (known after apply)
      + host_resource_group_arn              = (known after apply)
      + iam_instance_profile                 = (known after apply)
      + id                                   = (known after apply)
      + instance_initiated_shutdown_behavior = (known after apply)
      + instance_lifecycle                   = (known after apply)
      + instance_state                       = (known after apply)
      + instance_type                        = "t3.micro"
      + ipv6_address_count                   = (known after apply)
      + ipv6_addresses                       = (known after apply)
      + key_name                             = "my-aws-key"
      + monitoring                           = (known after apply)
      + outpost_arn                          = (known after apply)
      + password_data                        = (known after apply)
      + placement_group                      = (known after apply)
      + placement_group_id                   = (known after apply)
      + placement_partition_number           = (known after apply)
      + primary_network_interface_id         = (known after apply)
      + private_dns                          = (known after apply)
      + private_ip                           = (known after apply)
      + public_dns                           = (known after apply)
      + public_ip                            = (known after apply)
      + region                               = "eu-north-1"
      + secondary_private_ips                = (known after apply)
      + security_groups                      = (known after apply)
      + source_dest_check                    = true
      + spot_instance_request_id             = (known after apply)
      + subnet_id                            = (known after apply)
      + tags                                 = {
          + "Name" = "ubuntu-vm"
        }
      + tags_all                             = {
          + "Name" = "ubuntu-vm"
        }
      + tenancy                              = (known after apply)
      + user_data_base64                     = (known after apply)
      + user_data_replace_on_change          = false
      + vpc_security_group_ids               = [
          + "sg-04997b7f010ca238d",
        ]

      + capacity_reservation_specification (known after apply)

      + cpu_options (known after apply)

      + ebs_block_device (known after apply)

      + enclave_options (known after apply)

      + ephemeral_block_device (known after apply)

      + instance_market_options (known after apply)

      + maintenance_options (known after apply)

      + metadata_options (known after apply)

      + network_interface (known after apply)

      + primary_network_interface (known after apply)
+ private_dns_name_options (known after apply)

      + root_block_device (known after apply)

      + secondary_network_interface (known after apply)
    }

Plan: 1 to add, 0 to change, 0 to destroy.

Changes to Outputs:
  + public_ip = (known after apply)

Do you want to perform these actions?
  Terraform will perform the actions described above.
  Only 'yes' will be accepted to approve.

  Enter a value: yes

aws_instance.vm: Creating...
aws_instance.vm: Still creating... [00m10s elapsed]
aws_instance.vm: Creation complete after 14s [id=i-07c98146e8381e0db]

Apply complete! Resources: 1 added, 0 changed, 0 destroyed.

Outputs:

public_ip = "13.49.137.254"
```

- **Terraform destroy**

```
$ terraform destroy
aws_security_group.ssh: Refreshing state... [id=sg-04997b7f010ca238d]
aws_instance.vm: Refreshing state... [id=i-07c98146e8381e0db]

Terraform used the selected providers to generate the following execution plan. Resource
actions are indicated with the following symbols:
  - destroy

Terraform will perform the following actions:
<...>

Plan: 0 to add, 0 to change, 2 to destroy.

Changes to Outputs:
  - public_ip = "13.49.137.254" -> null

Do you really want to destroy all resources?
  Terraform will destroy all your managed infrastructure, as shown above.
  There is no undo. Only 'yes' will be accepted to confirm.

  Enter a value: yes
aws_instance.vm: Destroying... [id=i-07c98146e8381e0db]
aws_instance.vm: Still destroying... [id=i-07c98146e8381e0db, 00m10s elapsed]
aws_instance.vm: Still destroying... [id=i-07c98146e8381e0db, 00m20s elapsed]
aws_instance.vm: Still destroying... [id=i-07c98146e8381e0db, 00m30s elapsed]
aws_instance.vm: Still destroying... [id=i-07c98146e8381e0db, 00m40s elapsed]
aws_instance.vm: Still destroying... [id=i-07c98146e8381e0db, 00m50s elapsed]
aws_instance.vm: Still destroying... [id=i-07c98146e8381e0db, 01m00s elapsed]
aws_instance.vm: Destruction complete after 1m0s
aws_security_group.ssh: Destroying... [id=sg-04997b7f010ca238d]
aws_security_group.ssh: Destruction complete after 1s

Destroy complete! Resources: 2 destroyed.
```
- **SSH Login**
```
$ ssh -i ~/.ssh/my-aws-key ubuntu@13.49.137.254
Welcome to Ubuntu 24.04.4 LTS (GNU/Linux 6.17.0-1007-aws x86_64)

 * Documentation:  https://help.ubuntu.com
 * Management:     https://landscape.canonical.com
 * Support:        https://ubuntu.com/pro

 System information as of Thu Feb 19 16:01:28 UTC 2026

  System load:  0.07              Temperature:           -273.1 C
  Usage of /:   26.1% of 6.71GB   Processes:             117
  Memory usage: 25%               Users logged in:       0
  Swap usage:   0%                IPv4 address for ens5: 172.31.14.112

<...>

ubuntu@ip-172-31-14-112:~$ exit
logout
Connection to 13.49.137.254 closed.
```

---

### 2. Pulumi Implementation

- Pulumi version and language used: v3.221.0 typescript pulumi was used
- How code differs from Terraform: it's mostly direct terraform to pulumi conversion
- Advantages you discovered: as it can use various languages, including python, some setups are easier to do and understand
- Challenges encounted: I got kernel panic installing pulumi by overwriting some gcc libs with ones required by npm and nodejs 🤕🔫. But no challenges regarding pulumi itself

- **Pulumi config**
- 
Simple typescript config which almost directly replicates terraform one was used:

```
import * as pulumi from "@pulumi/pulumi";
import * as aws from "@pulumi/aws";

const config = new pulumi.Config();
const sshKeyName = config.require("ssh_key_name");

const region = "eu-north-1";
const awsConfig = new pulumi.Config("aws");
awsConfig.region = region;

const sshGroup = new aws.ec2.SecurityGroup("ubuntu-ssh", {
  ingress: [{
    protocol: "tcp",
    fromPort: 22,
    toPort: 22,
    cidrBlocks: ["0.0.0.0/0"],
  }],
  egress: [{
    protocol: "-1",
    fromPort: 0,
    toPort: 0,
    cidrBlocks: ["0.0.0.0/0"],
  }],
});

const vm = new aws.ec2.Instance("ubuntu-vm", {
  instanceType: "t3.micro",
  ami: "ami-0974a2c5ddf10f442",
  keyName: sshKeyName,
  vpcSecurityGroupIds: [sshGroup.id],
  associatePublicIpAddress: true,
  tags: {
    Name: "ubuntu-vm",
  },
});

export const publicIp = vm.publicIp;
```

- **Pulumi preview**

```
$ pulumi preview
Previewing update (projacktor/dev)

View in Browser (Ctrl+O): https://app.pulumi.com/saddogsec/doc/dev/previews/6e9c976c-519f-4c19-b72c-3666467e70b4

     Type                 Name            Plan        Info
     pulumi:pulumi:Stack  docl-dev              
 +-  └─ aws:ec2:Instance  docl      replace     [diff: ~ami,rootBlockDevice

Resources:
    +-1 to replace
    3 unchanged
```

- **Pulumi up**

```
$ pulumi up
Previewing update (saddogsec/dev)

View in Browser (Ctrl+O): https://app.pulumi.com/saddogsec/doc/dev/previews/7d61d76f-4006-4b87-b666-d2abf12240c5

     Type                 Name            Plan        Info
     pulumi:pulumi:Stack  docl-dev              
 +-  └─ aws:ec2:Instance  docl      replace     [diff: ~ami,rootBlockDevice

Resources:
    +-1 to replace
    3 unchanged

Do you want to perform this update? yes
Updating (saddogsec/dev)

View in Browser (Ctrl+O): https://app.pulumi.com/saddogsec/docl/dev/updates/4

     Type                 Name            Status             Info
     pulumi:pulumi:Stack  docl-dev                     
 +-  └─ aws:ec2:Instance  docl      replaced (35s)     [diff: ~ami,rootBloc

Outputs:
  ~ instancePublicIp: "23.20.145.103" => "35.71.98.18"

Resources:
    +-1 replaced
    3 unchanged

Duration: 32s
```

- **SSH**

```
$ ssh -i ~/.ssh/my-aws-key ubuntu@35.71.98.18
Welcome to Ubuntu 24.04.4 LTS (GNU/Linux 6.17.0-1007-aws x86_64)

 * Documentation:  https://help.ubuntu.com
 * Management:     https://landscape.canonical.com
 * Support:        https://ubuntu.com/pro

 System information as of Thu Feb 19 18:31:15 UTC 2026

  System load:  0.07              Temperature:           -273.1 C
  Usage of /:   26.2% of 6.71GB   Processes:             117
  Memory usage: 23%               Users logged in:       0
  Swap usage:   0%                IPv4 address for ens5: 172.30.12.112

<...>

ubuntu@ip-35.71.98.18:~$ exit
logout
Connection to 35.71.98.18 closed.
```
