{{/*
Resource definitions
Usage: {{ include "common-lib.resources" .Values.resources }}
*/}}
{{- define "common-lib.resources" -}}
{{- if . }}
resources:
  requests:
    memory: {{ .requests.memory }}
    cpu: {{ .requests.cpu }}
  limits:
    memory: {{ .limits.memory }}
    cpu: {{ .limits.cpu }}
{{- end }}
{{- end }}
