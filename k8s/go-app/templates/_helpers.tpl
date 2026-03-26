{{/*
Override common templates to use common-lib definitions.
This file bridges the go-app chart to the common-lib library.
*/}}

{{- define "go-app.name" -}}
{{- include "common.name" . }}
{{- end }}

{{- define "go-app.fullname" -}}
{{- include "common.fullname" . }}
{{- end }}

{{- define "go-app.chart" -}}
{{- include "common.chart" . }}
{{- end }}

{{- define "go-app.labels" -}}
{{- include "common.labels" . }}
{{- end }}

{{- define "go-app.selectorLabels" -}}
{{- include "common.selectorLabels" . }}
{{- end }}
