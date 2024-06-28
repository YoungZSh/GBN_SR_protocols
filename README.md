# GBN_SR_protocols
Using socket library to simulate GBN/SR protocol in Python， supporting file transfer in C/S mode.

##### 客户端

​	在客户端环境下，可以使用以下命令在程序文件的client目录下启动客户端程序`client.py`：

```shell
python client.py --server_ip=<server ip> --server_port=<server port> --loss_ratio=<loss ratio> --timeout=1 --win_size=4 --max_size=512
```

​	其中`--`后的参数为需要人为设置的超参，以控制协议的通讯目标和传输行为。`server_ip`与`server_port`告诉了程序传输目标的ip地址和端口号，`loss_ratio`（默认为0）控制了程序人为设置的丢包率，其余的超参也可以按照自己的意愿设置。

​	客户端程序启动后，使用者可以按照提示选择需要进行的操作，随后控制行将实时打印客户端对于文件的发送和接受日志，并在最后总结文件的传输过程信息。

##### 服务器端

​	在服务器端环境下，可以使用以下命令在程序文件的server目录下启动服务器端程序`server.py`：

```shell
python server.py --loss_ratio=<loss ratio> --timeout=1 --win_size=4 --max_size=512
```

​	与客户端类似，使用者需要指定一些超参以控制协议的通讯目标和传输行为。由于服务器端被设置为被动接受客户端指令，其只会实时打印服务器端对于文件的发送和接受日志，用户无需对其进行交互。
