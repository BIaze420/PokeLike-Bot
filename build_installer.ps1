$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ProjectRoot

if (-not (Test-Path "dist\PokeLike Bot.exe")) {
    .\build_exe.ps1
}

$iscc = Get-Command ISCC.exe -ErrorAction SilentlyContinue
if (-not $iscc) {
    $candidatePaths = @(
        "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
        "$env:ProgramFiles\Inno Setup 6\ISCC.exe",
        "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe"
    )
    foreach ($candidate in $candidatePaths) {
        if ($candidate -and (Test-Path $candidate)) {
            $iscc = Get-Item $candidate
            break
        }
    }
}
if (-not $iscc) {
    throw "Inno Setup Compiler (ISCC.exe) was not found. Install Inno Setup, then run this script again."
}

& $iscc.FullName "installer.iss"

Write-Host ""
Write-Host "Built installer:"
Write-Host "  $ProjectRoot\PokeLikeBotInstaller\PokeLikeBotSetup.exe"
