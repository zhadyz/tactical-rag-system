# fix-line-endings.ps1 - Run this anytime to fix corrupted .sh files
Get-ChildItem -Path . -Filter "*.sh" -Recurse | ForEach-Object {
    $bytes = [System.IO.File]::ReadAllBytes($_.FullName)
    if ($bytes -contains 0x0D) {
        $cleanBytes = $bytes | Where-Object { $_ -ne 0x0D }
        [System.IO.File]::WriteAllBytes($_.FullName, $cleanBytes)
        Write-Host "Fixed: $($_.Name)" -ForegroundColor Green
    } else {
        Write-Host "OK: $($_.Name)" -ForegroundColor Gray
    }
}