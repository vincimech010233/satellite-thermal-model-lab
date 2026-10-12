# Satellite Thermal Model Lab

INFERRED synthetic model; no physical digital-twin validation.

Final temperatures (K): [242.51147742497034, 225.64381277220764]

OBSERVED numerical checks: {&#x27;classification&#x27;: &#x27;OBSERVED&#x27;, &#x27;max_temperature_difference_refined_K&#x27;: 1.7074285096896347e-08, &#x27;refined_solver&#x27;: {&#x27;method&#x27;: &#x27;RK45 with segments split at heating discontinuities&#x27;, &#x27;max_step_s&#x27;: 30.0, &#x27;rtol&#x27;: 1e-09, &#x27;atol&#x27;: 1e-11, &#x27;rhs_evaluations&#x27;: 2252}, &#x27;energy_relative_tolerance&#x27;: 1e-05, &#x27;temperature_convergence_tolerance_K&#x27;: 0.001, &#x27;passed&#x27;: True}

Energy balance: {&#x27;delta_stored_J&#x27;: -36615.4987330733, &#x27;independent_net_external_integral_J&#x27;: -36615.49873341993, &#x27;residual_J&#x27;: 3.466338966973126e-07, &#x27;relative_residual&#x27;: 9.466862631613719e-12, &#x27;quadrature_error_estimate_J&#x27;: 5.318166657951296e-09}

Synthetic absorbed heating and effective blackbody background; no orbital geometry, Earth view factors, radiation exchange between nodes, convection, temperature-dependent materials or physical calibration.

![Executed trade study](thermal.png)
