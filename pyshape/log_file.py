#Last modified 26/08/2025

def read(fname):
    
    f = open(fname)
    lines = [l.strip().split() for l in f.readlines() if l[0]!='#']
    f.close()

    chisqrs = {}
    for l in lines: 
        if not l[0].isnumeric() and l[0]!='WARNING:':
            
            try:
                chi2 = float(l[-1][:-1])
            except:
                continue
            
            chisqrs[f'{l[0]}'] = chi2
                
            if l[0] == 'ALLDATA':
                chisqrs['unreduced'] = float(l[3])
                chisqrs['dof'] = float(l[5])
    return chisqrs

