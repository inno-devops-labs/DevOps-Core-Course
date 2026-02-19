# LAB04 — Infrastructure as Code (Terraform & Pulumi)

This document records the completed Lab 4 work: I provisioned infrastructure in Yandex Cloud using Terraform and re-created the same infrastructure with Pulumi (Python). It contains implementation details, sanitized terminal outputs, verification steps (SSH), a short Terraform vs Pulumi comparison, and the Lab 5 plan.

Status summary
- Cloud provider: Yandex Cloud
- Terraform: implemented in `terraform/` (HCL)
- Pulumi: implemented in `pulumi/` (Python)
- VM kept for Lab 5: Pulumi-created VM (documented below)
- Sensitive files: not committed (service account keys, private SSH keys, tfstate should be in .gitignore)

1) Cloud provider & infrastructure

Chosen provider: Yandex Cloud
- Rationale: free-tier availability in the region used, simple provider support in both Terraform and Pulumi, and accessibility from Russia.

Resources created (logical list)
- VPC network (yandex_vpc_network / yandex.VpcNetwork)
- Subnet (yandex_vpc_subnet / yandex.VpcSubnet)
- Security group / security group rules (SSH 22, HTTP 80, custom app port 5000)
- (Optional) static public IP (yandex_vpc_address)
- Compute instance (yandex_compute_instance / yandex.ComputeInstance)

Instance details (as configured)
- Zone: ru-central1-a (default in code)
- Platform: standard-v2
- CPU: 2 cores (core_fraction: 20%)
- Memory: 1 GB
- Boot disk: 10 GB (network-hdd)
- Image: ubuntu-2404-lts (Ubuntu 24.04 LTS)
- User: ubuntu (ssh key provisioned via variables / Pulumi config)

Cost: free-tier sizes used; expected $0 for the lab if free-tier limits are respected. Destroy resources when not used.

2) Terraform implementation

Files and location
- terraform/main.tf
- terraform/variables.tf
- terraform/providers.tf
- terraform/outputs.tf (if present)
- terraform/terraform.tfvars (gitignored; contains folder_id, cloud_id, ssh_public_key, allowed_ssh_ips)

Key decisions and notes
- Provider: `yandex-cloud/yandex` configured in `providers.tf` (uses environment variables YC_TOKEN, YC_CLOUD_ID, YC_FOLDER_ID or terraform.tfvars).
- SSH key is passed as a sensitive variable `ssh_public_key` 
- Security group restricts SSH access to `allowed_ssh_ips` variable — change it to your IP before applying.
- Cloud-init userdata installs docker and basic packages and adds the ubuntu user to docker group so the VM is ready for Ansible in Lab 5.
- A static IP resource `yandex_vpc_address` is created by default (count = 1). If you prefer ephemeral NAT only, set count = 0 or remove the resource.

Commands used (example)
```bash
# from repo root
cd terraform
terraform init
terraform fmt -check
terraform validate
terraform plan -var "folder_id=<YOUR_FOLDER_ID>" -var "ssh_public_key='$(cat ~/.ssh/id_ed25519.pub)'" -out=plan.out
terraform apply "plan.out"
```

Sanitized example outputs :
- terraform plan (truncated)
  - `Plan: 5 to add, 0 to change, 0 to destroy.

Changes to Outputs:
  + check_web_access       = (known after apply)
  + network_id             = (known after apply)
  + security_group_id      = (known after apply)
  + ssh_connection_command = (known after apply)
  + static_ip_address      = (known after apply)
  + subnet_id              = (known after apply)
  + vm_id                  = (known after apply)
  + vm_name                = "lab4-vm"
  + vm_private_ip          = (known after apply)
  + vm_public_ip           = (known after apply)`

- terraform apply (truncated)
  - `yandex_vpc_network.network: Creation complete after 3s [id=net-xxxxxxxxxxxx]`
  - `yandex_vpc_subnet.subnet: Creation complete after 2s [id=subnet-xxxxxxxxxxxx]`
  - `yandex_vpc_security_group.sg: Creation complete after 2s [id=sg-xxxxxxxxxxxx]`
  - `yandex_vpc_address.static_ip[0]: Creation complete after 1s [id=addr-xxxxxxxxxxxx]`
  - `yandex_compute_instance.vm: Creation complete after 45s [id=vm-xxxxxxxxxxxx]`
  - `Apply complete! Resources: 5 added, 0 changed, 0 destroyed.`

Retrieve public IP and test SSH
- Get the public IP from Terraform outputs or Cloud Console. Example (if outputs.tf exports public_ip):
  - `terraform output public_ip` -> <PUBLIC_IP>
- SSH into VM (example):
  - `ssh -i ~/.ssh/id_ed25519 ubuntu@<PUBLIC_IP>`


```bash
 ~/inn/Devo/DevOps-Core-Course/terraform   lab04 !1 ?3  ssh  -i ~/.ssh/id_ed25519 ubuntu@93.77.179.18             
The authenticity of host '93.77.179.18 (93.77.179.18)' can't be established.
ED25519 key fingerprint is SHA256:8e8GVsBUaRHdFE0sQOyXc1DZsp8qwTn5aFS8bhYFzSo.
This key is not known by any other names.
Are you sure you want to continue connecting (yes/no/[fingerprint])? yes
Warning: Permanently added '93.77.179.18' (ED25519) to the list of known hosts.
Welcome to Ubuntu 24.04.4 LTS (GNU/Linux 6.8.0-100-generic x86_64)

 * Documentation:  https://help.ubuntu.com
 * Management:     https://landscape.canonical.com
 * Support:        https://ubuntu.com/pro

 System information as of Thu Feb 19 20:48:28 UTC 2026

  System load:  0.08              Processes:             102
  Usage of /:   27.3% of 9.04GB   Users logged in:       0
  Memory usage: 25%               IPv4 address for eth0: 10.10.0.17
  Swap usage:   0%


Expanded Security Maintenance for Applications is not enabled.

7 updates can be applied immediately.
3 of these updates are standard security updates.
To see these additional updates run: apt list --upgradable

1 additional security update can be applied with ESM Apps.
Learn more about enabling ESM Apps service at https://ubuntu.com/esm



The programs included with the Ubuntu system are free software;
the exact distribution terms for each program are described in the
individual files in /usr/share/doc/*/copyright.

Ubuntu comes with ABSOLUTELY NO WARRANTY, to the extent permitted by
applicable law.

Lab 4 VM ready for Ansible Lab 5!
To run a command as administrator (user "root"), use "sudo <command>".
See "man sudo_root" for details.

ubuntu@fhmr155u8vkvb63ff5kl:~$ whoami
ubuntu
ubuntu@fhmr155u8vkvb63ff5kl:~$ docker --version
Docker version 28.2.2, build 28.2.2-0ubuntu1~24.04.1
```


3) Pulumi implementation (Python)

Files and location
- pulumi/__main__.py
- pulumi/requirements.txt
- Pulumi.yaml, Pulumi.<stack>.yaml (stack config)

Key decisions and notes
- Language: Python (Pulumi program in `pulumi/__main__.py`)
- Provider: `pulumi-yandex` (add to requirements.txt)
- Pulumi config is used to pass `cloud_id`, `folder_id` and optionally `ssh_public_key` (or read from `~/.ssh/id_ed25519.pub`).
- The Pulumi project provisions equivalent resources using the Pulumi Yandex SDK; subnet CIDR was chosen different from Terraform to avoid CIDR collision in the same account (`10.20.0.0/24` vs Terraform's `10.10.0.0/24`).
- `user-data` cloud-init is used the same way as Terraform so VM is ready for Ansible.

Commands used (example)
```bash
cd pulumi
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pulumi stack init dev  # only if stack doesn't exist
pulumi config set cloud_id <YOUR_CLOUD_ID>
pulumi config set folder_id <YOUR_FOLDER_ID>
# optional: pulumi config set --secret ssh_public_key "$(cat ~/.ssh/id_ed25519.pub)"
pulumi preview
pulumi up --yes
```

Sanitized example outputs (replace placeholders with your real values):
- pulumi preview shows the resources to be created, e.g. `+ yandex:compute/instance:Instance lab4-vm-pulumi` and others.
- pulumi up (truncated)
  - `     Type                                  Name                 Status            
 +   pulumi:pulumi:Stack                   lab4-pulumi-dev      created (47s)     
 +   ├─ yandex:index:VpcNetwork            lab4-network-pulumi  created (3s)      
 +   ├─ yandex:index:VpcSubnet             lab4-subnet-pulumi   created (1s)      
 +   ├─ yandex:index:VpcSecurityGroup      lab4-sg-pulumi       created (3s)      
 +   ├─ yandex:index:VpcSecurityGroupRule  lab4-sg-rule-ssh     created (1s)      
 +   ├─ yandex:index:VpcSecurityGroupRule  lab4-sg-rule-http    created (2s)      
 +   ├─ yandex:index:VpcSecurityGroupRule  lab4-sg-rule-egress  created (3s)      
 +   ├─ yandex:index:VpcSecurityGroupRule  lab4-sg-rule-app     created (4s)      
 +   └─ yandex:index:ComputeInstance       lab4-vm-pulumi       created (33s)     

Outputs:
    network_id       : "enpdustvupl91h748v6n"
    private_ip       : "10.20.0.11"
    public_ip        : "93.77.186.162"
    security_group_id: "enpcu7eqdm6qt57cfkhu"
    ssh_command      : "ssh ubuntu@93.77.186.162"
    subnet_id        : "e9bgmhlaufo0rt32k0jc"
    vm_id            : "fhm7is8pb023fc4okuai"
    vm_name          : "lab4-pulumi-vm"

Resources:
    + 9 created

Duration: 49s`

Get outputs
- `pulumi stack output public_ip` -> <PUBLIC_IP>
- SSH into VM: `ssh -i ~/.ssh/id_ed25519 ubuntu@<PUBLIC_IP>`

4) Terraform vs Pulumi — brief comparison
- Ease of learning: Terraform is quick to get started for simple resources (HCL). Pulumi was slightly harder initially due to environment setup (venv, packages) but allowed faster iteration with a real programming language.
- Code readability: Pulumi (Python) provides familiar syntax and IDE support; Terraform HCL is more compact for pure resource declarations.
- Debugging: Pulumi allows using Python debuggers and exceptions; Terraform's plan step gives an explicit preview which helps avoid surprises.
- Documentation & examples: Terraform has a larger ecosystem and more examples; Pulumi docs are good and language SDKs add convenience.
- Use cases: Use Terraform for simple declarative setups and broad community support. Use Pulumi when you need programming language features, loops, or to integrate with existing code.

5) Lab 5 preparation & cleanup (what I did)
- Kept: Pulumi-created VM for Lab 5 (Ansible provisioning) because Pulumi already provisions the VM I want to use.
- Destroyed: Terraform resources (I ran `terraform destroy` for the Terraform-managed stack only) to avoid duplicate VMs and unused resources.

Commands I ran for cleanup (examples)
```bash
# Destroy Terraform-managed resources (from terraform/)
cd terraform
terraform destroy -var "folder_id=<YOUR_FOLDER_ID>" -var "ssh_public_key='$(cat ~/.ssh/id_ed25519.pub)'" -auto-approve

# If later you want to destroy Pulumi-managed resources
cd ../pulumi
pulumi destroy --yes
pulumi stack rm dev --yes   # optional: remove stack records
```




