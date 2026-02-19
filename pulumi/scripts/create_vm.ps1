# Read config from environment variables (avoids quoting issues)
$VBoxManage      = $env:VBOX_MANAGE
$VmName          = $env:VM_NAME
$BoxUrl          = $env:BOX_URL
$VmMemory        = $env:VM_MEMORY
$VmCpus          = $env:VM_CPUS
$HostOnlyAdapter = $env:HOST_ONLY
$CacheDir        = $env:CACHE_DIR

$ErrorActionPreference = 'Stop'
$boxFile = Join-Path $CacheDir "ubuntu.box"
$ovfDir  = Join-Path $CacheDir "ovf"

# Skip if VM already running
$existing = & $VBoxManage list runningvms 2>$null | Select-String $VmName
if ($existing) { Write-Host "VM already running."; exit 0 }

# Download box if not cached
New-Item -ItemType Directory -Force -Path $CacheDir | Out-Null
if (!(Test-Path $boxFile)) {
    Write-Host "Downloading Ubuntu 22.04 box (~500 MB)..."
    Invoke-WebRequest -Uri $BoxUrl -OutFile $boxFile -UseBasicParsing
} else {
    Write-Host "Box already cached."
}

# Extract OVF
New-Item -ItemType Directory -Force -Path $ovfDir | Out-Null
if (!(Get-ChildItem $ovfDir -Filter '*.ovf' -Recurse -ErrorAction SilentlyContinue)) {
    Write-Host "Extracting box..."
    tar -xf $boxFile -C $ovfDir
}
$ovf = (Get-ChildItem $ovfDir -Filter '*.ovf' -Recurse | Select-Object -First 1).FullName

# Import VM
Write-Host "Importing VM into VirtualBox..."
& $VBoxManage import $ovf `
    --vsys 0 --vmname $VmName `
    --memory $VmMemory --cpus $VmCpus

# NIC1: NAT + SSH port forward localhost:2223 -> VM:22
& $VBoxManage modifyvm $VmName --nic1 nat
& $VBoxManage modifyvm $VmName --natpf1 "ssh,tcp,,2223,,22"

# NIC2: Host-only
& $VBoxManage modifyvm $VmName --nic2 hostonly `
    --hostonlyadapter2 $HostOnlyAdapter

# Start headless
Write-Host "Starting VM..."
& $VBoxManage startvm $VmName --type headless
Write-Host "Done. VM '$VmName' is running."
Write-Host "SSH: ssh -p 2223 vagrant@127.0.0.1  (password: vagrant)"
