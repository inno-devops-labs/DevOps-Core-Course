{{/*
Re-export common-lib helpers under the chart's own prefix
so templates can use either "devops-app.*" or "common.*" names.
*/}}

{{- define "devops-app.name" -}}
{{- include "common.name" . }}
{{- end }}

{{- define "devops-app.fullname" -}}
{{- include "common.fullname" . }}
{{- end }}

{{- define "devops-app.chart" -}}
{{- include "common.chart" . }}
{{- end }}

{{- define "devops-app.labels" -}}
{{- include "common.labels" . }}
{{- end }}

{{- define "devops-app.selectorLabels" -}}
{{- include "common.selectorLabels" . }}
{{- end }}
