# Lab 14 — Progressive Delivery with Argo Rollouts

## 1. Argo Rollouts Setup

### Controller Installation

Argo Rollouts controller installed in the `argo-rollouts` namespace:

```bash
$ kubectl create namespace argo-rollouts
$ kubectl apply -n argo-rollouts -f https://github.com/argoproj/argo-rollouts/releases/latest/download/install.yaml
```

### Controller Verification

```bash
$ kubectl get pods -n argo-rollouts
NAME                            READY   STATUS    RESTARTS   AGE
argo-rollouts-9f8b7c6d5-x2k4m   1/1     Running   0          2m
```

### kubectl Plugin Installation

```bash
$ kubectl argo rollouts version
  kubectl-argo-rollouts: v1.9.0+838d4e7
    BuildDate: 2026-03-20T21:08:11Z
    GitCommit: 838d4e792be666ec11bd0c80331e0c5511b5010e
    GitTreeState: clean
    GoVersion: go1.24.13
    Compiler: gc
    Platform: linux/amd64
```

### Dashboard Installation and Access

```bash
$ kubectl apply -n argo-rollouts -f https://github.com/argoproj/argo-rollouts/releases/latest/download/dashboard-install.yaml
deployment.apps/argo-rollouts-dashboard created
service/argo-rollouts-dashboard created

$ kubectl port-forward svc/argo-rollouts-dashboard -n argo-rollouts 3100:3100
Forwarding from 127.0.0.1:3100 -> 3100
Forwarding from [::1]:3100 -> 3100
```

The Argo Rollouts Dashboard is accessible at **http://localhost:3100**.

### Rollout vs Deployment Differences

| Aspect | Deployment | Rollout |
|--------|-----------|---------|
| **API Version** | `apps/v1` | `argoproj.io/v1alpha1` |
| **Kind** | `Deployment` | `Rollout` |
| **Strategy** | `RollingUpdate` or `Recreate` | `canary` or `blueGreen` |
| **Traffic Shifting** | Not supported natively | Supported via Ingress/Service Mesh |
| **Automated Analysis** | Not supported | AnalysisTemplate integration |
| **Auto-Rollback** | Manual rollback only | Automated rollback on failure |
| **Pause Steps** | Not supported | Built-in pause (manual or timed) |
| **Dashboard** | Generic Kubernetes | Specialized Rollouts Dashboard |

Key additional fields in Rollout:
- `spec.strategy.canary.steps` — defines progressive weight changes and pauses
- `spec.strategy.blueGreen.activeService` / `previewService` — service references
- `spec.strategy.canary.analysis` — automated metric-based promotion/rollback

---

## 2. Canary Deployment

### Strategy Configuration

The canary strategy is configured in `templates/rollout.yaml`:

```yaml
strategy:
  canary:
    steps:
      - setWeight: 20
      - pause: {}
      - setWeight: 40
      - pause: { duration: 30s }
      - setWeight: 60
      - pause: { duration: 30s }
      - setWeight: 80
      - pause: { duration: 30s }
      - setWeight: 100
```

Progressive traffic shifting: **20% → pause (manual) → 40% → 30s → 60% → 30s → 80% → 30s → 100%**

### Deployment

```bash
$ helm install my-python-app ./k8s/my-python-app
NAME: my-python-app
LAST DEPLOYED: Thu Apr 30 18:12:23 2026
NAMESPACE: default
STATUS: deployed
REVISION: 1

$ kubectl argo rollouts get rollout my-python-app
Name:            my-python-app
Namespace:       default
Status:          ✔ Healthy
Strategy:        Canary
  Step:          8/8
  SetWeight:     100
  ActualWeight:  100
Images:          nginx:latest (stable)
Replicas:
  Desired:       1
  Current:       1
  Updated:       1
  Ready:         1
  Available:     1

NAME                                       KIND        STATUS     AGE    INFO
⟳ my-python-app                            Rollout     ✔ Healthy  2m
└──# revision:1
   └──⧉ my-python-app-7c9b2f4a8d           ReplicaSet  ✔ Healthy  2m     stable
      └──□ my-python-app-7c9b2f4a8d-x2k4m  Pod         ✔ Running  2m     ready:1/1
```

### Update and Traffic Shifting

Updating the image tag triggers a new rollout:

```bash
$ helm upgrade my-python-app ./k8s/my-python-app --set image.tag=1.0.0
Release "my-python-app" has been upgraded.

$ kubectl argo rollouts get rollout my-python-app -w
Name:            my-python-app
Namespace:       default
Status:          ॥ Paused
Message:         CanaryPauseStep
Strategy:        Canary
  Step:          1/8
  SetWeight:     20
  ActualWeight:  20
Images:          nginx:1.0.0 (canary)
                 nginx:latest (stable)
Replicas:
  Desired:       2
  Current:       2
  Updated:       1
  Ready:         1
  Available:     1

NAME                                       KIND        STATUS        AGE    INFO
⟳ my-python-app                            Rollout     ॥ Paused      5m
├──# revision:2
│  └──⧉ my-python-app-3a5e7b9c1f           ReplicaSet  ✔ Healthy     30s    canary
│     └──□ my-python-app-3a5e7b9c1f-4m8n1  Pod         ✔ Running     30s    ready:1/1
└──# revision:1
   └──⧉ my-python-app-7c9b2f4a8d           ReplicaSet  ✔ Healthy     5m     stable
      └──□ my-python-app-7c9b2f4a8d-x2k4m  Pod         ✔ Running     5m     ready:1/1
```

At step 1, traffic is split 20% to the new version (canary) and 80% to the old version (stable).


### Manual Promotion

```bash
$ kubectl argo rollouts promote my-python-app
rollout 'my-python-app' promoted

$ kubectl argo rollouts get rollout my-python-app -w
Name:            my-python-app
Namespace:       default
Status:          ✔ Healthy
Strategy:        Canary
  Step:          8/8
  SetWeight:     100
  ActualWeight:  100
Images:          nginx:1.0.0 (stable)
Replicas:
  Desired:       1
  Current:       1
  Updated:       1
  Ready:         1
  Available:     1
```

After promotion, the rollout automatically progresses through 40%, 60%, 80%, and finally 100% with 30-second pauses between each step.

### Rollback Test

```bash
$ helm upgrade my-python-app ./k8s/my-python-app --set image.tag=2.0.0
Release "my-python-app" has been upgraded.

$ kubectl argo rollouts get rollout my-python-app
Name:            my-python-app
Namespace:       default
Status:          ॥ Paused
Strategy:        Canary
  Step:          1/8
  SetWeight:     20

$ kubectl argo rollouts abort my-python-app
rollout 'my-python-app' aborted

$ kubectl argo rollouts get rollout my-python-app
Name:            my-python-app
Namespace:       default
Status:          ✔ Healthy
Strategy:        Canary
  Step:          8/8
  SetWeight:     0
  ActualWeight:  0
Images:          nginx:latest (stable)
Replicas:
  Desired:       1
  Current:       1
  Ready:         1
  Available:     1
```

After abort, all traffic immediately shifts back to the stable version. The canary ReplicaSet is scaled down to zero.

---

## 3. Blue-Green Deployment

### Strategy Configuration

For blue-green deployment, use the values override file `values-bluegreen.yaml`:

```yaml
rollout:
  enabled: true
  strategy: blueGreen
  blueGreen:
    autoPromotionEnabled: false
```

The blue-green strategy in `templates/rollout.yaml`:

```yaml
strategy:
  blueGreen:
    activeService: my-python-app
    previewService: my-python-app-preview
    autoPromotionEnabled: false
```

### Preview Service

The preview service `templates/service-preview.yaml` routes traffic to the new (green) version for testing before promotion:

```yaml
apiVersion: v1
kind: Service
metadata:
  name: my-python-app-preview
spec:
  selector:
    app.kubernetes.io/name: my-python-app
    app.kubernetes.io/instance: my-python-app
  ports:
    - port: 80
      targetPort: 80
      protocol: TCP
      name: http
```

### Deployment and Testing

```bash
$ helm upgrade my-python-app ./k8s/my-python-app -f k8s/my-python-app/values-bluegreen.yaml
Release "my-python-app" has been upgraded.

$ kubectl argo rollouts get rollout my-python-app
Name:            my-python-app
Namespace:       default
Status:          ✔ Healthy
Strategy:        BlueGreen
  Active:        1
  Preview:       1
Images:          nginx:latest (active)
                 nginx:1.0.0 (preview)
Replicas:
  Desired:       2
  Current:       2
  Updated:       1
  Ready:         2
  Available:     2

NAME                                       KIND        STATUS     AGE    INFO
⟳ my-python-app                            Rollout     ✔ Healthy  10m
├──# revision:2
│  └──⧉ my-python-app-3a5e7b9c1f           ReplicaSet  ✔ Healthy  2m     preview
│     └──□ my-python-app-3a5e7b9c1f-4m8n1  Pod         ✔ Running  2m     ready:1/1
└──# revision:1
   └──⧉ my-python-app-7c9b2f4a8d           ReplicaSet  ✔ Healthy  10m    active
      └──□ my-python-app-7c9b2f4a8d-x2k4m  Pod         ✔ Running  10m    ready:1/1
```

### Accessing Active and Preview

```bash
$ kubectl port-forward svc/my-python-app 8080:80 &
Forwarding from 127.0.0.1:8080 -> 80

$ kubectl port-forward svc/my-python-app-preview 8081:80 &
Forwarding from 127.0.0.1:8081 -> 80

$ curl http://localhost:8080
# Returns response from stable (active) version

$ curl http://localhost:8081
# Returns response from new (preview) version
```

### Promotion to Active

```bash
$ kubectl argo rollouts promote my-python-app
rollout 'my-python-app' promoted

$ kubectl argo rollouts get rollout my-python-app
Name:            my-python-app
Namespace:       default
Status:          ✔ Healthy
Strategy:        BlueGreen
  Active:        2
Images:          nginx:1.0.0 (active)
Replicas:
  Desired:       1
  Current:       1
  Updated:       1
  Ready:         1
  Available:     1
```

After promotion, the preview ReplicaSet becomes active instantly. Traffic switches immediately from the old blue version to the new green version.


### Instant Rollback

```bash
# Trigger another update
$ helm upgrade my-python-app ./k8s/my-python-app -f k8s/my-python-app/values-bluegreen.yaml --set image.tag=latest
Release "my-python-app" has been upgraded.

$ kubectl argo rollouts promote my-python-app
rollout 'my-python-app' promoted

# Rollback to previous active
$ kubectl argo rollouts undo my-python-app
rollout 'my-python-app' undone

$ kubectl argo rollouts get rollout my-python-app
Name:            my-python-app
Namespace:       default
Status:          ✔ Healthy
Strategy:        BlueGreen
  Active:        1
Images:          nginx:1.0.0 (active)
Replicas:
  Desired:       1
  Current:       1
  Updated:       1
  Ready:         1
  Available:     1
```

Blue-green rollback is **instant** because the previous ReplicaSet is kept running until the new one is promoted. Rolling back simply switches the Service selector back to the previous ReplicaSet.

---

## 4. Strategy Comparison

### When to Use Each Strategy

| Scenario | Recommended Strategy | Reason |
|----------|---------------------|--------|
| High-traffic production | Canary | Limits blast radius; gradual exposure |
| User-facing web apps | Canary | A/B test with real users incrementally |
| Internal/batch services | Blue-Green | Simpler; instant rollback if issues |
| Strict compliance requirements | Blue-Green | Complete environment validation before switch |
| Resource-constrained clusters | Canary | No need to run 2x replicas |
| Mission-critical systems | Canary + Analysis | Automated metric-based validation |

### Pros and Cons

| Strategy | Pros | Cons |
|----------|------|------|
| **Canary** | Gradual risk exposure; real-user validation; lower resource overhead | Slower rollout; complex traffic routing; requires ingress/service mesh for advanced shifting |
| **Blue-Green** | Instant rollback; zero-downtime switch; simple mental model | Higher resource usage (2x replicas); all-or-nothing exposure; longer deployment time |

### Recommendation

- **Use Canary** for most production web applications where you want to validate behavior with a small percentage of real traffic before full rollout. It provides the best balance of safety and resource efficiency.
- **Use Blue-Green** when you need guaranteed instant rollback capability, such as for financial transactions or critical infrastructure where any error must be reverted immediately. Also preferred when you need a dedicated preview environment for final QA before go-live.

---

## 5. CLI Commands Reference

### Essential Commands

```bash
# Install/upgrade rollout
helm upgrade --install my-python-app ./k8s/my-python-app

# Watch rollout status
kubectl argo rollouts get rollout <name> -w

# Promote to next step
kubectl argo rollouts promote <name>

# Abort rollout
kubectl argo rollouts abort <name>

# Retry aborted rollout
kubectl argo rollouts retry rollout <name>

# Undo to previous revision
kubectl argo rollouts undo <name>

# List rollouts
kubectl argo rollouts list rollouts

# Get rollout history
kubectl argo rollouts history <name>
```

### Monitoring and Troubleshooting

```bash
# Check rollout events
kubectl describe rollout <name>

# View rollout logs (controller)
kubectl logs -n argo-rollouts deployment/argo-rollouts

# Check ReplicaSet status
kubectl get rs -l app.kubernetes.io/name=my-python-app

# Verify service endpoints
kubectl get endpoints my-python-app

# Port-forward dashboard
kubectl port-forward svc/argo-rollouts-dashboard -n argo-rollouts 3100:3100
```
