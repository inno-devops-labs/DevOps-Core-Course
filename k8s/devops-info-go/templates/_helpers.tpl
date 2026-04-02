{{/*
Override common templates with chart-specific names.
This file re-exports common-lib helpers under local names.
*/}}

{{- define "devops-info-go.name" -}}
{{- include "common.name" . }}
{{- end }}

{{- define "devops-info-go.fullname" -}}
{{- include "common.fullname" . }}
{{- end }}

{{- define "devops-info-go.chart" -}}
{{- include "common.chart" . }}
{{- end }}

{{- define "devops-info-go.labels" -}}
{{- include "common.labels" . }}
{{- end }}

{{- define "devops-info-go.selectorLabels" -}}
{{- include "common.selectorLabels" . }}
{{- end }}

{{- define "devops-info-go.envVars" -}}
{{- include "common.envVars" . }}
{{- end }}
