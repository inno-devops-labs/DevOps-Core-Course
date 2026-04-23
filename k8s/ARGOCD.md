# ArgoCD — Lab 13 Documentation

## 1. ArgoCD Setup

ArgoCD was installed into a dedicated `argocd` namespace using the official Helm chart from the `argo` repository.

The installation workflow included:

- adding the Helm repository,
- creating the namespace,
- installing the release,
- verifying pod readiness with `kubectl get pods -n argocd`.

The web UI was accessed through:

```bash
kubectl port-forward svc/argocd-server -n argocd 8080:443
```

The initial administrator password was retrieved from the bootstrap secret:

```bash
kubectl -n argocd get secret argocd-initial-admin-secret   -o jsonpath="{.data.password}" | base64 -d
```

The CLI was then used for local authentication:

```bash
argocd login localhost:8080 --insecure
argocd account get-user-info
```

This verified both UI-level and CLI-level access to the ArgoCD control plane.

---

## 2. Application Configuration

Three ArgoCD Application manifests are used in this repository:

- `k8s/argocd/application.yaml`
- `k8s/argocd/application-dev.yaml`
- `k8s/argocd/application-prod.yaml`

All of them reference the same Git source:

- repository: `https://github.com/Rozanalex/DevOps-Core-Course.git`
- revision: `lab13`
- chart path: `k8s/app-python-chart`

The destination cluster is the in-cluster Kubernetes API endpoint:

- `https://kubernetes.default.svc`

Namespaces differ by environment:

- `default` for the base application,
- `dev` for the development environment,
- `prod` for the production environment.

The Helm chart receives environment-specific values files through the ArgoCD `source.helm.valueFiles` field.

---

## 3. Multi-Environment Model

### Dev
The dev application uses `values-dev.yaml` and enables automated synchronization with:

- `prune: true`
- `selfHeal: true`

This means the development environment is continuously reconciled against the Git source. It is appropriate for fast feedback and frequent changes.

### Prod
The prod application uses `values-prod.yaml` and keeps synchronization manual. This is a safer operational pattern because production changes are applied only after explicit approval or an explicit sync action.

### Practical differences
The environment-specific values differ in:

- replica count,
- resource sizing,
- service exposure strategy,
- probe timings.

This allows the same chart to be reused across multiple environments while preserving different runtime behavior.

---

## 4. Sync Policy Differences and Rationale

### Base application (`python-app`)
The base application in `default` uses manual synchronization. This is useful for demonstrating the initial GitOps workflow step by step.

### Dev application (`python-app-dev`)
The dev application uses automated sync with self-healing. This allows ArgoCD to react automatically when the live state diverges from the Git-defined state.

### Prod application (`python-app-prod`)
The prod application is intentionally left on manual sync. This reflects a common best practice: production rollouts should be intentional, observable, and controlled.

---

## 5. Self-Healing Evidence

### Manual scale test
A manual scale drift was introduced in the dev environment using `kubectl scale deployment ... --replicas=5`. The screenshot set shows the drift attempt and resulting pod transitions.

### Pod deletion test
A running pod in `dev` was deleted manually. Kubernetes recreated a replacement pod automatically. This is Kubernetes self-healing performed by the Deployment/ReplicaSet controller.

### Configuration drift test
A manual label change (`drift=test`) was introduced into the dev deployment, followed by `argocd app diff` and `argocd app get`. The screenshots confirm that drift inspection commands were executed. However, the final screenshot does not explicitly show the label disappearing afterward, so the evidence proves drift injection and inspection more strongly than completed post-heal cleanup.

### Behavior explanation
- **Kubernetes self-healing** keeps the replica count satisfied and recreates failed or deleted pods.
- **ArgoCD self-healing** compares the live cluster state to the Git state and reconciles configuration drift when automated sync and self-heal are enabled.

ArgoCD sync may be triggered manually or by automated policy. In the automated case, Git changes and drift reconciliation are performed according to ArgoCD’s polling and reconciliation behavior.

---

## 6. Screenshots Used

The following screenshots were used as evidence for this lab:

- `task_1_agro_install.png`
- `task_1_argo_cli_login.png`
- `task_1_argo_deploy.png`
- `task_2_sync_python_app.png`
- `task_2_successfully_sync.png`
- `task_2_app_health_check.png`
- `task_3_dev_auto_sync.png`
- `task_3_prod_sync.png`
- `task_4_breake_argo.png`
- `task_4_drift.png`
- `task_4_new_pod.png`

---

## 7. Final Result

The repository now contains a working ArgoCD-based GitOps setup that:

- deploys the application from Git,
- supports separate dev and prod environments,
- uses different sync policies per environment,
- demonstrates both Kubernetes pod recovery and ArgoCD drift-oriented reconciliation behavior.