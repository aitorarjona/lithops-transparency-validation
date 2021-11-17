import cProfile, pstats
from func import ring_worker, all2all_worker, allreduce_master, allreduce_worker
from config import *
import multiprocessing as mp_


if LITHOPS:
    import lithops.multiprocessing as mp
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

    master_proc = mp_.Process(target=allreduce_master, args=(master_conns,))
    master_proc.start()

    with mp.Pool(processes=RING_SIZE) as pool:
        pool.starmap(
            allreduce_worker, [args for args in zip(range(RING_SIZE), worker_conns)]
        )

    master_proc.join()


if __name__ == "__main__":
    profiler = cProfile.Profile()
    profiler.enable()

    # ring()
    # all2all()
    allreduce()

    profiler.disable()
    stats = pstats.Stats(profiler).sort_stats("cumtime")
    stats.dump_stats("/tmp/stats_master.prof")
