import numpy as np
from astropy.time import Time
from astroquery.jplhorizons import Horizons
from ...io_utils import logger

def format_artificial_vectors(lc_data,t_init,t_stop,no_rotations,P,target_h,T0,unstable):

    logger.info('Creating artificial viewing angles')

    #Process lc_data
    jds_data = lc_data[:,0]
    sun_dir_data   = lc_data[:,2:5]*1e8
    earth_dir_data = lc_data[:,5:8]*1e8
    sun_dir_data_n   = np.linalg.norm(sun_dir_data,axis=1)
    earth_dir_data_n = np.linalg.norm(earth_dir_data,axis=1)        

    #Find phases of t_init and t_end, then subtract/add to have complete phases
    diffs = np.array([t_init,t_stop]) - T0
    alphas = (2 * np.pi / P) * diffs
    plotphases = np.mod(alphas / (2 * np.pi), no_rotations)
    #If no_rotations>1, shift to have start of LC start between 0 and 1
    plotphases = np.mod(plotphases - np.floor(plotphases[0]), no_rotations)

    if unstable:
        jd_start = t_init - P*plotphases[0]
        jd_end = t_stop + P*(no_rotations-plotphases[1])
    else:
        jd_start = t_init
        jd_end = t_init+P

    t_step = 0.01 * P  # 1% of rotation period in days
    step_quantum = 1/(60*24)  # 1 minutes in days
    t_step_rounded = round(t_step / step_quantum) * step_quantum
    jds_art = np.arange(jd_start, jd_end+t_step_rounded, t_step_rounded)
    
    #Query Horizons for Earth and Sun vectors
    epochs_range = {
        'start': f'{Time(jds_art[0], format="jd").iso[:16]}',
        'stop': f'{Time(jds_art[-1], format="jd").iso[:16]}',
        'step': f'{int(t_step_rounded/step_quantum)}m'}
    obj_E = Horizons(id=target_h, location='500', epochs=epochs_range)
    earth_vectors = obj_E.vectors()
    earth_dir_art = -np.vstack([
        earth_vectors['x'].data,
        earth_vectors['y'].data,
        earth_vectors['z'].data]).T
    earth_dir_art_n = np.linalg.norm(earth_dir_art, axis=1)
    obj_S = Horizons(id=target_h, location='500@10', epochs=epochs_range)
    sun_vectors = obj_S.vectors()
    sun_dir_art = -np.vstack([
        sun_vectors['x'].data,
        sun_vectors['y'].data,
        sun_vectors['z'].data]).T        
    sun_dir_art_n = np.linalg.norm(sun_dir_art, axis=1)

    #Combine with original observation data
    earth_dir = np.vstack([earth_dir_data, earth_dir_art]).data
    earth_dir_n = np.concatenate([earth_dir_data_n, earth_dir_art_n])
    sun_dir = np.vstack([sun_dir_data, sun_dir_art]).data
    sun_dir_n = np.concatenate([sun_dir_data_n, sun_dir_art_n])

    logger.debug('Done')

    return earth_dir,sun_dir,earth_dir_n,sun_dir_n,jds_art