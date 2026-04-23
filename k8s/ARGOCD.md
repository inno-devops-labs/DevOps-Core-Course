# ArgoCD — Lab 13 (GitOps)

Документация по установке ArgoCD, манифестам Application и проверкам self-healing для чарта `k8s/app-python`. Пошаговые команды см. в [labs/lab13.md](../labs/lab13.md).

---

## 1. ArgoCD Setup

**Проверка после установки Helm**

- Namespace `argocd` создан, release (например `argocd`) установлен из репозитория `argo/argo-cd`.
- Все поды в состоянии Ready, в том числе с лейблом `app.kubernetes.io/name=argocd-server` (см. подсказки в лабе для `kubectl wait`).

**Доступ к UI**

- Port-forward к сервису `argocd-server` в `argocd` (HTTPS на локальный порт, например 8080).
- Логин: пользователь `admin`, пароль из секрета `argocd-initial-admin-secret`.

**CLI**

- Установлен бинарник `argocd`, выполнен `argocd login` к тому же хосту/порту (при самоподписанном сертификате — флаг insecure по документации лабы).
- Проверка: `argocd version`, `argocd app list`.

---

## 2. Application Configuration

Манифесты лежат в [k8s/argocd/](argocd/).

| Файл | Имя Application | Values | Namespace назначения | Sync |
|------|-------------------|--------|----------------------|------|
| [application.yaml](argocd/application.yaml) | `python-app` | `values.yaml` | `default` | Ручной (блока `automated` нет) |
| [application-dev.yaml](argocd/application-dev.yaml) | `python-app-dev` | `values-dev.yaml` | `dev` | Авто: `prune`, `selfHeal` |
| [application-prod.yaml](argocd/application-prod.yaml) | `python-app-prod` | `values-prod.yaml` | `prod` | Ручной |

**Источник (общий для всех)**

- `repoURL`: `https://github.com/4hellboy4/DevOps-Core-Course.git` (должен совпадать с `git remote get-url origin`).
- `targetRevision`: ветка на GitHub, где лежат чарт и `k8s/argocd` (в манифестах: `lab13` — ветка должна быть **запушена**: `git push -u origin lab13`).
- `path`: `k8s/app-python` — корень Helm-чарта в репозитории.
- `helm.valueFiles`: файлы **относительно** каталога чарта (`values.yaml`, `values-dev.yaml`, `values-prod.yaml`).

**Назначение**

- `destination.server`: `https://kubernetes.default.svc` — in-cluster API.
- `syncOptions: CreateNamespace=true` — ArgoCD создаст namespace назначения при первом sync, если его ещё нет (для `default` обычно уже существует).

Применение: `kubectl apply -f k8s/argocd/<manifest>.yaml`. Первый sync для приложений без auto-sync — через UI или `argocd app sync <name>`.

---

## 3. Multi-Environment

| | Dev (`python-app-dev`) | Prod (`python-app-prod`) |
|---|------------------------|---------------------------|
| Kubernetes namespace | `dev` | `prod` |
| Values | [values-dev.yaml](app-python/values-dev.yaml) | [values-prod.yaml](app-python/values-prod.yaml) |
| Реплики | `2` (PVC отключён, см. комментарий в values) | `1` (наследуется persistence из базового `values.yaml`) |
| Ресурсы | Меньшие requests/limits | Большие limits относительно dev |
| Сервис | NodePort `30080` | NodePort `30081` |
| ArgoCD sync | Автоматический с `prune` и `selfHeal` | Только ручной sync |

**Почему prod остаётся manual**

- Возможность ревью и согласования изменений перед выкладкой.
- Контроль момента релиза (окна обслуживания, координация с мониторингом).
- Требования compliance/аудита: изменения в кластере должны совпадать с явным действием после проверки в Git.

Пространства `dev` и `prod` можно создать заранее (`kubectl create namespace dev|prod`) или полагаться на `CreateNamespace=true`.

---

## 4. Self-Healing Evidence

Имена ресурсов Helm для чарта `app-python`: шаблон полного имени — `{Release.Name}-{Chart.Name}`. У ArgoCD имя release по умолчанию совпадает с **именем Application**.

| Application | Имя Deployment (пример) |
|-------------|-------------------------|
| `python-app` | `python-app-app-python` |
| `python-app-dev` | `python-app-dev-app-python` |
| `python-app-prod` | `python-app-prod-app-python` |

Селекторы подов для этого чарта (см. [templates/_helpers.tpl](app-python/templates/_helpers.tpl)):

- `app.kubernetes.io/name=app-python` (имя чарта, не `python-app`).
- `app.kubernetes.io/instance=<имя Application>` (например `python-app-dev`).

Заполните таблицы после выполнения лабы у себя в кластере.

### 4.1 Ручной scale (dev, ожидается self-heal ArgoCD)

| Шаг | Время (UTC) | Команда / наблюдение |
|-----|-------------|----------------------|
| До | _заполнить_ | `kubectl get deploy -n dev`, зафиксировать replicas из Git (например 2). |
| Изменение в кластере | _заполнить_ | `kubectl scale deployment python-app-dev-app-python -n dev --replicas=5` |
| Дрейф в ArgoCD | _заполнить_ | В UI статус OutOfSync / `argocd app get python-app-dev`. |
| После self-heal | _заполнить_ | Снова `kubectl get deploy -n dev` — replicas возвращаются к значению из Git. |

### 4.2 Удаление пода (поведение Kubernetes)

| Шаг | Время (UTC) | Наблюдение |
|-----|-------------|------------|
| Удаление | _заполнить_ | `kubectl delete pod -n dev -l app.kubernetes.io/instance=python-app-dev` |
| Сразу после | _заполнить_ | ReplicaSet/Deployment создаёт новый под с тем же desired replicas — это **контроллер Kubernetes**, а не синк ArgoCD. |

### 4.3 Дрейф конфигурации (метка и т.д.)

| Шаг | Время (UTC) | Команда / наблюдение |
|-----|-------------|----------------------|
| Патч | _заполнить_ | Например `kubectl label deployment python-app-dev-app-python -n dev argocd-test=1 --overwrite` |
| Дифф | _заполнить_ | `argocd app diff python-app-dev` — видно отличие от манифеста из Git. |
| После self-heal | _заполнить_ | Лишняя метка снята после автоприведения к состоянию Git. |

---

## 5. Когда синкает ArgoCD и когда «лечит» Kubernetes

**ArgoCD sync**

- Периодический опрос Git (по умолчанию около **3 минут**; точное значение зависит от конфигурации `timeout.reconciliation` / настроек контроллера).
- Немедленно при ручном **Sync** в UI или CLI.
- При настройке **webhook** репозиторий может уведомлять ArgoCD об изменениях без ожидания интервала.

**Kubernetes self-healing (без ArgoCD)**

- Deployment/ReplicaSet поддерживает заданное число реплик: при падении или удалении пода создаётся новый под с тем же шаблоном, пока не изменён сам Deployment.

**ArgoCD self-heal (при включённом `selfHeal`)**

- Конфигурация объекта в кластере приводится к тому, что вычислено из Git (включая поля, изменённые `kubectl patch/edit`), в рамках политики sync.

Итого: удаление пода демонстрирует восстановление **числом реплик** на стороне Kubernetes; принудительный scale или патч полей манифеста демонстрирует **возврат к Git** на стороне ArgoCD (для dev с auto-sync и selfHeal).

---

## 6. Screenshots (для отчёта)

Добавьте в отчёт или рядом с репозиторием (как требует курс):

1. Список приложений в ArgoCD UI: видны `python-app` (если используете), `python-app-dev`, `python-app-prod`.
2. Общий статус sync/health для dev и prod.
3. Экран деталей одного приложения (дерево ресурсов, события sync).
4. (Опционально) Экран diff при OutOfSync до self-heal.

Файлы скриншотов в этом репозитории не хранятся — вставьте их в документ сдачи по инструкции преподавателя.
