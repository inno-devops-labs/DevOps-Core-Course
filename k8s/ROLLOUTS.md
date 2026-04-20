# Lab 14 — Argo Rollouts

I stayed on the same FastAPI service from the earlier labs (`nexonm22/devops-info-service`). The Helm chart lives in `k8s/devops-info-service`, and Argo CD in this repo points at that path while the env-specific numbers sit in `k8s/app-python/` (`values-dev.yaml`, `values-prod.yaml`). There is also a copy of the Rollout templates under `k8s/app-python/templates/` — I tried to keep it in sync with the real chart, but only `devops-info-service/templates/` is what Helm actually renders.

For the examples below I used the dev setup: release `python-app-dev`, namespace `dev`, same as in `k8s/argocd/application-dev.yaml`. The course repo is `https://github.com/nexonm22/DevOps-Core-Course.git`.

---

## Installing the controller and the UI

Nothing fancy here: create `argo-rollouts`, apply the upstream manifest, check the pod.

```bash
kubectl create namespace argo-rollouts
kubectl apply -n argo-rollouts -f https://github.com/argoproj/argo-rollouts/releases/latest/download/install.yaml
kubectl get pods -n argo-rollouts
```

I got the usual CRD/RBAC spam in the output, then a single controller pod in `Running` with `1/1` ready.

On Linux I pulled the kubectl plugin binary, chmod, moved it to `/usr/local/bin/kubectl-argo-rollouts`, and `kubectl argo rollouts version` showed something like v1.7.2.

The dashboard is another one-liner from the docs, then port-forward:

```bash
kubectl apply -n argo-rollouts -f https://github.com/argoproj/argo-rollouts/releases/latest/download/dashboard-install.yaml
kubectl port-forward svc/argo-rollouts-dashboard -n argo-rollouts 3100:3100
```

After that I opened `http://localhost:3100` in the browser and clicked through the UI; I am not attaching screen captures in this document, the proof below is mostly CLI plus what I saw live in the dashboard.

---

## Rollout vs Deployment (what actually changes)

Both objects describe the same workload shape: `metadata`, `spec.replicas`, `spec.selector`, `spec.template` with the pod spec. In our chart the pod template is intentionally the same bytes between `deployment.yaml` and `rollout.yaml` so image, resources, probes, volumes, and labels do not drift.

The differences that matter for the lab:

| Topic | Deployment (`apps/v1`) | Rollout (`argoproj.io/v1alpha1`) |
|--------|-------------------------|-----------------------------------|
| API group / kind | `apps/v1`, `Deployment` | `argoproj.io/v1alpha1`, `Rollout` |
| Update strategy | `spec.strategy.type` = `RollingUpdate` or `Recreate`, plus `rollingUpdate` limits | `spec.strategy.canary` or `spec.strategy.blueGreen` with steps, services, analysis hooks |
| Progressive delivery | Not built in; Kubernetes only replaces pods by surge/unavailable rules | Built in: weights, pauses, analysis runs, promotion, abort, undo |
| Traffic / revision model | One ReplicaSet moves forward; Service sends to all ready endpoints that match labels | Controller manages stable vs canary (or active vs preview) ReplicaSets and coordinates promotion |
| Tooling | `kubectl rollout …` | Argo Rollouts CRDs + `kubectl argo rollouts …` |

In `k8s/devops-info-service/values.yaml`, `rollout.enabled: true` means Helm renders the Rollout templates and **skips** the Deployment (`deployment.yaml` is wrapped in `{{- if not .Values.rollout.enabled }}`). If I set `rollout.enabled: false`, I get the classic Deployment again.

---

## Canary

I use the canary manifest below. Steps: 20% weight, analysis, manual `pause`, then 40 / 60 / 80 with 30s pauses, then 100%.

Deploy:

```bash
helm upgrade --install python-app-dev ./k8s/devops-info-service \
  -f k8s/app-python/values-dev.yaml -n dev --create-namespace
```

I watched progress with `kubectl argo rollouts get rollout python-app-dev -n dev -w`. When it stopped at a step I used `promote`. To bail out I ran `abort` and checked that things went back toward stable; `retry rollout` brought me back after a failed or aborted run.

One thing that tripped me up at first: the AnalysisTemplate checks `result == "ok"` but our `/health` returns `"healthy"`, so with the stock template the analysis fails unless you change the condition. That lines up with the bonus scenario at the end. For a clean happy path you would align `successCondition` with the real JSON.

### `rollout.yaml` (full Helm template from the chart)

```yaml
{{- if and .Values.rollout.enabled (eq .Values.rollout.strategy "canary") }}
apiVersion: argoproj.io/v1alpha1
kind: Rollout
metadata:
  name: {{ include "devops-info-service.fullname" . }}
  labels:
    {{- include "devops-info-service.labels" . | nindent 4 }}
spec:
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
        {{- if .Values.persistence.enabled }}
        - name: data-volume
          persistentVolumeClaim:
            claimName: {{ include "devops-info-service.pvcName" . }}
        {{- end }}
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
            {{- if .Values.persistence.enabled }}
            - name: data-volume
              mountPath: {{ .Values.persistence.mountPath }}
            {{- end }}
          resources:
            {{- toYaml .Values.resources | nindent 12 }}
          securityContext:
            {{- toYaml .Values.securityContext | nindent 12 }}
          livenessProbe:
            {{- toYaml .Values.livenessProbe | nindent 12 }}
          readinessProbe:
            {{- toYaml .Values.readinessProbe | nindent 12 }}
  strategy:
    canary:
      steps:
        - setWeight: 20
        - analysis:
            templates:
              - templateName: {{ include "devops-info-service.fullname" . }}-success-rate
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
{{- end }}
```

---

## Blue-green

For blue-green I added `k8s/app-python/values-bluegreen.yaml` on top of dev values (`rollout.strategy: bluegreen`). The main Service stays as before; preview is a second Service with a `-preview` suffix. I used `ClusterIP` on preview so I did not need a second `nodePort` on the same host port as the primary NodePort Service.

```bash
helm upgrade --install python-app-dev ./k8s/devops-info-service \
  -f k8s/app-python/values-dev.yaml \
  -f k8s/app-python/values-bluegreen.yaml \
  -n dev
```

With a new image I could see preview / active ReplicaSets in the CLI. In two terminals:

```bash
kubectl port-forward svc/python-app-dev 8080:80 -n dev
kubectl port-forward svc/python-app-dev-preview 8081:80 -n dev
```

Active on `http://localhost:8080`, preview on `http://localhost:8081`. After a quick check I ran `kubectl argo rollouts promote python-app-dev -n dev` for the instant switch. `kubectl argo rollouts undo python-app-dev -n dev` felt noticeably snappier than walking back a long canary.

### `rollout-bluegreen.yaml` (full Helm template)

```yaml
{{- if and .Values.rollout.enabled (eq .Values.rollout.strategy "bluegreen") }}
apiVersion: argoproj.io/v1alpha1
kind: Rollout
metadata:
  name: {{ include "devops-info-service.fullname" . }}
  labels:
    {{- include "devops-info-service.labels" . | nindent 4 }}
spec:
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
        {{- if .Values.persistence.enabled }}
        - name: data-volume
          persistentVolumeClaim:
            claimName: {{ include "devops-info-service.pvcName" . }}
        {{- end }}
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
            {{- if .Values.persistence.enabled }}
            - name: data-volume
              mountPath: {{ .Values.persistence.mountPath }}
            {{- end }}
          resources:
            {{- toYaml .Values.resources | nindent 12 }}
          securityContext:
            {{- toYaml .Values.securityContext | nindent 12 }}
          livenessProbe:
            {{- toYaml .Values.livenessProbe | nindent 12 }}
          readinessProbe:
            {{- toYaml .Values.readinessProbe | nindent 12 }}
  strategy:
    blueGreen:
      activeService: {{ include "devops-info-service.fullname" . }}
      previewService: {{ include "devops-info-service.fullname" . }}-preview
      autoPromotionEnabled: false
{{- end }}
```

### `service-preview.yaml` (full Helm template)

```yaml
{{- if and .Values.rollout.enabled (eq .Values.rollout.strategy "bluegreen") }}
apiVersion: v1
kind: Service
metadata:
  name: {{ include "devops-info-service.fullname" . }}-preview
  labels:
    {{- include "devops-info-service.labels" . | nindent 4 }}
spec:
  type: ClusterIP
  selector:
    {{- include "devops-info-service.selectorLabels" . | nindent 4 }}
  ports:
    - name: http
      protocol: TCP
      port: {{ .Values.service.port }}
      targetPort: {{ .Values.service.targetPort }}
{{- end }}
```

---

## Canary vs blue-green

| | Canary | Blue-green |
|--|--------|------------|
| Traffic | Step by step (`setWeight` and pauses) | Full cut-over when you `promote` |
| Rollback | Depends where you stopped; `abort` / `undo` | `undo` snaps back quickly in my tests |
| Resources | Often one “wave” of extra pods during the steps | Two stacks while preview exists |
| Good when | You want gradual exposure | You want two URLs to compare before one switch |
| Manual work | More `promote` clicks on pauses | Mostly: test preview, then promote |

Personally: canary spreads the risk across time; blue-green is easier to reason about as “old stack vs new stack” and the preview Service made testing obvious.

---

## Commands I used

- `kubectl argo rollouts get rollout …` and `… -w` — status and live updates  
- `kubectl argo rollouts promote …` — next canary step or flip preview to active  
- `kubectl argo rollouts abort …` — stop and lean back on stable  
- `kubectl argo rollouts retry rollout …` — try again after abort or failure  
- `kubectl argo rollouts undo …` — go back to the previous revision  
- `kubectl argo rollouts pause` / `resume` — hold or continue  
- `kubectl argo rollouts set image` — quick image change without editing Helm values  

---

## Bonus — automated analysis

The Rollout references this template by name (`…-success-rate`). It calls our Service’s `/health`, reads `$.status`, and evaluates `successCondition`. `interval` / `count` / `failureLimit` control how strict the check is.

With `ok` in the condition and `healthy` in the API, the run failed in my test: the watch showed the analysis step, then `AnalysisFailed`, the Rollout went `Degraded`, and traffic did not stay on the bad revision. I like having that gate right after the first weighted step.

### `analysis-template.yaml` (full Helm template)

```yaml
{{- if and .Values.rollout.enabled (eq .Values.rollout.strategy "canary") }}
apiVersion: argoproj.io/v1alpha1
kind: AnalysisTemplate
metadata:
  name: {{ include "devops-info-service.fullname" . }}-success-rate
  labels:
    {{- include "devops-info-service.labels" . | nindent 4 }}
spec:
  metrics:
    - name: webcheck
      provider:
        web:
          url: http://{{ include "devops-info-service.fullname" . }}.{{ .Release.Namespace }}.svc:{{ .Values.service.port }}/health
          jsonPath: "{$.status}"
      successCondition: result == "ok"
      interval: 10s
      count: 3
      failureLimit: 1
{{- end }}
```
