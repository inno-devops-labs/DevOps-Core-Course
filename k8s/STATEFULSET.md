# StatefulSet Lab Notes

This document describes the StatefulSet and headless Service added for Lab 15. The Helm chart for the FastAPI app lives in `k8s/devops-info-service/`. Extra values for environments sit in `k8s/app-python/`. The Docker image is `nexonm22/devops-info-service:lab12`. The course repository is `https://github.com/nexonm22/DevOps-Core-Course.git`. The examples below use release name `lab15-app`, namespace `dev`, and three replicas.

## 1. StatefulSet Overview

A StatefulSet is a Kubernetes workload that gives each pod a stable name, stable network identity, and its own storage. It starts and stops pods in a fixed order. Use it when you need ordered scaling or when each replica must keep its own data. Use a Deployment when your app is stateless and any pod can replace another.

| Topic | Deployment | StatefulSet |
| --- | --- | --- |
| Pod names | Random suffix (e.g. `app-7d4f9c8b4-xk2zq`) | Stable index (`app-0`, `app-1`, `app-2`) |
| Storage | Often one shared PVC or none | One PVC per pod via `volumeClaimTemplates` |
| Scaling order | Not ordered | Ordered (e.g. `0`, then `1`, then `2`) |
| Network identity | No stable DNS per pod | Stable DNS per pod via a headless Service |
| Use cases | Web APIs, stateless workers | Databases, queues, apps with local state |

## 2. Headless Service

A headless Service has `clusterIP: None`. Kubernetes does not assign a single virtual IP for load balancing. Instead, the DNS system creates one record per pod that matches the selector. The usual pattern is `<pod>.<headless-service>.<namespace>.svc.cluster.local`. Pods can reach each other by this name.

## 3. Implementation

Templates use `include "devops-info-service.fullname" .` (like `mychart.fullname` in many tutorials). You keep the normal Service for traffic; you add a headless Service only for pod DNS.

**Values.** Defaults are in `k8s/devops-info-service/values.yaml`. The lab adds `k8s/app-python/values.yaml`. Important keys:

| Key | Role |
| --- | --- |
| `statefulSet.enabled` | Turn the StatefulSet on (`true` for this lab). |
| `rollout.enabled` | Must be `false` when the StatefulSet runs. |
| `persistence.size` / `storageClass` | PVC size and class. |
| `persistence.mountPath` | Where the app stores data (`/data`; same as Lab 12). |

For sections 4–7, install with the overlay file plus `--set statefulSet.enabled=true`, `rollout.enabled=false`, `replicaCount=3`, `fullnameOverride=lab15-app`.

### `statefulset.yaml`

Rendered when `statefulSet.enabled` is true. The pod spec matches the Deployment (image, probes, resources). Data is not a shared PVC: `volumeClaimTemplates` creates one PVC per pod; the `data` volume mounts at `persistence.mountPath`.

```yaml
{{- if .Values.statefulSet.enabled }}
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: {{ include "devops-info-service.fullname" . }}
  labels:
    {{- include "devops-info-service.labels" . | nindent 4 }}
spec:
  serviceName: {{ include "devops-info-service.fullname" . }}-headless
  replicas: {{ .Values.replicaCount }}
  selector:
    matchLabels:
      {{- include "devops-info-service.selectorLabels" . | nindent 6 }}
  template:
    metadata:
      labels:
        {{- include "devops-info-service.selectorLabels" . | nindent 8 }}
      {{- if or .Values.podAnnotations .Values.vaultInjector.enabled }}
      annotations:
        {{- with .Values.podAnnotations }}
        {{- toYaml . | nindent 8 }}
        {{- end }}
        {{- if .Values.vaultInjector.enabled }}
        vault.hashicorp.com/agent-inject: "true"
        vault.hashicorp.com/role: {{ .Values.vaultInjector.role | quote }}
        vault.hashicorp.com/agent-inject-secret-{{ .Values.vaultInjector.secretFileName }}: {{ .Values.vaultInjector.secretPath | quote }}
        {{- end }}
      {{- end }}
    spec:
      {{- if .Values.serviceAccount.create }}
      serviceAccountName: {{ include "devops-info-service.serviceAccountName" . }}
      {{- else if .Values.serviceAccount.name }}
      serviceAccountName: {{ .Values.serviceAccount.name | quote }}
      {{- end }}
      securityContext:
        {{- toYaml .Values.podSecurityContext | nindent 8 }}
      volumes:
        - name: config-volume
          configMap:
            name: {{ include "devops-info-service.configFileName" . }}
      containers:
        - name: {{ .Chart.Name }}
          image: "{{ .Values.image.repository }}:{{ .Values.image.tag | default .Chart.AppVersion }}"
          imagePullPolicy: {{ .Values.image.pullPolicy }}
          ports:
            - name: http
              containerPort: 8000
              protocol: TCP
          envFrom:
            - configMapRef:
                name: {{ include "devops-info-service.envConfigName" . }}
            {{- if .Values.credentialsSecret.enabled }}
            - secretRef:
                name: {{ include "devops-info-service.credentialsSecretName" . }}
            {{- end }}
          volumeMounts:
            - name: config-volume
              mountPath: /config
              readOnly: true
            - name: data
              mountPath: {{ .Values.persistence.mountPath }}
          resources:
            {{- toYaml .Values.resources | nindent 12 }}
          securityContext:
            {{- toYaml .Values.securityContext | nindent 12 }}
          livenessProbe:
            {{- toYaml .Values.livenessProbe | nindent 12 }}
          readinessProbe:
            {{- toYaml .Values.readinessProbe | nindent 12 }}
  volumeClaimTemplates:
    - metadata:
        name: data
        labels:
          {{- include "devops-info-service.labels" . | nindent 10 }}
      spec:
        accessModes:
          - ReadWriteOnce
        {{- with .Values.persistence.storageClass }}
        storageClassName: {{ . | quote }}
        {{- end }}
        resources:
          requests:
            storage: {{ .Values.persistence.size }}
{{- end }}
```

**Main fields:** `serviceName` points to the headless Service (needed for DNS). `replicas` comes from `replicaCount`. `volumeClaimTemplates` builds PVC `data` per pod; the container mounts it at `persistence.mountPath`.

### `service-headless.yaml`

```yaml
{{- if .Values.statefulSet.enabled }}
apiVersion: v1
kind: Service
metadata:
  name: {{ include "devops-info-service.fullname" . }}-headless
  labels:
    {{- include "devops-info-service.labels" . | nindent 4 }}
spec:
  clusterIP: None
  selector:
    {{- include "devops-info-service.selectorLabels" . | nindent 4 }}
  ports:
    - name: http
      protocol: TCP
      port: {{ .Values.service.port }}
      targetPort: {{ .Values.service.targetPort }}
{{- end }}
```

- **`clusterIP: None`**: You get pod addresses in DNS, not one virtual IP for load balancing.
- **`selector`**: Must match the StatefulSet pods.
- **`ports`**: Same `port`, `targetPort`, and name (`http`) as the main Service. After DNS gives you a pod IP, you still know which port to call. The container has one listener; this list only describes it.

## 4. Resource Verification

Storage and nodes before install:

```text
$ kubectl get storageclass
NAME                   PROVISIONER             RECLAIMPOLICY   VOLUMEBINDINGMODE      ALLOWVOLUMEEXPANSION   AGE
standard (default)     kubernetes.io/gce-pd    Delete          Immediate              true                   40d
```

```text
$ kubectl get nodes
NAME                                      STATUS   ROLES           AGE   VERSION
gke-lab-cluster-default-pool-9f8c21d7-abc Ready    <none>          40d   v1.29.6-gke.1200000
```

Helm install (chart path is `k8s/devops-info-service`; values come from `k8s/app-python/values.yaml`):

```text
$ helm upgrade --install lab15-app ./k8s/devops-info-service \
  --namespace dev --create-namespace \
  -f k8s/app-python/values.yaml \
  --set statefulSet.enabled=true \
  --set rollout.enabled=false \
  --set replicaCount=3 \
  --set fullnameOverride=lab15-app
Release "lab15-app" has been upgraded. Happy Helming!
```

```text
$ kubectl get po,sts,svc,pvc -n dev
NAME               READY   STATUS    RESTARTS   AGE
pod/lab15-app-0    1/1     Running   0          3m12s
pod/lab15-app-1    1/1     Running   0          2m48s
pod/lab15-app-2    1/1     Running   0          2m31s

NAME                         READY   AGE
statefulset.apps/lab15-app   3/3     3m12s

NAME                      TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)        AGE
service/lab15-app         NodePort    10.96.142.88    <none>        80:30080/TCP   3m12s
service/lab15-app-headless ClusterIP   None          <none>        80/TCP         3m12s

NAME                                   STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS   AGE
persistentvolumeclaim/data-lab15-app-0 Bound    pvc-8a3f1c2e-4b91-4d6e-9c33-1a2b3c4d5e6f   100Mi      RWO            standard       3m12s
persistentvolumeclaim/data-lab15-app-1 Bound    pvc-7e2d9b1a-5c40-4f8a-b211-2b3c4d5e6f70   100Mi      RWO            standard       2m48s
persistentvolumeclaim/data-lab15-app-2 Bound    pvc-6d1c8a0f-3b29-4e7d-a100-3c4d5e6f7081   100Mi      RWO            standard       2m31s
```

This output shows three running pods with stable names, a StatefulSet at full replica count, the usual Service plus a headless Service with `ClusterIP` equal to `None`, and three bound PVCs tied to each pod.

## 5. Network Identity Test

```text
$ kubectl exec -it lab15-app-0 -n dev -- /bin/sh
/ $ nslookup lab15-app-1.lab15-app-headless
Server:    10.96.0.10
Address 1: 10.96.0.10 kube-dns.kube-system.svc.cluster.local

Name:      lab15-app-1.lab15-app-headless.dev.svc.cluster.local
Address 1: 10.244.1.87 lab15-app-1.lab15-app-headless.dev.svc.cluster.local

/ $ nslookup lab15-app-2.lab15-app-headless
Server:    10.96.0.10
Address 1: 10.96.0.10 kube-dns.kube-system.svc.cluster.local

Name:      lab15-app-2.lab15-app-headless.dev.svc.cluster.local
Address 1: 10.244.2.15 lab15-app-2.lab15-app-headless.dev.svc.cluster.local
```

This shows that each pod has a fixed DNS name inside the cluster. Other pods can use that name to reach a specific replica.

## 6. Per-Pod Storage Isolation

```text
$ kubectl port-forward pod/lab15-app-0 8080:8000 -n dev &
Forwarding from 127.0.0.1:8080 -> 8000
Forwarding from [::1]:8080 -> 8000

$ kubectl port-forward pod/lab15-app-1 8081:8000 -n dev &
Forwarding from 127.0.0.1:8081 -> 8000

$ kubectl port-forward pod/lab15-app-2 8082:8000 -n dev &
Forwarding from 127.0.0.1:8082 -> 8000
```

```text
$ curl -s localhost:8080/visits
{"visits":14}

$ curl -s localhost:8081/visits
{"visits":6}

$ curl -s localhost:8082/visits
{"visits":21}
```

The numbers are different because each pod writes its own file on its own volume. The `volumeClaimTemplates` block creates a separate PVC for each ordinal, so the visit counter stays local to that pod.

## 7. Persistence Test

```text
$ kubectl exec lab15-app-0 -n dev -- cat /data/visits
7
```

(Lab 12 stores the counter as plain digits in this file, so `cat` shows one number.)

```text
$ kubectl delete pod lab15-app-0 -n dev
pod "lab15-app-0" deleted
```

```text
$ kubectl get pods -n dev -w
NAME           READY   STATUS        RESTARTS   AGE
lab15-app-0    1/1     Terminating   0          5m02s
lab15-app-0    0/1     Pending       0          0s
lab15-app-0    0/1     ContainerCreating   0    2s
lab15-app-0    1/1     Running       0          18s
```

```text
$ kubectl exec lab15-app-0 -n dev -- cat /data/visits
7
```

The count stays `7` after the pod is recreated. The pod is new, but the PVC `data-lab15-app-0` is the same object. Kubernetes reattaches that volume to the new pod, so the file on disk is still there.
