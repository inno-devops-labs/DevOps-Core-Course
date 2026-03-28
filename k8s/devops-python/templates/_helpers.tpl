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
