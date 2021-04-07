# Open AI baselines validation

Original work by OpenAI contributors
- [https://github.com/openai/baselines](https://github.com/openai/baselines)

## Run experiment

| exp | nevns | timesteps | batches | updates |
|---|---|-------|-------|----|
|9	|1  |65536  |128	|512
|10	|2	|65536	|256	|256
|11	|4	|65536	|512	|128
|12	|8	|65536	|1024	|64
|13	|16	|65536	|2048	|32
|14	|32	|65536	|4096	|16
|15	|64	|65536	|8192	|8
|16	|128|65536	|16384	|4
|17	|256|65536	|32768	|2
|18	|512|65536	|65536	|1

Build a Lithops container runtime using `Dockerfile.lambda`.

```
python baselines/run.py --alg=ppo2 --env=BreakoutNoFrameskip-v4 --network=mlp --num_timesteps=$TIMESTEPS --num_env=$NENVS --log_path=logs
```

## Diffs
Up is the original code, down is the modified Lithops code.

```python
diff -r github/baselines/baselines/common/vec_env/subproc_vec_env.py lithops-transparency-validation/openai-baselines/baselines/common/vec_env/subproc_vec_env.py
1c1,2
< import multiprocessing as mp
---
> import lithops.multiprocessing as mp
7c8
< def worker(remote, parent_remote, env_fn_wrappers):
---
> def worker(remote, env_fn_wrappers):
14d14
<     parent_remote.close()
61,68c61,69
<         self.ps = [ctx.Process(target=worker, args=(work_remote, remote, CloudpickleWrapper(env_fn)))
<                    for (work_remote, remote, env_fn) in zip(self.work_remotes, self.remotes, env_fns)]
<         for p in self.ps:
<             p.daemon = True  # if the main process crashes, we should not cause things to hang
<             with clear_mpi_env_vars():
<                 p.start()
<         for remote in self.work_remotes:
<             remote.close()
---
>         self.ps = ctx.Pool().map_async(worker, zip(self.work_remotes, (CloudpickleWrapper(env_fn) for env_fn in env_fns)))
105,106c106,108
<         for p in self.ps:
<             p.join()
---
>         self.ps.get()
```

```python
diff -r github/baselines/baselines/common/cmd_util.py lithops-transparency-validation/openai-baselines/baselines/common/cmd_util.py
56c56
<     if not force_dummy and num_env > 1:
---
>     if not force_dummy and num_env >= 1:
```

```python
diff -r github/baselines/baselines/bench/monitor.py lithops-transparency-validation/openai-baselines/baselines/bench/monitor.py
9a10,11
> from lithops.storage.cloud_proxy import cloud_open as open
```