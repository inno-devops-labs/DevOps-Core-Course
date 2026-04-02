{{/*
Thin wrappers that delegate to common-lib templates.
This demonstrates the DRY benefit of library charts —
no logic duplication between devops-python-chart and devops-go-chart.
*/}}

{{- define "devops-go-chart.name" -}}
{{- include "common.name" . }}
{{- end }}

{{- define "devops-go-chart.fullname" -}}
{{- include "common.fullname" . }}
{{- end }}

{{- define "devops-go-chart.chart" -}}
{{- include "common.chart" . }}
{{- end }}

{{- define "devops-go-chart.labels" -}}
{{- include "common.labels" . }}
{{- end }}

{{- define "devops-go-chart.selectorLabels" -}}
{{- include "common.selectorLabels" . }}
{{- end }}
