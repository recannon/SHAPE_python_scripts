from ...io_utils import console,logger
from .format_artificial_vectors import format_artificial_vectors
from .plot_lc_fit import plot_lc_fit
from ...convinv import read_lctxt
import numpy as np
from astropy.time import Time
import trimesh
from rich.progress import Progress

def lightcurve_generator(V,F,Fn,FNA, lc_file, T0, lam, bet, P, x, out_path, phi,target_h, concave = False,hapke_vals=[0.1,1.32,-0.35,0.02,20], plot=True, show_plot=True):
    
    #Read in lightcurve file
    lightcurves, calibrated = read_lctxt(lc_file)
    no_lightcurves = len(lightcurves)

    # Convert to radians and days
    lam = np.radians(lam)
    bet = np.radians(90-bet)
    phi = np.radians(phi)
    P = P / 24.0

    #Set up the transformation matrices for lambda and beta
    Rlambda     = np.array([[np.cos(lam), -np.sin(lam), 0],
                            [np.sin(lam), np.cos(lam),  0],
                            [0,               0,                1]])
    
    Rbeta       = np.array([[np.cos(bet),  0, np.sin(bet)],
                            [0,            1, 0],
                            [-np.sin(bet), 0, np.cos(bet)]])
    
    #Divide by largest number in matrix (in most cases, 1)
    Rlambda /= np.linalg.norm(Rlambda,2)
    Rbeta   /= np.linalg.norm(Rbeta,2)
    Rneglambda = Rlambda.T
    Rnegbeta   = Rbeta.T

    #Define hapke values
    omega,B0,gF,hwidth,rough = hapke_vals

    #Make output results dictionary
    results = {
        "artificial_lc"    : [],
        "angle_to_sun"     : [],
        "angle_to_earth"   : [],
        "lambert"          : [],
        "lommelSeelinger"  : [],
        "hapke"            : [],
        "best_scaling"     : [],
        "best_scaling_chi" : [],
        "phase_angle"      : [],
        "aspect_angle"     : []
    }

    for i in range(no_lightcurves)[0:3]:
        console.print("\n")
        logger.info(f'Lightcurve {i}')
        
        #Read lightcurve data and sun and earth vectors
        lc_data = lightcurves[i]
        jds_lc = lc_data[:,0]
        t_0,t_fin = jds_lc[0],jds_lc[-1]    
        lc_len =len(jds_lc)

        sun_dir_init   = lc_data[0,2:5]
        earth_dir_init = lc_data[0,5:8]
        sun_dir_final   = lc_data[-1,2:5]
        earth_dir_final = lc_data[-1,5:8]

        if np.all(np.isclose(sun_dir_init, sun_dir_final,rtol=1e+0)) and np.all(np.isclose(earth_dir_init,earth_dir_final,rtol=1e-1)):
            logger.debug('Viewing geometries considered stable')
            unstable = False
            no_rotations=1
        else:
            logger.info('Viewing geometries considered UNSTABLE')
            unstable=True
            no_rotations = np.max([int((t_fin - t_0) // P + 1),2])
        earth_dir,sun_dir,earth_dir_n,sun_dir_n,jds_art = format_artificial_vectors(lc_data,t_0,t_fin,no_rotations,P,target_h,T0,unstable)
        art_lc_len = len(jds_art)

        #Apply asteroid frame transformation to all combined directions
        sun_dir_1 = (Rnegbeta @ Rneglambda @ sun_dir.T).T     
        earth_dir_1 = (Rnegbeta @ Rneglambda @ earth_dir.T).T

        #Create list of data and artificial jds
        jds_all = np.concatenate([jds_lc,jds_art])
        jds_all_len = len(jds_all)

        #Calculate plotting phases for observed lightcurve points, add relevant points to lc_data array
        diffs = jds_all - T0
        alphas = (2 * np.pi / P) * diffs
        plotphases = np.mod(alphas / (2 * np.pi), no_rotations)
        #If no_rotations>1, shift to have start of LC start between 0 and 1
        plotphases = np.mod(plotphases - np.floor(plotphases[0]), no_rotations)
        lc_data = np.concatenate([lc_data,plotphases[:lc_len, np.newaxis]], axis=1)

        #Properties of each data point
        lc_phase_angle = np.arccos(np.einsum('ij,ij->i', earth_dir, sun_dir)/(sun_dir_n*earth_dir_n))
        opposition_surge = B0 / (1+(np.tan(lc_phase_angle/2)) / hwidth)
        PPF = (1-gF**2) / ((1+2*gF*np.cos(lc_phase_angle) + gF**2)**1.5)
        BPPF = (1+opposition_surge)*PPF

        #Calculate phases
        wholecycles = np.floor((jds_all-t_0)/P)
        cycles = (jds_all-t_0)/P
        phases = cycles - wholecycles

        #Mean aspect angle
        mean_alpha = np.mean(alphas)
        Rr    = np.array([[np.cos(mean_alpha+phi), -np.sin(mean_alpha+phi), 0],
                          [np.sin(mean_alpha+phi),  np.cos(mean_alpha+phi), 0],
                          [0,                       0,                      1]])
        VPAB = np.array([0,0,1])
        pole_orientation = Rlambda @ Rbeta @ Rr @ VPAB.T
        # Aspect angle of observation
        lc_aspect_angle = np.degrees( np.arccos(np.dot(earth_dir,pole_orientation)/(earth_dir_n*np.linalg.norm(pole_orientation))) )

        #Arrays that need values saved to them for each point of the artificial lightcurve
        art_lc_data             = np.zeros([jds_all_len,8])
        lambert_contr           = np.zeros([jds_all_len,len(Fn)])
        lommelSeelinger_contr   = np.zeros([jds_all_len,len(Fn)])
        hapke_contr             = np.zeros([jds_all_len,len(Fn)])

        if concave: #Don't need to create more than once
            mesh = trimesh.Trimesh(vertices=V, faces=F, process=False)
            #Offset to avoid self-intersection
            origins = mesh.triangles_center + 1e-3 * Fn

        logger.info('Looping through jd values')
        #Loop through all data points (observed first, then additional ones for coverage)
        with Progress(console=console,transient=True) as progress:

            jd_prog = progress.add_task("", total=len(jds_all))

            for j in range(len(jds_all)):
                #Rotation Matrix due to rotation of the object
                Rr    = np.array([[np.cos(alphas[j]+phi), -np.sin(alphas[j]+phi), 0],
                                    [np.sin(alphas[j]+phi),  np.cos(alphas[j]+phi), 0],
                                    [0,                  0,                 1]])
                Rnegr = Rr.T

                # Create matrices which are the same size as A, but are populated with the Earth and Sun direction vectors.
                A = Fn
                C = (Rnegr @ earth_dir_1[j].T).T #Direction of Earth
                D = (Rnegr @ sun_dir_1[j].T).T   #Direction of Sun

                C = np.tile(C[:3], (A.shape[0], 1)) 
                D = np.tile(D[:3], (A.shape[0], 1)) 

                E = np.einsum('ij,ij->i', A, C) #Dot product to Earth
                G = np.einsum('ij,ij->i', A, D) #Dot product to Sun

                #Mask out vertices that the sun cannot 'see'
                illuminated_mask = (E > 0) & (G > 0) #Is facet visible from Earth? Is facet visible from Sun?
                # logger.debug(f'Currently considering {np.sum(illuminated_mask)}/{len(illuminated_mask)} facets')
                
                if concave:
                    
                    #Sun self shadowing
                    sun_vec = D[j] / np.linalg.norm(D[j])
                    directions = np.tile(sun_vec, (origins.shape[0], 1))
                    _, index_ray, _ = mesh.ray.intersects_location(origins, directions)
                    illuminated_mask[index_ray] = False #Mask sun
                    # logger.debug(f'Currently considering {np.sum(illuminated_mask)}/{len(illuminated_mask)} facets')

                    #Earth self shadowing
                    earth_vec = C[j] / np.linalg.norm(C[j])
                    directions = np.tile(earth_vec, (origins.shape[0], 1))
                    _, index_ray, _ = mesh.ray.intersects_location(origins, directions)
                    illuminated_mask[index_ray] = False #Mask earth
                    # logger.debug(f'Currently considering {np.sum(illuminated_mask)}/{len(illuminated_mask)} facets\n')

                angle_to_earth = E/earth_dir_n[j]
                angle_to_earth = np.where(illuminated_mask, angle_to_earth, 0)
                # angle_to_earth = np.array([0 if (val < 0 or np.isnan(val)) else val for val in angle_to_earth])

                angle_to_sun = G/sun_dir_n[j]
                angle_to_sun = np.where(illuminated_mask, angle_to_sun, 0)
                # angle_to_sun = np.array([0 if (val < 0 or np.isnan(val)) else val for val in angle_to_sun])

                musmue = angle_to_sun * angle_to_earth

                H1 = (1 + 2*angle_to_sun)/(1+2*angle_to_sun*((1 - omega)**0.5))
                H2 = (1 + 2*angle_to_earth)/(1+2*angle_to_earth*((1 - omega)**0.5))

                musplusmue = angle_to_sun+angle_to_earth
                musplusmue[musplusmue == 0] = np.nan #Avoid dividing by zero
                OVER = musmue / musplusmue
                OVER = np.nan_to_num(OVER, nan=0.0)

                hapke = (omega/(4*np.pi)  * FNA * OVER * ( BPPF[j] + H1 * H2 - 1) * np.cos(np.radians(rough))) 
                SH_illumination = np.sum(hapke) 
                SH_illumination = -2.5*np.log10(SH_illumination)

                SLS = np.sum(FNA*OVER)
                area_illuminated = np.sum(FNA*musmue)
                SL_illumination = -2.5*np.log10(area_illuminated)
                SLS_illumination = -2.5*np.log10(SLS)
                SLLS_illumination = -2.5*np.log10(SLS+omega*area_illuminated)

                art_point = [diffs[j],plotphases[j],SL_illumination,SLS_illumination,SLLS_illumination,SH_illumination,phases[j],i]

                art_lc_data[j,:]            = art_point
                lambert_contr[j,:]          = FNA*musmue
                lommelSeelinger_contr[j,:]  = FNA*OVER
                hapke_contr[j,:]            = hapke

                progress.update(jd_prog,advance=1)

        art_lc_data = np.array(art_lc_data)
        lambert_contr = np.array(lambert_contr)
        lommelSeelinger_contr = np.array(lommelSeelinger_contr)
        hapke_contr = np.array(hapke_contr)
    
        logger.debug('Done')

        #Arrays to scale data to be around 0
        scales = np.array([
            [(np.max(art_lc_data[:,2]) + np.min(art_lc_data[:,2]) )/2],
            [(np.max(art_lc_data[:,3]) + np.min(art_lc_data[:,3]) )/2],
            [(np.max(art_lc_data[:,4]) + np.min(art_lc_data[:,4]) )/2],
            [(np.max(art_lc_data[:,5]) + np.min(art_lc_data[:,5]) )/2],
            [np.mean(lc_data[:,9])]
        ])

        #Scaling data for artificial lightcurves (and actual data)
        for y in [2,3,4,5]:
            art_lc_data[:,y]   -= scales[y-2]
        lc_data[:,9] -= scales[4]
        
        #Scale lc_data further to align with the artificial lightcurve, based on minimum chisqr
        oldScalingChi=1e9
        bestsca = 0
        for sca in np.arange(-0.5, 0.501, 0.001):
            differences = art_lc_data[:lc_len,x[0]] - (lc_data[:,9] + sca)
            uncertainties = lc_data[:,8]
            #chisqr, scaled with uncertainties
            scalingChi = np.sum((differences/uncertainties) ** 2)
            if scalingChi < oldScalingChi:
                oldScalingChi = scalingChi*1
                bestsca = sca*1
        lc_data[:,9] += bestsca

        #Sort artificial lightcurve data by plotphase
        art_lc_data = art_lc_data[art_lc_data[:, 0].argsort()]

        if plot:
            plot_lc_fit(art_lc_data,lc_data,x,lc_phase_angle,lc_aspect_angle,i,no_rotations,out_path,show_plot)

        #Append results to the output dictionary
        results['artificial_lc'].append(art_lc_data)
        results['angle_to_sun'].append(angle_to_sun)
        results['angle_to_earth'].append(angle_to_earth)
        results['lambert'].append(lambert_contr)
        results['lommelSeelinger'].append(lommelSeelinger_contr)
        results['hapke'].append(hapke_contr)
        results['best_scaling'].append(bestsca)
        results['best_scaling_chi'].append(oldScalingChi)
        results['phase_angle'].append(lc_phase_angle)
        results['aspect_angle'].append(lc_aspect_angle)

    return results
