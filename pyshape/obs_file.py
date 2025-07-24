#Last modified 03/05/2025

import sys
import glob
import numpy as np

class obsDataset:
    VALID_TYPES = ['lightcurve','delay-doppler','doppler']
    
    def __init__(self, lines : list[str]):
        self.lines = lines
        self.type  = lines[7].split()[0]
        if self.type not in self.VALID_TYPES:
            raise ValueError(f'Invalid observation type: {self.type!r}')

    def __repr__(self):
        return f"obsDataset(setno={self.setno}, type={self.type})"
    
    #Computes setno when called, and allows it to be set to new value
    @property
    def setno(self) -> int:
        return int(self.lines[0].strip().split()[-1].rstrip('}'))
    @setno.setter
    def setno(self, new_setno : int):
        self.lines[0] = self.lines[0].replace(str(self.setno), str(new_setno),1)    

    #Change weights. Sets all components of the dataset the same.
    def change_weights(self,new_weights : float):
        '''
        Sets all weights for this dataset to new value
        '''
        
        if self.type == 'lightcurve': #Can only be one lightcurve per set
            #Still need to find file - last set of each file has fewer empty lines
            for i,line in enumerate(self.lines):
                if '{number of samples in lightcurve}' in line:
                    break
                else:
                    continue
            if i == len(self.lines)-1:
                raise ValueError("Could not find lightcurve info line")
            
            weights_line = self.lines[i+1].split()
            weights_line[3] = f'{new_weights:.6e}'
            self.lines[i+1] = ' '.join(weights_line) + '\n'
        
        elif self.type == 'delay-doppler' or self.type == 'doppler':
            #Delay doppler and CW are the same format to access weights
            #Find frame lines
            for i,line in enumerate(self.lines):
                if '{number of frames}' in line:
                    no_frames = int(line.split()[0])
                    break
                else:
                    continue
            if not no_frames:
                raise ValueError("Could not find start of frame info")

            #Loop through lines with frames
            for j,line in enumerate(self.lines[i+2:i+2+no_frames]):
                #Split with exact ' ' so as to keep structure
                weights_line = self.lines[i+2+j].split(' ')
                weights_line[-5] = f'{new_weights:.6e}'
                self.lines[i+2+j] = ' '.join(weights_line)
        
        else:
            raise ValueError("Invalid set type")

def read(fname):
    #Read obs file
    f = open(fname,'r')
    obs_lines = f.readlines()
    f.close()
    lines = [l.strip().split() for l in obs_lines]
    #no sets
    for l in lines:
        if l[1:] == ['{number', 'of', 'sets}']:
            no_sets = int(l[0])
            break

    #Get start of each set
    set_start_lines = [lines.index(['{SET', f'{i}}}']) for i in range(no_sets)] + [None]

    #Loop sets
    datasets = []
    for i in range(no_sets):
        set_line_start = set_start_lines[i]
        set_line_end   = set_start_lines[i+1]
        set_lines = obs_lines[set_line_start:set_line_end]

        set_i = obsDataset(set_lines)

        datasets.append(set_i)
    
    return datasets

def write(fname, datasets):

    no_sets = len(datasets)

    #Gappy text at start of file
    out_str = f'''{{DATA FILE FOR SHAPE.C VERSION 2.10.9 BUILD Mon 22 Jan 14:31:25 GMT 2024}}

                {no_sets} {{number of sets}}
                
                
'''

    for i,d in enumerate(datasets):
        d.setno = i

        out_str += ''.join(d.lines)

    f = open(fname,'w')
    f.write(out_str)
    f.close()
    return 1

