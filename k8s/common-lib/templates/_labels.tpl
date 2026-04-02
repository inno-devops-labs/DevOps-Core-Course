{{/*
Common labels — includes version and managed-by, can change on upgrade.
Use in metadata.labels of all resources.
*/}}
{{- define "common.labels" -}}
helm.sh/chart: {{ include "common.chart" . }}
{{ include "common.selectorLabels" . }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels — MUST be stable and immutable after first install.
Used in Deployment spec.selector.matchLabels (immutable field in Kubernetes).
Only app name and instance — never chart version or managed-by.
*/}}
{{- define "common.selectorLabels" -}}
app.kubernetes.io/name: {{ include "common.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}
