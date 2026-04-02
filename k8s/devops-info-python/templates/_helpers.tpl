{{/*
Override common templates with chart-specific names.
This file re-exports common-lib helpers under local names.
*/}}

{{- define "devops-info-python.name" -}}
{{- include "common.name" . }}
{{- end }}

{{- define "devops-info-python.fullname" -}}
{{- include "common.fullname" . }}
{{- end }}

{{- define "devops-info-python.chart" -}}
{{- include "common.chart" . }}
{{- end }}

{{- define "devops-info-python.labels" -}}
{{- include "common.labels" . }}
{{- end }}

{{- define "devops-info-python.selectorLabels" -}}
{{- include "common.selectorLabels" . }}
{{- end }}

{{- define "devops-info-python.envVars" -}}
{{- include "common.envVars" . }}
{{- end }}
