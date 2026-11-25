#Last modified by @recannon 20261125

#20261125 - Redo with regex
#20260827 - More Documentation

#Reads a logfile chisqrs
import re

#Returns match of [name, dof, reduced chi2]
CHI2_RE = re.compile(
    r'^(\w+) chi2 = \S+ for ([0-9.]+) dof \(reduced chi2 = ([0-9.]+)\)$'
)

def read(fname):
    '''
    Reads the chisquared from a logfile and returns a dictionary of all data types
    '''
    chisqrs = {}
    with open(fname) as f:
        lines = f.readlines()
    
    for line in lines:
        line = line.strip()
    
        match = CHI2_RE.match(line)
        if not match:
            continue
        
        name = match.group(1)
        chisqrs[name] = float(match.group(3))

        #Commenting this out as it's not required anywhere anymore
        # if name == 'ALLDATA':
            # chisqrs['dof'] = float(match.group(2))

    return chisqrs