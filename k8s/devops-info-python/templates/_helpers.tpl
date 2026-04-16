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
{{- if .Values.persistence.enabled -}}
{{- $persistenceSize := required "persistence.size must be set when persistence.enabled=true" .Values.persistence.size -}}
{{- end -}}
{{- $appName := required "app.name must be set" .Values.app.name -}}
{{- $appEnvironment := required "app.environment must be set" .Values.app.environment -}}
{{- $configMountPath := required "app.configMountPath must be set" .Values.app.configMountPath -}}
{{- $dataMountPath := required "app.dataMountPath must be set" .Values.app.dataMountPath -}}
{{- $configFileName := required "app.configFileName must be set" .Values.app.configFileName -}}
{{- $visitsFileName := required "app.visitsFileName must be set" .Values.app.visitsFileName -}}
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
Resolve the mounted application config file path.
*/}}
{{- define "devops-info-python.configFilePath" -}}
{{- printf "%s/%s" .Values.app.configMountPath .Values.app.configFileName -}}
{{- end -}}

{{/*
Resolve the mounted visits data file path.
*/}}
{{- define "devops-info-python.visitsFilePath" -}}
{{- printf "%s/%s" .Values.app.dataMountPath .Values.app.visitsFileName -}}
{{- end -}}

{{/*
Render the JSON config file stored under files/config.json.
*/}}
{{- define "devops-info-python.renderedConfigFile" -}}
{{- tpl (.Files.Get "files/config.json") . -}}
{{- end -}}

{{/*
Resolve the ConfigMap that stores the mounted JSON config file.
*/}}
{{- define "devops-info-python.configMapName" -}}
{{- printf "%s-config" (include "common.fullname" .) | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{/*
Resolve the ConfigMap that injects the runtime environment variables.
*/}}
{{- define "devops-info-python.envConfigMapName" -}}
{{- printf "%s-env" (include "common.fullname" .) | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{/*
Resolve the PersistentVolumeClaim used for visit persistence.
*/}}
{{- define "devops-info-python.persistenceClaimName" -}}
{{- if .Values.persistence.existingClaim -}}
{{- .Values.persistence.existingClaim | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- printf "%s-data" (include "common.fullname" .) | trunc 63 | trimSuffix "-" -}}
{{- end -}}
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
