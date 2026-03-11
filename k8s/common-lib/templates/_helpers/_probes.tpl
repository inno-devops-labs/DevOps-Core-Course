{{/*
Liveness probe definition
Usage: {{ include "common-lib.probes.liveness" .Values.livenessProbe }}
*/}}
{{- define "common-lib.probes.liveness" -}}
{{- if .enabled }}
livenessProbe:
  httpGet:
    path: {{ .path }}
    port: {{ .port }}
  initialDelaySeconds: {{ .initialDelaySeconds }}
  periodSeconds: {{ .periodSeconds }}
  timeoutSeconds: {{ .timeoutSeconds }}
  failureThreshold: {{ .failureThreshold }}
{{- end }}
{{- end }}

{{/*
Readiness probe definition
Usage: {{ include "common-lib.probes.readiness" .Values.readinessProbe }}
*/}}
{{- define "common-lib.probes.readiness" -}}
{{- if .enabled }}
readinessProbe:
  httpGet:
    path: {{ .path }}
    port: {{ .port }}
  initialDelaySeconds: {{ .initialDelaySeconds }}
  periodSeconds: {{ .periodSeconds }}
  timeoutSeconds: {{ .timeoutSeconds }}
  successThreshold: {{ .successThreshold }}
{{- end }}
{{- end }}
