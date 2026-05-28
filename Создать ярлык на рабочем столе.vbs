Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FilesystemObject")

' Определяем рабочий стол
desktop = WshShell.SpecialFolders("Desktop")

' Путь к bat-файлу
batPath = fso.GetParentFolderName(WScript.ScriptFullName) & "\😂 Анекдот в тему.bat"

' Создаём ярлык
Set shortcut = WshShell.CreateShortcut(desktop & "\😂 Анекдот в тему.lnk")
shortcut.TargetPath = batPath
shortcut.WorkingDirectory = fso.GetParentFolderName(batPath)
shortcut.Description = "Анекдот в тему — шутки через микрофон"
shortcut.IconLocation = "C:\Windows\System32\shell32.dll,13"  '笑脸
shortcut.Save

MsgBox "✅ Ярлык создан на рабочем столе!", vbInformation, "Анекдот в тему"
