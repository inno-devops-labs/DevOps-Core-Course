{{/*
Chart-specific labels built on top of the shared library chart.
*/}}
{{- define "devops-info-alt.baseLabels" -}}
{{ include "common-lib.labels" . }}
app.kubernetes.io/part-of: {{ .Values.partOf | quote }}
{{- end -}}

{{- define "devops-info-alt.deploymentLabels" -}}
{{ include "devops-info-alt.baseLabels" . }}
app.kubernetes.io/component: "api"
{{- end -}}

{{- define "devops-info-alt.serviceLabels" -}}
{{ include "devops-info-alt.baseLabels" . }}
app.kubernetes.io/component: "service"
{{- end -}}
