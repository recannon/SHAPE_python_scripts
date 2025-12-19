from .plot_lc_fit import plot_lc_fit
from ..convinv import read_lctxt
from .scattering_laws import scattering
from .self_shadowing import apply_self_shadowing
import numpy as np
from astropy.time import Time
import trimesh
from ..io_utils import logger


def lightcurve_generator(out_path, lc_file, T0, lam, bet, phi, P, Fn, FNA,
                         V=None, F=None, shadowing=False, scattering_law='lambert', scattering_params=None, plot=True, show_plot=False):

    #Read in lightcurve file
    lightcurves, calibrated = read_lctxt(lc_file)
    no_lightcurves = len(lightcurves)

    #Convert to radians and days
    lam = np.radians(lam)
    bet = np.radians(90-bet)
    phi0 = np.radians(phi)
    P = P / 24.0

    #Construct trimesh object for ray-tracing
    if shadowing:
        logger.info('Shadowing enabled')
        mesh = trimesh.Trimesh(vertices=V,faces=F,process=False)
        mesh_centers = mesh.triangles_center
        mesh_extent = np.linalg.norm(mesh.extents)
        #Characteristic length for offset
        eps = 1e-6 * np.linalg.norm(mesh.extents)

    #Set up the transformation matrices for lambda and beta
    Rlambda     = np.array([[ np.cos(lam), np.sin(lam), 0],
                            [-np.sin(lam), np.cos(lam), 0],
                            [ 0,           0,           1]])
    Rbeta       = np.array([[np.cos(bet),  0, -np.sin(bet)],
                            [0,            1,  0],
                            [np.sin(bet),  0,  np.cos(bet)]])
    
    #Divide by largest number in matrix (in most cases, 1)
    Rlambda /= np.linalg.norm(Rlambda,2)
    Rbeta   /= np.linalg.norm(Rbeta,2)

    for i in range(no_lightcurves):
        print("")
        logger.info(f'Lightcurve {i}')
        
        #Read lightcurve data and sun and earth vectors
        lc_data = lightcurves[i]
        jds_lc  = lc_data[:,0]
        mags_lc = lc_data[:,9]
        t_0,t_fin = jds_lc[0],jds_lc[-1]    
        lc_len =len(jds_lc)
        sun_dir_mean = np.mean(lc_data[:,2:5], axis=0)
        earth_dir_mean = np.mean(lc_data[:,5:8], axis=0)
                
        #Compute artificial lightcurve points as well
        #This has room to try and add variable geometry purely by swapping out the tiles
        jds_art = np.linspace(t_0,t_0+P,200)
        jds_all = np.concatenate([jds_lc,jds_art])
        jds_all_len = len(jds_all)
        earth_dir = np.tile(earth_dir_mean[:, None], (1, jds_all_len))
        sun_dir   = np.tile(sun_dir_mean[:, None],   (1, jds_all_len))
        earth_dir_n = earth_dir / np.linalg.norm(earth_dir,axis=0)
        sun_dir_n = sun_dir / np.linalg.norm(sun_dir,axis=0)

        #Time offsets from T0 and corresponding number of rotations and angular rotation
        dt = jds_all - T0
        drotations = dt / P
        dphi = (2*np.pi * drotations) + phi0
        plotphases = drotations % 1
        
        #Add plotphases to lc data information
        lc_data = np.concatenate([lc_data,plotphases[:lc_len, np.newaxis]], axis=1)

        #Earth and sun directions from pole reference frame
        Rpole = Rbeta @ Rlambda
        earth_pole = (Rpole @ earth_dir_n).T   #(N,3)
        sun_pole   = (Rpole @ sun_dir_n).T

        #Properties that don't depend on asteroid rotation
        lc_phase_angle = np.arccos(np.einsum('ij,ij->j', earth_dir_n, sun_dir_n))
        lc_aspect_angle = np.arccos(earth_pole @ [0,0,1]) #[0,0,1] is the pole in pole ref frame

        #Temporarily make all phase and aspect angles the mean (fixed geom)
        mean_phase = np.mean(lc_phase_angle)
        lc_phase_angle = np.full_like(lc_phase_angle, mean_phase)
        mean_aspect = np.mean(lc_aspect_angle)
        lc_aspect_angle = np.full_like(lc_aspect_angle, mean_aspect)

        #Then add in rotation phase
        #Manual matric combination of the below matrix so that it is vectorised
        # Rphi = np.array([[ np.cos(dphi),  np.sin(dphi), 0],
                        #  [-np.sin(dphi),  np.cos(dphi), 0],
                        #  [ 0,             0,            1]])
        #x_body = (Rphi @ x_pole.T).T 
        c, s = np.cos(dphi), np.sin(dphi)
        earth_body = np.column_stack((
            c*earth_pole[:,0] + s*earth_pole[:,1],
           -s*earth_pole[:,0] + c*earth_pole[:,1],
            earth_pole[:,2]))
        sun_body = np.column_stack((
            c*sun_pole[:,0] + s*sun_pole[:,1],
           -s*sun_pole[:,0] + c*sun_pole[:,1],
            sun_pole[:,2]))

        #Arrays that need values saved to them for each point of the artificial lightcurve
        art_lc_data = np.zeros([jds_all_len,5])

        #Cosine of angle between Earth/Sun and facet normals
        mu = Fn @ earth_body.T
        mu0 = Fn @ sun_body.T
        #Clip so cosine between 0 and 90 degrees. (Facing Earth/Sun, but not always both)
        mu = np.clip(mu, 0.0, 1.0)
        mu0 = np.clip(mu0, 0.0, 1.0)

        #Flux contributions from each facet for given law
        weights = scattering(
            name=scattering_law,
            mu=mu,
            mu0=mu0,
            solar_phase=lc_phase_angle,
            params=scattering_params)

        if shadowing:
            weights = apply_self_shadowing(mu,mu0,mesh,mesh_centers,mesh_extent,eps,Fn,earth_body,sun_body,weights)

        #Sum flux values of all (relevant, see above clipping) facets, one value per timestep
        flux = np.sum(FNA[:,None]*weights, axis=0)
        mag = -2.5 * np.log10(flux)

        art_lc_data = np.column_stack((
                dt,
                plotphases,
                flux,
                mag,
            ))

        #Could think about weighting this with errors?
        delta_m = np.mean(mags_lc - art_lc_data[:lc_len, 3]) #Only lc points (not additional 200)
        art_lc_data[:,3] += delta_m         

        if plot:
            plot_lc_fit(art_lc_data,lc_data,lc_phase_angle,lc_aspect_angle,i,out_path,show_plot)

    return True
