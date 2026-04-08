{{/*
Application-level helpers.

This chart delegates common naming/labels to the `common-lib` dependency.
*/}}

{{- define "devops-app-java.name" -}}
{{- include "common.name" . -}}
{{- end -}}

{{- define "devops-app-java.fullname" -}}
{{- include "common.fullname" . -}}
{{- end -}}

{{- define "devops-app-java.labels" -}}
{{- include "common.labels" . -}}
{{- end -}}

{{- define "devops-app-java.selectorLabels" -}}
{{- include "common.selectorLabels" . -}}
{{- end -}}

{{- define "devops-app-java.secretName" -}}
{{- if .Values.secret.name -}}
{{- .Values.secret.name -}}
{{- else -}}
{{- printf "%s-secret" (include "devops-app-java.fullname" .) -}}
{{- end -}}
{{- end -}}

{{- define "devops-app-java.serviceAccountName" -}}
{{- if .Values.serviceAccount.name -}}
{{- .Values.serviceAccount.name -}}
{{- else -}}
{{- include "devops-app-java.fullname" . -}}
{{- end -}}
{{- end -}}

{{- define "devops-app-java.commonEnv" -}}
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
{{- end -}}

