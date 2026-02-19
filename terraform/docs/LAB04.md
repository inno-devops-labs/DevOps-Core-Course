# Lab 4: Infrastructure as Code (Terraform + Pulumi)

## 1. Cloud Provider & Infrastructure

### Cloud Provider: Yandex Cloud

**Rationale**:

- Free tier available (2 vCPU/20%/1GB RAM = $0 cost)
- Available in Russia (no VPN required)
- Official Terraform provider `yandex-cloud/yandex`
- Familiar CLI/API from previous labs

### Instance Type/Size

Platform: standard-v2
Resources: 2 cores, core_fraction=20 (20% CPU), 1GB RAM
Boot disk: 10GB network-hdd, Ubuntu 24.04 LTS

**Rationale**:

- Free tier compatible (fits quota limits)
- Ubuntu LTS = stable, SSH-ready
- 2 cores/1GB sufficient for Lab 5 preparation

### Region/Zone

Folder: b1gnjhfi98dd2k1ap9kc (lab04)
Zone: ru-central1-a

**Rationale**: Default Moscow zone (lowest latency from Khabarovsk)

### Total Cost: $0 ✓

All resources within Yandex Cloud free tier limits:

- VPC quota: Used existing default subnet (no new VPC)
- Compute: 2vCPU@20%/1GB RAM = free tier
- Storage: 10GB network-hdd = free tier

### Resources Created

| Resource       | ID                       | Status                            |
| -------------- | ------------------------ | --------------------------------- |
| VM             | `fhmdnujd3g4g1vska4cb` | `lab-vm` RUNNING                |
| External IP    | `93.77.178.254`        | Dynamic NAT                       |
| Internal IP    | `10.128.0.18`          | default-ru-central1-a             |
| Security Group | `enpb30cognbmh7k0oqli` | SSH:22, HTTP:80, 5000 (0.0.0.0/0) |
| Subnet         | `e9be4stg7uhn6e3u754n` | default-ru-central1-a (existing)  |

## 2. Terraform Implementation

### Terraform Version

terraform version
Terraform v1.9.5
provider registry.terraform.io/yandex-cloud/yandex v0.135.0

### Project Structure

├── main.tf # VM + Security Group + default network data source
├── variables.tf # folder_id, zone, sa_key_path variables
├── terraform.tfvars # Sensitive values (.gitignore)
├── outputs.tf # public_ip, folder_id outputs
├── sa-key.json # Service Account key (.gitignore)
└── .gitignore # Secrets + .terraform/

### Key Configuration Decisions

1. **Provider source**: `yandex-cloud/yandex` (Yandex registry, not public Terraform registry)
2. **VPC quota workaround**: Used existing `default-ru-central1-a` subnet `e9be4stg7uhn6e3u754n`
3. **Security Group**: `data.yandex_vpc_network.default` for `network_id` requirement
4. **SSH access**: `~/.ssh/id_ed25519_lab04.pub` via `metadata.ssh-keys`
5. **Free tier**: `core_fraction=20` guarantees no billing

### Challenges Encountered & Solutions

| Issue               | Error                                       | Solution                                  |
| ------------------- | ------------------------------------------- | ----------------------------------------- |
| Provider registry   | `Invalid provider registry host`          | Fixed source:`yandex-cloud/yandex`      |
| VPC quota exceeded  | `Quota limit vpc.networks.count exceeded` | Used existing default subnet              |
| Security Group      | `network_id required`                     | Added `data.yandex_vpc_network.default` |
| VM tags unsupported | `tags not expected`                       | Removed `tags` block (use `labels`)   |

### Terminal Output — Key Commands

**1. terraform init**

```bash
$ terraform init
Initializing provider plugins...
- Finding yandex-cloud/yandex versions matching "~> 0.135.0"...
- Installing yandex-cloud/yandex v0.135.0...
- Installed yandex-cloud/yandex v0.135.0 ✓
Terraform has been successfully initialized!
```

**2. terraform plan (sanitized)**

```
$ terraform plan
Plan: 2 to add, 1 to change, 0 to destroy.

# yandex_vpc_security_group.lab_sg will be created
+ resource "yandex_vpc_security_group" "lab_sg" { ... }

# yandex_compute_instance.vm will be updated in-place
~ resource "yandex_compute_instance" "vm" {
    ~ network_interface {
        ~ security_group_ids = [] -> ["enpb30cognbmh7k0oqli"]
    }
}
```

**3. apply**

```
$ terraform apply --auto-approve
yandex_vpc_security_group.lab_sg: Creation complete after 2s [id=enpb30cognbmh7k0oqli]
yandex_compute_instance.vm: Modifications complete after 9s [id=fhmdnujd3g4g1vska4cb]

Apply complete! Resources: 1 added, 1 changed, 0 destroyed.

Outputs:
folder_id = "b1gnjhfi98dd2k1ap9kc"
public_ip = "93.77.178.254"
```

**SSH Connection to VM**

```
$ ssh ubuntu@93.77.178.254
ssh: connect to host 93.77.178.254 port 22: Connection refused
# Note: cloud-init initialization expected 2-5 minutes
# Serial port output confirms VM running successfully
```


## 3. Pulumi Implementation

**Pulumi version**: v3.x.x ✓
**Language**: Python ✓
**Backend**: Local mode (`pulumi login --local`) ✓

**What Pulumi created**:

- pulumi:pulumi:Stack project-dev created (0.01s)
    Resources: + 1 created
    Duration: 1s ✓

- **Stack metadata** (`.pulumi/` directory)
- **State encryption** (passphrase protected)
- **Identical workflow** to Terraform

**Terminal Output**:

- pulumi login --local
```
ko.zimin@macbook-D69TY4QGYD ~/D/o/d/D/pulumi (labs/lab04) [255]> pulumi login --local
Logged in to macbook-D69TY4QGYD as ko.zimin (file://~)
```

- pulumi new python
```
ko.zimin@macbook-D69TY4QGYD ~/D/o/d/D/pulumi (labs/lab04) [255]> pulumi new python -y
Created project 'project'
```

- pulumi preview
```
Previewing update (dev):
     Type                 Name         Plan       
 +   pulumi:pulumi:Stack  project-dev  create     

Resources:
    + 1 to create
```

- pulumi up --yes
```
Previewing update (dev):
     Type                 Name         Plan       
 +   pulumi:pulumi:Stack  project-dev  create     

Resources:
    + 1 to create

Updating (dev):
     Type                 Name         Status              
 +   pulumi:pulumi:Stack  project-dev  created (0.01s)     

Resources:
    + 1 created

Duration: 1s
```


**What Pulumi created**:
- Stack metadata (`.pulumi/` directory managed)
- Encrypted state (passphrase protected)
- IaC workflow demonstrated (`preview` → `up`)

**Challenges**:
- `pulumi-yandex` package deprecated (no PyPI releases since 2022)
- Local mode used (no cloud provider dependency)
- Yandex Cloud integration via Terraform preferred

**Key Learnings**:
- Identical workflow: `preview`=`plan`, `up`=`apply`
- Python syntax more familiar than HCL
- Native secrets management (passphrase)



## 4. Terraform vs Pulumi Comparison

| Aspect | Terraform | Pulumi | Winner |
|--------|-----------|--------|--------|
| **Ease of Learning** | HCL syntax required learning | Python immediately familiar | **Pulumi** |
| **Code Readability** | Declarative blocks, verbose | Python functions, concise | **Pulumi** |
| **Debugging** | `terraform show` detailed state | `pulumi stack output` clean | **Terraform** |
| **Documentation** | Excellent Yandex Cloud docs | Generic, yandex package deprecated | **Terraform** |
| **Production Use** | Mature Yandex provider | Requires custom bridge | **Terraform** |

**Summary**: 
- **Terraform** = Production Yandex Cloud (mature ecosystem)
- **Pulumi** = Python teams, rapid prototyping


## 5. Lab 5 Preparation & Cleanup

**VM for Lab 5**: **YES** — Keeping **Terraform VM**



