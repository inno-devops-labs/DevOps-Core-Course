# Lab 10 — Helm Package Manager

## Chart Overview

This lab converts the Kubernetes manifests from Lab 09 into a reusable Helm chart for the `devops-info-service` application.

The Helm chart packages the Kubernetes Deployment and Service into reusable templates with configurable values for different environments.

Chart location:

labs/lab10/k8s/devops-info-service/


Chart structure:

devops-info-service/
├── Chart.yaml
├── values.yaml
├── values-dev.yaml
├── values-prod.yaml
└── templates/
├── deployment.yaml
├── service.yaml
├── _helpers.tpl
├── NOTES.txt
└── hooks/
├── pre-install-job.yaml
└── post-install-job.yaml


### Template files

**deployment.yaml**
Defines the Kubernetes Deployment for the FastAPI application.  
Uses values for replicas, image, resources, probes, and security context.

**service.yaml**
Defines the Kubernetes Service that exposes the application.  
Service type and ports are configurable through values.

**_helpers.tpl**
Contains reusable Helm helper templates for:
- resource naming
- labels
- selectors

This avoids duplication and follows DRY principles.

**values.yaml**
Default configuration for the chart.

**values-dev.yaml**
Overrides for development environment.

**values-prod.yaml**
Overrides for production environment.

**hooks/**
Contains Helm lifecycle hook Jobs.

---

## Configuration Guide

The chart is configurable through Helm values.

### Replica configuration

replicaCount

Controls the number of application Pods.

### Image configuration

image.repository
image.tag
image.pullPolicy


Defines the Docker image used for the Deployment.

### Service configuration

service.type
service.port
service.targetPort
service.nodePort


Controls how the application is exposed.

### Resource configuration

resources.requests
resources.limits


Defines CPU and memory allocation for the container.

### Health checks

livenessProbe
readinessProbe


Both probes use the `/health` endpoint of the FastAPI application.

### Security configuration

securityContext.runAsNonRoot
securityContext.runAsUser
securityContext.allowPrivilegeEscalation


Ensures the container runs as a non-root user.

---

## Multi-Environment Configuration

Two environment configurations were created.

### Development environment (values-dev.yaml)
- replicaCount: 1
- Service type: NodePort
- lower resource limits
- faster probe timings
- suitable for local kind cluster

Install dev environment:

helm install dev-release . -f values-dev.yaml


### Production environment (values-prod.yaml)
- replicaCount: 3
- Service type: LoadBalancer
- higher resource limits
- production probe timings

Upgrade to production configuration:

helm upgrade dev-release devops-info-service -f values-prod.yaml


---

## Hook Implementation

Two Helm hooks were implemented.

### Pre-install Hook

File:

templates/hooks/pre-install-job.yaml


Purpose:
Runs a validation job before installing the application.

Hook annotations:

helm.sh/hook: pre-install
helm.sh/hook-weight: -5
helm.sh/hook-delete-policy: hook-succeeded


### Post-install Hook

File:

templates/hooks/post-install-job.yaml


Purpose:
Runs a smoke test job after installation.

Hook annotations:

helm.sh/hook: post-install
helm.sh/hook-weight: 5
helm.sh/hook-delete-policy: hook-succeeded


### Hook execution order

1. Pre-install hook runs first
2. Kubernetes resources are installed
3. Post-install hook runs after installation
4. Hook Jobs are deleted after successful execution

---

## Installation Evidence

### Helm installation

helm version


### Repository exploration

helm repo add prometheus-community https://prometheus-community.github.io/helm-charts

helm repo update
helm search repo prometheus
helm show chart prometheus-community/prometheus
helm show values prometheus-community/prometheus


### Chart validation

helm lint .
helm template mychart .
helm install --dry-run --debug test-release .


### Install release

helm install dev-release . -f values-dev.yaml


### Verify resources

helm list
kubectl get pods
kubectl get svc
kubectl get deployment


### Application test

kubectl port-forward service/dev-release-devops-info-service 8080:80
curl http://localhost:8080

curl http://localhost:8080/health


Both endpoints returned successful responses.

---

## Operations

### Install

helm install dev-release . -f values-dev.yaml


### Upgrade to production

helm upgrade dev-release . -f values-prod.yaml


### Release history

helm history dev-release


### Rollback

helm rollback dev-release 1


### Uninstall

helm uninstall dev-release


---

## Testing & Validation

The chart was validated using:

### Lint

helm lint .


### Template rendering

helm template .


### Dry-run installation

helm install --dry-run --debug test-release .


### Runtime validation

kubectl get pods
kubectl get svc
kubectl port-forward
curl /
curl /health


All tests passed successfully.

---

## Challenges & Solutions

### ImagePullBackOff
The kind cluster had intermittent connectivity issues to Docker Hub.

Solution:
Retried deployment and verified image availability.

### Security Context Issue
Kubernetes could not verify non-root execution because the image used a named user.

Solution:
Added numeric UID:

runAsNonRoot: true
runAsUser: 1000


### Default Helm Templates
The initial chart included unnecessary templates such as httproute and ingress.

Solution:
Removed unused templates and kept only required resources.

---

## What I Learned

In this lab I learned:

- how Helm packages Kubernetes applications into reusable charts
- how to convert static manifests into Helm templates
- how to use values.yaml for configuration
- how to manage multiple environments using values files
- how Helm hooks work
- how to install, upgrade, rollback, and uninstall Helm releases
- how Helm simplifies Kubernetes application management
