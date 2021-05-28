# Sources: 
# https://www.geeksforgeeks.org/iterative-quick-sort/
# https://www.techiedelight.com/inplace-merge-two-sorted-arrays/

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
    for i in range(len_x):
        if arr[i + x_start] > arr[y_start]:
            temp = arr[i + x_start]
            arr[i + x_start] = arr[y_start]
            arr[y_start] = temp

            first = arr[y_start]

            k = 1
            while k < len_y and arr[k + y_start] < first:
                arr[k + y_start - 1] = arr[k + y_start]
                k = k + 1

            arr[k + y_start - 1] = first


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