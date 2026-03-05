#Last modified by @recannon 04/03/2026

def read(fname):
    '''
    Reads the chisquared from a logfile and returns a dictionary of all data types
    '''
    f = open(fname)
    lines = [l.strip().split() for l in f.readlines() if l[0]!='#']
    f.close()

    chisqrs = {}
    for l in lines: 
        if not l[0].isnumeric() and l[0]!='WARNING:':
            
            try:
                chi2 = float(l[10][:7])
            except:
                continue
            
            chisqrs[f'{l[0]}'] = chi2
                
            if l[0] == 'ALLDATA':
                chisqrs['unreduced'] = float(l[3])
                chisqrs['dof'] = float(l[5])
    return chisqrs

