[CmdletBinding()]
param(
    [switch]$SkipExtract
)

$ErrorActionPreference = "Stop"

$repositoryRoot = [System.IO.Path]::GetFullPath(
    (Join-Path $PSScriptRoot "..\..\..")
)
$analyticsDirectory = Join-Path $repositoryRoot "dw\snowflake\analytics"
$pipelinePath = Join-Path $repositoryRoot "pipelines\ecommerce_bronze\ecommerce_bronze_pipeline.py"
$lockPath = Join-Path $PSScriptRoot "run_daily.lock"
$logDirectory = Join-Path $analyticsDirectory "logs"
$logPath = Join-Path $logDirectory (
    "run_daily_{0}_{1}.log" -f (Get-Date -Format "yyyyMMdd_HHmmss"), $PID
)

$lockAcquired = $false
$exitCode = 0

function Write-RunLog {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Message
    )

    $entry = "{0} {1}" -f (Get-Date -Format "yyyy-MM-ddTHH:mm:ssK"), $Message
    Write-Host $entry
    Add-Content -LiteralPath $logPath -Value $entry -Encoding UTF8
}

function Invoke-PipelineStep {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Name,

        [Parameter(Mandatory = $true)]
        [string]$Command,

        [string[]]$Arguments = @()
    )

    Write-RunLog "Starting $Name"
    & $Command @Arguments 2>&1 | ForEach-Object {
        Write-RunLog "$_"
    }
    $stepExitCode = $LASTEXITCODE

    if ($stepExitCode -ne 0) {
        Write-RunLog "$Name failed with exit code $stepExitCode"
        return $stepExitCode
    }

    Write-RunLog "$Name completed with exit code 0"
    return 0
}

New-Item -ItemType Directory -Path $logDirectory -Force | Out-Null

try {
    try {
        $lockStream = [System.IO.File]::Open(
            $lockPath,
            [System.IO.FileMode]::CreateNew,
            [System.IO.FileAccess]::Write,
            [System.IO.FileShare]::None
        )
        $lockWriter = New-Object System.IO.StreamWriter($lockStream)
        try {
            $lockWriter.WriteLine($PID)
        }
        finally {
            $lockWriter.Dispose()
        }
        $lockAcquired = $true
    }
    catch [System.IO.IOException] {
        $exitCode = 3
        Write-RunLog "Daily pipeline is already in progress; lock exists at $lockPath"
        throw
    }

    Write-RunLog "Daily pipeline started"

    if ($SkipExtract) {
        Write-RunLog "Bronze extraction skipped"
    }
    else {
        $exitCode = Invoke-PipelineStep `
            -Name "Bronze extraction" `
            -Command "python" `
            -Arguments @($pipelinePath)
        if ($exitCode -ne 0) {
            throw "Bronze extraction failed"
        }
    }

    $exitCode = Invoke-PipelineStep `
        -Name "dbt build" `
        -Command "dbt" `
        -Arguments @(
            "build",
            "--project-dir", $analyticsDirectory,
            "--profiles-dir", $analyticsDirectory
        )
    if ($exitCode -ne 0) {
        throw "dbt build failed"
    }

    Write-RunLog "Daily pipeline completed successfully"
}
catch {
    if ($exitCode -eq 0) {
        $exitCode = 1
        Write-RunLog "Daily pipeline failed: $($_.Exception.Message)"
    }
}
finally {
    if ($lockAcquired) {
        Remove-Item -LiteralPath $lockPath -Force
        Write-RunLog "Daily pipeline lock removed"
    }
}

exit $exitCode
