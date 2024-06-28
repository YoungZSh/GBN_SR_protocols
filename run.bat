@echo off
set LOSS_RATIO=0.01
REM 启动server.py
start cmd /k "cd server && python server.py --loss_ratio=%LOSS_RATIO% --timeout=1 --win_size=4 --max_size=512"
REM 等待一定时间，确保server.py已经启动
timeout /t 1
REM 启动client.py
start cmd /k "cd client && python client.py --server_ip=127.0.0.1 --server_port=9999 --loss_ratio=%LOSS_RATIO% --timeout=1 --win_size=4 --max_size=512"