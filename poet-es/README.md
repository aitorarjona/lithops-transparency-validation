# POET Evolution Strategies validation

Original work by Uber research
- [https://github.com/uber-research/poet](https://github.com/uber-research/poet)
- [https://eng.uber.com/poet-open-ended-deep-learning/](https://eng.uber.com/poet-open-ended-deep-learning/)

## Run experiment

Build a Lithops container runtime using `Dockerfile.lambda`. Replace `$WORKERS` with the desired number of parallel workers.

```
python master.py . --batch_size=5 --batches_per_chunk=512 --eval_batches_per_step=5 --normalize_grads_by_noise_std --returns_normalization=centered_ranks --envs stump pit roughness --num_workers=$WORKERS --n_iterations=5
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
19d18
<         import multiprocessing
23,26c22,43
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
>         generator = np.random.Generator(np.random.PCG64(seed))
>         self.noise = generator.random(size=count, dtype=np.float32)
> 
>         # import multiprocessing
>         # self.noise = np.random.RandomState(seed).randn(count).astype(np.float32)  # 64-bit to 32-bit conversion here
>         # self._shared_mem = multiprocessing.Array(ctypes.c_float, count)
>         # self.noise = np.ctypeslib.as_array(self._shared_mem.get_obj())
>         
>         #####################################################################
>         
28,29d44
<         self.noise[:] = np.random.RandomState(seed).randn(
<             count)  # 64-bit to 32-bit conversion here
36c51
<         return stream.randint(0, len(self.noise) - dim + 1)
\ No newline at end of file
---
>         return stream.randint(0, len(self.noise) - dim + 1)
