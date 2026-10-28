#Last modified @recannon 202610238

from PIL import Image

def load_rgb(path):
    """Open a .pgm (greyscale) or .ppm (colour) file as an RGB image."""
    with Image.open(path) as im:
        return im.convert('RGB')

def stack_images(images, horizontal:bool):
    '''Pastes images next to each other (horizontal) or on top of each other.
    Takes pillow Image objects as inputs, not file paths. Returns a pillow Image object.'''
    if horizontal:
        size = (sum(im.width for im in images), max(im.height for im in images))
    else:
        size = (max(im.width for im in images), sum(im.height for im in images))
    canvas = Image.new('RGB', size)
    pos = 0
    for im in images:
        canvas.paste(im, (pos, 0) if horizontal else (0, pos))
        pos += im.width if horizontal else im.height
    return canvas
    
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
                
                