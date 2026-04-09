{{/*
Environment variables (DRY include).
*/}}
{{- define "devops-info-python.envVars" -}}
- name: APP_ENV
  value: {{ .Values.app.environment | quote }}
- name: LOG_LEVEL
  value: {{ .Values.app.logLevel | quote }}
{{- if .Values.extraEnv }}
{{ toYaml .Values.extraEnv }}
{{- end }}
{{- end }}

