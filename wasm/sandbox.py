import pywasm
import wasi

def sha256(v):
    wasimod = wasi.Wasi(['sha-export.wasm'])
    runtime = pywasm.load('sha-export.wasm', { 'wasi_snapshot_preview1': wasimod.imports() })
     # Assume fixed offsets for demonstration.
    input_offset = 0
    n = len(v)
    output_offset = n+100
    
    # Convert the input to bytes if it's not already.
    if isinstance(v, str):
        v = v.encode('utf-8')
    
    for i, byte in enumerate(v):
        runtime.store.memory_list[0].data[input_offset + i] = byte
    
    runtime.exec('SHA256', [input_offset, len(v), output_offset])
    
    # Read the output data from the memory.
    r = runtime.store.memory_list[0].data[output_offset:output_offset+32]

    return bytes(r)