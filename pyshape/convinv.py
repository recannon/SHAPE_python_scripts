from .io_utils import logger
import numpy as np
import re

def read_par_file(filename):
    '''
    Function to read a text file and output the model spin-state
    
    Input: 
        - filename : Name and path of an output parameters file from convexinv
    Output:
        - model: [Dictionary]
          - lam, bet : coodinates of the rotation pole
          - P        : sidereal rotation period in hours
          - t0       : epoch of the model
          - c        : the Lommel-Salinger + Lambertian mixing parameter 
          - nu       : YORP strength [rad/d^2]
    '''
    logger.info('Reading convinv par file')

    f     = open(filename)
    lines = [l.strip() for l in f.readlines()]
    f.close()

    #Line 3 contains phase function params
    lam,bet,P = [float(el) for el in re.split('\t|   |  | ',lines[0])]
    t1,ph1    = [float(el) for el in re.split('\t|   |  | ',lines[1])]
    c         = [float(el) for el in re.split('\t|   |  | ',lines[3])][0]

    t0 = t1 - ((ph1/360)*(P/24))

    model = {
            'lam':lam, #pole solution lambda
            'bet':bet, #pole solution beta
            'P'  :P,   #Rotational Period
            't0' :t0,  #t0 for rotation
            'c'  :c,   #Lommel-Salinger + Lambertian mixing
            'nu' :0    #Yorp strength
            } 
    
    logger.debug('Done')

    return model

def read_trimod_file(filename):
    '''
    Function to read a text file and output the model vertex and facet information
    
    Input: 
        - filename : Name and path of an trimod file from convexinv
    Output:
        - V   : [2-D Numpy Array] Vertices locations in Nx3 array of floats
        - F   : [2-D Numpy Array] Facet arrangement in Nx3 array of integers
        - FN  : [2-D Numpy Array] Facet normal vectors in Nx3 array of floats
        - FNa : [1-D Numpy Array] Amplitudes of facet normal vectors
    '''
    
    logger.info('Reading convinv trimod file')

    f     = open(filename)
    lines = [l.strip() for l in f.readlines()]
    f.close()

    #Read file information
    no_vert,no_facets = [int(el) for el in re.split('\t|   |  | ',lines[0])]
    lines = lines[1:]

    V = np.zeros([no_vert,3])
    F = np.zeros([no_facets,3],dtype=int)
    FN = np.zeros_like(F,dtype=float)
    FNa = np.zeros(len(F))

    for i in range(0,no_vert):
        #Read vertices
        vertex = [float(el) for el in re.split('\t|   |  | ',lines[i])]
        V[i] = vertex
    lines = lines[no_vert:]

    for i in range(0,no_facets):
        #Read facets
        facet = np.array([int(el) for el in re.split('\t|   |  | ',lines[i])])
        F[i] = facet - 1
        
        #Calculate normals
        v1,v2,v3 = [V[F[i,j],:] for j in range(0,3)]
        a, b = v1-v3, v2-v3
        face_normal = np.cross(a,b)
        FNa[i] = np.linalg.norm(face_normal)/2
        FN[i,:] = face_normal/(2*FNa[i])

    logger.debug('Done')

    return V,F,FN,FNa

def read_lctxt(filename):
    '''
    Function to read in a text file and output the the lightcurve information within
    
    Input: 
        - filename : Name and path of an lightcurve file in the convexinv format.
    Output:
        - lightcurves: [List] List an 2-D NumPy arrays. Each array has 10 columns:
                        - JD       : jd time of observation
                        - Flux     : Intensity of flux
                        - Sx,Sy,Sz : Sun vectors for the asteroid (3 columns)
                        - Ex,Ey,Ez : Earth vectors for the asteroid (3 columns)
                        - Mag Unc  : Uncertainty in the magnitudes. Assumed as 0.01mag if not provided
                        - Mag      : Magnitude values, calculated from the flux column
        - calibrated: [List] 1-D array containing a value of 0 (uncalibrated) or 1 (calibrated) for each lightcurve
    '''

    logger.info('Reading lctxt file')

    #Open file and read lines
    f     = open(filename)
    lines = [l.strip() for l in f.readlines()]
    f.close()

    #Number of lightcurves
    no_lcs = int(lines[0])
    lines  = lines[1:]
    
    lightcurves = []
    calibrated  = []
    for i in range(no_lcs):
        #Read info for LC
        no_points, cal = [int(el) for el in lines[0].split('\t')]
        #Read data
        data = np.array([[float(el) for el in l.split('\t')] for l in lines[1:no_points+1]])
        #If no uncertainties, add in
        if len(data[0,:])==8:
            errors = np.ones_like(data[:,0]) * 0.01
            data = np.concatenate([data,errors[:,np.newaxis]],axis=1)
        
        #Calculate magnitude value for this intensity, and centre on 0
        magnitudes = -2.5*np.log10(data[:,1])+5
        data = np.concatenate([data, magnitudes[:, np.newaxis]], axis=1)
        #Append data to lightcurves list
        lightcurves.append(data)
        calibrated.append(cal)
        #Remove lightcurve from lines list
        lines = lines[no_points+1:]

    logger.debug('Done')

    return lightcurves, calibrated

