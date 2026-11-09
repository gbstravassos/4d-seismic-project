# 4D seismic time-shift benchmark

Research project comparing cross-correlation and constrained DTW against independently defined synthetic ground truth. **Current status: milestone 2 — synthetic data only (E0–E2); no shift estimator has been implemented.** See [PROJECT.md](PROJECT.md) for scientific scope and acceptance gates.

## Setup and run

Use Python 3.10+:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
jupyter lab notebooks/01_synthetic_data.ipynb
```

Run the notebook with the project root as your working directory, or navigate to `notebooks/` (both are supported). `outputs/figures/` contains example figures. The notebook has already been executed with Python 3.

## Scientific definition

- `baseline` and `monitor` are `(nt, nx)` arrays; time is the first axis.
- `dt` and all shift arrays use **seconds**, while plots often display **milliseconds**.
- Positive time shift means the monitor event is **later**.
- Forward mapping: `monitor(t) = baseline(t - shift_monitor(t))`, linear interpolation.
- `F(t) = t - shift_monitor(t)` must be strictly increasing.
- Event delay **in baseline-event coordinates**: `shift_event(u) = inverse(F)(u) - u`.
- Out-of-domain samples are explicitly `NaN`, with a `valid_mask` for monitor resampling. Inverse-domain validity is indicated by finite values of `shift_event_s`.
- No physical inversion or velocity-change attribution is supported by this generator.

## Files

- `src/synthetic.py` — reproducible Ricker/reflectivity simulator, zero/constant/variable shifts, inverse ground truth.
- `tests/test_synthetic.py` — identity, sign and ±4ms samples, seed reproducibility, inverse-coordinate identity, monotonicity, scenarios.
- `notebooks/01_synthetic_data.ipynb` — inspected examples E0–E2.
- `outputs/figures` — notebook-generated QC figures.
- `docs/decisions.md` — methodological choices.

## Reproducibility

Defaults: `nt=1501`, `nx=32`, `dt=0.001 s`, peak Ricker frequency `30 Hz`, seed `20261025`. The initial E1 delays are `-8,-4,0,+4,+8 ms`; E2 uses a smooth oscillatory delay vanishing at time bounds. Background reflectivity is randomized with the recorded seed; main reflector horizons are deterministic. **These are not field data.**

## Limitations / next steps

E0–E2 currently have no observational noise, wavelet mismatch, acquisition artifacts, or physically derived reservoir changes. Local time strain is a derivative of synthetic delay, not a measured reservoir property. Add independently tested CC/DTW estimators next, then more challenging E3–E7 scenarios; no preferential method has been selected.
