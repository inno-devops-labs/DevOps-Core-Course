# Lab 10 — Helm Package Manager

![difficulty](https://img.shields.io/badge/difficulty-intermediate-yellow)
![topic](https://img.shields.io/badge/topic-Helm-blue)
![points](https://img.shields.io/badge/points-12%2B2.5-orange)
![tech](https://img.shields.io/badge/tech-Helm-informational)

> Package your Kubernetes applications with Helm for reusable, configurable deployments across environments.

## Overview

Transform your Kubernetes manifests from Lab 9 into Helm charts. Learn templating, values management, lifecycle hooks, and chart best practices for production deployments.

**What You'll Learn:**
- Helm architecture and templating
- Creating production-ready charts
- Values and configuration management
- Chart hooks for lifecycle events
- Testing and validating charts
- Library charts for code reuse

**Tech Stack:** Helm 4.x | Kubernetes 1.33+ | Go templating | YAML

---

## Tasks

### Task 1 — Helm Fundamentals (2 pts)

**Objective:** Understand Helm concepts and set up your environment.

**Requirements:**

1. **Learn Helm Concepts**
   - Understand Charts, Releases, and Repositories
   - Learn Go template syntax basics
   - Study Helm architecture (v3)

2. **Install Helm**
   - Install Helm CLI
   - Verify installation
   - Add common chart repositories

3. **Explore Existing Charts**
   - Search public repositories
   - Inspect a chart's structure
   - Understand chart components

<details>
<summary>💡 Helm Concepts</summary>

**What is Helm?**
Package manager for Kubernetes. Think `apt`/`yum` for K8s applications.

**Core Concepts:**
- **Chart**: Package of Kubernetes resources (like a `.deb` or `.rpm`)
- **Release**: Instance of a chart running in a cluster
- **Repository**: Collection of charts (like package repositories)
- **Values**: Configuration parameters for customization

**Why Helm?**
- **Templating**: Reuse manifests across environments
- **Versioning**: Track and rollback releases
- **Dependencies**: Manage complex multi-chart applications
- **Hooks**: Execute actions during install/upgrade/delete
- **Standardization**: Industry-standard packaging

**Helm 4 (Current):**
- Released November 2025, first major version in 6 years
- Full backward compatibility with Helm 3 charts (apiVersion v2)
- OCI registry support
- No Tiller (removed in Helm 3)
- Improved security and performance

**Chart Structure:**
```
mychart/
├── Chart.yaml          # Chart metadata
├── values.yaml         # Default configuration values
├── charts/             # Chart dependencies
└── templates/          # Kubernetes manifest templates
    ├── deployment.yaml
    ├── service.yaml
    ├── _helpers.tpl    # Template helpers
    └── NOTES.txt       # Post-install notes
```

**Resources:**
- [Helm Architecture](https://helm.sh/docs/topics/architecture/)
- [Three Big Concepts](https://helm.sh/docs/intro/using_helm/#three-big-concepts)
- [Charts](https://helm.sh/docs/topics/charts/)
- [Install Helm](https://helm.sh/docs/intro/install/)

</details>

<details>
<summary>💡 Essential Helm Commands</summary>

**Repository Management:**
```bash
# Note: Traditional HTTP repositories are being phased out
# Many charts now use OCI registries

# Add a repository (traditional method)
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update
helm search repo prometheus

# Install from OCI registry (modern method)
helm install my-nginx oci://registry-1.docker.io/bitnamicharts/nginx
```

**Chart Operations:**
```bash
helm create mychart           # Create new chart
helm lint mychart             # Validate chart
helm template mychart         # Render templates locally
helm install myrelease mychart  # Install chart
helm list                     # List releases
helm uninstall myrelease      # Remove release
```

**Debugging:**
```bash
helm install --dry-run --debug myrelease mychart
helm get manifest myrelease
helm get values myrelease
```

</details>

**Documentation Required:**
- Terminal output showing Helm installation and version (should be 4.x)
- Output of exploring a public chart (e.g., `helm show chart prometheus-community/prometheus`)
- Brief explanation of Helm's value proposition

---

### Task 2 — Create Your Helm Chart (3 pts)

**Objective:** Convert your Lab 9 Kubernetes manifests into a Helm chart.

**Requirements:**

1. **Initialize Chart**
   - Create chart in `k8s/` directory
   - Choose appropriate chart name
   - Update `Chart.yaml` with metadata

2. **Convert Manifests to Templates**
   - Move your `deployment.yml` to `templates/deployment.yaml`
   - Move your `service.yml` to `templates/service.yaml`
   - Templatize using Go template syntax
   - Extract values to `values.yaml`

3. **Implement Proper Templating**
   - Image repository and tag from values
   - Replica count from values
   - Resource limits from values
   - Service type and ports from values
   - Labels using helper templates

4. **Keep Health Checks**
   - NEVER comment out liveness/readiness probes
   - Make probe configuration customizable via values
   - Provide sensible defaults

<details>
<summary>💡 Chart.yaml Structure</summary>

**Required Fields:**
```yaml
apiVersion: v2              # Chart API version (v2 for Helm 3+)
name: my-python-app         # Chart name
description: My Python application Helm chart
type: application           # application or library
version: 0.1.0              # Chart version (SemVer)
appVersion: "1.0"           # App version (can be any string)
```

**Optional but Recommended:**
```yaml
keywords:
  - python
  - web
maintainers:
  - name: Your Name
    email: your.email@example.com
sources:
  - https://github.com/yourusername/yourapp
```

**Chart vs App Version:**
- `version`: Chart version (change when chart changes)
- `appVersion`: Application version (change when app changes)

</details>

<details>
<summary>💡 Templating Basics</summary>

**Go Template Syntax:**
```yaml
# Access value from values.yaml
image: {{ .Values.image.repository }}:{{ .Values.image.tag }}

# With default value
replicas: {{ .Values.replicaCount | default 3 }}

# Conditional
{{- if .Values.service.enabled }}
# ... service definition
{{- end }}

# Range (loop)
{{- range .Values.env }}
- name: {{ .name }}
  value: {{ .value }}
{{- end }}
```

**Built-in Objects:**
- `.Values`: Values from `values.yaml` and overrides
- `.Chart`: Contents of `Chart.yaml`
- `.Release`: Info about the release (name, namespace, etc.)
- `.Template`: Info about current template

**Example Conversion:**

Before (static):
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-app
spec:
  replicas: 3
  template:
    spec:
      containers:
      - name: my-app
        image: myuser/myapp:v1.0
```

After (templated):
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ include "mychart.fullname" . }}
  labels:
    {{- include "mychart.labels" . | nindent 4 }}
spec:
  replicas: {{ .Values.replicaCount }}
  template:
    spec:
      containers:
      - name: {{ .Chart.Name }}
        image: "{{ .Values.image.repository }}:{{ .Values.image.tag | default .Chart.AppVersion }}"
```

</details>

<details>
<summary>💡 Values.yaml Design</summary>

**Structure Your Values:**
```yaml
# values.yaml
replicaCount: 3

image:
  repository: yourusername/yourapp
  tag: "1.0"
  pullPolicy: IfNotPresent

service:
  type: NodePort
  port: 80
  targetPort: 8000

resources:
  limits:
    cpu: 200m
    memory: 256Mi
  requests:
    cpu: 100m
    memory: 128Mi

livenessProbe:
  httpGet:
    path: /health
    port: 8000
  initialDelaySeconds: 10
  periodSeconds: 5

readinessProbe:
  httpGet:
    path: /ready
    port: 8000
  initialDelaySeconds: 5
  periodSeconds: 3
```

**Best Practices:**
- Nested structure for organization
- Sensible defaults
- Document each value
- Make everything configurable
- Never hardcode secrets

</details>

<details>
<summary>💡 Helper Templates</summary>

**_helpers.tpl Pattern:**
```yaml
{{/*
Expand the name of the chart.
*/}}
{{- define "mychart.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
*/}}
{{- define "mychart.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "mychart.labels" -}}
helm.sh/chart: {{ include "mychart.chart" . }}
{{ include "mychart.selectorLabels" . }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}
```

**Why Helpers?**
- DRY principle
- Consistent naming
- Reusable logic
- Easier maintenance

</details>

**Test Your Chart:**
```bash
helm lint k8s/mychart
helm template mychart k8s/mychart
helm install --dry-run --debug test-release k8s/mychart
helm install myrelease k8s/mychart
```

---

### Task 3 — Multi-Environment Support (2 pts)

**Objective:** Configure chart for different environments using values files.

**Requirements:**

1. **Create Environment-Specific Values**
   - `values-dev.yaml` for development
   - `values-prod.yaml` for production
   - Different configurations per environment

2. **Environment Differences**
   - Dev: 1 replica, relaxed resources, NodePort
   - Prod: 3+ replicas, proper resources, LoadBalancer ready
   - Different image tags or configurations

3. **Test Both Environments**
   - Install with dev values
   - Verify configuration
   - Upgrade to prod values
   - Verify changes applied

<details>
<summary>💡 Values Override Pattern</summary>

**values-dev.yaml:**
```yaml
replicaCount: 1

image:
  tag: "latest"

resources:
  limits:
    cpu: 100m
    memory: 128Mi
  requests:
    cpu: 50m
    memory: 64Mi

service:
  type: NodePort

livenessProbe:
  initialDelaySeconds: 5
  periodSeconds: 10
```

**values-prod.yaml:**
```yaml
replicaCount: 5

image:
  tag: "1.0.0"  # Specific version

resources:
  limits:
    cpu: 500m
    memory: 512Mi
  requests:
    cpu: 200m
    memory: 256Mi

service:
  type: LoadBalancer

livenessProbe:
  initialDelaySeconds: 30
  periodSeconds: 5

readinessProbe:
  initialDelaySeconds: 10
  periodSeconds: 3
```

**Using Values Files:**
```bash
# Development
helm install myapp-dev k8s/mychart -f k8s/mychart/values-dev.yaml

# Production
helm install myapp-prod k8s/mychart -f k8s/mychart/values-prod.yaml

# Override specific value
helm install myapp k8s/mychart --set replicaCount=10
```

</details>

---

### Task 4 — Chart Hooks (3 pts)

**Objective:** Implement Helm hooks for lifecycle management.

**Requirements:**

1. **Learn Hook Concepts**
   - Understand hook weights and execution order
   - Learn hook deletion policies

2. **Implement Hooks**
   - **Pre-install hook**: Job that runs before installation (e.g., database migration, validation)
   - **Post-install hook**: Job that runs after installation (e.g., smoke test, notification)

3. **Hook Configuration**
   - Proper annotations for hook type
   - Hook weight for execution order
   - Deletion policy (hook-succeeded)

4. **Verify Hooks**
   - Lint chart
   - Dry-run to see hook rendering
   - Install and verify hook execution
   - Confirm hooks are deleted per policy

<details>
<summary>💡 Helm Hooks Concept</summary>

**What Are Hooks?**
Special Kubernetes resources that execute at specific points in release lifecycle.

**Hook Types:**
- `pre-install`: Before resources are installed
- `post-install`: After all resources installed and ready
- `pre-delete`: Before deletion
- `post-delete`: After deletion
- `pre-upgrade`: Before upgrade
- `post-upgrade`: After upgrade
- `pre-rollback`: Before rollback
- `post-rollback`: After rollback

**Hook Weights:**
- Control execution order
- Lower weight runs first
- Default weight: 0

**Hook Deletion Policies:**
- `before-hook-creation`: Delete previous hook before new one
- `hook-succeeded`: Delete after successful execution
- `hook-failed`: Delete after failed execution

**Resources:**
- [Chart Hooks](https://helm.sh/docs/topics/charts_hooks/)

</details>

<details>
<summary>💡 Hook Implementation Pattern</summary>

**templates/hooks/pre-install-job.yaml:**
```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: "{{ include "mychart.fullname" . }}-pre-install"
  labels:
    {{- include "mychart.labels" . | nindent 4 }}
  annotations:
    "helm.sh/hook": pre-install
    "helm.sh/hook-weight": "-5"
    "helm.sh/hook-delete-policy": hook-succeeded
spec:
  template:
    metadata:
      name: "{{ include "mychart.fullname" . }}-pre-install"
    spec:
      restartPolicy: Never
      containers:
      - name: pre-install-job
        image: busybox
        command: ['sh', '-c', 'echo Pre-install task running && sleep 10 && echo Pre-install completed']
```

**templates/hooks/post-install-job.yaml:**
```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: "{{ include "mychart.fullname" . }}-post-install"
  labels:
    {{- include "mychart.labels" . | nindent 4 }}
  annotations:
    "helm.sh/hook": post-install
    "helm.sh/hook-weight": "5"
    "helm.sh/hook-delete-policy": hook-succeeded
spec:
  template:
    metadata:
      name: "{{ include "mychart.fullname" . }}-post-install"
    spec:
      restartPolicy: Never
      containers:
      - name: post-install-job
        image: busybox
        command: ['sh', '-c', 'echo Post-install validation && sleep 10 && echo Validation passed']
```

**Real-World Hook Examples:**
- Pre-install: Database schema migration
- Post-install: Smoke tests, send notification
- Pre-upgrade: Backup database
- Post-upgrade: Run integration tests
- Pre-delete: Backup data before cleanup

</details>

<details>
<summary>💡 Testing Hooks</summary>

**Validation Commands:**
```bash
# Lint chart
helm lint k8s/mychart

# Dry run to see hooks
helm install --dry-run --debug test-release k8s/mychart | grep -A 20 "hook"

# Install and watch hooks
helm install myrelease k8s/mychart
kubectl get jobs -w
kubectl get pods -w

# Check hook execution
kubectl describe job myrelease-pre-install
kubectl logs job/myrelease-pre-install

# Verify deletion policy worked
kubectl get jobs
```

**Hook Troubleshooting:**
- Check annotations are correct
- Verify hook weight if order matters
- Check pod logs for hook failures
- Ensure deletion policy is appropriate

</details>

---

### Task 5 — Documentation (2 pts)

**Objective:** Document your Helm chart implementation.

Create `k8s/HELM.md` with these sections:

**Required Sections:**

1. **Chart Overview**
   - Chart structure explanation
   - Key template files and their purpose
   - Values organization strategy

2. **Configuration Guide**
   - Important values and their purpose
   - How to customize for different environments
   - Example installations with different configurations

3. **Hook Implementation**
   - What hooks you implemented and why
   - Hook execution order and weights
   - Deletion policies explanation

4. **Installation Evidence**
   - `helm list` output
   - `kubectl get all` showing deployed resources
   - Hook execution output (`kubectl get jobs`, `kubectl describe job`)
   - Different environment deployments (dev vs prod)

5. **Operations**
   - Installation commands used
   - How to upgrade a release
   - How to rollback
   - How to uninstall

6. **Testing & Validation**
   - `helm lint` output
   - `helm template` verification
   - Dry-run output
   - Application accessibility verification

---

## Bonus Task — Library Charts (2.5 pts)

**Objective:** Create a library chart for shared templates across multiple applications.

**Requirements:**

1. **Deploy Second Application**
   - Create Helm chart for second app
   - Notice template duplication (labels, helpers, etc.)

2. **Create Library Chart**
   - Create library chart in `k8s/common-lib/`
   - Extract shared templates (labels, names, etc.)
   - Set chart type to `library` in Chart.yaml

3. **Use Library Chart**
   - Add library as dependency in both app charts
   - Reference library templates
   - Eliminate duplication

4. **Verify**
   - Both charts install successfully
   - Templates render correctly using library

<details>
<summary>💡 Library Chart Concepts</summary>

**What Are Library Charts?**
Charts that only contain templates (no resources). Used to share common template logic.

**Type: Library**
- Cannot be installed directly
- Used as dependencies
- Share templates across charts

**Common Use Cases:**
- Standard labels
- Name generation
- Security contexts
- Resource definitions
- Common configuration patterns

**Resources:**
- [Library Charts](https://helm.sh/docs/topics/library_charts/)

</details>

<details>
<summary>💡 Library Chart Implementation</summary>

**k8s/common-lib/Chart.yaml:**
```yaml
apiVersion: v2
name: common-lib
description: Common templates for all applications
type: library
version: 0.1.0
```

**k8s/common-lib/templates/_labels.tpl:**
```yaml
{{/*
Common labels
*/}}
{{- define "common.labels" -}}
app.kubernetes.io/name: {{ include "common.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
helm.sh/chart: {{ include "common.chart" . }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "common.selectorLabels" -}}
app.kubernetes.io/name: {{ include "common.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}
```

**Using Library Chart:**

**app1/Chart.yaml:**
```yaml
apiVersion: v2
name: app1
version: 0.1.0
dependencies:
  - name: common-lib
    version: 0.1.0
    repository: "file://../common-lib"
```

**app1/templates/deployment.yaml:**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ include "common.fullname" . }}
  labels:
    {{- include "common.labels" . | nindent 4 }}
spec:
  selector:
    matchLabels:
      {{- include "common.selectorLabels" . | nindent 6 }}
  # ... rest of deployment
```

**Install with Dependencies:**
```bash
helm dependency update k8s/app1
helm install app1-release k8s/app1
```

</details>

**Documentation Required:**
- Library chart structure
- Shared templates implemented
- How both apps use the library
- Benefits of this approach (DRY, consistency, maintainability)
- Terminal output showing successful deployment of both apps

---

## Checklist

### Task 1 — Helm Fundamentals (2 pts)
- [ ] Helm installed and verified
- [ ] Chart repositories explored
- [ ] Helm concepts understood
- [ ] Documentation of setup

### Task 2 — Create Your Helm Chart (3 pts)
- [ ] Chart created in `k8s/` directory
- [ ] `Chart.yaml` properly configured
- [ ] Manifests converted to templates
- [ ] Values properly extracted
- [ ] Helper templates implemented
- [ ] Health checks remain functional (not commented out!)
- [ ] Chart installs successfully

### Task 3 — Multi-Environment Support (2 pts)
- [ ] `values-dev.yaml` created
- [ ] `values-prod.yaml` created
- [ ] Environment-specific configurations
- [ ] Both environments tested
- [ ] Documentation of differences

### Task 4 — Chart Hooks (3 pts)
- [ ] Pre-install hook implemented
- [ ] Post-install hook implemented
- [ ] Proper hook annotations
- [ ] Hook weights configured
- [ ] Deletion policies applied
- [ ] Hooks execute successfully
- [ ] Hooks deleted per policy

### Task 5 — Documentation (2 pts)
- [ ] `k8s/HELM.md` complete
- [ ] Chart structure explained
- [ ] Configuration guide provided
- [ ] Hook implementation documented
- [ ] Installation evidence included
- [ ] Operations documented

### Bonus — Library Charts (2.5 pts)
- [ ] Library chart created
- [ ] Shared templates extracted
- [ ] Two app charts using library
- [ ] Dependencies configured
- [ ] Both apps deploy successfully
- [ ] Documentation complete

---

## Rubric

| Criteria | Points | Description |
|----------|--------|-------------|
| **Fundamentals** | 2 pts | Helm installed, concepts understood |
| **Chart Creation** | 3 pts | Proper templating, values, helpers |
| **Multi-Environment** | 2 pts | Different configs, tested |
| **Hooks** | 3 pts | Pre/post install hooks working |
| **Documentation** | 2 pts | Complete HELM.md |
| **Bonus** | 2.5 pts | Library chart implementation |
| **Total** | 14.5 pts | 12 pts required + 2.5 pts bonus |

**Grading:**
- **12/12:** Excellent templating, working hooks, multi-env, great docs
- **10-11/12:** Working chart, hooks function, good documentation
- **8-9/12:** Basic chart works, missing best practices or hooks
- **<8/12:** Chart doesn't install, commented out probes, poor templating

---

## Resources

<details>
<summary>📚 Official Helm Documentation</summary>

- [Helm Documentation](https://helm.sh/docs/)
- [Chart Best Practices](https://helm.sh/docs/chart_best_practices/)
- [Chart Template Guide](https://helm.sh/docs/chart_template_guide/)
- [Helm Commands](https://helm.sh/docs/helm/)

</details>

<details>
<summary>🎓 Learning Resources</summary>

- [Quickstart Guide](https://helm.sh/docs/intro/quickstart/)
- [Using Helm](https://helm.sh/docs/intro/using_helm/)
- [Go Template Primer](https://helm.sh/docs/chart_template_guide/builtin_objects/)
- [Chart Development Tips](https://helm.sh/docs/howto/charts_tips_and_tricks/)

</details>

<details>
<summary>🛠️ Tools</summary>

- [Helm](https://helm.sh/) - Official site
- [Artifact Hub](https://artifacthub.io/) - Public chart repository
- [helm-docs](https://github.com/norwoodj/helm-docs) - Generate docs from values
- [chart-testing](https://github.com/helm/chart-testing) - Lint and test charts

</details>

<details>
<summary>📦 Public Chart Repositories</summary>

- [Bitnami Charts](https://github.com/bitnami/charts)
- [Prometheus Community](https://github.com/prometheus-community/helm-charts)
- [Grafana Charts](https://github.com/grafana/helm-charts)

</details>

---

## Looking Ahead

- **Lab 11:** Secrets management with Vault (integrate with Helm)
- **Lab 12:** ConfigMaps and persistent volumes
- **Lab 13:** ArgoCD deploys Helm charts via GitOps
- **Lab 14:** Progressive delivery with Argo Rollouts
- **Lab 15:** StatefulSets for stateful applications

---

**Good luck!** ⛵

> **Remember:** Helm makes your deployments reusable and configurable. Never comment out health checks - configure them properly. Template everything, hardcode nothing (except defaults).
