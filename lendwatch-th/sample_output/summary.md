# lendwatch-th run summary

> Triage output for human review. Scores are not findings of illegality.

- Artefacts collected: 885 (scored: 828)
- Risk tiers: {'high': 504, 'medium': 88, 'low': 78, 'licensed_channel': 158}
- Licence match: {'unmatched': 666, 'licensed_name': 4, 'licensed_exact': 98, 'licensed_domain': 60}
- Operator clusters: 409 {'suspected_unlicensed': 230, 'needs_review': 47, 'other': 72, 'licensed': 60}
- Largest suspected operator: 9 artefacts
- Evidence chain valid: True

## Hidden population of suspected unlicensed operators

- Observed on at least one list: 230
- List sizes: {'google_play': 129, 'app_store': 37, 'web': 123, 'ad': 75, 'complaint': 42}
- Log-linear, model-averaged: N = 281 (95% CI 263-308); total / observed = 1.22
- Best model interactions: ['webxad']
- Chao lower bound: 323

## Evaluation against ground truth

- n_labelled: 828
- n_positive: 566
- rule_auc: 0.994
- rule_precision_at_n_positives: 0.968
- high_tier_precision: 0.998
- high_tier_recall: 0.889
- false_positives_in_high_tier: 1
- cost_optimal_threshold: {'threshold': 27.0, 'cost': 39.0, 'tp': 566, 'fp': 39, 'fn': 0, 'precision': 0.9355371900826446, 'recall': 1.0}
- supervised_oof_auc: 0.999
- supervised_precision_at_n_positives: 0.986
- supervised_top_coefficients: {'unlicensed_offering_credit': 2.436, 'operator_size': 2.32, 'no_privacy_policy': 1.402, 'no_bureau_check': 1.17, 'low_rating_share': -1.168, 'rate_above_any_ceiling': 1.064, 'harm_review_share': 0.971, 'apk_sideload_link': 0.76}
- true_illegal_operators_observed: 236
- clusters_holding_them: 249
- clusters_mixing_operators: 0
- true_total_illegal_operators: 300
- suspected_operators_observed: 230
- mse_estimate: 280.643
- mse_ci95: (262.70146122870545, 308.42750485576755)
- oracle_linkage_mse_estimate: 283.214
- oracle_linkage_mse_ci95: (267.0113539532167, 307.880868071459)
- oracle_linkage_chao_lower_bound: 318.14
