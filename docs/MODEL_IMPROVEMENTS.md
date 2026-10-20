# Model improvement report — 21 October 2026

Energy models and data are unchanged.

| Domain | Previous stored result | New result | Interpretation |
|---|---|---|---|
| Maintenance | MAE 12.31 cycles, R² 0.825 | MAE 10.25 cycles, R² 0.8801 | 16.7% lower error on the same reused NASA benchmark |
| Occupancy forecast | MAE 7.75 pp, R² 0.8072 | MAE 7.45 pp, R² 0.8253 | Modest improvement; split now keeps timestamps together and purges one-hour target overlap |
| Security | F1 0.7258 on training events | F1 0.9253, precision 0.9747, recall 0.8807 on later days | New supervised synthetic-pattern task; not directly comparable to old in-sample unsupervised score |
| Occupancy detection | 98.34% accuracy | Unchanged | Separate UCI sensor classifier, not zone utilization forecasting |
| Cost forecast | MAE ₹1,190,776, R² -0.145 | Existing model retained | Purged-validation alternatives did not improve the five-week benchmark |

Maintenance uses standardized support-vector regression with causal 20/40-cycle sensor smoothing. Model selection uses three engine-grouped validation folds, with one reproducibly truncated observation per validation engine. The official NASA test engines are excluded from selection. Earlier project work already used this benchmark, so it is not a pristine external test. The residual-based nominal 80% band covers 81% of these benchmark observations. It is not a guaranteed interval on new equipment. Global permutation weights retain the existing heuristic sensor explanations.

Occupancy uses target-hour calendar features and timestamp-based lag lookups, shared between training and inference. Missing readings no longer shift a positional lag to the wrong time. Training/validation boundaries exclude labels whose target lies in the next partition. The new dashboard scatter samples at most 250 uniformly spaced test rows; the score uses all test rows.

Security switches from an unsupervised outlier detector to a supervised random forest trained on the available synthetic incident labels. Model depth and probability threshold are selected on validation days, then evaluated on the final 20% of calendar days. No employee ID, incident label, anomaly type, or future event is used as a predictor. The validation-selected threshold is 0.9. The benchmark contains 347 true positives, 9 false positives, 47 false negatives and 16,965 true negatives. It does not demonstrate real-world security performance or reliable discovery of previously unseen threats. Historical comparison cards have different evaluation protocols and are labeled accordingly. Drift monitoring retains stable sensor/time features, excluding history-window-dependent novelty flags.

Cost experiments use a two-week purge because each target averages three future weeks. The validation-selected baseline was worse on the existing test tail, so it was not deployed. The original cost metric has only five overlapping test windows and its old selection process used that test tail; it is weak evidence. Live inference now uses the target week's calendar feature, matching training. Cost anomaly detection has no verified incident labels: model agreement is not accuracy. More representative, labeled data and longer invoice history are needed before claiming 90+ performance.

Reproduce from the repository root with the project virtualenv Python:

- `backend/ml_models/maintenance/train_validated_rul.py`
- `backend/ml_models/occupancy/train_validated_forecast.py`
- `backend/ml_models/security/train_validated_patterns.py`
- `backend/ml_models/cost/train_validated_forecast.py` (report only; does not replace live model)

No dataset was regenerated or modified to improve scores. R² is not classification accuracy. Forecast and security metrics cannot be compared as a single accuracy percentage.
