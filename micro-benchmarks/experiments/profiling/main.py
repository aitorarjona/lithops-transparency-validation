import cProfile, pstats
from func import ring_worker, all2all_worker, allreduce_master, allreduce_worker
from config import *
import multiprocessing as mp_
import time
import math
import json
import statistics


if LITHOPS:
    import lithops
    import lithops.multiprocessing as mp
    from lithops.multiprocessing import config as mp_config
    lithops.utils.setup_lithops_logger(logging.DEBUG)
    mp_config.set_parameter(mp_config.EXPORT_EXECUTION_DETAILS, '.')
else:
    import multiprocessing as mp


def ring():
    with mp.Pool() as pool:
        pool.starmap(ring_worker, [(proc_id,) for proc_id in range(RING_SIZE)])


def all2all():
    with mp.Pool() as pool:
        pool.starmap(all2all_worker, [(proc_id,) for proc_id in range(RING_SIZE)])


def allreduce():
    worker_conns, master_conns = [], []
    for i in range(RING_SIZE):
        conn1, conn2 = mp.Pipe()
        worker_conns.append(conn1)
        master_conns.append(conn2)


    t0 = time.time()
    master_proc = mp_.Process(target=allreduce_master, args=(master_conns,))
    master_proc.start()
    with mp.Pool(processes=RING_SIZE) as pool:
        times = pool.starmap(
            allreduce_worker, [args for args in zip(range(RING_SIZE), worker_conns)]
        )
    master_proc.join()
    t1 = time.time()

    print('Total time: {}'.format(t1 - t0))

    results = {}
    for i, t in enumerate(times):
        print(i, t)
        results[i] = t
    
    with open('profiling_results.json', 'w') as res_file:
        json.dump(results, res_file)

    print('---')
    print('mean')
    print('compute time: ', statistics.mean(t['compute_time'] for t in times))
    print('comm time: ', statistics.mean(t['comm_time'] for t in times))
    print('---')
    print('max')
    print('compute time: ', max(t['compute_time'] for t in times))
    print('comm time: ', max(t['comm_time'] for t in times))
    print('---')
    print('min')
    print('compute time: ', min(t['compute_time'] for t in times))
    print('comm time: ', min(t['comm_time'] for t in times))


if __name__ == "__main__":
    profiler = cProfile.Profile()
    profiler.enable()

    # ring()
    # all2all()
    allreduce()

    profiler.disable()
    stats = pstats.Stats(profiler).sort_stats("cumtime")
    stats.dump_stats("/tmp/stats_master.prof")
