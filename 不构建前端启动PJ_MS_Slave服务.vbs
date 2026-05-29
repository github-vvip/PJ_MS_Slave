Set ws = CreateObject("WScript.Shell")
' 设置工作目录（等同于 cd 命令）
ws.CurrentDirectory = "E:\PJ_MS_Slave\backend"
' 启动服务，0 表示隐藏窗口，False 表示不阻塞脚本
ws.Run "python manage.py runserver 0.0.0.0:8000", 0, False
Set ws = Nothing