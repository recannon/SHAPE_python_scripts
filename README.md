# Shape Scripts

Python tools and bash utilities for interacting with the SHAPE asteroid/comet modeling software.

## Required Directory Structure

The code assumes a working directory (`scan_dir/`) follows the structure below:

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
 - `pyshape.mod.convert_type` can be used to run mkvertmod or mkharmod on many files at once.
 - `pyshape.mod.freeze` can freeze/unfreeze components/sections of modfiles on a component basis.
 - `pyshape.mod.shuffle_vertices` will shuffle the vertices of a modfile vertex component.
 - `pyshape.obs.change_weights` can change weights of obsfile datasets on a set-by-set basis.
 - `pyshape.obs.speckle_mask` directly changes the mask files to cap the signal at the noise threshold
 - Modfile (and to a lesser extent obsfile) information and i/o can be accessed independantly with mod_io and obs_io for use in notebooks/further analysis.
- Writing and compiling SHAPE fits and commands
 - `slurm_pshape` runs a pshape command as a slurm array job, through a python wrapper.
 - `write_quick` produces a single PDF compiling information on the fits of all data types in the obs file in the model.
 - `write_pub` produces a PDF per data-type, producing publication-ready plots for each type.
 - `write_gravenv` produces PDF plots of the gravitational environment of an .obj file.
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

--

## Dependencies

- Python ≥ 3.15 and additional packages (`pyproject.toml`). Can be installed with `pip install .`
- SHAPE modeling software
- SLURM
- ffmpeg

---

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)