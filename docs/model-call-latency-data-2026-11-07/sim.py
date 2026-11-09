"""Stage 3: offline comparison of policies A (Terra first) and B(k) (Luna up to k repairs, then Terra).

Inputs are the recorded runs only; no model calls. Pre-registered rule is applied at the end.
"""
import json
import random

S = "/private/tmp/claude-501/-Users-atsushi-Desktop-projects-personal-pals--claude-worktrees-stacks-project-formalization-d2e49f/9390b54e-2180-4b94-830a-27ee4874a1c1/scratchpad/out/"
LUNA_USD, TERRA_USD = 0.0074, 0.0497  # per run, from the 2026-11-03 doc (0.265/36, 0.596/12)

# Terra's 12 cards (Terra medium, from docs 47a397e): id -> (verified, repairs, seconds)
terra_t = {
    "ftc_point_spike": (1, 1, 184), "orientation": (1, 0, 233), "lagrange": (0, 6, 471),
    "limit_order": (1, 0, 86), "geometric_boundary": (1, 1, 146), "kernel_zero": (1, 0, 220),
    "id_zero": (1, 1, 141), "composite": (1, 1, 151), "right_inverse": (1, 0, 78),
    "basis": (1, 0, 98), "gradient": (1, 4, 461), "two_sided": (1, 0, 139),
}
key = {
    "calculus_supp_v5_ftc_point_spike_counterexample": "ftc_point_spike",
    "mv_line_supp_v5_orientation_counterexample": "orientation",
    "mv_foundation_lagrange_multiplier_from_direction": "lagrange",
    "calculus_v3_limit_order": "limit_order",
    "calculus_supp_v3_geometric_boundary_counterexample": "geometric_boundary",
    "la_reuse_kernel_detects_zero": "kernel_zero",
    "commalg_modules_exact_id_zero": "id_zero",
    "la_v6_nonzero_maps_zero_composite": "composite",
    "la_reuse_right_inverse_surjective": "right_inverse",
    "la_v6_basis_recognition": "basis",
    "calculus_v4_gradient_direction_bound": "gradient",
    "calculus_v5_two_sided_limit_characterization": "two_sided",
}
luna_t = {}
for l in open(S + "s1a-luna-on-terra12.jsonl"):
    r = json.loads(l)
    luna_t[key[r["problem"]]] = (int(r["state"] == "verified"), r["repairs_used"], r["elapsed_seconds"])

# Luna's 12 cards (Luna low, from docs 47a397e, baseline arm): (verified, repairs, seconds)
luna_l = {
    "second_derivative_minimum": (0, 6, 961), "exceptional_section": (0, 6, 663),
    "fredholm": (0, 6, 716), "absolute_section": (0, 6, 880), "nondiff_minimum": (0, 6, 900),
    "clopen": (0, 6, 690), "rect_det": (1, 1, 411), "polarization": (1, 2, 258),
    "distinct_eigen": (1, 1, 220), "exact_seq": (1, 0, 199), "integral_scalar": (1, 1, 169),
    "convex_derivative": (1, 3, 320),
}
key2 = {
    "calculus_v5_second_derivative_minimum": "second_derivative_minimum",
    "mv_foundation_exceptional_section_counterexample": "exceptional_section",
    "la_v6_fredholm_solvability": "fredholm", "mv_v5_absolute_section_criterion": "absolute_section",
    "mv_foundation_nondifferentiable_minimum": "nondiff_minimum",
    "commalg_v4_clopen_unique_idempotent": "clopen", "la_v6_rectangular_determinant_transfer": "rect_det",
    "la_v3_polarization": "polarization", "la_v2_distinct_eigenspaces_intersection": "distinct_eigen",
    "la_reuse_exact_sequence_zero_composite": "exact_seq",
    "calculus_v2_integral_scalar_linearity": "integral_scalar",
    "calculus_v5_convex_derivative_monotone": "convex_derivative",
}
terra_l = {}
for f in ("s1b-terra-on-luna12.jsonl", "s1b2-terra-rerun-api-errors.jsonl", "s1b3-terra-rerun-api-errors2.jsonl"):
    for l in open(S + f):
        r = json.loads(l)
        if f == "s1b-terra-on-luna12.jsonl" and r["termination_reason"] == "repair_route_selection_failed":
            continue  # API-error aborts, rerun below
        terra_l[key2[r["problem"]]] = (int(r["state"] == "verified"), r["repairs_used"], r["elapsed_seconds"])

cards = [(k, luna_t[k], terra_t[k]) for k in terra_t] + [(k, luna_l[k], terra_l[k]) for k in luna_l]
assert len(cards) == 24


def policy_A(luna, terra):
    return terra[2], terra[0], TERRA_USD


def policy_B(k):
    def f(luna, terra):
        ok, rep, sec = luna
        if ok and rep <= k:
            return sec, 1, LUNA_USD
        # Luna time up to the (k+1)-th generation attempt; proportional approximation
        wasted = sec * (k + 1) / (rep + 1) if rep + 1 > k + 1 else sec
        return wasted + terra[2], terra[0], LUNA_USD + TERRA_USD
    return f


policies = {"A: Terra first": policy_A, "B(k=2)": policy_B(2), "B(k=3)": policy_B(3)}
res = {n: [p(l, t) for _, l, t in cards] for n, p in policies.items()}
print(f"Luna success {sum(l[0] for _,l,_ in cards)}/24, Terra success {sum(t[0] for _,_,t in cards)}/24")
for n, rs in res.items():
    print(f"{n:16s} time/card {sum(r[0] for r in rs)/24:7.1f}s  success {sum(r[1] for r in rs):2d}/24  cost/card ${sum(r[2] for r in rs)/24:.3f}")

random.seed(0)
a = [r[0] for r in res["A: Terra first"]]
for n in ("B(k=2)", "B(k=3)"):
    b = [r[0] for r in res[n]]
    diffs = [x - y for x, y in zip(a, b)]  # >0 means B is faster
    boots = []
    for _ in range(10000):
        s = [random.choice(diffs) for _ in diffs]
        boots.append(sum(s) / len(s))
    boots.sort()
    print(f"A - {n}: mean {sum(diffs)/24:6.1f}s  95% CI [{boots[250]:.1f}, {boots[9750]:.1f}]")
