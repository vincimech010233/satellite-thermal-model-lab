"""Synthetic lumped spacecraft thermal trade study with independent numerical checks."""

import argparse
import copy
import html
import json
import math
import sys
from pathlib import Path
import numpy as np
from scipy.integrate import solve_ivp, quad

SIGMA = 5.670374419e-8
UNITS = {
    "temperature": "K",
    "heat_capacity": "J/K",
    "conductance": "W/K",
    "area": "m2",
    "power": "W",
    "time": "s",
}
FIELDS = {
    "synthetic",
    "units",
    "capacity_J_per_K",
    "conductance_W_per_K",
    "area_m2",
    "emissivity",
    "initial_temperature_K",
    "environment_temperature_K",
    "internal_W",
    "sunlit_W",
    "eclipse_W",
    "orbital_period_s",
    "sunlit_fraction",
    "duration_s",
    "samples",
}


def scalar(x, name, lo, hi):
    if type(x) not in (int, float) or not math.isfinite(x) or not lo <= x <= hi:
        raise ValueError(f"invalid {name}")
    return float(x)


def vector(c, key, n, lo, hi):
    a = c[key]
    if not isinstance(a, list) or len(a) != n:
        raise ValueError(f"bad {key} shape")
    return np.array([scalar(x, key, lo, hi) for x in a])


def validate(c):
    if (
        not isinstance(c, dict)
        or set(c) != FIELDS
        or c["synthetic"] is not True
        or c["units"] != UNITS
    ):
        raise ValueError("restricted synthetic SI profile required")
    n = len(c["capacity_J_per_K"]) if isinstance(c["capacity_J_per_K"], list) else 0
    if not 1 <= n <= 6:
        raise ValueError("1..6 nodes required")
    cap = vector(c, "capacity_J_per_K", n, 10, 1e6)
    area = vector(c, "area_m2", n, 0, 1)
    eps = vector(c, "emissivity", n, 0, 1)
    initial = vector(c, "initial_temperature_K", n, 1, 500)
    internal = vector(c, "internal_W", n, 0, 200)
    sun = vector(c, "sunlit_W", n, 0, 200)
    eclipse = vector(c, "eclipse_W", n, 0, 200)
    g = c["conductance_W_per_K"]
    if (
        not isinstance(g, list)
        or len(g) != n
        or any(not isinstance(row, list) or len(row) != n for row in g)
    ):
        raise ValueError("conductance matrix shape")
    g = np.array([[scalar(x, "conductance", 0, 10) for x in row] for row in g])
    if (
        not np.allclose(g, g.T, rtol=0, atol=1e-12)
        or np.any(np.diag(g) != 0)
        or np.max(g.sum(axis=1) / cap) > 0.5
    ):
        raise ValueError("symmetric zero-diagonal bounded conductance required")
    env = scalar(c["environment_temperature_K"], "background temperature", 0, 400)
    period = scalar(c["orbital_period_s"], "period", 600, 12000)
    fraction = scalar(c["sunlit_fraction"], "sunlit fraction", 0, 1)
    duration = scalar(c["duration_s"], "duration", 1, 21600)
    if type(c["samples"]) is not int or not 10 <= c["samples"] <= 1000:
        raise ValueError("10..1000 output samples")
    return (
        cap,
        area,
        eps,
        initial,
        internal,
        sun,
        eclipse,
        g,
        env,
        period,
        fraction,
        duration,
    )


def simulate(c, max_step=60.0, rtol=1e-7, atol=1e-9):
    cap, area, eps, T, internal, sun, eclipse, g, env, period, fraction, duration = (
        validate(c)
    )
    scalar(max_step, "max step", 0.5, 300)
    scalar(rtol, "rtol", 1e-10, 1e-3)
    scalar(atol, "atol", 1e-12, 1e-3)
    boundaries = {0.0, duration}
    for k in range(int(duration / period) + 1):
        for t in [k * period, (k + fraction) * period]:
            if 0 < t < duration:
                boundaries.add(t)
    edges = sorted(boundaries)
    time = np.linspace(0, duration, c["samples"])
    temperatures = np.empty((len(cap), len(time)))
    coefficient = SIGMA * eps * area
    energy_integral = 0.0
    quad_error = 0.0
    calls = 0
    initial = T.copy()
    for start, end in zip(edges, edges[1:]):
        is_lit = ((start + end) / 2) % period < fraction * period
        power = internal + (sun if is_lit else eclipse)

        def radiation(temp):
            return coefficient * (env**4 - temp**4)

        def rhs(t, temp):
            nonlocal calls
            calls += 1
            if calls > 200000:
                raise ValueError("solver evaluation budget exceeded")
            if np.any(~np.isfinite(temp)) or np.any(temp <= 0) or np.any(temp > 1000):
                raise ValueError("temperature outside numerical model domain")
            return (power + radiation(temp) + g @ temp - g.sum(axis=1) * temp) / cap

        solution = solve_ivp(
            rhs,
            (start, end),
            T,
            method="RK45",
            rtol=rtol,
            atol=atol,
            max_step=max_step,
            dense_output=True,
        )
        if not solution.success:
            raise ValueError("solver failed: " + solution.message)
        mask = (time >= start) & (time <= end)
        temperatures[:, mask] = solution.sol(time[mask])
        T = solution.y[:, -1]
        # Independent adaptive quadrature of external net flux on dense temperature interpolants.
        integral, error = quad(
            lambda t: float(np.sum(power + radiation(solution.sol(t)))),
            start,
            end,
            epsabs=1e-6,
            epsrel=1e-8,
            limit=100,
        )
        energy_integral += integral
        quad_error += error
    if np.any(~np.isfinite(temperatures)) or np.any(temperatures <= 0):
        raise ValueError("invalid sampled temperatures")
    delta = float(np.dot(cap, T - initial))
    residual = delta - energy_integral
    return {
        "classification": "INFERRED",
        "synthetic": True,
        "profile": "lumped-thermal-v1",
        "config": c,
        "time_s": time.tolist(),
        "temperature_K": temperatures.tolist(),
        "final_temperature_K": T.tolist(),
        "energy": {
            "delta_stored_J": delta,
            "independent_net_external_integral_J": energy_integral,
            "residual_J": residual,
            "relative_residual": abs(residual)
            / max(1.0, abs(delta), abs(energy_integral)),
            "quadrature_error_estimate_J": quad_error,
        },
        "solver": {
            "method": "RK45 with segments split at heating discontinuities",
            "max_step_s": max_step,
            "rtol": rtol,
            "atol": atol,
            "rhs_evaluations": calls,
        },
        "limitations": "Synthetic absorbed heating and effective blackbody background; no orbital geometry, Earth view factors, radiation exchange between nodes, convection, temperature-dependent materials or physical calibration.",
    }


def trade_study(c):
    base = simulate(c)
    fine = simulate(c, max_step=30.0, rtol=1e-9, atol=1e-11)
    difference = float(
        np.max(
            np.abs(np.array(base["temperature_K"]) - np.array(fine["temperature_K"]))
        )
    )
    variants = {}
    for name, factor in [
        ("emissivity_minus_10pct", 0.9),
        ("emissivity_plus_10pct", 1.1),
    ]:
        v = copy.deepcopy(c)
        v["emissivity"] = [min(1.0, x * factor) for x in v["emissivity"]]
        s = simulate(v)
        variants[name] = {
            "actual_emissivity": v["emissivity"],
            "final_temperature_K": s["final_temperature_K"],
            "delta_final_K": (
                np.array(s["final_temperature_K"]) - base["final_temperature_K"]
            ).tolist(),
        }
    base["verification"] = {
        "classification": "OBSERVED",
        "max_temperature_difference_refined_K": difference,
        "refined_solver": fine["solver"],
        "energy_relative_tolerance": 1e-5,
        "temperature_convergence_tolerance_K": 1e-3,
        "passed": difference < 1e-3 and base["energy"]["relative_residual"] < 1e-5,
    }
    base["sensitivity"] = variants
    if not base["verification"]["passed"]:
        raise ValueError("numerical acceptance check failed")
    return base


def plot(report, out):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, 2, figsize=(11, 4), layout="constrained")
    time = np.array(report["time_s"]) / 3600
    for i, temperature in enumerate(report["temperature_K"]):
        axes[0].plot(time, temperature, label=f"Node {i + 1}")
    axes[0].set(
        xlabel="Synthetic elapsed time (h)",
        ylabel="Temperature (K)",
        title="Lumped transient / segmented heating",
    )
    axes[0].legend()
    axes[0].grid(alpha=0.25)
    for i in range(len(report["temperature_K"])):
        axes[1].plot(
            [-0.1, 0.1],
            [
                report["sensitivity"][name]["delta_final_K"][i]
                for name in ["emissivity_minus_10pct", "emissivity_plus_10pct"]
            ],
            marker="o",
            label=f"Node {i + 1}",
        )
    axes[1].set(
        xlabel="Requested emissivity fractional change",
        ylabel="Final temperature change (K)",
        title="Preliminary emissivity sensitivity",
    )
    axes[1].legend()
    axes[1].grid(alpha=0.25)
    fig.savefig(out, dpi=160)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input")
    parser.add_argument("output_dir")
    args = parser.parse_args()
    try:
        p = Path(args.input)
        if p.stat().st_size > 65536:
            raise ValueError("input exceeds 64 KiB")
        report = trade_study(json.loads(p.read_text()))
        out = Path(args.output_dir)
        out.mkdir(parents=True, exist_ok=True)
        plot(report, out / "thermal.png")
        (out / "report.json").write_text(
            json.dumps(report, indent=2, allow_nan=False) + "\n"
        )
        (out / "report.md").write_text(
            "# Satellite Thermal Model Lab\n\nINFERRED synthetic model; no physical digital-twin validation.\n\nFinal temperatures (K): "
            + str(report["final_temperature_K"])
            + "\n\nOBSERVED numerical checks: "
            + html.escape(str(report["verification"]))
            + "\n\nEnergy balance: "
            + html.escape(str(report["energy"]))
            + "\n\n"
            + report["limitations"]
            + "\n\n![Executed trade study](thermal.png)\n"
        )
    except (
        ValueError,
        TypeError,
        KeyError,
        OSError,
        OverflowError,
        FloatingPointError,
    ) as e:
        print(e, file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
