| 実行 | 題数 | 検証済み | 初回成功 | ≤10 s | ≤30 s | 回答まで ≤10 s | 検証 p50/p90 | 回答 p50/p90 | $/題 | 高速経路の結果 | 負荷(開始平均) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| du_base | 20 | 19 | 6 | 0 | 1 | 0 | 82.2/120.5 | 96.1/140.5 | 0.0452 | - | 5.9 |
| du_off | 20 | 20 | 10 | 3 | 11 | 1 | 29.8/112.3 | 33.7/121.1 | 0.0326 | - | 9.2 |
| du_cf_low | 20 | 20 | 13 | 7 | 14 | 0 | 12.5/123.1 | 21.3/135.9 | 0.0167 | - | 4.9 |
| du_cf_none | 20 | 20 | 7 | 6 | 13 | 0 | 26.4/141.5 | 34.7/145.8 | 0.0239 | - | 17.3 |
| du_cf_none_xn | 20 | 20 | 8 | 7 | 11 | 1 | 28.2/121.1 | 39.1/127.0 | 0.0210 | - | 6.3 |
| tu_base | 14 | 13 | 10 | 0 | 2 | 0 | 53.8/203.8 | 69.5/216.3 | 0.0546 | - | 5.3 |
| tu_off | 14 | 13 | 12 | 5 | 12 | 0 | 14.5/23.6 | 21.4/27.4 | 0.0518 | - | 5.8 |
| tu_cf_low | 14 | 14 | 11 | 5 | 11 | 0 | 12.6/70.2 | 20.3/79.8 | 0.0270 | - | 4.7 |
| tu_cf_none_xn | 14 | 13 | 10 | 9 | 10 | 0 | 6.5/66.2 | 13.8/75.8 | 0.0258 | - | 4.7 |

10 秒に収まらなかった題の内訳(検証までの秒。高速=高速経路が使った秒、検証=API 往復+検証器、通常=それ以外)

| 実行 | 題 | 検証 | 検証までの秒 | 高速経路の理由 | 高速 | 検証(全送信) | 通常(残り) | 送信数 | 負荷 |
|---|---|---|---|---|---|---|---|---|---|
| du_base | fy1-abs-continuous-at-zero | ○ | 53.2 | - | 0.0 | 8.7 | 44.6 | 2 | 6 |
| du_base | fy1-alternating-over-n-tends-to-zero | ○ | 65.3 | - | 0.0 | 6.3 | 59.0 | 1 | 5 |
| du_base | fy1-arctan-lipschitz | ○ | 89.0 | - | 0.0 | 3.5 | 85.4 | 1 | 6 |
| du_base | fy1-consecutive-product-even | × | 245.1 | - | 0.0 | 13.5 | 231.6 | 7 | 17 |
| du_base | fy1-coprime-sum-and-product | ○ | 171.9 | - | 0.0 | 4.8 | 167.1 | 3 | 6 |
| du_base | fy1-cube-minus-self-divisible-by-six | ○ | 162.7 | - | 0.0 | 10.2 | 152.5 | 3 | 4 |
| du_base | fy1-dependent-consecutive-triples | ○ | 82.2 | - | 0.0 | 4.2 | 78.0 | 2 | 5 |
| du_base | fy1-deviations-from-mean-sum-to-zero | ○ | 58.3 | - | 0.0 | 7.5 | 50.9 | 2 | 4 |
| du_base | fy1-exp-two-x-derivative | ○ | 34.3 | - | 0.0 | 5.9 | 28.4 | 1 | 4 |
| du_base | fy1-factorial-dominates-power-of-two | ○ | 92.2 | - | 0.0 | 8.1 | 84.1 | 3 | 4 |
| du_base | fy1-geometric-sequence-tends-to-zero | ○ | 99.7 | - | 0.0 | 6.4 | 93.2 | 1 | 4 |
| du_base | fy1-idempotent-eigenvalues | ○ | 120.5 | - | 0.0 | 8.0 | 112.4 | 2 | 6 |
| du_base | fy1-image-of-intersection | ○ | 64.5 | - | 0.0 | 6.9 | 57.7 | 2 | 6 |
| du_base | fy1-independent-union-probability | ○ | 56.5 | - | 0.0 | 5.2 | 51.4 | 1 | 5 |
| du_base | fy1-integral-of-sine-over-half-period | ○ | 60.5 | - | 0.0 | 10.1 | 50.3 | 2 | 5 |
| du_base | fy1-inverse-by-exhibiting | ○ | 93.7 | - | 0.0 | 4.8 | 89.0 | 2 | 6 |
| du_base | fy1-limit-of-sum | ○ | 48.8 | - | 0.0 | 7.8 | 41.0 | 2 | 6 |
| du_base | fy1-reverse-triangle-inequality | ○ | 89.4 | - | 0.0 | 10.6 | 78.8 | 3 | 6 |
| du_base | fy1-three-tosses-two-heads | ○ | 113.3 | - | 0.0 | 8.4 | 105.0 | 2 | 6 |
| du_base | fy1-union-monotone | ○ | 19.7 | - | 0.0 | 4.4 | 15.3 | 1 | 6 |
| du_off | fy1-alternating-over-n-tends-to-zero | ○ | 88.3 | - | 0.0 | 9.7 | 78.6 | 3 | 20 |
| du_off | fy1-arctan-lipschitz | ○ | 105.2 | - | 0.0 | 32.8 | 72.3 | 3 | 16 |
| du_off | fy1-consecutive-product-even | ○ | 29.8 | - | 0.0 | 4.3 | 25.5 | 2 | 17 |
| du_off | fy1-coprime-sum-and-product | ○ | 16.1 | - | 0.0 | 2.0 | 14.1 | 1 | 11 |
| du_off | fy1-cube-minus-self-divisible-by-six | ○ | 15.2 | - | 0.0 | 2.1 | 13.0 | 1 | 10 |
| du_off | fy1-dependent-consecutive-triples | ○ | 112.3 | - | 0.0 | 5.2 | 107.2 | 3 | 8 |
| du_off | fy1-deviations-from-mean-sum-to-zero | ○ | 11.4 | - | 0.0 | 1.9 | 9.5 | 1 | 6 |
| du_off | fy1-exp-two-x-derivative | ○ | 60.3 | - | 0.0 | 12.5 | 47.8 | 3 | 6 |
| du_off | fy1-factorial-dominates-power-of-two | ○ | 18.3 | - | 0.0 | 6.9 | 11.4 | 1 | 6 |
| du_off | fy1-geometric-sequence-tends-to-zero | ○ | 112.5 | - | 0.0 | 9.7 | 102.8 | 3 | 6 |
| du_off | fy1-idempotent-eigenvalues | ○ | 125.1 | - | 0.0 | 11.9 | 113.2 | 3 | 10 |
| du_off | fy1-image-of-intersection | ○ | 14.3 | - | 0.0 | 4.4 | 9.8 | 1 | 8 |
| du_off | fy1-independent-union-probability | ○ | 17.7 | - | 0.0 | 5.2 | 12.5 | 1 | 7 |
| du_off | fy1-integral-of-sine-over-half-period | ○ | 110.4 | - | 0.0 | 11.0 | 99.4 | 3 | 6 |
| du_off | fy1-limit-of-sum | ○ | 80.1 | - | 0.0 | 9.0 | 71.1 | 3 | 6 |
| du_off | fy1-reverse-triangle-inequality | ○ | 80.5 | - | 0.0 | 14.4 | 66.2 | 4 | 5 |
| du_off | fy1-three-tosses-two-heads | ○ | 13.0 | - | 0.0 | 1.9 | 11.1 | 1 | 9 |
| du_cf_low | fy1-alternating-over-n-tends-to-zero | ○ | 13.4 | - | 0.0 | 2.1 | 11.3 | 1 | 5 |
| du_cf_low | fy1-arctan-lipschitz | ○ | 90.8 | - | 0.0 | 5.0 | 85.8 | 3 | 5 |
| du_cf_low | fy1-consecutive-product-even | ○ | 33.1 | - | 0.0 | 3.3 | 29.8 | 2 | 4 |
| du_cf_low | fy1-cube-minus-self-divisible-by-six | ○ | 10.6 | - | 0.0 | 1.9 | 8.7 | 1 | 4 |
| du_cf_low | fy1-dependent-consecutive-triples | ○ | 123.1 | - | 0.0 | 5.1 | 118.0 | 3 | 5 |
| du_cf_low | fy1-deviations-from-mean-sum-to-zero | ○ | 11.9 | - | 0.0 | 2.0 | 10.0 | 1 | 4 |
| du_cf_low | fy1-exp-two-x-derivative | ○ | 36.5 | - | 0.0 | 4.9 | 31.7 | 3 | 4 |
| du_cf_low | fy1-idempotent-eigenvalues | ○ | 21.7 | - | 0.0 | 2.0 | 19.7 | 1 | 6 |
| du_cf_low | fy1-image-of-intersection | ○ | 12.5 | - | 0.0 | 1.8 | 10.7 | 1 | 5 |
| du_cf_low | fy1-integral-of-sine-over-half-period | ○ | 125.8 | - | 0.0 | 7.4 | 118.3 | 5 | 4 |
| du_cf_low | fy1-limit-of-sum | ○ | 25.3 | - | 0.0 | 3.4 | 21.8 | 2 | 4 |
| du_cf_low | fy1-reverse-triangle-inequality | ○ | 129.6 | - | 0.0 | 6.2 | 123.4 | 4 | 4 |
| du_cf_low | fy1-three-tosses-two-heads | ○ | 11.9 | - | 0.0 | 1.9 | 10.0 | 1 | 5 |
| du_cf_none | fy1-arctan-lipschitz | ○ | 147.7 | - | 0.0 | 27.9 | 119.8 | 4 | 6 |
| du_cf_none | fy1-consecutive-product-even | ○ | 21.1 | - | 0.0 | 3.4 | 17.7 | 2 | 5 |
| du_cf_none | fy1-coprime-sum-and-product | ○ | 26.4 | - | 0.0 | 3.4 | 23.1 | 2 | 5 |
| du_cf_none | fy1-cube-minus-self-divisible-by-six | ○ | 24.6 | - | 0.0 | 3.6 | 21.1 | 2 | 6 |
| du_cf_none | fy1-dependent-consecutive-triples | ○ | 23.0 | - | 0.0 | 3.5 | 19.5 | 2 | 5 |
| du_cf_none | fy1-exp-two-x-derivative | ○ | 100.9 | - | 0.0 | 6.2 | 94.7 | 4 | 5 |
| du_cf_none | fy1-factorial-dominates-power-of-two | ○ | 27.1 | - | 0.0 | 3.3 | 23.8 | 2 | 6 |
| du_cf_none | fy1-idempotent-eigenvalues | ○ | 28.7 | - | 0.0 | 3.7 | 25.0 | 2 | 9 |
| du_cf_none | fy1-independent-union-probability | ○ | 232.1 | - | 0.0 | 15.9 | 216.2 | 5 | 9 |
| du_cf_none | fy1-integral-of-sine-over-half-period | ○ | 124.8 | - | 0.0 | 11.3 | 113.5 | 4 | 40 |
| du_cf_none | fy1-inverse-by-exhibiting | ○ | 10.7 | - | 0.0 | 6.5 | 4.2 | 1 | 44 |
| du_cf_none | fy1-limit-of-sum | ○ | 33.5 | - | 0.0 | 11.0 | 22.4 | 2 | 43 |
| du_cf_none | fy1-reverse-triangle-inequality | ○ | 137.4 | - | 0.0 | 15.0 | 122.4 | 5 | 45 |
| du_cf_none | fy1-three-tosses-two-heads | ○ | 141.5 | - | 0.0 | 16.7 | 124.8 | 3 | 40 |
| du_cf_none_xn | fy1-alternating-over-n-tends-to-zero | ○ | 46.6 | - | 0.0 | 4.9 | 41.7 | 3 | 12 |
| du_cf_none_xn | fy1-arctan-lipschitz | ○ | 57.2 | - | 0.0 | 5.0 | 52.2 | 3 | 8 |
| du_cf_none_xn | fy1-coprime-sum-and-product | ○ | 23.6 | - | 0.0 | 3.5 | 20.1 | 2 | 6 |
| du_cf_none_xn | fy1-cube-minus-self-divisible-by-six | ○ | 46.0 | - | 0.0 | 3.9 | 42.1 | 2 | 6 |
| du_cf_none_xn | fy1-dependent-consecutive-triples | ○ | 97.7 | - | 0.0 | 6.5 | 91.2 | 4 | 6 |
| du_cf_none_xn | fy1-deviations-from-mean-sum-to-zero | ○ | 21.0 | - | 0.0 | 3.5 | 17.6 | 2 | 6 |
| du_cf_none_xn | fy1-exp-two-x-derivative | ○ | 28.2 | - | 0.0 | 5.0 | 23.2 | 3 | 6 |
| du_cf_none_xn | fy1-factorial-dominates-power-of-two | ○ | 60.9 | - | 0.0 | 4.8 | 56.0 | 3 | 6 |
| du_cf_none_xn | fy1-idempotent-eigenvalues | ○ | 26.3 | - | 0.0 | 3.7 | 22.6 | 2 | 6 |
| du_cf_none_xn | fy1-image-of-intersection | ○ | 49.2 | - | 0.0 | 1.9 | 47.4 | 1 | 6 |
| du_cf_none_xn | fy1-independent-union-probability | ○ | 185.1 | - | 0.0 | 33.0 | 152.0 | 4 | 5 |
| du_cf_none_xn | fy1-integral-of-sine-over-half-period | ○ | 121.1 | - | 0.0 | 7.5 | 113.6 | 5 | 5 |
| du_cf_none_xn | fy1-reverse-triangle-inequality | ○ | 128.3 | - | 0.0 | 7.4 | 120.8 | 5 | 6 |
| tu_base | la_v2_distinct_eigenspaces_intersection | ○ | 49.8 | - | 0.0 | 7.2 | 42.6 | 1 | 6 |
| tu_base | calculus_v5_derivative_difference_quotient_limit | ○ | 208.5 | - | 0.0 | 2.0 | 206.5 | 1 | 5 |
| tu_base | seed-absolute_value_not_differentiable | ○ | 128.5 | - | 0.0 | 3.7 | 124.9 | 2 | 4 |
| tu_base | la_reuse_kernel_detects_zero | ○ | 36.9 | - | 0.0 | 2.2 | 34.7 | 1 | 6 |
| tu_base | pq-bounded-monotone-real-sequence-convergence | ○ | 53.8 | - | 0.0 | 1.9 | 51.8 | 1 | 6 |
| tu_base | pq-prime-above-every-bound | ○ | 66.7 | - | 0.0 | 7.0 | 59.7 | 2 | 5 |
| tu_base | mv_foundation_exceptional_section_counterexample | × | 569.3 | - | 0.0 | 0.0 | 569.3 | 0 | 5 |
| tu_base | seed-quadratic_not_injective | ○ | 24.1 | - | 0.0 | 4.8 | 19.3 | 1 | 6 |
| tu_base | disc_size_difference_closed | ○ | 44.1 | - | 0.0 | 4.7 | 39.4 | 1 | 6 |
| tu_base | scheme-M13 | ○ | 203.8 | - | 0.0 | 10.7 | 193.1 | 1 | 5 |
| tu_base | scheme-M10 | ○ | 20.7 | - | 0.0 | 1.8 | 18.9 | 1 | 6 |
| tu_base | pq-compact-hausdorff-continuous-bijection-inverse | ○ | 95.0 | - | 0.0 | 4.5 | 90.5 | 2 | 6 |
| tu_base | rat_adjacent_partial_fractions | ○ | 33.1 | - | 0.0 | 5.0 | 28.2 | 1 | 4 |
| tu_base | seed-rank_nullity | ○ | 67.5 | - | 0.0 | 1.9 | 65.7 | 1 | 5 |
| tu_off | la_v2_distinct_eigenspaces_intersection | ○ | 14.1 | - | 0.0 | 2.2 | 11.9 | 1 | 5 |
| tu_off | calculus_v5_derivative_difference_quotient_limit | ○ | 14.5 | - | 0.0 | 2.0 | 12.5 | 1 | 5 |
| tu_off | seed-absolute_value_not_differentiable | ○ | 23.1 | - | 0.0 | 13.0 | 10.2 | 1 | 5 |
| tu_off | pq-bounded-monotone-real-sequence-convergence | ○ | 15.7 | - | 0.0 | 2.1 | 13.6 | 1 | 6 |
| tu_off | pq-prime-above-every-bound | ○ | 99.5 | - | 0.0 | 5.0 | 94.5 | 3 | 6 |
| tu_off | mv_foundation_exceptional_section_counterexample | × | 1098.0 | - | 0.0 | 1.5 | 1096.6 | 1 | 5 |
| tu_off | scheme-M13 | ○ | 23.6 | - | 0.0 | 11.8 | 11.8 | 1 | 5 |
| tu_off | pq-compact-hausdorff-continuous-bijection-inverse | ○ | 20.6 | - | 0.0 | 2.1 | 18.5 | 1 | 7 |
| tu_off | rat_adjacent_partial_fractions | ○ | 16.2 | - | 0.0 | 6.0 | 10.2 | 1 | 8 |
| tu_cf_low | la_v2_distinct_eigenspaces_intersection | ○ | 12.6 | - | 0.0 | 2.0 | 10.6 | 1 | 4 |
| tu_cf_low | calculus_v5_derivative_difference_quotient_limit | ○ | 13.2 | - | 0.0 | 1.9 | 11.3 | 1 | 4 |
| tu_cf_low | seed-absolute_value_not_differentiable | ○ | 19.5 | - | 0.0 | 9.8 | 9.7 | 1 | 4 |
| tu_cf_low | pq-bounded-monotone-real-sequence-convergence | ○ | 14.2 | - | 0.0 | 1.8 | 12.3 | 1 | 4 |
| tu_cf_low | pq-prime-above-every-bound | ○ | 42.2 | - | 0.0 | 3.2 | 39.0 | 2 | 5 |
| tu_cf_low | mv_foundation_exceptional_section_counterexample | ○ | 540.0 | - | 0.0 | 5.3 | 534.7 | 3 | 5 |
| tu_cf_low | scheme-M13 | ○ | 17.0 | - | 0.0 | 10.6 | 6.4 | 1 | 5 |
| tu_cf_low | pq-compact-hausdorff-continuous-bijection-inverse | ○ | 11.6 | - | 0.0 | 1.8 | 9.8 | 1 | 5 |
| tu_cf_low | seed-rank_nullity | ○ | 70.2 | - | 0.0 | 3.5 | 66.7 | 2 | 5 |
| tu_cf_none_xn | calculus_v5_derivative_difference_quotient_limit | ○ | 33.6 | - | 0.0 | 3.4 | 30.2 | 2 | 5 |
| tu_cf_none_xn | seed-absolute_value_not_differentiable | ○ | 66.2 | - | 0.0 | 13.8 | 52.4 | 3 | 5 |
| tu_cf_none_xn | mv_foundation_exceptional_section_counterexample | × | 471.4 | - | 0.0 | 0.0 | 471.4 | 0 | 5 |
| tu_cf_none_xn | scheme-M13 | ○ | 13.3 | - | 0.0 | 10.6 | 2.7 | 1 | 5 |
| tu_cf_none_xn | pq-compact-hausdorff-continuous-bijection-inverse | ○ | 82.8 | - | 0.0 | 3.3 | 79.5 | 2 | 4 |
