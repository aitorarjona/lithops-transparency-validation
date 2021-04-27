import uuid
import numpy as np
import time
import pickle
import click
import argparse





MB = 1000 ** 2

class RandomDataGenerator(object):
    """
    A file-like object which generates random data.
    1. Never actually keeps all the data in memory so
    can be used to generate huge files.
    2. Actually generates random data to eliminate
    false metrics based on compression.
    It does this by generating data in 1MB blocks
    from np.random where each block is seeded with
    the block number.
    """

    def __init__(self, bytes_total):
        self.bytes_total = bytes_total
        self.pos = 0
        self.current_block_id = None
        self.current_block_data = ""
        self.BLOCK_SIZE_BYTES = 1 * MB
        self.block_random = np.random.randint(0, 256, dtype=np.uint8,
                                              size=self.BLOCK_SIZE_BYTES)

    def __len__(self):
        return self.bytes_total

    @property
    def len(self):
        return self.bytes_total

    def tell(self):
        return self.pos

    def seek(self, pos, whence=0):
        if whence == 0:
            self.pos = pos
        elif whence == 1:
            self.pos += pos
        elif whence == 2:
            self.pos = self.bytes_total - pos

    def get_block(self, block_id):
        if block_id == self.current_block_id:
            return self.current_block_data

        self.current_block_id = block_id
        self.current_block_data = (block_id + self.block_random).tostring()
        return self.current_block_data

    def get_block_coords(self, abs_pos):
        block_id = abs_pos // self.BLOCK_SIZE_BYTES
        within_block_pos = abs_pos - block_id * self.BLOCK_SIZE_BYTES
        return block_id, within_block_pos

    def read(self, bytes_requested=None):
        if not bytes_requested:
            bytes_requested = self.bytes_total
        remaining_bytes = self.bytes_total - self.pos
        if remaining_bytes == 0:
            return b''

        bytes_out = min(remaining_bytes, bytes_requested)
        start_pos = self.pos

        byte_data = b''
        byte_pos = 0
        while byte_pos < bytes_out:
            abs_pos = start_pos + byte_pos
            bytes_remaining = bytes_out - byte_pos

            block_id, within_block_pos = self.get_block_coords(abs_pos)
            block = self.get_block(block_id)
            # how many bytes can we copy?
            chunk = block[within_block_pos:within_block_pos + bytes_remaining]

            byte_data += chunk

            byte_pos += len(chunk)

        self.pos += bytes_out

        return byte_data




def compute_rate_stat(results):
    rates = np.array([r['mb_rate'] for r in results])

    return rates.mean(), rates.std()


def compute_peak_rate(results, start_time):

    def compute_times_rates(start_time, d):
        runtime_bins = np.linspace(0, 50, 500)
        x = np.array(d)
        tzero = start_time
        tr_start_time = x[:, 0] - tzero
        tr_end_time = x[:, 1] - tzero
        rate = x[:, 2]

        N = len(tr_start_time)
        runtime_rate = np.zeros((N, len(runtime_bins)))

        for i in range(N):
            s = tr_start_time[i]
            e = tr_end_time[i]
            a, b = np.searchsorted(runtime_bins, [s, e])
            if b-a > 0:
                runtime_rate[i, a:b] = rate[i]

        return runtime_rate.sum(axis=0)

    mb_rates = [(res['start_time'], res['end_time'], res['mb_rate']) for res in results]

    runtime_rate = compute_times_rates(start_time, mb_rates)

    return runtime_rate.max()


def write_object(key_name, mb_per_file, chunk_size=100 * MB):
    bytes_n = mb_per_file * MB
    d = RandomDataGenerator(bytes_n)
    print(key_name)
    with open(key_name, 'wb') as f:
        data = d.read(chunk_size)
        start_time = time.time()
        while data:
            f.write(data)
            data = d.read(chunk_size)
        f.flush()
        end_time = time.time()

    mb_rate = mb_per_file / (end_time - start_time)
    print('MB write Rate: ' + str(mb_rate))

    return {'start_time': start_time, 'end_time': end_time, 'mb_rate': mb_rate}


def write(mb_per_file, number, key_prefix):
    # create list of random keys
    keynames = [key_prefix + str(uuid.uuid4().hex.upper()) for unused in range(number)]
    map_data = [(keyname, mb_per_file) for keyname in keynames]
    with Pool() as pool:
        start_time = time.time()
        results = pool.starmap(write_object, map_data)
        end_time = time.time()

    total_time = end_time-start_time

    write_start = min([result['start_time'] for result in results])
    write_end = max([result['end_time'] for result in results])
    mb_rate = number * mb_per_file / (write_end - write_start)

    mean, std = compute_rate_stat(results)
    peak_rate = compute_peak_rate(results, start_time)

    res = {'start_time': start_time,
           'total_time': total_time,
           'mb_rate': mb_rate,
           'keynames': keynames,
           'results': results,
           'mean_fn_rate': mean,
           'std_fn_rate': std,
           'peak_rate': peak_rate}

    return res


def read_object(key_name, mb_per_file, chunk_size=1*MB):
    print(key_name)

    with open(key_name, 'rb') as f:
        start_time = time.time()
        data = f.read(chunk_size)
        while data:
            data = f.read(chunk_size)
        end_time = time.time()

    mb_rate = mb_per_file/(end_time-start_time)
    print('MB read Rate: '+str(mb_rate))

    return {'start_time': start_time, 'end_time': end_time, 'mb_rate': mb_rate, 'bytes_read': mb_per_file}


def read(number, keylist_raw, mb_per_file):

    if number == 0:
        keynames = keylist_raw
    else:
        keynames = [keylist_raw[i % len(keylist_raw)] for i in range(number)]

    map_data = [(keyname, mb_per_file) for keyname in keynames]

    with Pool() as pool:
        start_time = time.time()
        results = pool.starmap(read_object, map_data)
        end_time = time.time()

    total_time = end_time-start_time

    read_start = min([result['start_time'] for result in results])
    read_end = max([result['end_time'] for result in results])
    mb_rate = number * mb_per_file / (read_end - read_start)

    mean, std = compute_rate_stat(results)
    peak_rate = compute_peak_rate(results, start_time)

    res = {'start_time': start_time,
           'total_time': total_time,
           'mb_rate': mb_rate,
           'results': results,
           'mean_fn_rate': mean,
           'std_fn_rate': std,
           'peak_rate': peak_rate}

    return res


def delete_temp_data(keynames):
    print('Deleting temp files...')
    for keyname in keynames:
        os.remove(keyname)
    print('Done!')


def run(mb_per_file, number, key_prefix, outdir, name):

    print('Executing Write Test:')
    res_write = write(mb_per_file, number, key_prefix)
    pickle.dump(res_write, open('{}/{}_write.pickle'.format(outdir, name), 'wb'), -1)

    print('Sleeping 20 seconds...')
    time.sleep(20)

    print('Executing Read Test:')
    keynames = res_write['keynames']
    res_read = read(number, keynames, mb_per_file)
    pickle.dump(res_read, open('{}/{}_read.pickle'.format(outdir, name), 'wb'), -1)

    delete_temp_data(keynames)

    print(f'Mean writing rate: {res_write["mb_rate"]} MB/s')
    print(f'Peak writing rate: {res_write["peak_rate"]} MB/s')
    print(f'Mean/std functions writing rate: {res_write["mean_fn_rate"]} / {res_write["std_fn_rate"]}  MB/s')

    print(f'Mean reading rate: {res_read["mb_rate"]} MB/s')
    print(f'Peak reading rate: {res_read["peak_rate"]} MB/s')
    print(f'Mean/std functions reading rate: {res_read["mean_fn_rate"]} / {res_read["std_fn_rate"]} MB/s')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-b', '--backend', default='mp', choices=['mp', 'lithops', 'fiber'])
    parser.add_argument('--number', default=20, type=int, help='number of files')
    parser.add_argument('--key_prefix', default='', type=str, help='Object key prefix')
    parser.add_argument('--outdir', default='.', type=str, help='dir to save results in')
    parser.add_argument('--name', default='disc_benchmark', type=str, help='filename to save results in')
    parser.add_argument('--mb_per_file', default=100, type=int, help='MB of each object')
    args = parser.parse_args()

    if args.backend == 'lithops':
        from lithops.multiprocessing import Pool
        from lithops.storage.cloud_proxy import open, os
    elif args.backend == 'mp':
        from multiprocessing import Pool
        import os

    run(args.mb_per_file, args.number, args.key_prefix, args.outdir, args.name)