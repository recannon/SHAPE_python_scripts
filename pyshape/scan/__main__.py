#Last modified 13/09/2025

from ..io_utils import console,safe_exit

def main():
    
    console.print('''Run commands with "python -m pyshape.scan.<command> <args>"

Available commands:
    run_grid    Run a grid scan
    run_line    Run a line scan
    qplot       Quick plotting (grid scan)
    pplot       Publication-ready plotting (grid scan)
    combine     Combine scan results
    rank.       Rank scan fits (and can delete those outside threshold)

Use "python -m pyshape.scan.<command> -h" for individual details.''')
    
    safe_exit()

if __name__ == "__main__":
    main()
