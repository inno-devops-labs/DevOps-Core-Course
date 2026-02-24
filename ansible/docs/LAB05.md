# LAB05 --- Ansible Fundamentals

## 1. Architecture Overview

**Control node:** macOS (Apple Silicon M1), Ansible running locally in a
Python virtual environment\
**Target host:** Ubuntu 24.04 LTS virtual machine\
**Automation approach:** role-based Ansible architecture

This project uses a modular Ansible role structure to provision
infrastructure and deploy a containerized Python application. Roles
separate responsibilities into reusable components, making automation
easier to maintain, reuse, and scale.

Project structure:

    ansible/
    ├── ansible.cfg
    ├── inventory/
    │   └── hosts.ini
    ├── playbooks/
    │   ├── provision.yml
    │   └── deploy.yml
    ├── roles/
    │   ├── common/
    │   ├── docker/
    │   └── web_app/
    ├── group_vars/
    │   └── all.yml (encrypted with Ansible Vault)
    └── docs/
        └── LAB05.md

Roles were used instead of a single playbook because roles improve
modularity, readability, and reusability.

------------------------------------------------------------------------

## 2. Roles Documentation

### Role: common

**Purpose:** Base system provisioning.

Tasks performed:

-   Waits for apt lock release
-   Updates apt cache
-   Installs essential packages
-   Sets timezone

------------------------------------------------------------------------

### Role: docker

**Purpose:** Install and configure Docker.

Tasks performed:

-   Adds Docker repository and GPG key
-   Installs Docker Engine
-   Starts and enables Docker service
-   Adds user to docker group

------------------------------------------------------------------------

### Role: web_app

**Purpose:** Deploy containerized application.

Tasks performed:

-   Logs in to Docker Hub using Vault credentials
-   Pulls Docker image
-   Starts container
-   Performs health check

------------------------------------------------------------------------

## 3. Idempotency Demonstration

First run:

    changed=5

Second run:

    changed=0

This proves the playbook is idempotent.

------------------------------------------------------------------------

## 4. Ansible Vault Usage

Vault file:

    group_vars/all.yml

Used to store:

-   Docker Hub username
-   Docker Hub access token

Vault ensures secrets are encrypted and secure.

------------------------------------------------------------------------

## 5. Deployment Verification

Container running:

    docker ps

Output:

    ostxxp/devops-lab02-python:latest
    0.0.0.0:5000->5000/tcp

Health check:

    HTTP/1.1 200 OK
    {"status":"healthy"}

------------------------------------------------------------------------

## 6. Key Decisions

Roles were used to improve modularity and reusability.

Handlers ensure services restart only when needed.

Vault protects sensitive credentials.

Tasks are idempotent to ensure consistent infrastructure state.

------------------------------------------------------------------------

## Conclusion

Infrastructure provisioning and deployment were successfully automated
using Ansible roles, Vault, and Docker. The deployment is secure,
modular, and idempotent.
