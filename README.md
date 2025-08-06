# Shape Scripts

Python tools and bash utilities for interacting with the SHAPE asteroid/comet modeling software.

## Required Directory Structure

Your working directory (`scan_dir/`) should follow the structure below:

```
scan_dir/
├── faction/        # SLURM output and error files
├── modfiles/       # .mod files (models)
├── obsfiles/       # .obs files (observations)
├── logfiles/       # Logs from launch_fitting.sbatch
├── waction/        # Log files for write action
├── par/            # Parameter files: wpar, mpar, fpar, etc.
└── namecores.txt   # List of file name cores (for mod/obs combinations to run)
```

---

## Notes

- Some directories are created are scripts and some aren't, so best to make sure they all exist.
- `namecores.txt` should contain base filenames (without extensions) for mod/obs pairs to run.

---

## Documentation

- Documentation for python scripts can be with `python -m <script> -h` There is limited documentation in the code, but example run commands at the top of every file
- The other only frequently run script is launch_fitting.sbatch, which can be run as follows:
```
sbatch --array=1-{no_files} launch_fitting.sbatch [a2]
```
a2 will look to run the fit in directory ./subscans/[a2]. Otherwise it will run in CWD

--

## Dependencies

- Python ≥ 3.8 and additional packages (`dependencies.txt`)
- SHAPE modeling software
- SLURM (for running `launch_fitting.sbatch`)
- Lines 7, 10, 12 and 13 of `launch_fitting.sbatch` may need to be changed depending on your compiler and number of cores available.

---

