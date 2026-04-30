# lab 14: progressive delivery with argo rollouts

## 1. argo rollouts setup

### installation

```bash
# create namespace and install controller
kubectl create namespace argo-rollouts
kubectl apply -n argo-rollouts -f https://github.com/argoproj/argo-rollouts/releases/latest/download/install.yaml

# install kubectl plugin (macos)
brew install argoproj/tap/kubectl-argo-rollouts

# verify
kubectl argo rollouts version
```

### dashboard

```bash
# install dashboard
kubectl apply -n argo-rollouts -f https://github.com/argoproj/argo-rollouts/releases/latest/download/dashboard-install.yaml

# access via port-forward (keep running)
kubectl port-forward svc/argo-rollouts-dashboard -n argo-rollouts 3100:3100
```

access at **http://localhost:3100**

### exploring the ui

the dashboard shows all rollouts in the cluster. after deploying a rollout:

1. select the rollout from the list — opens the detail view
2. the **visualizer** shows the current step in the canary/blue-green progression
3. stable and canary pods are displayed with their weight percentages
4. use the **promote** button to advance through manual pause steps
5. use the **abort** button to roll back immediately
6. the **revisions** tab shows rollout history for undo/rollback


[argo rollouts dashboard](docs/screenshots/rollouts-dashboard.png)

### rollout vs deployment

| aspect | deployment | rollout |
|--------|-----------|---------|
| api version | `apps/v1` | `argoproj.io/v1alpha1` |
| kind | deployment | rollout |
| strategy | rollingupdate / recreate | canary / bluegreen |
| traffic shifting | no | yes (via service/istio/smi) |
| automated rollback on metrics | no | yes (analysistemplate) |
| pause/resume | no | yes |
| pod template spec | standard | identical to deployment |

the rollout crd is a superset of deployment — all pod template fields are the same. the key difference is the `strategy` field, which supports `canary` and `blueGreen` with step-by-step traffic control.

---

## 2. canary deployment

### chart structure (updated)

```
k8s/
├── devops-info-service/            # helm chart
│   ├── Chart.yaml
│   ├── values.yaml                 # rollout.enabled: true, strategy: canary
│   ├── values-dev.yaml             # canary strategy
│   ├── values-prod.yaml            # bluegreen strategy
│   └── templates/
│       ├── deployment.yaml         # rendered only when rollout.enabled=false
│       ├── rollout.yaml            # rendered only when rollout.enabled=true
│       ├── preview-service.yaml    # rendered only with bluegreen strategy
│       ├── analysis-template.yaml  # rendered only when analysis.enabled=true
│       └── ...
├── argocd/
│   ├── application-rollout.yaml    # argocd app for rollouts
│   └── ...
└── ROLLOUTS.md                     # this documentation
```

### rollout manifest ([rollout.yaml](devops-info-service/templates/rollout.yaml))

when `rollout.enabled: true` and `rollout.strategy: canary`:

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Rollout
metadata:
  name: {{ include "devops-info-service.fullname" . }}
spec:
  replicas: {{ .Values.replicaCount }}
  selector:
    matchLabels:
      {{- include "devops-info-service.selectorLabels" . | nindent 6 }}
  strategy:
    canary:
      steps:
        - setWeight: 20
        - pause: {}                # manual promotion
        - setWeight: 40
        - pause: { duration: 30s }
        - setWeight: 60
        - pause: { duration: 30s }
        - setWeight: 80
        - pause: { duration: 30s }
        - setWeight: 100
  template:
    # same pod template as deployment
```

### values.yaml configuration

```yaml
rollout:
  enabled: true
  strategy: canary
  canary:
    steps:
      - setWeight: 20
      - pause: {}               # manual promotion required
      - setWeight: 40
      - pause:
          duration: 30s          # auto-promote after 30s
      - setWeight: 60
      - pause:
          duration: 30s
      - setWeight: 80
      - pause:
          duration: 30s
      - setWeight: 100           # full cutover
```

### step-by-step rollout progression

1. deploy initial version — all traffic goes to stable pods
2. trigger update — change image tag or env var in values
3. 20% canary — new pods receive 20% of traffic, then pauses for manual review
4. promote — `kubectl argo rollouts promote <name>` moves to 40%
5. auto-progress — 40% → 60% → 80% with 30s pauses between each
6. full promotion — 100% traffic on new version, old pods scaled down

[canary rollout progression](docs/screenshots/rollouts-canary.png)

### promoting and aborting

```bash
# watch rollout status in real-time
kubectl argo rollouts get rollout <name> -w

# promote to next step (from manual pause)
kubectl argo rollouts promote <name>

# promote fully (skip all remaining steps)
kubectl argo rollouts promote <name> --full

# abort and rollback
kubectl argo rollouts abort <name>

# retry an aborted rollout
kubectl argo rollouts retry rollout <name>
```

### rollback

when a rollout is aborted, argo rollouts shifts all traffic back to the stable version and scales down the canary pods. this is an immediate revert to the last known-good revision.

```bash
kubectl argo rollouts abort <name>
# traffic immediately returns to stable pods
```

[canary abort and rollback](docs/screenshots/rollouts-canary-abort.png)

---

## 3. blue-green deployment

### configuration

when `rollout.strategy: blueGreen`:

```yaml
rollout:
  enabled: true
  strategy: blueGreen
  blueGreen:
    autoPromotionEnabled: false   # requires manual promotion
    scaleDownDelaySeconds: 30     # wait before removing old pods
```

### active vs preview services

| service | purpose | routes to |
|---------|---------|-----------|
| `devops-info-service` | active (production) | blue (current) pods |
| `devops-info-service-preview` | preview (testing) | green (new) pods |

the preview service ([preview-service.yaml](devops-info-service/templates/preview-service.yaml)) is only created when strategy is bluegreen.

when a new version is deployed:
1. green pods are created alongside blue pods
2. preview service points to green pods for validation
3. active service still points to blue pods (no traffic disruption)
4. on promotion, active service instantly switches to green pods
5. blue pods are scaled down after `scaleDownDelaySeconds`

### testing the preview

```bash
# access production (active/blue)
kubectl port-forward svc/devops-info-service 8080:80

# access preview (green)
kubectl port-forward svc/devops-info-service-preview 8081:80

# verify both versions, then promote
kubectl argo rollouts promote devops-info-service
```

[blue-green preview vs active](docs/screenshots/rollouts-bluegreen-preview.png)

### instant rollback

```bash
# undo the promotion — instant switch back
kubectl argo rollouts undo devops-info-service
```

blue-green rollback is instant because both versions exist simultaneously — it's just a service selector switch. this is significantly faster than canary rollback.

[blue-green instant rollback](docs/screenshots/rollouts-bluegreen-rollback.png)

---

## 4. strategy comparison

| aspect | canary | blue-green |
|--------|--------|------------|
| traffic shift | gradual (20% → 40% → ... → 100%) | instant (0% → 100%) |
| risk exposure | low — small % of users affected initially | none during preview, all-at-once on promote |
| resource usage | only canary pods needed (fraction of replicas) | 2x resources (both versions running) |
| rollback speed | fast (traffic shifts back, pods scale up) | instant (service selector switch) |
| testing | real production traffic at small scale | dedicated preview environment |
| complexity | higher (steps, weights, pauses) | lower (just active/preview) |

### when to use each

| scenario | recommended strategy | why |
|----------|---------------------|-----|
| dev environment | canary | validate with real traffic at low risk, fewer resources needed |
| prod with limited resources | canary | no need for 2x capacity |
| prod with compliance requirements | blue-green | full preview for qa, instant rollback capability |
| critical releases | blue-green | zero-risk preview, instant switch back |
| gradual feature exposure | canary | fine-grained control over blast radius |

---

## 5. automated analysis (bonus)

### analysis template ([analysis-template.yaml](devops-info-service/templates/analysis-template.yaml))

```yaml
apiVersion: argoproj.io/v1alpha1
kind: AnalysisTemplate
metadata:
  name: {{ include "devops-info-service.fullname" . }}-analysis
spec:
  metrics:
    - name: webcheck
      provider:
        web:
          url: http://devops-info-service.default.svc/health
          jsonPath: "{$.status}"
      successCondition: result == "ok"
      interval: 10s
      count: 3
      failureLimit: 1
```

how it works:
- sends http requests to the `/health` endpoint
- checks that response json `$.status` equals `"ok"`
- runs 3 checks at 10-second intervals
- fails if more than 1 check fails (allows 1 transient failure)

### integration with canary

when `rollout.analysis.enabled: true`, an analysis step is added to the canary strategy:

```yaml
strategy:
  canary:
    steps:
      - setWeight: 20
      - analysis:                 # runs health check analysis
          templates:
            - templateName: devops-info-service-analysis
      - setWeight: 40
      - pause:
          duration: 30s
      - setWeight: 100
```

if the analysis fails (health checks return non-ok), the rollout is automatically rolled back to the stable version.

### values.yaml configuration

```yaml
rollout:
  analysis:
    enabled: false              # set to true to enable
    webUrl: ""                  # defaults to http://<release-name>.<namespace>.svc/health
    interval: 10s
    count: 3
    failureLimit: 1
```

[analysis auto-rollback](docs/screenshots/rollouts-analysis-rollback.png)

---

## 6. cli commands reference

### managing rollouts

```bash
# list rollouts
kubectl argo rollouts list rollouts

# get rollout status
kubectl argo rollouts get rollout <name>

# watch in real-time
kubectl argo rollouts get rollout <name> -w

# promote to next step
kubectl argo rollouts promote <name>

# promote fully (skip all remaining steps)
kubectl argo rollouts promote <name> --full

# abort rollout
kubectl argo rollouts abort <name>

# retry aborted rollout
kubectl argo rollouts retry rollout <name>

# undo (rollback to previous revision)
kubectl argo rollouts undo <name>

# restart rollout (same spec, new pods)
kubectl argo rollouts restart <name>
```

### troubleshooting

```bash
# view rollout events
kubectl describe rollout <name>

# view rollout revisions
kubectl argo rollouts history <name>

# view analysis runs
kubectl get analysisruns

# view analysis run details
kubectl describe analysisrun <name>

# check rollout crd
kubectl get rollouts
kubectl get rollout <name> -o yaml
```

### helm deployment

```bash
# deploy with canary strategy
helm install devops-info-service ./k8s/devops-info-service \
  --set rollout.enabled=true \
  --set rollout.strategy=canary

# deploy with blue-green strategy
helm install devops-info-service ./k8s/devops-info-service \
  --set rollout.enabled=true \
  --set rollout.strategy=blueGreen

# deploy with analysis enabled
helm install devops-info-service ./k8s/devops-info-service \
  --set rollout.enabled=true \
  --set rollout.strategy=canary \
  --set rollout.analysis.enabled=true

# deploy with standard deployment (no rollout)
helm install devops-info-service ./k8s/devops-info-service \
  --set rollout.enabled=false
```

---

## 7. file references

| file | description |
|------|-------------|
| [rollout.yaml](devops-info-service/templates/rollout.yaml) | rollout crd template (canary/bluegreen) |
| [preview-service.yaml](devops-info-service/templates/preview-service.yaml) | preview service for blue-green |
| [analysis-template.yaml](devops-info-service/templates/analysis-template.yaml) | analysis template for automated rollback |
| [deployment.yaml](devops-info-service/templates/deployment.yaml) | original deployment (when rollout disabled) |
| [application-rollout.yaml](argocd/application-rollout.yaml) | argocd application manifest |
| [values.yaml](devops-info-service/values.yaml) | default helm values (canary strategy) |
| [values-dev.yaml](devops-info-service/values-dev.yaml) | development environment values |
| [values-prod.yaml](devops-info-service/values-prod.yaml) | production environment values (bluegreen) |
