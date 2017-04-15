import numpy as np


def trimboth(a, prop_bound):
    a = np.asarray(a)

    if a.size == 0:
        return a

    num_element = a.shape[0]
    lowercut = int(prop_bound * num_element)
    uppercut = num_element - lowercut
    if lowercut >= uppercut:
        raise ValueError("Proportion too big.")


    # atmp = np.partition(a, (lowercut, uppercut - 1), axis)
    #
    # sl = [slice(None)] * atmp.ndim
    # sl = slice(lowercut, uppercut)
    # return atmp[sl]

    return None