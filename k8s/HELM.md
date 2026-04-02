# Lab 10 — Helm report

Chart: [`devops-info-service/`](./devops-info-service/)

## Task 1 — Helm fundamentals

Helm packages Kubernetes manifests as charts with defaults and templates; `install`, `upgrade`, and `rollback` replace hand-edited YAML per release. Shared helpers in `_helpers.tpl` keep names and labels consistent.

```bash
helm version
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update
helm show chart prometheus-community/kube-prometheus-stack --version 65.0.0 | head -30
helm show chart oci://registry-1.docker.io/bitnamicharts/nginx --version 18.0.0 | head -30
helm show chart ./k8s/devops-info-service
```

```text
$ helm version
version.BuildInfo{Version:"v3.17.3", GitCommit:"e4da49785aa6e6ee2b86efd5dd9e43400318262b", GitTreeState:"clean", GoVersion:"go1.24.2"}
```

```text
$ helm show chart ./k8s/devops-info-service
apiVersion: v2
appVersion: 1.0.0
description: Helm chart for DevOps Info Service (Flask) — Lab 10
keywords:
- python
- flask
- kubernetes
maintainers:
- name: Course participant
name: devops-info-service
sources:
- https://github.com/MariaRokkel/DevOps-Core-Course
type: application
version: 0.1.0
```

```text
Pulled: registry-1.docker.io/bitnamicharts/nginx:18.0.0
Digest: sha256:3fad5ba9d0602d46be9eec16b4c95286459355aa91a18d884c66545f94a5bdfa
annotations:
  category: Infrastructure
apiVersion: v2
appVersion: 1.27.0
description: NGINX Open Source is a web server that can be also used as a reverse
  proxy, load balancer, and HTTP cache. Recommended for high-demanding sites due to
  its ability to provide faster content.
home: https://bitnami.com
icon: https://bitnami.com/assets/stacks/nginx/img/nginx-stack-220x234.png
keywords:
- nginx
- http
- web
- www
- reverse proxy
```

## 1. Chart overview

| Path | Role |
|------|------|
| `Chart.yaml` | Chart metadata |
| `values.yaml` | Defaults: image, replicas, NodePort 80→5000, resources, rollout, env, `/health` probes, hook images; `hooks.deleteAfterSuccess: true` adds `hook-succeeded` |
| `values-dev.yaml` | 1 replica, smaller resources, NodePort **30081** (avoids conflict with Lab 9 service on 30080) |
| `values-prod.yaml` | 5 replicas, larger resources, LoadBalancer |
| `values-hooks-keep.yaml` | Sets `hooks.deleteAfterSuccess: false` so hook Jobs remain after success |
| `templates/_helpers.tpl` | `fullname`, labels |
| `templates/deployment.yaml` | Deployment |
| `templates/service.yaml` | Service; `nodePort` only for `NodePort` when set |
| `templates/NOTES.txt` | Post-install notes |
| `templates/hooks/*.yaml` | pre-install and post-install Jobs |

Equivalent workload to Lab 9 [`deployment.yml`](./deployment.yml) and [`service.yml`](./service.yml): container port 5000, probes on `/health`.

## 2. Configuration guide

Key values: `replicaCount`, `image.*`, `service.*`, `resources`, `strategy.rollingUpdate`, `env`, `livenessProbe`, `readinessProbe`, `hooks.*`.

```bash
helm install dev ./k8s/devops-info-service -f k8s/devops-info-service/values-dev.yaml --namespace lab10-dev --create-namespace
helm install prod ./k8s/devops-info-service -f k8s/devops-info-service/values-prod.yaml --namespace lab10-prod --create-namespace
```

| | Dev | Prod |
|---|-----|------|
| Replicas | 1 | 5 |
| Service | NodePort 30081 | LoadBalancer |
| CPU limit | 150m | 500m |
| Memory limit | 192Mi | 512Mi |

## 3. Hook implementation

| | Pre-install | Post-install |
|---|-------------|--------------|
| Kind | Job | Job |
| `helm.sh/hook` | `pre-install` | `post-install` |
| `helm.sh/hook-weight` | `-5` | `5` |
| `helm.sh/hook-delete-policy` | `hook-succeeded` when `hooks.deleteAfterSuccess` is true | same |

Pre-install logs release and namespace. Post-install runs `curl` against `http://<release-fullname>.<namespace>.svc.cluster.local:<service.port>/health` with retries. Hook pod labels exclude the app Service selector so hook pods are not Service endpoints.

## 4. Installation evidence

```text
$ helm lint ./k8s/devops-info-service
==> Linting ./k8s/devops-info-service
[INFO] Chart.yaml: icon is recommended
1 chart(s) linted, 0 chart(s) failed
```

```text
$ kubectl config current-context
minikube

$ kubectl cluster-info
Kubernetes control plane is running at https://127.0.0.1:65035
CoreDNS is running at https://127.0.0.1:65035/api/v1/namespaces/kube-system/services/kube-dns:dns/proxy

$ kubectl get nodes
NAME       STATUS   ROLES           AGE   VERSION
minikube   Ready    control-plane   8d    v1.32.0
```

```bash
helm template dev ./k8s/devops-info-service -f k8s/devops-info-service/values-dev.yaml -n lab10-dev
helm template prod ./k8s/devops-info-service -f k8s/devops-info-service/values-prod.yaml -n lab10-prod
```

```text
$ helm template dev ./k8s/devops-info-service -f k8s/devops-info-service/values-dev.yaml -n lab10-dev 2>&1 | head -42
---
# Source: devops-info-service/templates/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: dev-devops-info-service
  labels:
    helm.sh/chart: devops-info-service-0.1.0
    app.kubernetes.io/name: devops-info-service
    app.kubernetes.io/instance: dev
    app.kubernetes.io/version: "1.0.0"
    app.kubernetes.io/managed-by: Helm
spec:
  replicas: 1
  selector:
    matchLabels:
      app.kubernetes.io/name: devops-info-service
      app.kubernetes.io/instance: dev
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  template:
    metadata:
      labels:
        app.kubernetes.io/name: devops-info-service
        app.kubernetes.io/instance: dev
    spec:
      containers:
        - name: devops-info-service
          image: "mararokkel/devops-info-service:latest"
          imagePullPolicy: Always
          ports:
            - name: http
              containerPort: 5000
              protocol: TCP
```

```text
$ helm install dev ./k8s/devops-info-service \
  -f k8s/devops-info-service/values-dev.yaml \
  --namespace lab10-dev --create-namespace
NAME: dev
LAST DEPLOYED: Thu Apr  2 19:39:50 2026
NAMESPACE: lab10-dev
STATUS: deployed
REVISION: 1
TEST SUITE: None
NOTES:
1. Get the application URL by running these commands:
  export NODE_PORT=$(kubectl get --namespace lab10-dev -o jsonpath="{.spec.ports[0].nodePort}" services dev-devops-info-service)
  export NODE_IP=$(kubectl get nodes --namespace lab10-dev -o jsonpath="{.items[0].status.addresses[0].address}")
  echo http://$NODE_IP:$NODE_PORT/health

Release: dev
Namespace: lab10-dev
```

```text
$ helm list -n lab10-dev
NAME    NAMESPACE       REVISION        UPDATED                                 STATUS        CHART                            APP VERSION
dev     lab10-dev       1               2026-04-02 19:39:50.110994 +0300 MSK    deployed      devops-info-service-0.1.0        1.0.0
```

```text
$ kubectl get all -n lab10-dev
NAME                                           READY   STATUS    RESTARTS   AGE
pod/dev-devops-info-service-84579bd9bb-8mnkp   1/1     Running   0          62s

NAME                              TYPE       CLUSTER-IP       EXTERNAL-IP   PORT(S)        AGE
service/dev-devops-info-service   NodePort   10.103.117.200   <none>        80:30081/TCP   62s

NAME                                      READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/dev-devops-info-service   1/1     1            1           62s

NAME                                                 DESIRED   CURRENT   READY   AGE
replicaset.apps/dev-devops-info-service-84579bd9bb   1         1         1       62s
```

With default `deleteAfterSuccess: true`, hook Jobs are removed after success (`kubectl get jobs` is empty). With `values-hooks-keep.yaml`:

```bash
helm uninstall dev -n lab10-dev
helm install dev ./k8s/devops-info-service \
  -f k8s/devops-info-service/values-dev.yaml \
  -f k8s/devops-info-service/values-hooks-keep.yaml \
  --namespace lab10-dev
kubectl get jobs -n lab10-dev
kubectl describe job dev-devops-info-service-pre-install -n lab10-dev
kubectl describe job dev-devops-info-service-post-install -n lab10-dev
kubectl logs -n lab10-dev job/dev-devops-info-service-pre-install
kubectl logs -n lab10-dev job/dev-devops-info-service-post-install
```

```text
$ helm install dev ./k8s/devops-info-service \
  -f k8s/devops-info-service/values-dev.yaml \
  -f k8s/devops-info-service/values-hooks-keep.yaml \
  --namespace lab10-dev
NAME: dev
LAST DEPLOYED: Thu Apr  2 19:48:28 2026
NAMESPACE: lab10-dev
STATUS: deployed
REVISION: 1
```

```text
$ kubectl get jobs -n lab10-dev
NAME                                   STATUS     COMPLETIONS   DURATION   AGE
dev-devops-info-service-post-install   Complete   1/1           4s         12s
dev-devops-info-service-pre-install    Complete   1/1           3s         15s
```

```text
$ kubectl describe job dev-devops-info-service-pre-install -n lab10-dev
Name:             dev-devops-info-service-pre-install
Namespace:        lab10-dev
Selector:         batch.kubernetes.io/controller-uid=b3df58aa-361f-48fd-8b38-934fa4dbe167
Labels:           app.kubernetes.io/instance=dev
                  app.kubernetes.io/managed-by=Helm
                  app.kubernetes.io/name=devops-info-service
                  app.kubernetes.io/version=1.0.0
                  helm.sh/chart=devops-info-service-0.1.0
Annotations:      helm.sh/hook: pre-install
                  helm.sh/hook-weight: -5
Parallelism:      1
Completions:      1
Completion Mode:  NonIndexed
Suspend:          false
Backoff Limit:    2
Start Time:       Thu, 02 Apr 2026 19:48:28 +0300
Completed At:     Thu, 02 Apr 2026 19:48:31 +0300
Duration:         3s
Pods Statuses:    0 Active (0 Ready) / 1 Succeeded / 0 Failed
Pod Template:
  Labels:  app.kubernetes.io/managed-by=Helm
           batch.kubernetes.io/controller-uid=b3df58aa-361f-48fd-8b38-934fa4dbe167
           batch.kubernetes.io/job-name=dev-devops-info-service-pre-install
           controller-uid=b3df58aa-361f-48fd-8b38-934fa4dbe167
           helm.sh/hook=pre-install
           job-name=dev-devops-info-service-pre-install
  Containers:
   pre-install:
    Image:      busybox:1.36
    Command:
      sh
      -c
      set -e
      echo "pre-install: release=dev ns=lab10-dev"
      echo "pre-install OK"
    Environment:   <none>
    Mounts:        <none>
  Volumes:         <none>
  Node-Selectors:  <none>
  Tolerations:     <none>
Events:
  Type    Reason            Age   From            Message
  ----    ------            ----  ----            -------
  Normal  SuccessfulCreate  22s   job-controller  Created pod: dev-devops-info-service-pre-install-q8xgb
  Normal  Completed         19s   job-controller  Job completed
```

```text
$ kubectl logs -n lab10-dev job/dev-devops-info-service-pre-install
pre-install: release=dev ns=lab10-dev
pre-install OK
```

```text
$ kubectl logs -n lab10-dev job/dev-devops-info-service-post-install
post-install: smoke GET http://dev-devops-info-service.lab10-dev.svc.cluster.local:80/health
{"status":"healthy","timestamp":"2026-04-02T16:48:32.488027+00:00","uptime_seconds":507}
post-install OK
```

Production install (`values-prod.yaml`):

```text
$ helm list -n lab10-prod
NAME    NAMESPACE       REVISION        UPDATED                                 STATUS  CHART                          APP VERSION
prod    lab10-prod      1               2026-04-02 19:51:57.134345 +0300 MSK    failed  devops-info-service-0.1.0      1.0.0
```

```text
$ kubectl get all -n lab10-prod
NAME                                              READY   STATUS      RESTARTS   AGE
pod/prod-devops-info-service-75dff94df9-b77f4     0/1     Running     0          40s
pod/prod-devops-info-service-75dff94df9-lk2j2     0/1     Running     0          40s
pod/prod-devops-info-service-75dff94df9-q5ldt     0/1     Running     0          40s
pod/prod-devops-info-service-75dff94df9-sw95m     1/1     Running     0          40s
pod/prod-devops-info-service-75dff94df9-z45wb     1/1     Running     0          40s
pod/prod-devops-info-service-post-install-t4c9p   0/1     Completed   0          40s

NAME                               TYPE           CLUSTER-IP       EXTERNAL-IP   PORT(S)        AGE
service/prod-devops-info-service   LoadBalancer   10.103.135.218   <pending>     80:31854/TCP   40s

NAME                                       READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/prod-devops-info-service   2/5     5            2           40s

NAME                                                  DESIRED   CURRENT   READY   AGE
replicaset.apps/prod-devops-info-service-75dff94df9   5         5         2       40s

NAME                                              STATUS     COMPLETIONS   DURATION   AGE
job.batch/prod-devops-info-service-post-install   Complete   1/1           30s        40s
```

```text
$ kubectl get svc -n lab10-prod
NAME                       TYPE           CLUSTER-IP       EXTERNAL-IP   PORT(S)        AGE
prod-devops-info-service   LoadBalancer   10.103.135.218   <pending>     80:31854/TCP   47s
```

```bash
kubectl port-forward -n lab10-prod svc/prod-devops-info-service 8080:80
```

```text
$ kubectl rollout status deployment/prod-devops-info-service -n lab10-prod
deployment "prod-devops-info-service" successfully rolled out

$ helm upgrade prod ./k8s/devops-info-service -f k8s/devops-info-service/values-prod.yaml -n lab10-prod
Release "prod" has been upgraded. Happy Helming!
NAME: prod
LAST DEPLOYED: Thu Apr  2 19:54:16 2026
NAMESPACE: lab10-prod
STATUS: deployed
REVISION: 2
TEST SUITE: None
NOTES:
1. Get the application URL by running these commands:
  NOTE: It may take a few minutes for the LoadBalancer IP to be available.
        Watch status: kubectl get svc -w prod-devops-info-service
  export SERVICE_IP=$(kubectl get svc --namespace lab10-prod prod-devops-info-service -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
  echo http://$SERVICE_IP:80/health

Release: prod
Namespace: lab10-prod
```

The following `helm list -A` was captured before `helm upgrade prod`; the upgrade transcript above records `prod` at revision 2 `deployed`.

```text
$ helm list -A
NAME    NAMESPACE       REVISION        UPDATED                                 STATUS        CHART                            APP VERSION
dev     default         1               2026-04-02 19:38:26.499655 +0300 MSK    failed        devops-info-service-0.1.0        1.0.0
dev     lab10-dev       1               2026-04-02 19:48:28.029525 +0300 MSK    deployed      devops-info-service-0.1.0        1.0.0
prod    lab10-prod      1               2026-04-02 19:51:57.134345 +0300 MSK    failed        devops-info-service-0.1.0        1.0.0
```

```bash
helm uninstall dev -n default
```

## 5. Operations

```bash
helm upgrade dev ./k8s/devops-info-service -f k8s/devops-info-service/values-dev.yaml -n lab10-dev
helm history dev -n lab10-dev
helm rollback dev <revision> -n lab10-dev
helm uninstall dev -n lab10-dev
helm uninstall prod -n lab10-prod
```

Dev URL: `minikube service dev-devops-info-service -n lab10-dev --url` then `/health`, or NodePort **30081**.

## 6. Testing and validation

```bash
helm lint ./k8s/devops-info-service
helm template dev ./k8s/devops-info-service -f k8s/devops-info-service/values-dev.yaml -n lab10-dev
helm install dev-dryrun ./k8s/devops-info-service \
  -f k8s/devops-info-service/values-dev.yaml \
  --namespace lab-dryrun --create-namespace \
  --dry-run=client
```

```text
$ helm install dev-dryrun ./k8s/devops-info-service \
  -f k8s/devops-info-service/values-dev.yaml \
  --namespace lab-dryrun --create-namespace \
  --dry-run=client 2>&1 | head -80
NAME: dev-dryrun
LAST DEPLOYED: Thu Apr  2 19:53:17 2026
NAMESPACE: lab-dryrun
STATUS: pending-install
REVISION: 1
TEST SUITE: None
HOOKS:
---
# Source: devops-info-service/templates/hooks/post-install-job.yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: dev-dryrun-devops-info-service-post-install
  annotations:
    helm.sh/hook: post-install
    helm.sh/hook-weight: "5"
    helm.sh/hook-delete-policy: hook-succeeded
  labels:
    helm.sh/chart: devops-info-service-0.1.0
    app.kubernetes.io/name: devops-info-service
    app.kubernetes.io/instance: dev-dryrun
    app.kubernetes.io/version: "1.0.0"
    app.kubernetes.io/managed-by: Helm
spec:
  backoffLimit: 3
  template:
    metadata:
      labels:
        app.kubernetes.io/managed-by: Helm
        helm.sh/hook: post-install
    spec:
      restartPolicy: Never
      containers:
        - name: post-install
          image: "curlimages/curl:8.5.0"
          command:
            - sh
            - -c
            - |
              set -e
              URL="http://dev-dryrun-devops-info-service.lab-dryrun.svc.cluster.local:80/health"
              echo "post-install: smoke GET $URL"
              i=0
              while [ "$i" -lt 30 ]; do
                if curl -fsS --connect-timeout 3 --max-time 10 "$URL"; then
                  echo "post-install OK"
                  exit 0
                fi
                i=$((i + 1))
                echo "post-install: retry $i/30"
                sleep 2
              done
              echo "post-install: health check failed" >&2
              exit 1
```

```text
$ curl -sS -i localhost:8080/health

HTTP/1.1 200 OK
Server: Werkzeug/3.1.7 Python/3.13.12
Date: Thu, 02 Apr 2026 16:52:58 GMT
Content-Type: application/json
Content-Length: 88
Connection: close

{"status":"healthy","timestamp":"2026-04-02T16:52:58.654555+00:00","uptime_seconds":41}
```

```bash
curl -sS -o /dev/null -w "%{http_code}\n" "$(minikube service dev-devops-info-service -n lab10-dev --url)/health"
```
