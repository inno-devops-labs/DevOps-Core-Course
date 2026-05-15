\# Lab 10 - Helm Package Manager



\## Task 1 — Helm Fundamentals (2 pts)



\### Helm Installation



$ helm version

version.BuildInfo{Version:"v4.1.4", GitCommit:"05fa37973dc9e42b76e1d2883494c87174b6074f", GitTreeState:"clean", GoVersion:"go1.25.9", KubeClientVersion:"v1.35"}



\### Chart Repositories Added



$ helm repo add bitnami https://charts.bitnami.com/bitnami

"bitnami" has been added to your repositories



$ helm repo add prometheus-community https://prometheus-community.github.io/helm-charts

"prometheus-community" has been added to your repositories



$ helm repo update

Update Complete. ⎈Happy Helming!⎈



\### Exploring Public Chart



$ helm search repo bitnami/nginx

bitnami/nginx 24.0.0 1.31.0 NGINX Open Source is a web server



$ helm show chart bitnami/nginx

apiVersion: v2

appVersion: 1.31.0

description: NGINX Open Source web server

version: 24.0.0



\## Task 2 — Create Your Helm Chart (3 pts)



\### Chart Linting



$ helm lint .

==> Linting .

1 chart(s) linted, 0 chart(s) failed



\### Template Verification



$ helm template devops-info-service .

apiVersion: v1

kind: Service

metadata:

&#x20; name: devops-info-service

spec:

&#x20; type: NodePort

&#x20; ports:

&#x20; - name: http

&#x20;   port: 80

&#x20;   targetPort: 5000



\### Dry Run



$ helm install --dry-run --debug test-release .

NAME: test-release

STATUS: pending-install

REVISION: 1



\### Successful Installation



$ helm install devops-info-service . -f values-dev.yaml

NAME: devops-info-service

LAST DEPLOYED: Fri May 15 04:06:21 2026

NAMESPACE: default

STATUS: deployed

REVISION: 1



\### Deployed Resources



$ kubectl get pods

devops-info-service-7fd9b459b8-bvwc6    1/1 Running

devops-info-service-7fd9b459b8-f7xk2    1/1 Running

devops-info-service-7fd9b459b8-g9k7d    1/1 Running



$ kubectl get svc

devops-info-service    NodePort    10.99.131.53    80:30354/TCP

kubernetes             ClusterIP   10.96.0.1       443/TCP



\## Task 3 — Multi-Environment Support (2 pts)



\### Development Environment



$ helm install dev-env . -f values-dev.yaml

NAME: dev-env

STATUS: deployed



$ kubectl get pods -l app.kubernetes.io/instance=dev-env

dev-env-devops-info-service-9979bf999-b2wxs   1/1 Running



\### Production Environment



$ helm upgrade dev-env . -f values-prod.yaml

Release "dev-env" has been upgraded



$ kubectl get pods -l app.kubernetes.io/instance=dev-env

dev-env-devops-info-service-594dc458c-vw7qs   1/1 Running

dev-env-devops-info-service-9979bf999-b2wxs   1/1 Running

dev-env-devops-info-service-9979bf999-bnfk6   1/1 Running

dev-env-devops-info-service-9979bf999-pq2w4   1/1 Running



\### Environment Differences



Dev: 1 replica, CPU 100m/Memory 128Mi limits, NodePort

Prod: 3+ replicas, CPU 500m/Memory 512Mi limits, LoadBalancer



\## Task 4 — Chart Hooks (3 pts)



\### Hook Configuration



Pre-install hook with weight -5, post-install hook with weight 5, deletion policy: hook-succeeded



\### Hook Execution Logs



Pre-install hook for hook-test

Release namespace: default

Chart version: 0.1.0

Pre-install validation completed successfully!



Post-install hook for hook-test

Waiting for service to be ready...

Post-install validation completed!



\### Hook Weights and Order



1\. Pre-install hook (weight: -5) - runs before resources

2\. Resources (Deployment, Service) - created

3\. Post-install hook (weight: 5) - runs after resources ready



\## Task 5 — Documentation (2 pts)



\### Helm Releases



$ helm list

NAME                NAMESPACE   REVISION    STATUS      CHART

devops-info-service default     1           deployed    devops-info-service-0.1.0

dev-env             default     2           deployed    devops-info-service-0.1.0



\### Application Accessibility



$ curl http://localhost:8080/health



{

&#x20; "service": {

&#x20;   "name": "devops-info-service",

&#x20;   "description": "DevOps course info service",

&#x20;   "version": "1.0.0",

&#x20;   "framework": "Flask"

&#x20; },

&#x20; "endpoints": \[

&#x20;   {"path": "/", "method": "GET"},

&#x20;   {"path": "/health", "method": "GET"},

&#x20;   {"path": "/metrics", "method": "GET"}

&#x20; ]

}



\### Operations Commands



helm install myapp ./ -f values-dev.yaml

helm upgrade myapp ./ -f values-prod.yaml

helm rollback myapp 1

helm uninstall myapp

helm list

helm history myapp



\### Chart Structure



k8s/devops-info-service-chart/

├── Chart.yaml

├── values.yaml

├── values-dev.yaml

├── values-prod.yaml

├── templates/

│   ├── \_helpers.tpl

│   ├── deployment.yaml

│   ├── service.yaml

│   ├── NOTES.txt

│   └── hooks/

│       ├── pre-install-job.yaml

│       └── post-install-job.yaml



\## Conclusion



Lab 10 completed successfully with all requirements met: Helm installed, chart created with proper templating, multi-environment support, pre/post-install hooks working, application healthy and accessible.

