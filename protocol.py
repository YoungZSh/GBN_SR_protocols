import socket
from typing import Any

class ClientSocket:

    def __init__(self,
                 server_ip: str = 'localhost',
                 server_port: int = 9999) -> None:
        self.server_ip = server_ip
        self.server_port = server_port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def send_with_UDP(self, data: Any) -> None:
        self.socket.sendto(data, (self.server_ip, self.server_port))

    def receive_with_UDP(self, buffer_size: int = 1024) -> bytes:
        data, address = self.socket.recvfrom(buffer_size)
        return data, address
    
    def set_timeout(self, timeout: int) -> None:
        self.socket.settimeout(timeout)

    def set_TCP_connection(self) -> None:
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def start_TCP_connection(self) -> None:
        self.socket.connect((self.server_ip, self.server_port))

    def close_TCP_connection(self) -> None:
        self.socket.close()

    def send_with_TCP(self, data: Any) -> None:
        self.socket.send(data)

    def receive_with_TCP(self, buffer_size: int = 1024) -> bytes:
        data = self.socket.recv(buffer_size)
        return data
    
    def set_TCP_timeout(self, timeout: int) -> None:
        self.socket.settimeout(timeout)


class ServerSocket:

    def __init__(self,
                 bind_ip: str = '0.0.0.0',
                 bind_port: int = 9999) -> None:
        self.bind_ip = bind_ip
        self.bind_port = bind_port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.client_ip = None
        self.client_port = None
        self.connection = None
        self.set_bind()

    def set_bind(self) -> None:
        self.socket.bind((self.bind_ip, self.bind_port))

    def send_with_UDP(self, data: Any) -> None:
        self.socket.sendto(data, (self.client_ip, self.client_port))

    def receive_with_UDP(self, buffer_size: int = 1024) -> bytes:
        data, address = self.socket.recvfrom(buffer_size)
        return data, address

    def set_timeout(self, timeout: int) -> None:
        self.socket.settimeout(timeout)

    def set_TCP_connection(self) -> None:
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.set_bind()
        self.socket.listen(1)
    
    def accept_TCP_connection(self) -> bool:
        try:
            self.connection, (self.client_ip, self.client_port) = self.socket.accept()
            print(self.connection)
            return True
        except:
            return False
        
    def close_TCP_connection(self) -> None:
        self.connection.close()

    def send_with_TCP(self, data: Any) -> None:
        self.connection.send(data)

    def receive_with_TCP(self, buffer_size: int = 1024) -> bytes:
        data = self.connection.recv(buffer_size)
        return data



class Packet:

    def __init__(self,
                 protocol_type: str = 'GBN',
                 seq_num: int = 0,
                 ack_num: int = 0,
                 ack: int = 0,
                 fin: int = 0,
                 data: bytes = b'') -> None:
        self.protocol_type = protocol_type
        self.seq_num = seq_num
        self.ack_num = ack_num
        self.ack = ack
        self.fin = fin
        self.data = data
        self.length = len(self.data)

    def packet_encode(self) -> str:
        self.length = len(self.data)
        return (str(self.seq_num).zfill(8) + str(self.ack_num).zfill(8) +
                str(self.protocol_type).zfill(3) + str(self.ack).zfill(1) +
                str(self.fin).zfill(1) +
                str(self.length).zfill(4)).encode() + self.data

    @staticmethod
    def packet_decode(data: bytes) -> 'Packet':
        packet = Packet()
        packet.seq_num = str_to_Int(data[0:8].decode())
        packet.ack_num = str_to_Int(data[8:16].decode())
        packet.protocol_type = data[16:19].decode()
        packet.ack = str_to_Int(data[19:20].decode())
        packet.fin = str_to_Int(data[20:21].decode())
        packet.length = str_to_Int(data[21:25].decode())
        packet.data = data[25:len(data)]
        return packet

    def set_seq_num(self, seq_num: int) -> None:
        self.seq_num = seq_num

    def set_protocol_type(self, protocol_type: str) -> None:
        self.protocol_type = protocol_type

    def set_win_size(self, win_size: int) -> None:
        self.win_size = win_size


class GBN:

    def __init__(self,
                 base: int = 0,
                 seq_num_sent: int = 0,
                 seq_num_recv: int = 0,
                 seq_num_expected: int = 0,
                 timeout: int = 1,
                 max_size: int = 512,
                 win_size: int = 4) -> None:
        self.base = base
        self.seq_num_sent = seq_num_sent
        self.seq_num_recv = seq_num_recv
        self.seq_num_expected = seq_num_expected
        self.timeout = timeout
        self.max_size = max_size
        self.win_size = win_size

    def file_to_packets(self, file_path: str) -> list:
        packets = []
        with open(file_path, 'rb') as f:
            while True:
                data = f.read(self.max_size)
                if not data:
                    break
                packets.append(Packet(protocol_type='GBN', data=data))
        packets.append(Packet(protocol_type='GBN', fin=1))
        return packets
    
class SR:

    def __init__(self,
                 base: int = 0,
                 seq_num_sent: int = 0,
                 seq_num_recv: int = 0,
                 seq_num_expected: int = 0,
                 timeout: int = 1,
                 max_size: int = 512,
                 win_size: int = 4,
                 sr_buffer: list = [],
                 sr_buffer_index: list = [],
                 fin_num: int = -1,
                 ack_list: list = []) -> None:
        self.base = base
        self.seq_num_sent = seq_num_sent
        self.seq_num_recv = seq_num_recv
        self.seq_num_expected = seq_num_expected
        self.timeout = timeout
        self.max_size = max_size
        self.win_size = win_size
        self.sr_buffer = sr_buffer
        self.sr_buffer_index = sr_buffer_index 
        self.fin_num = fin_num
        self.ack_list = ack_list

    def file_to_packets(self, file_path: str) -> list:
        packets = []
        with open(file_path, 'rb') as f:
            while True:
                data = f.read(self.max_size)
                if not data:
                    break
                packets.append(Packet(protocol_type='GBN', data=data))
        packets.append(Packet(protocol_type='GBN', fin=1))
        return packets


def str_to_Int(str: str) -> int:
    num = 0
    length = len(str)
    for i in range(len(str)):
        num += int(str[i]) * 10**(length - i - 1)
    return num
