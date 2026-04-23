# ArgoCD Lab 13


## 1. ArgoCD Setup

### Cluster bootstrap

```bash
$ kubectl config current-context
minikube

$ kubectl get nodes -o wide
NAME       STATUS   ROLES           AGE   VERSION   INTERNAL-IP    EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION    CONTAINER-RUNTIME
minikube   Ready    control-plane   14s   v1.34.0   192.168.49.2   <none>        Ubuntu 22.04.5 LTS   6.17.0-1017-oem   docker://28.4.0
```

### Helm install

```bash
$ helm repo add argo https://argoproj.github.io/argo-helm
"argo" has been added to your repositories

$ helm repo update
...Successfully got an update from the "argo" chart repository
Update Complete. ⎈Happy Helming!⎈

$ kubectl create namespace argocd --dry-run=client -o yaml | kubectl apply -f -
namespace/argocd created

$ helm install argocd argo/argo-cd --namespace argocd --wait --timeout 10m
NAME: argocd
LAST DEPLOYED: Thu Apr 23 22:47:50 2026
NAMESPACE: argocd
STATUS: deployed
REVISION: 1
```

### ArgoCD pods ready

```bash
$ kubectl get pods -n argocd
NAME                                                READY   STATUS    RESTARTS   AGE
argocd-application-controller-0                     1/1     Running   0          70s
argocd-applicationset-controller-7dc6bb5fcb-wdm4q   1/1     Running   0          71s
argocd-dex-server-69b96cbcdd-77pjl                  1/1     Running   0          71s
argocd-notifications-controller-5996578cc4-k4lgv    1/1     Running   0          71s
argocd-redis-65f4b95795-rpd5f                       1/1     Running   0          71s
argocd-repo-server-577479c9bd-xll55                 1/1     Running   0          71s
argocd-server-7dcc98b5cb-vz49j                      1/1     Running   0          70s
```

### UI access and admin password

```bash
$ kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath='{.data.password}' | base64 -d
C27gDsMRUND7DvCU

$ kubectl port-forward svc/argocd-server -n argocd 8080:443
Forwarding from 127.0.0.1:8080 -> 8080

$ curl -k -I https://localhost:8080
HTTP/1.1 200 OK
```

### CLI install and login

Pinned CLI version:

```bash
$ /tmp/argocd-v3.3.8 version --client
argocd: v3.3.8+7ae7d2c
```

Installed into `~/.local/bin`:

```bash
$ argocd version --client
argocd: v3.3.8+7ae7d2c

$ argocd login localhost:8080 --username admin --password '***' --insecure --grpc-web
'admin:login' logged in successfully
Context 'localhost:8080' updated

$ argocd version
argocd: v3.3.8+7ae7d2c
argocd-server: v3.3.8

$ argocd account get-user-info
Logged In: true
Username: admin
Issuer: argocd
Groups:
```

## 2. Application Configuration

### Git source used by ArgoCD

Temporary local Git export:

```bash
$ git rev-parse --abbrev-ref HEAD
lab13

$ git rev-parse HEAD
6dbf4c2c0dfc284666ae1b38a3e788b1377a2bc4

$ git clone --bare /home/lanebo1/DevOps-Core-Course /tmp/devops-core-course.git
Cloning into bare repository '/tmp/devops-core-course.git'...
done.

$ git ls-remote git://127.0.0.1:9418/devops-core-course.git
6dbf4c2c0dfc284666ae1b38a3e788b1377a2bc4	HEAD
6dbf4c2c0dfc284666ae1b38a3e788b1377a2bc4	refs/heads/lab13
6ffd740366219f41ba38b8b60b72c26f9ed1861c	refs/heads/master
```

ArgoCD source values used:

- `repoURL: git://host.minikube.internal/devops-core-course.git`
- `targetRevision: lab13`
- `path: k8s/devops-info-service`

### Base application apply and sync

```bash
$ kubectl apply -f k8s/argocd/application.yaml
application.argoproj.io/devops-info-service created
```

Initial sync result:

```bash
$ argocd app wait devops-info-service --operation --health --sync --timeout 180
Name:               argocd/devops-info-service
Sync Policy:        Manual
Sync Status:        Synced to lab13 (6dbf4c2)
Health Status:      Healthy

Operation:          Sync
Phase:              Succeeded
Message:            successfully synced (no more tasks)
```

Base app access:

```bash
$ MINIKUBE_IP=$(minikube ip); curl -s "http://$MINIKUBE_IP:30080/health"
{"status":"healthy","timestamp":"2026-04-23T19:56:11.155067+00:00","uptime_seconds":27}
```

## 3. Multi-Environment

### Namespaces

```bash
$ kubectl create namespace dev --dry-run=client -o yaml | kubectl apply -f -
namespace/dev created

$ kubectl create namespace prod --dry-run=client -o yaml | kubectl apply -f -
namespace/prod created
```

### Environment-specific behavior

- `dev` uses `values-dev.yaml`
- `prod` uses `values-prod.yaml`
- `dev` auto-sync is enabled with `prune: true` and `selfHeal: true`
- `prod` stays manual sync
- `dev` overrides `service.nodePort=30081` to avoid colliding with the base app's `30080`
- `prod` overrides `service.type=ClusterIP` because minikube did not assign a useful `LoadBalancer` IP in this setup

### Final ArgoCD application state

```bash
$ argocd app list
NAME                             CLUSTER                         NAMESPACE  PROJECT  STATUS  HEALTH   SYNCPOLICY  CONDITIONS  REPO                                                 PATH                     TARGET
argocd/devops-info-service       https://kubernetes.default.svc  default    default  Synced  Healthy  Manual      <none>      git://host.minikube.internal/devops-core-course.git  k8s/devops-info-service  lab13
argocd/devops-info-service-dev   https://kubernetes.default.svc  dev        default  Synced  Healthy  Auto-Prune  <none>      git://host.minikube.internal/devops-core-course.git  k8s/devops-info-service  lab13
argocd/devops-info-service-prod  https://kubernetes.default.svc  prod       default  Synced  Healthy  Manual      <none>      git://host.minikube.internal/devops-core-course.git  k8s/devops-info-service  lab13
```

### Config differences verified

```bash
$ kubectl get deploy -n dev devops-info-service-dev -o jsonpath='dev replicas={.spec.replicas} cpu_req={.spec.template.spec.containers[0].resources.requests.cpu} mem_req={.spec.template.spec.containers[0].resources.requests.memory} cpu_lim={.spec.template.spec.containers[0].resources.limits.cpu} mem_lim={.spec.template.spec.containers[0].resources.limits.memory}{"\n"}'
dev replicas=1 cpu_req=50m mem_req=64Mi cpu_lim=100m mem_lim=128Mi

$ kubectl get deploy -n prod devops-info-service-prod -o jsonpath='prod replicas={.spec.replicas} cpu_req={.spec.template.spec.containers[0].resources.requests.cpu} mem_req={.spec.template.spec.containers[0].resources.requests.memory} cpu_lim={.spec.template.spec.containers[0].resources.limits.cpu} mem_lim={.spec.template.spec.containers[0].resources.limits.memory}{"\n"}'
prod replicas=5 cpu_req=200m mem_req=256Mi cpu_lim=500m mem_lim=512Mi
```

Services:

```bash
$ kubectl get svc -n dev devops-info-service-dev -o wide
NAME                      TYPE       CLUSTER-IP       EXTERNAL-IP   PORT(S)        AGE   SELECTOR
devops-info-service-dev   NodePort   10.111.103.213   <none>        80:30081/TCP   ...   app.kubernetes.io/instance=devops-info-service-dev,app.kubernetes.io/name=devops-info-service

$ kubectl get svc -n prod devops-info-service-prod -o wide
NAME                       TYPE        CLUSTER-IP       EXTERNAL-IP   PORT(S)   AGE   SELECTOR
devops-info-service-prod   ClusterIP   10.105.155.208   <none>        80/TCP    ...   app.kubernetes.io/instance=devops-info-service-prod,app.kubernetes.io/name=devops-info-service
```

## 4. Self-Healing Evidence

### 4.1 Manual scale drift in `dev`

Command:

```bash
$ kubectl scale deployment devops-info-service-dev -n dev --replicas=5
deployment.apps/devops-info-service-dev scaled
```

Observed state:

```text
before 2026-04-23T23:00:08+03:00 appSync=Synced health=Healthy spec=1 ready=1
loop   2026-04-23T23:00:08+03:00 appSync=Synced health=Healthy spec=5 ready=1
loop   2026-04-23T23:00:12+03:00 appSync=Synced health=Healthy spec=1 ready=1
loop   2026-04-23T23:00:15+03:00 appSync=Synced health=Healthy spec=1 ready=1
```

Result: ArgoCD self-healed the replica drift back to the Git-defined value `1` within a few seconds.

### 4.2 Pod deletion in `dev`

Command:

```bash
$ kubectl delete pod -n dev devops-info-service-dev-55b8bb6444-jfb2l --wait=false
pod "devops-info-service-dev-55b8bb6444-jfb2l" deleted from dev namespace
```

Observed state:

```text
before 2026-04-23T23:00:55+03:00 oldPod=devops-info-service-dev-55b8bb6444-jfb2l appSync=Synced health=Healthy
loop   2026-04-23T23:00:55+03:00 pods=devops-info-service-dev-55b8bb6444-jfb2l Running true;devops-info-service-dev-55b8bb6444-vq7lh Pending false; appSync=Synced health=Healthy
loop   2026-04-23T23:00:58+03:00 pods=devops-info-service-dev-55b8bb6444-vq7lh Pending false; appSync=Synced health=Progressing
loop   2026-04-23T23:01:01+03:00 pods=devops-info-service-dev-55b8bb6444-vq7lh Running false; appSync=Synced health=Progressing
loop   2026-04-23T23:01:07+03:00 pods=devops-info-service-dev-55b8bb6444-vq7lh Running true; appSync=Synced health=Healthy
```

Result: Kubernetes recreated the pod because the Deployment still wanted one replica. ArgoCD stayed `Synced` throughout, which is the key distinction.

### 4.3 Configuration drift in `dev`

I first tried a simple label-only metadata change. ArgoCD's apply strategy did not treat that extra label as meaningful drift, so I switched to a managed field that ArgoCD definitely owns: the container image.

Command:

```bash
$ kubectl set image deployment/devops-info-service-dev -n dev devops-info-service=nginx:1.29.1
deployment.apps/devops-info-service-dev image updated
```

Immediate refresh:

```text
Name:               argocd/devops-info-service-dev
Sync Status:        OutOfSync from lab13 (6dbf4c2)
Health Status:      Progressing
...
apps   Deployment   dev  devops-info-service-dev  OutOfSync  Progressing
```

Observed self-heal:

```text
before    2026-04-23T23:03:28+03:00 image=lanebo1/devops-info-service:latest
after-set 2026-04-23T23:03:28+03:00 image=nginx:1.29.1
loop      2026-04-23T23:03:29+03:00 image=lanebo1/devops-info-service:latest appSync=Synced health=Progressing
loop      2026-04-23T23:03:32+03:00 image=lanebo1/devops-info-service:latest appSync=Synced health=Healthy
```

Result: ArgoCD reverted the image back to the Git-defined value almost immediately.

## 5. Sync Behavior Summary

### When ArgoCD syncs

- Base app: only when I trigger sync manually
- Dev app: automatically, because `spec.syncPolicy.automated.prune=true` and `selfHeal=true`
- Prod app: manually only, which is safer for controlled production rollout

### When Kubernetes heals

- Pod deletion is handled by the Deployment/ReplicaSet controllers
- Kubernetes recreates pods to satisfy the current live Deployment spec
- This is different from ArgoCD, which reconciles the live Deployment spec back to Git

### Default timing

Based on the official ArgoCD docs:

- the automatic reconciliation interval is controlled by `timeout.reconciliation`, defaulting to `120s` plus `60s` jitter, so the max default period is 3 minutes
- with `selfHeal: true`, ArgoCD retries against live-cluster drift after the self-heal timeout, which is 5 seconds by default


