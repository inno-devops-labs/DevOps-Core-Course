# Lab 4 — Infrastructure as Code (Local VM Alternative)

## 1. Infrastructure Setup (Local Virtual Machine)

For this lab, a local virtual machine was used instead of a cloud provider.

The VM was created using VirtualBox.

### VM Configuration

- Hypervisor: VirtualBox
- Operating System: Ubuntu 24.04 LTS
- RAM: 16 GB
- CPU: 4 cores
- Disk: 20 GB
- Network: NAT with Port Forwarding
- SSH authentication: Public key based

### Network Configuration

NAT mode was used with port forwarding:

| Service | Host | Host Port | Guest Port |
|----------|--------|------------|------------|
| SSH | 127.0.0.1 | 2222 | 22 |

This allows SSH access from the host machine.

### SSH Setup

OpenSSH server was installed:

```bash
sudo apt update
sudo apt install openssh-server
```

SSH key authentication was configured:

```bash
mkdir -p ~/.ssh
nano ~/.ssh/authorized_keys
chmod 700 ~/.ssh
chmod 600 ~/.ssh/authorized_keys
```

Connection from host machine:

```bash
ssh hiksol@127.0.0.1 -p 2222
```

Password authentication was replaced with SSH key authentication.

---

## 2. Infrastructure Lifecycle Demonstration

Although Terraform and Pulumi were not used (Local VM Alternative), infrastructure lifecycle was demonstrated manually.

### Creation

* Virtual machine created in VirtualBox
* Resources allocated (CPU, RAM, Disk)
* Ubuntu installed
* SSH configured

### Configuration

* Network configured (NAT + port forwarding)
* SSH key authentication enabled
* System updated

### Usage

* Remote access via SSH verified
* VM accessible from host machine

### Stop / Start

The VM was stopped and started multiple times to verify persistence and configuration stability.

### Reproducibility

The VM configuration (CPU, RAM, Disk, Network) can be recreated manually using the same parameters in VirtualBox.

---

## 3. Infrastructure as Code Concepts (Theoretical Understanding)

Even though a cloud provider was not used, the following IaC concepts were understood:

* Infrastructure provisioning
* Infrastructure lifecycle management
* Remote access configuration
* Resource allocation planning
* Network exposure control (port forwarding)

Terraform and Pulumi were not implemented because the Local VM Alternative option was selected.

---

## 4. Lab 5 Preparation

This VM will be used in Lab 5 (Ansible).

Current VM status:

* Running
* Accessible via SSH key authentication
* Stable IP access through:

  ```bash
  ssh hiksol@127.0.0.1 -p 2222
  ```

No cloud resources were created, so no cloud cleanup is required.

---

## 5. Security Considerations

* SSH key authentication enabled
* No passwords stored in repository
* No sensitive credentials committed to Git
* VM isolated via NAT networking

---

## Conclusion

In this lab, infrastructure was provisioned using a local virtual machine instead of a cloud provider.

Although Terraform and Pulumi were not used, core infrastructure concepts such as:

* resource provisioning,
* lifecycle management,
* network configuration,
* secure remote access

were successfully demonstrated.

The virtual machine remains available for future labs.
