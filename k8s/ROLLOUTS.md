# ROLLOUTS.md — Argo Rollouts Progressive Delivery

## 1. Argo Rollouts Setup

### Installation
Argo Rollouts controller was installed in the cluster:

```bash
kubectl create namespace argo-rollouts
kubectl apply -n argo-rollouts -f https://github.com/argoproj/argo-rollouts/releases/latest/download/install.yaml
````

Verification:

```bash
kubectl get pods -n argo-rollouts
```

All controller pods are running successfully.

### Kubectl Plugin

Installed kubectl plugin:

```bash
kubectl argo rollouts version
```

### Dashboard

Dashboard installed and accessed via port-forward:

```bash
kubectl port-forward svc/argo-rollouts-dashboard -n argo-rollouts 3100:3100
```

URL:

```
http://localhost:3100
```

---

## 2. Canary Deployment

### Strategy Configuration

The application was converted from Deployment to Rollout with canary strategy:

* Progressive traffic shifting
* Manual and automatic pauses
* Gradual rollout steps

### Canary Steps

Configured rollout steps:

* 20% traffic → manual pause
* 40% traffic → pause 30s
* 60% traffic → pause 30s
* 80% traffic → pause 30s
* 100% traffic

### Behavior Observed

* New ReplicaSet created for each update
* Traffic gradually shifted between stable and canary pods
* Intermediate pauses observed in dashboard
* Final state: 100% traffic to new version

### Promotion

Manual promotion used during first pause:

```bash
kubectl argo rollouts promote myapp-dev -n dev
```

### Rollback Test

Rollback was tested using abort command:

```bash
kubectl argo rollouts abort myapp-dev -n dev
```

Result:

* Traffic immediately reverted to stable version
* New ReplicaSet scaled down
* No downtime observed

---

## 3. Blue-Green Deployment

### Strategy Configuration

Blue-green strategy implemented with:

* Active service (production traffic)
* Preview service (new version testing)
* Manual promotion control

### Services

* `myapp-dev` → active service
* `myapp-dev-preview` → preview service

### Flow

1. Initial version deployed (blue)
2. New version created (green)
3. Preview service used to validate new version
4. Manual promotion applied

### Access

```bash
kubectl port-forward svc/myapp-dev 8080:80
kubectl port-forward svc/myapp-dev-preview 8081:80
```

### Promotion

```bash
kubectl argo rollouts promote myapp-dev -n dev
```

### Rollback Behavior

* Rollback is instantaneous
* Traffic switches immediately back to previous version
* No gradual transition (unlike canary)

---

## 4. Strategy Comparison

### Canary Deployment

**Advantages:**

* Gradual traffic shift
* Safer for production
* Early detection of issues
* Fine-grained control

**Disadvantages:**

* Slower rollout
* More complex configuration

---

### Blue-Green Deployment

**Advantages:**

* Instant switch between versions
* Simple rollback
* Clear separation of environments

**Disadvantages:**

* Requires double resources
* No gradual validation under load

---

### Recommendation

* Use **Canary** for production APIs and user-facing services
* Use **Blue-Green** for critical releases requiring instant rollback
* Use Canary when risk needs to be minimized gradually

---

## 5. CLI Commands Reference

### Rollout Monitoring

```bash
kubectl argo rollouts get rollout myapp-dev -n dev -w
```

### Promotion

```bash
kubectl argo rollouts promote myapp-dev -n dev
```

### Abort Rollout

```bash
kubectl argo rollouts abort myapp-dev -n dev
```

### Restart Rollout

```bash
kubectl argo rollouts restart myapp-dev -n dev
```

### Status Check

```bash
kubectl get rollout -n dev
kubectl get rs -n dev
kubectl get pods -n dev
```

---

## 6. Observations

* Canary rollout successfully performed with step-based traffic shifting
* Blue-green deployment verified via preview service
* Rollback operations are instant and reliable
* Argo Rollouts dashboard clearly visualizes deployment state
* System remains stable during all transitions

---

## Conclusion

Argo Rollouts provides safe progressive delivery mechanisms:

* Canary → gradual rollout with controlled exposure
* Blue-Green → instant switching between environments

Both strategies were successfully implemented and tested in the cluster.