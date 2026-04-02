{{- define "app-go.name" -}}
{{- include "common.name" . }}
{{- end }}

{{- define "app-go.fullname" -}}
{{- include "common.fullname" . }}
{{- end }}

{{- define "app-go.chart" -}}
{{- include "common.chart" . }}
{{- end }}

{{- define "app-go.labels" -}}
{{- include "common.labels" . }}
{{- end }}

{{- define "app-go.selectorLabels" -}}
{{- include "common.selectorLabels" . }}
{{- end }}

{{- define "app-go.serviceAccountName" -}}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
