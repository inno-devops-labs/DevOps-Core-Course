 # Docker Role

   This role installs and configures Docker and Docker Compose.

   ## Requirements

   - Ansible 2.9+
   - Ubuntu 22.04

   ## Role Variables

   - `docker_version`: The version of Docker to install (default: `latest`).
   - `docker_compose_version`: The version of Docker Compose to install (default: `1.29.2`).

   ## Example Playbook

   ```yaml
   - hosts: all
      roles:
         - role: docker
