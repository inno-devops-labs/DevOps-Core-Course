{{- define "app-python.name" -}}
{{- include "common.name" . }}
{{- end }}

{{- define "app-python.fullname" -}}
{{- include "common.fullname" . }}
{{- end }}

{{- define "app-python.chart" -}}
{{- include "common.chart" . }}
{{- end }}

{{- define "app-python.labels" -}}
{{- include "common.labels" . }}
{{- end }}

{{- define "app-python.selectorLabels" -}}
{{- include "common.selectorLabels" . }}
{{- end }}

{{- define "app-python.serviceAccountName" -}}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}

{{- define "app-python.envVars" -}}
- name: APP_ENV
  value: "production"
- name: LOG_LEVEL
  value: "info"
{{- end }}
