import numpy as np
import dop
from itertools import product

__all__ = ['SatCount',
           'DOPH', 'DOPP', 'DOPT',
           'DOPG', 'DOPV',
           'DOPH_FAST', 'DOPP_FAST', 'DOPT_FAST',
           'DOPG_FAST', 'DOPV_FAST',
           ]

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

def _DOPS(scan, f = lambda pos, sat: dop.P(pos, sat)):
    result = np.zeros(scan["dim"], dtype="float32")
    it = np.nditer(result, op_flags=['writeonly'])

    it_pos = product(np.arange(scan["area"]["start"][2], scan["area"]["stop"][2], scan["area"]["inc"]),
                     np.arange(scan["area"]["stop"][1], scan["area"]["start"][1], -scan["area"]["inc"]),
                     np.arange(scan["area"]["start"][0], scan["area"]["stop"][0], scan["area"]["inc"]))

    for s in np.nditer(scan["matrix"]):
        satellites = scan["config"][int(s)]
        if satellites == None:
            dop_value = np.nan # inside a house
        elif len(satellites) == 0:
            dop_value = np.inf # not covered by satellites
        else:
            dop_value = f(it_pos.next(), satellites)

        it[0][...] = dop_value
        it.next()

    return result

def _DOPS_FAST(scan, f = lambda pos, sat: dop.P(pos, sat)):

    result = np.zeros(scan["dim"], dtype="float32")
    it = np.nditer(result, op_flags=['writeonly'])

    x, y = 0, 0
    z=scan['observer']['elevation']

    #print 'scan 0 len='+str(len(np.where(scan["matrix"] == 0)[0]))
    #print 'scan 1 len='+str(len(np.where(scan["matrix"] == 1)[0]))
    #print 'scan 2 len='+str(len(np.where(scan["matrix"] == 2)[0]))
    #print 'scan 3 len='+str(len(np.where(scan["matrix"] == 3)[0]))

    result[np.where(scan["matrix"] == 0)] = np.nan  # inside a house
    result[np.where(scan["matrix"] == 1)] = np.inf  # not covered by satellites

    for config_index in range(2,len(scan['config'])):
       dop_value = f((x,y,z), scan['config'][config_index])
       result[np.where(scan["matrix"] == config_index)] = dop_value

    return result

def DOPH(scan):
    return _DOPS(scan, lambda pos, sat: dop.H(pos, sat))

def DOPP(scan):
    return _DOPS(scan, lambda pos, sat: dop.P(pos, sat))

def DOPT(scan):
    return _DOPS(scan, lambda pos, sat: dop.T(pos, sat))

def DOPG(scan):
    return _DOPS(scan, lambda pos, sat: dop.G(pos, sat))

def DOPV(scan):
    return _DOPS(scan, lambda pos, sat: dop.V(pos, sat))

def DOPH_FAST(scan):
    return _DOPS_FAST(scan, lambda pos, sat: dop.H(pos, sat))

def DOPP_FAST(scan):
    return _DOPS_FAST(scan, lambda pos, sat: dop.P(pos, sat))

def DOPT_FAST(scan):
    return _DOPS_FAST(scan, lambda pos, sat: dop.T(pos, sat))

def DOPG_FAST(scan):
    return _DOPS_FAST(scan, lambda pos, sat: dop.G(pos, sat))

def DOPV_FAST(scan):
    return _DOPS_FAST(scan, lambda pos, sat: dop.V(pos, sat))


FCT_LIST = [SatCount, DOPH_FAST, DOPP_FAST, DOPT_FAST, DOPG_FAST, DOPV_FAST, DOPH, DOPP, DOPT, DOPG, DOPV]
