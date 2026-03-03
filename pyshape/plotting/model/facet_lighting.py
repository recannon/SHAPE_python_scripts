#Last modified by @recannon 03/03/2026

import numpy as np

def facet_lighting(light_dir, view_dir, normals, facet_id,
                   red_facets=None, yellow_facets=None,
                   ambient=0.2,
                   diffuse_strength=0.7,
                   specular_strength=0.6,
                   shininess=80):
    
    #Check normalised
    light_dir = light_dir / np.linalg.norm(light_dir)

    #Diffuse shading
    diffuse = max(np.dot(normals, light_dir), 0)
    #Specular (glossiness)
    reflect_dir = 2*np.dot(normals, light_dir)*normals - light_dir
    spec = max(np.dot(view_dir, reflect_dir), 0) ** shininess
    #Combine effects
    intensity = ambient + diffuse_strength*diffuse + specular_strength*spec
    intensity = np.clip(intensity, 0, 1)

    #Red and yellow tend colour->white rather than black->colour
    white = np.array([1.0, 1.0, 1.0])
    if red_facets is not None and facet_id in red_facets:
        bright = np.array([1.0, 0.0, 0.0])  # pure red
        shaded_colour = bright + (white - bright) * spec  # white highlight
        shaded_colour = np.clip(shaded_colour, 0, 1)
    elif yellow_facets is not None and facet_id in yellow_facets:
        bright = np.array([1.0, 1.0, 0.0])  # pure yellow
        shaded_colour = bright + (white - bright) * spec
        shaded_colour = np.clip(shaded_colour, 0, 1)
    else:
        base_colour = np.array([0.8, 0.8, 0.8])
        shaded_colour = base_colour * intensity
    
    return shaded_colour