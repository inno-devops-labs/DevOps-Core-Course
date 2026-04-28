{{- define "devops-python.name" -}}
{{- include "common-lib.name" . -}}
{{- end -}}

{{- define "devops-python.fullname" -}}
{{- include "common-lib.fullname" . -}}
{{- end -}}

{{- define "devops-python.labels" -}}
{{- include "common-lib.labels" . -}}
{{- end -}}

{{- define "devops-python.selectorLabels" -}}
{{- include "common-lib.selectorLabels" . -}}
{{- end -}}

{{- define "devops-python.serviceAccountName" -}}
{{- if .Values.serviceAccount.create -}}
{{- default (include "devops-python.fullname" .) .Values.serviceAccount.name -}}
{{- else -}}
{{- default "default" .Values.serviceAccount.name -}}
{{- end -}}
{{- end -}}

{{- define "devops-python.secretName" -}}
{{- if .Values.secrets.name -}}
{{- .Values.secrets.name -}}
{{- else -}}
{{- printf "%s-credentials" (include "devops-python.fullname" .) -}}
{{- end -}}
{{- end -}}

{{- define "devops-python.envVars" -}}
- name: APP_ENV
  value: {{ .Values.app.environment | quote }}
- name: LOG_LEVEL
  value: {{ .Values.app.logLevel | quote }}
{{- end -}}

{{- define "devops-python.configFileName" -}}
{{- printf "%s-config" (include "devops-python.fullname" .) -}}
{{- end -}}

{{- define "devops-python.configEnvName" -}}
{{- printf "%s-env" (include "devops-python.fullname" .) -}}
{{- end -}}

{{- define "devops-python.pvcName" -}}
{{- printf "%s-data" (include "devops-python.fullname" .) -}}
{{- end -}}

{{- define "devops-python.previewServiceName" -}}
{{- printf "%s-preview" (include "devops-python.fullname" .) -}}
{{- end -}}

{{- define "devops-python.analysisTemplateName" -}}
{{- printf "%s-health-analysis" (include "devops-python.fullname" .) -}}
{{- end -}}
