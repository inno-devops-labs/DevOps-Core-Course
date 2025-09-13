# Web App Role

This role deploys the application's Docker container using Docker Compose.

## Requirements

- Ansible 2.9+
- Ubuntu 22.04
- Docker installed and configured (dependency on the docker role)

## Role Variables

- **docker_image**: Docker image to pull and run (default: "yourdockeruser/yourapp:latest")
- **app_port**: Host port to map to the container's port 80 (default: 8080)
- **web_app_full_wipe**: Set to true to remove the container and docker-compose file (default: false)

## Role Structure
```bash
.
|-- defaults
|   `-- main.yml
|-- meta
|   `-- main.yml
|-- tasks
|   |-- 0-wipe.yml
|   `-- main.yml
`-- templates
   `-- docker-compose.yml.j2
```

## Role Tasks Overview

- **Pull Docker Image**:  
  Uses the `docker_image` variable to pull the required image (tagged with `docker`).

- **Deploy Application Container**:  
  Renders and deploys the Docker Compose file from the Jinja2 template, then starts the container with Docker Compose (tagged as `compose`).

- **Wipe Logic**:  
  If `web_app_full_wipe` is set to true, the tasks in `0-wipe.yml` will be executed to remove the running container and the docker-compose file. These tasks are tagged as `wipe`.

## Example Playbook

```yaml
- hosts: all
  become: yes
  roles:
    - role: docker    # Ensures Docker is installed and configured
    - role: web_app   # Deploys the application container
```
## Tags 
- deploy: Main deployment tasks.
- docker: Tasks related to pulling the Docker image.
- compose: Tasks for rendering and starting the container using Docker Compose.
- wipe: Tasks for wiping the deployed container and related files.

