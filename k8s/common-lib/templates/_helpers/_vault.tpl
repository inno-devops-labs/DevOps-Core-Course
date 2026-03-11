{{/*
Vault annotations for different secret formats
Usage: {{ include "common-lib.vault.annotations" (dict "ctx" $ "secretPath" .Values.vault.secretPath "role" .Values.vault.role) }}
*/}}
{{- define "common-lib.vault.annotations" -}}
{{- $ctx := .ctx -}}
{{- $secretPath := .secretPath | default "secret/data/info-service" -}}
{{- $role := .role | default "info-service-role" -}}
vault.hashicorp.com/agent-inject: "true"
vault.hashicorp.com/agent-init-first: "true"
vault.hashicorp.com/agent-inject-status: "update"
vault.hashicorp.com/role: {{ $role }}
vault.hashicorp.com/auth-path: auth/kubernetes
vault.hashicorp.com/secret-volume-path: /vault/secrets
vault.hashicorp.com/log-level: "info"
{{- end }}

{{/*
Environment variables template (for source-able .env file)
Usage: {{ include "common-lib.vault.template.env" (dict "secretPath" .Values.vault.secretPath) }}
*/}}
{{- define "common-lib.vault.template.env" -}}
{{- $secretPath := .secretPath | default "secret/data/info-service" -}}
vault.hashicorp.com/agent-inject-template-env: |
  {{- with secret $secretPath }}
  # Vault secrets - generated {{ now }}
  # DO NOT EDIT - This file is managed by Vault Agent
  {{- range $key, $value := .Data.data }}
  export {{ $key }}="{{ $value }}"
  {{- end }}
  # Application specific
  export APP_ENV="{{ $.ctx.Values.env.APP_NAME }}"
  export DEPLOYMENT_TIME="{{ now }}"
  {{- end }}
{{- end }}

{{/*
JSON format template (for config.json)
Usage: {{ include "common-lib.vault.template.json" (dict "secretPath" .Values.vault.secretPath) }}
*/}}
{{- define "common-lib.vault.template.json" -}}
{{- $secretPath := .secretPath | default "secret/data/info-service" -}}
vault.hashicorp.com/agent-inject-template-config.json: |
  {{- with secret $secretPath }}
  {
    "_metadata": {
      "generated_at": "{{ now }}",
      "version": {{ .Data.metadata.version }},
      "created_time": "{{ .Data.metadata.created_time }}",
      "source": "vault"
    },
    "secrets": {{ .Data.data | toPrettyJson }},
    "application": {
      "name": "{{ $.ctx.Chart.Name }}",
      "environment": "{{ $.ctx.Values.env.APP_NAME }}"
    }
  }
  {{- end }}
{{- end }}

{{/*
YAML format template (for config.yaml)
Usage: {{ include "common-lib.vault.template.yaml" (dict "secretPath" .Values.vault.secretPath) }}
*/}}
{{- define "common-lib.vault.template.yaml" -}}
{{- $secretPath := .secretPath | default "secret/data/info-service" -}}
vault.hashicorp.com/agent-inject-template-config.yaml: |
  {{- with secret $secretPath }}
  # Vault secrets - generated {{ now }}
  ---
  metadata:
    generated_at: {{ now }}
    version: {{ .Data.metadata.version }}
    created_time: {{ .Data.metadata.created_time }}
  secrets:
    {{- range $key, $value := .Data.data }}
    {{ $key }}: {{ $value | quote }}
    {{- end }}
  application:
    name: {{ $.ctx.Chart.Name }}
    environment: {{ $.ctx.Values.env.APP_NAME }}
  {{- end }}
{{- end }}

{{/*
Dynamic secret update with command
Usage: {{ include "common-lib.vault.command" . }}
*/}}
{{- define "common-lib.vault.command" -}}
vault.hashicorp.com/agent-inject-command: |
  #!/bin/sh
  echo "Secrets updated at $(date)" >> /dev/termination-log
  kill -HUP 1  # Send SIGHUP to main process to reload config
{{- end }}
