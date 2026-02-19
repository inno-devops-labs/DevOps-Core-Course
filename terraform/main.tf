terraform {
  required_providers {
    null = {
      source  = "hashicorp/null"
      version = "~> 3.0"
    }
  }
}

locals {
  vboxmanage = "C:\\Program Files\\Oracle\\VirtualBox\\VBoxManage.exe"
}

resource "null_resource" "ubuntu_vm" {
  triggers = {
    vm_name = var.vm_name
    vm_cpus = var.vm_cpus
    vm_mem  = var.vm_memory
  }

  provisioner "local-exec" {
    interpreter = ["PowerShell", "-Command"]
    command     = <<-EOT
      $ErrorActionPreference = 'Stop'
      $vbox    = '${local.vboxmanage}'
      $vmName  = '${var.vm_name}'
      $boxUrl  = '${var.vm_image_url}'
      $boxFile = "${path.module}\.terraform\ubuntu.box"
      $ovfDir  = "${path.module}\.terraform\ovf"

      # Skip if VM already running
      $existing = & $vbox list runningvms 2>$null | Select-String $vmName
      if ($existing) { Write-Host "VM already running."; exit 0 }

      # Download box if not cached
      New-Item -ItemType Directory -Force -Path (Split-Path $boxFile) | Out-Null
      if (!(Test-Path $boxFile)) {
        Write-Host "Downloading Ubuntu 22.04 box (~500 MB)..."
        Invoke-WebRequest -Uri $boxUrl -OutFile $boxFile -UseBasicParsing
      } else { Write-Host "Box already cached." }

      # Extract OVF
      New-Item -ItemType Directory -Force -Path $ovfDir | Out-Null
      if (!(Get-ChildItem $ovfDir -Filter '*.ovf' -Recurse)) {
        Write-Host "Extracting box..."
        tar -xf $boxFile -C $ovfDir
      }
      $ovf = (Get-ChildItem $ovfDir -Filter '*.ovf' -Recurse | Select-Object -First 1).FullName

      # Import VM
      Write-Host "Importing VM into VirtualBox..."
      & $vbox import $ovf `
        --vsys 0 --vmname $vmName `
        --memory ${var.vm_memory} --cpus ${var.vm_cpus}

      # NIC1: NAT (for internet + port-forwarded SSH)
      & $vbox modifyvm $vmName --nic1 nat
      # SSH port forward: localhost:2222 -> VM:22
      & $vbox modifyvm $vmName `
        --natpf1 "ssh,tcp,,2222,,22"
      # NIC2: Host-only (for direct access)
      & $vbox modifyvm $vmName --nic2 hostonly `
        --hostonlyadapter2 '${var.host_only_adapter}'

      # Start headless
      Write-Host "Starting VM..."
      & $vbox startvm $vmName --type headless
      Write-Host "Done. VM '$vmName' is running."
      Write-Host "SSH: ssh -p 2222 vagrant@127.0.0.1  (password: vagrant)"
    EOT
  }

  provisioner "local-exec" {
    when        = destroy
    interpreter = ["PowerShell", "-Command"]
    command     = <<-EOT
      $vbox   = 'C:\Program Files\Oracle\VirtualBox\VBoxManage.exe'
      $vmName = '${self.triggers.vm_name}'
      & $vbox controlvm $vmName poweroff 2>$null
      Start-Sleep 3
      & $vbox unregistervm $vmName --delete
      Write-Host "VM '$vmName' deleted."
    EOT
  }
}
