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

Legacy modules kept only as historical references:
- `spectrometer_gui_legacy_v1.py`
- `spectrometer_gui_legacy_v2.py`
- `spectrum_fit_dialog_legacy.py`

Legacy compatibility wrappers kept in place:
- `programme_angle_3.py` -> `experiment_master_gui.py`
- `combined_experiment_gui.py` -> `experiment_master_gui.py`
- `Spectro31.py` -> `spectrometer_gui.py`
- `Spectro2.py` -> `spectrometer_gui_legacy_v2.py`
- `Spectro1.py` -> `spectrometer_gui_legacy_v1.py`
- `Spectro_fit2.py` -> `spectrum_fit_dialog.py`
- `Spectro_fit.py` -> `spectrum_fit_dialog_legacy.py`
- `Camera1.py` -> `camera_gui.py`
- `Rotation1.py` -> `rotation_gui.py`
- `BandDiag2.py` -> `band_diagram_analysis.py`
- `filtre_camera.py` -> `camera_filter_analysis.py`

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

Legacy names still work:
- `python combined_experiment_gui.py`
- `python programme_angle_3.py`
- `python Spectro31.py`

## Repository policy

- Measurement outputs (`*.npz`) are ignored by Git.
- Local runtime config (`manip_angle_config.txt`) is ignored by Git.
- This is a direct legacy import; no code modernization was applied yet.

## Notes

- The code appears to target a Python 3.7/3.8 era environment.
- The master/worker split is now explicit in naming: `experiment_master_gui.py` orchestrates the active worker GUIs, and `spectrometer_gui.py` is the only current `Spectro*` implementation.
- A few helper scripts still contain hard-coded legacy paths from the original Linux workstation.
