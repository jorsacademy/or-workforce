# Benchmark

## Temporal holdout

- Selected model: `extra_trees`
- Holdout period: 2015-02-26 to 2015-03-11
- Development rows: 943
- Holdout rows: 254
- MAE: 0.0909
- RMSE: 0.1348
- R²: 0.3060
- Target-attainment accuracy: 55.118%

## OR planning example

- Planning date: 2015-03-11
- Teams/lines in case: 24
- Conserved headcount: 733
- Overtime blocks used: 60
- Mean baseline surrogate productivity: 0.7372
- Mean post-allocation surrogate productivity: 0.7581

The allocation output is a model-based what-if result, not a causal estimate of intervention impact.

## Cross-validation comparison

| model         |       mae |     rmse |       r2 |
|:--------------|----------:|---------:|---------:|
| extra_trees   | 0.0779621 | 0.128736 | 0.470124 |
| random_forest | 0.0819169 | 0.131399 | 0.447978 |
| ridge         | 0.0991029 | 0.140195 | 0.37159  |
