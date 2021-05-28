# Sources: 
# https://www.geeksforgeeks.org/iterative-quick-sort/
# https://www.techiedelight.com/inplace-merge-two-sorted-arrays/

#
# Optimization: copy array from shared memory, perform local sort and put the sorted
# array back to shared memory
#

# import multiprocessing as mp
import lithops.multiprocessing as mp
import random
import math

ARR_SIZE = 1600
PROCESSES = 4

random.seed(42)

src = [random.randint(0, 100) for _ in range(ARR_SIZE)]
arr = mp.Array('i', src)


def partition(arr, l, h):
    i = (l - 1)
    x = arr[h]

    for j in range(l, h):
        if arr[j] <= x:
            i = i + 1
            arr[i], arr[j] = arr[j], arr[i]

    arr[i + 1], arr[h] = arr[h], arr[i + 1]
    return (i + 1)


def quick_sort(l, h):
    l_, h_ = l, h
    local_arr = arr[l_:h_+1]
    l, h = 0, len(local_arr) - 1
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

        p = partition(local_arr, l, h)

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
    
    arr[l_:h_+1] = local_arr


def merge(x_start, len_x, y_start, len_y):
    x = arr[x_start:x_start+len_x]
    y = arr[y_start:y_start+len_y]
    
    m = len(x)
    n = len(y)
 
    for i in range(m):
        if x[i] > y[0]:
            temp = x[i]
            x[i] = y[0]
            y[0] = temp
 
            first = y[0]
 
            k = 1
            while k < n and y[k] < first:
                y[k - 1] = y[k]
                k = k + 1
 
            y[k - 1] = first
    
    arr[x_start:x_start+len_x] = x
    arr[y_start:y_start+len_y] = y
    


assert (ARR_SIZE % PROCESSES) == 0
chunk_size = ARR_SIZE // PROCESSES

pool = mp.Pool(processes=PROCESSES)

print('Performing parallel quick sort...')

iter_tasks = [((i * chunk_size), (i * chunk_size) + chunk_size - 1) for i in range(PROCESSES)]
pool.starmap(quick_sort, iter_tasks)

print('Done')

print('Performing tree merge sort...')

level = PROCESSES
reduce_steps = PROCESSES
chunk_size = ARR_SIZE // PROCESSES
for level in range(1, int(math.log(PROCESSES, 2) + 1)):
    reduce_steps = reduce_steps // 2
    assert (ARR_SIZE % (PROCESSES // level)) == 0
    iter_tasks = [((x * (chunk_size * 2)), chunk_size,
                   (x * (chunk_size * 2)) + chunk_size, chunk_size)
                  for x in range(reduce_steps)]
    pool.starmap(merge, iter_tasks)
    chunk_size += chunk_size

pool.close()
pool.join()

local_arr = arr[:]

assert all(local_arr[i] <= local_arr[i+1] for i in range(len(local_arr)-1)), 'Array is not sorted!!!'
print('Array sorted!')