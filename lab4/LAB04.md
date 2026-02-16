# Lab 04 Documentation

## 1. Cloud Provider & Infrastructure

### Cloud provider chosen and rationale

- **Provider:** Yandex Cloud
- **Why this provider:** it is covered in the lab guide, has direct Terraform/Pulumi provider support, and allows free-tier-friendly VM parameters for the required learning tasks.

### Instance type/size and why

- **Platform:** `standard-v2`
- **Compute:** `2 vCPU`, `core_fraction = 20`, `1 GB RAM`
- **Disk:** `10 GB`, `network-hdd`
- **Reasoning:** this is the minimum configuration from the lab recommendation for Yandex Cloud free-tier practice and is enough for SSH access and later Ansible exercises.

### Region/zone selected

- **Zone:** `ru-central1-d`
- **Reason:** available in the current folder/project and used consistently in both Terraform and Pulumi runs.

### Total cost

- Targeted free-tier-friendly setup for short-lived lab usage.
- Expected cost for this lab workflow is effectively **~$0** if resources are cleaned up or only one small VM is kept briefly for Lab 5.

### Resources created

**Terraform run (Task 1):**

- `yandex_compute_instance.lab04`
- `yandex_vpc_security_group.lab04`
- `yandex_vpc_address.lab04`
- `yandex_vpc_network.lab04` and `yandex_vpc_subnet.lab04` are defined in code; for this run network/subnet reuse was enabled because folder VPC network quota was exhausted.

**Pulumi run (Task 2):**

- `yandex:index/computeInstance:ComputeInstance` (`lab04-vm`)
- `yandex:index/vpcSecurityGroup:VpcSecurityGroup` (`lab04-security-group`)
- `yandex:index/vpcAddress:VpcAddress` (`lab04-public-ip`)
- Pulumi code also supports creating VPC/subnet, with fallback to existing network/subnet when quota limits apply.

---

## 2. Terraform Implementation

### Terraform version used

- `Terraform v1.5.7` (`darwin_arm64`)

### Project structure explanation

`terraform/`:

- `providers.tf` - Terraform and provider configuration
- `main.tf` - resources and data sources
- `variables.tf` - configurable inputs
- `outputs.tf` - exported values (public IP, SSH command, etc.)
- `terraform.tfvars.example` - non-secret variable template
- `terraform.tfvars` - local values with credentials path (gitignored)
- `.gitignore` / `README.md`

### Key configuration decisions

- Credentials are passed via `service_account_key_file` from local path, not committed to Git.
- SSH ingress is restricted to current public IP `/32`.
- Ports `80` and `5000` are open for future app deployment requirements.
- VM uses free-tier-friendly settings and labels.
- Added fallback variable `existing_instance_id_for_network` to reuse existing subnet/network in case of VPC quota limits.

### Challenges encountered

- Terraform registry access was geo-restricted; provider plugin had to be installed locally.
- Folder hit `vpc.networks.count` quota limit, so network/subnet reuse was required.
- SSH user mismatch was fixed by switching metadata user to `ubuntu` for reliable access.

### Terminal output from key commands

#### `terraform init`

```bash
terraform init -no-color
```

```text
Terraform has been successfully initialized!
```

#### `terraform plan` (sanitized)

```bash
terraform plan -no-color
```

```text
Plan: 2 to add, 0 to change, 0 to destroy.
```

#### `terraform apply`

```bash
terraform apply -auto-approve -no-color
```

```text
Apply complete! Resources: 2 added, 0 changed, 0 destroyed.
```

```text
ssh_command = "ssh ubuntu@158.160.214.133"
vm_id = "fv43ujts6lcnh5ij4r04"
vm_internal_ip = "10.130.0.21"
vm_public_ip = "158.160.214.133"
```

#### SSH connection to Terraform VM

```bash
ssh -o BatchMode=yes -o StrictHostKeyChecking=no ubuntu@158.160.214.133 "hostname && whoami"
```

```text
fv43ujts6lcnh5ij4r04
ubuntu
```

---

## 3. Pulumi Implementation

### Pulumi version and language used

- **Pulumi CLI:** `v3.220.0`
- **Language:** `Python`
- **Provider package:** `pulumi-yandex`

### How code differs from Terraform

- Terraform uses declarative HCL (`resource`, `data`, `variables`, `outputs`), while Pulumi uses imperative Python code with classes and functions.
- Conditional logic (create network or reuse existing network) is simpler and clearer in Python than in HCL conditionals.
- Pulumi exports values directly from program outputs (`pulumi.export`), while Terraform uses separate `outputs.tf`.

### Advantages discovered

- Better flexibility for complex branching logic.
- Easier to build helper functions and reusable code blocks.
- Native language tooling (Python virtualenv and package management).

### Challenges encountered

- `pulumi-yandex` currently relies on `pkg_resources`, so `setuptools` had to be pinned to `<81`.
- First `pulumi up` failed with `KeyError: 0` because provider output shape was map-like, not list-like; fixed by defensive parsing helper.
- Same VPC quota limitation required reusing existing subnet/network logic, similar to Terraform workaround.

### Terminal output from Pulumi commands

#### `pulumi preview`

```bash
PULUMI_CONFIG_PASSPHRASE='***' pulumi preview --non-interactive
```

```text
Resources:
    + 5 to create
```

#### `pulumi up`

```bash
PULUMI_CONFIG_PASSPHRASE='***' pulumi up --yes --non-interactive
```

```text
Resources:
    + 1 created
    4 unchanged
```

```text
sshCommand    ssh ubuntu@158.160.162.138
vmId          fv48ri0v9h7addr29frj
vmInternalIp  10.130.0.34
vmPublicIp    158.160.162.138
```

#### SSH connection to Pulumi VM

```bash
ssh -o BatchMode=yes -o StrictHostKeyChecking=no ubuntu@158.160.162.138 "hostname && whoami"
```

```text
fv48ri0v9h7addr29frj
ubuntu
```

---

## 4. Terraform vs Pulumi Comparison

### Ease of Learning

Terraform was easier to start with because HCL is focused only on infrastructure and the examples in docs are very consistent. The command workflow (`init -> plan -> apply`) is straightforward and predictable. Pulumi required understanding both IaC concepts and Python/provider SDK details, which adds an extra learning layer. For beginner-friendly first IaC tasks, Terraform felt faster to learn.

### Code Readability

For static infrastructure blocks, Terraform HCL looked cleaner and more compact. For conditional behavior (for example, network create vs reuse), Pulumi Python was more readable because normal language constructs can be used. In this lab both were readable, but they are readable in different scenarios. I prefer Terraform for simple stacks and Pulumi for logic-heavy stacks.

### Debugging

Terraform debugging is strong when the issue is in resource diffs or provider validation, because `terraform plan` gives a very explicit change model. Pulumi debugging helped when runtime logic was the issue, because Python stack traces pointed to exact code lines. In practice, Pulumi gave better diagnostics for programming errors, while Terraform gave better diagnostics for declarative state drift/plans. Both were useful but in different failure modes.

### Documentation

Terraform has larger ecosystem documentation and more examples for many providers and edge cases. Pulumi docs are good but sometimes rely on SDK specifics and language examples that can differ by version. In this lab, Terraform docs were enough to solve core setup quickly, while Pulumi required a bit more experimentation with SDK signatures. Overall, Terraform documentation felt more mature for troubleshooting.

### Use Case

I would choose Terraform for standard, mostly static infrastructure where readability and team-wide consistency are top priorities. I would choose Pulumi when infrastructure logic needs loops, branching, helper abstractions, or integration with application code patterns. For this lab both tools delivered equivalent final infrastructure. Selection depends on team skills and complexity of infrastructure logic.

---

## 5. Lab 5 Preparation & Cleanup

### VM for Lab 5

- **Keeping VM for Lab 5:** **Yes**
- **Which VM is kept:** **Pulumi-created VM**
  - `vmId = fv48ri0v9h7addr29frj`
  - `vmPublicIp = 158.160.162.138`

### Cleanup status

- Terraform resources from Task 1 were destroyed before Task 2.

```bash
terraform destroy -auto-approve -no-color
```

```text
Destroy complete! Resources: 3 destroyed.
```

- Terraform state after cleanup:

```bash
terraform state list
```

```text
# empty output (no resources in state)
```

- Pulumi VM remains running and accessible for Lab 5:

```bash
ssh -o BatchMode=yes -o StrictHostKeyChecking=no ubuntu@158.160.162.138 "hostname && whoami"
```

```text
fv48ri0v9h7addr29frj
ubuntu
```

### Secrets and sanitization

- No secrets are committed to Git.
- Sensitive values are stored locally (`terraform.tfvars`, Pulumi stack config file).
- Service account key JSON stays outside source control.
