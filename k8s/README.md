# Lab 09 - Kubernetes Fundamentals

## 1. Architecture Overview

The solution deploys the Python app from Lab 2 as a replicated, self-healing Kubernetes workload.

Core architecture:

- Namespace: devops-lab09
- Deployment: devops-python (3 replicas)
- Service: devops-python-service (NodePort, host access)
- Probes: liveness and readiness on /health
- Resource control: requests and limits to prevent noisy-neighbor issues

Traffic flow:

- User -> NodePort service (port 30080) -> devops-python pods on port 8080

Bonus architecture:

- Second deployment: devops-python-v2 (2 replicas)
- ClusterIP services for app1 and app2
- NGINX Ingress routes:
  - /app1 -> app1 service
  - /app2 -> app2 service
- TLS via secret devops-local-tls

## 2. Manifest Files and Key Choices

Core manifests:

- k8s/namespace.yml
  - Creates isolated namespace for all Lab 9 resources
- k8s/deployment.yml
  - 3 replicas for availability
  - RollingUpdate strategy with maxSurge: 1 and maxUnavailable: 0
  - requests: 100m CPU, 128Mi memory
  - limits: 200m CPU, 256Mi memory
  - readiness and liveness probes on /health
- k8s/service.yml
  - NodePort exposure for local testing
  - service port 80 -> targetPort 8080

Bonus manifests:

- k8s/bonus/deployment-app2.yml
- k8s/bonus/service-app1.yml
- k8s/bonus/service-app2.yml
- k8s/bonus/ingress.yml
- k8s/bonus/generate-tls.sh

Why these values:

- Replicas 3: baseline high availability in local cluster
- Requests/limits: enforce scheduling guarantees and prevent runaway usage
- Health probes: enables self-healing and safe rolling updates
- maxUnavailable 0: avoids downtime during updates

## 3. Local Kubernetes Setup

Used tool:

- kind (installed on Windows host with Docker Desktop)

Why kind:

- Lightweight local cluster
- Fast create/destroy cycle
- Good fit for repeatable lab verification

Executed setup commands:

- winget install Kubernetes.kind
- kind create cluster --name lab09 --wait 180s
- kubectl cluster-info --context kind-lab09
- kubectl get nodes -o wide

Observed output summary:

- Kubernetes control plane reachable on local endpoint
- Node lab09-control-plane is Ready (v1.35.0)

## 4. Deployment Evidence Commands

Apply core manifests:

- kubectl apply -f k8s/namespace.yml
- kubectl apply -f k8s/deployment.yml
- kubectl apply -f k8s/service.yml

Inspect resources:

- kubectl get all -n devops-lab09
- kubectl get pods,svc -n devops-lab09 -o wide
- kubectl describe deployment devops-python -n devops-lab09

Access service:

Used method:

- kubectl port-forward -n devops-lab09 service/devops-python-service 18080:80
- curl http://127.0.0.1:18080/health
- curl http://127.0.0.1:18080/

Observed output summary:

- Deployment rollout completed successfully
- kubectl get all showed 3 running pods for devops-python
- Service devops-python-service exposed as NodePort 30080
- Health endpoint returned status healthy

## 5. Scaling and Updates

Scaling demonstration:

- kubectl scale deployment/devops-python -n devops-lab09 --replicas=5
- kubectl get pods -n devops-lab09 -w
- kubectl rollout status deployment/devops-python -n devops-lab09

Rolling update demonstration:

- kubectl set env deployment/devops-python -n devops-lab09 LAB09_ROLLOUT=demo1
- kubectl rollout status deployment/devops-python -n devops-lab09
- kubectl rollout history deployment/devops-python -n devops-lab09

Rollback demonstration:

- kubectl rollout undo deployment/devops-python -n devops-lab09
- kubectl rollout history deployment/devops-python -n devops-lab09

Observed output summary:

- Scaling to 5 replicas completed with READY 5/5
- Rolling update completed with revision increment
- Rollback completed successfully and new revision recorded

## 6. Bonus: Ingress with TLS

Deploy second app and services:

- kubectl apply -f k8s/bonus/deployment-app2.yml
- kubectl apply -f k8s/bonus/service-app1.yml
- kubectl apply -f k8s/bonus/service-app2.yml

Enable ingress controller:

Minikube:

- minikube addons enable ingress

kind:

- kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/kind/deploy.yaml

Generate self-signed cert and TLS secret manifest:

- cd k8s/bonus
- chmod +x generate-tls.sh
- ./generate-tls.sh
- kubectl apply -f tls-secret.yml

Apply ingress:

- kubectl apply -f k8s/bonus/ingress.yml

Hosts entry and verification:

- Local verification used ingress-controller port-forward:
  - kubectl -n ingress-nginx port-forward service/ingress-nginx-controller 18443:443
  - curl -k https://127.0.0.1:18443/app1/health -H "Host: local.example.com"
  - curl -k https://127.0.0.1:18443/app2/health -H "Host: local.example.com"

Observed output summary:

- ingress-nginx controller installed and Ready
- Ingress resource devops-apps-ingress created
- Both TLS routes returned healthy responses

Ingress benefit vs NodePort:

- Single entrypoint for multiple apps
- Path-based routing at HTTP layer
- Centralized TLS termination

## 7. Production Considerations

Health checks:

- Liveness probe restarts stuck containers
- Readiness probe removes unhealthy pods from service endpoints

Resources:

- requests ensure placement guarantees
- limits cap container resource use and protect node stability

Improvements for production:

- Pin immutable image tags (not latest)
- Add PodDisruptionBudget and HPA
- Add NetworkPolicy and RBAC hardening
- Add dedicated startupProbe if cold starts are high

Observability strategy:

- Reuse Lab 8 stack: Prometheus and Grafana
- Scrape pod metrics and add service-level dashboards
- Track RED metrics and alerting rules

## 8. Challenges and Solutions

1. Cluster runtime availability

- Challenge: Docker was not integrated into WSL, so kind could not run in WSL shell
- Solution: installed and ran kind on Windows host where Docker Desktop was available

2. Zero-downtime update configuration

- Challenge: avoid request drops during rollout
- Solution: maxUnavailable: 0 and readiness probes on /health

3. Bonus ingress path routing

- Challenge: route prefixed paths to root-based apps
- Solution: regex path rules plus nginx rewrite-target /$2

## 9. Validation Notes

Local runtime validation completed against real cluster:

- Cluster creation: successful
- Core deployment/service: successful
- Scaling/update/rollback: successful
- Bonus ingress + TLS routing: successful

Additional evidence commands to attach screenshots/logs:

- kubectl get all -n devops-lab09
- kubectl get pods,svc -n devops-lab09 -o wide
- kubectl describe deployment devops-python -n devops-lab09
- kubectl get deploy,svc,ingress -n devops-lab09
