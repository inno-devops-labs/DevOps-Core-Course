#!/usr/bin/env bash
# Устанавливает провайдер yandex в локальное зеркало (обход блокировки registry.terraform.io).
# Запуск: ./setup-provider-mirror.sh

set -e
TERRAFORM_DIR="$(cd "$(dirname "$0")" && pwd)"
MIRROR_ROOT="${TERRAFORM_DIR}/.provider-mirror"
VERSION="0.100.0"
# GitHub releases доступны даже при блокировке registry.terraform.io
BASE_URL="https://github.com/yandex-cloud/terraform-provider-yandex/releases/download/v${VERSION}"

case "$(uname -s)" in
  Darwin)  OS="darwin" ;;
  Linux)   OS="linux" ;;
  *)       echo "Unsupported OS"; exit 1 ;;
esac
case "$(uname -m)" in
  x86_64|amd64)  ARCH="amd64" ;;
  arm64|aarch64) ARCH="arm64" ;;
  *)             echo "Unsupported arch"; exit 1 ;;
esac
PLATFORM="${OS}_${ARCH}"
ZIP="terraform-provider-yandex_${VERSION}_${OS}_${ARCH}.zip"
URL="${BASE_URL}/${ZIP}"

mkdir -p "${MIRROR_ROOT}/registry.terraform.io/yandex-cloud/yandex/${VERSION}/${PLATFORM}"
cd "${MIRROR_ROOT}/registry.terraform.io/yandex-cloud/yandex/${VERSION}/${PLATFORM}"

if [[ -f "${ZIP}" ]]; then
  echo "Provider already present: ${ZIP}"
  exit 0
fi

echo "Downloading ${URL} ..."
curl -sL -o "${ZIP}" "${URL}" || { echo "Download failed. Check network or use VPN."; exit 1; }
echo "Done. Mirror at ${MIRROR_ROOT}"

# Генерируем .terraformrc с путём к зеркалу (абсолютный путь)
cat > "${TERRAFORM_DIR}/.terraformrc.mirror" << EOF
# Локальное зеркало провайдера yandex (обход блокировки registry)
provider_installation {
  filesystem_mirror {
    path    = "${MIRROR_ROOT}"
    include = ["registry.terraform.io/yandex-cloud/*"]
  }
  direct {
    exclude = ["registry.terraform.io/yandex-cloud/*"]
  }
}
EOF
echo "Created ${TERRAFORM_DIR}/.terraformrc.mirror"
