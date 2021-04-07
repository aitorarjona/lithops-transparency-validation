import time
import sys
import argparse
import logging


def get_data(n_chars):
    return '0' * n_chars


def sender(reciver_conn, results_conn, n_chars, n_packets, warmup_chars=0, warmup_packets=0):
    data = get_data(n_chars=n_chars)

    warmup_data = get_data(n_chars=warmup_chars)
    for i in range(warmup_packets):
        reciver_conn.send(warmup_data)

    t1 = time.time()
    for i in range(n_packets):
        reciver_conn.send(data)
    msg = reciver_conn.recv()
    t2 = time.time()

    print(f'msg from receiver: "{msg}"')

    size = sys.getsizeof(data) * n_packets
    elapsed_time = t2 - t1
    throughput = size / elapsed_time
    results_conn.send((size, elapsed_time, throughput))


def reciver(sender_conn, n_packets, warmup_packets=0):
    for i in range(n_packets + warmup_packets):
        sender_conn.recv()
    sender_conn.send('ok')


def print_results(size, elapsed_time, throughput):
    print(f'Total bytes send: {size} B')
    print(f'Total time to transmit: {elapsed_time} s')
    print(f'Measured throughput: {throughput / 10 ** 6} MB/s')
    print()


def child2parent(chars, packets, warmup_chars=0, warmup_packets=0):
    print('Measuring throughtput from child to parent')

    conn1, conn2 = Pipe()
    p = Process(target=sender, args=(conn1, conn1, chars, packets, warmup_chars, warmup_packets))
    p.start()
    reciver(conn2, packets)
    p.join()

    size, elapsed_time, throughput = conn2.recv()

    conn1.close()
    conn2.close()
    print_results(size, elapsed_time, throughput)


def parent2child(chars, packets, warmup_chars=0, warmup_packets=0):
    print('Measuring throughtput from parent to child')

    conn1, conn2 = Pipe()
    conn3, conn4 = Pipe()
    p = Process(target=reciver, args=(conn2, packets))
    p.start()
    sender(conn1, conn3, chars, packets, warmup_chars, warmup_packets)
    p.join()

    size, elapsed_time, throughput = conn4.recv()

    conn1.close()
    conn2.close()
    conn3.close()
    conn4.close()

    print_results(size, elapsed_time, throughput)


def child2child(chars, packets, warmup_chars=0, warmup_packets=0):
    print('Measuring throughtput from child to child')

    conn1, conn2 = Pipe()
    conn3, conn4 = Pipe()
    p1 = Process(target=reciver, args=(conn2, packets))
    p2 = Process(target=sender, args=(conn1, conn3, chars, packets, warmup_chars, warmup_packets))

    p1.start()
    p2.start()
    p1.join()
    p2.join()

    size, elapsed_time, throughput = conn4.recv()

    conn1.close()
    conn2.close()
    conn3.close()
    conn4.close()

    print_results(size, elapsed_time, throughput)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-b', '--backend', default='mp', choices=['mp', 'lithops', 'fiber'])
    parser.add_argument('--bytes', default=10 ** 6, type=int)
    parser.add_argument('--packets', default=1000, type=int)
    args = parser.parse_args()

    if args.backend == 'mp':
        from multiprocessing import Pipe, Process
    elif args.backend == 'lithops':
        from lithops.multiprocessing import Pipe, Process
        from lithops.multiprocessing import config as mp_config
        import lithops
        lithops.utils.setup_lithops_logger(logging.DEBUG)
        # mp_config.set_parameter(mp_config.PIPE_CONNECTION_TYPE, 'nanomsgconn')
    elif args.backend == 'fiber':
        logging.basicConfig(level=logging.DEBUG)
        logging.getLogger('kubernetes').setLevel(logging.CRITICAL)
        from fiber import config as fiber_config
        from fiber import Pipe, Process
    
    # parent2child(chars=args.bytes, packets=args.packets)
    # child2parent(chars=args.bytes, packets=args.packets)
    child2child(chars=args.bytes, packets=args.packets)
