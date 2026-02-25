# LAB04 Report (Local VM Alternative - WSL)

## 1. Cloud Provider and Infrastructure

- Selected mode: Local VM Alternative using WSL2 (no cloud provider).
- Rationale: local mode is explicitly allowed in `labs/lab04.md`; this lab run focuses on IaC workflow basics and host access preparation for Lab 5.
- Host OS: Ubuntu 24.04.4 LTS on WSL2.
- Kernel: `Linux ZIGOTTA 6.6.87.2-microsoft-standard-WSL2`.
- Region/zone: not applicable in local mode.
- Total cost: $0.
- Resources used:
  - WSL2 Ubuntu instance (manual local VM alternative)
  - OpenSSH server (`openssh-server`)
  - SSH authentication and localhost SSH access

### Manual local VM creation/setup evidence

```bash
sudo apt update
sudo apt install -y openssh-server
mkdir -p ~/.ssh
chmod 700 ~/.ssh
cat ~/.ssh/id_ed25519.pub >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
sudo service ssh start
```

## 2. Terraform Implementation

- Terraform version: `Terraform v1.14.6`
- Project structure:
  - `terraform/main.tf`
  - `terraform/variables.tf`
  - `terraform/terraform.tfvars.example`
  - `terraform/README.md`
- Key decision: in local mode, cloud provider resources are intentionally not provisioned; Terraform configuration is kept minimal and valid.
- Challenges:
  - Cloud provider setup was intentionally skipped due to Local VM Alternative.
  - Main risk was documenting local-mode decisions clearly to avoid mismatch with cloud-only expectations.

### Command outputs

```bash
terraform init
```

```text
Initializing the backend...
Initializing provider plugins...

Terraform has been successfully initialized!

You may now begin working with Terraform. Try running "terraform plan" to see
any changes that are required for your infrastructure. All Terraform commands
should now work.

If you ever set or change modules or backend configuration for Terraform,
rerun this command to reinitialize your working directory. If you forget, other
commands will detect it and remind you to do so if necessary.
```

```bash
terraform validate
```

```text
Success! The configuration is valid.
```

### Local host access proof

```bash
sudo service ssh status
ssh $USER@localhost
```

```text
ssh.service - OpenBSD Secure Shell server
     Loaded: loaded (/usr/lib/systemd/system/ssh.service; disabled; preset: enabled)
     Active: active (running) since Wed 2026-02-25 23:43:00 MSK; 9min ago
TriggeredBy: ● ssh.socket
       Docs: man:sshd(8)
             man:sshd_config(5)
    Process: 7480 ExecStartPre=/usr/sbin/sshd -t (code=exited, status=0/SUCCESS)
   Main PID: 7482 (sshd)
      Tasks: 1 (limit: 9081)
     Memory: 1.2M (peak: 19.7M)
        CPU: 73ms
     CGroup: /system.slice/ssh.service
             └─7482 "sshd: /usr/sbin/sshd -D [listener] 0 of 10-100 startups"

Feb 25 23:43:00 ZIGOTTA systemd[1]: Starting ssh.service - OpenBSD Secure Shell server...
Feb 25 23:43:00 ZIGOTTA sshd[7482]: Server listening on 0.0.0.0 port 22.
Feb 25 23:43:00 ZIGOTTA sshd[7482]: Server listening on :: port 22.
Feb 25 23:43:00 ZIGOTTA systemd[1]: Started ssh.service - OpenBSD Secure Shell server.
Feb 25 23:43:20 ZIGOTTA sshd[7490]: Accepted password for andre from 127.0.0.1 port 52888 ssh2
Feb 25 23:43:20 ZIGOTTA sshd[7490]: pam_unix(sshd:session): session opened for user andre(uid=1000) by andre(uid=0)
```

## 3. Pulumi Implementation

- Pulumi status: skipped in execution for this lab run.
- Why skipped: Local VM Alternative in `labs/lab04.md` allows skipping Pulumi cloud recreation for Task 2.
- Validation note: `pulumi` CLI was not installed in this environment at the time of this report.
- Challenges:
  - Without running Pulumi commands, comparison is based on Terraform hands-on plus Pulumi documentation review.

### Command outputs

```bash
pulumi version
```

```text
pulumi not installed
```

## 4. Terraform vs Pulumi Comparison

### Ease of Learning

Terraform felt easier to start because HCL is focused only on infrastructure and the command flow is straightforward. For this lab, `init` and `validate` were enough to establish a working baseline quickly. Pulumi likely has a steeper start because it requires language/project runtime setup in addition to infrastructure concepts.

### Code Readability

Terraform is concise for simple infrastructure declarations and has a predictable structure (`main.tf`, `variables.tf`, `outputs.tf`). Pulumi can be more expressive because it uses general-purpose languages, which helps with reuse and abstractions. For beginners, Terraform files are usually easier to scan, while Pulumi readability depends on coding style.

### Debugging

Terraform debugging is clear for syntax and validation stages (`terraform validate`) and plan/apply errors are generally direct. Pulumi should benefit from normal language tooling (IDE, linters, debuggers), which is an advantage in complex logic. In this report, Pulumi debugging observations are inferred because no Pulumi run was executed.

### Documentation

Terraform has a larger ecosystem and more examples across providers, which makes finding fixes faster. Pulumi documentation is structured and good, but community examples are still fewer compared to Terraform. For local VM alternative work, Terraform docs were sufficient for completing the required baseline.

### Use Case

Terraform is a better default for standard declarative infrastructure and team workflows centered on plans and predictable state changes. Pulumi is stronger when infrastructure requires complex conditional logic, code reuse, or integration with software engineering patterns. In this lab context, Terraform was the practical fit for minimal local-mode validation.

## 5. Lab 5 Preparation and Cleanup

- Keeping VM for Lab 5: Yes.
- VM/host kept: WSL Ubuntu host with running SSH service.
- SSH access method: `$USER@localhost`.
- Cleanup status:
  - Cloud resources: none created.
  - Local SSH service: enabled and accessible.
