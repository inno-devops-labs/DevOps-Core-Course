# Lab 13 - GitOps with ArgoCD

Prepared on `2026-04-23`.

This file records the actual evidence collected for Lab 13 from:

- repository manifests in [`k8s/argocd/`](/home/eugene/IU/DevOps/DevOps-Core-Course/k8s/argocd)
- local Helm validation
- a freshly recreated `kind` cluster named `lab13`

Tools used:

- `helm v4.1.3`
- `kubectl v1.35.3`
- `kind v0.31.0`
- `argocd v2.13.3`

Cluster access method used for all live checks:

```bash
docker exec lab13-control-plane kubectl --kubeconfig=/etc/kubernetes/admin.conf ...
```

I used the in-container kubeconfig because the host-side `kind-lab13` endpoint was returning `EOF`, while the control-plane container itself remained accessible.

## 1. Implemented Repository Artifacts

Created files:

- [`k8s/argocd/application.yaml`](/home/eugene/IU/DevOps/DevOps-Core-Course/k8s/argocd/application.yaml)
- [`k8s/argocd/application-dev.yaml`](/home/eugene/IU/DevOps/DevOps-Core-Course/k8s/argocd/application-dev.yaml)
- [`k8s/argocd/application-prod.yaml`](/home/eugene/IU/DevOps/DevOps-Core-Course/k8s/argocd/application-prod.yaml)
- [`k8s/argocd/applicationset.yaml`](/home/eugene/IU/DevOps/DevOps-Core-Course/k8s/argocd/applicationset.yaml)

GitOps source configured in all manifests:

- repository: `https://github.com/ebortsov/DevOps-Core-Course.git`
- target revision: `lab13`
- path: `k8s/devops-info`

Application mapping implemented in the repo:

| Object | Destination namespace | Helm release | Values | Sync mode |
|---|---|---|---|---|
| `devops-info` | `devops-gitops` | `devops-info` | `values.yaml` | manual |
| `devops-info-dev` | `dev` | `devops-info-dev` | `values.yaml` + `values-dev.yaml` | automated |
| `devops-info-prod` | `prod` | `devops-info-prod` | `values.yaml` + `values-prod.yaml` | manual |

`applicationset.yaml` generates `dev` and `prod` environments from one template and enables automated sync only for `dev`.

## 2. Local Helm Validation

The ArgoCD target chart renders correctly for all declared environments.

```bash
$ helm lint k8s/devops-info
==> Linting k8s/devops-info
[INFO] Chart.yaml: icon is recommended

1 chart(s) linted, 0 chart(s) failed
```

```bash
helm template devops-info k8s/devops-info \
  -f k8s/devops-info/values.yaml >/dev/null

helm template devops-info-dev k8s/devops-info \
  -f k8s/devops-info/values.yaml \
  -f k8s/devops-info/values-dev.yaml >/dev/null

helm template devops-info-prod k8s/devops-info \
  -f k8s/devops-info/values.yaml \
  -f k8s/devops-info/values-prod.yaml >/dev/null
```

Confirmed value layering:

- `dev` renders as `NodePort`, `1` replica, debug-oriented config
- `prod` renders as `LoadBalancer`, `4` replicas, higher resources, `SERVICE_VERSION=1.0.1`

Published application image now configured in the chart:

- repository: `ebortsov/devops-info`
- tag: `1.0.0`

Docker Hub push evidence:

```bash
$ docker push ebortsov/devops-info:1.0.0
1.0.0: digest: sha256:f0718a5fc1d94e7567881f434b07603e8b885f22aaa4d4986e41d407d3fd479d size: 2200
```

## 3. Fresh Cluster Recreation

I recreated the `lab13` cluster from scratch before collecting the final evidence:

```bash
$ kind delete cluster --name lab13
Deleting cluster "lab13" ...
Deleted nodes: ["lab13-control-plane"]

$ kind create cluster --name lab13
Creating cluster "lab13" ...
...
Set kubectl context to "kind-lab13"
```

Fresh cluster node evidence:

```bash
$ docker exec lab13-control-plane kubectl --kubeconfig=/etc/kubernetes/admin.conf get nodes -o wide
NAME                  STATUS   ROLES           AGE   VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE                         KERNEL-VERSION      CONTAINER-RUNTIME
lab13-control-plane   Ready    control-plane   58s   v1.35.0   172.18.0.3    <none>        Debian GNU/Linux 12 (bookworm)   6.17.0-22-generic   containerd://2.2.0
```

## 4. ArgoCD Installation Evidence

Namespace creation:

```bash
$ docker exec lab13-control-plane kubectl --kubeconfig=/etc/kubernetes/admin.conf create namespace argocd --dry-run=client -o yaml | \
  docker exec -i lab13-control-plane kubectl --kubeconfig=/etc/kubernetes/admin.conf apply -f -
namespace/argocd created
```

Installation used the official ArgoCD manifest `v2.13.3`:

```bash
curl -fsSL -o /tmp/argocd-install-v2.13.3.yaml \
  https://raw.githubusercontent.com/argoproj/argo-cd/v2.13.3/manifests/install.yaml

docker exec -i lab13-control-plane kubectl --kubeconfig=/etc/kubernetes/admin.conf -n argocd apply -f - \
  < /tmp/argocd-install-v2.13.3.yaml
```

CRDs created:

```bash
$ docker exec lab13-control-plane kubectl --kubeconfig=/etc/kubernetes/admin.conf get crd | grep argoproj
applications.argoproj.io      2026-04-23T20:06:40Z
applicationsets.argoproj.io   2026-04-23T20:06:41Z
appprojects.argoproj.io       2026-04-23T20:06:41Z
```

Controller resources created in `argocd`:

```bash
$ docker exec lab13-control-plane kubectl --kubeconfig=/etc/kubernetes/admin.conf get deploy,sts,svc,pods -n argocd
NAME                                               READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/argocd-applicationset-controller   0/1     1            0           24s
deployment.apps/argocd-dex-server                  0/1     1            0           24s
deployment.apps/argocd-notifications-controller    0/1     1            0           24s
deployment.apps/argocd-redis                       0/1     1            0           24s
deployment.apps/argocd-repo-server                 0/1     1            0           24s
deployment.apps/argocd-server                      0/1     1            0           24s

NAME                                             READY   AGE
statefulset.apps/argocd-application-controller   0/1     24s

NAME                                                    READY   STATUS              RESTARTS   AGE
pod/argocd-application-controller-0                     0/1     ContainerCreating   0          24s
pod/argocd-applicationset-controller-5cc74c9f94-qwnx7   0/1     ContainerCreating   0          24s
pod/argocd-dex-server-859ffb9b65-84w49                  0/1     Init:0/1            0          24s
pod/argocd-notifications-controller-6b9986b99c-pnfs5    0/1     ContainerCreating   0          24s
pod/argocd-redis-5587bfd996-w78zg                       0/1     Init:0/1            0          24s
pod/argocd-repo-server-7c9fc5b5b9-sf629                 0/1     Init:0/1            0          24s
pod/argocd-server-c985f9b54-wzt6w                       0/1     ContainerCreating   0          24s
```

## 5. Live Application Evidence

I applied all repository manifests to the live cluster:

```bash
$ docker exec -i lab13-control-plane kubectl --kubeconfig=/etc/kubernetes/admin.conf apply -f - < k8s/argocd/application.yaml
application.argoproj.io/devops-info created

$ docker exec -i lab13-control-plane kubectl --kubeconfig=/etc/kubernetes/admin.conf apply -f - < k8s/argocd/application-dev.yaml
application.argoproj.io/devops-info-dev created

$ docker exec -i lab13-control-plane kubectl --kubeconfig=/etc/kubernetes/admin.conf apply -f - < k8s/argocd/application-prod.yaml
application.argoproj.io/devops-info-prod created

$ docker exec -i lab13-control-plane kubectl --kubeconfig=/etc/kubernetes/admin.conf apply -f - < k8s/argocd/applicationset.yaml
applicationset.argoproj.io/devops-info-envs created
```

Objects present in the cluster:

```bash
$ docker exec lab13-control-plane kubectl --kubeconfig=/etc/kubernetes/admin.conf get applications,applicationsets -A -o wide
NAMESPACE   NAME                                       SYNC STATUS   HEALTH STATUS   REVISION   PROJECT
argocd      application.argoproj.io/devops-info                                                 default
argocd      application.argoproj.io/devops-info-dev                                             default
argocd      application.argoproj.io/devops-info-prod                                            default

NAMESPACE   NAME                                          AGE
argocd      applicationset.argoproj.io/devops-info-envs   21s
```

Stored cluster-side `Application` spec for `devops-info-dev`:

```yaml
spec:
  destination:
    namespace: dev
    server: https://kubernetes.default.svc
  source:
    helm:
      releaseName: devops-info-dev
      valueFiles:
      - values.yaml
      - values-dev.yaml
    path: k8s/devops-info
    repoURL: https://github.com/ebortsov/DevOps-Core-Course.git
    targetRevision: lab13
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
    syncOptions:
    - CreateNamespace=true
```

Stored cluster-side `Application` spec for `devops-info-prod`:

```yaml
spec:
  destination:
    namespace: prod
    server: https://kubernetes.default.svc
  source:
    helm:
      releaseName: devops-info-prod
      valueFiles:
      - values.yaml
      - values-prod.yaml
    path: k8s/devops-info
    repoURL: https://github.com/ebortsov/DevOps-Core-Course.git
    targetRevision: lab13
  syncPolicy:
    syncOptions:
    - CreateNamespace=true
```

Stored cluster-side `ApplicationSet` spec confirms the `dev` / `prod` generator and conditional auto-sync template patch.

## 6. Runtime Blockers Found During Evidence Collection

The cluster objects for Lab 13 were created successfully, but one environment-level blocker still prevents a clean `Synced/Healthy` runtime demonstration.

### Blocker 1: broken system networking in the fresh `kind` cluster

Even after recreating `lab13` from scratch, `kube-proxy` fails:

```bash
$ docker exec lab13-control-plane kubectl --kubeconfig=/etc/kubernetes/admin.conf get pods -n kube-system
NAME                                          READY   STATUS    RESTARTS      AGE
coredns-7d764666f9-dt2j7                      0/1     Running   0             115s
coredns-7d764666f9-tsr4z                      0/1     Running   0             115s
etcd-lab13-control-plane                      1/1     Running   0             2m2s
kindnet-djxn8                                 1/1     Running   0             115s
kube-apiserver-lab13-control-plane            1/1     Running   0             2m2s
kube-controller-manager-lab13-control-plane   1/1     Running   0             2m2s
kube-proxy-xg2d9                              0/1     Error     4 (72s ago)   115s
kube-scheduler-lab13-control-plane            1/1     Running   0             2m2s
```

This prevents the cluster from reaching a clean baseline for controller-to-service communication and application health checks.

The GitHub branch blocker was resolved during validation:

```bash
$ git ls-remote --heads https://github.com/ebortsov/DevOps-Core-Course.git lab13
f894415169692355fee47a592f3e83cea30dfce1	refs/heads/lab13
```

However, ArgoCD controllers still cannot reconcile because they repeatedly fail to reach the Kubernetes service IP `10.96.0.1:443`:

```text
failed to list *v1alpha1.Application: Get "https://10.96.0.1:443/...": dial tcp 10.96.0.1:443: connect: no route to host
```

This matches the broken `kube-proxy` state in `kube-system` and explains why `Application.status.sync` and `Application.status.health` remain empty.

## 7. Conclusion

What is fully evidenced:

- Lab 13 manifests were created in the repository
- the target Helm chart passes local lint/render validation
- a fresh `kind` cluster was recreated for validation
- ArgoCD CRDs and controller resources were installed into the cluster
- all repository `Application` and `ApplicationSet` manifests were successfully created in the cluster
- the cluster-side stored specs match the intended namespaces, releases, value files, repo URL, and sync policies

What is not fully evidenced because of the environment:

- `Synced/Healthy` ArgoCD runtime state
- live self-healing demonstration
- UI login screenshots

The missing runtime proof is blocked by the current environment, not by missing Lab 13 manifests:

- fresh `kind` cluster still has failing `kube-proxy`
- the remote `lab13` branch now exists, but ArgoCD controllers still cannot talk to the in-cluster service IP
