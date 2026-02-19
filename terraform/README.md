# Terraform (lab04)

Каталог содержит конфигурацию Terraform для развёртывания одной виртуальной машины в Yandex Cloud:

- сеть и подсеть;
- security group с портами 22, 80 и 5000;
- VM Ubuntu с публичным IP и SSH‑доступом по ключу.

Основные файлы:

- `providers.tf` — провайдер Yandex;
- `variables.tf` — входные параметры;
- `main.tf` — ресурсы;
- `outputs.tf` — выходные значения;
- `terraform.tfvars` — реальные значения переменных (не добавлять в git).
