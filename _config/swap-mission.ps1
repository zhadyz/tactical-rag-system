# ============================================================
# TACTICAL RAG SYSTEM - MISSION SWAP SCRIPT
# ============================================================

# Display DoD Warning Banner
Write-Host ""
Write-Host "***********************************************************************" -ForegroundColor Red
Write-Host "                         WARNING NOTICE" -ForegroundColor Red
Write-Host "***********************************************************************" -ForegroundColor Yellow
Write-Host ""
Write-Host "You are accessing a U.S. Government (USG) Information System (IS) that" -ForegroundColor White
Write-Host "is provided for USG-authorized use only." -ForegroundColor White
Write-Host ""
Write-Host "By using this IS, you consent to USG monitoring and inspection." -ForegroundColor White
Write-Host "Communications are not private and may be disclosed for any" -ForegroundColor White
Write-Host "USG-authorized purpose." -ForegroundColor White
Write-Host ""
Write-Host "***********************************************************************" -ForegroundColor Red
Write-Host ""
$consent = Read-Host "Type 'I AGREE' to continue"
if ($consent -ne "I AGREE") {
    Write-Host "Access denied. Exiting..." -ForegroundColor Red
    exit
}
Write-Host ""

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "    MISSION DOCUMENT SWAP" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "This script will:" -ForegroundColor Yellow
Write-Host "1. Stop the current system" -ForegroundColor Yellow
Write-Host "2. Clear the document database" -ForegroundColor Yellow
Write-Host "3. Allow you to add new mission documents" -ForegroundColor Yellow
Write-Host "4. Re-index and restart the system" -ForegroundColor Yellow
Write-Host ""

$confirm = Read-Host "Continue? (y/n)"
if ($confirm -ne "y") {
    Write-Host "Cancelled" -ForegroundColor Red
    exit
}

Write-Host ""
Write-Host "Stopping system..." -ForegroundColor Yellow
docker-compose down

Write-Host "Clearing document database..." -ForegroundColor Yellow
if (Test-Path "chroma_db") {
    Remove-Item -Recurse -Force chroma_db
    Write-Host "Database cleared" -ForegroundColor Green
} else {
    Write-Host "No database to clear" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host "    SYSTEM READY FOR NEW MISSION" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""
Write-Host "NEXT STEPS:" -ForegroundColor Cyan
Write-Host "1. Remove old documents from the documents/ folder" -ForegroundColor White
Write-Host "2. Add new mission documents to the documents/ folder" -ForegroundColor White
Write-Host "3. Run deploy.ps1 to start the system" -ForegroundColor White
Write-Host ""
Write-Host "Opening documents folder..." -ForegroundColor Yellow
$documentsPath = Join-Path -Path (Get-Location) -ChildPath "documents"
Start-Process explorer.exe -ArgumentList $documentsPath

Write-Host ""
Read-Host "Press Enter to exit"