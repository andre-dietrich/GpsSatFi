import numpy as np
import dop
from itertools import product

__all__ = ['SatCount',
           'DOPH', 'DOPP', 'DOPT',
           'DOPG', 'DOPV']

def SatCount(scan):
    result = np.zeros(scan["dim"], dtype="float16")

    it = np.nditer(result, op_flags=['writeonly'])

    for s in np.nditer(scan["matrix"]):
        if scan["config"][int(s)] == None:
            it[0][...] = np.nan
        else:
            it[0][...] = len( scan["config"][int(s)] )
        it.next()

    return result

def _DOPS(scan, what="P"):
    if   what == "H":
        f = lambda pos, sat: dop.H(pos, sat)
    elif what == "P":
        f = lambda pos, sat: dop.P(pos, sat)
    elif what == "T":
        f = lambda pos, sat: dop.T(pos, sat)
    elif what == "G":
        f = lambda pos, sat: dop.G(pos, sat)
    elif what == "V":
        f = lambda pos, sat: dop.V(pos, sat)

    result = np.zeros(scan["dim"], dtype="float32")
    it = np.nditer(result, op_flags=['writeonly'])

    it_pos = product(np.arange(scan["area"]["start"][2], scan["area"]["stop"][2], scan["area"]["inc"]),
                     np.arange(scan["area"]["stop"][1], scan["area"]["start"][1], -scan["area"]["inc"]),
                     np.arange(scan["area"]["start"][0], scan["area"]["stop"][0], scan["area"]["inc"]))

    #for s in np.nditer(scan["matrix"]):
    #    dop_val = f(it_pos.next(), scan["config"][int(s)])
    #    it[0][...] = dop_val if dop_val < 25 else 25
    #    it.next()

    for s in np.nditer(scan["matrix"]):
        satellites = scan["config"][int(s)]
        if satellites == None:
            dop_value = np.nan
        elif len(satellites) == 0:
            dop_value = np.NaN
        else:
            dop_value = f(it_pos.next(), satellites)
            if dop_value > 25:
                dop_value = 25

        it[0][...] = dop_value
        it.next()

    return result

def DOPH(scan):
    return _DOPS(scan, "H")

def DOPP(scan):
    return _DOPS(scan, "P")

def DOPT(scan):
    return _DOPS(scan, "T")

def DOPG(scan):
    return _DOPS(scan, "G")

def DOPV(scan):
    return _DOPS(scan, "V")



FCT_LIST = [SatCount, DOPH, DOPP, DOPT, DOPG, DOPV]
