{{/*
Application-level helpers.

This chart delegates common naming/labels to the `common-lib` dependency.
*/}}

{{- define "devops-info-service.name" -}}
{{- include "common.name" . -}}
{{- end -}}

{{- define "devops-info-service.fullname" -}}
{{- include "common.fullname" . -}}
{{- end -}}

{{- define "devops-info-service.labels" -}}
{{- include "common.labels" . -}}
{{- end -}}

{{- define "devops-info-service.selectorLabels" -}}
{{- include "common.selectorLabels" . -}}
{{- end -}}

{{- define "devops-info-service.secretName" -}}
{{- if .Values.secret.name -}}
{{- .Values.secret.name -}}
{{- else -}}
{{- printf "%s-secret" (include "devops-info-service.fullname" .) -}}
{{- end -}}
{{- end -}}

{{- define "devops-info-service.serviceAccountName" -}}
{{- if .Values.serviceAccount.name -}}
{{- .Values.serviceAccount.name -}}
{{- else -}}
{{- include "devops-info-service.fullname" . -}}
{{- end -}}
{{- end -}}

{{- define "devops-info-service.configFileMapName" -}}
{{- printf "%s-config-file" (include "devops-info-service.fullname" .) -}}
{{- end -}}

{{- define "devops-info-service.configEnvMapName" -}}
{{- printf "%s-config-env" (include "devops-info-service.fullname" .) -}}
{{- end -}}

{{- define "devops-info-service.pvcName" -}}
{{- printf "%s-data" (include "devops-info-service.fullname" .) -}}
{{- end -}}

{{- define "devops-info-service.headlessServiceName" -}}
{{- printf "%s-headless" (include "devops-info-service.fullname" .) -}}
{{- end -}}

{{- define "devops-info-service.commonEnv" -}}
- name: HOST
  value: {{ .Values.env.host | quote }}
- name: PORT
  value: {{ .Values.env.port | quote }}
- name: SERVICE_NAME
  value: {{ .Values.env.serviceName | quote }}
- name: SERVICE_VERSION
  value: {{ .Values.env.serviceVersion | quote }}
- name: SERVICE_DESCRIPTION
  value: {{ .Values.env.serviceDescription | quote }}
- name: LOG_LEVEL
  value: {{ .Values.env.logLevel | quote }}
- name: PYTHONDONTWRITEBYTECODE
  value: {{ .Values.env.pythondontwritebytecode | quote }}
- name: VISITS_FILE
  value: {{ .Values.env.visitsFile | quote }}
{{- end -}}

