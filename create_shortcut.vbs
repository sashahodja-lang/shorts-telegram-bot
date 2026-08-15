Set WshShell = CreateObject("WScript.Shell")
strDesktop = WshShell.SpecialFolders("Desktop")
Set fso = CreateObject("Scripting.FileSystemObject")
strDir = fso.GetParentFolderName(WScript.ScriptFullName)

Set oShellLink = WshShell.CreateShortcut(strDesktop & "\Запуск Telegram Shorts Бота.lnk")
oShellLink.TargetPath = "wscript.exe"
oShellLink.Arguments = """" & strDir & "\run_bot_silent.vbs"""
oShellLink.WorkingDirectory = strDir
oShellLink.WindowStyle = 1
oShellLink.Description = "Запуск Telegram-бота для скачивания Shorts и Видео"
oShellLink.IconLocation = strDir & "\bot_icon.ico"
oShellLink.Save

WScript.Echo "Telegram Bot shortcut created successfully!"
