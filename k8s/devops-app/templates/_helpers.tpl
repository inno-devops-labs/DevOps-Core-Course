{{/*
Re-export common-lib helpers under the chart's own prefix
so templates can use either "devops-app.*" or "common.*" names.
*/}}

{{- define "devops-app.name" -}}
{{- include "common.name" . }}
{{- end }}

{{- define "devops-app.fullname" -}}
{{- include "common.fullname" . }}
{{- end }}

{{- define "devops-app.chart" -}}
{{- include "common.chart" . }}
{{- end }}

{{- define "devops-app.labels" -}}
{{- include "common.labels" . }}
{{- end }}

{{- define "devops-app.selectorLabels" -}}
{{- include "common.selectorLabels" . }}
{{- end }}

{{/*
Common environment variables shared across containers.
Keeps deployment DRY — add cross-cutting env vars here.
*/}}
{{- define "devops-app.envVars" -}}
- name: VAULT_ENABLED
  value: {{ .Values.vault.enabled | quote }}
- name: POD_NAME
  valueFrom:
    fieldRef:
      fieldPath: metadata.name
- name: POD_NAMESPACE
  valueFrom:
    fieldRef:
      fieldPath: metadata.namespace
{{- end }}
