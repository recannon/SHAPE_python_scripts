# Shape Scripts

Python tools and bash utilities for interacting with the SHAPE asteroid/comet modeling software.

## Required Directory Structure

Your working directory (`scan_dir/`) should follow the structure below:

```
scan_dir/
├── faction/        # SLURM output and error files
├── modfiles/       # *.mod files (models)
├── obsfiles/       # *.obs files (observations)
├── logfiles/       # Logs from shape fit actions called by launch_fitting.sbatch
├── waction/        # Log files for write action
├── par/            # Parameter files: wpar, mpar, fpar, etc.
├── namecores.txt   # List of file names (for launch_fitting.sbatch to run)
└── README          # Not compulsory but good practice to keep notes
```

`namecores.txt` should contain base filenames (without extensions) for mod/obs pairs to run. For gridscans, these should be followed by the parameter values. (e.g. As created by scan.run_grid)

---

## Capabilities
- Shape file I/O
 - `pyshape.obs.convert_type` can be used to run mkvertmod or mkharmod on many files at once.
 - `pyshape.mod.freeze` can freeze/unfreeze components/sections of modfiles on a component basis.
 - `pyshape.mod.shuffle_vertices` will shuffle the vertices of a modfile vertex component.
 - `pyshape.obs.change_weights` can change weights of obsfile datasets on a set-by-set basis.
 - Modfile (and to a lesser extent obsfile) information and i/o can be accessed independantly with mod_io and obs_io for use in notebooks/further analysis.
- Writing and compiling SHAPE fits
 - `write_quick` produces a single PDF compiling information on the fits of all data types in the obs file in the model.
 - `write_pub` produces a PDF per data-type, producing publication-ready plots for each type.
 - Plotting routines can be accessed independantly for use in notebooks etc.
- Grid scans
 - `pyshape.scan.run_grid` creates and runs a grid of fit actions using launch_fitting.sbatch. If performing a polescan, it will account for spherical coordinates to save computation at the poles.
 - `pyshape.scan.rank` outputs the top results of a grid scan. It can be used to automatically delete poor fits below a given threshold.
 - `pyshape.scan.combine` can combine subscans run by run_grid, or independant scan_dirs of your choice.
 - `pyshape.scan.qplot` creates a quick plot of the scan results
 - `pyshape.scan.pplot` creates a publication level plot for polescans (will break for non-polescans)

---

## Documentation

- Documentation for python scripts can be with `python -m <script> -h` (e.g. `python -m pyshape.scan.run_grid -h`). There is limited documentation in the code,   `python -m pyshape.scan -h` also works to remind you of the available commands.
- The other only frequently run script is launch_fitting.sbatch, which can be run as follows:
```
sbatch --array=1-{no_files} launch_fitting.sbatch [a2]
```
a2 will look to run the fit in directory ./subscans/[a2]. Otherwise it will run in CWD (only really required by run_grid backend)

--

## Dependencies

- Python ≥ 3.8 and additional packages (`dependencies.txt`)
- SHAPE modeling software
- SLURM (for running `launch_fitting.sbatch`)
- Lines 7, 10, 12 and 13 of `launch_fitting.sbatch` may need to be changed depending on your compiler and number of cores available.
- ffmpeg

---

