$PopupPath = '\"pythonw.exe\" \"C:\Users\Junior T.I\scratch\data_analysis\hemn_popup.py\"'
$UpdaterPath = '\"pythonw.exe\" \"C:\Users\Junior T.I\scratch\data_analysis\hemn_updater.py\"'

# Popups (Dia 13)
schtasks /create /f /tn "HEMN_System_Alerts_D13_10h" /tr $PopupPath /sc monthly /d 13 /st 10:00 
schtasks /create /f /tn "HEMN_System_Alerts_D13_14h" /tr $PopupPath /sc monthly /d 13 /st 14:00 
schtasks /create /f /tn "HEMN_System_Alerts_D13_18h" /tr $PopupPath /sc monthly /d 13 /st 18:00 

# Popups (Dia 28)
schtasks /create /f /tn "HEMN_System_Alerts_D28_10h" /tr $PopupPath /sc monthly /d 28 /st 10:00 
schtasks /create /f /tn "HEMN_System_Alerts_D28_14h" /tr $PopupPath /sc monthly /d 28 /st 14:00 
schtasks /create /f /tn "HEMN_System_Alerts_D28_18h" /tr $PopupPath /sc monthly /d 28 /st 18:00 

# Updater Invisível (19h30)
schtasks /create /f /tn "HEMN_System_Updater_Cron_D13" /tr $UpdaterPath /sc monthly /d 13 /st 19:30 
schtasks /create /f /tn "HEMN_System_Updater_Cron_D28" /tr $UpdaterPath /sc monthly /d 28 /st 19:30 

Write-Host "Todas as 8 tarefas agendadas exclusivas foram fixadas com exatidão matemática no Agendador V2 do Windows via SCHTASKS."
