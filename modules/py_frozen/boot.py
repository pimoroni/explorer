import builtins
import cppmem
import explorer

for k, v in explorer._exports.items():
    setattr(builtins, k, v)

# Switch C++ memory allocations to use MicroPython's heap
cppmem.set_mode(cppmem.MICROPYTHON)
