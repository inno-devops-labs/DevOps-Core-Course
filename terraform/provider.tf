provider "yandex" {
  cloud_id  = var.cloud_id
  folder_id = var.folder_id
  zone      = var.zone

  service_account_key_file = var.sa_key_file
}
