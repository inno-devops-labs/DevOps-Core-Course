{{/*
Security context definition
Usage: {{ include "common-lib.security.context" .Values.securityContext }}
*/}}
{{- define "common-lib.security.context" -}}
{{- if . }}
securityContext:
  {{- toYaml . | nindent 2 }}
{{- end }}
{{- end }}
