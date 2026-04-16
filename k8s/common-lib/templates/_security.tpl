{{/*
Reusable security context snippets.
*/}}
{{- define "common-lib.podSecurityContext" -}}
runAsNonRoot: {{ .runAsNonRoot }}
runAsUser: {{ .runAsUser }}
runAsGroup: {{ .runAsGroup }}
{{- if hasKey . "fsGroup" }}
fsGroup: {{ .fsGroup }}
{{- end }}
{{- if hasKey . "fsGroupChangePolicy" }}
fsGroupChangePolicy: {{ .fsGroupChangePolicy }}
{{- end }}
seccompProfile:
  type: {{ .seccompProfile.type }}
{{- end -}}

{{- define "common-lib.containerSecurityContext" -}}
{{- if hasKey . "runAsNonRoot" }}
runAsNonRoot: {{ .runAsNonRoot }}
{{- end }}
{{- if hasKey . "runAsUser" }}
runAsUser: {{ .runAsUser }}
{{- end }}
{{- if hasKey . "runAsGroup" }}
runAsGroup: {{ .runAsGroup }}
{{- end }}
allowPrivilegeEscalation: {{ .allowPrivilegeEscalation }}
capabilities:
  drop:
{{- range .capabilities.drop }}
    - {{ . }}
{{- end }}
{{- end -}}
