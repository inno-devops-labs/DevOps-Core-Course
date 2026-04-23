# Lab 13 - GitOps with ArgoCD

## What I built

I added a dedicated ArgoCD bundle under `k8s/argocd/` and kept the deployment flow fully declarative:

- `application.yaml` deploys a single manual-sync release into `lab13`
- `application-dev.yaml` deploys the dev environment with auto-sync, prune, and self-heal
- `application-prod.yaml` deploys the prod environment with manual sync
- `applicationset.yaml` provides the bonus List generator setup for dev and prod from one template
- `namespaces.yaml` declares the target namespaces
- `values.yaml` contains the Helm values I use for installing ArgoCD itself

All ArgoCD manifests in the repository target the remote `lab13` branch:

```yaml
targetRevision: lab13
```

That means the manifests are ready for the final GitOps flow, but the remote branch has to be pushed before ArgoCD can actually fetch and sync this exact state.

## Files added

```text
k8s/
├── ARGOCD.md
└── argocd/
    ├── application.yaml
    ├── application-dev.yaml
    ├── application-prod.yaml
    ├── applicationset.yaml
    ├── namespaces.yaml
    └── values.yaml
```

## ArgoCD setup

### Install ArgoCD with Helm

I used the official Helm chart:

```bash
helm repo add argo https://argoproj.github.io/argo-helm
helm repo update
kubectl create namespace argocd
helm install argocd argo/argo-cd \
  -n argocd \
  -f k8s/argocd/values.yaml \
  --wait --timeout 300s
```

The only custom value I set is:

- `server.insecure: true`

That makes local port-forwarding and CLI login easier in a lab cluster because TLS verification is no longer in the way.

### Accessing the UI

```bash
kubectl port-forward svc/argocd-server -n argocd 8080:80
```

ArgoCD UI:

- URL: `http://127.0.0.1:8080`
- Username: `admin`

Retrieve the initial password:

```bash
kubectl -n argocd get secret argocd-initial-admin-secret \
  -o jsonpath="{.data.password}" | base64 -d && echo
```

### CLI configuration

Install the CLI on macOS:

```bash
brew install argocd
```

Login:

```bash
argocd login 127.0.0.1:8080 \
  --username admin \
  --password '<password>' \
  --port-forward \
  --port-forward-namespace argocd \
  --plaintext
```

Basic verification:

```bash
argocd version
argocd app list
```

## Application configuration

### Single application

`k8s/argocd/application.yaml` deploys the Helm chart manually into namespace `lab13`.

Important settings:

- `repoURL`: `https://github.com/hikariatama/DevOps-Core-Course.git`
- `targetRevision`: `lab13`
- `path`: `k8s/devops-info-service`
- `helm.releaseName`: `devops-info-service`
- `helm.valueFiles`: `values.yaml`
- `helm.parameters.service.nodePort=30081`
- `destination.namespace`: `lab13`

I override the NodePort to `30081` in the single-app manifest so it can coexist with the dev environment, which still uses `30080`.

Apply it:

```bash
kubectl apply -f k8s/argocd/application.yaml
```

Manual sync:

```bash
argocd app sync devops-info-service
argocd app get devops-info-service
```

### Multi-environment applications

`application-dev.yaml` and `application-prod.yaml` use the same chart but different Helm values files:

- dev: `values.yaml` + `values-dev.yaml`
- prod: `values.yaml` + `values-prod.yaml`

Apply them:

```bash
kubectl apply -f k8s/argocd/application-dev.yaml
kubectl apply -f k8s/argocd/application-prod.yaml
```

### Namespace declarations

I added a small namespace bundle:

```bash
kubectl apply -f k8s/argocd/namespaces.yaml
```

ArgoCD can also create namespaces automatically because each Application includes:

```yaml
syncOptions:
  - CreateNamespace=true
```

I kept the namespace manifests anyway because they make the target layout explicit in Git.

## Dev vs prod

### Configuration differences

The environments are separated by namespace and Helm values:

| Environment | Namespace | Values file | Replicas | Service type | Sync mode |
| --- | --- | --- | --- | --- | --- |
| Manual app | `lab13` | `values.yaml` | 3 | `NodePort` | Manual |
| Dev | `dev` | `values-dev.yaml` | 1 | `NodePort` | Auto |
| Prod | `prod` | `values-prod.yaml` | 3 | `LoadBalancer` | Manual |

### Why dev is auto-sync

Dev is the place where I want fast feedback and automatic reconciliation:

- changes in Git deploy automatically
- removed resources get pruned
- manual drift gets reverted automatically

### Why prod is manual

Prod stays manual because it matches the safer release model:

- a person explicitly decides when to deploy
- change review can happen before sync
- rollback planning stays deliberate

## Bonus: ApplicationSet

`k8s/argocd/applicationset.yaml` uses the List generator and produces two Applications from one template:

- `devops-info-service-dev`
- `devops-info-service-prod`

Each generated app receives:

- the target namespace
- the environment-specific values file
- the final `targetRevision: lab13`

I used `goTemplate: true` and `templatePatch` so only the dev application gets the automated sync policy.

Apply the bonus manifest:

```bash
kubectl apply -f k8s/argocd/applicationset.yaml
```

This ApplicationSet is the cleaner long-term option because it removes duplicated Application boilerplate while preserving different environment behavior.

One practical detail: if the ApplicationSet is applied after `application-dev.yaml` and `application-prod.yaml`, it adopts those environment apps because the generated names are identical. That is what happened in my verification cluster, and it is fine as long as the manifests stay consistent.

## Live verification status

I verified the setup on a fresh Docker-backed `kind` cluster named `lab13` after the remote `lab13` branch became available.

Remote branch used by ArgoCD:

```text
$ git ls-remote origin refs/heads/lab13
64999fc7930821a5413e0130285e0840ea6b1ad4	refs/heads/lab13
```

Final ArgoCD state:

```text
$ argocd app list --port-forward --port-forward-namespace argocd --plaintext
NAME                             CLUSTER                         NAMESPACE  PROJECT  STATUS  HEALTH       SYNCPOLICY
argocd/devops-info-service       https://kubernetes.default.svc  lab13      default  Synced  Healthy      Manual
argocd/devops-info-service-dev   https://kubernetes.default.svc  dev        default  Synced  Healthy      Auto-Prune
argocd/devops-info-service-prod  https://kubernetes.default.svc  prod       default  Synced  Progressing  Manual
```

What that means:

- the single manual app in `lab13` synced successfully and became healthy
- the dev app auto-synced successfully and became healthy
- the prod app synced successfully, but health remains `Progressing` on `kind` because `values-prod.yaml` uses `LoadBalancer` and `kind` does not provide an external load balancer IP by default

Prod service evidence:

```text
$ kubectl get svc -n prod devops-info-service-prod -o wide
NAME                       TYPE           CLUSTER-IP    EXTERNAL-IP   PORT(S)        AGE
devops-info-service-prod   LoadBalancer   10.96.3.110   <pending>     80:32452/TCP   ...
```

That is a cluster-environment limitation, not an ArgoCD sync failure. The prod Deployment and PVC were created correctly.

## Verification commands

### Create a fresh local cluster

I used a new Docker-backed `kind` cluster:

```bash
kind create cluster --name lab13
```

### Build and load the application image

The Helm chart uses `devops-info-service-python:lab12`, so I built and loaded that image into the cluster:

```bash
docker build -t devops-info-service-python:lab12 app_python
kind load docker-image devops-info-service-python:lab12 --name lab13
```

### Install ArgoCD

```bash
helm repo add argo https://argoproj.github.io/argo-helm
helm repo update
kubectl create namespace argocd
helm install argocd argo/argo-cd \
  -n argocd \
  -f k8s/argocd/values.yaml \
  --wait --timeout 300s
```

### Apply the applications

Apply the final repository manifests after the remote `lab13` branch exists:

```bash
kubectl apply -f k8s/argocd/namespaces.yaml
kubectl apply -f k8s/argocd/application.yaml
kubectl apply -f k8s/argocd/application-dev.yaml
kubectl apply -f k8s/argocd/application-prod.yaml
```

Manual sync commands I used:

```bash
argocd app sync devops-info-service --port-forward --port-forward-namespace argocd --plaintext
argocd app sync devops-info-service-prod --port-forward --port-forward-namespace argocd --plaintext
```

Observed single-app sync result:

```text
Sync Status:        Synced to lab13 (64999fc)
Health Status:      Healthy
Phase:              Succeeded
Duration:           21s
Message:            successfully synced (no more tasks)
```

Observed dev auto-sync result:

```text
Sync Status:        Synced to lab13 (64999fc)
Health Status:      Healthy
Phase:              Succeeded
Duration:           15s
Message:            successfully synced (no more tasks)
```

## Self-healing behavior

### Manual scale test

Dev uses:

```yaml
syncPolicy:
  automated:
    prune: true
    selfHeal: true
```

I ran the test against the dev app after it was healthy:

```bash
kubectl scale deployment devops-info-service-dev -n dev --replicas=5
kubectl get deployment devops-info-service-dev -n dev -w
argocd app get devops-info-service-dev
```

Observed behavior:

- Kubernetes accepted the manual scale to `5`
- the Deployment events immediately showed scale up followed by ArgoCD-driven scale down back to `1`
- by the time I sampled the Deployment again, the spec was already back at the Git value

Relevant event lines:

```text
Scaled up replica set devops-info-service-dev-5f658f5c69 from 1 to 5
Scaled down replica set devops-info-service-dev-5f658f5c69 from 5 to 1
```

### Pod deletion test

```bash
kubectl delete pod -n dev -l app.kubernetes.io/instance=devops-info-service-dev
kubectl get pods -n dev -w
```

Observed behavior:

- the original pod was deleted
- Kubernetes immediately created a replacement pod with a new name
- this happened through the Deployment and ReplicaSet controller, not because ArgoCD performed a sync

Observed transition:

```text
deleted pod: devops-info-service-dev-5f658f5c69-26mlg
new pod:     devops-info-service-dev-5f658f5c69-892xn
```

### Configuration drift test

```bash
kubectl set image deployment/devops-info-service-dev -n dev \
  devops-info-service=devops-info-service-python:lab12-bad
kubectl get deployment devops-info-service-dev -n dev \
  -o jsonpath='{.spec.template.spec.containers[0].image}{"\n"}'
sleep 20
kubectl get deployment devops-info-service-dev -n dev \
  -o jsonpath='{.spec.template.spec.containers[0].image}{"\n"}'
```

Observed result:

- immediately after the manual change, the Deployment spec showed `devops-info-service-python:lab12-bad`
- about 20 seconds later, the image was back to `devops-info-service-python:lab12`
- this is the clearest proof from my run that ArgoCD self-healed a real configuration drift back to Git state

Output:

```text
devops-info-service-python:lab12
deployment.apps/devops-info-service-dev image updated
devops-info-service-python:lab12-bad
devops-info-service-python:lab12
```

## Kubernetes healing vs ArgoCD healing

These two behaviors are different:

- Kubernetes self-healing recreates failed or deleted Pods to satisfy the Deployment or ReplicaSet
- ArgoCD self-healing reverts live resource configuration back to the declarative state stored in Git

Examples:

- deleting a Pod is handled by Kubernetes
- changing the replica count or deployment image is reconciled by ArgoCD when self-heal is enabled

## When ArgoCD syncs

ArgoCD sync happens when:

- you trigger a manual sync
- auto-sync is enabled and Git changes are detected
- auto-sync with self-heal is enabled and cluster drift is detected

The normal polling interval is about 3 minutes by default, though webhooks can make Git change detection effectively immediate.
