#Last modified 14/05/2025

def read(fname):
    
    f = open(fname)
    lines = [l.strip().split() for l in f.readlines() if l[0]!='#']
    f.close()

    chisqrs = {}
    for l in lines[-30:]: 
        if not l[0].isnumeric() and l[0]!='WARNING:':
            chisqrs[f'{l[0]}'] = float(l[-1][:-1])
    return chisqrs

