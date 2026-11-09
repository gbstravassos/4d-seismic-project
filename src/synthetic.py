"""Deterministic post-stack synthetic 4D data and exact coordinate ground truth.

Convention: monitor(t,x) = baseline(t - shift_monitor(t,x),x).
Positive shift means a monitor event occurs later. All times in seconds.
"""
from dataclasses import dataclass
import numpy as np


@dataclass(frozen=True)
class SyntheticConfig:
    nt: int = 1501
    nx: int = 32
    dt: float = 0.001
    peak_hz: float = 30.0
    seed: int = 20261025
    background_density: float = 0.025
    background_scale: float = 0.12


@dataclass
class SyntheticPair:
    baseline: np.ndarray  # time x traces
    monitor: np.ndarray
    reflectivity: np.ndarray
    time_s: np.ndarray
    trace_index: np.ndarray
    shift_monitor_s: np.ndarray  # evaluated at monitor time t
    shift_event_s: np.ndarray  # delay evaluated at baseline event time u
    baseline_to_monitor_s: np.ndarray  # g(u)=F^{-1}(u)
    valid_mask: np.ndarray  # excludes interpolation edges
    scenario: str
    config: SyntheticConfig


def ricker(peak_hz: float, dt: float, half_width_s: float = 0.08) -> np.ndarray:
    if peak_hz <= 0 or dt <= 0 or half_width_s <= 0:
        raise ValueError('Wavelet parameters must be positive')
    n = int(round(half_width_s / dt))
    tau = np.arange(-n, n + 1) * dt
    a = (np.pi * peak_hz * tau) ** 2
    return (1 - 2*a) * np.exp(-a)


def make_baseline(config: SyntheticConfig) -> tuple[np.ndarray, np.ndarray]:
    if config.nt < 3 or config.nx < 1 or config.dt <= 0 or not 0 <= config.background_density <= 1:
        raise ValueError('Invalid config dimensions, sample interval or density')
    rng = np.random.default_rng(config.seed)
    r = rng.normal(0.0, config.background_scale, size=(config.nt, config.nx))
    r *= rng.random(size=r.shape) < config.background_density
    # Deterministic gently dipping events, well inside the modeled time interval.
    for j in range(config.nx):
        for k, amp in ((220, 0.9), (440, -0.75), (710, 1.0), (1030, -0.65), (1250, 0.8)):
            idx = k + int(round(9*np.sin(2*np.pi*j/max(config.nx, 2)) + 0.27*j))
            if 0 <= idx < config.nt:
                r[idx, j] += amp
    wavelet = ricker(config.peak_hz, config.dt)
    b = np.column_stack([np.convolve(r[:, j], wavelet, mode='same') for j in range(config.nx)])
    return b, r


def constant_shift(config: SyntheticConfig, delay_ms: float) -> np.ndarray:
    return np.full((config.nt, config.nx), delay_ms * 1e-3, dtype=float)


def varying_shift(config: SyntheticConfig, amplitude_ms: float = 5.0) -> np.ndarray:
    """A smooth compact perturbation with shift=0 at time-grid endpoints.

    Approximate maximum strain is far below 1 for default settings.
    """
    t = np.arange(config.nt) * config.dt
    duration = t[-1]
    curve = (np.sin(np.pi * t / duration)**2) * np.sin(2*np.pi*t/duration)
    return np.broadcast_to((amplitude_ms*1e-3*curve)[:, None], (config.nt, config.nx)).copy()


def make_pair(config: SyntheticConfig, shift_monitor_s: np.ndarray, scenario: str = 'custom') -> SyntheticPair:
    """Resample via linear interpolation; out-of-domain monitor samples are NaN.

    F(t) = t - shift_monitor(t). Inverse mapping g(u) is calculated directly
    by interpolation of the strictly increasing F grid. The corresponding
    event shift is g(u)-u; out-of-domain event shifts are NaN.
    """
    b, r = make_baseline(config)
    t = np.arange(config.nt) * config.dt
    s = np.asarray(shift_monitor_s, dtype=float)
    if s.shape != b.shape or not np.all(np.isfinite(s)):
        raise ValueError('Shift must be finite with shape (nt, nx)')
    monitor = np.full_like(b, np.nan)
    inverse = np.full_like(b, np.nan)
    shift_event = np.full_like(b, np.nan)
    valid = np.zeros_like(b, dtype=bool)
    for j in range(config.nx):
        f = t - s[:, j]
        if np.any(np.diff(f) <= 0):
            raise ValueError('Nonmonotone mapping: event reversal/duplication possible')
        valid[:, j] = (f >= t[0]) & (f <= t[-1])
        monitor[valid[:, j], j] = np.interp(f[valid[:, j]], t, b[:, j])
        in_event_domain = (t >= f[0]) & (t <= f[-1])
        inverse[in_event_domain, j] = np.interp(t[in_event_domain], f, t)
        shift_event[in_event_domain, j] = inverse[in_event_domain, j] - t[in_event_domain]
    return SyntheticPair(b, monitor, r, t, np.arange(config.nx), s.copy(), shift_event,
                         inverse, valid, scenario, config)


def generate_experiments(config: SyntheticConfig = SyntheticConfig()) -> dict[str, SyntheticPair]:
    experiments = {'E0': make_pair(config, constant_shift(config, 0), 'E0_identical')}
    for value in (-8, -4, 0, 4, 8):
        label = f'E1_{value:+d}ms'
        experiments[label] = make_pair(config, constant_shift(config, value), label)
    experiments['E2'] = make_pair(config, varying_shift(config), 'E2_variable')
    return experiments
