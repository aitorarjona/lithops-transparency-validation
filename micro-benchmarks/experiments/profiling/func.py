import hashlib
import multiprocessing as mp
import cProfile, pstats


BYTE_SIZE = 50_000_000
RING_SIZE = 4
HASH_LOOP_COUNT = 50
ROUNDS = 5


queues = [mp.Queue() for _ in range(RING_SIZE)]


def ring_worker(proc_id):
    profiler = cProfile.Profile()
    profiler.enable()

    for i in range(ROUNDS):
        print(f"[{proc_id}] round {i}")
        data = bytes(BYTE_SIZE)

        queues[(proc_id + 1) % RING_SIZE].put(data)
        data = queues[proc_id].get()

        hash_ = hashlib.sha512()
        for _ in range(HASH_LOOP_COUNT):
            hash_.update(data)
        print(f"[{proc_id}]", hash_.hexdigest())
    
    assert queues[proc_id].empty()

    profiler.disable()
    stats = pstats.Stats(profiler).sort_stats("cumtime")
    stats.dump_stats(f"stats_{proc_id}.prof")


def all2all_worker(proc_id):
    profiler = cProfile.Profile()
    profiler.enable()

    for i in range(ROUNDS):
        print(f"[{proc_id}] round {i}")
        data = bytes(BYTE_SIZE)

        for j in range(RING_SIZE):
            if j == proc_id:
                continue
            queues[j].put(data)
        
        for j in range(RING_SIZE):
            if j == proc_id:
                continue
            data = queues[proc_id].get()

        hash_ = hashlib.sha512()
        for _ in range(HASH_LOOP_COUNT):
            hash_.update(data)
        print(f"[{proc_id}]", hash_.hexdigest())
    
    assert queues[proc_id].empty()

    profiler.disable()
    stats = pstats.Stats(profiler).sort_stats("cumtime")
    stats.dump_stats(f"stats_{proc_id}.prof")


def allreduce_master(worker_conns):
    for i in range(ROUNDS):
        for conn in worker_conns:
            data = conn.recv()
        for conn in worker_conns:
            conn.send(data)


def allreduce_worker(proc_id, mast_conn):
    profiler = cProfile.Profile()
    profiler.enable()

    for i in range(ROUNDS):
        print(f"[{proc_id}] round {i}")
        data = bytes(BYTE_SIZE)

        mast_conn.send(data)
        data = mast_conn.recv()

        hash_ = hashlib.sha512()
        for _ in range(HASH_LOOP_COUNT):
            hash_.update(data)
        print(f"[{proc_id}]", hash_.hexdigest())
    
    profiler.disable()
    stats = pstats.Stats(profiler).sort_stats("cumtime")
    stats.dump_stats(f"stats_{proc_id}.prof")
