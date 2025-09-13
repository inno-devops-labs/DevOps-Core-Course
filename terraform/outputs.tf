output "container_id" {
  description = "ID of the Docker container"
  value       = docker_container.app_python.id
}

output "image_id" {
  description = "ID of the Docker image"
  value       = docker_image.moscow_time.image_id
}
