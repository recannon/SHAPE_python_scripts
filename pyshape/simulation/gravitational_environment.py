#Last modified @recannon 20261126

#Assumes rotates around z axis and CoM is on the origin

import numpy as np
from scipy import constants
from scipy.spatial.distance import cdist

G = constants.G

#Using cdist is 1/3 faster, slower version commented below with more descriptive var names
#Both version return exactly the same numerical values
def gravitational_potential_and_slopes(mesh, density, period_hr):

    V = mesh.vertices
    F = mesh.faces
    Fn = mesh.face_normals
    Fc = mesh.triangles_center
    fa = mesh.face_adjacency
    ed = mesh.face_adjacency_edges
    field_points = Fc                                   # (Nf, 3)

    #===Edge dyad===
    #Edge vectors (one vertex to another) and lengths/centers
    edge_vx1 = V[ed[:, 0]]
    edge_vx2 = V[ed[:, 1]]
    edge_vectors = edge_vx2 - edge_vx1
    edge_lengths = np.linalg.norm(edge_vectors, axis=1)
    edge_centres = edge_vx1 + 0.5 * edge_vectors

    #Edge normals, both handled at once (Ne, 2, 3)
    edge_face_normals = Fn[fa]
    edge_normals = np.cross(edge_vectors[:, None, :], edge_face_normals)
    edge_normals /= np.linalg.norm(edge_normals, axis=2, keepdims=True)
    #Flip any that point towards their own face's centre rather than away from it
    to_face_centre = Fc[fa] - edge_centres[:, None, :]
    edge_normals[np.einsum('efi,efi->ef', edge_normals, to_face_centre) > 0] *= -1

    edge_dyad = np.einsum('efi,efj->eij', edge_face_normals, edge_normals)   # (Ne, 3, 3)

    #===Face dyad===
    i1, i2, i3 = F[:, 0], F[:, 1], F[:, 2]
    fv1, fv2, fv3 = V[i1], V[i2], V[i3]
    face_plane_d = np.einsum('fi,fi->f', fv1, Fn)                    # n . v1
    face_two_area = np.linalg.norm(np.cross(fv2 - fv1, fv3 - fv1), axis=1)
    l12sq = np.sum((fv1 - fv2)**2, axis=1)
    l23sq = np.sum((fv2 - fv3)**2, axis=1)
    l31sq = np.sum((fv3 - fv1)**2, axis=1)

    #===Field points===
    #Distances from every field point to every vertex: edge ends and face corners are all vertices
    D = cdist(field_points, V)                                       # (Nf, Nv)

    #Edge term
    a = D[:, ed[:, 0]]                                               # (Nf, Ne)
    b = D[:, ed[:, 1]]
    L_e = np.log((a + b + edge_lengths) / (a + b - edge_lengths))

    #E . r_e = E . (r_mid - p), with the E . r_mid part precomputed and E . p done as one matmul
    E_r_mid = np.einsum('eij,ej->ei', edge_dyad, edge_centres)       # (Ne, 3)
    E_p = (field_points @ edge_dyad.reshape(-1, 3).T).reshape(len(field_points), -1, 3)
    E_r = E_r_mid - E_p                                              # (Nf, Ne, 3)
    r_e = edge_centres - field_points[:, None, :]                    # (Nf, Ne, 3)

    edge_term = (np.einsum('cei,cei->ce', r_e, E_r) * L_e).sum(axis=1)   # (Nf,)
    edge_acc = np.einsum('ce,cei->ci', L_e, E_r)                          # (Nf, 3)

    #Face term
    d1, d2, d3 = D[:, i1], D[:, i2], D[:, i3]                        # (Nf, Nfaces)
    #r_i . r_j from the law of cosines, no explicit vectors needed
    r12 = 0.5 * (d1**2 + d2**2 - l12sq)
    r23 = 0.5 * (d2**2 + d3**2 - l23sq)
    r31 = 0.5 * (d3**2 + d1**2 - l31sq)

    n_dot_r = face_plane_d - field_points @ Fn.T                     # n_f . r_1, used twice below
    denominator = d1 * d2 * d3 + r12 * d3 + r23 * d1 + r31 * d2
    #r_1 . (r_2 x r_3) = 2 * area * (n . r_1)
    omega_f = 2 * np.arctan2(face_two_area * n_dot_r, denominator)

    face_term = (n_dot_r**2 * omega_f).sum(axis=1)                   # (Nf,)
    face_acc = (n_dot_r * omega_f) @ Fn                              # (Nf, 3)

    U = 0.5 * G * density * (edge_term - face_term)
    a_grav = -G * density * (edge_acc - face_acc)

    #===Rotation===
    omega = 2 * np.pi / (period_hr * 3600)
    spin_axis = np.array([0.0, 0.0, 1.0])
    centre = [0,0,0] #mesh.center_mass

    r_rel = Fc - centre
    r_perp = r_rel - np.outer(r_rel @ spin_axis, spin_axis)
    U_cent = 0.5 * omega**2 * np.sum(r_perp**2, axis=1)
    a_cent = omega**2 * r_perp

    #===Slopes===
    g_eff = a_grav + a_cent
    cos_theta = -np.einsum('ij,ij->i', g_eff, Fn) / np.linalg.norm(g_eff, axis=1)
    slopes = np.degrees(np.arccos(np.clip(cos_theta, -1.0, 1.0)))

    print(f'{-U-U_cent}')
    print(f'{slopes}')

    return U, U_cent, slopes


# def gravitational_potential_and_slopes_old(mesh, density, period_hr):

#     V = mesh.vertices
#     F = mesh.faces
#     Fn = mesh.face_normals
#     F_adjacency = mesh.face_adjacency
#     F_adjacency_edges = mesh.face_adjacency_edges

#     #Face centres are the 'field points' I want to calculate potential for
#     Fc = mesh.triangles_center
#     field_points = Fc*1

#     #Adjacent face normals for each Edge
#     edge_face_normal_pairs = Fn[F_adjacency]

#     #Edge vector, from one vertex to the other
#     edge_vx1 = V[F_adjacency_edges[:,0]]
#     edge_vx2 = V[F_adjacency_edges[:,1]]
#     edge_vectors = edge_vx2 - edge_vx1
#     edge_centres = edge_vx1 + 0.5*edge_vectors
#     edge_lengths = np.linalg.norm(edge_vectors, axis=1)

#     #Edge normals, perpendicular to edge vector and face normal, pointing 'outwards' from the face
#     edge_normals_1 = np.cross(edge_vectors, edge_face_normal_pairs[:,0])
#     edge_normals_2 = np.cross(edge_vectors, edge_face_normal_pairs[:,1])
#     edge_normals_1 /= np.linalg.norm(edge_normals_1, axis=1)[:, None]
#     edge_normals_2 /= np.linalg.norm(edge_normals_2, axis=1)[:, None]
#     #Flip any that point towards their own face's centre rather than away from it
#     flip_1 = np.einsum('ij,ij->i', edge_normals_1, edge_centres - Fc[F_adjacency[:, 0]]) < 0
#     flip_2 = np.einsum('ij,ij->i', edge_normals_2, edge_centres - Fc[F_adjacency[:, 1]]) < 0
#     edge_normals_1[flip_1] *= -1
#     edge_normals_2[flip_2] *= -1

#     #Create edge dyad
#     edge_dyad = (np.einsum('ei,ej->eij', edge_face_normal_pairs[:, 0], edge_normals_1)
#             + np.einsum('ei,ej->eij', edge_face_normal_pairs[:, 1], edge_normals_2))

#     #Reshape field_points
#     field_points = field_points[:, None, :]  #(Nf, 1, 3) instead of (Nf, 3)

#     #a and b are the distances from field points to the ends of the edges
#     a = np.linalg.norm(edge_vx1 - field_points, axis=2)  #(Nf, Ne)
#     b = np.linalg.norm(edge_vx2 - field_points, axis=2)  #(Nf, Ne)
#     L_e = np.log((a + b + edge_lengths) / (a + b - edge_lengths))

#     #r_e is the vector from each field point to the midpoint of each edge
#     r_e = edge_centres - field_points #(Nf, Ne, 3)

#     r_E_r = np.einsum('cei,eij,cej->ce', r_e, edge_dyad, r_e)
#     edge_term = (r_E_r * L_e).sum(axis=1) # (Nf,)

#     #===Face Term===

#     #Face vertices
#     face_vx1 = V[F[:, 0]]
#     face_vx2 = V[F[:, 1]]
#     face_vx3 = V[F[:, 2]]

#     #Vectors from each field point to each face vertex  (Nf, Nfaces, 3)
#     r_1 = face_vx1 - field_points
#     r_2 = face_vx2 - field_points
#     r_3 = face_vx3 - field_points
#     r_1_len = np.linalg.norm(r_1, axis=2)
#     r_2_len = np.linalg.norm(r_2, axis=2)
#     r_3_len = np.linalg.norm(r_3, axis=2)

#     #Solid angle subtended by each face at each field point  (Nf, Nfaces)
#     numerator = np.einsum('cfi,cfi->cf', r_1, np.cross(r_2, r_3))
#     denominator = (r_1_len * r_2_len * r_3_len
#                 + np.einsum('cfi,cfi->cf', r_1, r_2) * r_3_len
#                 + np.einsum('cfi,cfi->cf', r_2, r_3) * r_1_len
#                 + np.einsum('cfi,cfi->cf', r_3, r_1) * r_2_len)
#     omega_f = 2 * np.arctan2(numerator, denominator)

#     #r_f . F_f . r_f = (r_f . n_f)^2, using vertex 1 as the point on the face
#     r_F_r = np.einsum('cfi,fi->cf', r_1, Fn) ** 2

#     face_term = (r_F_r * omega_f).sum(axis=1)   # (Nf,)

#     U = 0.5 * G * density * (edge_term - face_term)

#     #Rotation
#     period = period_hr * 3600                       # s
#     omega = 2*np.pi / period                     # rad/s
#     spin_axis = np.array([0.0, 0.0, 1.0])        # unit vector, in the model frame

#     #Field points relative to the centre of mass
#     r_com = mesh.triangles_center - np.array([0,0,0])#mesh.center_mass          # (Nf, 3)

#     #Component of each field point perpendicular to the spin axis
#     r_perp = r_com - np.outer(r_com @ spin_axis, spin_axis)   # (Nf, 3)

#     #Centrifugal potential, per unit mass
#     U_cent = 0.5 * omega**2 * np.sum(r_perp**2, axis=1)       # (Nf,)

#     #=== Gravitational Slopes===
    
#     #Gravitational acceleration at each field point
#     E_r = np.einsum('eij,cej->cei', edge_dyad, r_e)               # (Nf, Ne, 3)
#     edge_acc = (E_r * L_e[:, :, None]).sum(axis=1)                # (Nf, 3)

#     n_dot_r = np.einsum('cfi,fi->cf', r_1, Fn)                    # (Nf, Nfaces)
#     face_acc = np.einsum('cf,fi->ci', n_dot_r * omega_f, Fn)      # (Nf, 3)

#     a_grav = -G * density * (edge_acc - face_acc)
    
#     a_cent = omega**2 * r_perp                                # (Nf, 3)

#     g_eff = a_grav + a_cent                       # effective gravity, points "down"
#     down = -Fn                  
#     cos_theta = (np.einsum('ij,ij->i', g_eff, down)
#                  / np.linalg.norm(g_eff, axis=1))
#     slopes = np.degrees(np.arccos(np.clip(cos_theta, -1.0, 1.0)))

#     print(f'{-U-U_cent}')
#     print(f'{slopes}')

#     return U, U_cent, slopes
