| 実行 | 題数 | 検証済み | 初回成功 | ≤10 s | ≤30 s | 回答まで ≤10 s | 検証 p50/p90 | 回答 p50/p90 | $/題 | 高速経路の結果 | 負荷(開始平均) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| du_off | 20 | 20 | 10 | 3 | 11 | 1 | 29.8/112.3 | 33.7/121.1 | 0.0326 | - | 9.2 |
| du_sieve2 | 20 | 20 | 12 | 4 | 10 | 1 | 33.4/96.7 | 43.3/105.3 | 0.0275 | {'proposed_sieved': 5, 'sieve_rejected_all': 9, 'model_deadline': 1, 'not_a_proof_request:explain': 1, 'not_a_proof_request:prove': 2, 'gate_rejected': 2} | 7.0 |
| du_nosieve | 20 | 20 | 10 | 1 | 10 | 0 | 33.1/120.0 | 38.2/129.3 | 0.0314 | {'gate_deadline': 3, 'model_deadline': 2, 'proposed_unchecked': 8, 'not_a_proof_request:prove': 2, 'grammar_rejected': 1, 'error:OpenAIError': 1, 'not_a_proof_request:explain': 1, 'gate_rejected': 2} | 6.3 |
| tu_off | 14 | 13 | 12 | 5 | 12 | 0 | 14.5/23.6 | 21.4/27.4 | 0.0518 | - | 5.8 |
| tu_sieve | 14 | 13 | 12 | 2 | 12 | 0 | 17.9/23.9 | 23.2/31.8 | 0.0370 | {'formal_statement_given': 6, 'not_a_proof_request:explain': 1, 'model_deadline': 2, 'error:OpenAIError': 1, 'not_a_proof_request:decide': 2, 'sieve_rejected_all': 2} | 5.8 |

10 秒に収まらなかった題の内訳(検証までの秒。高速=高速経路が使った秒、検証=API 往復+検証器、通常=それ以外)

| 実行 | 題 | 検証 | 検証までの秒 | 高速経路の理由 | 高速 | 検証(全送信) | 通常(残り) | 送信数 | 負荷 |
|---|---|---|---|---|---|---|---|---|---|
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
| du_sieve2 | fy1-alternating-over-n-tends-to-zero | ○ | 82.8 | sieve_rejected_all | 8.1 | 4.9 | 69.8 | 3 | 6 |
| du_sieve2 | fy1-arctan-lipschitz | ○ | 80.6 | sieve_rejected_all | 8.0 | 23.2 | 49.4 | 2 | 5 |
| du_sieve2 | fy1-coprime-sum-and-product | ○ | 20.2 | sieve_rejected_all | 8.0 | 1.9 | 10.3 | 1 | 5 |
| du_sieve2 | fy1-cube-minus-self-divisible-by-six | ○ | 202.4 | sieve_rejected_all | 8.0 | 14.1 | 180.3 | 5 | 6 |
| du_sieve2 | fy1-dependent-consecutive-triples | ○ | 99.1 | sieve_rejected_all | 8.0 | 4.9 | 86.2 | 3 | 6 |
| du_sieve2 | fy1-deviations-from-mean-sum-to-zero | ○ | 20.9 | sieve_rejected_all | 8.0 | 1.8 | 11.0 | 1 | 6 |
| du_sieve2 | fy1-exp-two-x-derivative | ○ | 73.3 | sieve_rejected_all | 8.1 | 17.3 | 47.9 | 3 | 5 |
| du_sieve2 | fy1-factorial-dominates-power-of-two | ○ | 43.3 | sieve_rejected_all | 8.2 | 14.1 | 21.0 | 1 | 8 |
| du_sieve2 | fy1-idempotent-eigenvalues | ○ | 33.4 | model_deadline | 8.0 | 2.7 | 22.7 | 1 | 11 |
| du_sieve2 | fy1-image-of-intersection | ○ | 20.7 | not_a_proof_request:explain | 2.5 | 4.4 | 13.9 | 1 | 11 |
| du_sieve2 | fy1-independent-union-probability | ○ | 14.7 | not_a_proof_request:prove | 3.0 | 5.1 | 6.6 | 1 | 10 |
| du_sieve2 | fy1-integral-of-sine-over-half-period | ○ | 96.7 | gate_rejected | 7.0 | 6.1 | 83.6 | 4 | 9 |
| du_sieve2 | fy1-inverse-by-exhibiting | ○ | 69.1 | not_a_proof_request:prove | 2.3 | 7.1 | 59.8 | 3 | 5 |
| du_sieve2 | fy1-limit-of-sum | ○ | 94.3 | sieve_rejected_all | 8.0 | 12.1 | 74.2 | 3 | 6 |
| du_sieve2 | fy1-reverse-triangle-inequality | ○ | 10.8 | proposed_sieved | 8.8 | 2.0 | 0.0 | 1 | 6 |
| du_sieve2 | fy1-three-tosses-two-heads | ○ | 18.3 | gate_rejected | 5.7 | 1.9 | 10.8 | 1 | 7 |
| du_nosieve | fy1-abs-continuous-at-zero | ○ | 14.9 | gate_deadline | 8.0 | 1.8 | 5.1 | 1 | 7 |
| du_nosieve | fy1-alternating-over-n-tends-to-zero | ○ | 19.5 | model_deadline | 8.0 | 2.0 | 9.5 | 1 | 6 |
| du_nosieve | fy1-arctan-lipschitz | ○ | 103.6 | proposed_unchecked | 7.1 | 3.7 | 92.9 | 2 | 5 |
| du_nosieve | fy1-consecutive-product-even | ○ | 115.5 | proposed_unchecked | 7.0 | 5.0 | 103.5 | 3 | 8 |
| du_nosieve | fy1-coprime-sum-and-product | ○ | 114.0 | proposed_unchecked | 6.6 | 5.8 | 101.5 | 3 | 6 |
| du_nosieve | fy1-cube-minus-self-divisible-by-six | ○ | 33.1 | gate_deadline | 8.0 | 8.5 | 16.5 | 1 | 7 |
| du_nosieve | fy1-dependent-consecutive-triples | ○ | 120.0 | not_a_proof_request:prove | 2.8 | 12.8 | 104.4 | 4 | 7 |
| du_nosieve | fy1-deviations-from-mean-sum-to-zero | ○ | 16.6 | grammar_rejected | 3.6 | 2.1 | 10.9 | 1 | 6 |
| du_nosieve | fy1-exp-two-x-derivative | ○ | 103.7 | proposed_unchecked | 6.7 | 11.7 | 85.3 | 3 | 6 |
| du_nosieve | fy1-factorial-dominates-power-of-two | ○ | 29.7 | gate_deadline | 8.0 | 6.9 | 14.8 | 1 | 6 |
| du_nosieve | fy1-geometric-sequence-tends-to-zero | ○ | 13.5 | error:OpenAIError | 5.5 | 2.0 | 6.0 | 1 | 8 |
| du_nosieve | fy1-idempotent-eigenvalues | ○ | 111.0 | model_deadline | 8.0 | 9.6 | 93.4 | 3 | 7 |
| du_nosieve | fy1-image-of-intersection | ○ | 27.8 | not_a_proof_request:explain | 2.0 | 7.9 | 18.0 | 2 | 8 |
| du_nosieve | fy1-independent-union-probability | ○ | 14.4 | not_a_proof_request:prove | 2.5 | 5.2 | 6.7 | 1 | 8 |
| du_nosieve | fy1-integral-of-sine-over-half-period | ○ | 132.5 | proposed_unchecked | 5.9 | 8.4 | 118.2 | 5 | 7 |
| du_nosieve | fy1-inverse-by-exhibiting | ○ | 14.1 | gate_rejected | 5.4 | 2.1 | 6.6 | 1 | 6 |
| du_nosieve | fy1-reverse-triangle-inequality | ○ | 125.1 | proposed_unchecked | 5.0 | 12.2 | 107.9 | 4 | 5 |
| du_nosieve | fy1-three-tosses-two-heads | ○ | 98.5 | proposed_unchecked | 6.0 | 4.5 | 88.0 | 3 | 5 |
| du_nosieve | fy1-union-monotone | ○ | 13.2 | gate_rejected | 5.6 | 4.2 | 3.4 | 1 | 5 |
| tu_off | la_v2_distinct_eigenspaces_intersection | ○ | 14.1 | - | 0.0 | 2.2 | 11.9 | 1 | 5 |
| tu_off | calculus_v5_derivative_difference_quotient_limit | ○ | 14.5 | - | 0.0 | 2.0 | 12.5 | 1 | 5 |
| tu_off | seed-absolute_value_not_differentiable | ○ | 23.1 | - | 0.0 | 13.0 | 10.2 | 1 | 5 |
| tu_off | pq-bounded-monotone-real-sequence-convergence | ○ | 15.7 | - | 0.0 | 2.1 | 13.6 | 1 | 6 |
| tu_off | pq-prime-above-every-bound | ○ | 99.5 | - | 0.0 | 5.0 | 94.5 | 3 | 6 |
| tu_off | mv_foundation_exceptional_section_counterexample | × | 1098.0 | - | 0.0 | 1.5 | 1096.6 | 1 | 5 |
| tu_off | scheme-M13 | ○ | 23.6 | - | 0.0 | 11.8 | 11.8 | 1 | 5 |
| tu_off | pq-compact-hausdorff-continuous-bijection-inverse | ○ | 20.6 | - | 0.0 | 2.1 | 18.5 | 1 | 7 |
| tu_off | rat_adjacent_partial_fractions | ○ | 16.2 | - | 0.0 | 6.0 | 10.2 | 1 | 8 |
| tu_sieve | la_v2_distinct_eigenspaces_intersection | ○ | 13.6 | formal_statement_given | 0.0 | 2.2 | 11.4 | 1 | 6 |
| tu_sieve | calculus_v5_derivative_difference_quotient_limit | ○ | 20.2 | formal_statement_given | 0.0 | 2.2 | 18.0 | 1 | 6 |
| tu_sieve | seed-absolute_value_not_differentiable | ○ | 23.9 | not_a_proof_request:explain | 2.3 | 10.5 | 11.0 | 1 | 6 |
| tu_sieve | pq-bounded-monotone-real-sequence-convergence | ○ | 23.1 | model_deadline | 8.0 | 1.8 | 13.3 | 1 | 7 |
| tu_sieve | pq-prime-above-every-bound | ○ | 17.9 | error:OpenAIError | 8.0 | 1.9 | 8.0 | 1 | 6 |
| tu_sieve | mv_foundation_exceptional_section_counterexample | × | 690.0 | formal_statement_given | 0.0 | 1.4 | 688.6 | 1 | 5 |
| tu_sieve | seed-quadratic_not_injective | ○ | 14.0 | not_a_proof_request:decide | 3.6 | 5.1 | 5.2 | 1 | 5 |
| tu_sieve | disc_size_difference_closed | ○ | 12.5 | not_a_proof_request:decide | 3.0 | 4.7 | 4.8 | 1 | 5 |
| tu_sieve | scheme-M13 | ○ | 20.6 | formal_statement_given | 0.0 | 10.5 | 10.1 | 1 | 5 |
| tu_sieve | pq-compact-hausdorff-continuous-bijection-inverse | ○ | 86.9 | sieve_rejected_all | 8.7 | 4.6 | 73.7 | 3 | 5 |
| tu_sieve | rat_adjacent_partial_fractions | ○ | 21.6 | model_deadline | 8.0 | 5.2 | 8.4 | 1 | 5 |
| tu_sieve | seed-rank_nullity | ○ | 16.7 | sieve_rejected_all | 8.0 | 1.9 | 6.7 | 1 | 6 |
