# Decision log

## D001 — Start with synthetic post-stack data
- Date: 2026-10-25
- Decision: Generate deterministic synthetic baseline/monitor data before using field data.
- Reason: Synthetic ground truth permits direct bias/RMSE evaluation and controlled failure analysis.
- Revisit when: E0–E2 and the later robustness tests pass, and field data access/provenance is established.

## D002 — Positive time shift means monitor is later
- Date: 2026-10-25
- Decision: Positive `Δt` denotes a delayed monitor event compared with the corresponding baseline event.
- Caveat: Coordinate mappings must be made explicit for time-dependent shifts (see PROJECT.md).

## D003 — No preferred method in advance
- Date: 2026-10-25
- Decision: Compare CC and constrained DTW using identical masks and known ground truth, without presuming DTW is better.

## D004 — Linear forward interpolation and NaN boundaries
- Date: 2026-10-25
- Decision: Interpolate the monitor from baseline samples at `F(t)=t-shift_monitor(t)`; retain NaNs outside baseline temporal support and explicit validity masks.
- Reason: Do not silently introduce artificial zero-amplitude boundary samples.

## D005 — Ground truth in both coordinates
- Date: 2026-10-25
- Decision: Store `shift_monitor_s` and inverse-derived `shift_event_s` separately.
- Reason: For nonconstant shift these are different functions of their respective time coordinates, critical for unbiased algorithm comparisons.
