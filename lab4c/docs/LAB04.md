# LAB04 — Infrastructure as Code (Terraform & Pulumi)

## 1. Cloud Provider & Infrastructure

- **Cloud provider:** Yandex Cloud.
- **Rationale:** Used Yandex Cloud for this lab because of the free tier
- **Instance:** standard-v3, 2 cores 20%, 1 GB RAM, 10 GB disk.
- **Zone:** ru-central1-a.
- **Estimated cost:** Effectively $0 with the free tier for this kind of usage.
- **Resources created:**
  - 1× VPC network
  - 1× subnet
  - 1× security group (SSH 22, HTTP 80, 5000)
  - 1× compute instance (Ubuntu 22.04)
  - Public IP

## 2. Terraform Implementation

- **Terraform version:** Terraform v1.14.5
- **Project structure:** `terraform/` — main.tf (provider, Ubuntu image data source, VPC, subnet, security group, instance), variables.tf, outputs.tf, terraform.tfvars (gitignored). Auth via service account key path in tfvars
- **Key decisions:** Variables for folder_id, zone, SSH key path, and SSH CIDR so the same code works across environments. Data source for the latest Ubuntu 22.04 LTS image. Security group restricts SSH to our IP only; HTTP and 5000 are open for the app.
- **Challenges:** Getting auth right at first; I ended up putting the key file path in terraform.tfvars). Also hit the VPC network quota once and had to extend it.

**Terminal output:**

- `terraform init`:  
  ```
terraform init
Initializing the backend...
Initializing provider plugins...
- Finding yandex-cloud/yandex versions matching "~> 0.100"...
- Installing yandex-cloud/yandex v0.187.0...
- Installed yandex-cloud/yandex v0.187.0
  ```
- `terraform plan`:  
  ```
terraform plan
data.yandex_compute_image.ubuntu: Reading...
data.yandex_compute_image.ubuntu: Read complete after 0s [id=***********]

Terraform used the selected providers to generate the following execution plan. Resource actions are indicated with the
following symbols:
  + create

Terraform will perform the following actions:

  # yandex_compute_instance.lab4 will be created
  + resource "yandex_compute_instance" "lab4" {
  ```
- `terraform apply`:  
  ```
terraform apply
data.yandex_compute_image.ubuntu: Reading...
data.yandex_compute_image.ubuntu: Read complete after 0s [id=***********]

Terraform used the selected providers to generate the following execution plan. Resource actions are indicated with the
following symbols:
  + create

Terraform will perform the following actions:

  # yandex_compute_instance.lab4 will be created
  + resource "yandex_compute_instance" "lab4" {
  ```
- `SSH to VM`:  
  ```
The programs included with the Ubuntu system are free software;
the exact distribution terms for each program are described in the
individual files in /usr/share/doc/*/copyright.

Ubuntu comes with ABSOLUTELY NO WARRANTY, to the extent permitted by
applicable law.

To run a command as administrator (user "root"), use "sudo <command>".
See "man sudo_root" for details.

ubuntu@fhm24d5clqr3oh7b101s:~$
  ```

## 3. Pulumi Implementation

- **Pulumi version and language:** Pulumi v3.222.0, Python 3.x.
- **How it differs from Terraform:** Same logical resources (VPC, subnet, security group, VM), but defined in Python. You get normal Python (loops, functions, types) and the same state/plan/apply workflow.
- **Advantages:** Felt easier. Outputs are straightforward.
- **Challenges:** Initial setup took a bit: venv, `setuptools<82` for `pkg_resources`, and provider auth.

**Terminal output:**

- `pulumi preview`:  
  ```
  pulumi preview
Previewing update (dev)

View in Browser (Ctrl+O):

     Type                              Name           Plan       Info
 +   pulumi:pulumi:Stack               lab4c-vm-dev   create     2 messages
 +   ├─ yandex:index:VpcNetwork        lab4c-network  create
 +   ├─ yandex:index:VpcSubnet         lab4c-subnet   create
 +   ├─ yandex:index:VpcSecurityGroup  lab4c-vm-sg    create
 +   └─ yandex:index:ComputeInstance   lab4c-vm       create
Diagnostics:
  pulumi:pulumi:Stack (lab4c-vm-dev):
      import pkg_resources

Outputs:
    public_ip  : [unknown]
    ssh_command: [unknown]

Resources:
    + 5 to create
  ```
- `pulumi up`:  
  ```
  pulumi up
Previewing update (dev)

View in Browser (Ctrl+O):
     Type                              Name           Plan       Info
     pulumi:pulumi:Stack               lab4c-vm-dev              2 messages
 +   ├─ yandex:index:VpcNetwork        lab4c-network  create
 +   ├─ yandex:index:VpcSubnet         lab4c-subnet   create
 +   ├─ yandex:index:VpcSecurityGroup  lab4c-vm-sg    create
 +   └─ yandex:index:ComputeInstance   lab4c-vm       create
Diagnostics:
  pulumi:pulumi:Stack (lab4c-vm-dev):
      import pkg_resources

    [Pulumi Neo] Would you like help with these diagnostics?
  
Outputs:
  + public_ip  : [unknown]
  + ssh_command: [unknown]

Resources:
    + 4 to create
    1 unchanged

Do you want to perform this update? yes
Updating (dev)
  ```
- SSH to VM:  
  ```
  The programs included with the Ubuntu system are free software;
the exact distribution terms for each program are described in the
individual files in /usr/share/doc/*/copyright.

Ubuntu comes with ABSOLUTELY NO WARRANTY, to the extent permitted by
applicable law.

To run a command as administrator (user "root"), use "sudo <command>".
See "man sudo_root" for details.

ubuntu@fhm8nea1kubnsde4ooqn:~$
  ```

## 4. Terraform vs Pulumi Comparison

- **Ease of learning:** Terraform is easier if you only care about “describe resources in a file and apply.” HCL is small and focused. Pulumi is easier if you already know Python and want to use normal code;
- **Code readability:** Both are readable. Terraform is very declarative: you see resources and attributes. Pulumi looks like normal code, so you can structure it with variables and functions.
- **Debugging:** With Terraform, you rely on plan/apply messages and sometimes `terraform state`. With Pulumi, you get Python stack traces and can add prints or a debugger; the program runs in your environment, which helps.
- **Documentation:** all services are well documented
- **Use case:** I’d pick Terraform when the team is standardizing on it, when you want maximum portability (HCL, big ecosystem), or when you’re mostly gluing provider resources. I’d pick Pulumi when the team is code-first, when you want to share logic with the rest of your app (same language, tests, refactors), or when you need loops, conditionals, or abstractions that are clumsy in HCL.

## 5. Lab 5 Preparation & Cleanup

**VM for Lab 5:**

- **Keeping VM for Lab 5?** No.
- **Plan for Lab 5:** Will recreate a cloud VM when needed

**Cleanup status:**
```
terraform destroy
Destroy complete! Resources: 4 destroyed.
```
and 
```
pulumi destroy
Previewing destroy (dev)

View in Browser (Ctrl+O):

     Type                              Name           Plan
 -   pulumi:pulumi:Stack               lab4c-vm-dev   delete
 -   ├─ yandex:index:ComputeInstance   lab4c-vm       delete
 -   ├─ yandex:index:VpcSubnet         lab4c-subnet   delete
 -   ├─ yandex:index:VpcSecurityGroup  lab4c-vm-sg    delete
 -   └─ yandex:index:VpcNetwork        lab4c-network  delete
```
