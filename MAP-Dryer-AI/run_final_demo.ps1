param(
    [int]$RefreshSeconds = 5,
    [switch]$Resume
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# ============================================================================
# MAP-Dryer-AI — FINAL ONE-CLICK DEMO LAUNCHER
#
# Default behavior:
#   1) Uses realtime_pipeline/.env for DB/source/model configuration
#   2) Starts a FRESH demo by clearing only runtime demo tables
#   3) Forces the replay/inference cadence to 5 seconds
#   4) Forces Power BI automatic page refresh to 5 seconds
#   5) Starts realtime_service.py
#   6) Waits for the SQL/Power BI contract to become available
#   7) Opens the canonical .pbip dashboard
#   8) Keeps the simulation alive until Power BI is closed
#
# Resume without clearing runtime tables:
#   .\RUN_FINAL_DEMO.ps1 -Resume
#
# Different cadence (not recommended for the final presentation):
#   .\RUN_FINAL_DEMO.ps1 -RefreshSeconds 10
# ============================================================================

function Step([string]$Message) {
    Write-Host ""
    Write-Host "==> $Message" -ForegroundColor Cyan
}

function Success([string]$Message) {
    Write-Host "[OK] $Message" -ForegroundColor Green
}

function Fail([string]$Message) {
    throw $Message
}

function Find-BootstrapPython {
    $cmd = Get-Command python -ErrorAction SilentlyContinue
    if ($cmd) {
        return $cmd.Source
    }

    $py = Get-Command py -ErrorAction SilentlyContinue
    if ($py) {
        return $py.Source
    }

    Fail "Python was not found. Install Python 3 and rerun this launcher."
}

function Prepare-ProjectPython {
    $candidates = @(
        (Join-Path $ProjectRoot ".venv\Scripts\python.exe"),
        (Join-Path $ProjectRoot "venv\Scripts\python.exe"),
        (Join-Path $ProjectRoot "realtime_pipeline\.venv\Scripts\python.exe"),
        (Join-Path $ProjectRoot "realtime_pipeline\venv\Scripts\python.exe")
    )

    foreach ($candidate in $candidates) {
        if (Test-Path $candidate) {
            $python = (Resolve-Path $candidate).Path
            & $python -c "import dotenv, joblib, numpy, pandas, psycopg, scipy, sklearn" 2>$null
            if ($LASTEXITCODE -eq 0) {
                return $python
            }

            Step "Installing missing runtime dependencies into the project environment"
            & $python -m pip install -r (Join-Path $ProjectRoot "requirements.txt") -r (Join-Path $ProjectRoot "realtime_pipeline\requirements.txt")
            if ($LASTEXITCODE -ne 0) {
                Fail "Runtime dependencies could not be installed into $python."
            }
            return $python
        }
    }

    # No project venv exists. If the interpreter already on PATH satisfies the
    # runtime contract, use it rather than building and populating a new venv.
    $bootstrapPython = Find-BootstrapPython
    & $bootstrapPython -c "import dotenv, joblib, numpy, pandas, psycopg, scipy, sklearn" 2>$null
    if ($LASTEXITCODE -eq 0) {
        return $bootstrapPython
    }

    $venvRoot = Join-Path $ProjectRoot ".venv"
    Step "Creating the project Python environment"
    & $bootstrapPython -m venv $venvRoot
    if ($LASTEXITCODE -ne 0) {
        Fail "Could not create the project virtual environment at $venvRoot."
    }

    $python = Join-Path $venvRoot "Scripts\python.exe"
    & $python -m pip install -r (Join-Path $ProjectRoot "requirements.txt") -r (Join-Path $ProjectRoot "realtime_pipeline\requirements.txt")
    if ($LASTEXITCODE -ne 0) {
        Fail "Runtime dependencies could not be installed into $venvRoot."
    }
    return $python
}

function Patch-PowerBIRefresh([int]$Seconds) {
    $pagesRoot = Join-Path $PowerBIReportRoot "definition\pages"
    if (-not (Test-Path $pagesRoot)) {
        Fail "Power BI pages folder was not found: $pagesRoot"
    }

    $pageFiles = Get-ChildItem -Path $pagesRoot -Filter "page.json" -Recurse -File
    if (-not $pageFiles) {
        Fail "No Power BI page.json files were found."
    }

    # PBIR schema 2.1 stores DirectQuery APR as an ISO-8601 duration, e.g.
    # 'PT5S'. Older hand-authored pages may contain a 60D-style literal.
    $durationPattern = "'(?:PT)?\d+(?:S|D)'"
    $durationReplacement = "'PT${Seconds}S'"
    $utf8NoBom = New-Object System.Text.UTF8Encoding($false)

    $matched = 0
    $changed = 0
    $expectedDuration = '"Value"\s*:\s*"''PT{0}S''"' -f $Seconds

    foreach ($file in $pageFiles) {
        $text = [System.IO.File]::ReadAllText($file.FullName)

        if ($text -notmatch '"pageRefresh"') {
            continue
        }

        $newText = [System.Text.RegularExpressions.Regex]::Replace(
            $text, $durationPattern, $durationReplacement
        )

        if ($newText -ne $text) {
            [System.IO.File]::WriteAllText($file.FullName, $newText, $utf8NoBom)
            $changed++
        }

        if ($newText -match $expectedDuration) {
            $matched++
        }
    }

    if ($matched -eq 0) {
        Fail "Could not confirm a ${Seconds}-second automatic page refresh in the Power BI page definitions."
    }

    Success "Power BI automatic page refresh confirmed at ${Seconds}s on $matched page(s)."
}

function Reset-DemoTables {
    Step "Resetting runtime demo tables for a clean presentation replay"

    $env:MAP_DRYER_ENV_PATH = $EnvFile

    $resetCode = @'
import os
from dotenv import load_dotenv
import psycopg

env_path = os.environ["MAP_DRYER_ENV_PATH"]
load_dotenv(env_path, override=True)

required = ["DB_HOST", "DB_PORT", "DB_NAME", "DB_USER", "DB_PASSWORD"]
missing = [k for k in required if not os.getenv(k)]
if missing:
    raise RuntimeError("Missing DB settings in realtime_pipeline/.env: " + ", ".join(missing))

with psycopg.connect(
    host=os.environ["DB_HOST"],
    port=os.environ["DB_PORT"],
    dbname=os.environ["DB_NAME"],
    user=os.environ["DB_USER"],
    password=os.environ["DB_PASSWORD"],
) as conn:
    with conn.cursor() as cur:
        cur.execute("""
            TRUNCATE TABLE
                public.dryer_abnormal_variables,
                public.dryer_model_outputs,
                public.dryer_map
            RESTART IDENTITY CASCADE;
        """)
print("Runtime demo tables cleared.")
'@

    $resetCode | & $PythonExe -
    if ($LASTEXITCODE -ne 0) {
        Fail "Could not reset runtime demo tables. Verify PostgreSQL and realtime_pipeline/.env."
    }

    Success "Runtime demo tables reset. Datasets and model files were NOT touched."
}

function Test-RuntimeInputs {
    $env:MAP_DRYER_ENV_PATH = $EnvFile
    $env:MAP_DRYER_PIPELINE_ROOT = Split-Path -Parent $EnvFile

    $checkCode = @'
import os
from pathlib import Path
from dotenv import load_dotenv

env_path = Path(os.environ["MAP_DRYER_ENV_PATH"])
pipeline_root = Path(os.environ["MAP_DRYER_PIPELINE_ROOT"])
load_dotenv(env_path, override=False)

source = Path(os.environ.get("SOURCE_CSV_5S", "../data/raw/MAP_Dryer_Canonical_5s_deterministic.csv"))
models = Path(os.environ.get("MODELS_5S_DIR", "../models/5s"))
if not source.is_absolute():
    source = (pipeline_root / source).resolve()
if not models.is_absolute():
    models = (pipeline_root / models).resolve()

required = [
    source,
    models / "quality_moisture_pipeline.joblib",
    models / "anomaly_model.joblib",
    models / "anomaly_scaler.joblib",
    models / "feature_schema.json",
    models / "reference_profile.json",
]
missing = [str(path) for path in required if not path.is_file()]
if missing:
    raise FileNotFoundError("Missing required runtime files:\n- " + "\n- ".join(missing))
print(f"Replay source: {source}")
print(f"Model directory: {models}")
'@

    $checkCode | & $PythonExe -
    if ($LASTEXITCODE -ne 0) {
        Fail "Runtime input validation failed. Restore the canonical source/model artifact named above and rerun."
    }
    Success "Canonical source and final model artifacts are available."
}

# ---------------------------- Resolve project -------------------------------

$ProjectRoot = $PSScriptRoot
if (-not $ProjectRoot) {
    $ProjectRoot = (Get-Location).Path
}

$RealtimeScript   = Join-Path $ProjectRoot "realtime_pipeline\src\realtime_service.py"
$VerifyScript     = Join-Path $ProjectRoot "realtime_pipeline\src\verify_powerbi_views.py"
$BootstrapScript  = Join-Path $ProjectRoot "realtime_pipeline\src\apply_sql_migration.py"
$EnvFile          = Join-Path $ProjectRoot "realtime_pipeline\.env"
$PowerBIDir       = Join-Path $ProjectRoot "POWERBI DASHBOARD"
$PowerBIReportRoot = Join-Path $PowerBIDir "MAP Dryer AI Dashboard.Report"

foreach ($requiredPath in @($RealtimeScript, $EnvFile, $PowerBIDir)) {
    if (-not (Test-Path $requiredPath)) {
        Fail "Required project path not found: $requiredPath`nPlace RUN_FINAL_DEMO.ps1 in the MAP-Dryer-AI repository root."
    }
}

$PreferredPBIP = Join-Path $PowerBIDir "MAP Dryer AI Dashboard.pbip"
if (Test-Path $PreferredPBIP) {
    $PowerBIProject = $PreferredPBIP
}
else {
    $PowerBIProject = Get-ChildItem -Path $PowerBIDir -Filter "*.pbip" -File |
        Where-Object { $_.Name -notmatch '(?i)backup|old|test|draft' } |
        Select-Object -First 1 -ExpandProperty FullName
}

if (-not $PowerBIProject) {
    Fail "No canonical .pbip Power BI project was found in '$PowerBIDir'."
}

$PythonExe = Prepare-ProjectPython

Write-Host ""
Write-Host "============================================================" -ForegroundColor DarkGreen
Write-Host " MAP DRYER AI — FINAL 5-SECOND DEMO" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor DarkGreen
Write-Host "Project : $ProjectRoot"
Write-Host "Python  : $PythonExe"
Write-Host "Power BI: $PowerBIProject"
Write-Host "Cadence : $RefreshSeconds seconds"
Write-Host "Mode    : $(if ($Resume) { 'RESUME' } else { 'FRESH REPLAY' })"

# Do not modify PBIR files while Desktop has them open.
$existingPBI = Get-Process "PBIDesktop" -ErrorAction SilentlyContinue
if ($existingPBI) {
    Fail "Power BI Desktop is already open. Save/close it first, then rerun this launcher so the 5-second page-refresh setting can be applied safely."
}

# ---------------------------- Python sanity --------------------------------

Step "Checking Python"
& $PythonExe --version
if ($LASTEXITCODE -ne 0) {
    Fail "Python could not be executed."
}
Success "Python is available."

# ---------------------------- Environment ----------------------------------

Step "Preparing final 5-second replay settings"

# Remove stale shell-level project settings so realtime_service.py gets its
# DB/source/model configuration from realtime_pipeline/.env.
foreach ($name in @(
    "DB_HOST", "DB_PORT", "DB_NAME", "DB_USER", "DB_PASSWORD",
    "SOURCE_CSV_5S", "SOURCE_PARTITION_5S", "REPLAY_START_TIMESTAMP",
    "MODELS_5S_DIR"
)) {
    Remove-Item "Env:$name" -ErrorAction SilentlyContinue
}

# Runtime overrides for THIS launcher only.
$env:PYTHONUTF8 = "1"
# Unbuffered so realtime_pipeline/logs/final_demo_runtime.*.log stay
# readable while the service runs and survive a forced stop.
$env:PYTHONUNBUFFERED = "1"
$env:POLL_INTERVAL_SECONDS = [string]$RefreshSeconds
$env:REPLAY_INTERVAL_SECONDS = [string]$RefreshSeconds
$env:REPLAY_SPEED = "1"
$env:MAX_CYCLES = "0"
$env:EXIT_WHEN_EXHAUSTED = "true"
$env:CONTINUOUS_DEMO_MODE = "false"
$env:STALE_AFTER_SECONDS = [string]([Math]::Max(30, $RefreshSeconds * 6))
$env:REPLAY_FROM_START = if ($Resume) { "false" } else { "true" }

Success "Runtime cadence set to ${RefreshSeconds}s."

Step "Validating held-out replay and final model artifacts"
Test-RuntimeInputs

# ---------------------------- Power BI refresh -----------------------------

Step "Configuring Power BI for ${RefreshSeconds}-second DirectQuery page refresh"
Patch-PowerBIRefresh -Seconds $RefreshSeconds

# ---------------------------- Fresh/Resume DB -------------------------------

if (-not $Resume) {
    try {
        Reset-DemoTables
    }
    catch {
        # If the database/schema has never been initialized, bootstrap once.
        if (Test-Path $BootstrapScript) {
            Write-Warning "Initial reset failed. Attempting the existing database bootstrap once..."
            & $PythonExe $BootstrapScript
            if ($LASTEXITCODE -ne 0) {
                throw
            }
            Reset-DemoTables
        }
        else {
            throw
        }
    }
}
else {
    Success "Resume mode selected: existing runtime rows were preserved."
}

# ---------------------------- Start service --------------------------------

$ServiceProcess = $null
$LogDir = Join-Path $ProjectRoot "realtime_pipeline\logs"
$ServiceStdout = Join-Path $LogDir "final_demo_runtime.stdout.log"
$ServiceStderr = Join-Path $LogDir "final_demo_runtime.stderr.log"
New-Item -ItemType Directory -Path $LogDir -Force | Out-Null

try {
    Step "Starting the realtime inference/replay service"

    $ServiceProcess = Start-Process `
        -FilePath $PythonExe `
        -ArgumentList @("`"$RealtimeScript`"") `
        -WorkingDirectory $ProjectRoot `
        -RedirectStandardOutput $ServiceStdout `
        -RedirectStandardError $ServiceStderr `
        -PassThru

    Start-Sleep -Seconds 2
    $ServiceProcess.Refresh()

    if ($ServiceProcess.HasExited) {
        $details = if (Test-Path $ServiceStderr) { Get-Content $ServiceStderr -Raw } else { "No stderr log was produced." }
        $serviceExitCode = $ServiceProcess.ExitCode
        Fail ("The realtime service exited immediately with code {0}`n{1}" -f $serviceExitCode, $details)
    }

    Success ("Realtime service started (PID {0})" -f $ServiceProcess.Id)

    # ------------------------ Wait for SQL contract -------------------------

    if (Test-Path $VerifyScript) {
        Step "Waiting for PostgreSQL / Power BI views to become ready"

        $ready = $false
        $maxAttempts = 18   # about 90 seconds max
        $verifyLog = Join-Path $env:TEMP "map_dryer_verify_powerbi.txt"

        for ($attempt = 1; $attempt -le $maxAttempts; $attempt++) {
            Start-Sleep -Seconds 5

            $ServiceProcess.Refresh()
            if ($ServiceProcess.HasExited) {
                Fail "The realtime service stopped during startup with code $($ServiceProcess.ExitCode)."
            }

            & $PythonExe $VerifyScript *> $verifyLog
            if ($LASTEXITCODE -eq 0) {
                $ready = $true
                break
            }

            Write-Host "   Waiting for first data/view readiness... ($attempt/$maxAttempts)"
        }

        if ($ready) {
            Success "PostgreSQL / Power BI view verification passed."
        }
        else {
            $details = if (Test-Path $verifyLog) { Get-Content $verifyLog -Raw } else { "No verifier log was produced." }
            Fail "Power BI SQL views did not become ready within 90 seconds.`n$details"
        }
    }
    else {
        Write-Warning "verify_powerbi_views.py was not found; skipping the optional readiness check."
        Start-Sleep -Seconds 8
    }

    # ----------------------------- Open PBI ---------------------------------

    Step "Opening the final Power BI dashboard"
    Start-Process -FilePath $PowerBIProject | Out-Null

    # The Microsoft Store build starts through a short-lived PBIDesktop.exe
    # before handing the PBIP to the real report window. Track the titled
    # window, not that temporary process, or the runtime stops during loading.
    $DashboardTitle = [System.IO.Path]::GetFileNameWithoutExtension($PowerBIProject)
    $PowerBIProcess = $null
    for ($i = 1; $i -le 90; $i++) {
        Start-Sleep -Seconds 2
        $PowerBIProcess = Get-Process "PBIDesktop" -ErrorAction SilentlyContinue |
            Where-Object { $_.MainWindowTitle -like "*$DashboardTitle*" } |
            Sort-Object StartTime |
            Select-Object -First 1

        if ($PowerBIProcess) {
            break
        }

        if ($i % 5 -eq 0) {
            Write-Host "   Power BI is loading the dashboard... ($($i * 2)s)"
        }
    }

    if (-not $PowerBIProcess) {
        Fail "Power BI Desktop did not open '$DashboardTitle' within 180 seconds."
    }

    # Make the completed report visible instead of leaving it behind the
    # launcher/VS Code after the Store-app process handoff.
    try {
        $Shell = New-Object -ComObject WScript.Shell
        $null = $Shell.AppActivate($PowerBIProcess.Id)
    }
    catch {
        Write-Warning "The dashboard opened but could not be brought to the foreground automatically."
    }

    Write-Host ""
    Write-Host "============================================================" -ForegroundColor DarkGreen
    Write-Host " DEMO RUNNING" -ForegroundColor Green
    Write-Host "============================================================" -ForegroundColor DarkGreen
    Write-Host "• Runtime inserts one observation approximately every ${RefreshSeconds}s."
    Write-Host "• Power BI DirectQuery pages refresh approximately every ${RefreshSeconds}s."
    Write-Host "• The dashboard is the existing canonical .pbip project."
    Write-Host "• Close Power BI to stop the simulation automatically."
    Write-Host "• Or press Ctrl+C in this launcher."
    Write-Host ""

    Success ("Power BI dashboard opened (PID {0})" -f $PowerBIProcess.Id)

    # Follow the titled report window rather than one PID. This remains valid
    # if Power BI performs another internal process handoff.
    while ($true) {
        Start-Sleep -Seconds 2
        $OpenDashboard = Get-Process "PBIDesktop" -ErrorAction SilentlyContinue |
            Where-Object { $_.MainWindowTitle -like "*$DashboardTitle*" } |
            Select-Object -First 1
        if (-not $OpenDashboard) {
            Start-Sleep -Seconds 3
            $OpenDashboard = Get-Process "PBIDesktop" -ErrorAction SilentlyContinue |
                Where-Object { $_.MainWindowTitle -like "*$DashboardTitle*" } |
                Select-Object -First 1
            if (-not $OpenDashboard) {
                break
            }
        }
    }
}
finally {
    if ($ServiceProcess) {
        try {
            $ServiceProcess.Refresh()
            if (-not $ServiceProcess.HasExited) {
                Step "Stopping realtime simulation"
                Stop-Process -Id $ServiceProcess.Id -Force -ErrorAction SilentlyContinue
                Success "Realtime service stopped."
            }
        }
        catch {
            # Nothing else to clean up.
        }
    }

    Remove-Item Env:MAP_DRYER_ENV_PATH -ErrorAction SilentlyContinue
}

Write-Host ""
Write-Host "Demo finished." -ForegroundColor Green
