{{/*
Chart-specific aliases that delegate to the common-lib templates.
This eliminates duplication: naming, labelling, and chart metadata logic
lives in common-lib and is reused here via define/include.
*/}}

{{- define "devops-info-service.name" -}}
{{ include "common.name" . }}
{{- end }}

{{- define "devops-info-service.fullname" -}}
{{ include "common.fullname" . }}
{{- end }}

{{- define "devops-info-service.chart" -}}
{{ include "common.chart" . }}
{{- end }}

{{- define "devops-info-service.labels" -}}
{{ include "common.labels" . }}
{{- end }}

{{- define "devops-info-service.selectorLabels" -}}
{{ include "common.selectorLabels" . }}
{{- end }}

{{- define "devops-info-service.secretName" -}}
{{- printf "%s-credentials" (include "devops-info-service.fullname" .) }}
{{- end }}

{{- define "devops-info-service.serviceAccountName" -}}
{{- if .Values.serviceAccount.name }}
{{- .Values.serviceAccount.name }}
{{- else }}
{{- include "devops-info-service.fullname" . }}
{{- end }}
{{- end }}

{{/*
Non-sensitive container env from values (DRY). Secret keys are injected via envFrom.
*/}}
{{- define "devops-info-service.envVars" -}}
{{- if .Values.env }}
{{- toYaml .Values.env }}
{{- end }}
{{- end }}
