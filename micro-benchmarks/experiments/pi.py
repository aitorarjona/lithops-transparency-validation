import numpy as np
import time
import random
import math
import argparse
import logging


def in_circle_sequential_pure(args):
    batch_size, seed = args
    random.seed(seed)
    s = 0
    for _ in range(batch_size):
        x, y = random.random(), random.random()
        radius = math.sqrt(x**2 + y**2)
        s += radius <= 1
    return s


def measure(mp, workers=10, batch_size=1000):

    t1 = time.time()
    pool = mp.Pool(workers)
    t2 = time.time()

    t_pool = t2 - t1
    print(f'Time to create pool: {t_pool}')

    args = [[batch_size, i] for i in range(workers)]
    t1 = time.time()
    results = pool.map(in_circle_sequential_pure, args)
    t2 = time.time()
    pool.close()
    # pool.join()

    num_samples = workers * batch_size
    pi = (4.0 * sum(results) / num_samples)

    t_map = t2 - t1
    print(f'Time map: {t_map}')

    print(f'Total time: {t_map + t_pool}')
    print(f'π = {pi}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-b', '--backend', default='mp', choices=['mp', 'lithops', 'fiber'])
    parser.add_argument('--workers', default=4, type=int)
    parser.add_argument('--sample-points', default=None, type=int)
    parser.add_argument('--batch-size', default=1000, type=int)
    args = parser.parse_args()

    if args.backend == 'mp':
        import multiprocessing as mp
    elif args.backend == 'lithops':
        import lithops.multiprocessing as mp
        import lithops
        lithops.utils.setup_lithops_logger(logging.DEBUG)
    elif args.backend == 'fiber':
        logging.basicConfig(level=logging.DEBUG)
        logging.getLogger('kubernetes').setLevel(logging.CRITICAL)
        from fiber import config as fiber_config
        import fiber as mp

    batch_size = args.sample_points // args.workers if args.sample_points else args.batch_size
    measure(mp, workers=args.workers, batch_size=batch_size)
