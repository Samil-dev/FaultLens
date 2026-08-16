# Screenshots needed

This folder is referenced by the root `README.md` hero and feature sections, but
**no screenshots have been captured yet** — nothing here is invented. Once each
image below is added with the exact filename listed, it will appear
automatically in the main README (the links are already wired).

Capture at **1920×1080**, dark theme (the app's default), with the demo
E-Commerce Platform system loaded.

| # | Filename | What to capture | How |
|---|----------|------------------|-----|
| 1 | `01-digital-twin-dashboard.png` | The full dashboard at rest: header, left sidebar (Digital Twin panel), dependency graph with all 10 nodes healthy, right panel. | Open the app, don't select a node yet. |
| 2 | `02-chaos-experiment-modal.png` | The "Run Chaos Experiment" modal open, with a target node selected and a failure scenario chosen. | Click a node (e.g. Primary Database) → "Run Experiment". |
| 3 | `03-resilience-analysis.png` | The Resilience Panel after a completed experiment: score ring, blast radius, impact, recovery, risk assessment. | Run a "Service Down" experiment against `Primary Database`, wait for "Experiment complete". |
| 4 | `04-ai-insights.png` | The AI Analysis card in the Resilience Panel (or the left sidebar's "AI Insights" tab): summary, root cause, risk interpretation, confidence. | Same run as #3, scroll to the AI Analysis section. |
| 5 | `05-scenario-comparison.png` | Either the "Compare Scenarios" panel with 2+ runs selected, or the "Metrics" tab's before/after chart. | Run at least two experiments first, then open "Compare Scenarios" (or "Metrics"). |

Once added, run a quick sanity check that the images actually render:

```
git add docs/images/*.png
```

then open `README.md` in a Markdown previewer (or push and view it on GitHub).
