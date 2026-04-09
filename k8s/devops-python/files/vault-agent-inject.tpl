{{- with secret "secret/data/myapp/config" -}}
USERNAME={{ .Data.data.username }}
PASSWORD={{ .Data.data.password }}
{{- end -}}
