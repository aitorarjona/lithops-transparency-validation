import numpy as np
import time
import random
import math
import argparse
import logging
import time
import concurrent.futures
import socket
import io


def client(server, server_port, payload_sz):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((server, server_port))
    data = bytes(payload_sz)
    t0 = time.time()
    s.send(data)
    t1 = time.time()
    s.close()
    print(t1 - t0)


def server(bind_addr, sever_port, payload):
    serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    print(f'listening on {bind_addr}:{sever_port}')
    serversocket.bind((bind_addr, sever_port))
    serversocket.listen()

    (clientsocket, address) = serversocket.accept()
    t0 = time.time()
    data = clientsocket.recv(payload)
    t1 = time.time()
    print(len(data))
    clientsocket.close()
    td = t1 - t0
    print(td)

    throughput = (payload / td) / 1_000_000
    print('Throughput = {} MB/s'.format(throughput))
    
    serversocket.shutdown(socket.SHUT_RD)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--kind', required=True, choices=['server', 'client'])
    parser.add_argument('--host', required=True, type=str)
    parser.add_argument('--port', required=True, type=int)
    parser.add_argument('--payload', type=int, default=1024)
    args = parser.parse_args()

    if args.kind == 'server':
        server(args.host, args.port, args.payload)
    elif args.kind == 'client':
        client(args.host, args.port, args.payload)
    else:
        raise Exception(args.kind)
