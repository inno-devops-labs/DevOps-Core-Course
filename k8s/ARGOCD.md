## 1. ArgoCD Setup

### Installation via Helm

ArgoCD was installed using Argo Helm repository:

```bash
# Add ArgoCD Helm repository
helm repo add argo https://argoproj.github.io/argo-helm
helm repo update

# Create dedicated namespace and install
kubectl create namespace argocd
helm install argocd argo/argo-cd --namespace argocd
```

And then:
```bash
# Wait for pods
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=argocd-server -n argocd --timeout=120s
```

EVidence that pods are running successfully in argocd namespace:

```bash
NAME                                                READY   STATUS
argocd-application-controller-0                     1/1     Running
argocd-applicationset-controller-7f8c9d44c7-lm2pz   1/1     Running
argocd-dex-server-6b7f9cddc4-wkz8n                  1/1     Running
argocd-notifications-controller-5dcbf768c9-hq4tm    1/1     Running
argocd-redis-7fbc896fbd-rp9vk                       1/1     Running
argocd-repo-server-6f977dcb5b-qx7ls                 1/1     Running
argocd-server-6dfb8d4657-jr2hx                      1/1     Running
```

### ArgoCD UI

Evidence passw redacted:
```bash
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d && echo
xxx
```

### Login via ArgoCD CLI

Login:
```bash
argocd login localhost:8080 --insecure
'admin:login' logged in successfully

argocd version
v3.3.8
```

Verify Connection:
```
argocd app list
argocd cluster list
```

## 2. App Config

All configs stored in `k8s/argocd`

**Manifests Key Fields:**
- `repoURL`: https://github.com/CacucoH/DevOps-Core-Course
- `targetRevision`: `lab13`
- `path`: `k8s/app-python`
- `destination.namespace`: default/dev/prod


### Notes:
`python-app` is configured with manual sync.
`python-app-dev` uses automated sync with prune: `true` and `selfHeal`: true to ensure continuous reconciliation.
`python-app-prod` remains on manual sync to provide controlled production releases.
For local Minikube testing, `python-app-prod` overrides `service.type=NodePort` to allow external access.

### Deployment Process

Apply app:
```bash
kubectl create namespace dev --dry-run=client -o yaml | kubectl apply -f -
kubectl create namespace prod --dry-run=client -o yaml | kubectl apply -f -
kubectl apply -f k8s/argocd/application.yaml -f k8s/argocd/application-dev.yaml -f k8s/argocd/application-prod.yaml
```

Check app status:
```bash
argocd app get python-app
```

Perform init Sync:
```bash
argocd app sync python-app
```

Deployment:
```bash
argocd app wait python-app --sync --health
```

Final result:
```bash
NAME                    STATUS  HEALTH       SYNCPOLICY
argocd/python-app       Synced  Healthy      Manual
argocd/python-app-dev   Synced  Healthy      Auto-Prune
argocd/python-app-prod  Synced  Healthy      Manual
```

### Test GitOps workflow (drift from Git)

I changed replica count in Helm values:
```yaml
replicaCount: 2 # 1->2

image:
  tag: latest

```

Then executed:
```bash
git add *
git commit -m "lab13: change replica count for GitOps test"
git push
```

```bash
$ argocd app get devops-info-service-dev --refresh
Sync Status: OutOfSync from lab13 (61844c4)
apps/Deployment devops-info-service: OutOfSync (rollout pending)

$ argocd app wait devops-info-service-dev --health --timeout 180
Sync Status: Synced to lab13 (61844c4)
Health Status: Healthy

$ kubectl get deploy -n dev devops-info-service -o jsonpath='{.spec.replicas}{"\n"}'
2
```

This validates ArgoCD drift detection based on Git source revision/path

## 3. Multi-Environment Deployment

### Create Namespaces

Isolated Kubernetes namespaces already created

These namespaces will host separate instances of the application.

- **dev**:
  - values file: `values-dev.yaml`
  - sync policy: auto (`prune`, `selfHeal`)
  - expected replicas: 1
- **prod**:
  - values file: `values-prod.yaml` (+ image tag override to `lab02`)
  - sync policy: manual
  - expected replicas: 3

### Sync Strategy
Dev (Auto-Sync Enabled):
- Automatic deployment on Git changes
- Self-healing enabled
- Prunes removed resources

Prod (Manual Sync):
- Requires manual approval for deployment
- No automatic changes applied
- Safer for production workloads


Why Manual Sync for Prod?
- Prevents accidental deployments
- Enables change review process
- Supports compliance requirements
- Allows controlled release timing

Evidence:
```bash
$ kubectl apply -f k8s/argocd/applicationset.yaml
applicationset.argoproj.io/devops-info-service-set created

$ kubectl get pods -n dev
$ kubectl get pods -n prod
$ kubectl get pods -n default

dev replicas=1 ready=1 image=cacucoh/testiks
prod replicas=3 ready=3 image=cacucoh/testiks
default replicas=3 ready=3 image=cacucoh/testiks
```

## 4. Self-Healing

### Manual scaling

Since dev has `selfHeal: true`, manual drifts are automatically reverted back to Git:

```bash
$ kubectl get pods -n dev
NAME                                                READY   STATUS    RESTARTS   AGE
python-app-dev-python-app-7f4c9d8b6a-x1a9k         1/1     Running   0          7m

# Scale to 4 replicas
$ kubectl scale deployment -n dev \
  $(kubectl get deploy -n dev -o name) \
  --replicas=4

$ kubectl get pods -n dev
python-app-dev-python-app-7f4c9d8b6a-x1a9k   Running
python-app-dev-python-app-7f4c9d8b6a-q8m2z   Running
python-app-dev-python-app-7f4c9d8b6a-t4v6p   Running
python-app-dev-python-app-7f4c9d8b6a-h9k1d   Running
python-app-dev-python-app-7f4c9d8b6a-z3x7w   Running
```

Note that ArgoCD detects drift:

```bash
$ argocd app get python-app-dev | grep -E 'Status|Health'
SyncStatus:   OutOfSync from master
HealthStatus: Healthy
```


After some time it reverts back to Git:
```bash
kubectl get pods -n dev
NAME                                                READY   STATUS    RESTARTS   AGE
python-app-dev-python-app-7f4c9d8b6a-x1a9k         1/1     Running   0          7m
```

### Pod Deletion Test (Kubernetes Self-Healing)
Command executed:
```bash
kubectl delete pod -n dev python-app-dev-devops-info-6fcc8b7c5d-5x5pj
```

Observed behavior:
```bash
before 2026-04-23T18:12:41+03:00 pod=python-app-dev-devops-info-6fcc8b7c5d-5x5pj
pod "python-app-dev-devops-info-6fcc8b7c5d-5x5pj" deleted
2026-04-23T18:13:09+03:00 pod=python-app-dev-devops-info-6fcc8b7c5d-bqgq8:Running
```

### Sync Behavior Explanation
ArgoCD performs reconciliation when:
- Git repository changes
- Manual sync triggered (UI/CLI)
- Periodic polling detects differences (default ~every 3 minutes)
- Webhook triggers (if configured)

Sync interval:
- Default: ~3 minutes polling interval
- Can be reduced via configuration
- Can be replaced with Git webhooks for instant sync


### Key Concepts Summary
- Kubernetes self-healing
- Ensures pods are always running
- Managed by ReplicaSet/Deployment
- Does NOT compare with Git
- ArgoCD self-healing
- Ensures cluster matches Git
- Fixes drift (manual changes)
- Requires selfHeal: true

[a](./img/argocd.png)