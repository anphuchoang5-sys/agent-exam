param(
    [Parameter(Mandatory = $true)][string]$Python,
    [Parameter(Mandatory = $true)][string]$Backend,
    [Parameter(Mandatory = $true)][string]$Evidence,
    [Parameter(Mandatory = $true)][string]$PostgresImage,
    [Parameter(Mandatory = $true)][string]$MinioImage,
    [string]$Scope = "t05-s11-storage-20260923-01"
)

$ErrorActionPreference = "Stop"
$task = "05"
$prefix = "agentexam-t05-s11-storage"
$network = "$prefix-network"
$volume = "$prefix-postgres"
$postgres = "$prefix-postgres"
$minio = "$prefix-minio"
$evidencePath = [IO.Path]::GetFullPath($Evidence)
if (Test-Path -LiteralPath $evidencePath) {
    throw "S11_EVIDENCE_ALREADY_EXISTS:$evidencePath"
}
New-Item -ItemType Directory -Path $evidencePath | Out-Null
$commands = Join-Path $evidencePath "docker-commands.jsonl"

function Invoke-Docker([string[]]$DockerArgs) {
    $previousPreference = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    $output = & docker @DockerArgs 2>&1
    $code = $LASTEXITCODE
    $ErrorActionPreference = $previousPreference
    [pscustomobject]@{ argv = @("docker") + $DockerArgs; returncode = $code } |
        ConvertTo-Json -Compress | Add-Content -LiteralPath $commands
    if ($code -ne 0) {
        throw "S11_DOCKER_COMMAND_FAILED:$($DockerArgs -join ' '):$code`n$($output -join "`n")"
    }
    return ($output -join "`n")
}

function Assert-Free([string]$Kind, [string]$Name) {
    if (Test-DockerResource $Kind $Name) {
        throw "S11_RESOURCE_ALREADY_EXISTS:${Kind}:$Name"
    }
}

function Test-DockerResource([string]$Kind, [string]$Name) {
    $previousPreference = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    & docker $Kind inspect $Name *> $null
    $exists = $LASTEXITCODE -eq 0
    $ErrorActionPreference = $previousPreference
    return $exists
}

function Assert-Owned([string]$Kind, [string]$Name) {
    $value = (Invoke-Docker -DockerArgs @($Kind, "inspect", $Name) | ConvertFrom-Json)
    $labels = if ($Kind -eq "container") { $value[0].Config.Labels } else { $value[0].Labels }
    if ($labels."agentexam.task" -ne $task -or $labels."agentexam.scope" -ne $Scope) {
        throw "S11_RESOURCE_OWNERSHIP_MISMATCH:${Kind}:$Name"
    }
}

function Inventory([string]$Suffix) {
    Invoke-Docker -DockerArgs @("image", "ls", "--digests", "--no-trunc", "--format", "{{json .}}") |
        Set-Content -LiteralPath (Join-Path $evidencePath "images-$Suffix.jsonl")
    Invoke-Docker -DockerArgs @("volume", "ls", "--format", "{{json .}}") |
        Set-Content -LiteralPath (Join-Path $evidencePath "volumes-$Suffix.jsonl")
}

function Remove-Owned([string]$Kind, [string]$Name) {
    if (-not (Test-DockerResource $Kind $Name)) { return }
    Assert-Owned $Kind $Name
    if ($Kind -eq "container") { Invoke-Docker -DockerArgs @("rm", "--force", $Name) | Out-Null }
    elseif ($Kind -eq "network") { Invoke-Docker -DockerArgs @("network", "rm", $Name) | Out-Null }
    else { Invoke-Docker -DockerArgs @("volume", "rm", $Name) | Out-Null }
}

$exitCode = 1
Inventory "before"
try {
    Assert-Free "container" $postgres
    Assert-Free "container" $minio
    Assert-Free "network" $network
    Assert-Free "volume" $volume
    Invoke-Docker -DockerArgs @(
        "network", "create", "--driver", "bridge", "--opt",
        "com.docker.network.bridge.enable_ip_masquerade=false",
        "--label", "agentexam.task=$task", "--label", "agentexam.scope=$Scope", $network
    ) | Out-Null
    Invoke-Docker -DockerArgs @("volume", "create", "--label", "agentexam.task=$task", "--label", "agentexam.scope=$Scope", $volume) | Out-Null

    $env:POSTGRES_USER = "agentexam_identity_test"
    $env:POSTGRES_PASSWORD = "synthetic-postgres-password"
    $env:POSTGRES_DB = "agentexam_identity_test"
    Invoke-Docker -DockerArgs @(
        "run", "--detach", "--pull", "never", "--name", $postgres,
        "--label", "agentexam.task=$task", "--label", "agentexam.scope=$Scope",
        "--network", $network, "--publish", "127.0.0.1:0:5432",
        "--env", "POSTGRES_USER", "--env", "POSTGRES_PASSWORD", "--env", "POSTGRES_DB",
        "--volume", "${volume}:/var/lib/postgresql/data", $PostgresImage
    ) | Out-Null

    $env:MINIO_ROOT_USER = "ae_test_s11_access"
    $env:MINIO_ROOT_PASSWORD = "synthetic-minio-secret-s11"
    Invoke-Docker -DockerArgs @(
        "run", "--detach", "--pull", "never", "--name", $minio,
        "--label", "agentexam.task=$task", "--label", "agentexam.scope=$Scope",
        "--network", $network, "--publish", "127.0.0.1:0:9000",
        "--env", "MINIO_ROOT_USER", "--env", "MINIO_ROOT_PASSWORD",
        "--tmpfs", "/data:rw,noexec,nosuid,size=64m", $MinioImage,
        "server", "/data", "--address", ":9000"
    ) | Out-Null

    $pgBinding = Invoke-Docker -DockerArgs @("port", $postgres, "5432/tcp")
    $minioBinding = Invoke-Docker -DockerArgs @("port", $minio, "9000/tcp")
    $pgPort = [regex]::Match($pgBinding, "127\.0\.0\.1:(\d+)").Groups[1].Value
    $minioPort = [regex]::Match($minioBinding, "127\.0\.0\.1:(\d+)").Groups[1].Value
    if (-not $pgPort -or -not $minioPort -or $pgPort -eq "55432") {
        throw "S11_STORAGE_PORT_INVALID:postgres=$pgPort,minio=$minioPort"
    }

    $ready = $false
    for ($attempt = 0; $attempt -lt 60; $attempt++) {
        $previousPreference = $ErrorActionPreference
        $ErrorActionPreference = "Continue"
        & docker exec $postgres pg_isready -U agentexam_identity_test -d agentexam_identity_test *> $null
        $code = $LASTEXITCODE
        $ErrorActionPreference = $previousPreference
        if ($code -eq 0) { $ready = $true; break }
        Start-Sleep -Milliseconds 250
    }
    if (-not $ready) { throw "S11_POSTGRES_NOT_READY" }
    $ready = $false
    for ($attempt = 0; $attempt -lt 60; $attempt++) {
        try {
            $response = Invoke-WebRequest -UseBasicParsing "http://127.0.0.1:$minioPort/minio/health/live" -TimeoutSec 2
            if ($response.StatusCode -eq 200) { $ready = $true; break }
        } catch { Start-Sleep -Milliseconds 250 }
    }
    if (-not $ready) { throw "S11_MINIO_NOT_READY" }

    $env:AGENTEXAM_RUN_IDENTITY_POSTGRES = "1"
    $env:AGENTEXAM_RUN_JOB_MINIO = "1"
    $env:AGENTEXAM_TEST_DATABASE_URL = "postgresql://agentexam_identity_test:synthetic-postgres-password@127.0.0.1:$pgPort/agentexam_identity_test"
    $env:AGENTEXAM_MINIO_ENDPOINT = "http://127.0.0.1:$minioPort"
    $env:AGENTEXAM_MINIO_BUCKET = "agentexam-synthetic-test"
    $env:AGENTEXAM_MINIO_ACCESS_KEY = $env:MINIO_ROOT_USER
    $env:AGENTEXAM_MINIO_SECRET_KEY = $env:MINIO_ROOT_PASSWORD
    [pscustomobject]@{ postgres_port = [int]$pgPort; minio_port = [int]$minioPort; forbidden_port_used = ($pgPort -eq "55432") } |
        ConvertTo-Json | Set-Content -LiteralPath (Join-Path $evidencePath "bindings.json")
    Invoke-Docker -DockerArgs @("inspect", $postgres, $minio) | Set-Content -LiteralPath (Join-Path $evidencePath "containers.json")
    Invoke-Docker -DockerArgs @("network", "inspect", $network) | Set-Content -LiteralPath (Join-Path $evidencePath "network.json")

    Push-Location $Backend
    try {
        $previousPreference = $ErrorActionPreference
        $ErrorActionPreference = "Continue"
        & $Python -m pytest tests/jobs/artifacts/test_postgres_minio.py::test_real_postgres_and_minio_cleanup_preserves_results_and_audit -q --no-cov -p no:cacheprovider 2>&1 |
            Tee-Object -FilePath (Join-Path $evidencePath "pytest.txt")
        $code = $LASTEXITCODE
        $ErrorActionPreference = $previousPreference
        if ($code -ne 0) { throw "S11_STORAGE_TEST_FAILED:$code" }
    } finally { Pop-Location }
    $exitCode = 0
} finally {
    foreach ($name in @("AGENTEXAM_RUN_IDENTITY_POSTGRES", "AGENTEXAM_RUN_JOB_MINIO", "AGENTEXAM_TEST_DATABASE_URL", "AGENTEXAM_MINIO_ENDPOINT", "AGENTEXAM_MINIO_BUCKET", "AGENTEXAM_MINIO_ACCESS_KEY", "AGENTEXAM_MINIO_SECRET_KEY", "POSTGRES_USER", "POSTGRES_PASSWORD", "POSTGRES_DB", "MINIO_ROOT_USER", "MINIO_ROOT_PASSWORD")) {
        Remove-Item "Env:$name" -ErrorAction SilentlyContinue
    }
    Remove-Owned "container" $minio
    Remove-Owned "container" $postgres
    Remove-Owned "volume" $volume
    Remove-Owned "network" $network
    Inventory "after"
    $residual = [ordered]@{}
    foreach ($kind in @("container", "network", "volume")) {
        $queryArgs = @($kind, "ls", "--quiet", "--filter", "label=agentexam.task=$task", "--filter", "label=agentexam.scope=$Scope")
        if ($kind -eq "container") { $queryArgs = @("container", "ls", "--all", "--quiet", "--filter", "label=agentexam.task=$task", "--filter", "label=agentexam.scope=$Scope") }
        $residual[$kind + "s"] = @((Invoke-Docker -DockerArgs $queryArgs).Split([Environment]::NewLine, [StringSplitOptions]::RemoveEmptyEntries))
    }
    $residual | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $evidencePath "residual.json")
}
if ($exitCode -ne 0) { exit $exitCode }
Write-Output "status=verified"
