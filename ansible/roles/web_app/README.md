# Docker Role

Ansible role that installs `docker` with `docker-compose`, pulls the application image, and sets up services for it.

## Tags

- **wipe**: Wipes all application's artifacts by stopping services and deleting `web_app_dir` with configs
- **deploy**: Pulls and (re-)starts the application service using `docker-compose` with defined parameters

## Variables

### Application Configuration

- **`web_app_name`**: The name of the web application, also used as the Docker image name.
  - Example: `"app_python"`
- **`web_app_dir`**: The directory where the web application is installed, derived from `web_app_name`.
  - Example: `"/opt/{{ web_app_name }}"`

### Docker Configuration

- **`docker_registry`**: The Docker registry where the application image is hosted.
  - Example: `"docker.io"`
- **`docker_username`**: The username for accessing the Docker registry.
  - Example: `"adeepresession"`
- **`docker_image_tag`**: The tag for the web application image.
  - Example: `"v1.0"`
- **`docker_image`**: The full image name including registry, username, and application name.
  - Example: `"{{ docker_registry }}/{{ docker_username }}/{{ web_app_name }}:{{ docker_image_tag }}"`

### Network Configuration

- **`app_internal_port`**: The internal port on which the application operates inside the container.
  - Example: `8000`
- **`app_external_port`**: The external port accessible outside the container.
  - Example: `8000`

### Deployment Configuration

- **`web_app_full_wipe`**: Specifies whether a full wipe of the web application is required.
  - Example: `False`

## Requirements for the Hosts

- Ubuntu 22.04
- Python 3.12
- Self-made Docker role (available locally only)

## Usage

### Deploying `app_python`

```yaml
---
- name: Deploy app_python
  hosts: all
  become: yes
  roles:
    - web_app
  vars:
    web_app_name: "app_python"
    app_internal_port: 8000
    app_external_port: 8000
    web_app_full_wipe: False
```
