#Last modified 13/09/2025

from ..io_utils import console,safe_exit

def main():
    
    console.print('''Run commands with "python -m pyshape.scan.<command> <args>"

Available commands:
    convert_type       Apply mkharmod or mkvertmod
    freeze_mod         Freeze or unfreeze sets of variables
    shuffle_vertices   Shuffle vertices order

Use "python -m pyshape.scan.<command> -h" for individual details.''')
    
    safe_exit()

if __name__ == "__main__":
    main()
