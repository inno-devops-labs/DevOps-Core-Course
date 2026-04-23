# lab 13: gitops with argocd

## 1. argocd installation & setup

### installation via helm

```bash
# add helm repo
helm repo add argo https://argoproj.github.io/argo-helm
helm repo update

# create namespace and install
kubectl create namespace argocd
helm install argocd argo/argo-cd --namespace argocd

# wait for all components
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=argocd-server -n argocd --timeout=120s
```

### accessing the ui

```bash
# port-forward (keep running)
kubectl port-forward svc/argocd-server -n argocd 8080:443

# retrieve initial admin password
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d
```

access at **https://localhost:8080** with username `admin`

### cli setup

```bash
# install (macos)
brew install argocd

# log in
argocd login localhost:8080 --insecure

# verify
argocd app list
argocd account get-user-info
```

### verification

[argocd pods running](screenshots/argocd-pods.png)

[argocd ui](screenshots/argocd-ui.png)

---

## 2. application deployment

### chart structure (updated)

```
k8s/
├── devops-info-service/       # helm chart (from lab 10)
│   ├── Chart.yaml
│   ├── values.yaml
│   ├── values-dev.yaml
│   ├── values-prod.yaml
│   └── templates/...
├── argocd/                    # argocd manifests (new)
│   ├── application.yaml       # base app (manual sync)
│   ├── application-dev.yaml   # dev app (auto-sync)
│   ├── application-prod.yaml  # prod app (manual sync)
│   └── applicationset.yaml    # bonus: generates dev/prod
└── ARGOCD.md                  # this documentation
```

### application manifest ([application.yaml](argocd/application.yaml))

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: devops-info-service
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/serasma/devops-s26.git
    targetRevision: lab13
    path: k8s/devops-info-service
    helm:
      valueFiles:
        - values.yaml
  destination:
    server: https://kubernetes.default.svc
    namespace: default
  syncPolicy:
    syncOptions:
      - CreateNamespace=true
```

### key fields

| field | value | why |
|-------|-------|-----|
| `repoURL` | `https://github.com/serasma/devops-s26.git` | source git repository |
| `targetRevision` | `lab13` | branch to track |
| `path` | `k8s/devops-info-service` | helm chart location |
| `helm.valueFiles` | `values.yaml` | default values |
| `destination.namespace` | `default` | deploy to default namespace |
| `syncPolicy` | manual | no automated sync initially |

### deploying and syncing

```bash
# apply application manifest
kubectl apply -f k8s/argocd/application.yaml

# observe in ui — status: outofsync
# trigger manual sync
argocd app sync devops-info-service

# verify status
argocd app get devops-info-service
```

### sync status indicators

| status | meaning |
|--------|---------|
| synced | cluster matches git |
| outofsync | git has changes not applied |
| unknown | unable to determine state |
| healthy | all resources running |
| degraded | one or more resources unhealthy |
| progressing | deployment in progress |

### gitops workflow test

1. change `replicaCount` in `values.yaml`
2. commit and push to `lab13` branch
3. argocd detects drift (within 3 min polling interval)
4. sync the change via ui or `argocd app sync devops-info-service`

[argocd app sync](screenshots/argocd-app-sync.png)

---

## 3. multi-environment deployment

### namespaces

```bash
kubectl create namespace dev
kubectl create namespace prod
```

### dev application ([application-dev.yaml](argocd/application-dev.yaml))

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: devops-info-service-dev
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/serasma/devops-s26.git
    targetRevision: lab13
    path: k8s/devops-info-service
    helm:
      valueFiles:
        - values-dev.yaml
  destination:
    server: https://kubernetes.default.svc
    namespace: dev
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
    syncOptions:
      - CreateNamespace=true
```

### prod application ([application-prod.yaml](argocd/application-prod.yaml))

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: devops-info-service-prod
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/serasma/devops-s26.git
    targetRevision: lab13
    path: k8s/devops-info-service
    helm:
      valueFiles:
        - values-prod.yaml
  destination:
    server: https://kubernetes.default.svc
    namespace: prod
  syncPolicy:
    syncOptions:
      - CreateNamespace=true
```

### dev vs prod configuration

| parameter | dev | prod |
|-----------|-----|------|
| replicas | 1 | 5 |
| image tag | `latest` | `v0` |
| image pull policy | `always` | `ifnotpresent` |
| service type | `nodeport` (30080) | `loadbalancer` |
| cpu limit | 100m | 500m |
| memory limit | 128mi | 512mi |
| debug env | `true` | `false` |
| rolling update | default | maxsurge=1, maxunavailable=0 |
| pod anti-affinity | no | yes (preferred) |

### sync policy comparison

| aspect | dev | prod |
|--------|-----|------|
| automated sync | yes | no |
| prune | yes | n/a |
| selfheal | yes | n/a |
| deployment trigger | git push (automatic) | manual review required |

**why manual for prod:**
- changes require review before reaching production
- controlled release timing (deploy during low-traffic windows)
- compliance requirements often mandate approval gates
- rollback planning is easier when deployments are intentional

### verification

```bash
kubectl apply -f k8s/argocd/application-dev.yaml
kubectl apply -f k8s/argocd/application-prod.yaml

# check both apps
argocd app list

# verify per-namespace pods
kubectl get pods -n dev
kubectl get pods -n prod
```

[both apps in argocd ui](screenshots/argocd-multi-env.png)

---

## 4. self-healing & sync policies

### test 1: manual scale (argocd self-healing)

```bash
# before: dev has 1 replica (from values-dev.yaml)
$ kubectl get deployment devops-info-service -n dev -o jsonpath='{.spec.replicas}'
1

# manually scale to 5
$ kubectl scale deployment devops-info-service -n dev --replicas=5
deployment.apps/devops-info-service scaled

# argocd detects drift and self-heals
$ argocd app get devops-info-service-dev
# status: outofsync → synced (after self-heal)

# after: argocd reverts to 1 replica
$ kubectl get deployment devops-info-service -n dev -o jsonpath='{.spec.replicas}'
1
```

**behavior:** argocd detected that the live state (5 replicas) diverged from git state (1 replica) and automatically reverted the change.

[self-healing scale revert](screenshots/argocd-selfheal-scale.png)

### test 2: pod deletion (kubernetes self-healing)

```bash
# delete a pod
$ kubectl delete pod -n dev -l app.kubernetes.io/name=devops-info-service
pod "devops-info-service-xxx" deleted

# kubernetes immediately recreates the pod (replicaset controller)
$ kubectl get pods -n dev -w
# pod recreated within seconds
```

**behavior:** this is **kubernetes** self-healing, not argocd. the replicaset controller ensures the desired pod count. argocd is not involved because the pod count still matches the deployment spec.

### test 3: configuration drift

```bash
# add a label manually
$ kubectl label deployment devops-info-service -n dev manually-added=true
deployment.apps/devops-info-service labeled

# check diff
$ argocd app diff devops-info-service-dev
# shows the extra label as a difference

# argocd self-heals and removes the label
$ kubectl get deployment devops-info-service -n dev -o jsonpath='{.metadata.labels.manually-added}'
# output: (empty — label removed)
```

### kubernetes vs argocd self-healing

| aspect | kubernetes | argocd |
|--------|------------|--------|
| what it heals | pod count | deployment spec |
| trigger | pod crash/delete | config drift from git |
| mechanism | replicaset controller | git comparison + sync |
| scope | runtime (pods) | configuration (all resources) |
| requires selfheal? | no (always on) | yes (must be enabled) |

### sync triggers

| trigger | mechanism | response |
|---------|-----------|----------|
| git commit pushed | argocd polls git every 3 min | auto-sync applies changes (if automated) |
| git webhook | immediate notification | instant sync |
| manual | user clicks sync / runs cli | immediate sync |
| drift detected | periodic comparison | self-heal reverts (if enabled) |

**default sync interval:** 3 minutes (configurable via `timeout.reconciliation`)

---

## 5. bonus: applicationset

### applicationset manifest ([applicationset.yaml](argocd/applicationset.yaml))

```yaml
apiVersion: argoproj.io/v1alpha1
kind: ApplicationSet
metadata:
  name: devops-info-service-set
  namespace: argocd
spec:
  generators:
    - list:
        elements:
          - env: dev
            namespace: dev
            valuesFile: values-dev.yaml
          - env: prod
            namespace: prod
            valuesFile: values-prod.yaml
  template:
    metadata:
      name: 'devops-info-service-{{env}}'
    spec:
      project: default
      source:
        repoURL: https://github.com/serasma/devops-s26.git
        targetRevision: lab13
        path: k8s/devops-info-service
        helm:
          valueFiles:
            - '{{valuesFile}}'
      destination:
        server: https://kubernetes.default.svc
        namespace: '{{namespace}}'
      syncPolicy:
        automated:
          prune: true
          selfHeal: true
        syncOptions:
          - CreateNamespace=true
```

### how the list generator works

```
┌─────────────────────────────────────────────────────────┐
│                  applicationset                          │
│                                                          │
│  list generator:                                         │
│  ┌──────────────┐    ┌──────────────┐                   │
│  │ env: dev     │    │ env: prod    │                   │
│  │ ns:  dev     │    │ ns:  prod    │                   │
│  │ val: -dev    │    │ val: -prod   │                   │
│  └──────┬───────┘    └──────┬───────┘                   │
│         │                   │                            │
│         ▼                   ▼                            │
│  ┌──────────────┐    ┌──────────────┐                   │
│  │ application  │    │ application  │                   │
│  │  -dev        │    │  -prod       │                   │
│  └──────────────┘    └──────────────┘                   │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### individual applications vs applicationset

| aspect | individual applications | applicationset |
|--------|------------------------|----------------|
| number of manifests | one per environment | one for all environments |
| adding a new environment | create new application yaml | add element to list |
| consistency | must keep all in sync | template ensures consistency |
| dry principle | no — repeated fields | yes — shared template |

### generator types

| generator | use case |
|-----------|----------|
| list | small fixed set of environments |
| cluster | deploy to multiple clusters |
| git directory | auto-discover apps from repo structure |
| git files | parameterize from json/yaml in git |
| matrix | combine generators (e.g., all apps x all clusters) |
| merge | merge outputs from multiple generators |

### note on conditional sync policy

the applicationset template applies the same sync policy to all generated applications. to have dev auto-sync and prod manual sync, you can:
1. use two separate applicationsets with different sync policies
2. use a git files generator with sync policy defined in per-environment config files
3. patch the generated prod application after creation to remove auto-sync

---

## 6. file references

| file | description |
|------|-------------|
| [application.yaml](argocd/application.yaml) | base argocd application (manual sync) |
| [application-dev.yaml](argocd/application-dev.yaml) | dev argocd application (auto-sync + selfheal) |
| [application-prod.yaml](argocd/application-prod.yaml) | prod argocd application (manual sync) |
| [applicationset.yaml](argocd/applicationset.yaml) | applicationset with list generator |
| [values.yaml](devops-info-service/values.yaml) | default helm values |
| [values-dev.yaml](devops-info-service/values-dev.yaml) | development environment values |
| [values-prod.yaml](devops-info-service/values-prod.yaml) | production environment values |
