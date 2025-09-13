# Docker Role

This role installs and configures Docker and Docker Compose.

## Requirements

- Ansible 2.9+
- Ubuntu 22.04

## Role Variables

- `docker_compose_version`: The version of Docker Compose to install (default: `2.27.0`).

## Example Playbook

```yaml
- hosts: all
   roles:
      - role: docker
```
