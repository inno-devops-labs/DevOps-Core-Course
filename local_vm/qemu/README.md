# QEMU Local VM for Lab 4

## Prerequisites

- QEMU
- SSH public key at `~/.ssh/id_ed25519.pub` or `~/.ssh/id_rsa.pub`

## VM Deploy

```bash
chmod +x local_vm/qemu/*.sh
./local_vm/qemu/deploy.sh
```

Default connection:

```bash
./local_vm/qemu/ssh.sh
```

## Port Forwards

- `127.0.0.1:2222` -> guest `22` (SSH)
- `127.0.0.1:8080` -> guest `80` (HTTP)
- `127.0.0.1:5000` -> guest `5000` (app port)

## Stop and Cleanup

```bash
./local_vm/qemu/stop.sh
./local_vm/qemu/destroy.sh
```

Optional full cleanup, including downloaded Ubuntu cloud image:

```bash
REMOVE_BASE_IMAGE=1 ./local_vm/qemu/destroy.sh
```

## Configurable Variables

- `VM_NAME` default `lab4-qemu-vm`
- `VM_USER` default `devops`
- `VM_RAM_MB` default `2048`
- `VM_CPUS` default `2`
- `VM_DISK_GB` default `20`
- `SSH_PORT` default `2222`
- `HTTP_PORT` default `8080`
- `APP_PORT` default `5000`
- `SSH_PUB_KEY` overrides local key detection
