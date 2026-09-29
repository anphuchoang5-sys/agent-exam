param(
    [Parameter(Mandatory = $true)][string]$Python,
    [Parameter(Mandatory = $true)][string]$ProjectRoot,
    [Parameter(Mandatory = $true)][string]$Parquet,
    [Parameter(Mandatory = $true)][string]$CodexArchive,
    [Parameter(Mandatory = $true)][string]$ProviderImage,
    [Parameter(Mandatory = $true)][string]$PostgresImage,
    [Parameter(Mandatory = $true)][string]$MinioImage,
    [Parameter(Mandatory = $true)][string]$EvidenceRoot,
    [switch]$FinalizeOnly
)

$ErrorActionPreference = "Stop"
$root = [IO.Path]::GetFullPath($ProjectRoot)
$backend = Join-Path $root "apps/backend"
$evidence = [IO.Path]::GetFullPath($EvidenceRoot)

function Get-LongPathSha256([string]$Path) {
    $prefix = '\\?\'
    $extended = if ($Path.StartsWith($prefix)) { $Path } else { $prefix + $Path }
    $stream = [IO.File]::OpenRead($extended)
    try {
        $sha = [Security.Cryptography.SHA256]::Create()
        try { $digest = $sha.ComputeHash($stream) }
        finally { $sha.Dispose() }
    } finally { $stream.Dispose() }
    return [BitConverter]::ToString($digest).Replace("-", "").ToLowerInvariant()
}

function Write-EvidenceManifest {
    $reparse = Get-ChildItem -LiteralPath $evidence -Recurse -Force |
        Where-Object { $_.Attributes -band [IO.FileAttributes]::ReparsePoint } |
        Sort-Object FullName |
        ForEach-Object {
            $relative = $_.FullName.Substring($evidence.Length + 1).Replace("\", "/")
            "$relative -> $($_.Target -join ',')"
        }
    $reparse | Set-Content -LiteralPath (Join-Path $evidence "REPARSE_POINTS.txt")
    $lines = Get-ChildItem -LiteralPath $evidence -Recurse -File -Force |
        Where-Object {
            $_.Name -ne "SHA256SUMS.txt" -and
            -not ($_.Attributes -band [IO.FileAttributes]::ReparsePoint)
        } |
        Sort-Object FullName |
        ForEach-Object {
            $hash = Get-LongPathSha256 $_.FullName
            $relative = $_.FullName.Substring($evidence.Length + 1).Replace("\", "/")
            "$hash  $relative"
        }
    $lines | Set-Content -LiteralPath (Join-Path $evidence "SHA256SUMS.txt")
}

if ($FinalizeOnly) {
    if (-not (Test-Path -LiteralPath $evidence)) {
        throw "S11_EVIDENCE_MISSING:$evidence"
    }
    Write-EvidenceManifest
    Write-Output "evidence=$evidence"
    Write-Output "status=verified"
    exit 0
}
if (Test-Path -LiteralPath $evidence) { throw "S11_EVIDENCE_ALREADY_EXISTS:$evidence" }
New-Item -ItemType Directory -Path $evidence | Out-Null
$env:PYTHONPATH = "src;tests"

function Invoke-Python([string]$Name, [string[]]$Arguments) {
    (ConvertTo-Json (@($Python) + $Arguments) -Compress) | Add-Content -LiteralPath (Join-Path $evidence "commands.jsonl")
    $previousPreference = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    & $Python @Arguments 2>&1 | Tee-Object -FilePath (Join-Path $evidence "$Name.txt")
    $code = $LASTEXITCODE
    $ErrorActionPreference = $previousPreference
    if ($code -ne 0) { throw "S11_COMMAND_FAILED:${Name}:$code" }
}

Push-Location $backend
try {
    Invoke-Python "targeted-tests" @(
        "-m", "pytest", "-q", "--no-cov", "-p", "no:cacheprovider",
        "tests/providers/policy/test_provider_config_rendering.py",
        "tests/providers/lifecycle/test_egress_and_surface.py",
        "tests/providers/runtime/s11/test_verdicts.py",
        "tests/unit/harbor",
        "tests/providers/runtime/uploads/test_provider_uploads.py",
        "tests/jobs/runtime/test_worker_bindings.py",
        "tests/jobs/runtime/test_worker_runtime.py"
    )
    Invoke-Python "live-trials" @(
        "-m", "providers.runtime.s11.verify",
        "--project-root", $root,
        "--parquet", ([IO.Path]::GetFullPath($Parquet)),
        "--codex-archive", ([IO.Path]::GetFullPath($CodexArchive)),
        "--provider-image", $ProviderImage,
        "--evidence", (Join-Path $evidence "live")
    )

    $env:AGENTEXAM_RUN_FORK_INTEGRATION = "1"
    try {
        Invoke-Python "fixed-fork" @(
            "-m", "pytest", "tests/integration/test_swe_bench_integration.py",
            "-q", "--no-cov", "-p", "no:cacheprovider", "-k", "wrong",
            "--basetemp", (Join-Path $evidence "fixed-fork")
        )
    } finally { Remove-Item Env:AGENTEXAM_RUN_FORK_INTEGRATION -ErrorAction SilentlyContinue }

    & (Join-Path $backend "tests/providers/runtime/s11/storage.ps1") `
        -Python $Python -Backend $backend -Evidence (Join-Path $evidence "storage") `
        -PostgresImage $PostgresImage -MinioImage $MinioImage
    if ($LASTEXITCODE -ne 0) { throw "S11_STORAGE_SCRIPT_FAILED:$LASTEXITCODE" }
} finally {
    Pop-Location
    Remove-Item Env:PYTHONPATH -ErrorAction SilentlyContinue
}

Write-EvidenceManifest
Write-Output "evidence=$evidence"
Write-Output "status=verified"
