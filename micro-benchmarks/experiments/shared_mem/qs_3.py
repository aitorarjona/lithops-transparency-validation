# Sources:
# https://www.geeksforgeeks.org/iterative-quick-sort/
# https://www.geeksforgeeks.org/merge-two-sorted-arrays/

#
# Optimization: use pipes instead of shared memory
#

# import multiprocessing as mp
import lithops.multiprocessing as mp
import random
import math

ARR_SIZE = 1600
PROCESSES = 4

random.seed(42)

arr = [random.randint(0, 100) for _ in range(ARR_SIZE)]

queues = {rank: mp.Queue() for rank in range(PROCESSES)}
master_queue = mp.Queue()


def partition(arr, l, h):
    i = (l - 1)
    x = arr[h]

    for j in range(l, h):
        if arr[j] <= x:
            i = i + 1
            arr[i], arr[j] = arr[j], arr[i]

    arr[i + 1], arr[h] = arr[h], arr[i + 1]
    return (i + 1)


def quick_sort(arr):
    l, h = 0, len(arr) - 1
    size = h - l + 1
    stack = [0] * (size)

    top = -1

    top = top + 1
    stack[top] = l
    top = top + 1
    stack[top] = h

    while top >= 0:
        h = stack[top]
        top = top - 1
        l = stack[top]
        top = top - 1

        p = partition(arr, l, h)

        if p - 1 > l:
            top = top + 1
            stack[top] = l
            top = top + 1
            stack[top] = p - 1

        if p + 1 < h:
            top = top + 1
            stack[top] = p + 1
            top = top + 1
            stack[top] = h


def merge(arr1, arr2):
    n1, n2 = len(arr1), len(arr2)
    arr3 = [None] * (n1 + n2)
    i = 0
    j = 0
    k = 0
 
    while i < n1 and j < n2:
        if arr1[i] < arr2[j]:
            arr3[k] = arr1[i]
            k = k + 1
            i = i + 1
        else:
            arr3[k] = arr2[j]
            k = k + 1
            j = j + 1
     
    while i < n1:
        arr3[k] = arr1[i]
        k = k + 1
        i = i + 1
 
    while j < n2:
        arr3[k] = arr2[j]
        k = k + 1
        j = j + 1
    
    return arr3


def worker(rank, pipe):
    arr = pipe.recv()
    quick_sort(arr)

    done = False
    while not done:
        op, pipe_dst = queues[rank].get()
        if op == 'send':
            pipe_dst.send(arr)
            done = True
        elif op == 'recv':
            recvd_arr = pipe_dst.recv()
            arr = merge(arr, recvd_arr)
            master_queue.put(rank)
        elif op == 'end':
            pipe.send(arr)
            done = True


assert (ARR_SIZE % PROCESSES) == 0
chunk_size = ARR_SIZE // PROCESSES

print('Performing parallel quick sort...')

pipes = [mp.Pipe() for _ in range(PROCESSES)]

pool = mp.Pool(processes=PROCESSES)
map_async = pool.starmap_async(worker,
                               [(rank, p[1]) for rank, p in enumerate(pipes)])

for i, p in enumerate(pipes):
    p[0].send(arr[chunk_size * i:(chunk_size * i) + chunk_size])

print('Performing tree merge sort...')

reduce_steps = PROCESSES
for level in range(int(math.log(PROCESSES, 2))):
    offset = (2**level) * 2
    reduce_peer = offset // 2
    reduce_steps = reduce_steps // 2
    for i in range(reduce_steps):
        receiver, sender = i * offset, (i * offset) + reduce_peer
        c1, c2 = mp.Pipe()
        queues[receiver].put(('recv', c1))
        queues[sender].put(('send', c2))
    for _ in range(reduce_steps):
        rank = master_queue.get()

queues[0].put(('end', None))
arr_sorted = pipes[0][0].recv()
# print(arr_sorted)

map_async.get()
pool.close()
pool.join()

assert all(arr_sorted[i] <= arr_sorted[i + 1]
           for i in range(len(arr_sorted) - 1)), 'Array is not sorted!!!'
print('Array sorted!')