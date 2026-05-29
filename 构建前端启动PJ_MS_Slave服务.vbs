Set ws = CreateObject("WScript.Shell")

' 第1步：构建前端（隐藏窗口，等待构建完成）
ws.CurrentDirectory = "E:\PJ_MS_Slave\frontend"
ws.Run "cmd /c npm run build", 0, True

' 第2步：启动后端（隐藏窗口，后台运行）
ws.CurrentDirectory = "E:\PJ_MS_Slave\backend"
ws.Run "cmd /c python manage.py runserver 0.0.0.0:8000", 0, False

Set ws = Nothing