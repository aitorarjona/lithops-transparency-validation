# Parallel Pandas validation

Original work by Pandaparallel contributors
- [https://github.com/nalepae/pandarallel](https://github.com/nalepae/pandarallel)

## Run experiment

Build a Lithops container runtime using `Dockerfile.lambda`. Replace `$WORKERS` with the desired number of parallel workers.
TODO Find link of the tweets CSV dataset.

```
python experiment.py $WORKERS
```

## Diffs
Up is the original code, down is the modified Lithops code.

```python
diff -r poet-es/poet_distributed/es.py lithops-transparency-validation/evolution-strategies/poet_distributed/es.py
421,424c439,456
<         for i in range(batches_per_chunk):
<             chunk_tasks.append(
<                 pool.apply_async(runner, args=(self.iteration,
<                     self.optim_id, batch_size, rs_seeds[i])+args))
---
>         map_args = [
>             (self.iteration, self.optim_id, batch_size, rs_seeds[i]) + args
>             for i in range(batches_per_chunk)
>         ]
> 
>         #####################################################################
>         # MODIFICATION: Replaced pool.apply_async with pool.starmap_async
>         # Maps are more optimized in Lithops instead of a apply or Process.start() loop
> 
>         chunk_tasks = pool.starmap_async(runner, map_args)
> 
>         # for i in range(batches_per_chunk):
>         #     chunk_tasks.append(
>         #         pool.apply_async(runner, args=(self.iteration,
>         #             self.optim_id, batch_size, rs_seeds[i])+args))
> 
>         #####################################################################
> 
428c460,469
<         return [task.get() for task in tasks]
---
>         #####################################################################
>         # MODIFICATION: Now tasks is a AsyncResult instance (returned from
>         # starmap_async) instead of a list of AsyncResults, so we have
>         # to call get once here.
> 
>         return tasks.get()
> 
>         # return [task.get() for task in tasks]
> 
>         #####################################################################
```

```python
diff -r poet-es/poet_distributed/poet_algo.py lithops-transparency-validation/evolution-strategies/poet_distributed/poet_algo.py
53c53,63
<         import fiber as mp
---
>         #####################################################################
>         # MODIFICATION: Replaced fiber import with lithops.multiprocessing import
> 
>         # import fiber as mp
>         
>         import lithops.multiprocessing as mp
>         
>         #####################################################################
> 
>         # from lithops.utils import setup_lithops_logger
>         # setup_lithops_logger(log_level='DEBUG')
```

```python
diff -r poet-es/poet_distributed/noise.py lithops-transparency-validation/evolution-strategies/poet_distributed/noise.py
23,26c22,41
<         logger.info('Sampling {} random numbers with seed {}'.format(
<             count, seed))
<         self._shared_mem = multiprocessing.Array(ctypes.c_float, count)
<         self.noise = np.ctypeslib.as_array(self._shared_mem.get_obj())
---
>         logger.info('Sampling {} random numbers with seed {}'.format(count, seed))
>         
>         #####################################################################
>         # MODIFICATION: Noise table is an in-memory variable in the process instead of
>         # being put in shared memory using multiprocessing.Array.
>         # In Fiber or multiprocessing, a worker executes multiple processes, so
>         # it is useful to put the noise table in shared memory so that all processes
>         # withtin the worker can access it. However, in Lithops only one process is
>         # executed per worker, so it is unnecessary to put it in shared memory.
>         # In fact, AWS Lambda does not mount /dev/shm to the lambda function runtime,
>         # so this would actually raise an exception.
> 
>         self.noise = np.random.RandomState(seed).randn(count).astype(np.float32)  # 64-bit to 32-bit conversion here
> 
>         # import multiprocessing
>         # self._shared_mem = multiprocessing.Array(ctypes.c_float, count)
>         # self.noise = np.ctypeslib.as_array(self._shared_mem.get_obj())
>         
>         #####################################################################
```

## Diffs

```python
diff -r github/pandarallel/pandarallel/pandarallel.py lithops-transparency-validation/parallel-pandas/pandarallel/pandarallel.py
6c6,7
< from multiprocessing import get_context
---
> # Modification: Replaced multiprocessing with lithops.multiprocessing
> from lithops.multiprocessing import get_context
14c15,17
< import dill
---
> # Modificaiton: cloudpickle has better pickling for sending
> # rempote Python objects. It interfaces with dill.
> import cloudpickle as dill
```