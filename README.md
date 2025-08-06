# Shape Scripts

Python tools and bash utilities for interacting with the SHAPE asteroid/comet modeling software.

## 📁 Required Directory Structure

Your working directory (`scan_dir/`) should follow the structure below:

```
scan_dir/
├── faction/        # SLURM output and error files
├── modfiles/       # .mod files (models)
├── obsfiles/       # .obs files (observations)
├── logfiles/       # Logs from launch_fitting.sbatch
├── waction/        # Temporary files from write actions
│   └── logs/       # Logs from write_fit calling mpar and wpar
├── par/            # Parameter files: wpar, mpar, fpar, etc.
└── namecores.txt   # List of file name cores (for mod/obs combinations to run)
```

---

## 🐍 Python Scripts

### `change_weights.py`

Change the weights of datasets within one or more `.obs` files.

```bash
python -m change_weights <target> <datatype>
```

- `<target>`: Path to an `.obs` file or directory of `.obs` files.
- `<datatype>`: One of:
  - `dd` — Delay-Doppler
  - `cw` — Continuous-wave Doppler
  - `lc` — Lightcurve

---

### `freeze_mod.py`

Freeze or unfreeze specific model components/parameters.

```bash
python -m freeze_mod modfiles v 1
```

- `v`: Freeze vertices (`1` = freeze, `0` = unfreeze)

---

### `convert_mod_type.py`

Convert `.mod` files using `mkvertmod` or `mkharmod`. Supports vertex shuffling.

---

### `grid_scan.py`

Run a 2D grid scan across two parameters for fitting optimization.

---

### `line_scan.py`

Run a 1D parameter scan for fitting optimization.

---

### `write_fit.py`

Generate a `.pdf` showing the orthogonal model views and data fits.

- Internally uses `create_pdf.sh`

---

## 🐚 Bash Scripts

### `launch_fitting.sbatch`

SLURM array job for all model/observation pairs listed in `namecores.txt`.

```bash
sbatch launch_fitting.sbatch [angle2]
```

- If an argument is provided (e.g., `angle2`), runs in polescan mode and expects scan folders at `./subscans/<angle2>/`.

---

### `bash_scripts/create_pdf.sh`

Used internally by `write_fit.py` — not intended to be run directly.

---

### `bash_scripts/tri2mod.sh` (WIP)

Prototype for converting convex inversion `.tri` files to SHAPE `.mod` format.

- Still under development and may fail in certain scenarios.

---

## 🔧 Dependencies

- Python ≥ 3.8
- SHAPE modeling software
- SLURM (for running `launch_fitting.sbatch`)
- Additional dependencies may be required depending on the script (e.g., `matplotlib`, `rich`, `numpy`, etc.)

---

## 📝 Notes

- Make sure all required folders exist before running fitting or scanning scripts.
- `namecores.txt` should contain base filenames (without extensions) for mod/obs pairs to run.
- Grid/pole scans assume specific subdirectory structures — see the documentation in `grid_scan.py` or `launch_fitting.sbatch` for details.