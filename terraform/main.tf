terraform {
  required_providers {
    null = {
      source  = "hashicorp/null"
      version = "~> 3.0"
    }
  }
}

resource "null_resource" "vps_setup" {
  connection {
    type        = "ssh"
    host        = var.ssh_host
    user        = var.ssh_user
    private_key = file(pathexpand(var.ssh_private_key_path))
    agent       = false
  }

  provisioner "remote-exec" {
    inline = [
      "apt-get update -y",
      "apt-get install -y nginx",
      "systemctl enable nginx",
      "systemctl start nginx",
      "echo 'Lab04 VPS configured by Terraform' > /var/www/html/index.html"
    ]
  }
}
