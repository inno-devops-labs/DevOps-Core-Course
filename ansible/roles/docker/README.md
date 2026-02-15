# Docker Role

This role installs and configures Docker and Docker Compose on Ubuntu.

## Requirements
- Ansible 2.15.0+
- Ubuntu 20.04 LTS

## Role Variables
- `docker_edition` (default: "ce")
- `docker_users` (default: ["docker"])

## Example Playbook
```yaml
- hosts: yandex_vm
  become: true
  roles:
    - docker
```