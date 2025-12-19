import numpy as np

def apply_shadow(mask,direction,mesh,mesh_centers,Fn,eps,mesh_extent,ray_scale=5.0):
    
    origins = mesh_centers[mask] + eps * Fn[mask]
    directions = np.broadcast_to(direction * (ray_scale*mesh_extent), origins.shape)

    _, index_ray, index_tri = mesh.ray.intersects_location(
        origins,
        directions,
        multiple_hits=True
    )

    abs_idx = np.where(mask)[0]
    self_hit = index_tri == abs_idx[index_ray]
    shadowed = abs_idx[index_ray[~self_hit]]

    return shadowed

def apply_self_shadowing(mu,mu0,mesh,mesh_centers,mesh_extent,eps,Fn,earth_body,sun_body,weights,):
    
    len_jds = mu.shape[1]
    for j in range(len_jds):

        #Facets facing both earth and sun
        facing = (mu[:, j] > 0.) & (mu0[:, j] > 0.)
        if not np.any(facing):
            continue

        # ---- Earth shadowing (visibility) ----
        shadowed_earth = apply_shadow(facing, earth_body[j],
                                      mesh, mesh_centers, Fn, eps, mesh_extent)

        visible = facing.copy()
        visible[shadowed_earth] = False
        if not np.any(visible):
            continue

        # ---- Sun shadowing (illumination) ----
        shadowed_sun = apply_shadow(visible,sun_body[j],mesh, mesh_centers, Fn, eps, mesh_extent)

        # Zero out both
        weights[shadowed_earth, j] = 0.0
        weights[shadowed_sun, j] = 0.0

    return weights