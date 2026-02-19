# data.tf
data "yandex_compute_image" "ubuntu" {
  family = "ubuntu-2204-lts"
}
