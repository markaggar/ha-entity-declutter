param(
    [ValidateSet("dev", "prod")]
    [string]$Environment = "dev",
    [string]$HAHost,
    [string]$PyScriptDest,
    [string]$Token,
    [switch]$TestRun,
    [switch]$DumpLogs,
    [switch]$ForceCopy
)

# Environment-specific configuration
$environments = @{
    "dev" = @{
        Host = "10.0.0.55"
        PyScriptPath = "\\10.0.0.55\config\pyscript"
        Token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiIwYjRjNGRjY2JkZmE0MDlmODRhZmY3ZjhiZGJmYzdlNSIsImlhdCI6MTc1OTM2Mzk0MSwiZXhwIjoyMDc0NzIzOTQxfQ.ZlT1aOXxJIqp_GUrfjrzspl470RpYwB3QfjwPxyM_UA"
        EnvVar = "HA_DEV_TOKEN"
    }
    "prod" = @{
        Host = "10.0.0.26"
        PyScriptPath = "\\10.0.0.26\config\pyscript"
        Token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJmNjA4NGE1ZjE2ZWY0NDQ1OWUxNjU3MTNmZDg2NDJkOCIsImlhdCI6MTc1OTA4OTM3NywiZXhwIjoyMDc0NDQ5Mzc3fQ.oVj-uy96t5HWvH2Z_U-KDOTsF76uVJCdrOTWqwaTuiU"
        EnvVar = "HA_PROD_TOKEN"
    }
}

# Use environment-specific settings or override with parameters
$currentEnv = $environments[$Environment]
if (-not $HAHost) { $HAHost = $currentEnv.Host }
if (-not $PyScriptDest) { $PyScriptDest = $currentEnv.PyScriptPath }

# Token selection priority: 1) Parameter, 2) Environment-specific env var, 3) Hardcoded fallback
if (-not $Token) { 
    $envToken = [Environment]::GetEnvironmentVariable($currentEnv.EnvVar)
    if ($envToken) {
        $Token = $envToken
        Write-Host "Using token from $($currentEnv.EnvVar)" -ForegroundColor DarkGray
    } else {
        $Token = $currentEnv.Token 
        Write-Host "Using hardcoded token for $Environment" -ForegroundColor DarkGray
    }
}

# Track deployment status
$script:deploymentFailed = $false
$filesCopied = $false

Write-Host "=== PyScript Helper Analysis Deployment ===" -ForegroundColor Cyan
Write-Host "Environment: $Environment ($HAHost)" -ForegroundColor Cyan
Write-Host "Target: $PyScriptDest" -ForegroundColor Cyan

# Get script directory and source files
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$analyzeScript = Join-Path $scriptDir "analyze_helpers.py"
$deleteScript = Join-Path $scriptDir "delete_helpers.py"

# Verify source files exist
if (-not (Test-Path $analyzeScript)) {
    Write-Error "analyze_helpers.py not found in $scriptDir"
    exit 1
}
if (-not (Test-Path $deleteScript)) {
    Write-Error "delete_helpers.py not found in $scriptDir"
    exit 1
}

# Create destination directory if needed
if (-not (Test-Path $PyScriptDest)) {
    Write-Host "Creating PyScript directory: $PyScriptDest" -ForegroundColor Yellow
    try {
        New-Item -ItemType Directory -Force -Path $PyScriptDest | Out-Null
    } catch {
        Write-Error "Failed to create PyScript directory: $($_.Exception.Message)"
        exit 1
    }
}

# Deploy files using robocopy for reliability
$deployFiles = @(
    @{ Src = $analyzeScript; Name = "analyze_helpers.py" }
    @{ Src = $deleteScript; Name = "delete_helpers.py" }
)

foreach ($file in $deployFiles) {
    $srcDir = Split-Path -Parent $file.Src
    $fileName = $file.Name
    
    Write-Host "Deploying $fileName..." -ForegroundColor DarkGray
    
    $robocopyArgs = @(
        $srcDir,
        $PyScriptDest,
        $fileName,
        '/R:2', '/W:2', '/FFT'
    )
    
    if ($ForceCopy) {
        $robocopyArgs += @('/IS', '/IT')
    }
    
    & robocopy $robocopyArgs | Out-Null
    $code = $LASTEXITCODE
    if ($code -lt 0) { $code = 16 }
    
    if ($code -le 7) {
        if (($code -band 1) -ne 0) {
            $filesCopied = $true
            Write-Host "✓ Copied $fileName (robocopy code $code)" -ForegroundColor Green
        } else {
            Write-Host "✓ $fileName up to date (robocopy code $code)" -ForegroundColor DarkGray
        }
    } else {
        Write-Warning "Robocopy failed for $fileName (code $code), trying fallback..."
        try {
            Copy-Item -Path $file.Src -Destination (Join-Path $PyScriptDest $fileName) -Force
            $filesCopied = $true
            Write-Host "✓ Copied $fileName (fallback)" -ForegroundColor Yellow
        } catch {
            Write-Error "Failed to copy $fileName : $($_.Exception.Message)"
            $script:deploymentFailed = $true
        }
    }
}

if ($script:deploymentFailed) {
    Write-Error "Deployment failed!"
    exit 1
}

if (-not $filesCopied) {
    Write-Host "No files needed updating. Use -ForceCopy to force deployment." -ForegroundColor DarkGray
}

# Test PyScript services if requested
if ($TestRun -and -not [string]::IsNullOrWhiteSpace($Token)) {
    $baseUrl = "http://${HAHost}:8123"
    Write-Host "Base URL: $baseUrl" -ForegroundColor DarkGray
    $headers = @{ 
        Authorization = "Bearer $Token"
        'Content-Type' = 'application/json' 
    }
    
    Write-Host "`n=== Testing PyScript Services ===" -ForegroundColor Cyan
    
    # Wait a moment for PyScript to reload
    if ($filesCopied) {
        Write-Host "Waiting 5 seconds for PyScript to reload..." -ForegroundColor DarkGray
        Start-Sleep -Seconds 5
    }
    
    # Test 1: Check if pyscript.analyze_helpers service exists
    try {
        Write-Host "Checking for pyscript.analyze_helpers service..." -ForegroundColor DarkGray
        $servicesUri = "$baseUrl/api/services"
        $services = Invoke-RestMethod -Method Get -Uri $servicesUri -Headers $headers -TimeoutSec 15
        
        $pyscriptServices = $services.pyscript
        if ($pyscriptServices -and $pyscriptServices.analyze_helpers) {
            Write-Host "✓ pyscript.analyze_helpers service found" -ForegroundColor Green
        } else {
            Write-Warning "pyscript.analyze_helpers service not found. PyScript may not have loaded the script."
            $script:deploymentFailed = $true
        }
    } catch {
        Write-Warning "Failed to check services: $($_.Exception.Message)"
        $script:deploymentFailed = $true
    }
    
    # Test 2: Try running the enhanced analysis
    try {
        Write-Host "Running enhanced helper analysis test..." -ForegroundColor DarkGray
        $analyzeUri = "$baseUrl/api/services/pyscript/analyze_helpers"
        $response = Invoke-RestMethod -Method Post -Uri $analyzeUri -Headers $headers -Body '{}' -TimeoutSec 180
        Write-Host "✓ Enhanced analysis service called successfully" -ForegroundColor Green
        
        # Wait for analysis to complete
        Start-Sleep -Seconds 15
        
        # Check for results
        try {
            $statusUri = "$baseUrl/api/states/sensor.helper_analysis_status"
            $status = Invoke-RestMethod -Method Get -Uri $statusUri -Headers $headers -TimeoutSec 10
            if ($status -and $status.state -eq 'complete') {
                Write-Host "✓ Analysis completed successfully" -ForegroundColor Green
                $attrs = $status.attributes
                Write-Host "  Total helpers: $($attrs.total_helpers)" -ForegroundColor DarkGray
                Write-Host "  Orphaned: $($attrs.orphaned_count)" -ForegroundColor DarkGray
                if ($attrs.template_files_analyzed) {
                    Write-Host "  Template files analyzed: $($attrs.template_files_analyzed)" -ForegroundColor DarkGray
                }
                if ($attrs.template_dependencies_found) {
                    Write-Host "  Template dependencies found: $($attrs.template_dependencies_found)" -ForegroundColor DarkGray
                }
            } else {
                Write-Warning "Analysis may not have completed. Status: $($status.state)"
            }
        } catch {
            Write-Warning "Could not check analysis status: $($_.Exception.Message)"
        }
        
    } catch {
        Write-Warning "Failed to run analysis: $($_.Exception.Message)"
        $script:deploymentFailed = $true
    }
}

# Get logs if requested or if there were failures
if ($DumpLogs -or $script:deploymentFailed) {
    if (-not [string]::IsNullOrWhiteSpace($Token)) {
        Write-Host "`n=== Home Assistant Logs ===" -ForegroundColor Cyan
        try {
            $logUri = "$baseUrl/api/error_log"
            $logHeaders = @{ Authorization = "Bearer $Token"; 'Accept' = 'text/plain' }
            $logContent = Invoke-RestMethod -Method Get -Uri $logUri -Headers $logHeaders -TimeoutSec 20
            
            if ($logContent) {
                $lines = $logContent -split "`n"
                # Look for PyScript and helper analysis related lines
                $relevantLines = $lines | Where-Object { 
                    $_ -match 'pyscript|analyze_helpers|delete_helpers|helper_analysis|template.*depend|discover.*template' 
                } | Select-Object -Last 50
                
                if ($relevantLines) {
                    Write-Host "=== Recent PyScript/Helper Analysis Log Lines ===" -ForegroundColor Yellow
                    $relevantLines | ForEach-Object { Write-Host $_ -ForegroundColor Yellow }
                } else {
                    Write-Host "No PyScript/helper analysis related log entries found in recent logs." -ForegroundColor DarkGray
                }
                
                # Also show last 20 lines of general log
                Write-Host "`n=== Last 20 Log Lines ===" -ForegroundColor DarkYellow
                $lines | Select-Object -Last 20 | ForEach-Object { Write-Host $_ -ForegroundColor DarkYellow }
            }
        } catch {
            Write-Warning "Failed to fetch logs: $($_.Exception.Message)"
        }
    } else {
        Write-Host "Set HA_TOKEN environment variable or -Token parameter to fetch logs." -ForegroundColor DarkGray
    }
}

# Summary
Write-Host "`n=== Deployment Summary ===" -ForegroundColor Cyan
if ($script:deploymentFailed) {
    Write-Host "❌ Deployment had issues. Check logs above." -ForegroundColor Red
    exit 2
} else {
    Write-Host "✅ Deployment successful!" -ForegroundColor Green
    Write-Host "`nNext steps:" -ForegroundColor White
    Write-Host "1. Go to Developer Tools → Services in Home Assistant" -ForegroundColor DarkGray
    Write-Host "2. Run service: pyscript.analyze_helpers" -ForegroundColor DarkGray
    Write-Host "3. Check /config/helper_analysis/ for results" -ForegroundColor DarkGray
    Write-Host "4. Use the Home Assistant dashboard to manually delete helpers as needed" -ForegroundColor DarkGray
}

exit 0