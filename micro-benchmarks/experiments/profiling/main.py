import multiprocessing as mp
import cProfile, pstats
from func import ring_worker, all2all_worker, allreduce_master, allreduce_worker, RING_SIZE


if __name__ == "__main__":
    profiler = cProfile.Profile()
    profiler.enable()

    # ring worker
    # with mp.Pool() as pool:
    #     pool.starmap(ring_worker, [(proc_id,) for proc_id in range(RING_SIZE)])
    
    # all2all worker
    # with mp.Pool() as pool:
    #     pool.starmap(all2all_worker, [(proc_id,) for proc_id in range(RING_SIZE)])
    
    # allreduce worker
    worker_conns, master_conns = [], []
    for i in range(RING_SIZE):
        conn1, conn2 = mp.Pipe()
        worker_conns.append(conn1)
        master_conns.append(conn2)
    
    with mp.Pool(processes=RING_SIZE+1) as pool:
        master_proc = pool.apply_async(allreduce_master, (master_conns,))
        pool.starmap(allreduce_worker, [args for args in zip(range(RING_SIZE), worker_conns)])
        master_proc.get()

    profiler.disable()
    stats = pstats.Stats(profiler).sort_stats("cumtime")
    stats.dump_stats("stats_master.prof")
