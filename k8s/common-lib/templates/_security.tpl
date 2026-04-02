{{/*
Reusable security context snippets.
*/}}
{{- define "common-lib.podSecurityContext" -}}
runAsNonRoot: {{ .runAsNonRoot }}
runAsUser: {{ .runAsUser }}
runAsGroup: {{ .runAsGroup }}
seccompProfile:
  type: {{ .seccompProfile.type }}
{{- end -}}

{{- define "common-lib.containerSecurityContext" -}}
allowPrivilegeEscalation: {{ .allowPrivilegeEscalation }}
capabilities:
  drop:
{{- range .capabilities.drop }}
    - {{ . }}
{{- end }}
{{- end -}}
