# Lab 15 — StatefulSets & Persistent Storage

![difficulty](https://img.shields.io/badge/difficulty-advanced-red)
![topic](https://img.shields.io/badge/topic-StatefulSets-blue)
![points](https://img.shields.io/badge/points-10%2B2.5-orange)
![tech](https://img.shields.io/badge/tech-StatefulSet%20%7C%20PVC-informational)

> Manage stateful applications in Kubernetes with stable network identities and persistent per-pod storage.

## Overview

While Deployments and Rollouts are perfect for stateless applications, many real-world applications need stable identities and persistent storage per instance. StatefulSets provide guarantees about ordering, uniqueness, and storage that other controllers cannot offer.

**What You'll Learn:**
- StatefulSet vs Deployment: when to use which
- Stable network identities and pod naming
- VolumeClaimTemplates for per-pod storage
- Headless Services for direct pod access
- Ordered vs parallel pod management

**Building On:** Your Helm chart with visits counter from Lab 12. Note: StatefulSets serve a different purpose than Rollouts (Lab 14) - use Rollouts for progressive delivery of stateless apps, StatefulSets for stateful apps.

**Tech Stack:** StatefulSets | Headless Services | VolumeClaimTemplates | Persistent Volumes

---

## Tasks

### Task 1 — StatefulSet Concepts (2 pts)

**Objective:** Understand when and why to use StatefulSets.

**Requirements:**

1. **Study StatefulSet Guarantees**
   - Stable, unique network identifiers
   - Stable, persistent storage
   - Ordered, graceful deployment and scaling

2. **Compare with Deployments**
   - Document key differences
   - When to use Deployment vs StatefulSet
   - Examples of stateful workloads

3. **Understand Headless Services**
   - What is a headless service (`clusterIP: None`)?
   - How DNS works with StatefulSets

<details>
<summary>💡 Hints</summary>

**StatefulSet Use Cases:**
- Databases (MySQL, PostgreSQL, MongoDB)
- Message queues (Kafka, RabbitMQ)
- Distributed systems (Elasticsearch, Cassandra)

**Key Differences:**

| Feature | Deployment | StatefulSet |
|---------|------------|-------------|
| Pod Names | Random suffix | Ordered index (pod-0, pod-1) |
| Storage | Shared PVC | Per-pod PVC via templates |
| Scaling | Any order | Ordered (0→1→2) |
| Network ID | Random | Stable DNS name |

**Headless Service:**
A Service with `clusterIP: None` creates DNS records for each pod:
- `pod-0.service-name.namespace.svc.cluster.local`

**Resources:**
- [StatefulSet Basics](https://kubernetes.io/docs/tutorials/stateful-application/basic-stateful-set/)
- [StatefulSet Concepts](https://kubernetes.io/docs/concepts/workloads/controllers/statefulset/)

</details>

---

### Task 2 — Convert Deployment to StatefulSet (3 pts)

**Objective:** Transform your Helm chart to use a StatefulSet with per-pod storage.

**Requirements:**

1. **Create StatefulSet Template**
   - Create `statefulset.yaml` (keep rollout.yaml for reference)
   - Add `serviceName` field pointing to headless service
   - Configure `volumeClaimTemplates` for per-pod storage

2. **Create Headless Service**
   - Create a new service with `clusterIP: None`
   - Keep your existing service for external access

3. **Configure VolumeClaimTemplates**
   - Each pod gets its own PVC automatically
   - Configure storage class and size via values

4. **Deploy and Verify**
   - Pods named with ordinal suffixes (app-0, app-1, app-2)
   - Each pod has its own PVC

<details>
<summary>💡 Hints</summary>

**StatefulSet Structure:**
```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: {{ include "mychart.fullname" . }}
spec:
  serviceName: {{ include "mychart.fullname" . }}-headless
  replicas: {{ .Values.replicaCount }}
  selector:
    matchLabels:
      {{- include "mychart.selectorLabels" . | nindent 6 }}
  template:
    # Same as Deployment pod template
  volumeClaimTemplates:
    - metadata:
        name: data
      spec:
        accessModes: [ "ReadWriteOnce" ]
        resources:
          requests:
            storage: {{ .Values.persistence.size }}
```

**Headless Service:**
```yaml
apiVersion: v1
kind: Service
metadata:
  name: {{ include "mychart.fullname" . }}-headless
spec:
  clusterIP: None
  selector:
    {{- include "mychart.selectorLabels" . | nindent 4 }}
  ports:
    - port: {{ .Values.service.port }}
```

**Verification:**
```bash
kubectl get statefulset
kubectl get pods
kubectl get pvc
```

</details>

---

### Task 3 — Headless Service & Pod Identity (3 pts)

**Objective:** Verify stable network identities and per-pod storage isolation.

**Requirements:**

1. **Test DNS Resolution**
   - Exec into a pod
   - Resolve other pods via DNS
   - Document the DNS naming pattern

2. **Test Per-Pod Storage**
   - Access your app through each pod
   - Verify each pod maintains its own visit count
   - Demonstrate isolation between pods

3. **Test Persistence**
   - Note visit counts for each pod
   - Delete one pod (not the StatefulSet)
   - Verify the visit count is preserved after restart

<details>
<summary>💡 Hints</summary>

**DNS Resolution Test:**
```bash
kubectl exec -it <statefulset>-0 -- /bin/sh
nslookup <statefulset>-1.<headless-service>
```

**Per-Pod Visit Count Test:**
```bash
kubectl port-forward pod/<statefulset>-0 8080:8000 &
kubectl port-forward pod/<statefulset>-1 8081:8000 &
curl localhost:8080/visits
curl localhost:8081/visits
```

**Persistence Test:**
```bash
kubectl exec <statefulset>-0 -- cat /data/visits
kubectl delete pod <statefulset>-0
# Wait for restart
kubectl exec <statefulset>-0 -- cat /data/visits
```

</details>

---

### Task 4 — Documentation (2 pts)

**Objective:** Document your StatefulSet implementation.

**Create `k8s/STATEFULSET.md` with:**

1. **StatefulSet Overview** - Why StatefulSet, differences from Deployment
2. **Resource Verification** - Output of `kubectl get po,sts,svc,pvc`
3. **Network Identity** - DNS resolution outputs
4. **Per-Pod Storage Evidence** - Different visit counts per pod
5. **Persistence Test** - Data survives pod deletion

---

## Bonus Task — Update Strategies (2.5 pts)

**Objective:** Explore StatefulSet update strategies.

**Requirements:**

1. **Implement Partitioned Rolling Update**
   - Configure `updateStrategy` with `partition`
   - Update only pods with ordinal >= partition value

2. **Test OnDelete Strategy**
   - Pods only update when manually deleted
   - Document use cases

<details>
<summary>💡 Hints</summary>

**Rolling Update with Partition:**
```yaml
spec:
  updateStrategy:
    type: RollingUpdate
    rollingUpdate:
      partition: 2
```

**OnDelete Strategy:**
```yaml
spec:
  updateStrategy:
    type: OnDelete
```

**Resources:**
- [StatefulSet Update Strategies](https://kubernetes.io/docs/concepts/workloads/controllers/statefulset/#update-strategies)

</details>

---

## Checklist

- [ ] StatefulSet guarantees documented
- [ ] `statefulset.yaml` created with volumeClaimTemplates
- [ ] Headless service created
- [ ] Per-pod PVCs verified
- [ ] DNS resolution tested
- [ ] Per-pod storage isolation proven
- [ ] Persistence test passed
- [ ] `k8s/STATEFULSET.md` complete

---

## Rubric

| Criteria | Points |
|----------|--------|
| **Concepts** | 2 pts |
| **Implementation** | 3 pts |
| **Identity & Storage** | 3 pts |
| **Documentation** | 2 pts |
| **Bonus** | 2.5 pts |
| **Total** | 12.5 pts |

---

## Resources

<details>
<summary>📚 Documentation</summary>

- [StatefulSets](https://kubernetes.io/docs/concepts/workloads/controllers/statefulset/)
- [Headless Services](https://kubernetes.io/docs/concepts/services-networking/service/#headless-services)
- [VolumeClaimTemplates](https://kubernetes.io/docs/concepts/workloads/controllers/statefulset/#volume-claim-templates)

</details>

---

## Looking Ahead

- **Lab 16:** Monitoring your StatefulSet with Prometheus/Grafana

---

**Good luck!** 💾

> **Remember:** StatefulSets are for applications needing stable identity and storage. For progressive delivery of stateless apps, use Rollouts (Lab 14).
