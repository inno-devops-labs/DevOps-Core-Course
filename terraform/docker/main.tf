terraform {
  required_providers {
    docker = {
      source  = "kreuzwerker/docker"
      version = "~> 3.0.1"
    }
  }
}

provider "docker" {}

resource "docker_container" "moscow_time" {
  image = var.docker_image
  name  = var.container_name
  ports {
    internal = var.internal_port
    external = var.external_port
  }
}
