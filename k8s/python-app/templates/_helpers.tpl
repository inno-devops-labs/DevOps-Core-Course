{{/*
Bridge to common-lib templates.
All naming and labeling logic is delegated to the shared library chart.
*/}}

{{- define "python-app.name" -}}
{{- include "common.name" . }}
{{- end }}

{{- define "python-app.fullname" -}}
{{- include "common.fullname" . }}
{{- end }}

{{- define "python-app.chart" -}}
{{- include "common.chart" . }}
{{- end }}

{{- define "python-app.labels" -}}
{{- include "common.labels" . }}
{{- end }}

{{- define "python-app.selectorLabels" -}}
{{- include "common.selectorLabels" . }}
{{- end }}
