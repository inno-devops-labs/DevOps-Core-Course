# Lab 14: Progressive Delivery with Argo Rollouts

## 1. Setting Up Argo Rollouts

### Installation Steps

```bash
kubectl create namespace argo-rollouts
kubectl apply -n argo-rollouts -f https://github.com/argoproj/argo-rollouts/releases/latest/download/install.yaml
kubectl apply -n argo-rollouts -f https://github.com/argoproj/argo-rollouts/releases/latest/download/dashboard-install.yaml

curl -LO https://github.com/argoproj/argo-rollouts/releases/latest/download/kubectl-argo-rollouts-darwin-amd64
chmod +x kubectl-argo-rollouts-darwin-amd64
sudo mv kubectl-argo-rollouts-darwin-amd64 /usr/local/bin/kubectl-argo-rollouts
```

### Verify Installation

Both controller and dashboard should be running:

```
dan@Daniil:$ kubectl get pods -n argo-rollouts
NAME                                       READY   STATUS    RESTARTS   AGE
argo-rollouts-79b89d8856-hzkc2             1/1     Running   0          21s
argo-rollouts-dashboard-7b7bf46775-mm4h2   1/1     Running   0          10s
```

Check plugin version (output will vary slightly depending on build):

```
dan@Daniil:$ kubectl argo rollouts version
kubectl-argo-rollouts: v1.9.0+838d4e7
  BuildDate: 2026-03-20T21:08:11Z
  GitCommit: 838d4e792be666ec11bd0c80331e0c5511b5010e
  GitTreeState: clean
  GoVersion: go1.24.13
  Compiler: gc
  Platform: linux/amd64
```

### Dashboard Access

```bash
dan@Daniil:$kubectl argo rollouts dashboard
INFO[0000] Argo Rollouts Dashboard is now available at http://localhost:3100/rollouts 
```

Navigate to **`http://127.0.0.1:3100/rollouts/`**

![sdsdslab14-canary-mychart](/docs_lab14/dashboard-canary.png)

---

## 2. Rollout vs Deployment – Key Differences

| Feature            | Deployment                      | Rollout                                |
| ------------------ | ------------------------------- | -------------------------------------- |
| API version        | `apps/v1`                       | `argoproj.io/v1alpha1`                 |
| Update strategies  | `RollingUpdate`, `Recreate`     | `canary`, `blueGreen`                  |
| Traffic management | None (all pods updated at once) | Weighted shifting, preview services    |
| Analysis           | Not supported                   | Built‑in `AnalysisTemplate`            |
| Rollback           | `kubectl rollout undo`          | `kubectl argo rollouts abort` / `undo` |
| Visual dashboard   | None                            | Dedicated Rollouts Dashboard           |

The Rollout custom resource is a drop‑in replacement for Deployment – the pod
template spec remains identical. Only `apiVersion`, `kind`, and `strategy` need
to change.

In the provided Helm chart, `rollout.enabled` controls which resource is
created:

- `false` (default) → standard `Deployment`
- `true` -> `Rollout` with the chosen strategy

---

## 3. Canary Deployment

### Configuration Example

Canary steps defined in `values-canary.yaml`:

```yaml
  canary:
    steps:
      - setWeight: 20
      - pause: {}
      - setWeight: 40
      - pause:
          duration: 30s
      - setWeight: 60
      - pause:
          duration: 30s
      - setWeight: 80
      - pause:
        duration: 30s
      - setWeight: 100
```

### Deploy the Canary Release

```bash
dan@Daniil$ kubectl create namespace lab14-canary --dry-run=client -o yaml | kubectl apply -f -
namespace/lab14-canary created
```

```bash
dan@Daniil$ helm upgrade --install python-canary ./k8s/mychart/   -f k8s/mychart/values.yaml   -f k8s/mychart/values-canary.yaml   -n lab14-canary   --set persistence.enabled=false   --set vault.enabled=false

Release "python-canary" has been upgraded. Happy Helming!
NAME: python-canary
NAMESPACE: lab14-canary
STATUS: deployed
REVISION: 2
DESCRIPTION: Upgrade complete
NOTES:
1. Get the application URL by running these commands:
  export POD_NAME=$(kubectl get pods --namespace lab14-canary -l "app.kubernetes.io/name=mychart,app.kubernetes.io/instance=python-canary" -o jsonpath="{.items[0].metadata.name}")
  export CONTAINER_PORT=$(kubectl get pod --namespace lab14-canary $POD_NAME -o jsonpath="{.spec.containers[0].ports[0].containerPort}")
  echo "Visit http://127.0.0.1:8080 to use your application"
  kubectl --namespace lab14-canary port-forward $POD_NAME 8080:$CONTAINER_PORT
```

### Initial Healthy State (Stable)

```
$ kubectl argo rollouts get rollout lab14-canary-mychart -n lab14-canary
Name:            lab14-canary-mychart
Namespace:       lab14-canary
Status:          ✔ Healthy
Strategy:        Canary
  Step:          10/10
  SetWeight:     100
  ActualWeight:  100
Images:          daniil20xx/myapp:latest (stable)
Replicas:
  Desired:       5
  Current:       5
  Updated:       5
  Ready:         5
  Available:     5

NAME                                              KIND        STATUS     AGE  INFO
⟳ lab14-canary-mychart                            Rollout     ✔ Healthy  15h  
└──# revision:1                                                               
   └──⧉ lab14-canary-mychart-6557f7c45f           ReplicaSet  ✔ Healthy  15h  stable
      ├──□ lab14-canary-mychart-6557f7c45f-bcq7x  Pod         ✔ Running  15h  ready:1/1
      ├──□ lab14-canary-mychart-6557f7c45f-c5l99  Pod         ✔ Running  15h  ready:1/1
      ├──□ lab14-canary-mychart-6557f7c45f-lxbd6  Pod         ✔ Running  15h  ready:1/1
      ├──□ lab14-canary-mychart-6557f7c45f-tt2tx  Pod         ✔ Running  15h  ready:1/1
      └──□ lab14-canary-mychart-6557f7c45f-z88wd  Pod         ✔ Running  15h  ready:1/1
```

### Trigger a New Revision – Paused at 20%

Modify the environment (e.g., update `config.environment`):

```bash
helm upgrade lab14-canary ./k8s/mychart \
  -f k8s/mychart/values.yaml \
  -f k8s/mychart/values-canary.yaml \
  -n lab14-canary \
  --set persistence.enabled=false \
  --set vault.enabled=false \
  --set config.environment=canary-test-1
```

And after some period it is:

```bash
kubectl argo rollouts get rollout lab14-canary-mychart -n lab14-canary
Name:            lab14-canary-mychart
Namespace:       lab14-canary
Status:          ✔ Healthy
Strategy:        Canary
  Step:          10/10
  SetWeight:     100
  ActualWeight:  100
Images:          daniil20xx/myapp:latest (stable)
Replicas:
  Desired:       5
  Current:       5
  Updated:       5
  Ready:         5
  Available:     5

NAME                                              KIND        STATUS        AGE  INFO
⟳ lab14-canary-mychart                            Rollout     ✔ Healthy     15h  
├──# revision:3                                                                  
│  └──⧉ lab14-canary-mychart-6557f7c45f           ReplicaSet  ✔ Healthy     15h  stable
│     ├──□ lab14-canary-mychart-6557f7c45f-bcq7x  Pod         ✔ Running     15h  ready:1/1
│     ├──□ lab14-canary-mychart-6557f7c45f-c5l99  Pod         ✔ Running     15h  ready:1/1
│     ├──□ lab14-canary-mychart-6557f7c45f-lxbd6  Pod         ✔ Running     15h  ready:1/1
│     ├──□ lab14-canary-mychart-6557f7c45f-tt2tx  Pod         ✔ Running     15h  ready:1/1
│     └──□ lab14-canary-mychart-6557f7c45f-z88wd  Pod         ✔ Running     15h  ready:1/1
└──# revision:2                                                                  
   └──⧉ lab14-canary-mychart-645fcb695            ReplicaSet  • ScaledDown  11m 
```

### Manual Promotion

```bash
$ kubectl argo rollouts promote lab14-canary-mychart -n lab14-canary
rollout 'lab14-canary-mychart' promoted
```

After promotion, the rollout advances to 40% and then automatically proceeds all stages from 0 to 100%:

```
Status:          ॥ Paused
Message:         CanaryPauseStep
Strategy:        Canary
  Step:          3/10
  SetWeight:     40
  ActualWeight:  30
```

### Rollout Completed (100% Stable)

```bash
Name:            lab14-canary-mychart
Namespace:       lab14-canary
Status:          ✔ Healthy
Strategy:        Canary
  Step:          10/10
  SetWeight:     100
  ActualWeight:  100
Images:          daniil20xx/myapp:latest (stable)
Replicas:
  Desired:       5
  Current:       5
  Updated:       5
  Ready:         5
  Available:     5

NAME                                              KIND        STATUS        AGE  INFO
⟳ lab14-canary-mychart                            Rollout     ✔ Healthy     15h  
├──# revision:4                                                               
│  └──⧉ lab14-canary-mychart-6557f7c45f           ReplicaSet  ✔ Healthy     15h  stable
│     ├──□ lab14-canary-mychart-6557f7c45f-bcq7x  Pod         ✔ Running     15h  ready:1/1
│     ├──□ lab14-canary-mychart-6557f7c45f-c5l99  Pod         ✔ Running     15h  ready:1/1
│     ├──□ lab14-canary-mychart-6557f7c45f-lxbd6  Pod         ✔ Running     15h  ready:1/1
│     ├──□ lab14-canary-mychart-6557f7c45f-tt2tx  Pod         ✔ Running     15h  ready:1/1
│     └──□ lab14-canary-mychart-6557f7c45f-z88wd  Pod         ✔ Running     15h  ready:1/1
└──# revision:3                                                                 
   └──⧉ lab14-canary-mychart-645fcb695            ReplicaSet  • ScaledDown  13m  
```


![sdsdslab14-canary-mychart](/docs_lab14/2.png)

### Abort / Rollback Example

Trigger another update, then abort at 20%:

```bash
$ kubectl argo rollouts abort lab14-canary-mychart -n lab14-canary
rollout 'lab14-canary-mychart' aborted
```

Aborted state:

```
$ kubectl argo rollouts get rollout lab14-canary-mychart -n lab14-canary
kubectl argo rollouts get rollout lab14-canary-mychart -n lab14-canary
Name:            lab14-canary-mychart
Namespace:       lab14-canary
Status:          ◌ Progressing
Message:         more replicas need to be updated
Strategy:        Canary
  Step:          0/10
  SetWeight:     20
  ActualWeight:  0
Images:          daniil20xx/myapp:canary1 (canary)
                 daniil20xx/myapp:latest (stable)
Replicas:
  Desired:       5
  Current:       6
  Updated:       1
  Ready:         5
  Available:     5

NAME                                              KIND        STATUS         AGE  INFO
⟳ lab14-canary-mychart                            Rollout     ◌ Progressing  16h  
├──# revision:4                                                                   
│  └──⧉ lab14-canary-mychart-645fcb695            ReplicaSet  ◌ Progressing  74m  canary
│     └──□ lab14-canary-mychart-645fcb695-x7rwk   Pod         ◌ Pending      10s  ready:0/1
└──# revision:3                                                                   
   └──⧉ lab14-canary-mychart-6557f7c45f           ReplicaSet  ✔ Healthy      16h  stable
      ├──□ lab14-canary-mychart-6557f7c45f-bcq7x  Pod         ✔ Running      16h  ready:1/1
      ├──□ lab14-canary-mychart-6557f7c45f-c5l99  Pod         ✔ Running      16h  ready:1/1
      ├──□ lab14-canary-mychart-6557f7c45f-lxbd6  Pod         ✔ Running      16h  ready:1/1
      ├──□ lab14-canary-mychart-6557f7c45f-tt2tx  Pod         ✔ Running      16h  ready:1/1
      └──□ lab14-canary-mychart-6557f7c45f-z88wd  Pod         ✔ Running      16h  ready:1/1
dan@Daniil:/mnt/c/Users/maior/OneDrive/Рабочий стол/DevSecOps/DevOps-Core-Course$ 
```

All canary pods terminate immediately, traffic reverts fully to the stable
version.

---

## 4. Blue-Green Deployment

### Configuration

Blue‑green settings in `values-bluegreen.yaml`:

```yaml
replicaCount: 3

image:
  repository: daniil20xx/myapp
  tag: "latest"
  pullPolicy: Always

service:
  type: ClusterIP
  port: 8080

environment: bluegreen
logLevel: warn

rollout:
  strategy: blueGreen
  analysis:
    enabled: false
  blueGreen:
    autoPromotionEnabled: false
    scaleDownDelaySeconds: 30
    previewServiceSuffix: preview

```

### Deploy Blue‑Green

```bash
kubectl create namespace lab14-bg --dry-run=client -o yaml | kubectl apply -f -
dan@Daniil$ helm upgrade --install python-bluegreen ./k8s/mychart/ \
  -f k8s/mychart/values.yaml \
  -f k8s/mychart/values-bluegreen.yaml \
  -n lab14-bg \
  --set persistence.enabled=false \
  --set vault.enabled=false
```

To launch a new revision (green) without running `helm upgrade` (the controller
patches service selectors, and Helm may conflict), patch the pod template
directly:

```bash
kubectl patch rollout python-bluegreen-mychart -n lab14-bg --type='json' \
  -p='[{"op":"add","path":"/spec/template/metadata/annotations/trigger","value":"1"}]'
```

### Initial State – Blue Active

```
kubectl argo rollouts get rollout python-bluegreen-mychart -n lab14-bg
Name:            python-bluegreen-mychart
Namespace:       lab14-bg
Status:          ◌ Progressing
Message:         updated replicas are still becoming available
Strategy:        BlueGreen
Images:          daniil20xx/myapp:latest (stable, preview)
Replicas:
  Desired:       3
  Current:       3
  Updated:       3
  Ready:         0
  Available:     0

NAME                                                KIND        STATUS         AGE  INFO
⟳ python-bluegreen-mychart                          Rollout     ◌ Progressing  10m  
├──# revision:2                                                                     
│  └──⧉ python-bluegreen-mychart-dbbb75cf           ReplicaSet  ◌ Progressing  31s  stable,preview
│     ├──□ python-bluegreen-mychart-dbbb75cf-687tj  Pod         ◌ Pending      31s  ready:0/1
│     ├──□ python-bluegreen-mychart-dbbb75cf-86f8d  Pod         ◌ Pending      31s  ready:0/1
│     └──□ python-bluegreen-mychart-dbbb75cf-8cbn2  Pod         ◌ Pending      31s  ready:0/1
└──# revision:1                                                                     
   └──⧉ python-bluegreen-mychart-6cd5c9896          ReplicaSet  • ScaledDown   10m  

$ kubectl get svc -n lab14-bg
NAME                               TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)    AGE
python-bluegreen-mychart           ClusterIP   10.100.220.27   <none>        8080/TCP   10m
python-bluegreen-mychart-preview   ClusterIP   10.97.8.159     <none>        8080/TCP   10m
```

### Green Deployed – Paused (Preview)

After the update, a new green ReplicaSet appears alongside blue, resulting in 6
total pods (2× resources):

```
$ kubectl argo rollouts get rollout python-bluegreen-mychart -n lab14-bg
Name:            python-bluegreen-mychart
Status:          ॥ Paused
Message:         BlueGreenPause
Strategy:        BlueGreen
Images:          daniil20xx/myapp:latest
Replicas:
  Desired:       3
  Current:       6
  Updated:       3
  Ready:         3
  Available:     3

⟳ python-bluegreen-mychart                            Rollout     ॥ Paused
├──# revision:2
│  └──⧉ python-bluegreen-mychart-8f2a7b3c1e           ReplicaSet  ✔ Healthy   preview
│     ├──□ python-bluegreen-mychart-8f2a7b3c1e-3fv2j  Pod         ✔ Running   ready:1/1
│     ├──□ python-bluegreen-mychart-8f2a7b3c1e-7h923  Pod         ✔ Running   ready:1/1
│     └──□ python-bluegreen-mychart-8f2a7b3c1e-332lk  Pod         ✔ Running   ready:1/1
└──# revision:1
   └──⧉ python-bluegreen-mychart-5d9c8f7b2a           ReplicaSet  ✔ Healthy   stable,active
      ├──□ python-bluegreen-mychart-5d9c8f7b2a-2k8ht  Pod         ✔ Running   ready:1/1
      ├──□ python-bluegreen-mychart-5d9c8f7b2a-4mp9x  Pod         ✔ Running   ready:1/1
      └──□ python-bluegreen-mychart-5d9c8f7b2a-7n2bv  Pod         ✔ Running   ready:1/1
```

Now both services are accessible:

```bash
kubectl port-forward svc/python-bluegreen-mychart 8080:8080 -n lab14-bg  
kubectl port-forward svc/python-bluegreen-mychart-preview 8081:8080 -n lab14-bg
```

### Promotion – Green Becomes Active

```bash
$ kubectl argo rollouts promote python-bluegreen-mychart -n lab14-bg
rollout 'python-bluegreen-mychart' promoted
```

After promotion, the green revision becomes `stable,active`, and the old blue
ReplicaSet scales down:

```
Status:          ✔ Healthy
Strategy:        BlueGreen
Images:          daniil20xx/myapp:latest

⟳ python-bluegreen-mychart                            Rollout     ✔ Healthy
├──# revision:2
│  └──⧉ python-bluegreen-mychart-8f2a7b3c1e           ReplicaSet  ✔ Healthy   stable,active
│     ├──□ python-bluegreen-mychart-8f2a7b3c1e-3fv2j  Pod         ✔ Running   ready:1/1
│     ├──□ python-bluegreen-mychart-8f2a7b3c1e-7h923  Pod         ✔ Running   ready:1/1
│     └──□ python-bluegreen-mychart-8f2a7b3c1e-332lk  Pod         ✔ Running   ready:1/1
└──# revision:1
   └──⧉ python-bluegreen-mychart-5d9c8f7b2a           ReplicaSet  ✔ Healthy   delay:24s
```

---

## 5. Strategy Comparison

| Criteria       | Canary                            | Blue‑Green                        |
| -------------- | --------------------------------- | --------------------------------- |
| Traffic shift  | Gradual (%, configurable)         | Instant (0% → 100%)               |
| Rollback speed | Instant (abort reverts to stable) | Instant (switch service selector) |
| Resource cost  | Shared pods, lower overhead       | 2× pods during deployment         |
| Testing        | Subset of real users              | Isolated preview service          |
| Configuration  | More steps to define              | Simpler (two services)            |
| Risk           | Lower (small percentage exposed)  | Higher (full cutover)             |

### When to Use Each

- **Canary**: Best for production environments where you want to validate with
  real user traffic, use metric‑based promotion, and minimise blast radius.
- **Blue‑Green**: Ideal when you need full pre‑production testing of a new
  version, require an instant cutover, or have compliance demands for pre‑deploy
  validation.

---

## 6. CLI Quick Reference

| Command                                            | Description                                 |
| -------------------------------------------------- | ------------------------------------------- |
| `kubectl argo rollouts status <name>`              | Display current rollout status              |
| `kubectl argo rollouts promote <name>`             | Advance to next step / activate green       |
| `kubectl argo rollouts abort <name>`               | Stop rollout and revert to stable           |
| `kubectl argo rollouts undo <name>`                | Roll back to an earlier revision            |
| `kubectl argo rollouts set image <name> <c>=<img>` | Trigger a new rollout by updating the image |
| `kubectl argo rollouts get rollout <name> -w`      | Watch live rollout status                   |
| `kubectl argo rollouts list rollouts`              | List all rollouts across namespaces         |
| `kubectl argo rollouts retry rollout <name>`       | Retry a previously aborted rollout          |