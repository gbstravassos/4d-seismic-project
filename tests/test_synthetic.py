import unittest
import numpy as np
from src.synthetic import SyntheticConfig, constant_shift, varying_shift, make_baseline, make_pair, generate_experiments, ricker


class TestSynthetic(unittest.TestCase):
    def setUp(self):
        self.cfg = SyntheticConfig(nt=1501, nx=5)

    def test_zero_shift_exact(self):
        pair = make_pair(self.cfg, constant_shift(self.cfg, 0))
        np.testing.assert_array_equal(pair.monitor, pair.baseline)
        np.testing.assert_array_equal(pair.shift_event_s, 0.0)
        self.assertTrue(pair.valid_mask.all())

    def test_positive_negative_four_ms(self):
        for ms in (-4, 4):
            pair = make_pair(self.cfg, constant_shift(self.cfg, ms))
            delta = int(ms / (self.cfg.dt * 1000))
            # Shift at integer samples must be exact away from the edges.
            np.testing.assert_allclose(pair.monitor[20:-20], np.roll(pair.baseline, delta, axis=0)[20:-20], atol=1e-10)
            np.testing.assert_allclose(pair.shift_event_s[20:-20], ms / 1000, atol=1e-12)
            self.assertTrue(np.all(np.diff(pair.baseline_to_monitor_s[20:-20], axis=0) > 0))

    def test_reproducible(self):
        p = make_pair(self.cfg, varying_shift(self.cfg))
        q = make_pair(self.cfg, varying_shift(self.cfg))
        np.testing.assert_array_equal(p.baseline, q.baseline)
        np.testing.assert_array_equal(p.monitor, q.monitor)
        self.assertFalse(np.array_equal(p.baseline, make_baseline(SyntheticConfig(nt=1501, nx=5, seed=44))[0]))

    def test_variable_mapping_coordinate_identity(self):
        pair = make_pair(self.cfg, varying_shift(self.cfg))
        for j in range(self.cfg.nx):
            t = pair.time_s
            valid = np.isfinite(pair.baseline_to_monitor_s[:, j])
            g = pair.baseline_to_monitor_s[valid, j]
            f_at_g = np.interp(g, t, t - pair.shift_monitor_s[:, j])
            np.testing.assert_allclose(f_at_g, t[valid], atol=1e-12)
            np.testing.assert_allclose(pair.shift_event_s[valid, j], g - t[valid], atol=1e-12)
            self.assertTrue(np.all(np.diff(t - pair.shift_monitor_s[:, j]) > 0))

    def test_reject_nonmonotone(self):
        s = constant_shift(self.cfg, 0)
        s[100, :] = 0.020
        with self.assertRaises(ValueError):
            make_pair(self.cfg, s)

    def test_scenario_set_and_wavelet(self):
        keys = generate_experiments(self.cfg)
        self.assertEqual(len(keys), 7)
        self.assertEqual(ricker(30, 0.001).size % 2, 1)


if __name__ == '__main__':
    unittest.main()
