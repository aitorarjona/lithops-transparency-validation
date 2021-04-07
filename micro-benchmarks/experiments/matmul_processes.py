import time
import argparse
import logging
import concurrent.futures

def compute_flops(matn, loopcount):
    import numpy as np

    A = np.arange(matn**2, dtype=np.float64).reshape(matn, matn)
    B = np.arange(matn**2, dtype=np.float64).reshape(matn, matn)

    start = time.time()
    for i in range(loopcount):
        c = np.sum(np.dot(A, B))

    flops = 2 * matn**3 * loopcount
    end = time.time()
    return {'flops': flops / (end-start)}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-b', '--backend', default='mp', choices=['mp', 'lithops', 'fiber'])
    parser.add_argument('--workers', default=4, type=int)
    parser.add_argument('--matn', default=1024, type=int)
    parser.add_argument('--loopcount', default=6, type=int)
    args = parser.parse_args()

    if args.backend == 'mp':
        import multiprocessing as mp
    elif args.backend == 'lithops':
        import lithops.multiprocessing as mp
        import lithops
        lithops.utils.setup_lithops_logger(logging.DEBUG)
    elif args.backend == 'fiber':
        # logging.basicConfig(level=logging.DEBUG)
        logging.getLogger('kubernetes').setLevel(logging.CRITICAL)
        from fiber import config as fiber_config
        import fiber as mp
    
    procs = []

    def proc_spawn(i):
        proc = mp.Process(target=compute_flops, args=(args.matn, args.loopcount))
        proc.start()
        procs.append(proc)

    t0 = time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as p:
        p.map(proc_spawn, range(args.workers))

    [proc.join() for proc in procs]
    t1 = time.time()

    total_time = t1 - t0

    est_flops = args.workers * 2 * args.loopcount * args.matn ** 3
    # print(total_time, est_flops)
    print(total_time)
