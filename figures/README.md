# Development pilot figure

`development_pilot_metrics.png` and `.pdf` are generated from verified
`results/summary.json` by `tools/plot_pilot_results.py` using Matplotlib.
They show only the seven existing all-scope measurements. The pending new
experiment is omitted. These are inspected single-case development comparisons
with differing models, policies and compute; they are not held-out superiority
or statistical significance results.

To regenerate after validating the summary:

```text
python -m pip install -r requirements-figures.txt
python tools/plot_pilot_results.py
```

Generated figures are derived artifacts. Retain raw run records unchanged.
