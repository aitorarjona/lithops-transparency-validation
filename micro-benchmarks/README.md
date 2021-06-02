# Micro-benchmarks

Use the commands found below to execute the experiment. You may change the `$WORKERS` parameter to the desired number of total processes.

All scripts can be found in the [experiments](./experiments) directory.

### Fork-join overhead

```
python fork.py --backend lithops --workers $WORKERS --fork pool
```

### Network latency

Latency:
```
python latency.py --backend lithops
```

Throughput:
```
python throughput_simple.py --backend lithops
```

### Computation performance

```
python pi.py --backend lithops --workers $WORKERS
```

### Disk performance

```
python disc.py --backend lithops --number $WORKERS
```

### Shared memory performance

You may change the array size and number of processes using the `ARR_SIZE` and `PROCESSES` constant vars in the code.

- Implementation 1 - Shared memory array: `qs_1.py`
- Implementation 2 - Shared memory array with local copy: `qs_2.py`
- Implementation 3 - Using pipes: `qs_3.py`
