$WshShell = New-Object -ComObject WScript.Shell
$DesktopPath = [Environment]::GetFolderPath("Desktop")
$Shortcut = $WshShell.CreateShortcut("$DesktopPath\HEMN SYSTEM.lnk")
$Shortcut.TargetPath = "C:\Users\Junior T.I\.gemini\antigravity\scratch\data_analysis\dist\HEMN SYSTEM\HEMN SYSTEM.exe"
$Shortcut.WorkingDirectory = 'C:\Users\Junior T.I\.gemini\antigravity\scratch\data_analysis\dist\HEMN SYSTEM'
$Shortcut.Description = "HEMN SYSTEM"
$Shortcut.Save()
