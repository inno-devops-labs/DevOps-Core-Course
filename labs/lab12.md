# Lab 12 — ConfigMaps & Persistent Volumes

![difficulty](https://img.shields.io/badge/difficulty-intermediate-yellow)
![topic](https://img.shields.io/badge/topic-Configuration%20%26%20Storage-blue)
![points](https://img.shields.io/badge/points-10%2B2.5-orange)
![tech](https://img.shields.io/badge/tech-ConfigMaps%20%7C%20PVC-informational)

> Externalize application configuration with ConfigMaps and ensure data persistence with Persistent Volumes.

## Overview

Production applications need externalized configuration and persistent storage. ConfigMaps decouple configuration from container images, enabling the same image to run in different environments. Persistent Volumes ensure your application data survives pod restarts and rescheduling.

**What You'll Learn:**
- ConfigMap creation and mounting strategies
- File-based vs environment variable configuration
- Persistent Volume Claims (PVC) in Kubernetes
- Volume mounting and data persistence
- Configuration best practices

**Building On:** Your Helm chart from Lab 11 will be extended with ConfigMaps and persistent storage.

**Tech Stack:** Kubernetes ConfigMaps | PersistentVolumeClaim | Helm | Volume Mounts

---

## Tasks

### Task 1 — Application Persistence Upgrade (2 pts)

**Objective:** Modify your application to track and persist visit counts.

**Requirements:**

1. **Add Visits Counter Logic**
   - Implement a counter that increments on each request to the root endpoint
   - Store the counter value in a file (e.g., `/data/visits`)
   - Create a new `/visits` endpoint that returns the current count

2. **Update Application Code**
   - Read counter from file on startup (default to 0 if file doesn't exist)
   - Increment and save on each root endpoint access
   - Handle concurrent access appropriately

3. **Test Locally with Docker**
   - Update `docker-compose.yml` to mount a volume for the visits file
   - Verify the counter persists across container restarts
   - Update your application's `README.md`

<details>
<summary>💡 Hints</summary>

**Implementation Pattern:**
```
Request to / → Read counter from file → Increment → Write back → Return response
Request to /visits → Read counter from file → Return count
```

**File-Based Counter:**
- Use a simple text file or JSON
- Handle file not found gracefully
- Consider atomic write operations

**Docker Compose Volume:**
```yaml
volumes:
  - ./data:/app/data
```

**Testing:**
1. Start container
2. Access root endpoint multiple times
3. Check file on host: `cat ./data/visits`
4. Restart container
5. Verify counter continues from last value

**Thread Safety:**
For a simple counter, file locking or atomic operations help prevent race conditions. For this lab, basic file read/write is acceptable.

</details>

---

### Task 2 — ConfigMaps (3 pts)

**Objective:** Externalize application configuration using Kubernetes ConfigMaps.

**Requirements:**

1. **Create Configuration File**
   - Create a `files/` directory in your Helm chart
   - Add `config.json` with application configuration:
     - Application name
     - Environment (dev/prod)
     - Feature flags or settings

2. **Create ConfigMap Template**
   - Add `templates/configmap.yaml` to your Helm chart
   - Use `.Files.Get` to load the config file content
   - Include proper metadata and labels

3. **Mount ConfigMap as File**
   - Update deployment to mount ConfigMap as a volume
   - Mount at a specific path (e.g., `/config/config.json`)
   - Verify the file is accessible inside the pod

4. **Use ConfigMap as Environment Variables**
   - Create a second ConfigMap with key-value pairs
   - Use `envFrom` with `configMapRef` to inject all keys
   - Verify environment variables in the pod

<details>
<summary>💡 Hints</summary>

**ConfigMap from File:**
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: {{ include "mychart.fullname" . }}-config
data:
  config.json: |-
{{ .Files.Get "files/config.json" | indent 4 }}
```

**ConfigMap for Env Vars:**
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: {{ include "mychart.fullname" . }}-env
data:
  APP_ENV: {{ .Values.environment | quote }}
  LOG_LEVEL: {{ .Values.logLevel | quote }}
```

**Volume Mount Pattern:**
In deployment spec:
```yaml
volumes:
  - name: config-volume
    configMap:
      name: config-name
containers:
  - volumeMounts:
      - name: config-volume
        mountPath: /config
```

**Environment Variables:**
```yaml
envFrom:
  - configMapRef:
      name: {{ include "mychart.fullname" . }}-env
```

**Verification:**
```bash
kubectl exec <pod> -- cat /config/config.json
kubectl exec <pod> -- printenv | grep APP_
```

**Resources:**
- [ConfigMaps](https://kubernetes.io/docs/concepts/configuration/configmap/)
- [Configure Pod with ConfigMap](https://kubernetes.io/docs/tasks/configure-pod-container/configure-pod-configmap/)

</details>

---

### Task 3 — Persistent Volumes (3 pts)

**Objective:** Implement persistent storage for your application's visit counter.

**Requirements:**

1. **Create PersistentVolumeClaim**
   - Add `templates/pvc.yaml` to your Helm chart
   - Request appropriate storage size (e.g., 100Mi)
   - Use `ReadWriteOnce` access mode
   - Make storage class configurable via values

2. **Mount PVC to Deployment**
   - Add volume referencing the PVC
   - Mount at your data directory (e.g., `/data`)
   - Ensure your application writes visits file there

3. **Verify Persistence**
   - Deploy the application
   - Access root endpoint multiple times
   - Delete the pod (not the deployment)
   - Verify the new pod has the same counter value

4. **Test Data Survival**
   - Check visits count before pod deletion
   - Delete pod: `kubectl delete pod <pod-name>`
   - Wait for new pod to start
   - Verify visits count is preserved

<details>
<summary>💡 Hints</summary>

**PVC Template:**
```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: {{ include "mychart.fullname" . }}-data
  labels:
    {{- include "mychart.labels" . | nindent 4 }}
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: {{ .Values.persistence.size }}
  {{- if .Values.persistence.storageClass }}
  storageClassName: {{ .Values.persistence.storageClass }}
  {{- end }}
```

**Values.yaml:**
```yaml
persistence:
  enabled: true
  size: 100Mi
  storageClass: ""  # Use default
```

**Mounting PVC:**
```yaml
volumes:
  - name: data-volume
    persistentVolumeClaim:
      claimName: {{ include "mychart.fullname" . }}-data
containers:
  - volumeMounts:
      - name: data-volume
        mountPath: /data
```

**Minikube Storage:**
Minikube provides a default storage class that provisions hostPath volumes automatically.

**Verification Commands:**
```bash
kubectl get pvc
kubectl describe pvc <pvc-name>
kubectl exec <pod> -- cat /data/visits
```

**Resources:**
- [Persistent Volumes](https://kubernetes.io/docs/concepts/storage/persistent-volumes/)
- [Configure Pod with PVC](https://kubernetes.io/docs/tasks/configure-pod-container/configure-persistent-volume-storage/)

</details>

---

### Task 4 — Documentation (2 pts)

**Objective:** Document your ConfigMap and persistence implementation.

**Create `k8s/CONFIGMAPS.md` with:**

1. **Application Changes**
   - Description of visits counter implementation
   - New endpoint documentation
   - Local testing evidence with Docker

2. **ConfigMap Implementation**
   - ConfigMap template structure
   - `config.json` content
   - How ConfigMap is mounted as file
   - How ConfigMap provides environment variables
   - Verification outputs

3. **Persistent Volume**
   - PVC configuration explanation
   - Access modes and storage class discussion
   - Volume mount configuration
   - Persistence test evidence:
     - Counter value before pod deletion
     - Pod deletion command
     - Counter value after new pod starts

4. **ConfigMap vs Secret**
   - When to use ConfigMap
   - When to use Secret
   - Key differences

**Required Screenshots/Outputs:**
- `kubectl get configmap,pvc` output
- File content inside pod (`cat /config/config.json`)
- Environment variables in pod
- Persistence test (before/after pod restart)

---

## Bonus Task — ConfigMap Hot Reload (2.5 pts)

**Objective:** Understand ConfigMap update behavior and implement configuration reloading.

**Requirements:**

1. **Test Default Update Behavior**
   - Update ConfigMap content (e.g., via `kubectl edit configmap`)
   - Observe when changes appear in the mounted file
   - Document the delay (kubelet sync period)

2. **Understand subPath Limitation**
   - Research why `subPath` mounts don't receive updates
   - Document when to use and avoid `subPath`

3. **Implement Application Reload**
   - Research approaches for configuration hot reload:
     - Sidecar pattern (config reloader)
     - Application file watching
     - Pod restart via annotations
   - Implement one approach and document it

4. **Helm Upgrade Pattern**
   - Use `helm.sh/resource-policy` or checksum annotations
   - Trigger pod restart when ConfigMap changes
   - Demonstrate the pattern

<details>
<summary>💡 Hints</summary>

**Checksum Annotation Pattern:**
```yaml
spec:
  template:
    metadata:
      annotations:
        checksum/config: {{ include (print $.Template.BasePath "/configmap.yaml") . | sha256sum }}
```

This causes the deployment to update (and pods to restart) whenever the ConfigMap changes.

**Config Reloader Sidecar:**
Projects like `stakater/Reloader` automatically restart pods when ConfigMaps change.

**Kubelet Sync Period:**
By default, kubelet syncs ConfigMap changes every 60 seconds + cache TTL. Total delay can be up to a few minutes.

**subPath Behavior:**
When using `subPath`, the file is a copy, not a symlink, so it doesn't update. Use full directory mounts for auto-updates.

**Resources:**
- [ConfigMap Auto-Updates](https://kubernetes.io/docs/concepts/configuration/configmap/#mounted-configmaps-are-updated-automatically)
- [Reloader](https://github.com/stakater/Reloader)

</details>

**Bonus Documentation:**
- Update delay measurement
- subPath limitation explanation
- Chosen reload approach implementation
- Evidence of configuration reload working

---

## Checklist

### Task 1 — Application Persistence Upgrade (2 pts)
- [ ] Visits counter implemented
- [ ] `/visits` endpoint created
- [ ] Counter persists in file
- [ ] Docker Compose volume configured
- [ ] Local testing successful
- [ ] README updated

### Task 2 — ConfigMaps (3 pts)
- [ ] `files/config.json` created
- [ ] ConfigMap template for file mounting
- [ ] ConfigMap template for env vars
- [ ] ConfigMap mounted as file in pod
- [ ] Environment variables injected
- [ ] Verification outputs collected

### Task 3 — Persistent Volumes (3 pts)
- [ ] PVC template created
- [ ] PVC mounted to deployment
- [ ] Visits file stored on PVC
- [ ] Persistence tested (pod deletion)
- [ ] Data survives pod restart

### Task 4 — Documentation (2 pts)
- [ ] `k8s/CONFIGMAPS.md` complete
- [ ] Application changes documented
- [ ] ConfigMap implementation documented
- [ ] PVC implementation documented
- [ ] All verification outputs included

### Bonus — ConfigMap Hot Reload (2.5 pts)
- [ ] Update delay tested
- [ ] subPath limitation documented
- [ ] Reload mechanism implemented
- [ ] Documentation complete

---

## Rubric

| Criteria | Points | Description |
|----------|--------|-------------|
| **App Upgrade** | 2 pts | Visits counter, persistence, /visits endpoint |
| **ConfigMaps** | 3 pts | File mount, env vars, proper templating |
| **Persistent Volumes** | 3 pts | PVC, mount, verified persistence |
| **Documentation** | 2 pts | Complete CONFIGMAPS.md |
| **Bonus** | 2.5 pts | Hot reload understanding and implementation |
| **Total** | 12.5 pts | 10 pts required + 2.5 pts bonus |

**Grading:**
- **10/10:** Working persistence, proper ConfigMaps, verified data survival
- **8-9/10:** ConfigMaps work, persistence mostly working
- **6-7/10:** Basic ConfigMap mounting, persistence issues
- **<6/10:** ConfigMaps not properly mounted, no persistence

---

## Resources

<details>
<summary>📚 Official Documentation</summary>

- [ConfigMaps](https://kubernetes.io/docs/concepts/configuration/configmap/)
- [Persistent Volumes](https://kubernetes.io/docs/concepts/storage/persistent-volumes/)
- [Persistent Volume Claims](https://kubernetes.io/docs/concepts/storage/persistent-volumes/#persistentvolumeclaims)
- [Storage Classes](https://kubernetes.io/docs/concepts/storage/storage-classes/)

</details>

<details>
<summary>🎓 Tutorials</summary>

- [Configure Pod with ConfigMap](https://kubernetes.io/docs/tasks/configure-pod-container/configure-pod-configmap/)
- [Configure Pod with PVC](https://kubernetes.io/docs/tasks/configure-pod-container/configure-persistent-volume-storage/)
- [Mounting ConfigMaps as Files](https://kubernetes.io/docs/concepts/configuration/configmap/#using-configmaps-as-files-from-a-pod)

</details>

<details>
<summary>🛠️ Tools & Patterns</summary>

- [Helm Files Function](https://helm.sh/docs/chart_template_guide/accessing_files/)
- [Stakater Reloader](https://github.com/stakater/Reloader)
- [Minikube Storage](https://minikube.sigs.k8s.io/docs/handbook/persistent_volumes/)

</details>

---

## Looking Ahead

- **Lab 13:** ArgoCD will deploy your configured Helm charts via GitOps
- **Lab 14:** Progressive delivery with Argo Rollouts
- **Lab 15:** StatefulSets for per-pod persistent storage
- **Lab 16:** Monitoring your application configuration and storage

---

**Good luck!** 📦

> **Remember:** ConfigMaps are for non-sensitive configuration data. Use Secrets (Lab 11) for sensitive data. Persistent Volumes ensure your data survives the ephemeral nature of pods.
