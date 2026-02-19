# Read config from environment variables
$VBoxManage = $env:VBOX_MANAGE
$VmName     = $env:VM_NAME

& $VBoxManage controlvm $VmName poweroff 2>$null
Start-Sleep 3
& $VBoxManage unregistervm $VmName --delete
Write-Host "VM '$VmName' deleted."
