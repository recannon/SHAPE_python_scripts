
import trimesh
import numpy as np
from ..plotting import model
from scipy import constants

mesh = trimesh.load('/home/rcannon/Code/Radar/SHAPE/Final_Models/2024on/2024on.obj')

G = constants.G

def gravitational_potential(mesh, density):

    V = mesh.vertices
    F = mesh.faces
    Fn = mesh.face_normals
    F_adjacency = mesh.face_adjacency
    F_adjacency_edges = mesh.face_adjacency_edges

    #Face centres are the 'field points' I want to calculate potential for
    Fc = mesh.triangles_center
    field_points = Fc*1

    #Adjacent face normals for each Edge
    edge_face_normal_pairs = Fn[F_adjacency]

    #Edge vector, from one vertex to the other
    edge_vx1 = V[F_adjacency_edges[:,0]]
    edge_vx2 = V[F_adjacency_edges[:,1]]
    edge_vectors = edge_vx2 - edge_vx1
    edge_centres = edge_vx1 + 0.5*edge_vectors
    edge_lengths = np.linalg.norm(edge_vectors, axis=1)

    #Edge normals, perpendicular to edge vector and face normal, pointing 'outwards' from the face
    edge_normals_1 = np.cross(edge_vectors, edge_face_normal_pairs[:,0])
    edge_normals_2 = np.cross(edge_vectors, edge_face_normal_pairs[:,1])
    edge_normals_1 /= np.linalg.norm(edge_normals_1, axis=1)[:, None]
    edge_normals_2 /= np.linalg.norm(edge_normals_2, axis=1)[:, None]
    #Flip any that point towards their own face's centre rather than away from it
    flip_1 = np.einsum('ij,ij->i', edge_normals_1, edge_centres - Fc[F_adjacency[:, 0]]) < 0
    flip_2 = np.einsum('ij,ij->i', edge_normals_2, edge_centres - Fc[F_adjacency[:, 1]]) < 0
    edge_normals_1[flip_1] *= -1
    edge_normals_2[flip_2] *= -1

    #Create edge dyad
    edge_dyad = (np.einsum('ei,ej->eij', edge_face_normal_pairs[:, 0], edge_normals_1)
            + np.einsum('ei,ej->eij', edge_face_normal_pairs[:, 1], edge_normals_2))

    #Reshape field_points
    field_points = field_points[:, None, :]  #(Nf, 1, 3) instead of (Nf, 3)

    #a and b are the distances from field points to the ends of the edges
    a = np.linalg.norm(edge_vx1 - field_points, axis=2)  #(Nf, Ne)
    b = np.linalg.norm(edge_vx2 - field_points, axis=2)  #(Nf, Ne)
    L_e = np.log((a + b + edge_lengths) / (a + b - edge_lengths))

    #r_e is the vector from each field point to the midpoint of each edge
    r_e = edge_centres - field_points #(Nf, Ne, 3)

    r_E_r = np.einsum('cei,eij,cej->ce', r_e, edge_dyad, r_e)
    edge_term = (r_E_r * L_e).sum(axis=1) # (Nf,)

    #===Face Term===

    #Face vertices
    face_vx1 = V[F[:, 0]]
    face_vx2 = V[F[:, 1]]
    face_vx3 = V[F[:, 2]]

    #Vectors from each field point to each face vertex  (Nf, Nfaces, 3)
    r_1 = face_vx1 - field_points
    r_2 = face_vx2 - field_points
    r_3 = face_vx3 - field_points
    r_1_len = np.linalg.norm(r_1, axis=2)
    r_2_len = np.linalg.norm(r_2, axis=2)
    r_3_len = np.linalg.norm(r_3, axis=2)

    #Solid angle subtended by each face at each field point  (Nf, Nfaces)
    numerator = np.einsum('cfi,cfi->cf', r_1, np.cross(r_2, r_3))
    denominator = (r_1_len * r_2_len * r_3_len
                + np.einsum('cfi,cfi->cf', r_1, r_2) * r_3_len
                + np.einsum('cfi,cfi->cf', r_2, r_3) * r_1_len
                + np.einsum('cfi,cfi->cf', r_3, r_1) * r_2_len)
    omega_f = 2 * np.arctan2(numerator, denominator)

    #r_f . F_f . r_f = (r_f . n_f)^2, using vertex 1 as the point on the face
    r_F_r = np.einsum('cfi,fi->cf', r_1, Fn) ** 2

    face_term = (r_F_r * omega_f).sum(axis=1)   # (Nf,)

    U = 0.5 * G * density * (edge_term - face_term)

    #Rotation
    period = 6.0162 * 3600                       # s
    omega = 2*np.pi / period                     # rad/s
    spin_axis = np.array([0.0, 0.0, 1.0])        # unit vector, in the model frame

    #Field points relative to the centre of mass
    r_com = mesh.triangles_center - mesh.center_mass          # (Nf, 3)

    #Component of each field point perpendicular to the spin axis
    r_perp = r_com - np.outer(r_com @ spin_axis, spin_axis)   # (Nf, 3)

    #Centrifugal potential, per unit mass
    U_cent = 0.5 * omega**2 * np.sum(r_perp**2, axis=1)       # (Nf,)

    return U, U_cent

# density = 1700

# mesh.apply_scale(1000)
# U, U_cent = gravitational_potential(mesh)
# mesh.apply_scale(0.001)


# V = mesh.vertices
# F = mesh.faces
# FN = mesh.face_normals

# from matplotlib import colors
# import matplotlib.pyplot as plt

# U_plot = (-U-U_cent) * 100

# print(U_plot)

# # min,max = -0.62,-0.47
# pmin,pmax = U_plot.min(),U_plot.max()

# orex = [[0.3843,0.2941,0.6588], [0.3137,0.3725,0.6902], [0.1961,0.4510,0.7216], [0.1451,0.5255,0.7294], [0.0471,0.6000,0.7333], [0.1451,0.6667,0.6980], [0.1922,0.7451,0.6549], [0.3333,0.7843,0.6431], [0.4431,0.8235,0.6353], [0.5490,0.8588,0.6235], [0.6471,0.8902,0.6078], [0.7373,0.9176,0.5882], [0.8196,0.9490,0.5647], [0.8745,0.9647,0.5882], [0.9294,0.9843,0.6118], [0.9647,0.9961,0.6588], [1.0000,1.0000,0.7098], [1.0000,0.9647,0.6510], [1.0000,0.9294,0.5765], [1.0000,0.8784,0.5098], [1.0000,0.8275,0.4471], [1.0000,0.7647,0.3882], [1.0000,0.6941,0.3294], [1.0000,0.6157,0.2902], [1.0000,0.5294,0.2549], [1.0000,0.4510,0.2353], [1.0000,0.3647,0.2118], [0.9765,0.2941,0.2431], [0.9412,0.2235,0.2706], [0.8824,0.1412,0.2745], [0.8235,0.0667,0.2784], [0.7490,0.0353,0.2667]]
# norm = colors.Normalize(vmin=pmin, vmax=pmax)
# cmap_orex = colors.ListedColormap(orex)
# # sm = plt.cm.ScalarMappable(cmap=cmap_orex, norm=norm)
# cmap = plt.get_cmap(cmap_orex)

# facet_colours = cmap(norm(U_plot))[:, :3]            # (Nf, 3) RGB

# out_stem = '/home/rcannon/Code/Radar/SHAPE/Final_Models/2024on/test_grav_plot'
# lims,ticks = 0.25,0.2
# shading_flags = np.zeros(len(F), dtype=int)
# model.pub_model(V,F,FN,facet_colours,shading_flags,out_stem,
#                 lims=lims,ticks=ticks,
#                 norm=norm, cmap=cmap, cbar_label='Gravitational Potential [0.01 J/kg]',
#                 cbar_params=[pmin,pmax,0.01])