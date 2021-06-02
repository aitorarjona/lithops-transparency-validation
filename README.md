# Lithops Transparency Validation

This repository contains the code of the experiments carried out in the validation of the X article.

## Experiments

### Micro-benchmarks

All micro-benchmarks code can be found in the [micro-benchmarks directory](./micro-benchmarks/)

1. [Fork-join overhead](./micro-benchmarks/experiments/fork.py).
2. [Network latency](./micro-benchmarks/experiments/latency.py) and [throughput](./micro-benchmarks/experiments/throughput-simple.py).
3. [Computational performance](./micro-benchmarks/experiments/pi.py)
4. [Disk performance](./micro-benchmarks/experiments/disc.py)
5. [Shared memory performance](./micro-benchmarks/shared_mem)

Further instructions on how to replicate the experiments and the parameters used can be found [here](./micro-benchmarks/README.md)

### Applications

All applications used from external sources are property of their respective original contributors. This repository contains the source code of the applications with the modifications made to be executed with Lithops multiprocessing.

1. [Evolution strategies](./poet-es) from [Uber-research](https://github.com/uber-research/poet)
2. [OpenAI Baselines](./openai-baselines) from [Open AI](https://github.com/openai/baselines)
3. [Pandaral·lel](./parallel-pandas) from [Manu NALEPA](https://github.com/nalepae/pandarallel) (Pandaral·lel creator).
4. [Gridsearch hyperparameter tuning](./gridsearch) from [Scikit-learn](https://github.com/scikit-learn/scikit-learn) and [joblib](https://github.com/joblib/joblib).

Further instructions on how to replicate the experiments and the parameters used can be found at the `README.md` of each application directory.
