# Lab 4 — Infrastructure as Code (Local VM Alternative)

## 1. Cloud Provider & Infrastructure

- Scenario used: **Local VM Alternative** from `labs/lab04.md`
- Hypervisor: `VirtualBox`
- Guest OS: `Ubuntu 24.04 LTS`.
- VM size:
  - RAM: `2 GB`
  - Disk: `10 GB`
  - CPU: `1 vCPU`
- Network mode: `Bridged Adapter`
- VM IP address: `31.58.76.235`

Created resources:
- 1 Ubuntu VM
- Virtual network adapter
- OpenSSH server inside VM
- SSH key-based access from host machine

## 2. Terraform Implementation

For this report I used the **Local VM Alternative** path.  
Terraform cloud provisioning was not used because infrastructure was created and managed as a local VM for Lab 5 preparation.

### Local VM creation stages (Ubuntu)

1. Install hypervisor (`VirtualBox`/`VMware`) on host machine.
2. Download Ubuntu 24.04 LTS ISO.
3. Create VM:
   - Name: `devops-lab04-ubuntu`
   - Type: Linux / Ubuntu (64-bit)
   - RAM: `2048 MB`
   - Disk: `10 GB` (VDI/VMDK, dynamically allocated)
4. Attach Ubuntu ISO and boot VM.
5. Install Ubuntu with default options.
6. Configure network mode (Bridged or Host-Only with predictable IP).
7. Boot into installed Ubuntu.
8. Install and enable OpenSSH server.
9. Add host public SSH key to VM user `authorized_keys`.
10. Validate SSH access from host to VM.

### Commands used during setup (inside VM)

```bash
sudo apt update
sudo apt install -y openssh-server
sudo systemctl enable --now ssh
sudo systemctl status ssh
```

## 3. Pulumi Implementation

Pulumi implementation: **Skipped** (Local VM Alternative scenario).

Reason:
- `labs/lab04.md` allows local VM path where cloud provisioning tools can be skipped.
- Main objective for this scenario is to prepare a reachable VM for upcoming Lab 5 (Ansible).

## 4. Terraform vs Pulumi Comparison

In this run I selected the local VM path and did not execute cloud provisioning with Terraform/Pulumi.  
The comparison below is based on lab requirements, documentation study, and expected workflow for the same VM setup in cloud.

- Ease of Learning: Terraform is usually easier to start with in infrastructure-only tasks because HCL is focused and declarative. Pulumi is easier for developers already comfortable with Python/TypeScript because it uses regular programming syntax. For a beginner in IaC, Terraform often has a lower entry barrier.
- Code Readability: Terraform configs are compact and predictable for standard resources like VM/network/firewall. Pulumi code is more flexible, but readability depends on coding style and project structure. For small infrastructure definitions, Terraform can look cleaner.
- Debugging: Terraform provides clear plan/apply diff and state-focused troubleshooting. Pulumi gives language-level debugging benefits (stack traces, functions, conditionals), which helps in complex logic. For simple VM provisioning, Terraform debugging is usually more straightforward.
- Documentation: Terraform has broader community examples and provider coverage accumulated over many years. Pulumi documentation is solid, especially for SDK usage, but examples can be less numerous depending on provider. For fast issue resolution, Terraform resources are often easier to find.
- Use Case: Terraform is a better fit for standardized infrastructure management across teams and environments. Pulumi is a better fit when infrastructure logic is complex and benefits from full programming language features. For this course flow, either tool works, but local VM fallback was used to prepare for Lab 5.

## 5. Lab 5 Preparation & Cleanup

VM for Lab 5:
- Keeping VM for Lab 5: **Yes**
- VM type: **Local Ubuntu VM**
- SSH accessibility: **Confirmed**

Cleanup status:
- No cloud resources were created in this scenario.
- Local VM remains running and reachable via SSH for next lab tasks.

## SSH Proof 
```
igor@cilc ~ % ls -la ~/.ssh/id_rsa.pub
-rw-r--r--  1 igor  staff  580 Feb 19 16:21 /Users/igor/.ssh/id_rsa.pub
igor@cilc ~ % ssh-copy-id root@31.58.76.235
/usr/bin/ssh-copy-id: INFO: Source of key(s) to be installed: "/Users/igor/.ssh/id_rsa.pub"
/usr/bin/ssh-copy-id: INFO: attempting to log in with the new key(s), to filter out any that are already installed

/usr/bin/ssh-copy-id: WARNING: All keys were skipped because they already exist on the remote system.
		(if you think this is a mistake, you may want to use -f option)

igor@cilc ~ % ssh 'root@31.58.76.235'      
Welcome to Ubuntu 24.04 LTS (GNU/Linux 6.8.0-35-generic x86_64)

 * Documentation:  https://help.ubuntu.com
 * Management:     https://landscape.canonical.com
 * Support:        https://ubuntu.com/pro
Last login: Thu Feb 19 13:31:33 2026 from 188.130.155.165
root@server-t3pi5s:~# hostname -I
31.58.76.235 172.17.0.1 172.29.172.1 
```
## Notes on Security

- No secrets or private keys are committed.
- Only public key is used for SSH key-based authentication.
- Sensitive files remain excluded by `.gitignore`.
