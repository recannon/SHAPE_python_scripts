#Last modified @recannon 20261126
#This script varies slightly from the Sam Jackson/Ben Rozitis c++ scripts
#Testing puts this down to using mesh.center_mass rather than origin as the rotation center

import numpy as np
from scipy import constants

G = constants.G

def gravitational_potential_and_slopes(mesh, density, period_hr):

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
    period = period_hr * 3600                       # s
    omega = 2*np.pi / period                     # rad/s
    spin_axis = np.array([0.0, 0.0, 1.0])        # unit vector, in the model frame

    #Field points relative to the centre of mass
    r_com = mesh.triangles_center - mesh.center_mass          # (Nf, 3)

    #Component of each field point perpendicular to the spin axis
    r_perp = r_com - np.outer(r_com @ spin_axis, spin_axis)   # (Nf, 3)

    #Centrifugal potential, per unit mass
    U_cent = 0.5 * omega**2 * np.sum(r_perp**2, axis=1)       # (Nf,)

    #=== Gravitational Slopes===
    
    #Gravitational acceleration at each field point
    E_r = np.einsum('eij,cej->cei', edge_dyad, r_e)               # (Nf, Ne, 3)
    edge_acc = (E_r * L_e[:, :, None]).sum(axis=1)                # (Nf, 3)

    n_dot_r = np.einsum('cfi,fi->cf', r_1, Fn)                    # (Nf, Nfaces)
    face_acc = np.einsum('cf,fi->ci', n_dot_r * omega_f, Fn)      # (Nf, 3)

    a_grav = -G * density * (edge_acc - face_acc)
    
    a_cent = omega**2 * r_perp                                # (Nf, 3)

    g_eff = a_grav + a_cent                       # effective gravity, points "down"
    down = -Fn                  
    cos_theta = (np.einsum('ij,ij->i', g_eff, down)
                 / np.linalg.norm(g_eff, axis=1))
    slopes = np.degrees(np.arccos(np.clip(cos_theta, -1.0, 1.0)))

    print(f'{-U-U_cent}')
    print(f'{slopes}')

    return U, U_cent, slopes
