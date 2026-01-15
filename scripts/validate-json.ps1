# MuseumSpark State JSON Validator
# PowerShell script to validate state JSON files

param(
    [Parameter(Mandatory=$false)]
    [string]$State
)

function Test-JsonSyntax {
    param(
        [string]$FilePath
    )

    try {
        $content = Get-Content -Path $FilePath -Raw -ErrorAction Stop
        $json = $content | ConvertFrom-Json -ErrorAction Stop
        return $true, $json, $null
    }
    catch {
        return $false, $null, $_.Exception.Message
    }
}

function Test-RequiredFields {
    param(
        [object]$StateData,
        [string]$FileName
    )

    $errors = @()

    # Check state-level fields
    if (-not $StateData.state) {
        $errors += "Missing required field: state"
    }
    if (-not $StateData.state_code) {
        $errors += "Missing required field: state_code"
    }
    if (-not $StateData.museums) {
        $errors += "Missing required field: museums"
    }

    # Check each museum
    if ($StateData.museums) {
        for ($i = 0; $i -lt $StateData.museums.Count; $i++) {
            $museum = $StateData.museums[$i]
            $prefix = "Museum #$($i+1)"

            if (-not $museum.museum_name) {
                $errors += "$prefix: Missing required field: museum_name"
            }
            if (-not $museum.country) {
                $errors += "$prefix: Missing required field: country"
            }
            if (-not $museum.state_province) {
                $errors += "$prefix: Missing required field: state_province"
            }
            if (-not $museum.city) {
                $errors += "$prefix: Missing required field: city"
            }
            if (-not $museum.museum_type) {
                $errors += "$prefix: Missing required field: museum_type"
            }
        }
    }

    return $errors
}

# Determine project root (script is in scripts/ directory)
$ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptRoot
$StatesDir = Join-Path $ProjectRoot "data\states"

Write-Host "MuseumSpark State JSON Validator" -ForegroundColor Cyan
Write-Host "=" * 50

# Determine which files to validate
if ($State) {
    $StateCode = $State.ToUpper()
    $Files = @(Get-Item (Join-Path $StatesDir "$StateCode.json") -ErrorAction SilentlyContinue)
    if ($Files.Count -eq 0) {
        Write-Host "❌ Error: State file not found: $StateCode.json" -ForegroundColor Red
        exit 1
    }
}
else {
    $Files = Get-ChildItem -Path $StatesDir -Filter "*.json" -File | Sort-Object Name
    if ($Files.Count -eq 0) {
        Write-Host "❌ Error: No JSON files found in $StatesDir" -ForegroundColor Red
        exit 1
    }
}

Write-Host "`nValidating $($Files.Count) file(s)...`n"

$ValidCount = 0
$InvalidCount = 0

foreach ($File in $Files) {
    $FileName = $File.Name

    # Test JSON syntax
    $isValid, $data, $error = Test-JsonSyntax -FilePath $File.FullName

    if (-not $isValid) {
        Write-Host "❌ $FileName : Invalid JSON" -ForegroundColor Red
        Write-Host "   Error: $error" -ForegroundColor Red
        $InvalidCount++
        continue
    }

    # Test required fields
    $fieldErrors = Test-RequiredFields -StateData $data -FileName $FileName

    if ($fieldErrors.Count -gt 0) {
        Write-Host "❌ $FileName : Validation failed" -ForegroundColor Red
        foreach ($err in $fieldErrors) {
            Write-Host "   $err" -ForegroundColor Red
        }
        $InvalidCount++
    }
    else {
        Write-Host "✓ $FileName : Valid" -ForegroundColor Green
        $ValidCount++
    }
}

# Summary
Write-Host "`n$('=' * 50)"
Write-Host "Validation Summary:"
Write-Host "  ✓ Valid files: $ValidCount" -ForegroundColor Green
Write-Host "  ❌ Invalid files: $InvalidCount" -ForegroundColor Red
Write-Host "=" * 50

if ($InvalidCount -gt 0) {
    Write-Host "`n⚠ Some files have validation errors" -ForegroundColor Yellow
    exit 1
}
else {
    Write-Host "`n🎉 All files are valid!" -ForegroundColor Green
    exit 0
}
