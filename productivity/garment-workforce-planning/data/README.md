# Data

The project expects one raw file:

```text
data/raw/garments_worker_productivity.csv
```

Run `python scripts/download_data.py` to hydrate it. The downloader also writes `data/raw/manifest.json` with byte size and SHA-256 integrity information.

The modeling loader standardizes whitespace/case in categorical fields, normalizes the known `sweing` spelling to `sewing`, parses dates, and converts numeric columns. Missing `wip` values are preserved until the scikit-learn pipeline imputes them inside each training fold.

`idle_time` and `idle_men` are retained in the raw table for diagnostics but excluded from the default pre-shift forecasting model because they are realized interruption outcomes.
