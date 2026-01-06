#Last modified by @recannon 20/12/2025

#None of these have been extensively tested or checked.
#All I can say is I THINK the form for each is right

import numpy as np

def lambert(mu, mu0, **kwargs):
    return mu * mu0

def lommel_seeliger(mu, mu0, **kwargs):
    denom = mu + mu0
    denom[denom == 0] = np.nan
    return np.nan_to_num(mu * mu0 / denom, nan=0.0)

def hapke(mu, mu0, solar_phase, params):
    
    omega  = params['omega']
    B0 = params.get('B0', 0.0)
    hwidth = params.get('hwidth', 0.01)
    gF = params.get('gF', 0.0)
    rough  = params.get('rough', 0.0)

    opposition_surge = B0 / (1+(np.tan(solar_phase/2)) / hwidth)
    PPF = (1-gF**2) / ((1+2*gF*np.cos(solar_phase) + gF**2)**1.5)
    BPPF = (1+opposition_surge)*PPF

    H1 = (1 + 2*mu0) / (1 + 2*mu0*np.sqrt(1 - omega))
    H2 = (1 + 2*mu ) / (1 + 2*mu *np.sqrt(1 - omega))

    denom = mu + mu0
    denom[denom == 0] = np.nan
    over = np.nan_to_num(mu * mu0 / denom, nan=0.0)

    return (
        omega / (4*np.pi)
        * over
        * (BPPF + H1*H2 - 1)
        * np.cos(np.radians(rough))
    )
    
def kaasalainen(mu, mu0, solar_phase, params):
    
    #Gonna be real this is just from chat gpt for now
    
    R  = params['R']               # reflectance scale
    D  = params.get('D', 0.0)      # Lambert fraction
    k  = params.get('k', 0.0)      # phase slope
    wt = params.get('wt', 0.0)     # opposition weight
    A0 = params.get('A0', 0.0)     # opposition amplitude
    h  = params.get('h', 1.0)      # opposition width (deg)

    # Core scattering
    LS = mu * mu0 / (mu + mu0 + 1e-12)
    L  = mu * mu0
    core = (1 - D) * LS + D * L

    # Opposition surge
    B = A0 * np.exp(-solar_phase / h)
    opposition = 1.0 + wt * B

    # Phase darkening
    phase_term = np.exp(-k * solar_phase)

    return R * core * opposition * phase_term
    
    
    
SCATTERING_LAWS = {
    'lambert': lambert,
    'lommel_seeliger': lommel_seeliger,
    'hapke': hapke,
    'kaasalainen': kaasalainen,
}

def scattering(name, mu, mu0, solar_phase=None, params=None):
    try:
        return SCATTERING_LAWS[name](
            mu, mu0,
            phase=solar_phase,
            params=params or {}
        )
    except KeyError:
        raise ValueError(f'Unknown scattering law: {name}')