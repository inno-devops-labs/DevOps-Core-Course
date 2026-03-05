## 1. Overview

In this lab, the infrastructure automation was extended using more advanced Ansible concepts including:

Task tagging and selective execution

Blocks for logical grouping of tasks

Docker Compose deployment

Controlled wipe logic for application reset

CI/CD pipeline integration using GitHub Actions

The goal of this lab was to improve maintainability, flexibility, and automation capabilities of the infrastructure management system.

The application deployed in this lab is the DevOps Info Service, a containerized FastAPI application running on a remote Ubuntu server.

## 2. Infrastructure Architecture
Control Node

Local machine running:

Ansible 2.16+

SSH access to target VM

Target Node

Remote VM running:

Ubuntu 24.04 LTS

Docker Engine

Docker Compose (v2 plugin)

Application

Containerized FastAPI service:

fayzullin/devops-info-service:latest

The service exposes the following endpoints:

/          - service information
/health    - health check endpoint

Public access:

http://93.77.190.119:5000
## 3. Ansible Role Architecture

The project uses a modular role-based structure.

ansible/
├── inventory/
│   └── hosts.ini
├── playbooks/
│   ├── provision.yml
│   └── deploy.yml
├── roles/
│   ├── common/
│   ├── docker/
│   └── web_app/
│       ├── tasks/
│       │   ├── main.yml
│       │   └── wipe.yml
│       ├── defaults/
│       │   └── main.yml
│       ├── templates/
│       │   └── docker-compose.yml.j2
│       └── meta/
│           └── main.yml
└── docs/
    └── LAB06.md
Roles

common

installs base system packages

configures system settings

docker

installs Docker engine

enables docker service

installs python docker bindings

web_app

deploys the application using Docker Compose

supports application wipe/reset

performs health verification

## 4. Task Tags

Tags were implemented to allow selective execution of tasks.

Example tags used in the project:

common
packages
docker_install
docker_config
app_deploy
compose
web_app_wipe
Listing tags
ansible-playbook playbooks/provision.yml --list-tags
Example selective execution

Install only Docker:

ansible-playbook playbooks/provision.yml --tags docker_install

Install only system packages:

ansible-playbook playbooks/provision.yml --tags packages

Tags allow faster execution during debugging or partial updates.

## 5. Blocks Usage

Ansible blocks were used to group logically related tasks inside the web_app role.

Example structure:

block:
  - create compose directory
  - generate docker-compose.yml
  - run docker compose
  - wait for service
  - run health check

Benefits of blocks:

improved readability

structured execution flow

easier error handling

ability to apply conditions or tags to multiple tasks

## 6. Docker Compose Deployment

The application is deployed using Docker Compose v2.

Compose file is generated dynamically using an Ansible template.

Template

roles/web_app/templates/docker-compose.yml.j2

Example structure:

version: "3.8"

services:
  devops-info-service:
    image: fayzullin/devops-info-service:latest
    container_name: devops-info-service
    ports:
      - "5000:5000"
    restart: unless-stopped
Deployment Flow

The web_app role performs the following steps:

Create project directory

/opt/devops-info-service

Render docker-compose file from template

Run Docker Compose

docker compose up -d

Wait until port becomes available

Verify service health endpoint

## 7. Idempotency

Ansible ensures idempotent infrastructure management.

This means repeated execution does not modify the system if the desired state is already achieved.

Example:

First run:

changed=3

Second run:

changed=0

This proves the system converges to the desired state without unnecessary modifications.

## 8. Wipe Logic (Controlled Reset)

A controlled wipe mechanism was implemented to allow safe application reset.

The wipe mechanism requires two conditions:

1️⃣ variable web_app_wipe=true

2️⃣ tag web_app_wipe

This prevents accidental destruction of running services.

Scenario 1 — Normal deploy
ansible-playbook deploy.yml

Result:

wipe skipped
application running
Scenario 2 — Wipe only
ansible-playbook deploy.yml \
-e "web_app_wipe=true" \
--tags web_app_wipe

Result:

containers removed
compose directory deleted
Scenario 3 — Clean reinstall
ansible-playbook deploy.yml \
-e "web_app_wipe=true"

Result:

wipe executed
application redeployed
Scenario 4 — Tag only (blocked)
ansible-playbook deploy.yml \
--tags web_app_wipe

Result:

wipe skipped (safety condition)
## 9. Health Verification

After deployment the service health endpoint is verified:

curl http://93.77.190.119:5000/health

Example response:

{
 "status": "healthy",
 "timestamp": "...",
 "uptime_seconds": 7128
}

This confirms that the containerized application is running correctly.

## 10. CI/CD Pipeline

A CI/CD pipeline was implemented using GitHub Actions.

Pipeline stages:

1. Lint Stage

Runs:

ansible-lint

Purpose:

validate Ansible syntax

detect best practice violations

2. Deploy Stage

Steps:

Checkout repository

Install Ansible

Install community.docker collection

Configure SSH access

Run Ansible deployment playbook

Deployment command:

ansible-playbook playbooks/deploy.yml
3. Verification Stage

After deployment, the pipeline checks application availability:

curl http://<VM-IP>:5000/health

If the endpoint responds successfully, the deployment is considered successful.

## 11. Security Considerations

Sensitive data is stored using Ansible Vault.

Encrypted file:

group_vars/all.yml

Secrets stored:

Docker Hub credentials

environment variables

Vault ensures:

secrets are encrypted in Git

secure infrastructure configuration

## 12. Conclusion

This lab extended the automation infrastructure with advanced Ansible features.

Key improvements implemented:

modular role architecture

selective task execution using tags

logical task grouping using blocks

Docker Compose deployment

controlled wipe/reset mechanism

CI/CD automation using GitHub Actions

full idempotent infrastructure management

The final system provides a reliable, maintainable, and production-ready automated deployment pipeline.

