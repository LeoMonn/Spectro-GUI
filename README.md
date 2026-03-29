# GUI Manip

Legacy PyQt application for a spectroscopy / angle-resolved experiment.

The codebase bundles several GUI tools used on the original setup:
- rotation stage control
- spectrometer acquisition
- camera acquisition
- spectrum fitting and post-processing

## Main entry points

Canonical module names:
- `experiment_master_gui.py`: master GUI orchestrating rotation + spectrometer + camera workers
- `spectrometer_gui.py`: current standalone spectrometer worker GUI (the only up-to-date `Spectro*` line)
- `camera_gui.py`: standalone camera worker GUI
- `rotation_gui.py`: standalone rotation worker GUI
- `spectrum_fit_dialog.py`: current fitting dialog used by `spectrometer_gui.py`
- `band_diagram_analysis.py`, `camera_filter_analysis.py`, `fit_donnees2`: analysis helpers

Historical entry points and wrappers are now kept only in the ignored local `legacy/`
directory when needed; they are no longer part of the tracked repository.

## Dependencies

Core Python packages:
- PyQt5
- numpy
- scipy
- matplotlib
- pyqtgraph
- seabreeze

Optional hardware-specific modules used by the original lab setup:
- `OSA_Thorlabs`
- `aravis`
- `thorpy.comm.discovery`

## Run

From this directory:
- `python experiment_master_gui.py`
- `python spectrometer_gui.py`

Historical wrapper filenames are no longer tracked. Run the canonical modules directly,
or keep private local aliases under `legacy/` if you still want the old names on this machine.

## Repository policy

- Measurement outputs (`*.npz`) are ignored by Git.
- Local runtime config (`manip_angle_config.txt`) is ignored by Git.
- The active modules were cleaned for usability, while preserving the underlying experiment logic.

## Notes

- The code appears to target a Python 3.7/3.8 era environment.
- The master/worker split is now explicit in naming: `experiment_master_gui.py` orchestrates the active worker GUIs, and `spectrometer_gui.py` is the only current `Spectro*` implementation.
- A few helper scripts still contain hard-coded legacy paths from the original Linux workstation.
