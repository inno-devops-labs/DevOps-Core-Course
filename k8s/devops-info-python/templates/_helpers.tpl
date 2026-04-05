{{/*
Validate chart values early so Helm fails before any Pod is created.
*/}}
{{- define "devops-info-python.validateValues" -}}
{{- if and (not .Values.secret.create) (not .Values.secret.existingSecret) (not .Values.secret.name) -}}
{{- fail "secret.create=false requires secret.existingSecret or secret.name to be set" -}}
{{- end -}}
{{- if .Values.vault.enabled -}}
{{- if not .Values.serviceAccount.automountServiceAccountToken -}}
{{- fail "vault.enabled=true requires serviceAccount.automountServiceAccountToken=true" -}}
{{- end -}}
{{- $vaultRole := required "vault.enabled=true requires vault.role to be set" .Values.vault.role -}}
{{- $vaultSecretPath := required "vault.enabled=true requires vault.secretPath to be set" .Values.vault.secretPath -}}
{{- end -}}
{{- end -}}

{{/*
Resolve the name of the Kubernetes Secret consumed by the application.
*/}}
{{- define "devops-info-python.secretName" -}}
{{- if and (not .Values.secret.create) (not .Values.secret.existingSecret) (not .Values.secret.name) -}}
{{- fail "secret.create=false requires secret.existingSecret or secret.name to be set" -}}
{{- end -}}
{{- if .Values.secret.existingSecret -}}
{{- .Values.secret.existingSecret | trunc 63 | trimSuffix "-" -}}
{{- else if .Values.secret.name -}}
{{- .Values.secret.name | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- printf "%s-credentials" (include "common.fullname" .) | trunc 63 | trimSuffix "-" -}}
{{- end -}}
{{- end -}}

{{/*
Resolve the ServiceAccount name used by the workload and Vault role binding.
*/}}
{{- define "devops-info-python.serviceAccountName" -}}
{{- if .Values.serviceAccount.create -}}
{{- default (include "common.fullname" .) .Values.serviceAccount.name | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- default "default" .Values.serviceAccount.name | trunc 63 | trimSuffix "-" -}}
{{- end -}}
{{- end -}}

{{/*
Render only the non-secret container environment in one place to keep the Deployment DRY.
*/}}
{{- define "devops-info-python.commonEnvVars" -}}
- name: HOST
  value: {{ .Values.config.host | quote }}
- name: PORT
  value: {{ .Values.config.port | quote }}
- name: LOG_LEVEL
  value: {{ .Values.config.logLevel | quote }}
{{- end -}}

{{/*
Render the Vault Agent template body as literal Vault template syntax.
*/}}
{{- define "devops-info-python.vaultAgentTemplate" -}}
{{ printf "{{- with secret %q -}}" .Values.vault.secretPath }}
APP_USERNAME={{ "{{ .Data.data.username }}" }}
APP_PASSWORD={{ "{{ .Data.data.password }}" }}
{{ "{{- end }}" }}
{{- end -}}

{{/*
Vault Agent Injector annotations for Lab 11.
*/}}
{{- define "devops-info-python.vaultAnnotations" -}}
vault.hashicorp.com/agent-inject: "true"
vault.hashicorp.com/auth-path: {{ .Values.vault.authPath | quote }}
vault.hashicorp.com/role: {{ .Values.vault.role | quote }}
vault.hashicorp.com/agent-pre-populate: "true"
vault.hashicorp.com/secret-volume-path: {{ .Values.vault.secretVolumePath | quote }}
vault.hashicorp.com/agent-inject-secret-app-env: {{ .Values.vault.secretPath | quote }}
vault.hashicorp.com/agent-inject-file-app-env: {{ .Values.vault.fileName | quote }}
vault.hashicorp.com/agent-inject-perms-app-env: {{ .Values.vault.filePermissions | quote }}
vault.hashicorp.com/error-on-missing-key-app-env: "true"
vault.hashicorp.com/template-static-secret-render-interval: {{ .Values.vault.templateStaticSecretRenderInterval | quote }}
vault.hashicorp.com/agent-inject-template-app-env: |
  {{- include "devops-info-python.vaultAgentTemplate" . | nindent 2 }}
{{- with .Values.vault.agentInjectCommand }}
vault.hashicorp.com/agent-inject-command-app-env: {{ . | quote }}
{{- end }}
{{- end -}}
