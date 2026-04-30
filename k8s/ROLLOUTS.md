## 1. Argo Rollouts Setup

### Install the Controller

```bash
kubectl create namespace argo-rollouts
kubectl apply -n argo-rollouts -f https://github.com/argoproj/argo-rollouts/releases/latest/download/install.yaml
```

### Verify the Controller Is Running

```bash
kubectl get pods -n argo-rollouts
```

Expected output:

```
NAME                             READY   STATUS    RESTARTS   AGE
argo-rollouts-xxxxxxxxxx-xxxxx   1/1     Running   0          1m
```

### Install the kubectl Plugin

**Using Homebrew (macOS/Linux):**

```bash
brew install argoproj/tap/kubectl-argo-rollouts
```

**Manual install (Linux):**

```bash
curl -LO https://github.com/argoproj/argo-rollouts/releases/latest/download/kubectl-argo-rollouts-linux-amd64
chmod +x kubectl-argo-rollouts-linux-amd64
sudo mv kubectl-argo-rollouts-linux-amd64 /usr/local/bin/kubectl-argo-rollouts
```

Verify:

```bash
kubectl argo rollouts version
```

### Access the Dashboard

```bash
kubectl argo rollouts dashboard
```

Then open [http://localhost:3100](http://localhost:3100) in your browser.

> ![Dashboard screenshot](./screenshots/dashboard.png)
> _Argo Rollouts dashboard showing active rollouts and their step progress._

---

## 2. Rollout vs Deployment

The `Rollout` CRD is a drop-in replacement for a standard Kubernetes `Deployment`, but with advanced deployment strategy support baked in.

| Feature                  | `Deployment`                                         | `Rollout`                                                                    |
| ------------------------ | ---------------------------------------------------- | ---------------------------------------------------------------------------- |
| **API Version**          | `apps/v1`                                            | `argoproj.io/v1alpha1`                                                       |
| **Kind**                 | `Deployment`                                         | `Rollout`                                                                    |
| **Strategy field**       | `spec.strategy` (`RollingUpdate`, `Recreate`)        | `spec.strategy` (`canary`, `blueGreen`)                                      |
| **Traffic management**   | Basic rolling update; no fine-grained weight control | Weighted traffic splitting, header-based routing (with ingress/service mesh) |
| **Rollback**             | `kubectl rollout undo`                               | `kubectl argo rollouts abort` + `undo`, or automatic on failure              |
| **Pause / resume**       | Not supported natively                               | First-class: manual pauses between steps                                     |
| **Analysis / metrics**   | Not supported                                        | Supports `AnalysisRun` for automated pass/fail gates                         |
| **Preview environments** | Not supported                                        | Native blue-green preview service support                                    |

> **Migration note:** The pod template (`spec.template`) is identical between a `Deployment` and a `Rollout` — you only need to change the `apiVersion`, `kind`, and `spec.strategy` fields.

---

## 3. Canary Deployment

### How It Works

A canary deployment gradually shifts traffic from the **stable** (old) version to the **canary** (new) version in incremental steps. At each step you can pause for manual verification or a fixed duration before proceeding.

### Strategy Configuration

```yaml
strategy:
  canary:
    steps:
      - setWeight: 20
      - pause: {} # manual gate — requires human promotion
      - setWeight: 40
      - pause:
          duration: 30s
      - setWeight: 60
      - pause:
          duration: 30s
      - setWeight: 80
      - pause:
          duration: 30s
```

#### Step Breakdown

| Step            | Traffic to Canary | Pause Type       | Purpose                                          |
| --------------- | ----------------- | ---------------- | ------------------------------------------------ |
| `setWeight: 20` | 20%               | —                | Initial small slice for early validation         |
| `pause: {}`     | 20%               | **Manual**       | Operator inspects metrics/logs before continuing |
| `setWeight: 40` | 40%               | —                | Widen canary audience                            |
| `pause: 30s`    | 40%               | Automatic (30 s) | Short soak time                                  |
| `setWeight: 60` | 60%               | —                | Majority of traffic on new version               |
| `pause: 30s`    | 60%               | Automatic (30 s) | Short soak time                                  |
| `setWeight: 80` | 80%               | —                | Almost full rollout                              |
| `pause: 30s`    | 80%               | Automatic (30 s) | Final soak before full promotion                 |

After all steps complete the rollout automatically promotes and 100% of traffic goes to the new version.

### Enable Canary via Helm

```bash
helm upgrade app-python ./k8s/app-python \
  --set rollout.enabled=true \
  --set rollout.strategy=canary \
  --set image.tag=v2.0.0
```

### Watching a Canary Rollout

```bash
# Live status in terminal
kubectl argo rollouts get rollout app-python --watch

# Or via the dashboard
kubectl argo rollouts dashboard
```

> ![Canary rollout progress](./screenshots/canary-steps.png)
> _Terminal output showing canary step progress and current weight._

### Promoting (Advancing Past a Manual Pause)

```bash
# Advance one step at a time
kubectl argo rollouts promote app-python

# Skip all remaining steps and fully promote immediately
kubectl argo rollouts promote app-python --full
```

### Aborting a Canary

```bash
kubectl argo rollouts abort app-python
```

This sets the rollout to a **Degraded** state and scales the canary down to 0, restoring 100% traffic to the stable version.

### Testing Rollback

1. Deploy a bad image:

```bash
helm upgrade app-python ./k8s/app-python \
  --set rollout.enabled=true \
  --set rollout.strategy=canary \
  --set image.tag=broken-tag
```

2. Watch the rollout reach the manual pause, then abort:

```bash
kubectl argo rollouts abort app-python
```

3. Undo to the previous stable revision:

```bash
kubectl argo rollouts undo app-python
```

---

## 4. Blue-Green Deployment

### How It Works

Blue-green maintains **two full environments** simultaneously:

- **Active (blue)** — the live production environment receiving all traffic.
- **Preview (green)** — the new version running in parallel, accessible via a separate preview service for testing.

Promotion switches the active service's selector to point to the new pods atomically.

### Strategy Configuration

```yaml
strategy:
  blueGreen:
    activeService: app-python # points to current production pods
    previewService: app-python-preview # points to new version pods
    autoPromotionEnabled: false # requires manual promotion
```

With `autoPromotionEnabled: false`, the new version is deployed and ready on the preview service, but traffic is **not** switched until you explicitly promote.

### Enable Blue-Green via Helm

```bash
helm upgrade app-python ./k8s/app-python \
  --set rollout.enabled=true \
  --set rollout.strategy=blueGreen \
  --set image.tag=v2.0.0
```

This also renders the `preview-service.yaml` template, creating the `app-python-preview` Service automatically.

### Watching a Blue-Green Rollout

```bash
kubectl argo rollouts get rollout app-python --watch
```

> ![Blue-green rollout](./screenshots/bluegreen-preview.png)
> _Dashboard view showing both active (blue) and preview (green) replica sets side-by-side._

### Accessing the Preview Service

```bash
# Port-forward the preview service to test the new version
kubectl port-forward svc/app-python-preview 8080:80
```

Then visit [http://localhost:8080](http://localhost:8080) to validate the new version before promotion.

### Promoting to Active

Once you're satisfied with the preview:

```bash
kubectl argo rollouts promote app-python
```

This updates the **active** service selector to route traffic to the new (green) pods. The old (blue) pods are kept briefly then scaled down.

### Aborting a Blue-Green Rollout

```bash
kubectl argo rollouts abort app-python
```

The active service continues to serve the old version; the preview pods are scaled down.

---

## 5. Strategy Comparison

### Pros & Cons

|                     | **Canary**                                       | **Blue-Green**                                          |
| ------------------- | ------------------------------------------------ | ------------------------------------------------------- |
| **Resource usage**  | Low — only a fraction of new pods run at a time  | High — two full environments run simultaneously         |
| **Traffic control** | Granular percentage-based weight shifting        | Binary switch: 0% or 100% to new version                |
| **Rollback speed**  | Fast (`abort` scales canary to 0)                | Instant (switch selector back to old pods)              |
| **Risk**            | Lower — small user subset sees new version first | Medium — all users switch at once on promotion          |
| **Testing in prod** | Real production traffic on canary subset         | Isolated preview service before any production exposure |
| **Complexity**      | Medium — requires traffic splitting support      | Low — simple service selector swap                      |
| **Downtime**        | Zero                                             | Zero                                                    |

### When to Use Each

| Scenario                                              | Recommended Strategy              |
| ----------------------------------------------------- | --------------------------------- |
| Gradually validating a risky change with real traffic | **Canary**                        |
| A/B testing or feature flag validation at scale       | **Canary**                        |
| Complete environment swap with pre-promotion QA       | **Blue-Green**                    |
| Instant rollback capability is critical               | **Blue-Green**                    |
| Limited cluster resources                             | **Canary**                        |
| Microservice with service mesh (Istio/Linkerd)        | **Canary** (with traffic routing) |

---

## 6. CLI Commands Reference

### Rollout Management

| Command                                            | Description                                |
| -------------------------------------------------- | ------------------------------------------ |
| `kubectl argo rollouts list rollouts`              | List all rollouts in the current namespace |
| `kubectl argo rollouts get rollout <name>`         | Show rollout status and history            |
| `kubectl argo rollouts get rollout <name> --watch` | Live-watch rollout status                  |
| `kubectl argo rollouts promote <name>`             | Advance past a manual pause (one step)     |
| `kubectl argo rollouts promote <name> --full`      | Skip all steps and fully promote           |
| `kubectl argo rollouts abort <name>`               | Abort the current rollout, restore stable  |
| `kubectl argo rollouts undo <name>`                | Roll back to the previous revision         |
| `kubectl argo rollouts retry rollout <name>`       | Retry an aborted or degraded rollout       |
| `kubectl argo rollouts pause <name>`               | Manually pause a running rollout           |
| `kubectl argo rollouts resume <name>`              | Resume a paused rollout                    |

### History & Revisions

| Command                                               | Description                      |
| ----------------------------------------------------- | -------------------------------- |
| `kubectl argo rollouts history rollout <name>`        | Show revision history            |
| `kubectl argo rollouts undo <name> --to-revision=<N>` | Roll back to a specific revision |

### Dashboard

| Command                                       | Description                        |
| --------------------------------------------- | ---------------------------------- |
| `kubectl argo rollouts dashboard`             | Start local dashboard on port 3100 |
| `kubectl argo rollouts dashboard --port 8080` | Start dashboard on a custom port   |

### Helm Integration

| Command                                                                                      | Description                                |
| -------------------------------------------------------------------------------------------- | ------------------------------------------ |
| `helm upgrade <release> <chart> --set rollout.enabled=true --set rollout.strategy=canary`    | Enable canary rollout via Helm             |
| `helm upgrade <release> <chart> --set rollout.enabled=true --set rollout.strategy=blueGreen` | Enable blue-green rollout via Helm         |
| `helm upgrade <release> <chart> --set rollout.enabled=false`                                 | Disable rollout (uses standard Deployment) |
