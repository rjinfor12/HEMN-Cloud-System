$WshShell = New-Object -ComObject WScript.Shell
$DesktopPath = [Environment]::GetFolderPath('Desktop')
$Shortcut = $WshShell.CreateShortcut("$DesktopPath\TMM Premium.lnk")

# Caminho absoluto para a versão NOVO com Sidebar
$Shortcut.TargetPath = "C:\Users\Junior T.I\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\pythonw.exe"
$Shortcut.Arguments = '"C:\Users\Junior T.I\scratch\data_analysis\main_gui.py"'
$Shortcut.WorkingDirectory = "C:\Users\Junior T.I\scratch\data_analysis"
$Shortcut.IconLocation = "C:\Users\Junior T.I\scratch\data_analysis\logo.ico"
$Shortcut.Description = "Sistema TMM Premium - Ti Mailling Mayk"
$Shortcut.Save()
