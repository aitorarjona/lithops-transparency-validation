import os
import time
import hashlib
import argparse
import logging


def sender(pipe, dict_result, batches, batch_size):
    print('Wait until receiver is up', flush=True)
    pipe.send('Are you ready?')
    res = pipe.recv()
    print(res)

    data = os.urandom(batch_size)
    print('Start sending...')
    t0 = time.time()
    for i in range(batches):
        pipe.send(data)
    t1 = time.time()

    elapsed = t1 - t0
    dict_result['sender'] = elapsed
    print(f'Sender elapsed: {t1 - t0}', flush=True)


def receiver(pipe, dict_result, batches, batch_size):
    print('Start receiver', flush=True)
    msg = pipe.recv()
    print(msg)
    pipe.send('Yes!')

    print('Start receiving...')
    t0 = time.time()
    for _ in range(batches):
        data = pipe.recv()
    t1 = time.time()

    elapsed = t1 - t0
    dict_result['receiver'] = elapsed
    print(f'Receiver elapsed: {t1 - t0}', flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-b',
                        '--backend',
                        default='lithops',
                        choices=['mp', 'lithops', 'fiber'])
    parser.add_argument('--batches', default=1000, type=int)
    parser.add_argument('--batch-size', default=1_000_000, type=int)
    args = parser.parse_args()

    if args.backend == 'mp':
        import multiprocessing as mp
    elif args.backend == 'lithops':
        import lithops
        import lithops.multiprocessing as mp
        from lithops.multiprocessing import config as mp_config
        lithops.utils.setup_lithops_logger(logging.DEBUG)
        mp_config.set_parameter(mp_config.PIPE_CONNECTION_TYPE, 'redislist')
    elif args.backend == 'fiber':
        logging.basicConfig(level=logging.DEBUG)
        logging.getLogger('kubernetes').setLevel(logging.CRITICAL)
        import fiber as mp

    print('Total data to transmit: {} MB'.format((args.batches * args.batch_size) / 1e6))

    c1, c2 = mp.Pipe()
    man = mp.Manager()
    d = man.dict()

    p1 = mp.Process(target=sender, args=(c1, d, args.batches, args.batch_size))
    p2 = mp.Process(target=receiver, args=(c2, d, args.batches, args.batch_size))

    p2.start()
    p1.start()

    p2.join()
    p1.join()

    print('Sender time: {}'.format(d['sender']))
    print('Receiver time: {}'.format(d['receiver']))

    throughput = ((args.batches * args.batch_size) / d['receiver']) / 1_000_000
    print('Throughput = {} MB/s'.format(throughput))
