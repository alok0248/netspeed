# PowerShell script to build MSI using WiX Toolset
# Prerequisite: WiX installed and added to PATH (candle.exe, light.exe)

param(
    [string]$Version = "1.0.0",
    [string]$SourceExe = "..\..\..\dist\v$Version\windows\NetSpeed.exe",
    [string]$IconPath = "..\..\..\dist\v$Version\windows\NetSpeed.ico",
    [string]$OutputDir = "..\..\..\dist\v$Version\windows"
)

# Ensure output directory exists
if (-not (Test-Path $OutputDir)) {
    New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null
}

# Paths
$wxsFile = "netspeed.wxs"
$wixobj = "netspeed.wixobj"
$msiFile = "NetSpeed-$Version.msi"

# Update the .wxs file paths if needed (optional, assuming placeholders are correct)
# Build MSI
Write-Host "Compiling WiX source..."
$candlePath = 'C:\Program Files (x86)\WiX Toolset v3.11\bin\candle.exe'
if (-not (Test-Path $candlePath)) { Write-Error "candle.exe not found at $candlePath"; exit 1 }
$candleResult = & "$candlePath" $wxsFile -out $wixobj
if ($LASTEXITCODE -ne 0) {
    Write-Error "candle failed with exit code $LASTEXITCODE"
    exit $LASTEXITCODE
}

Write-Host "Linking MSI..."
$lightResult = light $wixobj -o $OutputDir\$msiFile
if ($LASTEXITCODE -ne 0) {
    Write-Error "light failed with exit code $LASTEXITCODE"
    exit $LASTEXITCODE
}

Write-Host "MSI built successfully: $OutputDir\$msiFile"
