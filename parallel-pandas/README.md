# Parallel Pandas validation

Original work by Manu NALEPA
- [https://github.com/nalepae/pandarallel](https://github.com/nalepae/pandarallel)

## Run experiment

Build a Lithops container runtime using `Dockerfile.lambda`. Replace `$WORKERS` with the desired number of parallel workers.
You may find a copy of the dataset used [here](https://www.kaggle.com/kazanova/sentiment140).

```
python experiment.py $WORKERS
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