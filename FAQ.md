# plus-automation-en FAQ

> For engine errors, **check the bundled manual first**: `docs\tutorial-1-plus-model-principles-and-software-intro-20250531.pdf` chapter 5 "Common problems" (error-code quick-reference table in `docs\troubleshooting.md`).
> This file only collects known pitfalls of the **skill's own flow** that the manual does not cover. Each entry is organized as "symptom → cause → fix" and cites the observed source, to prevent recurrence.

## F1. Breakpoint markers .stage_*.done take effect automatically (changed 2026-11-10)

- **Mechanism**: after a slow stage (①②⑤) completes, a `.stage_N.done` file is written in the data directory (content = configuration fingerprint: demand method / matrix / years / validation mode). On re-run, if the marker exists and the fingerprint matches → **that stage is auto-skipped** — no need to remember `--resume` (the old mechanism "marker present but flag absent" would re-run from scratch, re-download factors over the network, or even hang; the advisor hit this in a live test on 2026-11-10).
- **Forced re-run**: delete the corresponding `.stage_*.done` file under `data_dir`; if the configuration changed (e.g. different demand method), the fingerprint won't match and it re-runs automatically — stale results are never reused.
- **Source**: advisor hit the old mechanism in a live test 2026-11-10; user decided auto-effect on 2026-11-10.

## F2. CARS crash 0xC0000005 (expansion map missing the last class)

- **Symptom**: LEAS outputs one fewer probability band than the number of land-use classes (e.g. 7 bands vs 8 classes), and CARS crashes with `0xC0000005`.
- **Cause**: LEAS decides the number of probability bands by the "maximum class code in the expansion map". When the last class (e.g. wetland with code 8) never has an incoming patch in the whole training period, it is absent from the expansion map → one band short; CARS reads bands by land-use class count → class misalignment crash. Manual Tutorial 1, section 5.8 documents this.
- **Fixes** (in priority order):
  1. **Manual's solution (Tutorial 1, 5.8)**: re-code so that a "class with expansion" is last (e.g. swap the codes of urban land and the no-expansion class), then re-run expansion extraction;
  2. **In-skill solution**: make sure expansion uses the full period (first year → latest year) rather than the last two epochs — the full period makes it easier for every class to keep a few incoming patches (verified by the advisor on 2026-11-10);
  3. The pipeline already **auto-detects "expansion map missing classes"** after expansion: a missing last class errors out loudly and stops (CARS never gets the chance to crash); a missing middle class only warns (band count is unaffected; that class gets no development probability and barely expands in the simulation).
- **Source**: advisor's live test 2026-11-10 (8-class scenario with wetland); Zhengzhou's 7 classes all had incoming transitions, so it was not triggered.

## F3. Continuous-prediction sequence semantics (changed 2026-11-10): intermediate epochs run up to the target year, never past it

- **Background**: the old mechanism `--sequence 3,5` = **append** 5 epochs after the target year (the advisor's test of `5,5` produced 6 epochs up to 2060 — counter-intuitive); changed to the new mechanism by user decision.
- **New mechanism**: `--sequence N` (interval in years only). Intermediate epochs = one every N years after the latest year, running up to the target year; **the target year is always the last epoch of the sequence** (= the main simulation year). When the interval does not divide the span evenly, intermediate epochs are truncated and the target year is appended last.
  - Example: 2025→2035: interval 5 → **2030, 2035** (2 epochs); interval 3 → **2028, 2031, 2034, 2035** (4 epochs); interval ≥ span → target year only.
- **Compatibility**: the old "interval,count" format errors out with a hint about the new usage; historical project JSONs that already store a sequence year list are unaffected (re-running a historical project reuses it directly).
- **Source**: mechanism decided by the user 2026-11-10 (the advisor's live test found the old epoch counts counter-intuitive).

## F4. Summary report wrote "CLCD 30m" for user-supplied data (hard-coded template)

- **Symptom**: when running with user-supplied data, the summary report's data-source row still said "CLCD 30m annual data (CAS, Yang & Huang 2021)".
- **Cause**: `make_report.py` had the data source hard-coded in the template (before the 2026-11-10 fix).
- **Fix (done)**: `run_full.py` records `data_source` when writing the project (auto-determined by "does a CLCD download report exist"); `make_report.py` generates the data-source description from that field. Old projects (without the field) are inferred the same way when the report is regenerated.
- **Source**: found by the advisor 2026-11-10 (previously worked around with annotate_demo.py; now replaced by the official mechanism).

## F5 (explanatory). The correct way to regionalize the transition matrix: project.json's matrix_restrictions

- Regionalizing the matrix (e.g. no lake filling, allow forest→cropland) requires no script changes; two ways:
  ① In the Q&A, choose "Regional customization", and the AI automatically researches the region + literature/policy and generates rules, passed as a parameter: `--matrix-restrictions '[{"from":"水域","to":"建设用地","allow":false,"依据":"Yangtze River Protection Law art. 25"}]'` (SKILL.md requires the AI to do this automatically — never make the user edit it);
  ② or edit `matrix_restrictions` in the generated `project_full_*.json`.
  Rules and their bases go into the summary report's "3b. Transition matrix rules" section (baseline + each change + basis) — fully traceable.
- Example:
  ```json
  "matrix_restrictions": [
    {"from": "水域", "to": "建设用地", "allow": false, "依据": "Yangtze River Protection Law art. 25/26, no encroachment on rivers and lakes"}
  ]
  ```
- Note: the advisor's local copy once used an "environment variable injection point" for the same feature; the official entry point of this skill is `matrix_restrictions` (explained in SKILL.md's item-8 dialog).

## F6 (hard rule). "Synthetic placeholder drivers" are forbidden — modeling input always uses genuinely downloaded data

- **Rule (set by the advisor 2026-11-10, hard — do not change)**: driving factors (and all modeling inputs) use only genuinely downloaded data; if a factor download fails → error out and stop, go through `--manual` as the human fallback. **Never substitute with self-generated data (all-zero, random numbers, constant surfaces, etc. — "synthetic placeholder factors")** — synthetic factors make LEAS/CARS produce results that look normal but are scientifically meaningless; that is worse than failing.
- **Explanation**: the advisor's local test copy has a "synthetic placeholder drivers" option for his personal experiments; the official skill provides no such option, and SKILL.md hard-codes the ban. If anyone (including an AI) tries to generate factors on their own to bypass downloading, refuse. **Observed: the Hy4 assistant once volunteered this option while executing the skill (2026-11-10); SKILL.md's header now recommends DeepSeek for execution.**
- **Source**: required by the advisor after his live test 2026-11-10.

## F7. FoM "target practice" rule: nearer years → higher Kappa; farther years → higher FoM

- **Target-practice analogy**: computing FoM is like target practice — in high-change regions the target is big and easier to hit, so FoM is high; in low-change regions the target is small and harder to hit, so FoM is low (same structure as "the net/gross change structure caps FoM").
- **Empirical rule (three-city tests)**: nearer years (short prediction span) → fewer changed pixels → higher unchanged share → Kappa naturally high, FoM low; farther years (long span) → more changed pixels (bigger target) → FoM relatively high, while Kappa falls back as the change region grows.
- **Interpretation**: Kappa/FoM with different prediction spans cannot be compared directly — check the span first, then judge against the rule above; use the target-practice analogy (plain language) when explaining accuracy to users.
- **Source**: user's phrasing 2026-11-11; training-period recommendations are coupled to the data source (Esri 2017/2025 two epochs = 9 years, CLCD 2000/2020 two epochs = 20 years; only 2 epochs recommended, taking the farthest apart; decided 2026-11-12; see SKILL.md dialog items 2 and 5).
