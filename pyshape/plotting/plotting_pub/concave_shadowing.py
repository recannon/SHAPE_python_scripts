#Last modified 14/05/2025
# import trimesh
import numpy as np

def concave_shadowing(V,F,FN):

    M = F.shape[0]

    # Face centroids
    Vcentr = (V[F[:,0]] + V[F[:,1]] + V[F[:,2]]) / 3

    vismap = np.zeros((M, M))
    logic = np.ones((M, M), dtype=bool)
    Dtab = np.zeros((M, M))
    Zangle = np.zeros((M, M))
    P0 = np.zeros((M, 3, M))  # M x 3 x M — matching MATLAB's 3D array

    for point in range(M):
        Vc = Vcentr[point]
        FNp = FN[point]
        Vfac = np.tile(V[F[point, 0]], (M, 1))

        diffN = np.linalg.norm(Vcentr - Vfac, axis=1)
        dvecs = Vcentr - Vfac
        dproj = np.dot(dvecs, FNp)
        Dtab[point, :] = dproj
        Zangle[point, :] = dproj / diffN
        logic[point, :] = dproj > 0
        vismap[point, point] = 4

        for i in range(M):
            if not logic[point, i]:
                continue
            Vci = Vcentr[i]
            FNi = FN[i]
            viewfac = np.dot(FNp, Vci - Vc) * np.dot(FNi, Vc - Vci)
            if viewfac >= 0:
                logic[point, i] = False

        P0[:, :, point] = Vcentr[point] - V[F[:, 0]]

    # Tangent basis vectors
    v = V[F[:, 1]] - V[F[:, 0]]
    u = V[F[:, 2]] - V[F[:, 0]]
    uv = np.einsum('ij,ij->i', u, v)
    uu = np.einsum('ij,ij->i', u, u)
    vv = np.einsum('ij,ij->i', v, v)
    denom = uv**2 - uu * vv
    denom_safe = np.where(denom == 0, 1e-10, denom)

    shadows = {
        'Vcentr': Vcentr,
        'vismap': vismap,
        'logic': logic,
        'Dtab': Dtab,
        'Zangle': Zangle,
        'v': v,
        'u': u,
        'uv': uv / denom_safe,
        'uu': uu / denom_safe,
        'vv': vv / denom_safe,
        'denom': 1.0 / denom_safe,
        'P0': P0
    }

    return shadows