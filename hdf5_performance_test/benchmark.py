import tables
import h5py
import numpy as np
import time
import os
import contextlib
from argparse import ArgumentParser


from pyemma.coordinates.data import DataInMemory

parser = ArgumentParser()
parser.add_argument("-f", "--file", dest="filename",
                    help="write report to FILE", metavar="FILE")
parser.add_argument("-m", "--mode", dest="mode")
parser.add_argument('--transposed', dest='transposed', action='store_true')
parser.add_argument('--not-transposed', dest='transposed', action='store_false')
parser.set_defaults(transposed=False)
args = parser.parse_args()

propfaid = h5py.h5p.create(h5py.h5p.FILE_ACCESS)
settings = list(propfaid.get_cache())
# 5 mb cache
settings[2] *= 5
propfaid.set_cache(*settings)
with contextlib.closing(h5py.h5f.open(args.filename, fapl=propfaid)) as fid:
    f = h5py.File(fid)

    import gc
    #gc.disable()
    fn = "{m}_{f}.txt"
    read_cs = 10000

    ra_cols = np.sort(np.array([3203, 100, 3003, 500, 2803, 700, 2503, 900, 2303, 1100, 2103, 1300, 1903, 1500, 1703, 1705, 1503, 1900, 1303, 2100, 1103, 2300, 903, 2500, 703, 2700, 503, 2900, 303, 3100, 103, 3300, 3]))

    with open(fn.format(m=args.mode, f=os.path.basename(args.filename)), mode="w") as fh:
        for i in range(4):
            d = f["ds"]
            r = DataInMemory(d)
            print("chunksize: ", d.chunks)
            start = time.time()
            if args.mode == "linear":
                if args.transposed:
                    raise Exception("dont transpose in linear mode.")
                else:
                    for _ in r.iterator(chunk=read_cs):
                        pass
            elif args.mode == "racols":
                if args.transposed:
                    _ = d[np.array(ra_cols), :]
                else:
                    _ = d[:, np.array(ra_cols)]

            stop = time.time()

            print("{i}\t{t}".format(i=i, t=stop - start))
            fh.write("{i}\t{t}\n".format(i=i, t=stop - start))