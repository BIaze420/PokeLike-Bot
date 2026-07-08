$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ProjectRoot

function Invoke-Checked {
    param(
        [Parameter(Mandatory = $true)]
        [ScriptBlock] $Command
    )
    & $Command
    if ($LASTEXITCODE -ne 0) {
        throw "Command failed with exit code $LASTEXITCODE"
    }
}

if (-not (Test-Path ".venv")) {
    Invoke-Checked { py -m venv .venv }
}

Invoke-Checked { & ".\.venv\Scripts\python.exe" -m pip install --upgrade pip }
Invoke-Checked { & ".\.venv\Scripts\python.exe" -m pip install -r requirements.txt }

if (Test-Path "build\PokeLikeBot") {
    & attrib -R "build\PokeLikeBot\*" /S /D
}

Invoke-Checked { & ".\.venv\Scripts\python.exe" -m PyInstaller --clean PokeLikeBot.spec }

Write-Host ""
Write-Host "Built executable:"
Write-Host "  $ProjectRoot\dist\PokeLike Bot.exe"
