output "container_name" {
  value = docker_container.moscow_time.name
}

output "container_id" {
  value = docker_container.moscow_time.id
}

output "container_image" {
  value = docker_container.moscow_time.image
}

output "container_port" {
  value = docker_container.moscow_time.ports
}
