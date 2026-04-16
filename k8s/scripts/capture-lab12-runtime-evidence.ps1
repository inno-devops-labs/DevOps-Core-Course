param(
    [string]$ReleaseName = "dev",
    [string]$Namespace = "default",
    [string]$ValuesFile = "k8s/devops-info-chart/values-dev.yaml",
    [int]$RootHits = 5
)

$ErrorActionPreference = "Continue"

$chartPath = "k8s/devops-info-chart"
$deploymentName = "$ReleaseName-devops-info-chart"
$evidenceDir = "k8s/lab12-evidence"
$runtimeEvidence = Join-Path $evidenceDir "runtime-k8s.txt"
$hasErrors = $false
$skipReason = $null

New-Item -ItemType Directory -Force -Path $evidenceDir | Out-Null
Remove-Item -Force -ErrorAction SilentlyContinue $runtimeEvidence

function Write-Section {
    param([string]$Title)
    @"

============================================================
$Title
============================================================
"@ | Tee-Object -FilePath $runtimeEvidence -Append | Out-Null
}

function Append-CommandOutput {
    param([string]$CommandText, [scriptblock]$Action)

    $script:lastStepSucceeded = $false
    "PS> $CommandText" | Tee-Object -FilePath $runtimeEvidence -Append | Out-Null

    try {
        $output = & $Action 2>&1
        if ($null -ne $output) {
            $output | Tee-Object -FilePath $runtimeEvidence -Append | Out-Null
        }

        if ($LASTEXITCODE -ne 0) {
            "ExitCode: $LASTEXITCODE" | Tee-Object -FilePath $runtimeEvidence -Append | Out-Null
            $script:hasErrors = $true
        } else {
            $script:lastStepSucceeded = $true
        }
    } catch {
        $_.Exception.Message | Tee-Object -FilePath $runtimeEvidence -Append | Out-Null
        $script:hasErrors = $true
    }

    "" | Tee-Object -FilePath $runtimeEvidence -Append | Out-Null
    return $script:lastStepSucceeded
}

function Write-Note {
    param([string]$Text)
    "NOTE: $Text" | Tee-Object -FilePath $runtimeEvidence -Append | Out-Null
    "" | Tee-Object -FilePath $runtimeEvidence -Append | Out-Null
}

Write-Section "Cluster state before verification"
$null = Append-CommandOutput -CommandText "kubectl config current-context" -Action { kubectl config current-context }
$clusterReachable = Append-CommandOutput -CommandText "kubectl get nodes" -Action { kubectl get nodes }

if (-not $clusterReachable) {
    $skipReason = "Kubernetes cluster is unreachable from current host session."
    Write-Note $skipReason
}

if ($clusterReachable) {
    Write-Section "Deploy Helm chart"
    $null = Append-CommandOutput -CommandText "helm upgrade --install $ReleaseName $chartPath -f $ValuesFile -n $Namespace --create-namespace" -Action {
        helm upgrade --install $ReleaseName $chartPath -f $ValuesFile -n $Namespace --create-namespace
    }
    $null = Append-CommandOutput -CommandText "kubectl rollout status deployment/$deploymentName -n $Namespace --timeout=180s" -Action {
        kubectl rollout status deployment/$deploymentName -n $Namespace --timeout=180s
    }

    $pod = (kubectl get pods -n $Namespace -l "app.kubernetes.io/instance=$ReleaseName,app.kubernetes.io/name=devops-info-chart" -o jsonpath="{.items[0].metadata.name}" 2>$null)
    $serviceUrl = (minikube service $deploymentName -n $Namespace --url 2>$null)
    $serviceUrl = ($serviceUrl | Select-Object -First 1)

    Write-Section "Required outputs for lab12"
    $null = Append-CommandOutput -CommandText "kubectl get configmap,pvc -n $Namespace" -Action { kubectl get configmap,pvc -n $Namespace }

    if ([string]::IsNullOrWhiteSpace($pod)) {
        Write-Note "Pod name could not be resolved. Skipping exec-based checks."
        $hasErrors = $true
    } else {
        $null = Append-CommandOutput -CommandText "kubectl exec -n $Namespace $pod -- cat /config/config.json" -Action {
            kubectl exec -n $Namespace $pod -- cat /config/config.json
        }
        $null = Append-CommandOutput -CommandText "kubectl exec -n $Namespace $pod -- printenv | Select-String APP_ENV|LOG_LEVEL|VISITS_FILE" -Action {
            kubectl exec -n $Namespace $pod -- printenv | Select-String -Pattern "^(APP_ENV|LOG_LEVEL|VISITS_FILE)="
        }
    }

    Write-Section "Persistence verification"
    if ([string]::IsNullOrWhiteSpace($serviceUrl)) {
        Write-Note "Service URL could not be resolved. Skipping HTTP hit loop."
        $hasErrors = $true
    } else {
        for ($i = 1; $i -le $RootHits; $i++) {
            try {
                Invoke-RestMethod -Uri $serviceUrl -Method Get | Out-Null
            } catch {
                "HTTP request failed on iteration $($i): $($_.Exception.Message)" | Tee-Object -FilePath $runtimeEvidence -Append | Out-Null
                $hasErrors = $true
            }
        }
        "" | Tee-Object -FilePath $runtimeEvidence -Append | Out-Null
    }

    if (-not [string]::IsNullOrWhiteSpace($pod)) {
        $null = Append-CommandOutput -CommandText "kubectl exec -n $Namespace $pod -- cat /data/visits  # before pod deletion" -Action {
            kubectl exec -n $Namespace $pod -- cat /data/visits
        }
        $null = Append-CommandOutput -CommandText "kubectl delete pod $pod -n $Namespace" -Action { kubectl delete pod $pod -n $Namespace }
        $null = Append-CommandOutput -CommandText "kubectl rollout status deployment/$deploymentName -n $Namespace --timeout=180s" -Action {
            kubectl rollout status deployment/$deploymentName -n $Namespace --timeout=180s
        }
        $newPod = (kubectl get pods -n $Namespace -l "app.kubernetes.io/instance=$ReleaseName,app.kubernetes.io/name=devops-info-chart" -o jsonpath="{.items[0].metadata.name}" 2>$null)
        if ([string]::IsNullOrWhiteSpace($newPod)) {
            Write-Note "New pod name could not be resolved after deletion."
            $hasErrors = $true
        } else {
            $null = Append-CommandOutput -CommandText "kubectl exec -n $Namespace $newPod -- cat /data/visits  # after pod recreation" -Action {
                kubectl exec -n $Namespace $newPod -- cat /data/visits
            }
        }
    }
}

Write-Section "Done"
if ($hasErrors) {
    "Status: COMPLETED WITH ERRORS" | Tee-Object -FilePath $runtimeEvidence -Append | Out-Null
} else {
    "Status: SUCCESS" | Tee-Object -FilePath $runtimeEvidence -Append | Out-Null
}
"Runtime evidence saved to: $runtimeEvidence" | Tee-Object -FilePath $runtimeEvidence -Append | Out-Null
Write-Output "Lab12 runtime evidence saved to $runtimeEvidence"
