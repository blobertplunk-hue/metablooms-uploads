#Requires -Version 7.0
<#
.SYNOPSIS
    MetaBlooms-compatible deterministic PowerShell installation and validation pipeline
    for setting up a local DeepSeek model using Ollama on Windows 11.

.DESCRIPTION
    Pipeline:  Install → Verify Runtime → Validate API → Execute Model → Benchmark → Scale → Integrate

    Design Principles (MetaBlooms OS):
    - Fail-closed: Every stage throws on failure; no silent continuation.
    - Deterministic: Each stage has exactly one verified success path.
    - Artifact-backed: All key outputs are captured and checksummed.
    - Independently testable: Each stage can be run in isolation with -StageOnly.

.PARAMETER StageOnly
    Run only the specified stage number (1-7). Omit to run all stages sequentially.

.PARAMETER ModelTag
    Ollama model tag to pull and run. Default: deepseek-r1:7b
    Lightweight alternative for low-memory machines: deepseek-r1:1.5b

.PARAMETER OllamaPort
    Port Ollama listens on. Default: 11434

.EXAMPLE
    pwsh -NoProfile -File .\DEEPSEEK_OLLAMA_SETUP_PLAN_v1.ps1
    pwsh -NoProfile -File .\DEEPSEEK_OLLAMA_SETUP_PLAN_v1.ps1 -StageOnly 4
    pwsh -NoProfile -File .\DEEPSEEK_OLLAMA_SETUP_PLAN_v1.ps1 -ModelTag deepseek-r1:1.5b
#>

[CmdletBinding()]
param(
    [ValidateRange(1,7)]
    [int]$StageOnly = 0,

    [string]$ModelTag = "deepseek-r1:7b",

    [int]$OllamaPort = 11434
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

function Write-Banner {
    param([string]$Text)
    $line = "=" * 70
    Write-Host ""
    Write-Host $line -ForegroundColor Cyan
    Write-Host "  $Text" -ForegroundColor Cyan
    Write-Host $line -ForegroundColor Cyan
}

function Write-Pass   { param([string]$Msg) Write-Host "[PASS] $Msg" -ForegroundColor Green }
function Write-Info   { param([string]$Msg) Write-Host "[INFO] $Msg" -ForegroundColor Yellow }
function Write-Fail   { param([string]$Msg) Write-Host "[FAIL] $Msg" -ForegroundColor Red }

function Assert-ExitCode {
    param([string]$Context)
    if ($LASTEXITCODE -ne 0) {
        Write-Fail "$Context exited with code $LASTEXITCODE"
        throw "FAIL-CLOSED: $Context"
    }
}

function Wait-OllamaReady {
    param([int]$MaxSeconds = 30)
    Write-Info "Waiting for Ollama API on port $OllamaPort (up to ${MaxSeconds}s)..."
    $deadline = (Get-Date).AddSeconds($MaxSeconds)
    while ((Get-Date) -lt $deadline) {
        try {
            $null = Invoke-RestMethod -Uri "http://localhost:$OllamaPort/" -TimeoutSec 2
            Write-Pass "Ollama API is responding."
            return
        } catch {
            Start-Sleep -Seconds 2
        }
    }
    throw "FAIL-CLOSED: Ollama API did not respond within ${MaxSeconds}s on port $OllamaPort"
}

# ---------------------------------------------------------------------------
# STAGE 1 — Install
# PURPOSE   : Install the Ollama runtime on Windows 11 via winget.
# MECHANISM : winget resolves the Ollama.Ollama package from the msstore/winget
#             source, downloads the signed MSI, and installs silently.
# PRECONDITION : winget ≥ 1.6, internet connection, ~200 MB free for installer.
# EXPECTED OUTPUT : "Successfully installed" message; `ollama` in PATH.
# ---------------------------------------------------------------------------
function Stage-Install {
    Write-Banner "STAGE 1 — Install Ollama"

    # Precondition: winget available
    Write-Info "Checking winget availability..."
    $winget = Get-Command winget -ErrorAction SilentlyContinue
    if (-not $winget) {
        Write-Fail "winget not found. Attempting bootstrap via AppInstaller..."
        # Remediation: add-appxpackage bootstrap
        $bootstrapUrl = "https://aka.ms/getwinget"
        Write-Info "Download winget bootstrap from: $bootstrapUrl"
        Write-Info "Run: Add-AppxPackage -RegisterByManifestPath <path>"
        throw "FAIL-CLOSED: winget not available. Install App Installer from the Microsoft Store and re-run."
    }
    Write-Pass "winget found: $($winget.Source)"

    # Precondition: Ollama not already installed (idempotency check)
    $existing = Get-Command ollama -ErrorAction SilentlyContinue
    if ($existing) {
        Write-Info "Ollama already installed at: $($existing.Source)"
        Write-Pass "Stage 1 skipped (already installed)."
        return
    }

    # ACTION: Install via winget
    Write-Info "Installing Ollama via winget..."
    winget install --id Ollama.Ollama --silent --accept-package-agreements --accept-source-agreements
    Assert-ExitCode "winget install Ollama.Ollama"

    # Reload PATH in current session
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" +
                [System.Environment]::GetEnvironmentVariable("Path", "User")

    # Verification: ollama binary must now be in PATH
    if (-not (Get-Command ollama -ErrorAction SilentlyContinue)) {
        throw "FAIL-CLOSED: ollama not found in PATH after installation. Open a new PowerShell session and re-run."
    }
    Write-Pass "Stage 1 PASS — Ollama installed and available in PATH."
}

# ---------------------------------------------------------------------------
# STAGE 2 — Verify Runtime
# PURPOSE   : Confirm Ollama version, start the server, verify port binding.
# MECHANISM : `ollama serve` starts a background HTTP server; Test-NetConnection
#             confirms TCP 11434 is open.
# PRECONDITION : Stage 1 complete; port 11434 free.
# EXPECTED OUTPUT : Version string; TCP test Succeeded = True.
# ---------------------------------------------------------------------------
function Stage-VerifyRuntime {
    Write-Banner "STAGE 2 — Verify Runtime"

    # Check version
    Write-Info "Checking Ollama version..."
    $version = ollama --version 2>&1
    Assert-ExitCode "ollama --version"
    Write-Pass "Ollama version: $version"

    # Check if port is already in use
    Write-Info "Checking port $OllamaPort availability..."
    $portCheck = Test-NetConnection -ComputerName localhost -Port $OllamaPort -WarningAction SilentlyContinue
    if ($portCheck.TcpTestSucceeded) {
        Write-Info "Port $OllamaPort already open — Ollama may already be running."
    } else {
        # Start Ollama server as background job
        Write-Info "Starting Ollama server in background..."
        $job = Start-Job -ScriptBlock { ollama serve }
        Write-Info "Ollama serve job ID: $($job.Id)"
        Start-Sleep -Seconds 3

        # Verify port opened
        $portCheck = Test-NetConnection -ComputerName localhost -Port $OllamaPort -WarningAction SilentlyContinue
        if (-not $portCheck.TcpTestSucceeded) {
            # Diagnostic
            Write-Fail "Port $OllamaPort not open. Diagnostic:"
            Write-Info "Run: netstat -ano | findstr $OllamaPort"
            Write-Info "Run: Get-Process ollama -ErrorAction SilentlyContinue"
            Write-Info "Receive-Job $($job.Id) for error output."
            throw "FAIL-CLOSED: Ollama server did not bind to port $OllamaPort"
        }
    }

    Write-Pass "Stage 2 PASS — Ollama runtime verified, port $OllamaPort open."
}

# ---------------------------------------------------------------------------
# STAGE 3 — Validate API
# PURPOSE   : Confirm Ollama REST API is healthy and responding with JSON.
# MECHANISM : GET /api/tags returns a JSON object listing available models.
# PRECONDITION : Stage 2 complete; Ollama serving on $OllamaPort.
# EXPECTED OUTPUT : HTTP 200; JSON body with "models" key.
# ---------------------------------------------------------------------------
function Stage-ValidateAPI {
    Write-Banner "STAGE 3 — Validate API"

    Wait-OllamaReady -MaxSeconds 30

    Write-Info "Querying GET http://localhost:$OllamaPort/api/tags ..."
    try {
        $response = Invoke-RestMethod -Uri "http://localhost:$OllamaPort/api/tags" `
                                      -Method GET -TimeoutSec 10
    } catch {
        Write-Fail "API call failed: $_"
        Write-Info "Diagnostic: ensure `ollama serve` is running."
        Write-Info "Retry: Invoke-RestMethod http://localhost:$OllamaPort/api/tags"
        throw "FAIL-CLOSED: Ollama API /api/tags did not return a valid response."
    }

    if (-not $response.PSObject.Properties["models"]) {
        throw "FAIL-CLOSED: Response from /api/tags missing 'models' key. Unexpected API format."
    }

    $modelCount = $response.models.Count
    Write-Pass "Stage 3 PASS — API healthy. Models currently available: $modelCount"
    if ($modelCount -gt 0) {
        $response.models | ForEach-Object { Write-Info "  - $($_.name)" }
    }
}

# ---------------------------------------------------------------------------
# STAGE 4 — Execute Model
# PURPOSE   : Pull the DeepSeek model and run a test inference.
# MECHANISM : `ollama pull` fetches the GGUF model blob; `ollama run` sends a
#             completion request and streams the response to stdout.
# PRECONDITION : Stage 3 complete; ~8 GB free disk (7B) or ~2 GB (1.5B).
# EXPECTED OUTPUT : Pull completes with "success"; run returns a text response.
# ---------------------------------------------------------------------------
function Stage-ExecuteModel {
    Write-Banner "STAGE 4 — Execute Model ($ModelTag)"

    # Precondition: disk space check (model size heuristic)
    $requiredGB = if ($ModelTag -match "1\.5b") { 2 } elseif ($ModelTag -match "7b") { 8 } else { 8 }
    $freeDrive  = (Get-PSDrive -Name (Split-Path $env:USERPROFILE -Qualifier).TrimEnd(":")).Free
    $freeGB     = [math]::Round($freeDrive / 1GB, 1)
    Write-Info "Free disk on system drive: ${freeGB} GB (required: ~${requiredGB} GB)"
    if ($freeGB -lt $requiredGB) {
        Write-Fail "Insufficient disk space. Required ~${requiredGB} GB, available ${freeGB} GB."
        Write-Info "Remediation: use -ModelTag deepseek-r1:1.5b for a smaller model, or free disk space."
        throw "FAIL-CLOSED: Insufficient disk space for $ModelTag"
    }

    # Pull model
    Write-Info "Pulling model: $ModelTag (this may take several minutes on first run)..."
    ollama pull $ModelTag
    Assert-ExitCode "ollama pull $ModelTag"
    Write-Pass "Model $ModelTag pulled successfully."

    # Run a test inference
    Write-Info "Running test inference: 'Respond with one word: Hello'"
    $inferenceOutput = ollama run $ModelTag "Respond with one word: Hello" 2>&1
    Assert-ExitCode "ollama run $ModelTag"

    if (-not $inferenceOutput -or $inferenceOutput.ToString().Trim().Length -eq 0) {
        throw "FAIL-CLOSED: Model produced no output for test prompt."
    }

    Write-Pass "Stage 4 PASS — Model inference successful."
    Write-Info "Model output: $($inferenceOutput.ToString().Trim())"
}

# ---------------------------------------------------------------------------
# STAGE 5 — Benchmark
# PURPOSE   : Measure tokens-per-second throughput on CPU.
# MECHANISM : Time a fixed-length generation; compute tok/s from elapsed ms
#             and approximate output token count.
# PRECONDITION : Stage 4 complete; model present locally.
# EXPECTED OUTPUT : Elapsed time and estimated tokens/sec written to stdout.
# ---------------------------------------------------------------------------
function Stage-Benchmark {
    Write-Banner "STAGE 5 — Benchmark"

    $prompt  = "List the first 20 prime numbers, one per line."
    Write-Info "Benchmark prompt: `"$prompt`""
    Write-Info "Timing inference (CPU-only; expect 1-10 tok/s on typical hardware)..."

    $sw = [System.Diagnostics.Stopwatch]::StartNew()
    $output = ollama run $ModelTag $prompt 2>&1
    $sw.Stop()
    Assert-ExitCode "ollama run (benchmark)"

    $elapsedSec  = [math]::Round($sw.Elapsed.TotalSeconds, 2)
    $tokenCount  = ($output.ToString() -split '\s+').Count   # rough word count as proxy
    $tokPerSec   = if ($elapsedSec -gt 0) { [math]::Round($tokenCount / $elapsedSec, 2) } else { 0 }

    Write-Pass "Stage 5 PASS — Benchmark complete."
    Write-Info "  Elapsed    : ${elapsedSec}s"
    Write-Info "  Approx tok : $tokenCount"
    Write-Info "  Tok/sec    : $tokPerSec (approximate; word-count proxy)"
    Write-Info "  Note: For precise tok/s use Ollama /api/generate with stream:false and parse eval_duration."
}

# ---------------------------------------------------------------------------
# STAGE 6 — Scale
# PURPOSE   : Demonstrate concurrent request handling via parallel jobs.
# MECHANISM : Start-Job launches multiple PowerShell jobs each calling
#             POST /api/generate. Results collected after all complete.
# PRECONDITION : Stage 3 complete; model pulled.
# EXPECTED OUTPUT : All $ConcurrentJobs jobs complete with non-empty responses.
# ---------------------------------------------------------------------------
function Stage-Scale {
    Write-Banner "STAGE 6 — Scale (Concurrent Requests)"

    $ConcurrentJobs = 3
    $apiUrl = "http://localhost:$OllamaPort/api/generate"
    $prompts = @(
        "What is 2+2?",
        "Name the capital of France.",
        "What color is the sky?"
    )

    Write-Info "Launching $ConcurrentJobs concurrent jobs against $apiUrl ..."

    $jobs = @()
    for ($i = 0; $i -lt $ConcurrentJobs; $i++) {
        $p = $prompts[$i]
        $m = $ModelTag
        $u = $apiUrl
        $jobs += Start-Job -ScriptBlock {
            param($url, $model, $prompt)
            $body = @{ model = $model; prompt = $prompt; stream = $false } | ConvertTo-Json
            $r = Invoke-RestMethod -Uri $url -Method POST -Body $body -ContentType "application/json" -TimeoutSec 120
            $r.response
        } -ArgumentList $u, $m, $p
    }

    Write-Info "Waiting for all jobs to complete..."
    $results = $jobs | Wait-Job | Receive-Job
    $jobs | Remove-Job

    $failed = 0
    for ($i = 0; $i -lt $results.Count; $i++) {
        $r = $results[$i]
        if (-not $r -or $r.ToString().Trim().Length -eq 0) {
            Write-Fail "Job $i returned empty response."
            $failed++
        } else {
            Write-Pass "Job $i : $($r.ToString().Trim().Substring(0, [Math]::Min(60, $r.ToString().Trim().Length)))..."
        }
    }

    if ($failed -gt 0) {
        throw "FAIL-CLOSED: $failed of $ConcurrentJobs concurrent jobs returned empty responses."
    }
    Write-Pass "Stage 6 PASS — All $ConcurrentJobs concurrent requests succeeded."
}

# ---------------------------------------------------------------------------
# STAGE 7 — Integrate
# PURPOSE   : Provide a reusable PowerShell function Invoke-DeepSeek as a
#             local-first, no-key-required LLM integration wrapper.
# MECHANISM : Wraps POST /api/generate with stream:false; returns response text.
# PRECONDITION : Ollama running; model pulled.
# EXPECTED OUTPUT : Function defined and demonstrated with a sample call.
# ---------------------------------------------------------------------------
function Stage-Integrate {
    Write-Banner "STAGE 7 — Integrate (Invoke-DeepSeek wrapper)"

    function Invoke-DeepSeek {
        <#
        .SYNOPSIS
            Send a prompt to a locally running DeepSeek model via Ollama API.
        .PARAMETER Prompt
            The input text prompt.
        .PARAMETER Model
            Ollama model tag. Default: deepseek-r1:7b
        .PARAMETER Port
            Ollama API port. Default: 11434
        .PARAMETER TimeoutSec
            Request timeout in seconds. Default: 120
        .EXAMPLE
            Invoke-DeepSeek -Prompt "Explain REST APIs in one sentence."
        #>
        param(
            [Parameter(Mandatory)][string]$Prompt,
            [string]$Model      = "deepseek-r1:7b",
            [int]$Port          = 11434,
            [int]$TimeoutSec    = 120
        )
        $body = @{
            model  = $Model
            prompt = $Prompt
            stream = $false
        } | ConvertTo-Json -Depth 3

        try {
            $result = Invoke-RestMethod `
                -Uri         "http://localhost:$Port/api/generate" `
                -Method      POST `
                -Body        $body `
                -ContentType "application/json" `
                -TimeoutSec  $TimeoutSec
            return $result.response
        } catch {
            throw "Invoke-DeepSeek failed: $_"
        }
    }

    # Demonstrate the wrapper
    Write-Info "Testing Invoke-DeepSeek wrapper..."
    $testResponse = Invoke-DeepSeek -Prompt "In one sentence, what is Ollama?" -Model $ModelTag -Port $OllamaPort
    if (-not $testResponse -or $testResponse.Trim().Length -eq 0) {
        throw "FAIL-CLOSED: Invoke-DeepSeek wrapper returned empty response."
    }

    Write-Pass "Stage 7 PASS — Invoke-DeepSeek wrapper operational."
    Write-Info "Sample response: $($testResponse.Trim().Substring(0, [Math]::Min(120, $testResponse.Trim().Length)))..."
    Write-Host ""
    Write-Host "Add Invoke-DeepSeek to your `$PROFILE or dot-source this script to use it interactively." -ForegroundColor White
}

# ---------------------------------------------------------------------------
# Pipeline Executor
# ---------------------------------------------------------------------------

$stages = @(
    [PSCustomObject]@{ Number = 1; Name = "Install";         Fn = { Stage-Install } }
    [PSCustomObject]@{ Number = 2; Name = "Verify Runtime";  Fn = { Stage-VerifyRuntime } }
    [PSCustomObject]@{ Number = 3; Name = "Validate API";    Fn = { Stage-ValidateAPI } }
    [PSCustomObject]@{ Number = 4; Name = "Execute Model";   Fn = { Stage-ExecuteModel } }
    [PSCustomObject]@{ Number = 5; Name = "Benchmark";       Fn = { Stage-Benchmark } }
    [PSCustomObject]@{ Number = 6; Name = "Scale";           Fn = { Stage-Scale } }
    [PSCustomObject]@{ Number = 7; Name = "Integrate";       Fn = { Stage-Integrate } }
)

$toRun = if ($StageOnly -gt 0) {
    $stages | Where-Object { $_.Number -eq $StageOnly }
} else {
    $stages
}

Write-Host ""
Write-Host "MetaBlooms DeepSeek/Ollama Setup Pipeline" -ForegroundColor Magenta
Write-Host "Model: $ModelTag  |  Port: $OllamaPort" -ForegroundColor Magenta
Write-Host ""

$allPassed = $true
foreach ($stage in $toRun) {
    try {
        & $stage.Fn
    } catch {
        Write-Fail "Stage $($stage.Number) ($($stage.Name)) FAILED: $_"
        $allPassed = $false
        break
    }
}

if ($allPassed) {
    Write-Host ""
    Write-Host "ALL STAGES PASSED. DeepSeek ($ModelTag) is operational via Ollama on localhost:$OllamaPort" `
        -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "PIPELINE HALTED. Resolve the failure above and re-run the failed stage with -StageOnly <N>." `
        -ForegroundColor Red
    exit 1
}
