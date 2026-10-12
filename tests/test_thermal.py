import json
import sys
import unittest
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from thermal import simulate, trade_study, SIGMA


class ThermalTests(unittest.TestCase):
    def base(self, n=1):
        c = json.loads(Path("examples/satellite.json").read_text())
        c.update(
            capacity_J_per_K=[100.0] * n,
            conductance_W_per_K=[[0.0] * n for _ in range(n)],
            area_m2=[0.1] * n,
            emissivity=[0.0] * n,
            initial_temperature_K=[300.0] * n,
            internal_W=[0.0] * n,
            sunlit_W=[0.0] * n,
            eclipse_W=[0.0] * n,
            environment_temperature_K=0.0,
            sunlit_fraction=0.0,
            duration_s=100.0,
            samples=101,
        )
        return c

    def test_linear_heating(self):
        c = self.base()
        c["internal_W"] = [10.0]
        r = simulate(c)
        expected = 300 + np.array(r["time_s"]) * 0.1
        self.assertLess(
            float(np.max(np.abs(np.array(r["temperature_K"][0]) - expected))), 1e-8
        )
        self.assertLess(abs(r["energy"]["residual_J"]), 1e-6)

    def test_isolated_conduction(self):
        c = self.base(2)
        c.update(
            conductance_W_per_K=[[0.0, 0.2], [0.2, 0.0]],
            initial_temperature_K=[320.0, 280.0],
        )
        r = simulate(c)
        t = np.array(r["time_s"])
        expected = 300 + 20 * np.exp(-0.004 * t)
        self.assertLess(
            float(np.max(abs(np.array(r["temperature_K"][0]) - expected))), 1e-5
        )
        self.assertLess(abs(r["energy"]["delta_stored_J"]), 1e-6)

    def test_radiative_cooling_reference(self):
        c = self.base()
        c["emissivity"] = [1.0]
        r = simulate(c, max_step=5.0)
        t = np.array(r["time_s"])
        expected = (300.0**-3 + 3 * SIGMA * 0.1 / 100 * t) ** (-1 / 3)
        self.assertLess(
            float(np.max(abs(np.array(r["temperature_K"][0]) - expected))), 1e-5
        )

    def test_radiative_equilibrium(self):
        c = self.base()
        c.update(emissivity=[0.8], environment_temperature_K=3.0, internal_W=[5.0])
        eq = (5 / (SIGMA * 0.8 * 0.1) + 3**4) ** 0.25
        c["initial_temperature_K"] = [eq]
        r = simulate(c)
        self.assertLess(float(np.max(abs(np.array(r["temperature_K"]) - eq))), 1e-8)

    def test_segmented_heating_integral(self):
        c = self.base()
        c.update(
            duration_s=1200.0,
            orbital_period_s=600.0,
            sunlit_fraction=0.5,
            sunlit_W=[2.0],
        )
        r = simulate(c)
        self.assertAlmostEqual(r["energy"]["delta_stored_J"], 1200.0, places=6)
        self.assertAlmostEqual(r["final_temperature_K"][0], 312.0, places=7)

    def test_convergence_energy_and_sensitivity(self):
        c = json.loads(Path("examples/satellite.json").read_text())
        r = trade_study(c)
        self.assertTrue(r["verification"]["passed"])
        self.assertLess(r["verification"]["max_temperature_difference_refined_K"], 2e-4)
        self.assertLess(r["energy"]["relative_residual"], 1e-6)
        self.assertGreater(
            r["sensitivity"]["emissivity_minus_10pct"]["delta_final_K"][0], 0.0
        )

    def test_invalid(self):
        for key, value in [
            ("capacity_J_per_K", [0.0]),
            ("emissivity", [1.1]),
            ("duration_s", 0),
            ("samples", 5000),
            ("initial_temperature_K", [True]),
        ]:
            c = self.base()
            c[key] = value
            with self.assertRaises(ValueError):
                simulate(c)
        c = self.base(2)
        c["conductance_W_per_K"] = [[0.0, 1.0], [0.0, 0.0]]
        with self.assertRaises(ValueError):
            simulate(c)

    def test_reproducible(self):
        c = self.base()
        self.assertEqual(simulate(c), simulate(c))


if __name__ == "__main__":
    unittest.main()
