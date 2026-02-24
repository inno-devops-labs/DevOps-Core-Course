# Lab 04 Report — Infrastructure as Code (IaC)

## 1. Cloud Provider & Infrastructure

**Cloud Provider**: Yandex Cloud (chosen due to regional availability and educational grant support).

**Instance Type**: `standard-v2` (2 vCPU, 2GB RAM, 20% Core Fraction).

**Region/Zone**: `ru-central1-a`.

**Total Cost**: $0 (covered by the free tier/trial grant).

**Resources Created**:

* `yandex_vpc_network`: Isolated network for the project.

* `yandex_vpc_subnet`: Subnet for the compute resources.

* `yandex_vpc_security_group`: Firewall rules (SSH, HTTP, App Port).

* `yandex_compute_instance`: Ubuntu 22.04 LTS virtual machine.

## 2. Terraform Implementation

**Terraform Version**: v1.x

**Project Structure**:

* `*main.tf`: Core resource definitions.

* `providers.tf`: Provider and backend configuration.

* `variables.tf` / `outputs.tf`: Input/output definitions for modularity.

**Key Decisions**: Used a Service Account with a JSON key for authentication to avoid using personal OAuth tokens in the CLI.

**Challenges Encountered**: The main issue was a `Permission Denied` error during resource creation. It was discovered that the Billing Account must be explicitly linked to the Cloud ID, even if the account has a positive balance.

**Execution Evidence**:

* `terraform init`: Successfully initialized providers.

* `terraform apply`: Infrastructure created successfully.

* Public IP: `93.77.177.119`.

## 3. Pulumi Implementation

**Pulumi Version**: v3.x

**Language**: Python 3.12+

**Code Differences**: Unlike Terraform's HCL, Pulumi uses standard Python syntax. It required handling asynchronous outputs (Output objects) and utilized `pip` for dependency management.

**Advantages**:

* IDE support (autocompletion, type checking).

* Ability to use standard Python libraries (e.g., `os`, `json`) and logic (loops, conditionals) directly in the infrastructure code.

**Challenges**: The transition to Python 3.12 caused a `ModuleNotFoundError: No module named 'pkg_resources'` because `setuptools` is no longer bundled by default. This was solved by manually installing `setuptools` in the virtual environment.

## 4. Terraform vs Pulumi Comparison

**Ease of Learning**: Terraform was easier to learn initially. HCL is specifically designed for infrastructure and has a very shallow learning curve compared to setting up a Python environment with Pulumi.

**Code Readability**: Terraform is more readable for pure infrastructure descriptions. Pulumi is more readable for developers who are already familiar with general-purpose programming languages.

**Debugging**: Pulumi was easier to debug. Since it is a Python program, I could use standard traceback logs and print statements to identify issues with logic or types.

**Documentation**: Terraform has a larger community and more "copy-paste" examples available. Pulumi's documentation is excellent but sometimes requires switching between different language tabs (TS/Python/Go).

**Use Case**: I would use Terraform for stable, straightforward infrastructure. I would choose Pulumi for complex, dynamic environments where infrastructure depends on external API data or requires complex logic.

## 5. Lab 5 Preparation & Cleanup

**VM for Lab 5**: Yes, I am keeping the VM created via Pulumi.

**Cleanup Status**:

* Terraform resources were destroyed using `terraform destroy`.

* Pulumi resources are currently active.

* Cloud console verifies that only the `lab-vm-pulumi` instance and its associated network are running.