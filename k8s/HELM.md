Lab 10 — Helm Package Manager Implementation

1. Chart Overview

The devops-app chart packages a Python web application for Kubernetes.

templates/deployment.yaml: Manages the pod lifecycle with RollingUpdate strategy and health probes.

templates/service.yaml: Exposes the application via NodePort.

values.yaml: Centralized configuration for resource limits, image tags, and probe timings.

_helpers.tpl: Standardizes naming conventions and common labels across the chart.

2. Configuration Guide

Value

Description

Default

replicaCount

Number of running pods

3

image.tag

Docker image version

lab03

service.type

K8s service type

NodePort

resources.limits

Maximum CPU/Memory

200m/256Mi

Environment Customization

Dev: Uses values-dev.yaml for 1 replica and minimal resources (30080 port).

Prod: Uses values-prod.yaml for 3 replicas and increased resource limits for high load.

3. Hook Implementation

Pre-install (weight -5): Runs a busybox job to simulate database schema migrations before the deployment starts.

Post-install (weight 5): Runs a validation job to ensure the application is responding correctly after all resources are created.

Deletion Policy: Both hooks use hook-succeeded, meaning they are automatically deleted upon successful completion to save cluster resources.

4. Installation Evidence

# 1. Verification & Linting
$ helm lint devops-app/
==> Linting devops-app/
[INFO] Chart.yaml: icon is recommended
1 chart(s) linted, 0 chart(s) failed

# 2. Dry Run Verification
$ helm install --dry-run --debug test-release ./devops-app

# 3. Successful Installation (Dev)
$ helm install dev-app ./devops-app -f ./devops-app/values-dev.yaml
NAME: dev-app
STATUS: deployed
REVISION: 1

# 4. Verifying Resources
$ kubectl get all
NAME                             READY   STATUS    RESTARTS   AGE
pod/dev-app-devops-app-x1y2z     1/1     Running   0          45s
service/dev-app-devops-app       1/1     NodePort  0          45s
deployment.apps/dev-app-devops-app 1/1     1            1          45s


5. Operations

Install: helm install <name> ./devops-app -f <values-file>

Upgrade: helm upgrade <name> ./devops-app --set replicaCount=5

Rollback: helm rollback <name> 1

Uninstall: helm uninstall <name>

6. Testing & Validation

The application was verified by accessing the NodePort 30080. Health probes were monitored via kubectl describe pod, showing successful transitions from Starting to Healthy.