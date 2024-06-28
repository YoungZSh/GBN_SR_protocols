import sys
import os
import argparse

sys.path.append("..")
from protocol import ClientSocket, Packet, GBN, SR
import logging
import time
from random import random

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s')

server_ip = 'localhost'
server_port = 9999
loss_ratio = 0
timeout = 1
win_size = 4
max_size = 512

def random_drop(ratio: float):
    if random() < ratio:
        return True
    else:
        return False


def download_file(filename: str, GBN_or_SR: str = "GBN"):
    client = ClientSocket(server_ip=server_ip, server_port=server_port)
    file_received = open(filename, 'wb', buffering=0)
    if GBN_or_SR == "GBN":
        protocol = GBN(seq_num_sent=0,
                       seq_num_recv=0,
                       seq_num_expected=0,
                       timeout=timeout)
        client.send_with_UDP(
            Packet(protocol_type='GBN',
                   seq_num=protocol.seq_num_sent,
                   data=filename.encode()).packet_encode())
        protocol.seq_num_sent += 1
        logging.info(f'File {filename} download begin with GBN protocol')
        start = time.time()
        # ack_continue = 0
        while True:
            data, _ = client.receive_with_UDP(1024)
            packet = Packet.packet_decode(data)
            if random_drop(loss_ratio):
                continue  # simulate packet loss
            protocol.seq_num_recv = packet.seq_num
            if protocol.seq_num_recv == protocol.seq_num_expected:
                client.send_with_UDP(
                    Packet(seq_num=protocol.seq_num_sent,
                           ack_num=protocol.seq_num_recv,
                           ack=1,
                           protocol_type='GBN').packet_encode())
                protocol.seq_num_sent += 1
                logging.info(
                    f'Packet {protocol.seq_num_recv} received, sending ack number {protocol.seq_num_recv} to server'
                )
                if packet.fin == 1:
                    break
                else:
                    file_received.write(packet.data)
                protocol.seq_num_expected += 1
            else:
                logging.info(
                    f'Received packet {protocol.seq_num_recv} is not expected, waiting for {protocol.seq_num_expected}'
                )
        end = time.time()
        file_size = os.path.getsize(filename)
        logging.info(
            f'File {filename} download complete with GBN protocol in {end-start} seconds, average speed {file_size/(end-start)} B/s'
        )
    elif GBN_or_SR == "SR":
        protocol = SR(seq_num_sent=0,
                      seq_num_recv=0,
                      seq_num_expected=0,
                      timeout=timeout)
        client.send_with_UDP(
            Packet(protocol_type='SR',
                   seq_num=protocol.seq_num_sent,
                   data=filename.encode()).packet_encode())
        protocol.seq_num_sent += 1
        logging.info(f'File {filename} download begin with SR protocol')
        start = time.time()
        flag = 0
        while True:
            data, _ = client.receive_with_UDP(1024)
            packet = Packet.packet_decode(data)
            if random_drop(loss_ratio):
                continue  # simulate packet loss
            protocol.seq_num_recv = packet.seq_num
            if protocol.seq_num_recv >= protocol.seq_num_expected:
                # logging.info(
                #     f'Expecting receiving packet {protocol.seq_num_expected}')
                ack_num = protocol.seq_num_recv
                client.send_with_UDP(
                    Packet(seq_num=protocol.seq_num_sent,
                           ack_num=ack_num,
                           ack=1,
                           protocol_type='SR').packet_encode())
                protocol.seq_num_sent += 1
                logging.info(
                    f'Packet {protocol.seq_num_recv} received, sending ack number {ack_num} to server'
                )
                if protocol.seq_num_recv == protocol.seq_num_expected:
                    if packet.fin == 1:
                        break
                    else:
                        file_received.write(packet.data)
                        protocol.seq_num_expected += 1
                        while protocol.seq_num_expected in protocol.sr_buffer_index:
                            file_received.write(protocol.sr_buffer[
                                protocol.sr_buffer_index.index(
                                    protocol.seq_num_expected)])
                            if protocol.seq_num_expected == protocol.fin_num:
                                flag = 1
                                break
                            protocol.seq_num_expected += 1
                        if flag == 1:
                            break
                elif protocol.seq_num_recv > protocol.seq_num_expected:
                    protocol.sr_buffer.append(packet.data)
                    protocol.sr_buffer_index.append(protocol.seq_num_recv)
                    if packet.fin == 1:
                        protocol.fin_num = protocol.seq_num_recv
                    logging.info(
                        f'Received packet {protocol.seq_num_recv} is not in order, waiting for {protocol.seq_num_expected}'
                    )
        end = time.time()
        file_size = os.path.getsize(filename)
        logging.info(
            f'File {filename} download complete with SR protocol in {end-start} seconds, average speed {file_size/(end-start)} B/s'
        )
    else:
        logging.error(f'Invalid protocol {GBN_or_SR}')


def upload_file(filename: str, GBN_or_SR: str = "GBN") -> bool:
    client = ClientSocket(server_ip=server_ip, server_port=server_port)
    loss_cnt = 0
    if GBN_or_SR == "GBN":
        protocol = GBN(seq_num_sent=0,
                       seq_num_recv=0,
                       seq_num_expected=0,
                       win_size=win_size,
                       timeout=timeout)
        client.send_with_UDP(
            Packet(protocol_type='GBN',
                   seq_num=protocol.seq_num_sent,
                   data=filename.encode()).packet_encode())
        # protocol.seq_num_sent += 1
        logging.info(f'File {filename} upload begin with GBN protocol')
        # client_TCP = ClientSocket(server_ip='localhost', server_port=9998)
        # client_TCP.socket.bind(('localhost', 9997))
        # client_TCP.set_TCP_connection()
        # client_TCP.start_TCP_connection()
        # logging.info(f"TCP connection established with server {client_TCP.server_ip}:{client_TCP.server_port}")
        # protocol = GBN(base=0,
        #                seq_num_sent=0,
        #                seq_num_recv=0,
        #                seq_num_expected=0,
        #                win_size=4,
        #                timeout=1,
        #                max_size=512)
        packets = protocol.file_to_packets(filename)
        logging.info(f"Sending {len(packets)} packets to server...")
        start = time.time()
        while True:
            while protocol.seq_num_sent < protocol.base + protocol.win_size and protocol.seq_num_sent < len(
                    packets):
                packets[protocol.seq_num_sent].seq_num = protocol.seq_num_sent
                client.send_with_UDP(
                    packets[protocol.seq_num_sent].packet_encode())
                logging.info(f"Sending packet {protocol.seq_num_sent}")
                protocol.seq_num_sent += 1
            client.set_timeout(protocol.timeout)
            try:
                data, _ = client.receive_with_UDP(1024)
                packet = Packet.packet_decode(data)
                logging.info(f'Receive ack {packet.ack_num}')
                protocol.base = packet.ack_num + 1
            except:
                logging.info("Timeout")
                loss_cnt += 1
                protocol.seq_num_sent = protocol.base
            if protocol.base == len(packets):
                break
        end = time.time()
        logging.info(
            f"File sent successfully in {end-start} seconds, with {(loss_cnt/len(packets))*100}% packet loss rate"
        )
        # client_TCP.close_TCP_connection()
    elif GBN_or_SR == "SR":
        protocol = SR(base=0,
                      seq_num_sent=0,
                      seq_num_recv=0,
                      seq_num_expected=0,
                      win_size=win_size,
                      timeout=timeout,
                      max_size=max_size,
                      ack_list=[])
        client.send_with_UDP(
            Packet(protocol_type='SR',
                   seq_num=protocol.seq_num_sent,
                   data=filename.encode()).packet_encode())
        # protocol.seq_num_sent += 1
        logging.info(f'File {filename} upload begin with SR protocol')
        packets = protocol.file_to_packets(filename)
        logging.info(f"Sending {len(packets)} packets to server...")
        start = time.time()
        while True:
            while protocol.seq_num_sent < protocol.base + protocol.win_size and protocol.seq_num_sent < len(
                    packets):
                if protocol.seq_num_sent not in protocol.ack_list:
                    packets[
                        protocol.seq_num_sent].seq_num = protocol.seq_num_sent
                    client.send_with_UDP(
                        packets[protocol.seq_num_sent].packet_encode())
                    logging.info(f"Sending packet {protocol.seq_num_sent}")
                protocol.seq_num_sent += 1
            client.set_timeout(protocol.timeout)
            try:
                data, _ = client.receive_with_UDP(1024)
                packet = Packet.packet_decode(data)
                logging.info(f'Receive ack {packet.ack_num}')
                protocol.ack_list.append(packet.ack_num)
                if protocol.base == packet.ack_num:
                    protocol.base += 1
                    while protocol.base in protocol.ack_list:
                        protocol.base += 1
            except:
                logging.info("Timeout")
                loss_cnt += 1
                protocol.seq_num_sent = protocol.base
            if protocol.base == len(packets):
                break
        end = time.time()
        logging.info(
            f"File sent successfully in {end-start} seconds, with {loss_cnt/len(packets)*100}% packet loss rate")
    else:
        logging.error(f'Invalid protocol {GBN_or_SR}')

server_file_list = []

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--server_ip',  type=str, default = 'localhost')
    parser.add_argument('--server_port', type=int, default = 9999)
    parser.add_argument('--loss_ratio', type=float, default = 0)
    parser.add_argument('--timeout', type=float, default = 1)
    parser.add_argument('--win_size', type=int, default = 4)
    parser.add_argument('--max_size', type=int, default = 512)
    args = parser.parse_args()
    server_ip = args.server_ip
    server_port = args.server_port
    loss_ratio = args.loss_ratio
    timeout = args.timeout
    win_size = args.win_size
    max_size = args.max_size

    while True:
        choice = input(f"Please select your operation:\n 1. Download file\n 2. Upload file\n 3. Exit\n ")
        if choice == '1':
            print("File list in server:")
            for i, filename in enumerate(server_file_list):
                print(f"{i+1}. {filename}")
            filename = input("Enter filename to download:\n ")
            while filename not in server_file_list:
                filename = input("Invalid filename, please enter again:\n ")
            protocol = input("Enter protocol to use (GBN/SR):\n ")
            download_file(filename, protocol)
        elif choice == '2':
            current_directory = os.getcwd()
            filename = input("Enter filename to upload:\n ")
            if filename in server_file_list:
                print("File already exists in server.")
                continue
            file_path = os.path.join(current_directory, filename)
            if os.path.exists(file_path):
                protocol = input("Enter protocol to use (GBN/SR):\n ")
                upload_file(filename, protocol)
                server_file_list.append(filename)
            else:
                print("File does not exist.")
        elif choice == '3':
            break
        else:
            print("Invalid choice")

    #download_file('2.jpg', 'SR')
    # upload_file('test.jpg', 'SR')
