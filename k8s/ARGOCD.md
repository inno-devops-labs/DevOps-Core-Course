# Lab 13 Report — GitOps with ArgoCD

## 1. Overview

Lab 13 implements GitOps-based deployment for the existing Helm chart `k8s/devops-info` using ArgoCD.

The work was completed on a fresh local `kind` cluster after recreating the previous unstable control plane:

- cluster: `kind-devops-lab`
- ArgoCD chart: `argo/argo-cd` `7.7.23`
- ArgoCD app version: `v2.13.4`
- Git branch tracked by ArgoCD: `lab13`
- GitOps commits used in this lab:
  - `675eee7` — `Add ArgoCD manifests for lab13`
  - `7e59e95` — `Update dev values for GitOps sync test`

Relevant files created for this lab:

```text
k8s/
├── ARGOCD.md
└── argocd/
    ├── application.yaml
    ├── application-dev.yaml
    ├── application-prod.yaml
    ├── applicationset.yaml
    ├── install-values.yaml
    └── namespaces.yaml
```

## 2. ArgoCD Setup

### 2.1 Installation

ArgoCD was installed with a lightweight values file to fit the single-node `kind` cluster:

```bash
helm install argocd argo/argo-cd \
  --version 7.7.23 \
  --namespace argocd \
  --create-namespace \
  -f k8s/argocd/install-values.yaml \
  --wait --timeout 10m
```

Installation result:

```bash
$ helm install ...
NAME: argocd
NAMESPACE: argocd
STATUS: deployed
REVISION: 1
DESCRIPTION: Install complete
```

### 2.2 Installed components

Healthy ArgoCD control plane after installation:

```bash
$ kubectl get pods -n argocd
NAME                                                READY   STATUS
argocd-application-controller-0                     1/1     Running
argocd-applicationset-controller-77ffc45f46-mttbn   1/1     Running
argocd-redis-68444f7db4-qrn44                       1/1     Running
argocd-repo-server-6c48f968bb-gqc7s                 1/1     Running
argocd-server-d5c7c964b-gp8wj                       1/1     Running
```

### 2.3 UI access method

ArgoCD server service:

```bash
$ kubectl get svc -n argocd
NAME                               TYPE        CLUSTER-IP      PORT(S)
argocd-applicationset-controller   ClusterIP   10.96.43.47     7000/TCP
argocd-redis                       ClusterIP   10.96.104.240   6379/TCP
argocd-repo-server                 ClusterIP   10.96.157.229   8081/TCP
argocd-server                      ClusterIP   10.96.241.44    80/TCP,443/TCP
```

UI access command:

```bash
kubectl port-forward service/argocd-server -n argocd 8080:80
```

Initial admin password was retrieved successfully:

```bash
$ kubectl -n argocd get secret argocd-initial-admin-secret \
    -o jsonpath='{.data.password}' | base64 -d
<redacted>
```

### 2.4 CLI configuration

The local CLI was installed already on the workstation:

```bash
$ argocd version --client
argocd: v3.3.8+7ae7d2c.dirty
```

Because local port-forwarding from the terminal was flaky in this environment, I validated CLI login from inside the `argocd-server` pod:

```bash
$ kubectl exec -n argocd argocd-server-d5c7c964b-gp8wj -- sh -lc \
  "argocd login 127.0.0.1:8080 --plaintext --username admin --password '<redacted>' >/dev/null && \
   echo '[user]' && argocd account get-user-info && \
   echo '[apps]' && argocd app list"

[user]
Logged In: true
Username: admin
Issuer: argocd

[apps]
NAME  CLUSTER  NAMESPACE  PROJECT  STATUS  HEALTH  SYNCPOLICY  CONDITIONS  REPO  PATH  TARGET
```

That confirms the CLI connection and authenticated access.

## 3. Application Configuration

### 3.1 Single-environment application

Task 2 required one manual-sync Application first. I created:

- `k8s/argocd/application.yaml`

Key configuration:

- name: `lab13-devops-info`
- source repo: `https://github.com/sofiakulagina/DevOps-Core-Course.git`
- target revision: `lab13`
- chart path: `k8s/devops-info`
- values file: `values-dev.yaml`
- release name: `lab13-devops-info`
- namespace: `lab13`
- sync policy: manual
- extra Helm parameters:
  - `service.nodePort=30085`
  - `hookJobs.enabled=false`

Application creation:

```bash
$ kubectl apply -f k8s/argocd/application.yaml
application.argoproj.io/lab13-devops-info created
```

Before sync:

```bash
$ argocd app get lab13-devops-info
Sync Policy:        Manual
Sync Status:        OutOfSync from lab13 (675eee7)
Health Status:      Missing
```

Initial manual sync:

```bash
$ argocd app sync lab13-devops-info
Operation:          Sync
Sync Revision:      675eee7eb9d61551154d4ca1233dca3d399e8c9a
Phase:              Succeeded
Message:            successfully synced (all tasks run)
```

Deployed resources in `lab13`:

```bash
$ kubectl get all,cm,secret,pvc -A | grep lab13-devops-info
lab13  pod/lab13-devops-info-787577dddc-zk6m2                  1/1     Running
lab13  service/lab13-devops-info                               NodePort   80:30085/TCP
lab13  deployment.apps/lab13-devops-info                       1/1
lab13  configmap/lab13-devops-info-config
lab13  configmap/lab13-devops-info-env
lab13  secret/lab13-devops-info-secret
lab13  persistentvolumeclaim/lab13-devops-info-data           Bound
```

Application verification:

```bash
$ kubectl wait --for=condition=available deployment/lab13-devops-info -n lab13 --timeout=180s
deployment.apps/lab13-devops-info condition met
```

Service verification:

```bash
$ kubectl get svc -n lab13 lab13-devops-info
NAME                TYPE       CLUSTER-IP      PORT(S)
lab13-devops-info   NodePort   10.96.242.223   80:30085/TCP
```

Health endpoint via port-forward:

```bash
$ kubectl port-forward service/lab13-devops-info -n lab13 5005:80
$ curl -sS http://127.0.0.1:5005/health
{"status":"healthy","timestamp":"2026-04-23T20:26:41.094082+00:00","uptime_seconds":71}
```

## 4. Multi-Environment Deployment

### 4.1 Namespaces

Created namespaces:

```bash
$ kubectl apply -f k8s/argocd/namespaces.yaml
namespace/lab13 created
namespace/dev created
namespace/prod created
```

### 4.2 Dev and prod Applications

Created manifests:

- `k8s/argocd/application-dev.yaml`
- `k8s/argocd/application-prod.yaml`

Configuration differences:

| Setting | Dev | Prod |
|---|---|---|
| Application | `lab13-devops-info-dev` | `lab13-devops-info-prod` |
| Namespace | `dev` | `prod` |
| Values file | `values-dev.yaml` | `values-prod.yaml` |
| Replicas | `2` after Git change | `4` |
| Service type | `NodePort` | `LoadBalancer` |
| NodePort | `30086` | dynamically allocated by Kubernetes |
| Sync policy | automated (`prune`, `selfHeal`) | manual |

Initial status after creating both Applications:

```bash
$ argocd app list
NAME                           STATUS     HEALTH       SYNCPOLICY
lab13-devops-info              Synced     Healthy      Manual
lab13-devops-info-dev          Synced     Progressing  Auto-Prune
lab13-devops-info-prod         OutOfSync  Missing      Manual
```

Manual sync for prod:

```bash
$ argocd app sync lab13-devops-info-prod
Phase:              Succeeded
Message:            successfully synced (all tasks run)
```

Final runtime state:

```bash
$ kubectl get deploy -n dev lab13-devops-info-dev -o jsonpath='{.spec.replicas} {.status.readyReplicas} {.spec.template.spec.containers[0].image}'
2 2 sofiakulagina/devops-info:lab2

$ kubectl get deploy -n prod lab13-devops-info-prod -o jsonpath='{.spec.replicas} {.status.readyReplicas} {.spec.template.spec.containers[0].image}'
4 4 sofiakulagina/devops-info:lab2
```

Service differences:

```bash
$ kubectl get svc -n dev lab13-devops-info-dev
NAME                    TYPE       CLUSTER-IP      PORT(S)
lab13-devops-info-dev   NodePort   10.96.171.159   80:30086/TCP

$ kubectl get svc -n prod lab13-devops-info-prod
NAME                     TYPE           CLUSTER-IP     EXTERNAL-IP   PORT(S)
lab13-devops-info-prod   LoadBalancer   10.96.71.203   <pending>     80:30264/TCP
```

Important note about prod health on `kind`:

- the prod Deployment itself reached `4/4` ready replicas
- the prod Service is `LoadBalancer`
- on local `kind` there is no cloud load balancer controller, so `EXTERNAL-IP` remains `<pending>`
- because of that, ArgoCD keeps the prod app in `Progressing` even though the Deployment is available

Current Application status table:

```bash
$ kubectl get applications -n argocd
NAME                     SYNC STATUS   HEALTH STATUS
lab13-devops-info        Synced        Healthy
lab13-devops-info-dev    Synced        Healthy
lab13-devops-info-prod   Synced        Progressing
```

### 4.3 Why dev is auto-sync and prod is manual

This split matches common deployment practice:

- `dev` auto-sync allows fast feedback on every commit
- `selfHeal` and `prune` keep the environment aligned with Git continuously
- `prod` stays manual so deployment timing remains controlled
- manual prod sync allows review, scheduling, and rollback planning before rollout

## 5. GitOps Workflow Validation

To validate GitOps drift detection, I changed `k8s/devops-info/values-dev.yaml` and pushed it to `origin/lab13`.

Change commit:

```bash
$ git log --oneline -2
7e59e95 Update dev values for GitOps sync test
675eee7 Add ArgoCD manifests for lab13
```

Changed fields:

- `replicaCount: 1 -> 2`
- `APP_REVISION: dev-v1 -> dev-v2`

After explicit refresh, ArgoCD detected the new Git revision:

```bash
$ argocd app get lab13-devops-info --refresh
Sync Policy:        Manual
Sync Status:        OutOfSync from lab13 (7e59e95)
Health Status:      Healthy

$ argocd app get lab13-devops-info-dev --refresh
Sync Policy:        Automated (Prune)
Sync Status:        OutOfSync from lab13 (7e59e95)
Health Status:      Healthy
```

Observed behavior:

- the single-environment app `lab13-devops-info` stayed `OutOfSync` until I manually ran `argocd app sync`
- the dev app auto-synced to the new commit and reached `2/2` replicas automatically

Manual sync of the single app after the Git change:

```bash
$ argocd app sync lab13-devops-info
Sync Revision:      7e59e9528658ee4dc063be94c9e5567dd4ebe217
Phase:              Succeeded
Message:            successfully synced (all tasks run)
```

Final dev rollout after auto-sync:

```bash
$ kubectl get deploy -n dev lab13-devops-info-dev -o jsonpath='{.spec.replicas} {.status.readyReplicas}'
2 2
```

## 6. Self-Healing Evidence

### 6.1 Manual scale drift in dev

Baseline before test:

```bash
$ date '+%Y-%m-%d %H:%M:%S %Z'
2026-04-23 23:32:24 MSK

$ kubectl get deploy -n dev lab13-devops-info-dev -o jsonpath='{.spec.replicas} {.status.readyReplicas}'
2 2
```

Manual drift introduced:

```bash
$ date '+%Y-%m-%d %H:%M:%S %Z'
2026-04-23 23:32:37 MSK

$ kubectl scale deployment lab13-devops-info-dev -n dev --replicas=5
deployment.apps/lab13-devops-info-dev scaled
```

Live watch of the deployment showed the transition and the revert:

```bash
$ kubectl get deploy -n dev lab13-devops-info-dev -w
lab13-devops-info-dev   2/5     2            2
lab13-devops-info-dev   2/5     5            2
lab13-devops-info-dev   2/2     5            2
lab13-devops-info-dev   2/2     2            2
```

Interpretation:

- the manual scale changed the Deployment spec from the Git-defined `2` to `5`
- ArgoCD detected the drift and restored the spec back to `2`
- that is ArgoCD self-healing, not Kubernetes ReplicaSet behavior

State after self-heal:

```bash
$ date '+%Y-%m-%d %H:%M:%S %Z'
2026-04-23 23:33:46 MSK

$ argocd app get lab13-devops-info-dev --refresh
Sync Status:        Synced to lab13 (7e59e95)
Health Status:      Healthy
```

### 6.2 Pod deletion test

Baseline pod names:

```bash
$ kubectl get pods -n dev
lab13-devops-info-dev-64b7856976-dm69q
lab13-devops-info-dev-64b7856976-tslt5
```

Deletion time:

```bash
$ date '+%Y-%m-%d %H:%M:%S %Z'
2026-04-23 23:34:00 MSK
```

Deleted one pod:

```bash
$ kubectl delete pod -n dev lab13-devops-info-dev-64b7856976-dm69q
pod "lab13-devops-info-dev-64b7856976-dm69q" deleted
```

Observed behavior:

```bash
$ kubectl get pods -n dev -w
lab13-devops-info-dev-64b7856976-dm69q   1/1     Terminating
lab13-devops-info-dev-64b7856976-xgx2v   0/1     Pending
lab13-devops-info-dev-64b7856976-xgx2v   0/1     ContainerCreating
lab13-devops-info-dev-64b7856976-xgx2v   0/1     Running
lab13-devops-info-dev-64b7856976-xgx2v   1/1     Running
```

Interpretation:

- this is Kubernetes self-healing
- the ReplicaSet/Deployment controller noticed the missing pod and created a replacement
- ArgoCD was not required here because the desired object configuration in Git did not change

### 6.3 Configuration drift test

To demonstrate drift on a clearly managed field, I changed the Deployment image in `dev`.

Change time:

```bash
$ date '+%Y-%m-%d %H:%M:%S %Z'
2026-04-23 23:37:03 MSK
```

Manual image drift:

```bash
$ kubectl set image deployment/lab13-devops-info-dev -n dev devops-info=nginx:1.27
deployment.apps/lab13-devops-info-dev image updated
```

Live watch of the image field:

```bash
$ kubectl get deploy -n dev lab13-devops-info-dev \
    -o 'custom-columns=NAME:.metadata.name,IMAGE:.spec.template.spec.containers[0].image' -w

lab13-devops-info-dev   sofiakulagina/devops-info:lab2
lab13-devops-info-dev   nginx:1.27
lab13-devops-info-dev   nginx:1.27
lab13-devops-info-dev   sofiakulagina/devops-info:lab2
lab13-devops-info-dev   sofiakulagina/devops-info:lab2
```

Final state:

```bash
$ date '+%Y-%m-%d %H:%M:%S %Z'
2026-04-23 23:37:27 MSK

$ kubectl get deploy -n dev lab13-devops-info-dev \
    -o jsonpath='{.spec.template.spec.containers[0].image} {.spec.replicas} {.status.readyReplicas}'
sofiakulagina/devops-info:lab2 2 2
```

This is the clearest proof of ArgoCD self-healing:

- a tracked field in the live cluster was changed manually
- ArgoCD restored it back to the Git-defined image

## 7. Sync Behavior Summary

### When Kubernetes heals

Kubernetes heals runtime failures when the declared workload object still matches the desired spec:

- pod deletion
- container restart
- node rescheduling

Example from this lab:

- deleting a dev pod caused the ReplicaSet to create a new pod automatically

### When ArgoCD heals

ArgoCD heals configuration drift between the live cluster and Git:

- manual scale to `5` reverted to Git-defined `2`
- manual image change to `nginx:1.27` reverted to `sofiakulagina/devops-info:lab2`

### What triggers sync

In this lab, sync occurred from:

- manual `argocd app sync` for the single app and prod app
- automated sync for the dev app after the Git commit
- self-heal on the dev app after manual drift

### Reconciliation interval

From `install-values.yaml` / ArgoCD defaults used in this lab:

- `timeout.reconciliation: 120s`
- `timeout.reconciliation.jitter: 60s`

So Git polling is approximately every 2 minutes plus jitter, unless a manual refresh/sync is triggered earlier.

## 8. Bonus — ApplicationSet

### 8.1 Implemented manifest

Bonus manifest:

- `k8s/argocd/applicationset.yaml`

It uses a List generator with two parameter sets:

- `dev`
- `prod`

Parameters include:

- environment name
- destination namespace
- values file
- release name
- node port override for dev
- whether auto-sync should be enabled

### 8.2 Replacement of individual Applications

After validating the regular Task 3 workflow with individual `Application` resources, I replaced the dev/prod Application CRs with the ApplicationSet-generated equivalents:

```bash
$ kubectl delete application -n argocd lab13-devops-info-dev lab13-devops-info-prod
$ kubectl apply -f k8s/argocd/applicationset.yaml
applicationset.argoproj.io/lab13-devops-info created
```

Live ApplicationSet status:

```bash
$ kubectl get applicationset -n argocd
NAME                AGE
lab13-devops-info   3m10s
```

Generated resources from ApplicationSet status:

```yaml
status:
  resources:
    - kind: Application
      name: lab13-devops-info-dev
    - kind: Application
      name: lab13-devops-info-prod
```

ArgoCD application list after the swap:

```bash
$ argocd app list
NAME                           STATUS  HEALTH       SYNCPOLICY
lab13-devops-info              Synced  Healthy      Manual
lab13-devops-info-dev          Synced  Healthy      Auto-Prune
lab13-devops-info-prod         Synced  Progressing  Manual
```

### 8.3 Why ApplicationSet is useful

Benefits compared to individual `Application` manifests:

- one template generates multiple environment-specific applications
- less duplication across repo URL, chart path, and common Helm parameters
- easier scaling when adding more environments or clusters
- consistent naming and sync-policy patterns

When to use it:

- multiple environments for the same app
- mono-repo with repeated app structure
- multi-cluster rollouts with cluster-specific parameters

## 9. Final Status

Final state of the lab:

```bash
$ kubectl get applications -n argocd
NAME                     SYNC STATUS   HEALTH STATUS
lab13-devops-info        Synced        Healthy
lab13-devops-info-dev    Synced        Healthy
lab13-devops-info-prod   Synced        Progressing
```

Interpretation:

- `lab13-devops-info`: fully healthy manual app
- `lab13-devops-info-dev`: fully healthy automated app with confirmed self-heal
- `lab13-devops-info-prod`: synced and deployed, but health remains `Progressing` because `LoadBalancer` external IP is pending in local `kind`

This means all core GitOps tasks were completed successfully, and the bonus ApplicationSet pattern was implemented and applied.

## 10. Screenshots To Add Manually

The lab explicitly requires screenshots from the ArgoCD UI. These still need to be captured manually in the browser:

1. ArgoCD UI overview showing:
   - `lab13-devops-info`
   - `lab13-devops-info-dev`
   - `lab13-devops-info-prod`
2. Application details page for `lab13-devops-info-dev`
3. Sync status view showing:
   - manual app behavior
   - auto-sync dev behavior
   - prod application
4. Bonus screenshot showing the ApplicationSet-generated apps

Suggested access command before taking screenshots:

```bash
kubectl port-forward service/argocd-server -n argocd 8080:80
```

Then open:

```text
http://127.0.0.1:8080
```

Login:

- username: `admin`
- password: retrieve with:

```bash
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath='{.data.password}' | base64 -d
```
