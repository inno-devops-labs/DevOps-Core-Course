variable "python_container_name" {
  description = "Name of the container"
  type        = string
  default     = "moscow-time-app-renamed"
}

variable "app_image_name" {
  description = "Docker image name"
  type        = string
  default     = "karamkhaddourpro/my-fastapi-app:latest"
}

variable "internal_port" {
  description = "Internal port used by the app"
  type        = number
  default     = 8000
}

variable "external_port" {
  description = "External port exposed on the host"
  type        = number
  default     = 9080
}
