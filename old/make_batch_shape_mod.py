#Last modified 14/05/2025

import numpy as np
import copy
import argparse
import os

def make_batch_shape_mod(bet_min,bet_max,bet_step,lam_min,lam_max,lam_step,a2=0,mod='./mod.template',obs='./obs.template'):

    print(f'Using templates {mod} and {obs}')

    #Check if mod and obs templates exist
    if not os.path.exists(mod) or not os.path.exists(obs):
        raise FileNotFoundError("Cannot find either the mod and obs templates.")

    #Bet values can be linear as all lines of longitude are great circles
    bet_array = np.arange(bet_min,bet_max+bet_step,bet_step)

    #Assuming lam_step is given for the largest small circle, we scale the others accordingly.
    #Do this by calculating the distance around the small circle for the largest small circle
    sc_radii = np.cos(np.deg2rad(bet_array))
    max_radii = np.max(sc_radii)
    lam_step_dist = 2*np.pi*max_radii * lam_step/360

    #Create a list of divisors for lambda range to round steps down to
    lam_range = lam_max-lam_min
    divisors = [d for d in range(1,lam_range+1) if lam_range % d == 0]

    #Then change the step on other small circles to have the distance be the same
    lam_step_b = lam_step_dist*360/(2*np.pi*sc_radii)
    lam_step_b = [max([d for d in divisors if d <= el+1]) for el in lam_step_b]
    
    #Create beta and lambda arrays
    beta_list   = []
    lambda_list = []
    for bet,lam_s in zip(bet_array,lam_step_b):
        
        #Checks to not have duplicate files be made.
        if bet == 90 or bet == -90: #Poles only need one value
            lam_array = np.array([0])
        elif lam_min == 0 and lam_max == 360: #360 and 0 are the same
            lam_array = np.arange(lam_min,lam_max,lam_s)
        else:
            lam_array = np.arange(lam_min,lam_max+lam_s,lam_s)

        for l in lam_array:
            lambda_list.append(l)
            beta_list.append(bet)

    # Open obs file
    f = open(obs,'r')
    obs_temp_lines = f.readlines()
    f.close()

    # Open mod file
    f = open(mod,'r')
    mod_temp_lines = f.readlines()
    f.close()

    #Reset namecores file by opening and closing it.
    f = open('./namecores.txt','w')
    f.close()
    
    start_ind = mod_temp_lines.index('{SPIN STATE}\n')

    for bet, lam in zip(beta_list,lambda_list):

        #Create new file names
        lam_name = f'{lam:03d}'
        bet_name = f'{bet:+03d}'

        namecore = f'lat{bet_name}lon{lam_name}'
        obsfile = f'{namecore}.obs'
        modfile = f'{namecore}.mod'

        #Edit pole in mod files (Correcting for SHAPE's coordinate system)
        lam_shape = f'{(lam + 90):.10f}'
        bet_shape = f'{(90 - bet):.10f}'
        a2_shape  = f'{a2:.10f}'

        #New pole lines
        angle0 = f' c   {lam_shape: >14} {{angle 0 (deg) lambda={lam:.6f}}}\n'
        angle1 = f' c   {bet_shape: >14} {{angle 1 (deg) beta={bet:.6f}}}\n'
        angle2 = f' f   {a2_shape: >14} {{angle 2 (deg)}}\n'

        #Create mod.template copy and change lines
        mod_new_lines = copy.copy(mod_temp_lines)
        mod_new_lines[start_ind+2:start_ind+5] = [angle0,angle1,angle2]

        f = open(f'./obsfiles/{obsfile}', 'w')
        f.writelines(obs_temp_lines)
        f.close()

        f = open(f'./modfiles/{modfile}', 'w')
        f.writelines(mod_new_lines)
        f.close()

        #make namecores.txt (so can stop with the damn .e.)
        f = open(f'./namecores.txt', 'a')
        f.write(namecore + '\n')
        f.close()

    return 1

def main():
    parser = argparse.ArgumentParser(description="Create batches of mod and obs files in modfiles and obsfiles for a pole scan")

    #Beta and lambda ranges and steps
    parser.add_argument("bet_min",  type=int, help="Minimum beta value")
    parser.add_argument("bet_max",  type=int, help="Maximum beta value")
    parser.add_argument("bet_step", type=int, help="Step size of beta")
    parser.add_argument("lam_min",  type=int, help="Minimum lambda value")
    parser.add_argument("lam_max",  type=int, help="Maximum lambda value")
    parser.add_argument("lam_step", type=int, help="Step size of lambda") 

    #mod and obs template files
    parser.add_argument("--angle-2", "-a2", type=float, default = 0, dest='angle_2',
                        help="The value placed in angle 2 of the objects spinstate")
    parser.add_argument("--mod-template", "-mod", type=str, default='./mod.template', dest='mod_template',
                        help="The template mod file. Will keep the f/c state of non pole variables")
    parser.add_argument("--obs-template", "-obs", type=str, default='./obs.template', dest='obs_template',
                        help="The template obs file. Will not be changed")

    args = parser.parse_args()

    make_batch_shape_mod(*vars(args).values())

if __name__ == "__main__":
    main()