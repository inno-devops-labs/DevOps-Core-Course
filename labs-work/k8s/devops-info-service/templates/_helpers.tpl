{{/*
Expand the name of the chart.
Wraps the common library template.
*/}}
{{- define "devops-info-service.name" -}}
{{- include "common.name" . -}}
{{- end }}

{{/*
Create a default fully qualified app name.
Wraps the common library template.
*/}}
{{- define "devops-info-service.fullname" -}}
{{- include "common.fullname" . -}}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
Wraps the common library template.
*/}}
{{- define "devops-info-service.chart" -}}
{{- include "common.chart" . -}}
{{- end }}

{{/*
Common labels.
Wraps the common library template.
*/}}
{{- define "devops-info-service.labels" -}}
{{- include "common.labels" . -}}
{{- end }}

{{/*
Selector labels.
Wraps the common library template.
*/}}
{{- define "devops-info-service.selectorLabels" -}}
{{- include "common.selectorLabels" . -}}
{{- end }}

{{/*
Common environment variables for the application.
Demonstrates DRY principle via named templates.
*/}}
{{- define "devops-info-service.envVars" -}}
{{- range .Values.env }}
- name: {{ .name }}
  value: {{ .value | quote }}
{{- end }}
{{- end }}
