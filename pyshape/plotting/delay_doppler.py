#Last modified @recannon 202610238

from ..utils import stack_images, load_rgb
    
def format_delay_doppler_images(obs_frames, fit_frames, sky_frames,
                                no_cols, dd_figfile,
                                res_frames=[]):
        
    #Compile strip files into a list, then open them all into pillow objects
    strips = []
    if len(res_frames) == 0:
        for files in zip(obs_frames, fit_frames, sky_frames, strict=True):
            strips.append(stack_images([load_rgb(f) for f in files], horizontal=True))
    else:
        for files in zip(obs_frames, fit_frames, res_frames, sky_frames, strict=True):
            strips.append(stack_images([load_rgb(f) for f in files], horizontal=True))

    no_rows = len(strips) // no_cols + int(len(strips) % no_cols != 0)
    
    #Stack strips into columns, then put the columns side by side
    columns = []
    for c in range(no_cols):
        col_strips = strips[c * no_rows:(c + 1) * no_rows]
        if col_strips:                          
            columns.append(stack_images(col_strips, horizontal=False))

    stack_images(columns, horizontal=True).save(dd_figfile, quality=90)
    
    return dd_figfile
                
                