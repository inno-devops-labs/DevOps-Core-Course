# Lab 04 - Local VM Alternative

## 1. Cloud Provider & Infrastructure

- Cloud provider: not used
- Rationale: expensive
- VM platform: QEMU
- OS image: Ubuntu 24.04 LTS cloud image
- VM size: 2 vCPU, 2 GB RAM, 20 GB disk
- Exposed ports:
  - SSH `127.0.0.1:2222` -> guest `22`
  - HTTP `127.0.0.1:8080` -> guest `80`
  - App `127.0.0.1:5000` -> guest `5000`
- Cost: `$0` (local machine only)
- Resources created:
  - Base Ubuntu cloud image
  - VM qcow2 disk
  - Cloud-init seed ISO
  - Running QEMU process

Deployment output:

```bash
$ ./local_vm/qemu/deploy.sh
VM name: lab4-qemu-vm
SSH command: ssh -p 2222 devops@127.0.0.1
Forwarded ports: 2222->22, 8080->80, 5000->5000
```

## 2. Terraform Implementation

Not used.

## 3. Pulumi Implementation

Not used.

## 4. Terraform vs Pulumi Comparison

- Ease of learning: Terraform is usually faster to start for basic infrastructure because examples are short and declarative. Pulumi requires selecting a language and SDK.
- Code readability: Terraform is compact for pure resource declarations. Pulumi is usually easier when logic or reuse grows.
- Debugging: Pulumi can be easier for developers due to normal language tooling. Terraform planning output is very clear for infrastructure diffs.
- Documentation: Terraform has broader ecosystem examples. Pulumi docs are strong but usually narrower for edge cases.
- Use case: Terraform fits standard multi-cloud declarative stacks. Pulumi fits teams that want infrastructure managed in application languages.

## 5. Lab 5 Preparation & Cleanup

- VM for Lab 5: `Yes`
- VM source: local QEMU VM from `local_vm/qemu`
- SSH command:

```bash
./local_vm/qemu/ssh.sh
```

- Deploy command:

```bash
chmod +x local_vm/qemu/*.sh
./local_vm/qemu/deploy.sh
```

- Stop and cleanup commands:

```bash
./local_vm/qemu/stop.sh
./local_vm/qemu/destroy.sh
```

SSH access proof:

```bash
$ ./local_vm/qemu/ssh.sh 'uname -a && lsb_release -ds && whoami'
Linux lab4-qemu-vm 6.8.0-100-generic #100-Ubuntu SMP PREEMPT_DYNAMIC Tue Jan 13 16:39:21 UTC 2026 aarch64 aarch64 aarch64 GNU/Linux
Ubuntu 24.04.4 LTS
devops
```
