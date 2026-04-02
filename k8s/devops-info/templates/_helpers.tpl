{{/*
Chart-specific labels built on top of the shared library chart.
*/}}
{{- define "devops-info.baseLabels" -}}
{{ include "common-lib.labels" . }}
app.kubernetes.io/part-of: {{ .Values.partOf | quote }}
{{- end -}}

{{- define "devops-info.deploymentLabels" -}}
{{ include "devops-info.baseLabels" . }}
app.kubernetes.io/component: "api"
{{- end -}}

{{- define "devops-info.serviceLabels" -}}
{{ include "devops-info.baseLabels" . }}
app.kubernetes.io/component: "service"
{{- end -}}

{{- define "devops-info.hookLabels" -}}
{{ include "devops-info.baseLabels" . }}
app.kubernetes.io/component: "hook"
{{- end -}}
