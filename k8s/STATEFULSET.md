# Lab 15 — StatefulSets & Persistent Storage

## 1. StatefulSet Overview

StatefulSet was chosen for this lab because the application needs:
- stable per-pod identity (`<name>-0`, `<name>-1`, `<name>-2`)
- stable per-pod persistent storage
- ordered scale/start behavior

### Deployment vs StatefulSet

| Feature | Deployment | StatefulSet |
|---|---|---|
| Pod naming | random suffix | deterministic ordinal suffix |
| Storage | shared/optional PVC | per-pod PVC via `volumeClaimTemplates` |
| Network identity | generic service load-balancing | stable pod DNS via headless service |
| Scaling | parallel/unspecified order | ordered by default (`OrderedReady`) |

### Headless Service and DNS

Headless service is configured with:
- `clusterIP: None`
- selector matching StatefulSet pods

This enables DNS names like:
- `<statefulset-name>-0.<headless-service>.<namespace>.svc.cluster.local`
- `<statefulset-name>-1.<headless-service>.<namespace>.svc.cluster.local`

---

## 2. Resource Verification

### Helm/stateful files

- StatefulSet template: `k8s/devops-info-service/templates/statefulset.yaml`
- Headless service: `k8s/devops-info-service/templates/service-headless.yaml`
- Stateful values profile: `k8s/devops-info-service/values-statefulset.yaml`

### Deploy commands

```bash
helm upgrade --install devops-stateful k8s/devops-info-service \
  -n dev --create-namespace \
  -f k8s/devops-info-service/values-dev.yaml \
  -f k8s/devops-info-service/values-statefulset.yaml
```

### Verification commands

```bash
kubectl get po,sts,svc,pvc -n dev
```

Expected patterns:
- StatefulSet exists (e.g., `devops-stateful-devops-info-service`)
- Pods named `...-0`, `...-1`, ...
- one PVC per pod from `volumeClaimTemplates`
- both external service and `-headless` service present

Example output shape:

```text
NAME                                            READY   STATUS    RESTARTS   AGE
pod/devops-stateful-devops-info-service-0       1/1     Running   0          3m

NAME                                                       READY   AGE
statefulset.apps/devops-stateful-devops-info-service      1/1     3m

NAME                                                TYPE        CLUSTER-IP   EXTERNAL-IP   PORT(S)        AGE
service/devops-stateful-devops-info-service         NodePort    10.x.x.x     <none>        80:30084/TCP   3m
service/devops-stateful-devops-info-service-headless ClusterIP None          <none>        80/TCP         3m

NAME                                                     STATUS   VOLUME   CAPACITY   ACCESS MODES   STORAGECLASS   AGE
persistentvolumeclaim/data-devops-stateful-devops-info-service-0 Bound    pvc-... 100Mi      RWO            standard       3m
```

---

## 3. Network Identity

### DNS resolution test

```bash
kubectl exec -it devops-stateful-devops-info-service-0 -n dev -- /bin/sh
nslookup devops-stateful-devops-info-service-0.devops-stateful-devops-info-service-headless.dev.svc.cluster.local
```

Optional cross-pod check (if replicas > 1):

```bash
nslookup devops-stateful-devops-info-service-1.devops-stateful-devops-info-service-headless.dev.svc.cluster.local
```

Expected:
- each pod resolves by stable DNS name
- names remain stable across pod restarts

---

## 4. Per-Pod Storage Evidence

Each pod gets a dedicated PVC via `volumeClaimTemplates`. The visits file is stored at `/data/visits` in each pod and is isolated by pod ordinal.

### Commands

```bash
# If using multiple replicas, check each pod separately
kubectl exec devops-stateful-devops-info-service-0 -n dev -- cat /data/visits
kubectl exec devops-stateful-devops-info-service-1 -n dev -- cat /data/visits
```

For HTTP-level check:

```bash
kubectl port-forward pod/devops-stateful-devops-info-service-0 -n dev 8080:5000
curl -s http://127.0.0.1:8080/visits
```

Repeat for another pod on another local port to show independent counters.

---

## 5. Persistence Test

### Procedure

1. Record current visit count:
```bash
kubectl exec devops-stateful-devops-info-service-0 -n dev -- cat /data/visits
```

2. Delete pod 0 (not StatefulSet):
```bash
kubectl delete pod devops-stateful-devops-info-service-0 -n dev
kubectl get pods -n dev -w
```

3. After pod is recreated, check count again:
```bash
kubectl exec devops-stateful-devops-info-service-0 -n dev -- cat /data/visits
```

Expected result:
- value before and after deletion is preserved
- demonstrates PVC reattachment and data persistence

---

## Manual Evidence to Capture for Submission

1. Output of:
   - `kubectl get po,sts,svc,pvc -n dev`
2. DNS proof:
   - `nslookup` output for pod DNS via headless service
3. Per-pod storage:
   - `/data/visits` from at least two pods (if replicas > 1)
4. Persistence test:
   - visits value before pod delete
   - pod delete command/output
   - visits value after recreation

