# PLUS Engine Common Problems — Quick Reference (index to the bundled manual)

> Source: chapter 5 "Common problems" of `tutorial-1-plus-model-principles-and-software-intro-20250531.pdf` (the PDF is in this directory; sections contain screenshots; the PDF text is in Chinese — the original is authoritative).
> Usage: match the left "error code / symptom" column → open the corresponding Tutorial 1 section for the original text and figures → apply the right-column key points.
> Pitfalls of the skill's own flow (breakpoints / continuous-prediction epoch counts / report template / matrix) are not here — see the package root `FAQ.md`.

| Error code / symptom | Manual section | Key points (summary; original text prevails) |
|---|---|---|
| PLUS software won't open | 5.1 | Install Visual C++ Redistributable for VS2015 (x64; download link from Microsoft's site is in the original) |
| LEAS reports "make df-trees success=-1" / crash without dialog | 5.2 | Driving factors and the expansion map have inconsistent rows/columns/CRS: first feed only 1 factor to see if it runs, then add factors one by one to locate the problem factor; use GIS to unify rows/columns, coordinate system and projection of all factors and the expansion map |
| LEAS dialog crash ("Predicting, please wait...") | 5.3 | Data volume exceeds memory: lower the resolution, or use a machine with 64G/128G RAM |
| Random noise pixels in probability maps / simulation results | 5.4 | Re-run the LEAS module with thread count = 1, then feed the new probability bands to CARS again |
| No-data holes in simulation results | 5.5 | Driving factors contain no-data areas: remove the factors with nodata |
| Markov outputs NaN | 5.6 | The two epochs' class codes must be consecutive integers with identical rows/columns (this skill already auto-validates code continuity + auto-merges zero-pixel classes in the starting year) |
| A class never reaches its demand | 5.7 | ① check the probability bands are non-empty and normal ② demand and starting quantity must be of the same order ③ tune: larger neighborhood (11, 21), lower patch-generation threshold, larger expansion coefficient; complex cases use two-stage simulation (full example in the original) |
| **CARS crash 0xC0000005** / expansion map missing a class | **5.8** | **LEAS decides band count by the maximum class code in the expansion map; if the last class never expanded → one band short → CARS class-count mismatch crash. Fix: re-code so a "class with expansion" is last, re-run expansion extraction (or ensure the last class keeps a few incoming patches). The skill auto-detects this; details in FAQ.md F2** |

## Supplementary notes

- **The 5.6 / 5.8 cases are already auto-guarded by the skill** (code-continuity checks, zero-pixel class auto-merge, expansion-map missing-class detection); when hit, the pipeline prints a clear error and points back to this table — it never pushes through the problem.
- The remaining entries (5.1–5.5, 5.7) are engine/data-level issues the skill cannot auto-fix; handle them manually per the table.
- Three PDFs in this directory: `tutorial-1` (user manual, contains the common-problems chapter), `tutorial-2` (planning-policy raster tutorial), `plus-model-principles-v3` (older introduction, for method reference). PDF contents are in Chinese.
