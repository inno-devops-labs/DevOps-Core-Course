{{/*
Chart-specific labels built on top of the shared library chart.
*/}}
{{- define "devops-info.baseLabels" -}}
{{ include "common-lib.labels" . }}
app.kubernetes.io/part-of: {{ .Values.partOf | quote }}
{{- end -}}

{{- define "devops-info.deploymentLabels" -}}
{{ include "devops-info.baseLabels" . }}
app.kubernetes.io/component: "api"
{{- end -}}

{{- define "devops-info.serviceLabels" -}}
{{ include "devops-info.baseLabels" . }}
app.kubernetes.io/component: "service"
{{- end -}}

{{- define "devops-info.hookLabels" -}}
{{ include "devops-info.baseLabels" . }}
app.kubernetes.io/component: "hook"
{{- end -}}

{{- define "devops-info.serviceAccountName" -}}
{{- if .Values.serviceAccount.create -}}
{{- default (printf "%s-sa" (include "common-lib.fullname" .)) .Values.serviceAccount.name -}}
{{- else -}}
{{- default "default" .Values.serviceAccount.name -}}
{{- end -}}
{{- end -}}

{{- define "devops-info.secretName" -}}
{{- default (printf "%s-secret" (include "common-lib.fullname" .)) .Values.secret.name -}}
{{- end -}}

{{/*
Name for the ConfigMap that exposes environment variables.
*/}}
{{- define "devops-info.envConfigMapName" -}}
{{- default (printf "%s-env" (include "common-lib.fullname" .)) .Values.configMap.envName -}}
{{- end -}}

{{/*
Name for the ConfigMap that exposes the mounted JSON file.
*/}}
{{- define "devops-info.fileConfigMapName" -}}
{{- default (printf "%s-config" (include "common-lib.fullname" .)) .Values.configMap.fileNameOverride -}}
{{- end -}}

{{/*
Name for the PVC that stores the visits counter.
*/}}
{{- define "devops-info.persistenceClaimName" -}}
{{- default (printf "%s-data" (include "common-lib.fullname" .)) .Values.persistence.claimName -}}
{{- end -}}

{{/*
Render the Vault Agent template that writes secrets in .env format.
*/}}
{{- define "devops-info.vaultSecretTemplate" -}}
{{- printf "{{- with secret %q -}}\nAPP_USERNAME={{ .Data.data.username }}\nAPP_PASSWORD={{ .Data.data.password }}\n{{- end -}}\n" .Values.vault.secretPath -}}
{{- end -}}

{{/*
Render Vault Agent injector annotations for the pod template.
*/}}
{{- define "devops-info.vaultAnnotations" -}}
{{- if .Values.vault.enabled }}
vault.hashicorp.com/agent-inject: "true"
vault.hashicorp.com/auth-type: {{ .Values.vault.authType | quote }}
vault.hashicorp.com/auth-path: {{ .Values.vault.authPath | quote }}
vault.hashicorp.com/role: {{ .Values.vault.role | quote }}
vault.hashicorp.com/agent-run-as-same-user: {{ .Values.vault.runAsSameUser | quote }}
vault.hashicorp.com/agent-inject-secret-{{ .Values.vault.secretName }}: {{ .Values.vault.secretPath | quote }}
vault.hashicorp.com/secret-volume-path-{{ .Values.vault.secretName }}: {{ .Values.vault.secretVolumePath | quote }}
vault.hashicorp.com/agent-inject-file-{{ .Values.vault.secretName }}: {{ .Values.vault.fileName | quote }}
vault.hashicorp.com/agent-inject-perms-{{ .Values.vault.secretName }}: {{ .Values.vault.filePermissions | quote }}
vault.hashicorp.com/agent-inject-template-{{ .Values.vault.secretName }}: |
{{ include "devops-info.vaultSecretTemplate" . | indent 2 }}
{{- if .Values.vault.command }}
vault.hashicorp.com/agent-inject-command-{{ .Values.vault.secretName }}: {{ .Values.vault.command | quote }}
{{- end }}
{{- end }}
{{- end -}}
