# Critical review — Satellite Thermal Model Lab

Reviewer: separate same-model agent, not an independent model or external audit. Scope: bounded synthetic lumped-node physics, analytic references, integration/conservation checks and generated artifacts. No flight, spacecraft correspondence or physical digital-twin validation.

VERIFIED: **VALIDATED_LOCAL** for `docs/ACCEPTANCE.md`. No critical numerical defect was found in executed bounded cases. Manual publication still requires final repository/privacy/artifact checks. The gate establishes numerical behavior under stated assumptions, not engineering certification.

## Independently executed evidence

OBSERVED: `OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 MPLBACKEND=Agg .venv/bin/python -m unittest discover -s tests -v` passed eight tests. Ruff check/format passed via `../portfolio-delivery-20261012/.venv/bin/ruff`; `.venv/bin/pip check` passed. Tests cover linear heating, conductive relaxation, radiative cooling/equilibrium, heating discontinuities, energy/refinement, malformed inputs and reproducibility.

VERIFIED: extra analytic partial-orbit cases with no radiation/conduction matched hand energy totals at sunlit fractions 0, 0.37 and 1: 500, 1166 and 2000 J, with final temperatures 305, 311.66 and 320 K. Unequal-capacity conductive relaxation matched the capacity-weighted equilibrium/exponential reference within 1.13e-5 K; total stored-energy change was about -2.27e-13 J. Inputs/reports and observations remain in `results/reviewer-fixtures/`.

OBSERVED: actual fixture report gives final temperatures approximately 242.5115 and 225.6438 K, relative energy residual 9.47e-12 and maximum sampled-grid temperature difference against refinement 1.71e-8 K. The executable tests reproduced passing numerical criteria. Reviewer independently inspected actual `results/thermal.png`: readable time/temperature units, both node curves and labeled emissivity sensitivity; no fabricated screenshot or physical validation claim.

## Critical interpretation and method boundaries

VERIFIED by source inspection: heating changes are segmented exactly; each interval uses a constant supplied absorbed-power regime. Conductive links are nonnegative, zero-diagonal and symmetric within a stated numerical tolerance, so internal transfer cancels in total energy. Radiative term uses absolute Kelvin temperatures and effective blackbody background. Strict SI fields, node/sample/time bounds and evaluation budget reject unsupported configurations; no orbital geometry or Earth view factors are inferred.

The energy quadrature uses a distinct adaptive integration routine **on the same dense numerical temperature trajectory**. It checks consistency between external-flux integration and stored-energy change; it is not an independent dynamics solution or physical measurement. Quadrature error estimates are reported, not proven error bounds. Refinement compares tighter RK45 settings on the same output grid and does not establish a rigorous whole-trajectory error bound. The three emissivity runs are trade sensitivities, not calibrated mission uncertainty; refined verification applies to the base run.

The current fixture satisfies stated tolerances, analytical cases constrain major sign/unit errors, and synthetic repetition is deterministic. These checks do not cover all permitted extreme parameter combinations or solver-warning/failure paths. Temperature/capacity bounds are numerical domain restrictions, not claims about material applicability. The RHS budget applies per simulation; a trade study runs multiple simulations.

Minor visualization follow-up: x-axis emissivity perturbations are requested ±10% values; clipping can reduce actual changes at emissivity bounds. Reports retain actual emissivities. Labeling the axis as requested fractional change would make this distinction clearer if boundary configurations are plotted.

## Value, security and provenance

INFERRED: transparent numerical checks and preliminary trade studies offer credible educational/portfolio value. Research acknowledges broader thermal-network tools and primary numerical/spacecraft context; no unique-method, mission-performance or digital-twin claim is accepted. Real loads, geometry, properties and physical correspondence remain NOT_VERIFIED.

VERIFIED by inspection: synthetic profile, bounded CPU-only arrays, no remote computation, personal datasets or host monitoring. JSON binds full configuration, solver settings, residuals and sensitivity values. MIT license, runtime lockfiles, dependency license metadata and OSV results are present. Empty advisory results do not establish vulnerability absence; exhaustive legal/supply-chain review and authorship beyond supplied provenance remain NOT_VERIFIED. CI requires standard public packages without credentials; hosted execution is NOT_VERIFIED.

Follow-up: preserve analytical/energy references when expanding geometry or material models, and obtain physical comparison evidence before adopting a digital-twin or flight-use claim.
