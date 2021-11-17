import hashlib
import cProfile, pstats
from config import *

if LITHOPS:
    import lithops.multiprocessing as mp
else:
    import multiprocessing as mp


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
    stats.dump_stats(f"/tmp/stats_{proc_id}.prof")

    if LITHOPS:
        import lithops.storage as storage

        sto = storage.Storage()
        with open(f"/tmp/stats_{proc_id}.prof", "rb") as f:
            stat_data = f.read()
            sto.put_object(
                bucket="aitor-data", key=f"/tmp/stats_{proc_id}.prof", body=stat_data
            )


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
    stats.dump_stats(f"/tmp/stats_{proc_id}.prof")

    if LITHOPS:
        import lithops.storage as storage

        sto = storage.Storage()
        with open(f"/tmp/stats_{proc_id}.prof", "rb") as f:
            stat_data = f.read()
            sto.put_object(
                bucket="aitor-data", key=f"/tmp/stats_{proc_id}.prof", body=stat_data
            )


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
    stats.dump_stats(f"/tmp/stats_{proc_id}.prof")

    if LITHOPS:
        import lithops.storage as storage

        sto = storage.Storage()
        with open(f"/tmp/stats_{proc_id}.prof", "rb") as f:
            stat_data = f.read()
            sto.put_object(
                bucket="aitor-data", key=f"/tmp/stats_{proc_id}.prof", body=stat_data
            )
