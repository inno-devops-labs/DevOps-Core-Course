# LAB05 — Ansible Fundamentals

## 1. Architecture Overview

Ansible version: 2.16+

Target VM: Ubuntu 24.04 LTS (Yandex Cloud)

Cloud Provider: Yandex Cloud

Application: DevOps Info Service (FastAPI)

Container Runtime: Docker

Role Structure

The project follows a role-based architecture:

common — installs base packages and configures system settings

docker — installs and configures Docker engine

app_deploy — deploys the containerized application

Roles were chosen instead of monolithic playbooks to ensure modularity, reusability, and maintainability.

## 2. Role Descriptions
Role: common

Updates apt cache

Installs essential system packages

Configures timezone

Fully idempotent

Role: docker

Installs Docker from Ubuntu repository

Enables and starts docker service

Adds user to docker group

Installs python3-docker for Ansible modules

Role: app_deploy

Pulls Docker image from Docker Hub

Removes previous container if exists

Starts container with restart policy

Performs health check

Uses Ansible Vault for credentials

## 3. Idempotency Demonstration
First Run

Several tasks were marked as changed because packages and services were installed.

Second Run

All tasks returned ok with changed=0, proving idempotency.

Idempotency is achieved by using declarative modules (apt, service, docker_container) with defined states.

## 4. Deployment
Successful Deployment

Running Container

Health Check

The application is publicly available at:

http://93.77.190.119:5000
## 5. Ansible Vault

Sensitive credentials are stored in:

group_vars/all.yml

The file is encrypted using Ansible Vault:

Vault ensures secrets are not stored in plaintext while allowing version control.

## 6. Key Concepts

Idempotency ensures repeated execution does not change system state unnecessarily.

Roles improve reusability and separation of concerns.

Handlers optimize service restarts.

Vault secures sensitive data.

## 7. Conclusion

The infrastructure provisioning and application deployment were successfully automated using Ansible roles.
The solution is idempotent, secure, modular, and production-ready.
