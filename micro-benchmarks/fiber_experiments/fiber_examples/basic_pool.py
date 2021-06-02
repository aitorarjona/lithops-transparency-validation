from fiber import Pool

def f(num):
    print(num)
    return num ** 2

if __name__ == "__main__":
    p = Pool(max_workers=10)
    res = p.map(f, [i for i in range(10)])
    print(res)
    p.close()
