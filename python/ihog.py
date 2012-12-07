"""
This file implements the paired dictionary inference algorithm for HOG
inversion with Python. For learning the dictionary, see the MATLAB port.
"""

import os
import scipy.io
from numpy import *
import spams

class PairedDictionary(object):
    def __init__(self, dgray, dhog, n, k, ny, nx, lambda1, sbin):
        self.dgray = dgray
        self.dhog = dhog
        self.n = n
        self.k = k
        self.ny = ny
        self.nx = nx
        self.lambda1 = lambda1
        self.sbin = sbin

    @classmethod
    def load(cls, filepath):
        mat = scipy.io.loadmat(filepath)

        sbin = mat['sbin'][0][0]
        lambda1 = mat['lambda'][0][0]
        k = mat['k'][0][0]
        n = mat['n'][0][0]
        ny = mat['ny'][0][0]
        nx = mat['nx'][0][0]
        iters = mat['iters'][0][0]
        dhog = mat['dhog']
        dgray = mat['dgray']

        dhog = array(dhog, dtype = float64, order = 'F')
        dgray = array(dgray, dtype = float64, order = 'F')

        pd = PairedDictionary(dgray, dhog, n, k, ny, nx, lambda1, sbin)

        return pd

pdcache = None

def invertHOG(feat, pd = None):
    if not pd:
        global pdcache
        if pdcache is None:
            filepath = "{0}/../pd.mat".format(
                os.path.dirname(os.path.abspath(__file__)))
            pdcache = PairedDictionary.load(filepath)
        pd = pdcache

    ny = feat.shape[0]
    nx = feat.shape[1]

    windows = zeros((pd.ny*pd.nx*32, (ny-pd.ny+1)*(nx-pd.nx+1)),
                    dtype = float64, order = 'F')
    c = 0
    for i in range(feat.shape[0] - pd.ny + 1):
        for j in range(feat.shape[1] - pd.nx + 1):
            hog = feat[i:i+pd.ny, j:j+pd.nx, :].flatten()
            hog = hog - hog.mean()
            hog = hog / sqrt(hog.var() + 1)
            windows[:, c] = hog
            c += 1

    alpha = spams.lasso(windows, pd.dhog, lambda1 = pd.lambda1, mode = 2)

    recon = dot(pd.dgray, alpha.todense())

    im = zeros(((ny+2)*pd.sbin, (nx+2)*pd.sbin))
    weights = zeros(((ny+2)*pd.sbin, (nx+2)*pd.sbin))
    c = 0
    for i in range(ny - pd.ny + 1):
        for j in range(nx - pd.nx + 1):
            patch = recon[:, c].reshape(((pd.ny+2)*pd.sbin, (pd.nx+2)*pd.sbin))

            im[i*pd.sbin:i*pd.sbin+(pd.ny+2)*pd.sbin,
               j*pd.sbin:j*pd.sbin+(pd.nx+2)*pd.sbin] += patch
            weights[i*pd.sbin:i*pd.sbin+(pd.ny+2)*pd.sbin,
                    j*pd.sbin:j*pd.sbin+(pd.nx+2)*pd.sbin] += 1

            c = c + 1


    im = divide(im, weights)
    im -= im.flatten().min()
    im /= im.flatten().max()

    im = array(im * 255, dtype=uint8)

    return im

if __name__ == "__main__":
    import Image
    im = invertHOG(random.random((10, 10, 32)))
    im = Image.fromarray(im)
    im.convert("RGB").save("out.jpg")