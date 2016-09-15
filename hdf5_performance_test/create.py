import tables
import h5py
import numpy as np
import contextlib
from argparse import ArgumentParser

parser = ArgumentParser()
parser.add_argument("-f", "--file", dest="filename",
                    help="write report to FILE", metavar="FILE")
parser.add_argument("-m", "--mode", dest="mode")
parser.add_argument("--rows", dest="rows", type=int, default=100000)
parser.add_argument("--cols", dest="cols", type=int, default=3000)
args = parser.parse_args()

print("creating file %s" % args.filename)
fname = args.filename
with h5py.File(fname) as f:

    n_dim = args.cols
    n_frames = args.rows
    print("with (rows,cols)=(%s, %s)" % (n_frames, n_dim))

    # blosc filter
    blosc_filter_id = 32001
    # blosc args
    blosc_compression_level = 3
    # use blosc shuffle rather than hdf5 shuffle as its performing better
    blosc_shuffle = True
    # compressors shipped with blosc:
    # BLOSC_BLOSCLZ = 0
    # BLOSC_LZ4 = 1
    # BLOSC_LZ4HC = 2
    # BLOSC_SNAPPY = 3
    # BLOSC_ZLIB = 4
    # BLOSC_ZSTD = 5
    blosc_compressor = 0

    print("selected mode: %s" % args.mode)
    if args.mode == "chunk":
        d = f.create_dataset("ds", (n_frames, n_dim), chunks=True, compression=blosc_filter_id,
                             compression_opts=(0, 0, 0, 0,
                                               blosc_compression_level,
                                               1 if blosc_shuffle else 0,
                                               blosc_compressor),
                             shuffle=False)
        d[:] = np.random.random((n_frames, n_dim))
    elif args.mode == "row_cont":
        d = f.create_dataset("ds", (n_frames, n_dim), compression=blosc_filter_id,
                             compression_opts=(0, 0, 0, 0,
                                               blosc_compression_level,
                                               1 if blosc_shuffle else 0,
                                               blosc_compressor),
                             shuffle=False)
        d[:] = np.random.random((n_frames, n_dim))
    elif args.mode == "col_cont":
        d = f.create_dataset("ds", (n_dim, n_frames), compression=32001,
                             compression_opts=(0, 0, 0, 0,
                                               blosc_compression_level,
                                               1 if blosc_shuffle else 0,
                                               blosc_compressor),
                             shuffle=False)
        d[:] = np.random.random((n_dim, n_frames))
    else:
        print("unknown mode")

    f.flush()