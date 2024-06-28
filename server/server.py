import sys
import os
import argparse

sys.path.append("..")
from protocol import ServerSocket, GBN, Packet, SR
import logging
import time
from random import random

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s')

loss_ratio = 0
timeout = 1
win_size = 4
max_size = 512

def random_drop(ratio: float):
    if random() < ratio:
        return True
    else:
        return False


def send_file(init_packet: Packet, server: ServerSocket):
    loss_cnt = 0
    if init_packet.protocol_type == 'GBN':
        protocol = GBN(base=0,
                       seq_num_sent=0,
                       seq_num_recv=0,
                       seq_num_expected=0,
                       win_size=win_size,
                       timeout=timeout,
                       max_size=max_size)
        filename = init_packet.data.decode()
        packets = protocol.file_to_packets(filename)
        logging.info(f"Sending {len(packets)} packets to client...")
        start = time.time()
        while True:
            while protocol.seq_num_sent < protocol.base + protocol.win_size and protocol.seq_num_sent < len(
                    packets):
                packets[protocol.seq_num_sent].seq_num = protocol.seq_num_sent
                server.send_with_UDP(
                    packets[protocol.seq_num_sent].packet_encode())
                logging.info(f"Sending packet {protocol.seq_num_sent}")
                protocol.seq_num_sent += 1
            server.set_timeout(protocol.timeout)
            try:
                data, _ = server.receive_with_UDP(1024)
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
    else:
        protocol = SR(base=0,
                      seq_num_sent=0,
                      seq_num_recv=0,
                      seq_num_expected=0,
                      win_size=win_size,
                      timeout=timeout,
                      max_size=max_size,
                      ack_list=[])
        logging.info(f"filename: {init_packet.data.decode()}")
        packets = protocol.file_to_packets(init_packet.data.decode())
        filename = init_packet.data.decode()
        logging.info(f"Sending {len(packets)} packets to client...")
        start = time.time()
        while True:
            while protocol.seq_num_sent < protocol.base + protocol.win_size and protocol.seq_num_sent < len(
                    packets):
                if protocol.seq_num_sent not in protocol.ack_list:
                    packets[
                        protocol.seq_num_sent].seq_num = protocol.seq_num_sent
                    server.send_with_UDP(
                        packets[protocol.seq_num_sent].packet_encode())
                    logging.info(f"Sending packet {protocol.seq_num_sent}")
                protocol.seq_num_sent += 1
            server.set_timeout(protocol.timeout)
            try:
                data, _ = server.receive_with_UDP(1024)
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
            f"File sent successfully in {end-start} seconds, with {(loss_cnt/len(packets))*100}% packet loss rate"
        )


def receive_file(init_packet: Packet, server: ServerSocket):
    # server_TCP = ServerSocket(bind_ip='127.0.0.1', bind_port=9998)
    # server_TCP.set_TCP_connection()
    # if server_TCP.accept_TCP_connection():
    # logging.info(f"Receiving file from client {server.client_ip}:{server.client_port}")
    file_received = open(init_packet.data.decode(), 'wb', buffering=0)
    if init_packet.protocol_type == 'GBN':
        protocol = GBN(seq_num_sent=0,
                       seq_num_recv=0,
                       seq_num_expected=0,
                       timeout=timeout)
        start = time.time()
        while True:
            data, _ = server.receive_with_UDP(1024)
            # logging.debug(f"Received data: {data}")
            packet = Packet.packet_decode(data)
            if random_drop(loss_ratio):
                continue  # simulate packet loss
            protocol.seq_num_recv = packet.seq_num
            if protocol.seq_num_recv == protocol.seq_num_expected:
                server.send_with_UDP(
                    Packet(seq_num=protocol.seq_num_sent,
                           ack_num=protocol.seq_num_recv,
                           ack=1,
                           protocol_type='GBN').packet_encode())
                protocol.seq_num_sent += 1
                logging.info(
                    f'Packet {protocol.seq_num_recv} received, sending ack number {protocol.seq_num_recv} to client'
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
        file_size = os.path.getsize(init_packet.data.decode())
        #server_TCP.close_TCP_connection()
        logging.info(
            f'File {init_packet.data.decode()} download complete with GBN protocol in {end-start} seconds, average speed {file_size/(end-start)} B/s'
        )
    # else:
    #     logging.info("Connection failed")
    else:
        protocol = SR(seq_num_sent=0,
                      seq_num_recv=0,
                      seq_num_expected=0,
                      timeout=timeout)
        start = time.time()
        flag = 0
        while True:
            data, _ = server.receive_with_UDP(1024)
            packet = Packet.packet_decode(data)
            if random_drop(loss_ratio):
                continue  # simulate packet loss
            protocol.seq_num_recv = packet.seq_num
            if protocol.seq_num_recv >= protocol.seq_num_expected:
                # logging.info(
                #     f'Expecting receiving packet {protocol.seq_num_expected}')
                ack_num = protocol.seq_num_recv
                server.send_with_UDP(
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
        file_size = os.path.getsize(init_packet.data.decode())
        logging.info(
            f'File {init_packet.data.decode()} download complete with SR protocol in {end-start} seconds, average speed {file_size/(end-start)} B/s'
        )
    # logging.debug(f"end")


file_list = []

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--loss_ratio', type=float, default = 0)
    parser.add_argument('--timeout', type=float, default = 1)
    parser.add_argument('--win_size', type=int, default = 4)
    parser.add_argument('--max_size', type=int, default = 512)
    args = parser.parse_args()
    loss_ratio = args.loss_ratio
    timeout = args.timeout
    win_size = args.win_size
    max_size = args.max_size
    server = ServerSocket(bind_ip='0.0.0.0', bind_port=9999)
    while True:
        logging.info("Waiting for client to request...")
        try:
            data, addr = server.receive_with_UDP(1024)
            server.client_ip = addr[0]
            server.client_port = addr[1]
            logging.info(
                f"Received request from {server.client_ip}:{server.client_port}"
            )
            packet = Packet.packet_decode(data)
            # logging.info(packet.data.decode())
            # logging.debug(packet.data.decode() in file_list)
            if packet.data.decode() in file_list:
                logging.info("inin")
                send_file(packet, server)
            else:
                receive_file(packet, server)
                file_list.append(packet.data.decode())
                logging.info(f"File list: {file_list}")
        except TimeoutError:
            pass
        except Exception as e:
            logging.error(e)
