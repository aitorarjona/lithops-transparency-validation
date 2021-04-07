import numpy as np
import time
import random
import math
import argparse
import logging
import time
import concurrent.futures


def worker_function(sleep_seconds):
    time.sleep(sleep_seconds)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-b', '--backend', default='mp', choices=['mp', 'lithops', 'fiber'])
    parser.add_argument('--fork', default='processes', choices=['processes', 'pool'])
    parser.add_argument('--workers', default=4, type=int)
    parser.add_argument('--sleep', default=5, type=int)
    args = parser.parse_args()


    if args.backend == 'mp':
        import multiprocessing as mp
    elif args.backend == 'lithops':
        import lithops
        import lithops.multiprocessing as mp
        lithops.utils.setup_lithops_logger(logging.DEBUG)
    elif args.backend == 'fiber':
        logging.basicConfig(level=logging.DEBUG)
        logging.getLogger('kubernetes').setLevel(logging.CRITICAL)
        from fiber import config as fiber_config
        import fiber as mp

    t1 = time.time()
    if args.fork == 'processes':
        procs = []

        def proc_spawn(i):
            proc = mp.Process(target=worker_function, args=(args.sleep, ))
            proc.start()
            procs.append(proc)

        with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as p:
            p.map(proc_spawn, range(args.workers))

        [proc.join() for proc in procs]
    elif args.fork == 'pool':
        p = mp.Pool(processes=args.workers)
        map_result = p.map_async(worker_function, [args.sleep] * args.workers)
        p.close()
        map_result.wait()
    t2 = time.time()

    print((t2 - t1) - args.sleep)

