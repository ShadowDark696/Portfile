# Deploy script to push index.html to GitHub
# Run in PowerShell inside C:\Portfile

git status --porcelain
git add index.html README.md
git push -u origin main
Set-Location $PSScriptRoot

# Check for git
$gitCmd = Get-Command git -ErrorAction SilentlyContinue
if (-not $gitCmd) {
    Write-Host "Git no está instalado o no está en PATH. Instala Git y vuelve a ejecutar este script." -ForegroundColor Red
    exit 1
}

Write-Host "Showing git status (if repository exists)..."
& git status --porcelain

# Initialize repo if needed
$inside = $false
try {
    & git rev-parse --is-inside-work-tree 2>$null
    if ($LASTEXITCODE -eq 0) { $inside = $true }
}
catch {
    $inside = $false
}

if (-not $inside) {
    Write-Host "Inicializando repositorio git..."
    & git init
}

# Ensure remote is set (remove if exists then add)
try {
    & git remote remove origin 2>$null
}
catch {}

Write-Host "Setting remote origin to https://github.com/ShadowDark696/Portfile.git"
& git remote add origin https://github.com/ShadowDark696/Portfile.git 2>$null

Write-Host "Adding files and committing..."
& git add index.html README.md
& git commit -m "Add portfolio index.html" --allow-empty
& git branch -M main

Write-Host "Pushing to origin/main..."
& git push -u origin main

Write-Host "Push finished. If prompted, authenticate with your GitHub credentials or PAT." -ForegroundColor Green