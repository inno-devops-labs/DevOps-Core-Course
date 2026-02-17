Cloud Provider

Chosen provider: Yandex Cloud

Reason:
Yandex Cloud provides a free grant and free-tier resources suitable for educational use. It is accessible in Russia and integrates well with Terraform via the official provider.

Terraform Version
Terraform v1.14.5
on darwin_arm64

Infrastructure Overview
Region / Zone
ru-central1-a

VM Configuration

Platform: standard-v1

CPU: 2 cores

Core fraction: 20%

RAM: 2 GB

Disk: 10 GB network-ssd

OS: Ubuntu 24.04 LTS

Network Resources Created

VPC network: lab04-net

Subnet: lab04-subnet

Security Group: lab04-sg

Security Group Rules

SSH (22) — allowed

HTTP (80) — allowed

Custom port 5000 — allowed

All outbound traffic — allowed

Terraform Plan Output
Plan: 4 to add, 0 to change, 0 to destroy.

Resources to be created:

yandex_vpc_network.net

yandex_vpc_subnet.subnet

yandex_vpc_security_group.sg

yandex_compute_instance.vm


---

## Terraform Apply Output



Apply complete! Resources: 4 added, 0 changed, 0 destroyed.

Outputs:

public_ip = "89.169.155.6"
ssh_command = "ssh ubuntu@89.169.155.6"


---

## Public IP Address



89.169.155.6


---

## SSH Connection Command



ssh ubuntu@89.169.155.6


---

## Proof of SSH Access

Successful connection to the VM:

ubuntu@fhmk0s8osvpb95b53051:~$ whoami
ubuntu

ubuntu@fhmk0s8osvpb95b53051:~$ hostname
fhmk0s8osvpb95b53051

This confirms that:
- The VM was successfully created
- The public IP is reachable
- SSH authentication via key works correctly


Pulumi Version
pulumi version
v3.220.0


Language used: Python

Pulumi Preview Output
Previewing update (dev)

Type                              Name
+   pulumi:pulumi:Stack            project-dev
+   yandex:index:VpcNetwork        lab04-net
+   yandex:index:VpcSecurityGroup  lab04-sg
+   yandex:index:VpcSubnet         lab04-subnet
+   yandex:index:ComputeInstance   lab04-vm

Resources:
    + 5 to create

Pulumi Up Output
Outputs:
    public_ip  : "93.77.185.128"
    ssh_command: "ssh ubuntu@93.77.185.128"

Public IP (Pulumi VM)
93.77.185.128

SSH Connection (Pulumi VM)
ssh ubuntu@93.77.185.128

Proof of SSH Access

Successful SSH connection:

ubuntu@fhmco5ffl738gc28a2pc:~$ whoami
ubuntu

ubuntu@fhmco5ffl738gc28a2pc:~$ hostname
fhmco5ffl738gc28a2pc


This confirms that:

Infrastructure was successfully recreated using Pulumi

Public IP is reachable

SSH authentication works correctly

4. Terraform vs Pulumi Comparison
Ease of Learning

Terraform was easier to start with because the HCL configuration is declarative and focused only on infrastructure. Pulumi required additional setup (Python environment, dependencies, plugin configuration).

Code Readability

Pulumi feels more flexible since it uses a real programming language (Python), which allows logic and reusable code. However, Terraform configuration is more structured and concise for simple infrastructure.

Debugging

Terraform provides clearer error messages during plan and apply. Pulumi errors are Python runtime errors, which can sometimes be harder to debug.

Documentation

Terraform documentation is more extensive and mature. Pulumi documentation is good but sometimes less detailed for specific cloud providers.

When to Use Each Tool

Terraform is preferable for:

Standardized infrastructure

Large teams

Declarative infrastructure management

Pulumi is preferable for:

Complex logic

Dynamic infrastructure generation

Teams comfortable with general-purpose programming languages

5. Lab 5 Preparation & Cleanup
VM for Lab 5

Yes, I am keeping the Pulumi-created VM for Lab 5.

Active VM:

93.77.185.128


This VM will be used for Ansible configuration in the next lab.