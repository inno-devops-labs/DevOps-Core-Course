{{/*
Expand the name of the chart.
Wraps the common library template.
*/}}
{{- define "devops-info-service-go.name" -}}
{{- include "common.name" . -}}
{{- end }}

{{/*
Create a default fully qualified app name.
Wraps the common library template.
*/}}
{{- define "devops-info-service-go.fullname" -}}
{{- include "common.fullname" . -}}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
Wraps the common library template.
*/}}
{{- define "devops-info-service-go.chart" -}}
{{- include "common.chart" . -}}
{{- end }}

{{/*
Common labels.
Wraps the common library template.
*/}}
{{- define "devops-info-service-go.labels" -}}
{{- include "common.labels" . -}}
{{- end }}

{{/*
Selector labels.
Wraps the common library template.
*/}}
{{- define "devops-info-service-go.selectorLabels" -}}
{{- include "common.selectorLabels" . -}}
{{- end }}
