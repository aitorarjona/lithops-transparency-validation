import hashlib
import cProfile, pstats
import concurrent.futures
import time
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
                bucket="aitor-data", key=f"tmp/stats_{proc_id}.prof", body=stat_data
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
                bucket="aitor-data", key=f"tmp/stats_{proc_id}.prof", body=stat_data
            )


def allreduce_master(worker_conns):
    print('starting master')

    def _master(conn):
        for i in range(ROUNDS):
            data = conn.recv()
            conn.send(data)
        
    with concurrent.futures.ThreadPoolExecutor(max_workers=RING_SIZE) as p:
        fts = []
        for worker_conn in worker_conns:
            ft = p.submit(_master, worker_conn)
            fts.append(ft)
        [ft.result() for ft in fts]


def allreduce_worker(proc_id, mast_conn):
    compute_time = 0.0
    comm_time = 0.0

    data = bytes(BYTE_SIZE)
    payload = bytes(PAYLOAD_SIZE)
    for i in range(ROUNDS):
        print(f"[{proc_id}] round {i}")

        hash_ = hashlib.sha512()
        t0 = time.time()
        for _ in range(HASH_LOOP_COUNT):
            hash_.update(data)
        t1 = time.time()
        td = t1 - t0
        compute_time += td
        
        t0 = time.time()
        mast_conn.send(payload)
        _ = mast_conn.recv()
        t1 = time.time()
        td = t1 - t0
        comm_time += td

        print(f"[{proc_id}]", hash_.hexdigest())

    return {'compute_time': compute_time, 'comm_time': comm_time}