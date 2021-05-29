# Sources: 
# https://www.geeksforgeeks.org/iterative-quick-sort/
# https://www.geeksforgeeks.org/merge-two-sorted-arrays/

#
# Naive approach: using direct access to the shared array
#

# import multiprocessing as mp
import lithops.multiprocessing as mp
import random
import math

ARR_SIZE = 1600
PROCESSES = 4

random.seed(42)

src = [random.randint(0, 100) for _ in range(ARR_SIZE)]
arr = mp.RawArray('i', src)


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


def merge(x_start, len_x, y_start, len_y):
    arr1 = arr[x_start:x_start+len_x]
    arr2 = arr[y_start:y_start+len_y]
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
    
    arr[x_start:y_start+len_y] = arr3


assert (ARR_SIZE % PROCESSES) == 0
chunk_size = ARR_SIZE // PROCESSES

pool = mp.Pool(processes=PROCESSES)

print('Performing parallel quick sort...')

iter_tasks = [((i * chunk_size), (i * chunk_size) + chunk_size - 1)
              for i in range(PROCESSES)]
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

assert all(arr[i] <= arr[i + 1]
           for i in range(len(arr) - 1)), 'Array is not sorted!!!'
print('Array sorted!')