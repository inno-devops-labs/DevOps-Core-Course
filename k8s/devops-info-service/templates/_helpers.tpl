{{- define "devops-info-service.name" -}}
{{ .Chart.Name }}
{{- end }}

{{- define "devops-info-service.fullname" -}}
{{ .Release.Name }}-{{ .Chart.Name }}
{{- end }}

{{- define "devops-info-service.labels" -}}
app: {{ include "devops-info-service.name" . }}
project: devops-core-course
tier: backend
{{- end }}
