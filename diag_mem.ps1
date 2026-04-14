$processes = Get-Process | Sort-Object WorkingSet64 -Descending | Select-Object Name, @{Name='RAM_MB';Expression={[math]::Round($_.WorkingSet64 / 1MB, 2)}}, @{Name='CPU_Time';Expression={$_.CPU}} -First 20
$processes | Format-Table -AutoSize
Get-CimInstance Win32_OperatingSystem | Select-Object TotalVisibleMemorySize, FreePhysicalMemory, TotalVirtualMemorySize, FreeVirtualMemory | Format-List
