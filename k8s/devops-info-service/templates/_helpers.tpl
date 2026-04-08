{{/*
Chart-local wrappers around the shared library helpers.
*/}}
{{- define "devops-info-service.name" -}}
{{- include "common-lib.name" . -}}
{{- end -}}

{{- define "devops-info-service.fullname" -}}
{{- include "common-lib.fullname" . -}}
{{- end -}}

{{- define "devops-info-service.labels" -}}
{{- include "common-lib.labels" . -}}
{{- end -}}

{{- define "devops-info-service.selectorLabels" -}}
{{- include "common-lib.selectorLabels" . -}}
{{- end -}}

{{- define "devops-info-service.preInstallJobName" -}}
{{- printf "%s-pre-install" (include "devops-info-service.fullname" .) | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "devops-info-service.postInstallJobName" -}}
{{- printf "%s-post-install" (include "devops-info-service.fullname" .) | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "devops-info-service.serviceAccountName" -}}
{{- if .Values.serviceAccount.create -}}
{{- default (include "devops-info-service.fullname" .) .Values.serviceAccount.name -}}
{{- else -}}
{{- default "default" .Values.serviceAccount.name -}}
{{- end -}}
{{- end -}}

{{- define "devops-info-service.secretName" -}}
{{- default (printf "%s-secret" (include "devops-info-service.fullname" .)) .Values.secrets.name -}}
{{- end -}}

{{- define "devops-info-service.envVars" -}}
- name: HOST
  value: {{ .Values.env.host | quote }}
- name: PORT
  value: {{ .Values.container.port | quote }}
- name: APP_ENV
  value: {{ .Values.env.appEnv | quote }}
- name: LOG_LEVEL
  value: {{ .Values.env.logLevel | quote }}
{{- with .Values.env.extra }}
{{- range . }}
- name: {{ .name }}
  value: {{ .value | quote }}
{{- end }}
{{- end }}
{{- end -}}

{{- define "devops-info-service.vaultConfigTemplate" -}}
{{- $open := "{{" -}}
{{- $close := "}}" -}}
{{- printf "%s- with secret %q -%s\nAPP_USERNAME=%s .Data.data.username %s\nAPP_PASSWORD=%s .Data.data.password %s\n%s- end %s" $open .Values.vault.secretPath $close $open $close $open $close $open $close -}}
{{- end -}}

{{- define "devops-info-service.vaultAnnotations" -}}
vault.hashicorp.com/agent-inject: "true"
vault.hashicorp.com/role: {{ .Values.vault.role | quote }}
vault.hashicorp.com/auth-path: {{ .Values.vault.authPath | quote }}
vault.hashicorp.com/agent-inject-secret-config: {{ .Values.vault.secretPath | quote }}
vault.hashicorp.com/secret-volume-path-config: {{ .Values.vault.mountPath | quote }}
vault.hashicorp.com/agent-inject-file-config: {{ .Values.vault.fileName | quote }}
{{- if .Values.vault.template.enabled }}
vault.hashicorp.com/agent-inject-template-config: |
{{ include "devops-info-service.vaultConfigTemplate" . | nindent 2 }}
{{- end }}
{{- with .Values.vault.template.staticSecretRenderInterval }}
vault.hashicorp.com/template-static-secret-render-interval: {{ . | quote }}
{{- end }}
{{- with .Values.vault.injectCommand }}
vault.hashicorp.com/agent-inject-command-config: {{ . | quote }}
{{- end }}
{{- end -}}
