import numpy as np
import time
import random
import math
import argparse
import logging
import concurrent.futures


def in_circle_sequential_pure(batch_size, seed):
    random.seed(seed)
    s = 0
    for _ in range(batch_size):
        x, y = random.random(), random.random()
        radius = math.sqrt(x**2 + y**2)
        s += radius <= 1
    return s


def measure(mp, workers=10, batch_size=1000):

    procs = []

    def proc_spawn(i):
        proc = mp.Process(target=in_circle_sequential_pure, args=(batch_size, i))
        proc.start()
        procs.append(proc)

    t1 = time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as p:
        p.map(proc_spawn, range(workers))

    [proc.join() for proc in procs]
    t2 = time.time()

    print(t2 - t1)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-b', '--backend', default='mp', choices=['mp', 'lithops', 'fiber'])
    parser.add_argument('--workers', default=4, type=int)
    parser.add_argument('--batch-size', default=1000, type=int)
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

    print(args.backend, args.workers, args.batch_size)
    measure(mp, workers=args.workers, batch_size=args.batch_size)
