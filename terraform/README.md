# Lab 04 Local VM (WSL) Mode

This project is configured for the local VM alternative from `labs/lab04.md`.
Instead of a cloud VM, use your WSL instance as the host for Lab 4/5 practice.

## What this means for Lab 4

- Task 1: document local host setup (WSL) and SSH accessibility.
- Task 2: document that cloud recreation with Pulumi is skipped in local mode, or
  recreate an equivalent local flow if your instructor requires it.
- Task 3: fill `docs/LAB04.md` with evidence and command outputs.

## WSL setup checklist

Run in WSL:

```bash
sudo apt update
sudo apt install -y openssh-server
mkdir -p ~/.ssh
chmod 700 ~/.ssh
```

Add your public key:

```bash
cat ~/.ssh/id_ed25519.pub >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
```

Enable/start SSH service:

```bash
sudo service ssh start
sudo service ssh status
```

Verify SSH:

```bash
ssh -o StrictHostKeyChecking=no "$USER@localhost"
```

## Suggested evidence to collect

- `uname -a`
- `lsb_release -a`
- `ip a`
- `sudo service ssh status`
- successful SSH command output

Use these outputs in `docs/LAB04.md`.
