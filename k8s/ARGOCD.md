# Lab 13 - GitOps with ArgoCD

## ArgoCD Setup

ArgoCD was installed into the local Minikube cluster with the official Helm chart:

```bash
helm repo add argo https://argoproj.github.io/argo-helm
helm repo update argo
kubectl create namespace argocd
helm upgrade --install argocd argo/argo-cd \
  --namespace argocd \
  --version 7.7.16 \
  --set configs.params.server\.insecure=true
kubectl wait --for=condition=ready pod \
  -l app.kubernetes.io/name=argocd-server \
  -n argocd --timeout=180s
```

Installed components:

```text
NAME                                                READY   STATUS      RESTARTS   AGE
argocd-application-controller-0                     1/1     Running     0          20s
argocd-applicationset-controller-859d967fcd-nv68b   1/1     Running     0          20s
argocd-dex-server-66969bfbff-6hfs5                  1/1     Running     0          20s
argocd-notifications-controller-7695cdb96d-ktsf7    1/1     Running     0          20s
argocd-redis-8566df5cb6-bq8c6                       1/1     Running     0          20s
argocd-repo-server-64ccfdfd57-4gvdc                 1/1     Running     0          20s
argocd-server-75c855d679-574qk                      1/1     Running     0          20s
```

The UI is exposed locally with:

```bash
kubectl port-forward svc/argocd-server -n argocd 8080:80
```

Then open `https://localhost:8080` or `http://localhost:8080` depending on the browser redirect. The username is `admin`; the initial password was retrieved from `argocd-initial-admin-secret`.

The locally installed Homebrew CLI was newer than the server, so I used the matching v2.13.3 CLI binary for verification:

```bash
/tmp/argocd-v2.13.3 --config /tmp/argocd-lab13-config login \
  localhost:8080 --username admin --password '<redacted>' --insecure --grpc-web
```

## Application Configuration

Main manifests are stored in `k8s/argocd/`:

- `application.yaml` deploys a single manual-sync Python app to `default`.
- `application-dev.yaml` deploys dev with automated sync, prune, and self-heal.
- `application-prod.yaml` deploys prod with manual sync.
- `applicationset.yaml` is the bonus replacement that generates dev and prod apps from one template.
- `namespaces.yaml` declares the `dev` and `prod` namespaces.
- `kustomization.yaml` applies the namespace declarations and the ApplicationSet.

All ArgoCD apps use:

```text
repoURL: https://github.com/ellilin/DevOps.git
targetRevision: feature/lab13
path: k8s/python-app
```

The branch was pushed to `origin/feature/lab13` so ArgoCD could fetch the Git source of truth.

## Multi-Environment

Dev uses `values-dev.yaml`:

- namespace: `dev`
- replicas: `1`
- service type: `ClusterIP`
- smaller resources: `50m/64Mi` requests and `100m/128Mi` limits
- log level: `debug`
- sync policy: automated with `prune` and `selfHeal`

Prod uses `values-prod.yaml`:

- namespace: `prod`
- replicas: `2`
- service type: `ClusterIP`
- larger resources: `150m/192Mi` requests and `300m/384Mi` limits
- log level: `info`
- sync policy: manual

Prod remains manual so releases can be reviewed, timed, and rolled back deliberately. Dev auto-syncs because it is the fast feedback environment where drift should be corrected without operator action.

Verification after applying `kubectl apply -k k8s/argocd` and manually syncing prod:

```text
NAME                    CLUSTER                         NAMESPACE  PROJECT  STATUS  HEALTH   SYNCPOLICY  CONDITIONS  REPO                                   PATH            TARGET
argocd/python-app-dev   https://kubernetes.default.svc  dev        default  Synced  Healthy  Auto-Prune  <none>      https://github.com/ellilin/DevOps.git  k8s/python-app  feature/lab13
argocd/python-app-prod  https://kubernetes.default.svc  prod       default  Synced  Healthy  Manual      <none>      https://github.com/ellilin/DevOps.git  k8s/python-app  feature/lab13
```

Kubernetes resources:

```text
dev:  1/1 ready replica, service/python-app-dev-devops-info-python ClusterIP, PVC 100Mi
prod: 2/2 ready replicas, service/python-app-prod-devops-info-python ClusterIP, PVC 1Gi
```

Application access was verified through port-forwarding:

```bash
kubectl port-forward svc/python-app-dev-devops-info-python -n dev 18080:80
curl -sS http://127.0.0.1:18080/health
```

```json
{"status":"healthy","timestamp":"2026-04-26T15:53:43.176060+00:00","uptime_seconds":148}
```

## Self-Healing Evidence

### Manual Scale Drift

At `2026-04-26 18:51 MSK`, I manually changed the dev Deployment to 5 replicas:

```bash
kubectl scale deployment python-app-dev-devops-info-python -n dev --replicas=5
```

ArgoCD self-heal immediately reconciled the Deployment back to the Git-defined state:

```text
kubectl get deployment python-app-dev-devops-info-python -n dev -o jsonpath='{.spec.replicas} {.status.readyReplicas}'
1 1
```

### Pod Deletion

At `2026-04-26 18:52 MSK`, I deleted the dev pod:

```bash
kubectl delete pod -n dev -l app.kubernetes.io/instance=python-app-dev
```

Kubernetes recreated the pod through the Deployment/ReplicaSet controller:

```text
NAME                                                READY   STATUS    RESTARTS   AGE
python-app-dev-devops-info-python-bddb5cb8c-7m4rt   1/1     Running   0          2m19s
```

This is Kubernetes self-healing, not ArgoCD self-healing: the Deployment controller maintains the desired pod count already stored in the cluster.

### Configuration Drift

At `2026-04-26 18:53 MSK`, I manually changed the dev ConfigMap:

```bash
kubectl patch configmap python-app-dev-devops-info-python-env \
  -n dev --type merge -p '{"data":{"LOG_LEVEL":"warn"}}'
```

ArgoCD diff showed live cluster state diverging from Git:

```diff
===== /ConfigMap dev/python-app-dev-devops-info-python-env ======
6c6
<   LOG_LEVEL: warn
---
>   LOG_LEVEL: debug
```

After refresh, self-heal restored the value:

```text
kubectl get configmap python-app-dev-devops-info-python-env -n dev -o jsonpath='{.data.LOG_LEVEL}'
debug
```

ArgoCD self-healing reconciles Kubernetes resources back to Git when a managed field changes. ArgoCD polls Git approximately every 3 minutes by default, can receive webhooks for faster Git change detection, and can also be refreshed or synced manually from the UI/CLI. Self-heal also reacts to detected live-state drift for automated applications.

## Bonus - ApplicationSet

`k8s/argocd/applicationset.yaml` uses a List generator:

```yaml
generators:
  - list:
      elements:
        - env: dev
          namespace: dev
          valuesFile: values-dev.yaml
          replicas: "1"
          autoSync: "true"
        - env: prod
          namespace: prod
          valuesFile: values-prod.yaml
          replicas: "2"
          autoSync: "false"
```

The template creates `python-app-dev` and `python-app-prod` from the same Helm chart. `templatePatch` conditionally adds automated sync only when `autoSync` is `"true"`, so dev self-heals and prod stays manual.

ApplicationSet is better than repeated individual `Application` manifests when the deployment pattern is identical and only environment parameters differ. A List generator is good for a small controlled environment matrix. A Git directory generator is better for monorepos where apps should be discovered from chart directories. Cluster and Matrix generators scale the same pattern across many clusters, tenants, or environment combinations.

Generated applications:

```text
NAME              SYNC STATUS   HEALTH STATUS
python-app-dev    Synced        Healthy
python-app-prod   Synced        Healthy
```

## Screenshot Checklist

The UI is available at `localhost:8080` during the port-forward. Screenshots to include in the submission:

- ArgoCD application grid showing `python-app-dev` and `python-app-prod`.
- `python-app-dev` details showing `Synced`, `Healthy`, and automated sync.
- `python-app-prod` details showing `Synced`, `Healthy`, and manual sync.
- Diff view from the ConfigMap drift test.
