# LAB04 --- Infrastructure as Code (Terraform & Pulumi)

Date: 2026-02-19

## 1. Cloud Provider & Infrastructure

**Cloud provider:** Yandex Cloud (YC)\
**Why YC:** accessible from Russia, straightforward free-tier/minimal VM
configuration.

### Cloud resources created (both Terraform and Pulumi)

-   VPC Network: `lab04-net`
-   Subnet: `lab04-subnet` (`10.10.0.0/24`, zone `ru-central1-a`)
-   Security Group: `lab04-sg`
    -   Ingress:
        -   **22/tcp (SSH)** --- only from my public IP (`my_ssh_cidr`,
            e.g. `1.2.3.4/32`)
        -   **80/tcp (HTTP)** --- from `0.0.0.0/0`
        -   **5000/tcp (App)** --- from `0.0.0.0/0`
    -   Egress:
        -   **ANY** --- to `0.0.0.0/0`
-   Compute instance: `lab04-vm`
    -   Platform: `standard-v2`
    -   CPU: 2 cores, `core_fraction = 20%`
    -   RAM: 1 GB
    -   Boot disk: 10 GB (`network-hdd`)
    -   Public IP via `nat = true`
    -   SSH key injected through metadata

Expected cost: \$0 (minimal configuration).

------------------------------------------------------------------------

## 2. Terraform Implementation

### Versions and layout

-   Terraform: \>= 1.9.0
-   Provider: `yandex-cloud/yandex`

Structure:

    terraform/
      main.tf
      variables.tf
      outputs.tf
      terraform.tfvars  (gitignored)
      key.json          (gitignored)
    docs/
      LAB04.md

### Key decisions

-   Authentication via `service_account_key_file` (never committed).

-   Ubuntu image via data source (`ubuntu-2404-lts`).

-   SSH key passed with:

    ``` hcl
    ssh-keys = "${var.ssh_user}:${file(var.ssh_public_key_path)}"
    ```

-   SSH restricted to `var.my_ssh_cidr`.

-   HTTP (80) and App (5000) open to public.

-   Egress allow-all for outbound connectivity.

### Commands

``` bash
terraform fmt
terraform init
terraform validate
terraform plan
terraform apply
```

Outputs: - `public_ip` - `ssh_command`

Verification:

``` bash
ssh ubuntu@<PUBLIC_IP>
whoami
```

Cleanup:

``` bash
terraform destroy
```

------------------------------------------------------------------------

## 3. Pulumi Implementation (Python)

### Stack configuration

Pulumi config keys: - `zone` - `sshUser` - `mySshCidr` -
`sshPublicKeyPath` - `imageId`

### Infrastructure

Creates: - Network + Subnet (`10.10.0.0/24`) - Security Group + separate
rules: - SSH (22) from `mySshCidr` - HTTP (80) from `0.0.0.0/0` - App
(5000) from `0.0.0.0/0` - Egress ANY - VM `lab04-vm` - standard-v2, 2
cores, 20%, 1 GB RAM - 10 GB boot disk - NAT enabled - SSH metadata

Exports: - `public_ip` - `ssh_command`

Commands:

``` bash
pulumi preview
pulumi up
pulumi stack output ssh_command
pulumi destroy
```

------------------------------------------------------------------------

## 4. Terraform vs Pulumi Comparison

**Ease of learning:**\
Terraform is simpler for basic infrastructure. Pulumi requires Python
runtime and handling Outputs.

**Readability:**\
Terraform is concise and declarative. Pulumi is flexible but more
verbose.

**Debugging:**\
Terraform `plan` is very clear. Pulumi `preview` is similar but Output
handling adds complexity.

**Use cases:**\
Terraform --- standard infra provisioning.\
Pulumi --- infra with complex logic or reusable code libraries.

------------------------------------------------------------------------

## 5. Lab 5 Plan

Cloud VMs were destroyed after testing.

For Lab 5 I prepared a local VM: - QEMU/KVM + virt-manager - Ubuntu
Server 25 - virtio NAT network - Ports opened with `ufw`:

``` bash
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 5000/tcp
sudo ufw enable
```

------------------------------------------------------------------------

## Bonus

Bonus tasks (CI/CD and GitHub import) were not implemented.