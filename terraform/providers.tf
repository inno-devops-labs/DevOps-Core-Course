terraform {
  required_version = ">= 1.3.0"
  required_providers {
    yandex = {
      source  = "yandex-cloud/yandex"
      version = ">= 0.87.0"
    }
  }
}

provider "yandex" {
  # Using environment variables (YC_TOKEN, YC_CLOUD_ID, YC_FOLDER_ID)
  zone = var.zone
}
