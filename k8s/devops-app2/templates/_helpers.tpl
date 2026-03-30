{{/*
Re-export common-lib helpers under the chart's own prefix.
*/}}

{{- define "devops-app2.name" -}}
{{- include "common.name" . }}
{{- end }}

{{- define "devops-app2.fullname" -}}
{{- include "common.fullname" . }}
{{- end }}

{{- define "devops-app2.chart" -}}
{{- include "common.chart" . }}
{{- end }}

{{- define "devops-app2.labels" -}}
{{- include "common.labels" . }}
{{- end }}

{{- define "devops-app2.selectorLabels" -}}
{{- include "common.selectorLabels" . }}
{{- end }}
