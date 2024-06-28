#!/bin/bash
# 启动server.py
gnome-terminal --working-directory="$PWD/server" -e 'python server.py' &
# 等待一定时间，确保server.py已经启动
sleep 2
# 启动client.py
gnome-terminal --working-directory="$PWD/client" -e 'python client.py' &
wait
