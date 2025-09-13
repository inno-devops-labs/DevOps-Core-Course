1. Installed terraform

```shell
PS C:\Users\EzzySoft\PycharmProjects\S25-core-course-labs\terraform> terraform version
Terraform v1.11.4
on windows_amd64
PS C:\Users\EzzySoft\PycharmProjects\S25-core-course-labs\terraform> 
```

2. Init terraform .lock

```shell
PS C:\Users\EzzySoft\PycharmProjects\S25-core-course-labs\terraform> terraform init
Initializing the backend...
Initializing provider plugins...
- Finding kreuzwerker/docker versions matching "~> 3.0.1"...
- Finding latest version of yandex-cloud/yandex...
- Installing kreuzwerker/docker v3.0.2...
- Installed kreuzwerker/docker v3.0.2 (self-signed, key ID BD080C4571C6104C)
- Installing yandex-cloud/yandex v0.141.0...
- Installed yandex-cloud/yandex v0.141.0 (self-signed, key ID E40F590B50BB8E40)
Partner and community providers are signed by their developers.
If youd like to know more about provider signing, you can read about it here:
https://developer.hashicorp.com/terraform/cli/plugins/signing
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

3. Plan Terraform

```shell
PS C:\Users\EzzySoft\PycharmProjects\S25-core-course-labs\terraform> terraform plan

Terraform used the selected providers to generate the following execution plan. Resource actions are indicated with the following symbols:
  + create

Terraform will perform the following actions:

  # docker_container.app_python will be created
  + resource "docker_container" "app_python" {
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
      + image                                       = (known after apply)
      + init                                        = (known after apply)
      + ipc_mode                                    = (known after apply)
      + log_driver                                  = (known after apply)
      + logs                                        = false
      + must_run                                    = true
      + name                                        = "app_python_container"
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
          + external = 5000
          + internal = 5000
          + ip       = "0.0.0.0"
          + protocol = "tcp"
        }
    }

  # docker_image.moscow_time will be created
  + resource "docker_image" "moscow_time" {
      + id           = (known after apply)
      + image_id     = (known after apply)
      + keep_locally = false
      + name         = "ezzysoft/moscow-time:latest"
      + repo_digest  = (known after apply)

      + build {
          + cache_from     = []
          + context        = "../app_python"
          + dockerfile     = "Dockerfile"
          + extra_hosts    = []
          + remove         = true
          + security_opt   = []
          + tag            = []
            # (11 unchanged attributes hidden)
        }
    }

  # yandex_compute_disk.boot-disk-1 will be created
  + resource "yandex_compute_disk" "boot-disk-1" {
      + block_size  = 4096
      + created_at  = (known after apply)
      + folder_id   = (known after apply)
      + id          = (known after apply)
      + image_id    = "fd81n0sfjm6d5nq6l05g"
      + name        = "boot-disk-1"
      + product_ids = (known after apply)
      + size        = 20
      + status      = (known after apply)
      + type        = "network-hdd"
      + zone        = "ru-central1-a"

      + disk_placement_policy (known after apply)

      + hardware_generation (known after apply)
    }

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
          + "user-data" = <<-EOT
                #cloud-config
                users:
                  - name: ezzy
                    groups: sudo
                    shell: /bin/bash
                    sudo: 'ALL=(ALL) NOPASSWD:ALL'
                    ssh_authorized_keys:
                      - ezzy:ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIM+TOfIcOibPsJwS9Gtg2Zc5i4xDbo/XngqM5d638U ezzy@desktop
            EOT
        }
      + name                      = "terraform1"
      + network_acceleration_type = "standard"
      + platform_id               = "standard-v1"
      + service_account_id        = (known after apply)
      + status                    = (known after apply)
      + zone                      = (known after apply)

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
          + core_fraction = 100
          + cores         = 2
          + memory        = 2
        }

      + scheduling_policy (known after apply)
    }

  # yandex_vpc_network.network-1 will be created
  + resource "yandex_vpc_network" "network-1" {
      + created_at                = (known after apply)
      + default_security_group_id = (known after apply)
      + folder_id                 = (known after apply)
      + id                        = (known after apply)
      + labels                    = (known after apply)
      + name                      = "network1"
      + subnet_ids                = (known after apply)
    }

  # yandex_vpc_subnet.subnet-1 will be created
  + resource "yandex_vpc_subnet" "subnet-1" {
      + created_at     = (known after apply)
      + folder_id      = (known after apply)
      + id             = (known after apply)
      + labels         = (known after apply)
      + name           = "subnet1"
      + network_id     = (known after apply)
      + v4_cidr_blocks = [
          + "192.168.10.0/24",
        ]
      + v6_cidr_blocks = (known after apply)
      + zone           = "ru-central1-a"
    }

Plan: 6 to add, 0 to change, 0 to destroy.

Changes to Outputs:
  + container_id             = (known after apply)
  + external_ip_address_vm_1 = (known after apply)
  + image_id                 = (known after apply)
  + internal_ip_address_vm_1 = (known after apply)

─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────── 

Note: You didn't use the -out option to save this plan, so Terraform can't guarantee to take exactly these actions if you run "terraform apply" now.
```

4. Deploy with terraform

```shell
PS C:\Users\EzzySoft\PycharmProjects\S25-core-course-labs\terraform> terraform apply -auto-approve
docker_image.moscow_time: Refreshing state... [id=sha256:a26d1944d32ba4efc45cc01376973570c3eef502f00cd949d05f1a301f60a50fezzysoft/moscow-time:latest]
docker_container.app_python: Refreshing state... [id=d1eee63c856703734fff83c5b63d9cdaa2f01886795d4e86f3c30d498675fb4c]
yandex_compute_disk.boot-disk-1: Refreshing state... [id=fhm2d7fk9pba8l6tr70v]

Note: Objects have changed outside of Terraform

Terraform detected the following changes made outside of Terraform since the last "terraform apply" which may have affected this plan:

  # yandex_compute_disk.boot-disk-1 has been deleted
  - resource "yandex_compute_disk" "boot-disk-1" {
      - id          = "fhm2d7fk9pba8l6tr70v" -> null
        name        = "boot-disk-1"
        # (11 unchanged attributes hidden)

        # (2 unchanged blocks hidden)
    }


Unless you have made equivalent changes to your configuration, or ignored the relevant attributes using ignore_changes, the following plan may include actions to undo or respond to these changes.

─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────── 

Terraform used the selected providers to generate the following execution plan. Resource actions are indicated with the following symbols:
  + create
-/+ destroy and then create replacement

Terraform will perform the following actions:

  # docker_container.app_python must be replaced
-/+ resource "docker_container" "app_python" {
      + bridge                                      = (known after apply)
      ~ command                                     = [
          - "python",
          - "app.py",
        ] -> (known after apply)
      + container_logs                              = (known after apply)
      - cpu_shares                                  = 0 -> null
      - dns                                         = [] -> null
      - dns_opts                                    = [] -> null
      - dns_search                                  = [] -> null
      ~ entrypoint                                  = [] -> (known after apply)
      ~ env                                         = [] -> (known after apply)
      + exit_code                                   = (known after apply)
      - group_add                                   = [] -> null
      ~ hostname                                    = "d1eee63c8567" -> (known after apply)
      ~ id                                          = "d1eee63c856703734fff83c5b63d9cdaa2f01886795d4e86f3c30d498675fb4c" -> (known after apply)
      ~ init                                        = false -> (known after apply)
      ~ ipc_mode                                    = "private" -> (known after apply)
      ~ log_driver                                  = "json-file" -> (known after apply)
      - log_opts                                    = {} -> null
      - max_retry_count                             = 0 -> null
      - memory                                      = 0 -> null
      - memory_swap                                 = 0 -> null
        name                                        = "app_python_container"
      ~ network_data                                = [
          - {
              - gateway                   = "172.17.0.1"
              - global_ipv6_prefix_length = 0
              - ip_address                = "172.17.0.2"
              - ip_prefix_length          = 16
              - mac_address               = "16:22:4c:5e:36:98"
              - network_name              = "bridge"
                # (2 unchanged attributes hidden)
            },
        ] -> (known after apply)
      - network_mode                                = "bridge" -> null # forces replacement
      - privileged                                  = false -> null
      - publish_all_ports                           = false -> null
      ~ runtime                                     = "runc" -> (known after apply)
      ~ security_opts                               = [] -> (known after apply)
      ~ shm_size                                    = 64 -> (known after apply)
      + stop_signal                                 = (known after apply)
      ~ stop_timeout                                = 0 -> (known after apply)
      - storage_opts                                = {} -> null
      - sysctls                                     = {} -> null
      - tmpfs                                       = {} -> null
      - user                                        = "appuser" -> null
      - working_dir                                 = "/home/appuser/app" -> null
        # (18 unchanged attributes hidden)

      ~ healthcheck (known after apply)

      ~ labels (known after apply)

        # (1 unchanged block hidden)
    }

  # yandex_compute_disk.boot-disk-1 will be created
  + resource "yandex_compute_disk" "boot-disk-1" {
      + block_size  = 4096
      + created_at  = (known after apply)
      + folder_id   = (known after apply)
      + id          = (known after apply)
      + image_id    = "fd81n0sfjm6d5nq6l05g"
      + name        = "boot-disk-1"
      + product_ids = (known after apply)
      + size        = 20
      + status      = (known after apply)
      + type        = "network-hdd"
      + zone        = "ru-central1-a"

      + disk_placement_policy (known after apply)

      + hardware_generation (known after apply)
    }

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
          + "user-data" = <<-EOT
                #cloud-config
                users:
                  - name: ezzy
                    groups: sudo
                    shell: /bin/bash
                    sudo: 'ALL=(ALL) NOPASSWD:ALL'
                    ssh_authorized_keys:
                      - ezzy:ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIM+TOfIcOibPsJwS9Gtg2Zc5i4xDbo/XngqM5d638U ezzy@desktop
            EOT
        }
      + name                      = "terraform1"
      + network_acceleration_type = "standard"
      + platform_id               = "standard-v1"
      + service_account_id        = (known after apply)
      + status                    = (known after apply)
      + zone                      = (known after apply)

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
          + core_fraction = 100
          + cores         = 2
          + memory        = 2
        }

      + scheduling_policy (known after apply)
    }

  # yandex_vpc_network.network-1 will be created
  + resource "yandex_vpc_network" "network-1" {
      + created_at                = (known after apply)
      + default_security_group_id = (known after apply)
      + folder_id                 = (known after apply)
      + id                        = (known after apply)
      + labels                    = (known after apply)
      + name                      = "network1"
      + subnet_ids                = (known after apply)
    }

  # yandex_vpc_subnet.subnet-1 will be created
  + resource "yandex_vpc_subnet" "subnet-1" {
      + created_at     = (known after apply)
      + folder_id      = (known after apply)
      + id             = (known after apply)
      + labels         = (known after apply)
      + name           = "subnet1"
      + network_id     = (known after apply)
      + v4_cidr_blocks = [
          + "192.168.10.0/24",
        ]
      + v6_cidr_blocks = (known after apply)
      + zone           = "ru-central1-a"
    }

Plan: 5 to add, 0 to change, 1 to destroy.

Changes to Outputs:
  ~ container_id             = "d1eee63c856703734fff83c5b63d9cdaa2f01886795d4e86f3c30d498675fb4c" -> (known after apply)
  + external_ip_address_vm_1 = (known after apply)
  + internal_ip_address_vm_1 = (known after apply)
docker_container.app_python: Destroying... [id=d1eee63c856703734fff83c5b63d9cdaa2f01886795d4e86f3c30d498675fb4c]
docker_container.app_python: Destruction complete after 1s
docker_container.app_python: Creating...
yandex_vpc_network.network-1: Creating...
yandex_compute_disk.boot-disk-1: Creating...
docker_container.app_python: Creation complete after 1s [id=68dc05d024cb76cbf52df8be292f05cbedab12929adf25ed849528b76251a42d]
yandex_vpc_network.network-1: Creation complete after 4s [id=enpvlgckmp32b7mvsteu]
yandex_vpc_subnet.subnet-1: Creating...
yandex_vpc_subnet.subnet-1: Creation complete after 0s [id=e9bq9o9edr9eqmuu0n82]
yandex_compute_disk.boot-disk-1: Still creating... [10s elapsed]
yandex_compute_disk.boot-disk-1: Creation complete after 15s [id=fhmtb6giaqn8t5agqevg]
yandex_compute_instance.vm-1: Creating...
yandex_compute_instance.vm-1: Still creating... [10s elapsed]
yandex_compute_instance.vm-1: Still creating... [20s elapsed]
yandex_compute_instance.vm-1: Still creating... [30s elapsed]
yandex_compute_instance.vm-1: Creation complete after 31s [id=fhm5q2gpf4ofuiotfvo1]

Apply complete! Resources: 5 added, 0 changed, 1 destroyed.

Outputs:

container_id = "68dc05d024cb76cbf52df8be292f05cbedab12929adf25ed849528b76251a42d"
external_ip_address_vm_1 = "51.250.65.239"
image_id = "sha256:a26d1944d32ba4efc45cc01376973570c3eef502f00cd949d05f1a301f60a50f"
internal_ip_address_vm_1 = "192.168.10.30"
```

5. State list

```shell
PS C:\Users\EzzySoft\PycharmProjects\S25-core-course-labs\terraform>     terraform state list
docker_container.app_python
docker_image.moscow_time
yandex_compute_disk.boot-disk-1
yandex_compute_instance.vm-1
yandex_vpc_network.network-1
yandex_vpc_subnet.subnet-1
PS C:\Users\EzzySoft\PycharmProjects\S25-core-course-labs\terraform>
```

6. State show (f.e. docker_image.moscow_time)

```shell
PS C:\Users\EzzySoft\PycharmProjects\S25-core-course-labs\terraform>     terraform state show docker_image.moscow_time
# docker_image.moscow_time:
resource "docker_image" "moscow_time" {
    id           = "sha256:a26d1944d32ba4efc45cc01376973570c3eef502f00cd949d05f1a301f60a50fezzysoft/moscow-time:latest"
    image_id     = "sha256:a26d1944d32ba4efc45cc01376973570c3eef502f00cd949d05f1a301f60a50f"
    keep_locally = false
    name         = "ezzysoft/moscow-time:latest"
    repo_digest  = null

    build {
        build_arg       = {}
        build_args      = {}
        build_id        = null
        cache_from      = []
        cgroup_parent   = null
        context         = "../app_python"
        cpu_period      = 0
        cpu_quota       = 0
        cpu_set_cpus    = null
        cpu_set_mems    = null
        cpu_shares      = 0
        dockerfile      = "Dockerfile"
        extra_hosts     = []
        force_remove    = false
        isolation       = null
        label           = {}
        labels          = {}
        memory          = 0
        memory_swap     = 0
        network_mode    = null
        no_cache        = false
        platform        = null
        pull_parent     = false
        remote_context  = null
        remove          = true
        security_opt    = []
        session_id      = null
        shm_size        = 0
        squash          = false
        suppress_output = false
        tag             = []
        target          = null
        version         = null
    }
}
```

7. Test sensitive git token value passing

```shell
PS C:\Users\EzzySoft\PycharmProjects\S25-core-course-labs\terraform\github> 
PS C:\Users\EzzySoft\PycharmProjects\S25-core-course-labs\terraform\github> terraform console -no-color
> var.token
(sensitive value)
```

8. Deploy git repo with terraform 
```shell
PS C:\Users\EzzySoft\PycharmProjects\S25-core-course-labs\terraform\github> terraform plan                                                                               
github_repository.repo: Refreshing state... [id=1Pwd9000-Demo-Repo-2022]
github_branch_default.master: Refreshing state... [id=1Pwd9000-Demo-Repo-2022]
github_branch_protection.default: Refreshing state... [id=BPR_kwDOOhNk2c4DtlsV]

No changes. Your infrastructure matches the configuration.

Terraform has compared your real infrastructure against your configuration and found no differences, so no changes are needed.
PS C:\Users\EzzySoft\PycharmProjects\S25-core-course-labs\terraform\github> terraform apply                                                                              
github_repository.repo: Refreshing state... [id=1Pwd9000-Demo-Repo-2022]
github_branch_default.master: Refreshing state... [id=1Pwd9000-Demo-Repo-2022]
github_branch_protection.default: Refreshing state... [id=BPR_kwDOOhNk2c4DtlsV]

No changes. Your infrastructure matches the configuration.

Terraform has compared your real infrastructure against your configuration and found no differences, so no changes are needed.

Apply complete! Resources: 0 added, 0 changed, 0 destroyed.
```

![img.png](img.png)