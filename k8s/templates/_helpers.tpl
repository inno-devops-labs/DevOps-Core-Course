{{- define "python-app.name" -}}
python-app
{{- end }}

{{- define "python-app.fullname" -}}
{{ include "python-app.name" . }}-{{ .Release.Name }}
{{- end }}

{{- define "python-app.labels" -}}
app: {{ include "python-app.name" . }}
app.kubernetes.io/name: {{ include "python-app.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{- define "python-app.headlessServiceName" -}}
{{ include "python-app.fullname" . }}-headless
{{- end }}

{{- define "python-app.headlessServiceName" -}}
{{ include "python-app.fullname" . }}-headless
{{- end }}