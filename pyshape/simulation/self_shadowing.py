#Last modified @recannon 20261110

#20261110 - Changed ray-tracing to stop on first hit, rather than track location of all hits.
#           Speed up of ~25%-50% for 2024on. Also removed need for ray_scale and mesh_extent.

import numpy as np

def apply_shadow(mask,direction,mesh,mesh_trace_origins):
    
    #Mask out already not visible facets
    origins = mesh_trace_origins[mask]
    
    #Perform ray tracing
    # directions = np.broadcast_to(direction * (ray_scale*mesh_extent), origins.shape)
    
    # _, index_ray, index_tri = mesh.ray.intersects_location(
    #     origins,
    #     directions,
    #     multiple_hits=True
    # )
    
    # #Create new mask
    # abs_idx = np.where(mask)[0]
    # self_hit = index_tri == abs_idx[index_ray]
    # shadowed = abs_idx[index_ray[~self_hit]]

    directions = np.broadcast_to(direction, origins.shape)

    hit_any = mesh.ray.intersects_any(origins, directions)
    abs_idx = np.where(mask)[0]
    shadowed = abs_idx[hit_any]

    return shadowed

def apply_self_shadowing(mu,mu0,mesh,mesh_trace_origins,earth_body,sun_body,weights,):
    
    len_jds = mu.shape[1]
    for j in range(len_jds):

        #Facets facing both earth and sun
        facing_e = (mu[:, j] > 0.) & (mu0[:, j] > 0.)
        if not np.any(facing_e):
            continue

        #Earth raytracing
        shadowed_e = apply_shadow(facing_e, earth_body[j],
                                      mesh, mesh_trace_origins)

        #Repeat for sun on fewer facets
        facing_s = facing_e.copy()
        facing_s[shadowed_e] = False
        if not np.any(facing_s):
            continue

        #Sun raytracing
        shadowed_s = apply_shadow(facing_s, sun_body[j],
                                    mesh, mesh_trace_origins)

        #Shadowed arrays: True if shaddowed
        #Facing arrays: True if visible
        weights[shadowed_e, j] = 0.0
        weights[shadowed_s, j] = 0.0

    return weights