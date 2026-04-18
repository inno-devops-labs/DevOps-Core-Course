# Lab 13 - GitOps with ArgoCD

This submission adds declarative ArgoCD application manifests for the existing Helm chart and sets up separate GitOps flows for `default`, `dev`, and `prod`. The bonus `ApplicationSet` task was intentionally not implemented.

## 1. ArgoCD Setup

### Installation workflow
ArgoCD is installed into its own namespace with the official Helm chart:

```bash
helm repo add argo https://argoproj.github.io/argo-helm
helm repo update
kubectl create namespace argocd
helm upgrade --install argocd argo/argo-cd --namespace argocd --wait --timeout 5m
kubectl get pods -n argocd
```

Expected result:
- `argocd-server`
- `argocd-repo-server`
- `argocd-application-controller`
- `argocd-redis`

### UI access
Use port forwarding to reach the UI locally:

```bash
kubectl port-forward svc/argocd-server -n argocd 8080:443
```

Then open:
- `https://localhost:8080`

Retrieve the initial admin password:

```bash
kubectl -n argocd get secret argocd-initial-admin-secret \
  -o jsonpath="{.data.password}" | base64 -d && echo
```

Login credentials:
- username: `admin`
- password: value from the secret above

### CLI setup
Install the CLI:

```bash
brew install argocd
```

Login from the terminal:

```bash
argocd login localhost:8080 --insecure
argocd app list
```

### Live verification on April 18, 2026
Tooling available in this workspace:

```bash
$ helm version --short
v4.1.3+gc94d381

$ kubectl version --client
Client Version: v1.33.0
Kustomize Version: v5.6.0
```

I started a fresh local cluster and installed ArgoCD successfully:

```bash
$ minikube start --driver=docker
* Done! kubectl is now configured to use "minikube" cluster and "default" namespace by default

$ kubectl create namespace argocd
namespace/argocd created

$ helm upgrade --install argocd argo/argo-cd --namespace argocd --wait --timeout 10m
NAME: argocd
STATUS: deployed
REVISION: 1
```

Initial admin password retrieval worked:

```bash
$ kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath='{.data.password}' | base64 -d
TKejAdYP43L4Q6Si
```

CLI installation and login were verified:

```bash
$ brew install argocd
$ argocd version --client
argocd: v3.3.7+035e855.dirty

$ kubectl port-forward svc/argocd-server -n argocd 8080:80
$ argocd login localhost:8080 --username admin --password '***' --insecure --grpc-web
'admin:login' logged in successfully
Context 'localhost:8080' updated
```

## 2. Application Configuration

### Added files
The ArgoCD manifests live in:

```text
k8s/
├── ARGOCD.md
└── argocd/
    ├── application.yaml
    ├── application-dev.yaml
    ├── application-prod.yaml
    └── namespaces.yaml
```

### Repository source
All ArgoCD applications use this repository as the GitOps source:

- `repoURL`: `https://github.com/ph1larmon1a/DevOps-Core-Course.git`
- `targetRevision`: `lab12`
- `path`: `k8s/python-app`

This means ArgoCD will deploy directly from the most recent pushed remote branch that already contains the Helm chart from Labs 10-12.
If the `lab13` branch is later pushed to GitHub, `targetRevision` can be updated from `lab12` to `lab13`.

### Baseline application
`k8s/argocd/application.yaml` defines a manual-sync ArgoCD application for the `default` namespace.

Key choices:
- `project: default`
- destination cluster: `https://kubernetes.default.svc`
- destination namespace: `default`
- Helm release name: `python-app`
- values file: `values.yaml`
- Helm parameter override: `service.nodePort=30081`
- sync policy: manual

Apply it with:

```bash
kubectl apply -f k8s/argocd/application.yaml
```

The explicit `service.nodePort=30081` override avoids a collision with the dev environment, which uses `30080` from `values-dev.yaml`.

Manual sync:

```bash
argocd app sync python-app
argocd app get python-app
```

## 3. Multi-Environment Deployment

### Namespace separation
Environment namespaces are declared in `k8s/argocd/namespaces.yaml`:

```bash
kubectl apply -f k8s/argocd/namespaces.yaml
kubectl get ns dev prod
```

ArgoCD applications also include `CreateNamespace=true`, so namespace creation is safe even if ArgoCD creates them first.

### Dev application
`k8s/argocd/application-dev.yaml` deploys the chart into the `dev` namespace with:

- Helm release name: `python-app-dev`
- values files:
  - `values.yaml`
  - `values-dev.yaml`
- automated sync enabled
- `prune: true`
- `selfHeal: true`

Apply it with:

```bash
kubectl apply -f k8s/argocd/application-dev.yaml
```

### Prod application
`k8s/argocd/application-prod.yaml` deploys the chart into the `prod` namespace with:

- Helm release name: `python-app-prod`
- values files:
  - `values.yaml`
  - `values-prod.yaml`
- manual sync only

Apply it with:

```bash
kubectl apply -f k8s/argocd/application-prod.yaml
```

### Why the release names differ
Each application uses a distinct Helm release name so resources do not collide:

- `python-app`
- `python-app-dev`
- `python-app-prod`

This is important because the chart names Deployments, Services, ConfigMaps, Secrets, PVCs, and ServiceAccounts from the Helm release name.

### Dev vs Prod differences
Development:
- `replicaCount: 1`
- `NodePort` service on `30080`
- lighter CPU and memory limits
- `APP_ENV=development`
- auto-sync with self-healing and pruning

Production:
- `replicaCount: 3`
- `LoadBalancer` service
- stronger CPU and memory limits
- `APP_ENV=production`
- manual sync for controlled rollout

### Why prod stays manual
Manual sync is safer for production because it:
- gives time for review before release
- supports planned release windows
- reduces accidental deploys from in-progress commits
- makes rollback and change coordination easier

### Live application state
After applying the ArgoCD manifests:

```bash
$ kubectl apply -f k8s/argocd/namespaces.yaml
namespace/dev created
namespace/prod created

$ kubectl apply -f k8s/argocd/application.yaml
$ kubectl apply -f k8s/argocd/application-dev.yaml
$ kubectl apply -f k8s/argocd/application-prod.yaml
```

I used manual sync for `python-app` and `python-app-prod`, while `python-app-dev` synced automatically because of its `automated` policy.

Final app list:

```bash
$ argocd app list
NAME                    CLUSTER                         NAMESPACE  PROJECT  STATUS  HEALTH       SYNCPOLICY  REPO                                                   PATH            TARGET
argocd/python-app       https://kubernetes.default.svc  default    default  Synced  Healthy      Manual      https://github.com/ph1larmon1a/DevOps-Core-Course.git  k8s/python-app  lab12
argocd/python-app-dev   https://kubernetes.default.svc  dev        default  Synced  Healthy      Auto-Prune  https://github.com/ph1larmon1a/DevOps-Core-Course.git  k8s/python-app  lab12
argocd/python-app-prod  https://kubernetes.default.svc  prod       default  Synced  Progressing  Manual      https://github.com/ph1larmon1a/DevOps-Core-Course.git  k8s/python-app  lab12
```

Namespace workloads:

```bash
$ kubectl get pods -n default
python-app-74457f6bb9-8hbxc   1/1 Running
python-app-74457f6bb9-9kfks   1/1 Running
python-app-74457f6bb9-nkvtd   1/1 Running

$ kubectl get pods -n dev
python-app-dev-c9464dd7b-jvdv2   1/1 Running

$ kubectl get pods -n prod
python-app-prod-6ff56744bc-fndzw   1/1 Running
python-app-prod-6ff56744bc-vqh42   1/1 Running
python-app-prod-6ff56744bc-zvslq   1/1 Running
```

Service state:

```bash
$ kubectl get svc -n default
python-app       NodePort      80:30081/TCP

$ kubectl get svc -n dev
python-app-dev   NodePort      80:30080/TCP

$ kubectl get svc -n prod
python-app-prod  LoadBalancer  80:32655/TCP  EXTERNAL-IP <pending>
```

The baseline app uses `30081` because both `values.yaml` and `values-dev.yaml` would otherwise try to claim `30080` on the same cluster.
On Minikube, the production `LoadBalancer` Service stays `Progressing` until a tunnel or equivalent local load balancer mechanism is enabled.

## 4. Sync and Self-Healing Behavior

### Initial deployment workflow
After applying the manifests, verify all applications:

```bash
argocd app list
argocd app get python-app
argocd app get python-app-dev
argocd app get python-app-prod
kubectl get pods -n dev
kubectl get pods -n prod
```

Expected status:
- `python-app`: manual sync
- `python-app-dev`: auto-sync enabled
- `python-app-prod`: manual sync

### GitOps change test
To demonstrate drift from Git:

1. Change the Helm chart, for example update `replicaCount` in `k8s/python-app/values-dev.yaml`.
2. Commit and push the change to the tracked Git branch.
3. Watch ArgoCD mark the application `OutOfSync`.
4. Let dev auto-sync or manually sync prod.

Useful commands:

```bash
git add k8s/python-app/values-dev.yaml
git commit -m "Adjust dev replica count"
git push origin lab12
argocd app get python-app-dev
argocd app get python-app-prod
```

### Self-healing test
For the dev environment:

```bash
kubectl scale deployment python-app-dev -n dev --replicas=5
kubectl get pods -n dev -w
argocd app diff python-app-dev
argocd app get python-app-dev
```

Expected behavior:
- Kubernetes scales the deployment immediately because the API accepted the change.
- ArgoCD detects that the live state differs from Git.
- Because `selfHeal` is enabled, ArgoCD reconciles the deployment back to the Git-defined replica count.

Observed result on April 18, 2026:

```bash
$ date
2026-04-18 18:30:45 MSK

$ kubectl get deploy python-app-dev -n dev -o jsonpath='{.spec.replicas} {.status.availableReplicas}'
1 1

$ kubectl scale deployment python-app-dev -n dev --replicas=5
deployment.apps/python-app-dev scaled
```

Shortly after the manual scale, the deployment showed drift:

```bash
$ kubectl get deploy python-app-dev -n dev -o jsonpath='{.spec.replicas} {.status.availableReplicas}'
5 1
```

Later confirmation after ArgoCD reconciliation:

```bash
$ date
2026-04-18 18:43:30 MSK

$ kubectl get deploy python-app-dev -n dev -o jsonpath='{.spec.replicas} {.status.availableReplicas}'
1 1

$ kubectl get app python-app-dev -n argocd -o jsonpath='{.status.sync.status} {.status.health.status} {.status.operationState.phase} {.status.operationState.message}'
Synced Healthy Succeeded successfully synced (all tasks run)
```

This demonstrates ArgoCD self-healing: the live replica count was changed manually, and ArgoCD restored the Git-defined value.

### Pod deletion test
Delete a dev pod:

```bash
kubectl delete pod -n dev -l app.kubernetes.io/instance=python-app-dev
kubectl get pods -n dev -w
```

Expected behavior:
- Kubernetes recreates the missing pod through the ReplicaSet or Deployment controller.
- This is Kubernetes self-healing, not ArgoCD self-healing.

Observed result:

```bash
$ date
2026-04-18 18:43:52 MSK

$ kubectl delete pod -n dev python-app-dev-c9464dd7b-fvds9
pod "python-app-dev-c9464dd7b-fvds9" deleted

$ kubectl rollout status deployment/python-app-dev -n dev --timeout=180s
deployment "python-app-dev" successfully rolled out

$ date
2026-04-18 18:44:06 MSK

$ kubectl get pods -n dev
python-app-dev-c9464dd7b-fvds9   Terminating
python-app-dev-c9464dd7b-jvdv2   Running
```

This was Kubernetes self-healing through the Deployment and ReplicaSet controllers, not an ArgoCD reconciliation event.

### Configuration drift test
Patch a live resource in dev:

```bash
kubectl label deployment python-app-dev -n dev drift-test=true --overwrite
argocd app diff python-app-dev
argocd app get python-app-dev
```

Expected behavior:
- ArgoCD shows the extra label as drift.
- Auto-sync with `selfHeal` removes the unexpected live change.

Observed result:
- A top-level Deployment label change did not produce a meaningful reconciliation event in this setup.
- A pod-template annotation patch triggered a rollout and the app moved to `Progressing`, but the drift was not automatically removed during the observation window.
- The replica drift test above did self-heal correctly, so auto-sync and reconciliation are functioning, but not every metadata-only change produced the same behavior on this local cluster.

### Sync interval
ArgoCD checks Git on a regular polling interval, commonly every 3 minutes by default. Sync can also happen sooner if:
- a user clicks Sync in the UI
- `argocd app sync` is run
- a webhook is configured from GitHub to ArgoCD

## 5. Validation Performed

### Helm validation
The Helm chart still renders cleanly for all three ArgoCD release names:

```bash
helm lint k8s/python-app
helm template python-app k8s/python-app -f k8s/python-app/values.yaml >/tmp/python-app-default.yaml
helm template python-app-dev k8s/python-app -f k8s/python-app/values.yaml -f k8s/python-app/values-dev.yaml >/tmp/python-app-dev.yaml
helm template python-app-prod k8s/python-app -f k8s/python-app/values.yaml -f k8s/python-app/values-prod.yaml >/tmp/python-app-prod.yaml
```

This verifies:
- the chart remains valid
- the ArgoCD value file combinations render correctly
- separate release names generate separate Kubernetes object names

### Reachability checks
The two NodePort-based environments were reachable through Minikube:

```bash
$ minikube service python-app --url
http://127.0.0.1:52766

$ curl -s http://127.0.0.1:52766/health
{"status":"healthy","timestamp":"2026-04-18T15:30:32.343567+00:00","uptime_seconds":314}

$ minikube service python-app-dev -n dev --url
http://127.0.0.1:52764

$ curl -s http://127.0.0.1:52764/health
{"status":"healthy","timestamp":"2026-04-18T15:30:32.392196+00:00","uptime_seconds":315}
```

### Remaining UI evidence
The only missing evidence from this terminal-only workflow is screenshot capture from the ArgoCD web UI.
