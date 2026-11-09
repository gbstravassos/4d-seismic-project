# Project specification — Quantification of 4D seismic time shifts

**Status:** v0.1 — specification baseline (2026-10-25)  
**Primary deliverable:** a reproducible, physically interpretable comparison of windowed cross-correlation (CC) and dynamic time warping (DTW) for synthetic baseline/monitor seismic traces, with known ground-truth shifts.

## 1. Scientific question

Under which combinations of time shift, noise, wavelet mismatch, amplitude mismatch, and lateral/vertical variability can CC and constrained DTW reliably recover a known 4D time-shift field? When can a recovered time shift be interpreted as a change in seismic propagation time rather than a processing or acquisition artifact?

## 2. Scope

**In scope (first release):** synthetic 1D traces and 2D post-stack sections; exact ground truth; CC with sliding windows; DTW with explicit lag and local-strain constraints; confidence/QC masks; quantitative metrics; repeatable plots and tests.

**Out of scope (first release):** real field data, SEG-Y ingestion, inversion for pressure/saturation, 3D/4D prestack processing, full 4D cross-equalization, elastic/poroelastic reservoir modeling, quantitative inference of reservoir changes directly from time shifts.

A later phase may add real baseline/monitor sections only after the synthetic benchmarks pass.

## 3. Definitions and conventions

Let `b(t,x)` be the baseline and `m(t,x)` the monitor, for two-way time `t` (seconds or milliseconds as explicitly stated) and trace coordinate `x`.

**Sign convention:** a positive `Δt(t,x)` means the corresponding monitor event arrives *later* than the baseline event. For a synthetic pure delay, define

`m(t,x) = b(t - Δt_true(t,x), x) + ε(t,x)`.

For nonconstant shifts, this definition is a forward resampling model: a monitor sample at `t` corresponds to a baseline sample at `t - Δt_true(t,x)`. Consequently, if an estimator measures monitor arrival-time delay as a function of the *baseline* event time `u`, its exact reference field is `Δt_event(u,x) = F_x^{-1}(u) - u`, where `F_x(t) = t - Δt_true(t,x)`; compare estimators only after mapping them onto a common time coordinate. For small smoothly varying shifts, this distinction is small but should not be silently ignored.

**Time strain:** `ε_t(t,x) = ∂Δt(t,x)/∂t`, dimensionless. Estimate only within accepted signal/QC zones; document derivative method and regularization. Time strain is *not* automatically an interval velocity change or mechanical strain. Under strongly simplifying assumptions of a fixed raypath, unchanged thickness, and small perturbation of propagation velocity, a local relative velocity perturbation is approximately `δv/v ≈ -ε_t` (with the specific time coordinate and assumptions stated). Do not use this approximation for reservoir attribution without more evidence.

**Sampling:** constant two-way-time interval `dt` for baseline and monitor; all time shifts and tolerances in milliseconds in reports. No silent interpolation onto a different grid.

**Shift domain:** default central zone excludes convolution/resampling edge artifacts and noisy/no-signal samples.

## 4. Data generation and ground truth

1. Use a deterministic random seed, archived in experiment metadata.
2. Generate a reflectivity series with sparse deterministic interfaces plus optional random background reflectivity.
3. Convolve with a documented Ricker wavelet (same initial wavelet for the baseline and monitor).
4. Produce monitor data with known constant delays and later smoothly varying shift fields, using interpolation with a stated order and boundary policy.
5. Perturb one factor at a time (additive noise, amplitude scale, spectral/wavelet discrepancy, spatial variability), then selected combinations.
6. Store `baseline`, `monitor`, the true mapping, `dt`, `x`, random seeds, and masks separately. Never infer ground truth from an estimated shift.

**Recommended initial settings (proposals, to be tested):** `dt=1 ms`, `nt=1501` (1.5 s), `nx=32`, Ricker peak frequency `30 Hz`, synthetic reference shift `+4 ms`, max evaluated shift `±16 ms`, and three CC window lengths around `80/160/240 ms`. Parameters are not universal optimal settings.

## 5. Experiment matrix

| ID | Scenario | Primary purpose |
|---|---|---|
| E0 | Identical baseline and monitor | Verify zero-lag and near-zero error |
| E1 | Constant shifts of −8, −4, 0, +4, +8 ms; no noise | Verify sign convention, delay recovery, and method bias |
| E2 | Smoothly time-varying delay; no noise | Test local-shift reconstruction and time-strain |
| E3 | E2 with multiple reproducible noise levels | Characterize robustness and confidence masking |
| E4 | E2 with common amplitude scaling | Test gain invariance and effects of normalization |
| E5 | E2 with wavelet/bandwidth mismatch | Identify nonrepeatability-related artifacts |
| E6 | A laterally variable 2D shift field | Check spatial continuity and bias |
| E7 | No physical shift but waveform mismatch and noise | Measure false-positive shift estimates |

E0–E2 are mandatory gates before attempting the more realistic perturbations.

## 6. Methods and controls

### Windowed cross-correlation

- State explicitly whether baseline is shifted relative to monitor or vice versa.
- Compute normalized CC in sliding, tapered windows, with bounded lag search.
- Use parabolic/subsample peak refinement where supported, and retain peak correlation as a confidence measure.
- Report window length and stride; exclude invalid edge windows.

### Constrained DTW

- Document pointwise misfit, admissible time-lag band, allowed path increments/local strain, interpolation and smoothing.
- A lag bound by itself is **not** a local-strain bound. If the implementation uses approximate strain regularization rather than a hard constraint, label it accurately.
- Produce raw and, if used, regularized shift fields; publish the regularization parameters.
- Check that mapping is monotone and that no event duplication/reversal is introduced by the resampling convention.

### Common comparisons

Use exactly the same baseline, monitor, ground truth, region of interest, time grid, and QC masks for all methods. Test methods on hold-out synthetic seeds rather than tuning and reporting on the same realization only.

## 7. Quantitative metrics

For errors `e_i = Δt_est,i - Δt_true,i` on a common valid mask:

- **Shift RMSE (ms):** `sqrt(mean(e_i^2))`.
- **Shift bias (ms):** `mean(e_i)`.
- **Shift MAE (ms):** `mean(abs(e_i))`.
- **Time-strain RMSE:** same formula on estimated versus true derivatives; mask boundaries and samples affected by smoothing.
- **NRMS (%):** for comparable traces/windows, `200 * RMS(m-b) / (RMS(m)+RMS(b))`; specify whether pre- or post-alignment and any gain normalization were applied. A low post-warp NRMS alone does not validate the physical shift estimate.
- **False positives:** nonzero shift magnitudes on E0/E7, summarized by RMSE and 95th percentile absolute shift.
- **Computational cost:** wall-clock timing with environment and array dimensions recorded (illustrative, hardware-dependent).

Report both median and spread across repeated seeds for noisy experiments and include plots of recovered versus true shifts.

## 8. Minimum acceptance criteria (project gates)

These are **provisional engineering criteria**, not statements about expected scientific performance:

- **Reproducibility:** same configuration and seed reproduce identical arrays and metrics (within declared numerical tolerances).
- **E0:** CC and DTW return absolute shift error ≤ 0.5 ms in evaluated, high-signal zones; any failure triggers diagnosis before moving on.
- **E1:** after subsample estimation on the 1 ms grid, CC recovers all five constant shifts with RMSE ≤ 1.0 ms over accepted zones; DTW should satisfy the same test before comparisons are reported.
- **E2:** compare CC/DTW against known ground truth, with no a-priori assumption that DTW is superior; publish RMSE, bias and time-strain error before selecting a preferred method.
- **E7:** explicitly measure spurious shifts; never equate improved waveform match to a confirmed physical change.
- **Documentation:** report the exact data generator, parameters, seeds, source commit, masks and environment in each experiment.

Failure of a gate is an analysis result, not permission to alter the truth data or hide unfavorable traces.

## 9. Project structure and milestones

```text
README.md
PROJECT.md
requirements.txt
src/
  synthetic.py
  cross_correlation.py
  dtw.py
tests/
notebooks/
  01_synthetic_data.ipynb
  02_cross_correlation.ipynb
  03_dtw.ipynb
docs/
  methodology.md
  decisions.md
  ai_workflow.md
outputs/
  figures/
```

**Milestone 1 — specification (this file):** approve scientific question, shift sign/coordinates, baseline experiment, validation gates.  
**Milestone 2 — synthetic generator:** deterministic `src/synthetic.py`, E0/E1/E2 datasets, figures, and unit tests.  
**Milestone 3 — CC:** windowed CC, E0–E2 metrics, QC and tests.  
**Milestone 4 — DTW:** constrained DTW, E0–E2 metrics, QC and tests.  
**Milestone 5 — robustness:** E3–E7 parameter sweeps, method comparison and failure modes.  
**Milestone 6 — report:** technical synthesis, interpretation limits, reproducible run instructions; optionally scope real-data extension.

## 10. Division of work: researcher and generative AI

**Researcher retains:** physical interpretation, assumptions, validity domains, sign convention, pass/fail thresholds, methodology decisions and claims of scientific significance.

**AI may implement under review:** data generation, initial code, tests, documentation, QC plots, metrics, refactoring and experiment runners. Verification relies on independent synthetic ground truth, invariants, code review of critical operations, and comparison with an alternative method—not blind acceptance of generated outputs.

## 11. Immediate next task

Implement `src/synthetic.py` and notebook `01_synthetic_data.ipynb` for E0/E1/E2 with deterministic seeds. **Before** writing CC or DTW, inspect plots for (a) correct temporal polarity of delayed events, (b) unchanged amplitudes in E1 away from interpolation/edge artifacts, and (c) monotone mapping for E2. Add unit tests for zero delay, ±4 ms delay, reproducibility, and time-coordinate transformations.
