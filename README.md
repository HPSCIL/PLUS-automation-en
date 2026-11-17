# plus-automation-en: one-stop PLUS land-use simulation skill

**In one sentence**: install this skill, tell your AI "predict Wuhan's 2050 land-use map", answer a few rounds of multiple-choice questions, and everything else runs automatically — data download, factor preparation, model training, future simulation, accuracy report, publication-grade figures. Done in one pass.

## What problem it solves

Running the PLUS land-use model the traditional way involves a pile of fiddly, error-prone chores: finding data sources, downloading year-by-year land-use maps, preparing a dozen-plus driving factors, unifying projections and grids, checking data formats, operating each module by hand, assembling results into figures... high barrier, slow.

This skill **automates the entire chain**:

```
one-sentence request → round-by-round parameter confirmation → auto data download
→ auto factor preparation → auto modeling → auto accuracy validation
→ auto publication-grade figures → one complete report
```

Every step carries quality checks: mismatched data formats are caught and auto-fixed, misaligned factors are auto-resampled, modeling errors are diagnosed against the bundled manual — it never pushes through a problem and produces fake results.

## What you get

- **Future land-use simulation maps** (e.g. class distribution for 2050; publication-grade 300 dpi figures with legend / scale bar / north arrow)
- **Per-class area statistics** (square kilometers per class per epoch, and the changes)
- **Accuracy reports** (Kappa and FoM dual metrics + error decomposition, explained in plain language)
- **A complete, traceable pipeline report** (what data, what parameters, what rules were changed — all on disk)

## How to use

1. Install the skill into Claude Code (or a similar AI assistant); DeepSeek-series models are recommended for execution
2. Say one sentence, e.g. "predict Chengdu's 2050 land-use map"
3. Answer a few multiple-choice questions about region, years, data source, etc.
4. Wait for the results

## Core features

- **Automatic data download**: CLCD 30m annual land use (China), ESA WorldCover 10m (global), 17 default driving factors, with automatic fallback when a source fails
- **Model untouched**: invokes the PLUS engine as-is for computation; the model itself is never modified; results are pixel-identical to manual operation
- **Ask before running**: all research decisions (years, matrix, water lock, ...) are your choice; the AI only executes
- **Honest reporting**: accuracy metrics reported as they are, with "backtest validation" and "future prediction" modes clearly distinguished
- **Reproducible**: re-runs with the same configuration are statistically consistent; the whole process is archived

## Contact

For issues, feedback, or questions about this project, email: **1202621221@cug.edu.cn**

## License

- The PLUS engine is distributed with the package under the authorization of its author, Prof. Xun Liang
- Data-source licenses and citation formats: see DATA_SOURCES.md
- Scientific research and education use only
