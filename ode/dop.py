import numpy as np

def DOP(observer, satellites):
    if satellites != []:
        try:
            satellites = np.array(satellites)
            observer   = np.array(observer)

            R = map(lambda sat: ( (sat - observer)**2 ).sum() ** 0.5 ,satellites)

            A = np.zeros((len(satellites), 4)) - 1
            for i, sat in enumerate(satellites):
                A[i][0:3] = (sat-observer) / R[i]

            A = np.matrix(A)

            Q = (np.dot(A.transpose(), A)) ** -1

            return Q.diagonal().tolist()[0]
        except:
            pass

    return [np.inf, np.inf, np.inf, np.inf]


def H(observer, satellites):
    """horizontal DOP (X-Y)"""
    dop = DOP(observer, satellites)
    try:
        return (dop[0] + dop[1])**0.5
    except:
        return np.inf

def T(observer, satellites):
    """DOP of time"""
    dop = DOP(observer, satellites)
    try:
        return dop[3]**0.5
    except:
        return np.inf

def V(observer, satellites):
    """vertical DOP (z)"""
    dop = DOP(observer, satellites)
    try:
        return dop[2]**0.5
    except:
        return np.inf

def P(observer, satellites):
    """position DOP (X-Y-Z)"""
    dop = DOP(observer, satellites)
    try:
        return (dop[0] + dop[1] + dop[2])**0.5
    except:
        return np.inf

def G(observer, satellites):
    """global DOP (X, Y, Z, T)"""
    dop = DOP(observer, satellites)
    try:
        return (dop[0] + dop[1] + dop[2] + dop[3])**0.5
    except:
        return np.inf
