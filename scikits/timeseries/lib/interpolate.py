"""
A collection of intperolation tools for timeseries

:author: Pierre GF Gerard-Marchant & Matt Knox
:contact: pierregm_at_uga_dot_edu - mattknox_ca_at_hotmail_dot_com
:version: $Id$
"""
__author__ = "Pierre GF Gerard-Marchant & Matt Knox ($Author$)"
__revision__ = "$Revision$"
__date__     = '$Date$'

import numpy as np
import numpy.ma as ma
from numpy.ma import masked, nomask, getmask
from numpy.ma.extras import flatnotmasked_edges

marray = ma.array

__all__ = ['forward_fill', 'backward_fill', 'interp_masked1d',
          ]

#####---------------------------------------------------------------------------
#---- --- Functions for filling in masked values in a masked array ---
#####---------------------------------------------------------------------------
def forward_fill(marr, maxgap=None):
    """
    Forward fills masked values in a 1-d array when there are less ``maxgap``
    consecutive masked values.

    Parameters
    ----------
    marr : MaskedArray
        Series to fill
    maxgap : {None, int}, optional
        Maximum gap between consecutive masked values.
        If ``maxgap`` is None, all masked values are forward-filled.

    """
    # Initialization ..................
    if np.ndim(marr) > 1:
        raise ValueError,"The input array should be 1D only!"
    marr = marray(marr, copy=True)
    if getmask(marr) is nomask or marr.size == 0:
        return marr
    #
    currGap = 0
    if maxgap is not None:
        previdx = -999
        for i in np.where(marr._mask)[0]:
            if i != previdx + 1: currGap = 0
            currGap += 1
            if currGap <= maxgap and not marr._mask[i-1]:
                marr._data[i] = marr._data[i-1]
                marr._mask[i] = False
            elif currGap == maxgap + 1:
                marr._mask[i-maxgap:i] = True
    else:
        for i in np.where(marr._mask)[0]:
            if not marr._mask[i-1]:
                marr._data[i] = marr._data[i-1]
                marr._mask[i] = False
    return marr


def backward_fill(marr, maxgap=None):
    """
    Backward fills masked values in a 1-d array when there are less than ``maxgap``
    consecutive masked values.


    Parameters
    ----------
    marr : MaskedArray
        Series to fill
    maxgap : {None, int}, optional
        Maximum gap between consecutive masked values.
        If ``maxgap`` is None, all masked values are backward-filled.
    """
    return forward_fill(marr[::-1], maxgap=maxgap)[::-1]


def interp_masked1d(marr, kind='linear'):
    """

    Interpolates masked values in an array according to the given method.

    Parameters
    ----------
    marr : MaskedArray
        Array to fill
    kind : {'constant', 'linear', 'cubic', quintic'}, optional
        Type of interpolation

    """
    if np.ndim(marr) > 1:
        raise ValueError("array must be 1 dimensional!")
    #
    marr = marray(marr, copy=True)
    if getmask(marr) is nomask:
        return marr
    #
    unmaskedIndices = (~marr._mask).nonzero()[0]
    if unmaskedIndices.size < 2:
        return marr
    #
    kind = kind.lower()
    if kind == 'constant':
        return forward_fill(marr)
    try:
        k = {'linear' : 1,
             'cubic' : 3,
             'quintic' : 5}[kind.lower()]
    except KeyError:
        raise ValueError("Unsupported interpolation type.")

    first_unmasked, last_unmasked = flatnotmasked_edges(marr)

    vals = marr.data[unmaskedIndices]

    from scipy.interpolate import fitpack
    tck = fitpack.splrep(unmaskedIndices, vals, k=k)

    maskedIndices = marr._mask.nonzero()[0]
    interpIndices = maskedIndices[(maskedIndices > first_unmasked) & \
                                  (maskedIndices < last_unmasked)]
    marr[interpIndices] = fitpack.splev(interpIndices, tck).astype(marr.dtype)
    return marr
