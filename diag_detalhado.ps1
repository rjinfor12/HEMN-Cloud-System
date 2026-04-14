$processes = Get-Process | Select-Object Name, 
    @{Name='RAM_Fisica_MB';Expression={[math]::Round($_.WorkingSet64 / 1MB, 2)}}, 
    @{Name='RAM_Privada_MB';Expression={[math]::Round($_.PrivateMemorySize64 / 1MB, 2)}}, 
    Description | 
    Sort-Object RAM_Fisica_MB -Descending | 
    Select-Object -First 30

$processes | Format-Table -AutoSize

$os = Get-CimInstance Win32_OperatingSystem
Write-Host "`n--- Resumo de Memória do Sistema ---"
Write-Host "Total Visível: $([math]::Round($os.TotalVisibleMemorySize / 1KB, 2)) MB"
Write-Host "Física Livre: $([math]::Round($os.FreePhysicalMemory / 1KB, 2)) MB"
Write-Host "Pool Não Paginável: $([math]::Round($os.MaxProcessMemorySize / 1MB, 2)) MB" # Placeholder for pool info
Write-Host "Em Cache (Standby): Ver Gerenciador de Tarefas"
