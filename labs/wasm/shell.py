import pywasm
import wasi
import sys

(_, cmd, rootdir) = sys.argv
cmd = cmd.encode('utf-8')
verbose = False

wasimod = wasi.Wasi([cmd], verbose=verbose, rootdir=rootdir)
runtime = pywasm.load(cmd, { 'wasi_snapshot_preview1': wasimod.imports() })
runtime.exec('_start', [])
