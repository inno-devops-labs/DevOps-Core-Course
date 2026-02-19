#!/bin/bash
set -e

export PATH="$HOME/yandex-cloud/bin:$PATH"
export YANDEX_CLOUD_ID="b1gcp8cg7tvn2caegjgd"
export YANDEX_FOLDER_ID="b1g1fo9hga197p8d8ork"
export YANDEX_TOKEN=$(yc iam create-token 2>/dev/null)

cd "$(dirname "$0")"

echo "=== Terraform Init ==="
terraform init

echo ""
echo "=== Terraform Format ==="
terraform fmt -recursive

echo ""
echo "=== Terraform Validate ==="
terraform validate

echo ""
echo "=== Terraform Plan ==="
terraform plan -out=tfplan

echo ""
echo "✅ Все команды выполнены успешно!"
