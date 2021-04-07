import time
import argparse
import logging


def pinging(pinged_conn, results_conn, packets, warmup_packets=0, packet_size=1):
    times = []
    data = '0' * packet_size

    for i in range(warmup_packets):
        pinged_conn.send(data)
        pinged_conn.recv()

    for i in range(packets):
        t1 = time.time()
        pinged_conn.send(data)
        pinged_conn.recv()
        t2 = time.time()
        times.append(t2-t1)

    results_conn.send(times)


def pinged(pinging_conn, packets, warmup_packets=0):
    for i in range(packets + warmup_packets):
        pinging_conn.send(pinging_conn.recv())


def print_results(results):
    print(f'Latency results')
    print(f'mean = {sum(results)/len(results)}, max = {max(results)}, min = {min(results)}')
    print()


def child2parent(Process, Pipe, packets, warmup_packets=0, packet_size=1):
    conn1, conn2 = Pipe()
    p = Process(target=pinging, args=(conn1, conn1, packets, warmup_packets, packet_size))
    p.start()
    pinged(conn2, packets, warmup_packets)
    p.join()

    results = conn2.recv()

    conn1.close()
    conn2.close()

    print_results(results)


def parent2child(Process, Pipe, packets, warmup_packets=0, packet_size=1):
    conn1, conn2 = Pipe()
    conn3, conn4 = Pipe()

    p = Process(target=pinged, args=(conn2, packets, warmup_packets))
    p.start()
    pinging(conn1, conn3, packets, warmup_packets, packet_size)
    p.join()

    results = conn4.recv()

    conn1.close()
    conn2.close()
    conn3.close()
    conn4.close()

    print_results(results)


def child_child(Process, Pipe, packets, warmup_packets=0, packet_size=1):
    conn1, conn2 = Pipe()
    conn3, conn4 = Pipe()
    p1 = Process(target=pinging, args=(conn1, conn3, packets, warmup_packets, packet_size))
    p2 = Process(target=pinged, args=(conn2, packets, warmup_packets))

    p1.start()
    p2.start()

    p1.join()
    p2.join()

    results = conn4.recv()

    conn1.close()
    conn2.close()
    conn3.close()
    conn4.close()

    print_results(results)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-b', '--backend', default='mp', choices=['mp', 'lithops', 'fiber'])
    parser.add_argument('--packets', default=1000, type=int)
    args = parser.parse_args()

    if args.backend == 'mp':
        from multiprocessing import Process, Pipe
    elif args.backend == 'lithops':
        import lithops
        from lithops.multiprocessing import Process, Pipe
        from lithops.multiprocessing import config as mp_config
        # mp_config.set_parameter(mp_config.PIPE_CONNECTION_TYPE, 'nanomsgconn')
        lithops.utils.setup_lithops_logger(logging.DEBUG)
    elif args.backend == 'fiber':
        logging.basicConfig(level=logging.DEBUG)
        logging.getLogger('kubernetes').setLevel(logging.CRITICAL)
        from fiber import config as fiber_config
        from fiber import Process, Pipe

    child2parent(Process, Pipe, args.packets)
    parent2child(Process, Pipe, args.packets)
    child_child(Process, Pipe, args.packets)
