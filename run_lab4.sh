#!/bin/bash
# Скрипт для автоматического выполнения Lab 4
# Запускайте после настройки Yandex Cloud credentials

set -e  # Остановка при ошибке

echo "🚀 Начало выполнения Lab 4"
echo "================================"

# Проверка переменных окружения (ключ ИЛИ OAuth-токен через yc)
echo ""
echo "📋 Проверка переменных окружения..."
if [ -z "$YANDEX_CLOUD_ID" ] || [ -z "$YANDEX_FOLDER_ID" ]; then
    echo "❌ ОШИБКА: Задайте YANDEX_CLOUD_ID и YANDEX_FOLDER_ID"
    echo "Пример: export YANDEX_CLOUD_ID=... YANDEX_FOLDER_ID=..."
    exit 1
fi

# Если задан путь к ключу, но файла нет — пробуем скопировать из .yandex_key_temp.json в репозитории
if [ -n "$YANDEX_SERVICE_ACCOUNT_KEY_FILE" ]; then
    if [ ! -f "$YANDEX_SERVICE_ACCOUNT_KEY_FILE" ]; then
        REPO_ROOT="$(cd "$(dirname "$0")" && pwd)"
        if [ -f "$REPO_ROOT/.yandex_key_temp.json" ]; then
            mkdir -p "$(dirname "$YANDEX_SERVICE_ACCOUNT_KEY_FILE")"
            cp "$REPO_ROOT/.yandex_key_temp.json" "$YANDEX_SERVICE_ACCOUNT_KEY_FILE"
            echo "✅ Ключ скопирован из .yandex_key_temp.json в $YANDEX_SERVICE_ACCOUNT_KEY_FILE"
        else
            echo "❌ ОШИБКА: Файл ключа не найден: $YANDEX_SERVICE_ACCOUNT_KEY_FILE"
            echo "   Положите JSON-ключ в этот путь или в корень репо как .yandex_key_temp.json"
            exit 1
        fi
    fi
    if [ -f "$YANDEX_SERVICE_ACCOUNT_KEY_FILE" ]; then
        echo "✅ Auth: Service Account key file"
    fi
elif command -v yc &>/dev/null; then
    export YANDEX_TOKEN=$(yc iam create-token 2>/dev/null) || true
    if [ -z "$YANDEX_TOKEN" ]; then
        echo "❌ ОШИБКА: Выполните 'yc login' или задайте YANDEX_SERVICE_ACCOUNT_KEY_FILE"
        exit 1
    fi
    echo "✅ Auth: yc OAuth token"
else
    echo "❌ ОШИБКА: Задайте YANDEX_SERVICE_ACCOUNT_KEY_FILE (путь к JSON-ключу) или установите yc и выполните yc login"
    exit 1
fi

echo "✅ Cloud ID: $YANDEX_CLOUD_ID"
echo "✅ Folder ID: $YANDEX_FOLDER_ID"

# Создаём директорию для сохранения выводов
OUTPUT_DIR="lab4_outputs"
mkdir -p "$OUTPUT_DIR"

echo ""
echo "================================"
echo "📦 TASK 1: Terraform Implementation"
echo "================================"

cd terraform

echo ""
echo "1️⃣ Инициализация Terraform..."
terraform init | tee "../$OUTPUT_DIR/terraform_init.txt"

echo ""
echo "2️⃣ Форматирование кода..."
terraform fmt

echo ""
echo "3️⃣ Валидация конфигурации..."
terraform validate | tee "../$OUTPUT_DIR/terraform_validate.txt"

echo ""
echo "4️⃣ Предпросмотр изменений (terraform plan)..."
terraform plan | tee "../$OUTPUT_DIR/terraform_plan.txt"

echo ""
echo "5️⃣ Применение инфраструктуры (terraform apply)..."
echo "⚠️  Это создаст реальные ресурсы в Yandex Cloud!"
read -p "Продолжить? (yes/no): " confirm
if [ "$confirm" != "yes" ]; then
    echo "Отменено пользователем"
    exit 0
fi

terraform apply -auto-approve | tee "../$OUTPUT_DIR/terraform_apply.txt"

echo ""
echo "6️⃣ Получение выходных значений..."
terraform output | tee "../$OUTPUT_DIR/terraform_output.txt"

VM_IP=$(terraform output -raw vm_public_ip)
SSH_CMD=$(terraform output -raw ssh_command)

echo ""
echo "✅ Terraform инфраструктура создана!"
echo "📝 Public IP: $VM_IP"
echo "🔑 SSH команда: $SSH_CMD"

echo ""
echo "7️⃣ Проверка SSH доступа..."
echo "Ожидание 30 секунд для инициализации VM..."
sleep 30

if ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 ubuntu@$VM_IP "echo 'SSH connection successful'" 2>/dev/null; then
    echo "✅ SSH доступ работает!"
    ssh -o StrictHostKeyChecking=no ubuntu@$VM_IP "hostname && uname -a" | tee "../$OUTPUT_DIR/ssh_terraform_verify.txt"
else
    echo "⚠️  SSH пока недоступен (VM может ещё инициализироваться)"
    echo "Попробуйте подключиться позже: $SSH_CMD"
fi

cd ..

echo ""
echo "================================"
echo "📦 TASK 2: Pulumi Implementation"
echo "================================"

echo ""
echo "1️⃣ Удаление Terraform инфраструктуры..."
cd terraform
read -p "Удалить Terraform ресурсы перед созданием Pulumi? (yes/no): " destroy_confirm
if [ "$destroy_confirm" = "yes" ]; then
    terraform destroy -auto-approve | tee "../$OUTPUT_DIR/terraform_destroy.txt"
    echo "✅ Terraform ресурсы удалены"
else
    echo "⚠️  Terraform ресурсы сохранены (будет 2 VM)"
fi
cd ..

echo ""
echo "2️⃣ Настройка Pulumi..."
cd pulumi

# Проверка входа в Pulumi
if ! pulumi whoami &>/dev/null; then
    echo "⚠️  Требуется вход в Pulumi Cloud"
    echo "Выполните: pulumi login"
    echo "Затем запустите скрипт снова"
    exit 1
fi

# Создание virtual environment если его нет
if [ ! -d "venv" ]; then
    echo "Создание Python virtual environment..."
    python3 -m venv venv
fi

echo "Активация virtual environment..."
source venv/bin/activate

echo "Установка зависимостей..."
pip install -q -r requirements.txt

echo ""
echo "3️⃣ Настройка Pulumi config..."
MY_IP=$(curl -s ifconfig.me)
pulumi config set project_name devops-lab4 --stack dev 2>/dev/null || pulumi stack init dev
pulumi config set zone ru-central1-a --stack dev
pulumi config set ssh_allowed_cidr "${MY_IP}/32" --stack dev
pulumi config set ssh_user ubuntu --stack dev
pulumi config set ssh_public_key_path ~/.ssh/id_rsa.pub --stack dev

echo ""
echo "4️⃣ Предпросмотр изменений (pulumi preview)..."
pulumi preview --stack dev | tee "../$OUTPUT_DIR/pulumi_preview.txt"

echo ""
echo "5️⃣ Применение инфраструктуры (pulumi up)..."
echo "⚠️  Это создаст реальные ресурсы в Yandex Cloud!"
read -p "Продолжить? (yes/no): " confirm
if [ "$confirm" != "yes" ]; then
    echo "Отменено пользователем"
    exit 0
fi

pulumi up --yes --stack dev | tee "../$OUTPUT_DIR/pulumi_up.txt"

echo ""
echo "6️⃣ Получение выходных значений..."
pulumi stack output --stack dev | tee "../$OUTPUT_DIR/pulumi_output.txt"

PULUMI_VM_IP=$(pulumi stack output vm_public_ip --stack dev)

echo ""
echo "✅ Pulumi инфраструктура создана!"
echo "📝 Public IP: $PULUMI_VM_IP"

echo ""
echo "7️⃣ Проверка SSH доступа..."
echo "Ожидание 30 секунд для инициализации VM..."
sleep 30

if ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 ubuntu@$PULUMI_VM_IP "echo 'SSH connection successful'" 2>/dev/null; then
    echo "✅ SSH доступ работает!"
    ssh -o StrictHostKeyChecking=no ubuntu@$PULUMI_VM_IP "hostname && uname -a" | tee "../$OUTPUT_DIR/ssh_pulumi_verify.txt"
else
    echo "⚠️  SSH пока недоступен (VM может ещё инициализироваться)"
    echo "Попробуйте подключиться позже: ssh ubuntu@$PULUMI_VM_IP"
fi

deactivate
cd ..

echo ""
echo "================================"
echo "✅ Lab 4 выполнена!"
echo "================================"
echo ""
echo "📁 Все выводы команд сохранены в директории: $OUTPUT_DIR/"
echo ""
echo "📝 Следующие шаги:"
echo "1. Заполните terraform/docs/LAB04.md с выводами из $OUTPUT_DIR/"
echo "2. Решите, какую VM оставить для Lab 5 (Terraform или Pulumi)"
echo "3. Удалите ненужную VM:"
echo "   - Terraform: cd terraform && terraform destroy"
echo "   - Pulumi: cd pulumi && pulumi destroy --stack dev"
echo ""
echo "⚠️  ВАЖНО: Не коммитьте файлы из $OUTPUT_DIR/ в Git (могут содержать секреты)"
