{{- define "devops-info-service.name" -}}
{{ .Chart.Name }}
{{- end }}

{{- define "devops-info-service.fullname" -}}
{{ .Release.Name }}-{{ .Chart.Name }}
{{- end }}

{{- define "devops-info-service.selectorLabels" -}}
app.kubernetes.io/name: {{ include "devops-info-service.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{- define "devops-info-service.labels" -}}
{{ include "devops-info-service.selectorLabels" . }}
project: devops-core-course
tier: backend
{{- end }}