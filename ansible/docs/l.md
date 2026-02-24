# Lab 05 — Ansible Fundamentals Implementation

## 1. Architecture Overview

**Ansible Version:** 2.16+  
**Target VM OS:** Ubuntu 24.04.4 LTS (WLS) 

### Role Structure

```
ansible/
│
├─ docs/
│   ├─ screenshots/                 # Screenshots of terminal
│   └─ LAB05.md                     # This documentation
│
├─ group_vars/
│   └─ all.yml                      # Encrypted credentials
│
├─ inventory/
│   └─ hosts.ini                    # Static inventory
│
├─ playbooks/
│   ├─ deploy.yml                   # Application deployment 
│   └─ provision.yml                # System provisioning playbook
│
├─ roles/
│   ├─ app_deploy/                  # Application deployment
│   │   ├─ defaults/main.yml
│   │   ├─ handlers/main.yml
│   │   └─ tasks/main.yml
│   │
│   ├─ common/                      # System provisioning
│   │   ├─ defaults/main.yml
│   │   └─ tasks/main.yml
│   │
│   └─ docker/                      # Docker installation
│       ├─ defaults/main.yml
│       ├─ handlers/main.yml
│       └─ tasks/main.yml
│
└─ ansible.cfg                      # Configuration

```

### Почему использовать роли?

1. **Переиспользуемость** — одна роль может применяться к разным проектам
2. **Организация** — четкая структура, легко навигировать
3. **Поддерживаемость** — изменения в одном месте
4. **Масштабируемость** — легко добавлять новые роли

---

## 2. Roles Documentation

### Role: common

**Назначение:** Базовая настройка всех серверов

**Переменные:**
- `common_packages` — список пакетов для установки (по умолчанию: python3-pip, curl, git, vim, htop, wget, net-tools)

**Задачи:**
- Update apt cache
- Install common packages
- Set timezone to UTC

**Зависимости:** Нет

---

### Role: docker

**Назначение:** Установка и настройка Docker

**Переменные:**
- `docker_user` — пользователь для добавления в docker группу (по умолчанию: ubuntu)

**Обработчики (Handlers):**
- `restart docker` — перезагрузка сервиса Docker

**Задачи:**
- Add Docker GPG key
- Add Docker repository
- Install Docker packages (docker-ce, docker-ce-cli, containerd.io)
- Start and enable Docker service
- Add user to docker group
- Install python3-docker

**Зависимости:** common

---

### Role: app_deploy

**Назначение:** Развертывание контейнеризованного приложения

**Переменные (из Vault):**
- `dockerhub_username` — имя пользователя Docker Hub
- `dockerhub_password` — пароль/токен Docker Hub
- `app_name` — имя приложения (по умолчанию: devops-app)
- `docker_image` — образ Docker
- `docker_image_tag` — версия образа (по умолчанию: latest)
- `app_port` — порт приложения (по умолчанию: 5000)

**Обработчики:**
- Restart application container (при необходимости)

**Задачи:**
1. Login to Docker Hub (с no_log для безопасности)
2. Pull Docker image
3. Stop existing container
4. Remove old container
5. Run new container с правильным маппингом портов
6. Wait for application port
7. Verify health endpoint

**Зависимости:** docker

---

## 3. Idempotency Demonstration

### First Run Output

```
PLAY [Provision web servers] ****

TASK [common : Update apt cache] **
changed: [your-vm-name]

TASK [common : Install common packages] **
changed: [your-vm-name]

TASK [docker : Add Docker GPG key] **
changed: [your-vm-name]

[... more tasks ...]

PLAY RECAP **
your-vm-name : ok=12 changed=11 unreachable=0 failed=0
```

### Second Run Output

```
PLAY [Provision web servers] ****

TASK [common : Update apt cache] **
ok: [your-vm-name]

TASK [common : Install common packages] **
ok: [your-vm-name]

TASK [docker : Add Docker GPG key] **
ok: [your-vm-name]

[... more tasks ...]

PLAY RECAP **
your-vm-name : ok=12 changed=0 unreachable=0 failed=0
```

### Analysis

**First run:** Все задачи показывали `changed` (желтый цвет), т.к. нужно было установить пакеты и настроить сервисы.

**Second run:** Все задачи показывали `ok` (зеленый цвет), т.к. система уже достигла желаемого состояния.

**Идемпотентность:** Используются stateful модули Ansible (apt, service, docker_container), которые проверяют текущее состояние и делают изменения только если необходимо.

---

## 4. Ansible Vault Usage

### Создание зашифрованного хранилища

```bash
ansible-vault create group_vars/all.yml
```

### Содержимое all.yml

```yaml
---
# Docker Hub credentials
dockerhub_username: your-username
dockerhub_password: your-access-token

# Application configuration
app_name: devops-app
docker_image: "{{ dockerhub_username }}/{{ app_name }}"
docker_image_tag: latest
app_port: 5000
app_container_name: "{{ app_name }}"
```

### Стратегия управления паролем

**Вариант 1:** Интерактивный ввод пароля
```bash
ansible-playbook playbooks/provision.yml --ask-vault-pass
```

**Вариант 2:** Файл с паролем (добавить в .gitignore!)
```bash
echo "my-vault-password" > .vault_pass
chmod 600 .vault_pass
ansible-playbook playbooks/provision.yml
```

### Почему Ansible Vault важен?

- ✅ Шифрует чувствительные данные
- ✅ Можно безопасно хранить в Git (зашифрованные файлы)
- ✅ Разделение кода и конфигурации
- ✅ Защита от случайного раскрытия учетных данных

---

## 5. Deployment Verification

### Запуск развертывания

```bash
ansible-playbook playbooks/deploy.yml --ask-vault-pass
```

### Проверка контейнера

```bash
# На VM или через Ansible
ansible webservers -a "docker ps"

# Output:
CONTAINER ID   IMAGE          COMMAND        CREATED      STATUS
abc123def456   user/app       "python app"   2 min ago    Up 2 minutes
```

### Проверка health endpoint

```bash
curl http://<VM-IP>:5000/health
# Output: {"status": "ok"}
```

### Проверка основного endpoint

```bash
curl http://<VM-IP>:5000/
# Output: Welcome to DevOps App!
```

---

## 6. Key Decisions

### Почему использовать роли вместо простых playbooks?

Роли обеспечивают переиспользуемость кода, четкую организацию и возможность комбинирования. Вместо больших monolithic playbooks, каждая роль отвечает ��а одну область (provisioning, Docker, deployment).

### Как роли улучшают переиспользуемость?

Одну роль (например, docker) можно использовать в разных playbooks и проектах. Достаточно передать нужные переменные.

### Что делает задачу идемпотентной?

Использование stateful модулей (apt, service, docker_container) вместо команд. Эти модули проверяют текущее состояние и действуют только при необходимости.

### Как handlers улучшают эффективность?

Handlers запускаются только если задача что-то изменила. Например, Docker перезагружается только если его конфигурация действительно изменилась.

### Почему Ansible Vault необходим?

Credentials и sensitive data нельзя хранить в plain text в Git. Vault шифрует эти данные, и они остаются защищенными в версионном контроле.

---

## 7. Challenges & Solutions

- **Проблема:** Docker требует Python module
  - **Решение:** Установить python3-docker в роли docker

- **Проблема:** Container уже может быть запущен
  - **Решение:** Использовать `ignore_errors: yes` при остановке старого контейнера

- **Проблема:** Нужно ждать пока приложение стартует
  - **Решение:** Использовать wait_for модуль для проверки порта

---

## 8. Testing Instructions

### Тестирование Idempotency

```bash
# Первый запуск
ansible-playbook playbooks/provision.yml

# Второй запуск (проверка idempotency)
ansible-playbook playbooks/provision.yml

# Все должны быть "ok" (зеленые)
```

### Тестирование Deployment

```bash
ansible-playbook playbooks/deploy.yml --ask-vault-pass

# Проверка контейнера
ansible webservers -a "docker ps"

# Проверка health
curl http://<VM-IP>:5000/health
```
