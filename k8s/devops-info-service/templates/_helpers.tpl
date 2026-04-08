{{/*
ServiceAccount name used by the pod and by Vault Kubernetes auth role binding.
*/}}
{{- define "devops-info-service.serviceAccountName" -}}
{{- if .Values.serviceAccount.name }}
{{- .Values.serviceAccount.name }}
{{- else }}
{{- include "common-lib.fullname" . }}
{{- end }}
{{- end }}

{{/*
Shared env snippets (DRY): chart/release metadata for verification and logs.
*/}}
{{- define "devops-info-service.extraEnv" -}}
- name: CHART_NAME
  value: {{ .Chart.Name | quote }}
- name: RELEASE_NAME
  value: {{ .Release.Name | quote }}
{{- end }}
