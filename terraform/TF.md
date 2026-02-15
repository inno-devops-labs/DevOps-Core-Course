# Documentation for Terraform

This document contains the outputs, state information, and key configurations of the Terraform infrastructure that provisions a Docker container running a FastAPI app to display Moscow time.

---

## File Structure

```

terraform/
├── TF.md     
├── .gitignore
└── docker/      
    ├── main.tf
    ├── variables.tf
    └── outputs.tf
└── yandex/      
    ├── main.tf
    ├── variables.tf
    └── outputs.tf
└── github/
    ├── main.tf
    ├── variables.tf
    ├── outputs.tf

```

---

## Docker

### Terraform Commands & Outputs

#### `terraform init`

<details>
<summary>command-output</summary>

```
kokai@kokai:~/Desktop/S25-core-course-labs/terraform/docker$ terraform init
Initializing the backend...
Initializing provider plugins...
- Finding kreuzwerker/docker versions matching "~> 3.0.2"...
- Installing kreuzwerker/docker v3.0.2...
- Installed kreuzwerker/docker v3.0.2 (self-signed, key ID BD080C4571C6104C)
Partner and community providers are signed by their developers.
If you'd like to know more about provider signing, you can read about it here:
https://www.terraform.io/docs/cli/plugins/signing.html
Terraform has created a lock file .terraform.lock.hcl to record the provider
selections it made above. Include this file in your version control repository
so that Terraform can guarantee to make the same selections by default when
you run "terraform init" in the future.

Terraform has been successfully initialized!

You may now begin working with Terraform. Try running "terraform plan" to see
any changes that are required for your infrastructure. All Terraform commands
should now work.

If you ever set or change modules or backend configuration for Terraform,
rerun this command to reinitialize your working directory. If you forget, other
commands will detect it and remind you to do so if necessary.
```
</details>

---

#### `terraform fmt`

<details>
<summary>command-output</summary>

```
No output
```
</details>

---


#### `terraform validate`


<details>
<summary>command-output</summary>

```
kokai@kokai:~/Desktop/S25-core-course-labs/terraform/docker$ terraform validate
Success! The configuration is valid.
```
</details>


---

#### `terraform apply`

<details>
<summary>command-output</summary>

```
kokai@kokai:~/Desktop/S25-core-course-labs/terraform/docker$ terraform apply
docker_image.moscow_time_app: Refreshing state... [id=sha256:dba8a2f516085b7b99baeca76fb1a48ee4294900dbef82f8dba5fd7f15c9a80dkaramkhaddourpro/my-fastapi-app:latest]
docker_container.moscow_time_app: Refreshing state... [id=ebf3a244147f1479aa19af57483ab561063ace082587852d2211eefd1b61f28d]

Note: Objects have changed outside of Terraform

Terraform detected the following changes made outside of Terraform since the last "terraform apply" which may have affected this plan:

  # docker_container.moscow_time_app has been deleted
  - resource "docker_container" "moscow_time_app" {
      - id                                          = "ebf3a244147f1479aa19af57483ab561063ace082587852d2211eefd1b61f28d" -> null
        name                                        = "moscow-time-app"
        # (16 unchanged attributes hidden)

        # (1 unchanged block hidden)
    }


Unless you have made equivalent changes to your configuration, or ignored the relevant attributes using ignore_changes, the following plan may include
actions to undo or respond to these changes.

───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

Terraform used the selected providers to generate the following execution plan. Resource actions are indicated with the following symbols:
  + create

Terraform will perform the following actions:

  # docker_container.moscow_time_app will be created
  + resource "docker_container" "moscow_time_app" {
      + attach                                      = false
      + bridge                                      = (known after apply)
      + command                                     = (known after apply)
      + container_logs                              = (known after apply)
      + container_read_refresh_timeout_milliseconds = 15000
      + entrypoint                                  = (known after apply)
      + env                                         = (known after apply)
      + exit_code                                   = (known after apply)
      + hostname                                    = (known after apply)
      + id                                          = (known after apply)
      + image                                       = "sha256:dba8a2f516085b7b99baeca76fb1a48ee4294900dbef82f8dba5fd7f15c9a80d"
      + init                                        = (known after apply)
      + ipc_mode                                    = (known after apply)
      + log_driver                                  = (known after apply)
      + logs                                        = false
      + must_run                                    = true
      + name                                        = "moscow-time-app"
      + network_data                                = (known after apply)
      + read_only                                   = false
      + remove_volumes                              = true
      + restart                                     = "no"
      + rm                                          = false
      + runtime                                     = (known after apply)
      + security_opts                               = (known after apply)
      + shm_size                                    = (known after apply)
      + start                                       = true
      + stdin_open                                  = false
      + stop_signal                                 = (known after apply)
      + stop_timeout                                = (known after apply)
      + tty                                         = false
      + wait                                        = false
      + wait_timeout                                = 60

      + healthcheck (known after apply)

      + labels (known after apply)

      + ports {
          + external = 8080
          + internal = 8000
          + ip       = "0.0.0.0"
          + protocol = "tcp"
        }
    }

Plan: 1 to add, 0 to change, 0 to destroy.

Changes to Outputs:
  + container_id    = (known after apply)

Do you want to perform these actions?
  Terraform will perform the actions described above.
  Only 'yes' will be accepted to approve.

  Enter a value: yes

docker_container.moscow_time_app: Creating...
docker_container.moscow_time_app: Creation complete after 0s [id=62a249ea6101f26fac7950c54502b8ddd52ad1cb1a31ebaadbd8bc0f87caf674]

Apply complete! Resources: 1 added, 0 changed, 0 destroyed.

Outputs:

container_id = "62a249ea6101f26fac7950c54502b8ddd52ad1cb1a31ebaadbd8bc0f87caf674"
container_ports = tolist([
  {
    "external" = 8080
    "internal" = 8000
    "ip" = "0.0.0.0"
    "protocol" = "tcp"
  },
])
```

</details>


---
#### `terraform state list`

<details>
<summary>command-output</summary>

```
kokai@kokai:~/Desktop/S25-core-course-labs/terraform/docker$ terraform state list
docker_container.moscow_time_app
docker_image.moscow_time_app
```
</details>


---

#### `terraform state show docker_container.moscow_time_app`


<details>
<summary>command-output</summary>

```
kokai@kokai:~/Desktop/S25-core-course-labs/terraform/docker$ terraform state show docker_container.moscow_time_app
# docker_container.moscow_time_app:
resource "docker_container" "moscow_time_app" {
    attach                                      = false
    bridge                                      = null
    command                                     = [
        "uvicorn",
        "main:app",
        "--host",
        "0.0.0.0",
        "--port",
        "8000",
    ]
    container_read_refresh_timeout_milliseconds = 15000
    cpu_set                                     = null
    cpu_shares                                  = 0
    domainname                                  = null
    entrypoint                                  = []
    env                                         = []
    hostname                                    = "62a249ea6101"
    id                                          = "62a249ea6101f26fac7950c54502b8ddd52ad1cb1a31ebaadbd8bc0f87caf674"
    image                                       = "sha256:dba8a2f516085b7b99baeca76fb1a48ee4294900dbef82f8dba5fd7f15c9a80d"
    init                                        = false
    ipc_mode                                    = "private"
    log_driver                                  = "json-file"
    logs                                        = false
    max_retry_count                             = 0
    memory                                      = 0
    memory_swap                                 = 0
    must_run                                    = true
    name                                        = "moscow-time-app"
    network_data                                = [
        {
            gateway                   = "172.17.0.1"
            global_ipv6_address       = null
            global_ipv6_prefix_length = 0
            ip_address                = "172.17.0.3"
            ip_prefix_length          = 16
            ipv6_gateway              = null
            mac_address               = "62:06:d4:28:e6:13"
            network_name              = "bridge"
        },
    ]
    network_mode                                = "bridge"
    pid_mode                                    = null
    privileged                                  = false
    publish_all_ports                           = false
    read_only                                   = false
    remove_volumes                              = true
    restart                                     = "no"
    rm                                          = false
    runtime                                     = "runc"
    security_opts                               = []
    shm_size                                    = 64
    start                                       = true
    stdin_open                                  = false
    stop_signal                                 = null
    stop_timeout                                = 0
    tty                                         = false
    user                                        = "appuser"
    userns_mode                                 = null
    wait                                        = false
    wait_timeout                                = 60
    working_dir                                 = "/app"

    ports {
        external = 8080
        internal = 8000
        ip       = "0.0.0.0"
        protocol = "tcp"
    }
}
```

</details>

---

#### `terraform output`
<details>
<summary>command-output</summary>

```
kokai@kokai:~/Desktop/S25-core-course-labs/terraform/docker$ terraform output
container_id = "62a249ea6101f26fac7950c54502b8ddd52ad1cb1a31ebaadbd8bc0f87caf674"
container_ports = tolist([
  {
    "external" = 8080
    "internal" = 8000
    "ip" = "0.0.0.0"
    "protocol" = "tcp"
  },
])
```
</details>

---

### Input Variables

| Variable Name           | Description                             | Default Value                                       |
|-------------------------|-----------------------------------------|----------------------------------------------------|
| `python_container_name` | Name of the Docker container            | `moscow-time-app`                                  |
| `app_image_name`        | Docker image name                       | `karamkhaddourpro/my-fastapi-app:latest`           |
| `internal_port`         | Internal port exposed by the app        | `8000`                                             |
| `external_port`         | Host port mapped to the app container   | `8080`                                             |

---

### Renaming my Docker container using input variables.
---
simply I changed the container name inside of varaibles.tf to moscow-time-app-renamed
I applied the following command 

### `terraoform apply` 

After it I applied terrform state show docker_container.moscow_tim_app 


#### ` terraform state show docker_container.moscow_time_app`

<details>

<summary>command-output</summary>

```bash

 kokai@kokai:~/Desktop/S25-core-course-labs/terraform/docker$ terraform state show docker_container.moscow_time_app
# docker_container.moscow_time_app:
resource "docker_container" "moscow_time_app" {
    attach                                      = false
    bridge                                      = null
    command                                     = [
        "uvicorn",
        "main:app",
        "--host",
        "0.0.0.0",
        "--port",
        "8000",
    ]
    container_read_refresh_timeout_milliseconds = 15000
    cpu_set                                     = null
    cpu_shares                                  = 0
    domainname                                  = null
    entrypoint                                  = []
    env                                         = []
    hostname                                    = "5a55a604922c"
    id                                          = "5a55a604922c04c49b70fb4a7f7250e0d18f7f49719f321b4f9733e1e4289fb9"
    image                                       = "sha256:dba8a2f516085b7b99baeca76fb1a48ee4294900dbef82f8dba5fd7f15c9a80d"
    init                                        = false
    ipc_mode                                    = "private"
    log_driver                                  = "json-file"
    logs                                        = false
    max_retry_count                             = 0
    memory                                      = 0
    memory_swap                                 = 0
    must_run                                    = true
    name                                        = "moscow-time-app-renamed"
    network_data                                = [
        {
            gateway                   = "172.17.0.1"
            global_ipv6_address       = null
            global_ipv6_prefix_length = 0
            ip_address                = "172.17.0.3"
            ip_prefix_length          = 16
            ipv6_gateway              = null
            mac_address               = "22:11:54:76:79:65"
            network_name              = "bridge"
        },
    ]
    network_mode                                = "bridge"
    pid_mode                                    = null
    privileged                                  = false
    publish_all_ports                           = false
    read_only                                   = false
    remove_volumes                              = true
    restart                                     = "no"
    rm                                          = false
    runtime                                     = "runc"
    security_opts                               = []
    shm_size                                    = 64
    start                                       = true
    stdin_open                                  = false
    stop_signal                                 = null
    stop_timeout                                = 0
    tty                                         = false
    user                                        = "appuser"
    userns_mode                                 = null
    wait                                        = false
    wait_timeout                                = 60
    working_dir                                 = "/app"

    ports {
        external = 9080
        internal = 8000
        ip       = "0.0.0.0"
        protocol = "tcp"
    }
}

```
</details>
and we can see that the name is chaned to the name we had in our varaibls moscow-time-app-renamed

## Yandex Cloud

### Step 1: Create Yandex Cloud Account

I created an account on Yandex Cloud and logged into the console.

I needed to purchase a small virtual machine in yandex cloud :

- Small VM instances
- Limited disk storage
- Limited network usage

### Step 2: Configure Authentication

I created a service account in Yandex Cloud and assigned the "admin" role.

Then I generated an OAuth token using the Yandex CLI:

```bash
yc iam create-token
```

and got the folder_id and cloud_id from the UI
These values were stored securely in Terraform variables.

### Step 3: Terraform Configuration

I created the following Terraform resources:

- VPC Network
- Subnet
- Boot disk
- Virtual Machine instance

The VM uses:

- 2 CPU cores
- 2 GB RAM
- 20 GB disk
- Ubuntu image
- Public NAT IP for SSH access

Terraform automatically handles dependencies between resources.

### Step 4: SSH Access Configuration

I configured SSH access by providing my public SSH key:

```
~/.ssh/id_rsa.pub
```

This allows secure remote login:


#### `terraform init`

<details>
<summary>command-output</summary>
``` Initializing the backend...
Initializing provider plugins...
- Finding yandex-cloud/yandex versions matching "~> 0.75"...
- Installing yandex-cloud/yandex v0.142.0...
- Installed yandex-cloud/yandex v0.142.0 (self-signed, key ID E40F590B50BB8E40)
Partner and community providers are signed by their developers.
If you'd like to know more about provider signing, you can read about it here:
https://www.terraform.io/docs/cli/plugins/signing.html
Terraform has created a lock file .terraform.lock.hcl to record the provider
selections it made above. Include this file in your version control repository
so that Terraform can guarantee to make the same selections by default when
you run "terraform init" in the future.

Terraform has been successfully initialized!

You may now begin working with Terraform. Try running "terraform plan" to see
any changes that are required for your infrastructure. All Terraform commands
should now work.

If you ever set or change modules or backend configuration for Terraform,
rerun this command to reinitialize your working directory. If you forget, other
commands will detect it and remind you to do so if necessary.
```
</details>

#### `terraform fmt`

<details>
<summary>command-output</summary>

```

kokai@kokai:~/Desktop/S25-core-course-labs/terraform/yandex$ terraform fmt
variables.tf

```
</details>



#### `terraform validate`


<details>
<summary>command-output</summary>

```
kokai@kokai:~/Desktop/S25-core-course-labs/terraform/yandex$ terraform validate
Success! The configuration is valid.
```
</details>

#### `terraform apply`

<details>
<summary>command-output</summary>

```
kokai@kokai:~/Desktop/S25-core-course-labs/terraform/yandex$ terraform apply

Terraform used the selected providers to generate the following execution plan. Resource actions are indicated with the following symbols:
  + create

Terraform will perform the following actions:

  # yandex_compute_disk.boot_disk will be created
  + resource "yandex_compute_disk" "boot_disk" {
      + block_size  = 4096
      + created_at  = (known after apply)
      + folder_id   = (known after apply)
      + id          = (known after apply)
      + image_id    = "fd865v46cboopthn7u0k"
      + name        = "terraform-boot-disk"
      + product_ids = (known after apply)
      + size        = 20
      + status      = (known after apply)
      + type        = "network-hdd"
      + zone        = "ru-central1-a"

      + disk_placement_policy (known after apply)

      + hardware_generation (known after apply)
    }

  # yandex_compute_instance.vm will be created
  + resource "yandex_compute_instance" "vm" {
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
          + "ssh-keys" = <<-EOT
                ubuntu:ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQCkyMWPCG2OjpoLRryBZph+Ruv67V+dZsBZaZi2tt1+/yP1VVYJoZQ0z6GezI2jJuca6vqY2q9aLFzC0zyy2OjdAowX8DuB+Qdy+pdMW9Uep9r8cG9gSKQ+3yycZZney4cpH7hZPh2lr5BnFYm7QSIH0jLxDh6mSZ1rr/Qy1pEnvEPLVsK7UkV+0oIIFaogt226WkFePk0WQ/AvVTMksNbNKNEC4XAs/V2y9g9fDUYC7mo1CJHc2bSOIL/yMif2gfWYbj+3hZhVKzsqJ5lEYYd8KyUabsjClqNdcs94af0GbhaK7RCAdRkpPZD9eAYSfUgWvLyR3eFb/NbS2iFONDPP24qb0PxPdIQHUPKz8O/NhNVBDVR9Rtt4oLFTmTsN1Ttr2PNDxCPr2JWrtWI/ALo8Qw4iS+MAYQAkl2aeewCFDcW6ypkByR2A6moOvf0I7nAU5VyMcH70PlDr/KPPmQLqSs/xy/HciqkhZ1Va0e/QtbQ772l2RHHH/Yd1PJzrDnPIHsZwR7cP6k9jyIdfZCiVJqwGEifpHugSvGRCg+yOG9kpUFNaVoUcpEqRoZ17x7O8vdBPpGvbOpLo8T/nkJA3tvqP/4bnH8POWu8adlMvLDg41MFld40S0dwYUYNK48+4wIC6+oe1w475rNc69r29jjI96EnJCv+3qE0S0WzjKw== karam13549@gmail.com
            EOT
        }
      + name                      = "terraform-vm"
      + network_acceleration_type = "standard"
      + platform_id               = "standard-v1"
      + service_account_id        = (known after apply)
      + status                    = (known after apply)
      + zone                      = "ru-central1-a"

      + boot_disk {
          + auto_delete = true
          + device_name = (known after apply)
          + disk_id     = (known after apply)
          + mode        = (known after apply)

          + initialize_params (known after apply)
        }

      + metadata_options (known after apply)

      + network_interface {
          + index              = (known after apply)
          + ip_address         = (known after apply)
          + ipv4               = true
          + ipv6               = (known after apply)
          + ipv6_address       = (known after apply)
          + mac_address        = (known after apply)
          + nat                = true
          + nat_ip_address     = (known after apply)
          + nat_ip_version     = (known after apply)
          + security_group_ids = (known after apply)
          + subnet_id          = (known after apply)
        }

      + placement_policy (known after apply)

      + resources {
          + core_fraction = 20
          + cores         = 2
          + memory        = 2
        }

      + scheduling_policy {
          + preemptible = true
        }
    }

  # yandex_vpc_network.network will be created
  + resource "yandex_vpc_network" "network" {
      + created_at                = (known after apply)
      + default_security_group_id = (known after apply)
      + folder_id                 = (known after apply)
      + id                        = (known after apply)
      + labels                    = (known after apply)
      + name                      = "terraform-network"
      + subnet_ids                = (known after apply)
    }

  # yandex_vpc_subnet.subnet will be created
  + resource "yandex_vpc_subnet" "subnet" {
      + created_at     = (known after apply)
      + folder_id      = (known after apply)
      + id             = (known after apply)
      + labels         = (known after apply)
      + name           = "terraform-subnet"
      + network_id     = (known after apply)
      + v4_cidr_blocks = [
          + "192.168.10.0/24",
        ]
      + v6_cidr_blocks = (known after apply)
      + zone           = "ru-central1-a"
    }

Plan: 4 to add, 0 to change, 0 to destroy.

Changes to Outputs:
  + external_ip = (known after apply)
  + internal_ip = (known after apply)

Do you want to perform these actions?
  Terraform will perform the actions described above.
  Only 'yes' will be accepted to approve.

  Enter a value: yes

yandex_vpc_network.network: Creating...
yandex_compute_disk.boot_disk: Creating...
yandex_vpc_network.network: Creation complete after 4s [id=enpgn1a5erb0jnb6j70i]
yandex_vpc_subnet.subnet: Creating...
yandex_vpc_subnet.subnet: Creation complete after 1s [id=e9bdtu2o252hoj8vrpjr]
yandex_compute_disk.boot_disk: Still creating... [10s elapsed]
yandex_compute_disk.boot_disk: Creation complete after 15s [id=fhmn87klqhf9ifcumb5o]
yandex_compute_instance.vm: Creating...
yandex_compute_instance.vm: Still creating... [10s elapsed]
yandex_compute_instance.vm: Still creating... [20s elapsed]
yandex_compute_instance.vm: Still creating... [30s elapsed]
yandex_compute_instance.vm: Creation complete after 38s [id=fhmp9oduglg02moefva7]

Apply complete! Resources: 4 added, 0 changed, 0 destroyed.

Outputs:

external_ip = "84.201.132.123"
internal_ip = "192.168.10.34"
```
</details>


#### `terraform output`
<details>
<summary>command-output</summary>

```
kokai@kokai:~/Desktop/S25-core-course-labs/terraform/yandex$ terraform output
external_ip = "84.201.132.123"
internal_ip = "192.168.10.34"
```

</details>

## GitHub

### Terraform Commands & Outputs

#### `terraform init`

<details>
<summary>command-output</summary>


```
kokai@kokai:~/Desktop/S25-core-course-labs/terraform/github$ terraform init
Initializing the backend...
Initializing provider plugins...
- Reusing previous version of integrations/github from the dependency lock file
- Using previously-installed integrations/github v4.31.0

Terraform has been successfully initialized!

You may now begin working with Terraform. Try running "terraform plan" to see
any changes that are required for your infrastructure. All Terraform commands
should now work.

If you ever set or change modules or backend configuration for Terraform,
rerun this command to reinitialize your working directory. If you forget, other
commands will detect it and remind you to do so if necessary.

```

</details>


#### `terraform fmt`

<details>
<summary>command-output</summary>

```


main.tf 

```

</details>



#### `terraform validate`


<details>
<summary>command-output</summary>

```

kokai@kokai:~/Desktop/S25-core-course-labs/terraform/github$ terraform validate
Success! The configuration is valid.

```

</details>

#### `terraform import`


<details>
<summary>command-output</summary>

```
kokai@kokai:~/Desktop/S25-core-course-labs/terraform/github$ terraform import github_repository.repo S25-core-course-labs
github_repository.repo: Importing from ID "S25-core-course-labs"...
github_repository.repo: Import prepared!
  Prepared github_repository for import
github_repository.repo: Refreshing state... [id=S25-core-course-labs]

Import successful!

The resources that were imported are shown above. These resources are now in
your Terraform state and will henceforth be managed by Terraform.

```

</details>



#### `terraform apply`

<details>
<summary>command-output</summary>

```
kokai@kokai:~/Desktop/S25-core-course-labs/terraform/github$ terraform apply
github_repository.repo: Refreshing state... [id=S25-core-course-labs]

Terraform used the selected providers to generate the following execution plan. Resource actions are indicated with the following symbols:
  + create
  ~ update in-place

Terraform will perform the following actions:

  # github_branch_default.master will be created
  + resource "github_branch_default" "master" {
      + branch     = "master"
      + id         = (known after apply)
      + repository = "S25-core-course-labs"
    }

  # github_branch_protection.default will be created
  + resource "github_branch_protection" "default" {
      + allows_deletions                = false
      + allows_force_pushes             = false
      + blocks_creations                = false
      + enforce_admins                  = true
      + id                              = (known after apply)
      + pattern                         = "master"
      + repository_id                   = "S25-core-course-labs"
      + require_conversation_resolution = true
      + require_signed_commits          = false
      + required_linear_history         = false

      + required_pull_request_reviews {
          + required_approving_review_count = 1
        }
    }

  # github_repository.repo will be updated in-place
  ~ resource "github_repository" "repo" {
      ~ auto_init                   = false -> true
      + description                 = "Devops course repo"
      + gitignore_template          = "VisualStudio"
      - has_downloads               = true -> null
      ~ has_issues                  = false -> true
      - has_projects                = true -> null
        id                          = "S25-core-course-labs"
      + license_template            = "mit"
        name                        = "S25-core-course-labs"
        # (28 unchanged attributes hidden)
    }

Plan: 2 to add, 1 to change, 0 to destroy.

Do you want to perform these actions?
  Terraform will perform the actions described above.
  Only 'yes' will be accepted to approve.

  Enter a value: yes

github_repository.repo: Modifying... [id=S25-core-course-labs]
github_repository.repo: Modifications complete after 2s [id=S25-core-course-labs]
github_branch_default.master: Creating...
github_branch_default.master: Creation complete after 1s [id=S25-core-course-labs]
github_branch_protection.default: Creating...
github_branch_protection.default: Creation complete after 5s [id=BPR_kwDONxiVLM4DxL_c]

Apply complete! Resources: 2 added, 1 changed, 0 destroyed.

```
</details>


#### `terraform output`
<details>
<summary>command-output</summary>

```
repo_url = "https://github.com/KaramKhaddour/S25-core-course-labs"
```

</details>




## Best Practices

### Secrets Management
- **Sensitive data** such as API tokens and private environment variables were **never hardcoded**.
- Used **environment variables** and `.env` files to reference secrets.
- These files were **excluded from version control** via a properly configured `.gitignore`.

### Code Formatting and Validation
- `terraform fmt` was consistently used to **enforce standard code formatting**.
- `terraform validate` was run before every execution to **verify syntax** and **catch configuration errors early**.

### Planning and State Management
- `terraform plan` was used before each `terraform apply` to **preview infrastructure changes** and prevent unintended modifications.
- `terraform state list` and `terraform state show` were used prior to destroying any resource to **inspect and confirm** state details.

### Resource Importing
- Existing infrastructure components were **imported** using `terraform import` to avoid resource recreation and to bring them under Terraform management seamlessly.

### Version Locking
- **Terraform CLI version** and **provider versions** were explicitly defined using constraints to **avoid unexpected updates or breaking changes**.

### Naming and Structure
- The configuration files followed **Terraform best practices**:
  - `main.tf` for providers and core logic
  - `variables.tf` for input variables
  - `outputs.tf` for declared outputs

### Version Control Hygiene
- `.gitignore` was configured to **exclude**:
  - `.terraform/` directories
  - local state files (`*.tfstate`, `*.tfstate.backup`)
  - `.env` and other system- or user-specific files
