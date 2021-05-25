import lithops
import time
import shutil

def f(s):
    time.sleep(s)
    try:
        shutil.rmtree('/tmp/lithops/cache')
    except:
        pass


fexec = lithops.FunctionExecutor()
fexec.map(f, [3] * 128)
fexec.get_result()
