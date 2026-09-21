# DE-CORE-004.3 — Adaptive Fusion Weighting

Version: 0.4.0

## Changes
- Adds regime-aware fusion weights for Technical, Fundamental and Business Momentum.
- Preserves 45/35/20 as the neutral/base policy.
- Determines Decision Regime from the neutral base score first, avoiding recursive regime/weight feedback.
- Recomputes the final Combined Score using the regime policy.
- Preserves missing-engine renormalization and all technical hard gates.
- Exposes base_weight, regime_weight, effective_weight, weight_delta and contribution for auditability.
- Adds base_combined_score and adaptive_weighting metadata to the API response.
- Updates Fundamental UI to show Base Weight -> Regime Weight -> Contribution.

## Regime policies
- CAPITAL_PROTECTION: 65 / 25 / 10
- DEFENSIVE: 60 / 25 / 15
- TIMING_BLOCKED: 55 / 30 / 15
- RECOVERY_WATCH: 40 / 30 / 30
- PRICE_AHEAD_OF_BUSINESS: 50 / 35 / 15
- CROSS_ENGINE_CONFLICT: 50 / 35 / 15
- CONFIRMED_CONSTRUCTIVE: 45 / 35 / 20
- CONFIRMED_DEFENSIVE: 60 / 30 / 10
- TRANSITION: 45 / 35 / 20

## Validation
- Python compilation: PASS
- Architecture contracts: 3/3 PASS
