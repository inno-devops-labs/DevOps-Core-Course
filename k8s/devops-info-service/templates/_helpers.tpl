{{- define "devops-service.name" -}}
devops-service
{{- end }}

{{- define "devops-service.labels" -}}
app: {{ include "devops-service.name" . }}
{{- end }}