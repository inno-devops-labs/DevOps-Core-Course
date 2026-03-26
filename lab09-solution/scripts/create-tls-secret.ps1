# Creates self-signed cert for local.example.com and TLS secret in namespace lab09
$ErrorActionPreference = "Stop"
$dir = Split-Path -Parent $MyInvocation.MyCommand.Path
$certDir = Join-Path $dir "certs"
New-Item -ItemType Directory -Force -Path $certDir | Out-Null
$key = Join-Path $certDir "tls.key"
$crt = Join-Path $certDir "tls.crt"

openssl req -x509 -nodes -days 365 -newkey rsa:2048 `
  -keyout $key -out $crt `
  -subj "/CN=local.example.com/O=local.example.com"

kubectl create secret tls tls-secret --namespace=lab09 --key=$key --cert=$crt --dry-run=client -o yaml | kubectl apply -f -

Write-Host "Done. Add to hosts: <cluster-ip> local.example.com"
Write-Host "Test: curl -k https://local.example.com/app1/  and  curl -k https://local.example.com/app2/"
