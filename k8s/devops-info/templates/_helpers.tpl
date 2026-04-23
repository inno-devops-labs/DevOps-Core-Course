{{- define "devops-info.name" -}}
{{- include "common.name" . -}}
{{- end -}}

{{- define "devops-info.fullname" -}}
{{- include "common.fullname" . -}}
{{- end -}}

{{- define "devops-info.labels" -}}
{{- include "common.labels" . -}}
{{- end -}}

{{- define "devops-info.selectorLabels" -}}
{{- include "common.selectorLabels" . -}}
{{- end -}}

{{- define "devops-info.secretName" -}}
{{- if .Values.secret.name -}}
{{- .Values.secret.name -}}
{{- else -}}
{{- printf "%s-secret" (include "devops-info.fullname" .) -}}
{{- end -}}
{{- end -}}

{{- define "devops-info.fileConfigMapName" -}}
{{- printf "%s-config" (include "devops-info.fullname" .) -}}
{{- end -}}

{{- define "devops-info.envConfigMapName" -}}
{{- printf "%s-env" (include "devops-info.fullname" .) -}}
{{- end -}}

{{- define "devops-info.pvcName" -}}
{{- printf "%s-data" (include "devops-info.fullname" .) -}}
{{- end -}}

{{- define "devops-info.serviceAccountName" -}}
{{- if .Values.serviceAccount.create -}}
{{- default (include "devops-info.fullname" .) .Values.serviceAccount.name -}}
{{- else -}}
{{- default "default" .Values.serviceAccount.name -}}
{{- end -}}
{{- end -}}

{{- define "devops-info.envVars" -}}
{{- range .Values.env }}
- name: {{ .name }}
  value: {{ .value | quote }}
{{- end }}
{{- end -}}

{{- define "devops-info.vaultAnnotations" -}}
{{- if .Values.vault.enabled }}
vault.hashicorp.com/agent-inject: "true"
vault.hashicorp.com/role: {{ .Values.vault.role | quote }}
{{ printf "vault.hashicorp.com/agent-inject-secret-%s" .Values.vault.fileName }}: {{ .Values.vault.secretPath | quote }}
{{- if .Values.vault.template }}
{{ printf "vault.hashicorp.com/agent-inject-template-%s" .Values.vault.fileName }}: |
{{ tpl .Values.vault.template . | nindent 2 }}
{{- end }}
{{- if .Values.vault.command }}
vault.hashicorp.com/agent-inject-command: {{ .Values.vault.command | quote }}
{{- end }}
{{- end }}
{{- end -}}
