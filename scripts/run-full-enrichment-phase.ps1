#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Run full open data enrichment across all states in phases
.DESCRIPTION
    Processes all state files through the Pre-MRD Phase enrichment pipeline
    with official website scraping (up to 10 pages per museum).
    Divides states into logical batches for progress tracking.
#>

param(
    [int]$MaxPages = 10,
    [switch]$SkipIndexRebuild,
    [string[]]$StatesOnly
)

$ErrorActionPreference = "Stop"

# State groupings for phased processing
$phases = @{
    "Phase1_Small" = @("AK", "HI", "ND", "SD", "MT", "WY", "ID", "NV", "UT", "NM")  # 10 states, smaller museums
    "Phase2_Medium" = @("VT", "NH", "ME", "RI", "DE", "WV", "NE", "KS", "MS", "OK")  # 10 states, medium size
    "Phase3_South" = @("AL", "AR", "LA", "SC", "KY", "TN")  # 6 states, southern region
    "Phase4_Midwest" = @("IA", "MO", "WI", "MN", "IN", "OH", "MI")  # 7 states, midwest
    "Phase5_Mountain" = @("CO", "AZ", "OR", "WA")  # 4 states, mountain/west
    "Phase6_Northeast" = @("CT", "NJ", "MD", "VA", "NC", "GA")  # 6 states, northeast/mid-atlantic
    "Phase7_Major" = @("MA", "PA", "IL", "TX", "FL", "CA", "NY", "DC")  # 8 states, largest collections
    "Phase8_Other" = @("ZZ")  # 1 state, international/other
}

$python = ".venv\Scripts\python.exe"
$script = "scripts\enrich-open-data.py"

# If specific states requested, filter to only those
if ($StatesOnly) {
    $filteredPhases = @{}
    foreach ($phaseName in $phases.Keys | Sort-Object) {
        $statesInPhase = $phases[$phaseName] | Where-Object { $StatesOnly -contains $_ }
        if ($statesInPhase) {
            $filteredPhases[$phaseName] = $statesInPhase
        }
    }
    $phases = $filteredPhases
}

Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host "MuseumSpark - Full Open Data Enrichment Pipeline" -ForegroundColor Cyan
Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host ""
Write-Host "Configuration:" -ForegroundColor Yellow
Write-Host "  Max pages per museum: $MaxPages"
Write-Host "  Total phases: $($phases.Count)"
Write-Host "  Total states: $($phases.Values | ForEach-Object { $_.Count } | Measure-Object -Sum | Select-Object -ExpandProperty Sum)"
Write-Host ""

$totalStates = 0
$processedStates = 0
$failedStates = @()
$startTime = Get-Date

foreach ($phaseName in $phases.Keys | Sort-Object) {
    $statesInPhase = $phases[$phaseName]
    $totalStates += $statesInPhase.Count
    
    Write-Host ""
    Write-Host "=" * 80 -ForegroundColor Green
    Write-Host "$phaseName - $($statesInPhase.Count) states" -ForegroundColor Green
    Write-Host "=" * 80 -ForegroundColor Green
    Write-Host "States: $($statesInPhase -join ', ')"
    Write-Host ""
    
    foreach ($state in $statesInPhase) {
        $processedStates++
        Write-Host ""
        Write-Host "[$processedStates/$totalStates] Processing: $state" -ForegroundColor Cyan
        Write-Host "-" * 60
        
        try {
            $args = @(
                $script,
                "--state", $state,
                "--scrape-website",
                "--scrape-max-pages", $MaxPages,
                "--compute-mrd-fields"
            )
            
            & $python $args
            
            if ($LASTEXITCODE -ne 0) {
                throw "Enrichment failed with exit code $LASTEXITCODE"
            }
            
            Write-Host "[OK] Completed: $state" -ForegroundColor Green
            
        } catch {
            Write-Host "[ERROR] Failed: $state - $_" -ForegroundColor Red
            $failedStates += $state
        }
    }
    
    # Rebuild index after each phase
    if (-not $SkipIndexRebuild) {
        Write-Host ""
        Write-Host "Rebuilding master index after $phaseName..." -ForegroundColor Yellow
        try {
            & $python "scripts\build-index.py" "--update-nearby-counts"
            Write-Host "[OK] Index rebuilt" -ForegroundColor Green
        } catch {
            Write-Host "[WARN] Index rebuild failed: $_" -ForegroundColor Yellow
        }
    }
}

$endTime = Get-Date
$duration = $endTime - $startTime

Write-Host ""
Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host "Enrichment Pipeline Complete" -ForegroundColor Cyan
Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host ""
Write-Host "Summary:" -ForegroundColor Yellow
Write-Host "  Total states processed: $processedStates"
Write-Host "  Successful: $($processedStates - $failedStates.Count)"
Write-Host "  Failed: $($failedStates.Count)"
if ($failedStates.Count -gt 0) {
    Write-Host "  Failed states: $($failedStates -join ', ')" -ForegroundColor Red
}
Write-Host "  Duration: $($duration.ToString('hh\:mm\:ss'))"
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Review any failed states and retry if needed"
Write-Host "  2. Run: python scripts/build-progress.py"
Write-Host "  3. Run: python scripts/build-missing-report.py"
Write-Host "  4. Commit changes to git"
Write-Host ""
