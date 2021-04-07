import pandas as pd
import time
from pandarallel import pandarallel
import math
import numpy as np

pandarallel.initialize(use_memory_fs=False, nb_workers=4)

df_size = 100
df = pd.DataFrame(dict(a=np.random.randint(1, 8, df_size), b=np.random.rand(df_size)))

def func(x):
    return math.sin(x.a**2) + math.sin(x.b**2)

print('sequential')
res_seq = df.apply(func, axis=1)

print('parallel')
res_parallel = df.parallel_apply(func, axis=1)

assert res_seq.equals(res_parallel)
