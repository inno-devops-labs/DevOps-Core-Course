{{- define "devops-python-v2.name" -}}
{{- include "common-lib.name" . -}}
{{- end -}}

{{- define "devops-python-v2.fullname" -}}
{{- include "common-lib.fullname" . -}}
{{- end -}}

{{- define "devops-python-v2.labels" -}}
{{- include "common-lib.labels" . -}}
{{- end -}}

{{- define "devops-python-v2.selectorLabels" -}}
{{- include "common-lib.selectorLabels" . -}}
{{- end -}}

{{- define "devops-python-v2.serviceAccountName" -}}
{{- if .Values.serviceAccount.create -}}
{{- default (include "devops-python-v2.fullname" .) .Values.serviceAccount.name -}}
{{- else -}}
{{- default "default" .Values.serviceAccount.name -}}
{{- end -}}
{{- end -}}
