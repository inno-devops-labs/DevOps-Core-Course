# Lab 4 - Infrastructure as Code (Local VM Only)

## Execution Mode

This lab was completed on using only **Option 1: VirtualBox VM** on local machine.

- Cloud provider usage: not used
- Terraform execution: not used
- Pulumi execution: not used
- Cost: $0

For any cloud-related requirement in the lab text: I ran local, not cloud.

---

## 1. Local Infrastructure Implemented

### Host and Hypervisor

- Host OS: Linux Mint 22.2 (Ubuntu noble base)
- Hypervisor: VirtualBox `7.0.16_Ubuntur162802`
- Virtualization mode used: local VirtualBox VM only

### Guest VM

- VM name: `lab04-ubuntu24`
- Guest OS image: `ubuntu-24.04.2-live-server-amd64.iso`
- ISO location: `/home/lanebo1/Downloads/ubuntu-24.04.2-live-server-amd64.iso`
- VM size: 2 vCPU, 2048 MB RAM, 20 GB VDI
- Network: NAT with SSH port forwarding
- Port forward: `127.0.0.1:2222 -> guest:22`

### Current VM Status (evidence)

```bash
VBoxManage showvminfo "lab04-ubuntu24" --machinereadable | rg 'name=|VMState=|memory=|cpus=|Forwarding\(0\)'
```

Result:

```text
name="lab04-ubuntu24"
memory=2048
cpus=2
VMState="running"
Forwarding(0)="guestssh,tcp,127.0.0.1,2222,,22"
```

---

## 2. Issues Encountered and Fixes

### Issue 1: VirtualBox unattended hostname validation

Error:

```text
Incomplete hostname 'lab04-ubuntu24' - must include both a name and a domain
```

Fix:

- Updated script to use FQDN style hostname:
  - `VM_HOSTNAME="${VM_NAME}.localdomain"`

### Issue 2: AMD-V busy (`VERR_SVM_IN_USE`)

Error:

```text
VirtualBox can't enable the AMD-V extension ... (VERR_SVM_IN_USE)
```

Root cause:

- KVM modules/services were active on host.

Fix used:

```bash
sudo systemctl stop qemu-kvm.service libvirtd.service virtqemud.service
sudo modprobe -r kvm_amd kvm
VBoxManage startvm "lab04-ubuntu24" --type headless
```

After fix, VM start succeeded and state became `running`.

---

## 3. SSH Access Proof (Local)

Service reachable via local forwarded port:

```bash
nc -vz -w 2 127.0.0.1 2222
```

Result:

```text
Connection to 127.0.0.1 2222 port [tcp/*] succeeded!
```

SSH banner check:

```bash
printf 'SSH-2.0-probe\r\n' | nc -w 2 127.0.0.1 2222 | head -n 1
```

Result:

```text
SSH-2.0-OpenSSH_9.6p1 Ubuntu-3ubuntu13.5
```

Connection command:

```bash
ssh -p 2222 devops@127.0.0.1
```

Initial password set during unattended setup:

```text
DevOps123!
```

---

## 4. Terraform Implementation (Conceptual Only)

Cloud note: I ran local, so Terraform was not executed in this submission.

Basic Terraform concepts:

- Provider, resource, variable, output, state

If I would do on clouds, I would:

1. Install Terraform CLI.
2. Configure provider credentials securely.
3. Define VM/network/firewall in `terraform/`.
4. Run `terraform init`, `terraform plan`, `terraform apply`.
5. Verify SSH access and outputs.
6. Destroy resources with `terraform destroy` when done.

---

## 5. Pulumi Implementation (Conceptual Only)

Cloud note: I ran local, so Pulumi was not executed in this submission.

Basic Pulumi concepts:

- Real language SDK, stacks, config/secrets, preview/apply/destroy

If I would do on clouds, I would:

1. Install Pulumi CLI.
2. Initialize project in `pulumi/`.
3. Configure provider credentials and region.
4. Recreate equivalent VM/network/firewall.
5. Run `pulumi preview`, then `pulumi up`.
6. Verify SSH access.
7. Clean up with `pulumi destroy`.

---

## 6. Terraform vs Pulumi (Conceptual)

Cloud note: conceptual comparison only, because this submission is local-only.

- Terraform is easier to start for pure infrastructure definitions.
- Pulumi is better when advanced programming logic/reuse is needed.
- Terraform ecosystem/docs are broader; Pulumi gives better native language tooling.

---

## 7. Lab 5 Preparation and Cleanup

- Keeping VM for Lab 5: Yes
- VM kept: local `lab04-ubuntu24` VirtualBox VM
- Cloud cleanup: not applicable (no cloud resources created)
- Ready for Ansible target access through `127.0.0.1:2222`

Recommended quick checks before Lab 5:

```bash
ssh -p 2222 devops@127.0.0.1 "hostnamectl"
ssh -p 2222 devops@127.0.0.1 "python3 --version"
ssh -p 2222 devops@127.0.0.1 "sudo -n true && echo sudo_ok"
```
