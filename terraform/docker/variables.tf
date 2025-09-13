variable "container_name" {
  description = "Docker container Name"
  type        = string
  default     = "app_python"
}

variable "docker_image" {
  description = "Docker Image"
  type        = string
  default     = "adeepresession/app_python:v1.0"
}

variable "internal_port" {
  description = "Internal Port"
  type        = number
  default     = 8080
}

variable "external_port" {
  description = "External Port"
  type        = number
  default     = 8080
}
