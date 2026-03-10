#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
EVIDENCE_DIR="${ROOT_DIR}/docs/lab04-evidence"
TERRAFORM_YANDEX_DIR="${ROOT_DIR}/terraform"
TERRAFORM_DOCKER_DIR="${ROOT_DIR}/terraform/docker"
TERRAFORM_GITHUB_DIR="${ROOT_DIR}/terraform/github-import"
PULUMI_DIR="${ROOT_DIR}/pulumi"

# --- Yandex Cloud credentials ---
# Set your Cloud ID and Folder ID (visible in console.cloud.yandex.ru header or folder settings).
# If unset, defaults below are used; on "Folder not found" set correct values.
export YANDEX_CLOUD_ID="${YANDEX_CLOUD_ID:-b1gcp8cg7tvn2caegjgd}"
export YANDEX_FOLDER_ID="${YANDEX_FOLDER_ID:-b1glfo9hga197p8d8ork}"
export YANDEX_SERVICE_ACCOUNT_KEY_FILE="${YANDEX_SERVICE_ACCOUNT_KEY_FILE:-$HOME/.yandex/key.json}"

# If key file is missing, copy from temp file in repo
if [[ ! -f "$YANDEX_SERVICE_ACCOUNT_KEY_FILE" ]] && [[ -f "${ROOT_DIR}/.yandex_key_temp.json" ]]; then
  mkdir -p "$(dirname "$YANDEX_SERVICE_ACCOUNT_KEY_FILE")"
  cp "${ROOT_DIR}/.yandex_key_temp.json" "$YANDEX_SERVICE_ACCOUNT_KEY_FILE"
  echo "Key copied to $YANDEX_SERVICE_ACCOUNT_KEY_FILE"
fi

mkdir -p "${EVIDENCE_DIR}"

log() {
  echo "[$(date +'%Y-%m-%d %H:%M:%S')] $*"
}

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || {
    echo "Error: required command '$1' is not installed." >&2
    exit 1
  }
}

# Check Yandex env vars before Terraform/Pulumi
check_yandex_env() {
  if [[ -z "$YANDEX_CLOUD_ID" ]] || [[ -z "$YANDEX_FOLDER_ID" ]]; then
    echo "Error: set YANDEX_CLOUD_ID and YANDEX_FOLDER_ID (or they are set above in script)." >&2
    exit 1
  fi
  if [[ -n "$YANDEX_SERVICE_ACCOUNT_KEY_FILE" ]] && [[ ! -f "$YANDEX_SERVICE_ACCOUNT_KEY_FILE" ]]; then
    echo "Error: key file not found: $YANDEX_SERVICE_ACCOUNT_KEY_FILE" >&2
    exit 1
  fi
}

# Create terraform.tfvars from example if missing (with your IP for SSH)
ensure_terraform_tfvars() {
  cd "${TERRAFORM_YANDEX_DIR}"
  if [[ ! -f terraform.tfvars ]]; then
    MY_IP="$(curl -s --max-time 5 ifconfig.me 2>/dev/null || echo '0.0.0.0')"
    sed "s|ssh_allowed_cidr = .*|ssh_allowed_cidr = \"${MY_IP}/32\"|" terraform.tfvars.example > terraform.tfvars
    log "Created terraform.tfvars with ssh_allowed_cidr=${MY_IP}/32"
  fi
  cd "${ROOT_DIR}"
}

run_terraform_yandex() {
  require_cmd terraform
  require_cmd ssh
  check_yandex_env
  ensure_terraform_tfvars

  # Pass credentials to Terraform via TF_VAR_ (yandex provider requires them explicitly)
  export TF_VAR_yandex_cloud_id="${YANDEX_CLOUD_ID}"
  export TF_VAR_yandex_folder_id="${YANDEX_FOLDER_ID}"
  export TF_VAR_yandex_service_account_key_file="${YANDEX_SERVICE_ACCOUNT_KEY_FILE}"

  # Workaround for broken .terraformrc or registry block: use minimal config first
  local tf_rc="${TERRAFORM_YANDEX_DIR}/.terraformrc.minimal"
  if [[ -f "$tf_rc" ]]; then
    export TF_CLI_CONFIG_FILE="$tf_rc"
    log "Using TF_CLI_CONFIG_FILE=$tf_rc"
  fi

  cd "${TERRAFORM_YANDEX_DIR}"
  log "Terraform (yandex): init"
  if ! terraform init -no-color -input=false 2>&1 | tee "${EVIDENCE_DIR}/tf-init.txt"; then
    if grep -q "Invalid provider registry host" "${EVIDENCE_DIR}/tf-init.txt" 2>/dev/null; then
      log "Registry unreachable — downloading provider from GitHub and setting up mirror"
      local mirror_rc="${TERRAFORM_YANDEX_DIR}/.terraformrc.mirror"
      local setup_script="${TERRAFORM_YANDEX_DIR}/setup-provider-mirror.sh"
      if [[ -x "$setup_script" ]]; then
        bash "$setup_script" || true
      fi
      if [[ -f "$mirror_rc" ]]; then
        export TF_CLI_CONFIG_FILE="$mirror_rc"
        log "Retrying init with mirror"
        if ! terraform init -no-color -input=false 2>&1 | tee -a "${EVIDENCE_DIR}/tf-init.txt"; then
          echo ""; echo "Error after mirror. Check: ./terraform/setup-provider-mirror.sh or use VPN."
          exit 1
        fi
      else
        echo ""; echo "Run manually: cd terraform && ./setup-provider-mirror.sh then ./lab04_evidence.sh terraform again. Or use VPN."
        exit 1
      fi
    else
      exit 1
    fi
  fi

  log "Terraform (yandex): fmt"
  terraform fmt -recursive | tee "${EVIDENCE_DIR}/tf-fmt.txt"

  log "Terraform (yandex): validate"
  terraform validate -no-color | tee "${EVIDENCE_DIR}/tf-validate.txt"

  log "Terraform (yandex): plan"
  terraform plan -no-color -out=tfplan | tee "${EVIDENCE_DIR}/tf-plan.txt"

  log "Terraform (yandex): apply"
  if ! terraform apply -no-color -auto-approve tfplan 2>&1 | tee "${EVIDENCE_DIR}/tf-apply.txt"; then
    if grep -q "Folder with id.*not found\|not found" "${EVIDENCE_DIR}/tf-apply.txt" 2>/dev/null; then
      echo ""
      echo "Error: Folder not found. Set correct Cloud ID and Folder ID from Yandex Cloud console:"
      echo "  export YANDEX_CLOUD_ID=\"your-cloud-id\""
      echo "  export YANDEX_FOLDER_ID=\"your-folder-id\""
      echo "Then run again: ./lab04_evidence.sh terraform"
      exit 1
    fi
    exit 1
  fi

  log "Terraform (yandex): output"
  terraform output -no-color | tee "${EVIDENCE_DIR}/tf-output.txt"

  local ip
  ip="$(terraform output -raw vm_public_ip 2>/dev/null || true)"
  local ssh_user="${SSH_USER:-ubuntu}"

  if [[ -n "$ip" ]]; then
    log "Terraform (yandex): ssh proof (waiting 30s for VM boot)"
    sleep 30
    if ssh -o StrictHostKeyChecking=accept-new -o ConnectTimeout=15 "${ssh_user}@${ip}" \
      "hostname; uptime; free -h" 2>/dev/null | tee "${EVIDENCE_DIR}/tf-ssh-proof.txt"; then
      log "Terraform (yandex): SSH proof OK"
    else
      log "Terraform (yandex): SSH not ready yet, try later: ssh ${ssh_user}@${ip}"
      echo "(SSH failed or timeout)" >> "${EVIDENCE_DIR}/tf-ssh-proof.txt"
    fi
  else
    log "Terraform (yandex): vm_public_ip output missing, skip SSH proof"
  fi

  log "Terraform (yandex) evidence completed"
}

run_terraform_yandex_destroy() {
  require_cmd terraform
  check_yandex_env
  export TF_VAR_yandex_cloud_id="${YANDEX_CLOUD_ID}"
  export TF_VAR_yandex_folder_id="${YANDEX_FOLDER_ID}"
  export TF_VAR_yandex_service_account_key_file="${YANDEX_SERVICE_ACCOUNT_KEY_FILE}"
  local tf_rc="${TERRAFORM_YANDEX_DIR}/.terraformrc.mirror"
  if [[ ! -f "$tf_rc" ]]; then
    tf_rc="${TERRAFORM_YANDEX_DIR}/.terraformrc.minimal"
  fi
  [[ -f "$tf_rc" ]] && export TF_CLI_CONFIG_FILE="$tf_rc"
  cd "${TERRAFORM_YANDEX_DIR}"
  log "Terraform (yandex): destroy"
  terraform destroy -no-color -auto-approve | tee "${EVIDENCE_DIR}/tf-destroy.txt"
}

run_terraform_docker_destroy() {
  if [[ ! -d "${TERRAFORM_DOCKER_DIR}" ]]; then
    log "Terraform (docker): directory not found, skip"
    return 0
  fi
  require_cmd terraform
  cd "${TERRAFORM_DOCKER_DIR}"
  log "Terraform (docker): destroy"
  terraform destroy -no-color -auto-approve | tee "${EVIDENCE_DIR}/tf-docker-destroy.txt"
}

run_pulumi() {
  require_cmd pulumi
  require_cmd python3
  require_cmd ssh
  check_yandex_env

  cd "${PULUMI_DIR}"

  # Use local backend so no interactive login is required
  export PULUMI_BACKEND_URL="${PULUMI_BACKEND_URL:-file://.}"
  log "Pulumi: using backend ${PULUMI_BACKEND_URL}"
  # Set passphrase for secrets encryption (required for local backend)
  # For dev/lab environment, using a simple passphrase is acceptable
  export PULUMI_CONFIG_PASSPHRASE="${PULUMI_CONFIG_PASSPHRASE:-devops-lab4-dev}"
  # Ensure backend is initialized (login to local backend)
  pulumi login "${PULUMI_BACKEND_URL}" --non-interactive 2>&1 || {
    log "Pulumi: backend login may have failed, continuing anyway"
  }

  if [[ ! -d venv ]]; then
    log "Pulumi: creating venv"
    python3 -m venv venv
  fi

  # shellcheck disable=SC1091
  source venv/bin/activate
  # Force Pulumi subprocess to use venv's Python (so it sees setuptools/pkg_resources)
  export PATH="${PULUMI_DIR}/venv/bin:${PATH}"
  export VIRTUAL_ENV="${PULUMI_DIR}/venv"

  log "Pulumi: install dependencies"
  pip install -q -U setuptools
  pip install -q -r requirements.txt | tee "${EVIDENCE_DIR}/pulumi-pip-install.txt"
  # pkg_resources is required by pulumi_yandex (from setuptools); Python 3.12+ does not ship it
  if ! python -c "import pkg_resources" 2>/dev/null; then
    log "Pulumi: pkg_resources missing, reinstalling setuptools and retrying"
    pip install --force-reinstall -q setuptools
    if ! python -c "import pkg_resources" 2>/dev/null; then
      log "Pulumi: removing venv and recreating (fix pkg_resources)"
      deactivate 2>/dev/null || true
      rm -rf venv
      python3 -m venv venv
      source venv/bin/activate
      export PATH="${PULUMI_DIR}/venv/bin:${PATH}"
      export VIRTUAL_ENV="${PULUMI_DIR}/venv"
      pip install -q -U setuptools
      pip install -q -r requirements.txt | tee "${EVIDENCE_DIR}/pulumi-pip-install.txt"
    fi
  fi

  # Stack dev: select or create
  log "Pulumi: ensuring stack dev exists"
  # Try to select first (if exists)
  if pulumi stack select dev 2>/dev/null; then
    log "Pulumi: stack dev selected successfully"
  else
    # Stack doesn't exist, create it
    log "Pulumi: creating stack dev"
    # Create with non-interactive flag
    if pulumi stack init dev --non-interactive 2>&1; then
      log "Pulumi: stack dev created successfully"
    else
      log "Pulumi: stack init returned error (may already exist or need different approach)"
    fi
    # Now select it
    if pulumi stack select dev 2>&1; then
      log "Pulumi: stack dev selected successfully"
    else
      log "Pulumi: ERROR - failed to create/select stack dev"
      log "Pulumi: listing available stacks:"
      pulumi stack ls 2>&1 || true
      log "Pulumi: trying alternative: pulumi stack init dev (without flags)"
      pulumi stack init dev 2>&1 || true
      pulumi stack select dev 2>&1 || {
        log "Pulumi: FATAL - cannot proceed without stack dev"
        exit 1
      }
    fi
  fi

  # Test if we can access stack config (check passphrase)
  log "Pulumi: testing stack config access"
  if ! pulumi config ls 2>/dev/null >/dev/null; then
    log "Pulumi: cannot access stack config (wrong passphrase), removing and recreating stack"
    pulumi stack rm dev --yes --non-interactive 2>&1 || true
    pulumi stack init dev --non-interactive 2>&1 || true
    pulumi stack select dev 2>&1 || {
      log "Pulumi: FATAL - failed to recreate stack dev"
      exit 1
    }
    log "Pulumi: stack dev recreated successfully"
  fi

  # Config (your IP for SSH, key path)
  MY_IP="${MY_IP:-$(curl -s --max-time 5 ifconfig.me 2>/dev/null || echo '0.0.0.0')}"
  pulumi config set project_name devops-lab4 2>/dev/null || true
  pulumi config set zone ru-central1-a 2>/dev/null || true
  pulumi config set ssh_allowed_cidr "${MY_IP}/32" 2>/dev/null || true
  pulumi config set ssh_user ubuntu 2>/dev/null || true
  pulumi config set ssh_public_key_path ~/.ssh/id_rsa.pub 2>/dev/null || true

  log "Pulumi: preview"
  pulumi preview --non-interactive 2>&1 | tee "${EVIDENCE_DIR}/pulumi-preview.txt"

  log "Pulumi: up"
  pulumi up --yes --non-interactive 2>&1 | tee "${EVIDENCE_DIR}/pulumi-up.txt"

  log "Pulumi: stack output"
  pulumi stack output 2>&1 | tee "${EVIDENCE_DIR}/pulumi-output.txt"

  local ip
  ip="$(pulumi stack output vm_public_ip 2>/dev/null || true)"
  local ssh_user
  ssh_user="$(pulumi config get ssh_user 2>/dev/null || echo ubuntu)"

  if [[ -n "$ip" ]]; then
    log "Pulumi: ssh proof (waiting 30s for VM boot)"
    sleep 30
    if ssh -o StrictHostKeyChecking=accept-new -o ConnectTimeout=15 "${ssh_user}@${ip}" \
      "hostname; uptime; free -h" 2>/dev/null | tee "${EVIDENCE_DIR}/pulumi-ssh-proof.txt"; then
      log "Pulumi: SSH proof OK"
    else
      log "Pulumi: SSH not ready yet, try later: ssh ${ssh_user}@${ip}"
      echo "(SSH failed or timeout)" >> "${EVIDENCE_DIR}/pulumi-ssh-proof.txt"
    fi
  else
    log "Pulumi: vm_public_ip output missing, skip SSH proof"
  fi

  log "Pulumi evidence completed"
}

run_pulumi_destroy() {
  require_cmd pulumi
  cd "${PULUMI_DIR}"
  export PULUMI_BACKEND_URL="${PULUMI_BACKEND_URL:-file://.}"
  export PULUMI_CONFIG_PASSPHRASE="${PULUMI_CONFIG_PASSPHRASE:-devops-lab4-dev}"

  if [[ -f venv/bin/activate ]]; then
    # shellcheck disable=SC1091
    source venv/bin/activate
  fi

  log "Pulumi: destroy"
  pulumi destroy --yes --non-interactive 2>&1 | tee "${EVIDENCE_DIR}/pulumi-destroy.txt"
}

run_bonus_import() {
  require_cmd terraform
  cd "${TERRAFORM_GITHUB_DIR}"

  log "Terraform (github): init"
  terraform init -no-color -input=false | tee "${EVIDENCE_DIR}/gh-init.txt"

  log "Terraform (github): validate"
  terraform validate -no-color | tee "${EVIDENCE_DIR}/gh-validate.txt"

  if [[ -z "${IMPORT_REPO_ID:-}" ]]; then
    echo "Error: set IMPORT_REPO_ID env var, example: IMPORT_REPO_ID=DevOps-Core-Course" >&2
    exit 1
  fi

  log "Terraform (github): import ${IMPORT_REPO_ID}"
  terraform import "github_repository.course_repo" "${IMPORT_REPO_ID}" 2>&1 | tee "${EVIDENCE_DIR}/gh-import.txt"

  log "Terraform (github): plan after import"
  terraform plan -no-color 2>&1 | tee "${EVIDENCE_DIR}/gh-plan-after-import.txt"

  log "Terraform (github): output"
  terraform output -no-color 2>&1 | tee "${EVIDENCE_DIR}/gh-output.txt"
}

usage() {
  cat <<USAGE
Usage: $(basename "$0") <command>

Commands:
  terraform          Run Terraform Yandex init/plan/apply/output + SSH proof
  pulumi             Run Pulumi preview/up/output + SSH proof
  bonus              Run GitHub import (set IMPORT_REPO_ID=YourRepoName)
  cleanup-terraform  Destroy Terraform Yandex resources
  cleanup-docker     Destroy Terraform docker resources (if exist)
  cleanup-pulumi     Destroy Pulumi resources

Your Yandex env (set in script or export before run):
  YANDEX_CLOUD_ID=${YANDEX_CLOUD_ID:-<not set>}
  YANDEX_FOLDER_ID=${YANDEX_FOLDER_ID:-<not set>}
  YANDEX_SERVICE_ACCOUNT_KEY_FILE=${YANDEX_SERVICE_ACCOUNT_KEY_FILE:-<not set>}

Examples:
  $(basename "$0") terraform
  $(basename "$0") pulumi
  $(basename "$0") cleanup-terraform && $(basename "$0") pulumi
  IMPORT_REPO_ID=DevOps-Core-Course $(basename "$0") bonus
USAGE
}

main() {
  if [[ $# -ne 1 ]]; then
    usage
    exit 1
  fi

  case "$1" in
    terraform)
      run_terraform_yandex
      ;;
    pulumi)
      run_pulumi
      ;;
    bonus)
      run_bonus_import
      ;;
    cleanup-terraform)
      run_terraform_yandex_destroy
      ;;
    cleanup-docker)
      run_terraform_docker_destroy
      ;;
    cleanup-pulumi)
      run_pulumi_destroy
      ;;
    *)
      usage
      exit 1
      ;;
  esac
}

main "$@"
