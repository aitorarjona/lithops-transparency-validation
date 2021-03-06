import time
import struct
import argparse
import time
import socket
import io


def client(server, server_port, payload_sz):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((server, server_port))
    length = struct.pack('>Q', payload_sz)
    s.sendall(length)
    data = bytes(payload_sz)
    t0 = time.time()
    s.sendall(data)
    t1 = time.time()
    s.shutdown(socket.SHUT_WR)
    s.close()

    td = t1 - t0
    print(td)
    throughput = (payload_sz / td) / 1_000_000
    print('Throughput = {} MB/s'.format(throughput))

    return {'throughput': throughput, 'td': td}


def server(bind_addr, sever_port):
    serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    print(f'listening on {bind_addr}:{sever_port}')
    serversocket.bind((bind_addr, sever_port))
    serversocket.listen(1)

    buff = io.BytesIO()
    (clientsocket, address) = serversocket.accept()
    try:
        bs = clientsocket.recv(8)
        (length,) = struct.unpack('>Q', bs)
        print(length)
        data_recv = 0
        t0 = time.time()
        while data_recv < length:
            to_read = length - data_recv
            print(to_read)
            data = clientsocket.recv(length if to_read > length else to_read)
            data_recv += len(data)
            buff.write(data)
    finally:
        t1 = time.time()
        clientsocket.shutdown(socket.SHUT_WR)
        clientsocket.close()
    print(buff.tell())
    
    td = t1 - t0
    print(td)
    throughput = (length / td) / 1_000_000
    print('Throughput = {} MB/s'.format(throughput))

    serversocket.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--kind', required=True, choices=['server', 'client', 'lithops-client'])
    parser.add_argument('--host', required=True, type=str)
    parser.add_argument('--port', required=True, type=int)
    parser.add_argument('--payload', type=int, default=1024)
    args = parser.parse_args()

    if args.kind == 'server':
        server(args.host, args.port)
    elif args.kind == 'client':
        client(args.host, args.port, args.payload)
    elif args.kind == 'lithops-client':
        import lithops
        fexec = lithops.FunctionExecutor()
        fexec.call_async(client, (args.host, args.port, args.payload))
        res = fexec.get_result()
        print(res)
    else:
        raise Exception(args.kind)
