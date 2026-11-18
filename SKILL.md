---
name: plus-automation-en
description: PLUS land-use simulation, end-to-end: from one sentence to an accuracy report. Given a study region and multiple historical years → automatically download land-use data and 17 default driving factors → semantic reclassification & format checks → modeling (expansion/LEAS/demand/CARS) → Kappa+FoM+error-decomposition report. Use when the user says "predict land use of region X in year Y", "run the full PLUS pipeline", "simulate future land use". **Before starting, ALL items must be asked via multi-round choice dialogs (data source / historical years / area-demand method / backtest or not / continuous prediction / water lock / transition matrix / output dir / reclassification mapping; items the user already gave — region & target year — must NOT be re-asked); execute only after every item is answered. Never ask only 3–4 of them and start. Every dialog option must be listed verbatim from SKILL.md (including year ranges, no-registration / registration-required / recommended tags); do not simplify or omit options — the user repeatedly corrected AIs (2026-11-13) for dropping tags/options.**
---

# PLUS End-to-End Pipeline

> **Recommended execution model: DeepSeek series LLMs**
> The hard rules of this skill (ask-before-run / troubleshooting protocol / no synthetic placeholder factors / real data only as modeling input) require strict compliance from the executing model. Observed in practice: assistants such as Hy4 once volunteered a "synthetic placeholder drivers" option while executing this skill (violating the hard ban in FAQ F6); DeepSeek models have the best observed compliance record on this skill. **Prefer DeepSeek to run this skill; if another model is used, it must first read "Automated handling rules" and the hard-rule entries in FAQ.md.**

## Standard flow (ask before running; multi-round dialogs; no skipping)

**Prefer the "standardized Q&A flow" (2026-11-13 pilot, strongly recommended)**: the AI does not compose dialogs itself, but copies the standard questions produced by the script — option text, tags, and branch recommendations are all fixed in the script, leaving the AI zero room for improvisation:

```
Step 1: python scripts/ask_questions.py --dump
        → get the standard question list (copy options verbatim into the dialogs,
          including "(recommended)" / "no registration" / "registration required" tags)
Step 2: ask question by question with choice dialogs (two-level data-source dialog,
        branch years, two area options, two backtest modes, ...).
        After all answers are collected:
        python scripts/ask_questions.py --finalize '<answers JSON>'
        → on validation failure it prints specific errors; you must re-ask.
          On success it writes answers.json.
Step 3: python scripts/run_ask.py
        → answers are translated item-by-item into run_full arguments and executed
          (answers are the parameters — everything asked takes effect)
```

The detailed rules for each question below = the source of the script's question definitions; fall back to hand-written dialogs only when the script is unavailable (in that case obey every option clause verbatim, including all hard bans marked "observed AI simplification / user correction").

After the user issues the request, the AI asks **all items via multi-round choice dialogs (AskUserQuestion)**; execute only after everything is answered.

**Dialog conventions (important)**:
- Items the user already stated in their request (e.g. region, target year) must not be re-asked; everything else **must be asked — one item at a time, none missed**.
- ≤4 questions per round, 2–3 rounds total; even items with defaults must be asked (put the default option first and tag it "recommended").
- Use plain language; avoid jargon such as "in-sample / out-of-sample" (see items 4, 5).
- Missing items = poor guidance: in particular, never ask only "historical years / continuous prediction / water lock" while dropping "area method, backtest accuracy, transition matrix, output dir, reclassification mapping".

```
Round 1 · data source & modeling parameters
  1. Which land-use data source? (Esri = no registration, years 2017-2025, at 30m it is auto-aggregated from 10m, at 10m it is native;
     CLCD = register yourself and provide the account, 1990-2022; among other sources: WorldCover = no registration, only 2020-2021,
     Stanford = proxy required, own data = user-provided)
     · Esri 30m (no registration, recommended)
     · Esri 10m (no registration)
     · CLCD 30m (registration required)
     · Other sources (choose this to pick WorldCover / Stanford / own data in the second question)
     Additional source (second question; users who picked one of the first 3 just choose option 1 "none"):
     · None — use the source from the first question
     · WorldCover 30m/10m 2020-2021 (no registration; only 2020/2021)
     · Stanford derived data (proxy required; provide the folder after downloading via proxy)
     · My own multi-year tifs (an input box for the folder path follows immediately; if you know the
       dataset name [e.g. CNLUCC/GlobeLand30], tell the AI — a match in the built-in legend library
       means no legend table needed)
     Year coupling: Esri limited to 2017-2025; CLCD 1990-2022; WorldCover only 2020/2021.
     If CLCD is chosen, run in parallel: after the remaining questions, start the driver download first
     (in the background), while guiding the user through registration ("Data source registration guide");
     once credentials are ready, start the land-use download.
  2. Which historical years for modeling? (longer span = more change samples; branch by item 1)
     · Esri: 2017, 2025 two epochs (recommended, longest span = most change samples) / 2017, 2021, 2025 three epochs / other years
     · CLCD: 2000, 2020 two epochs (recommended, longest span = most change samples) / 2000, 2010, 2020 three epochs / other years
     · WorldCover: 2020, 2021 two epochs (recommended, this source has only these two) / other years
     · Own data: ask the user for the year of each file directly
  3. Area-demand method (**default recommendation is markov, hard-coded**, user decision 2026-11-13; when the target year is off the integer cycle, handle it per item 6's interpolation rules — do not change the recommendation because of that):
     · Markov chain (recommended; standard method for two historical epochs)
     · Linear regression (more suitable with three historical epochs)
  4. Do you want a backtest accuracy check first:
     · Yes, produce Kappa/FoM (recommended; the backtest validates against a historical year)
     · No, pure prediction (target year is after the latest year; no real map to compare)

Round 2 · backtest mode / prediction settings / policy constraints
  5. Which backtest mode? (validation year = latest year; fill [first]/[latest] per the chosen epochs)
     · Simulate from the [first]-year map to [latest] using the [latest] year's real areas (recommended)
     · Simulate from the [first]-year map to [latest] using predicted areas (needs three historical epochs)
  6. Do you need intermediate transition-year maps?
     · No, only the [target] map (recommended)
     · Yes (every candidate must be written as "every N years, X epochs in total: full year list", e.g. "every 5 years, 2 epochs: 2030, 2035")
     Sequence semantics: intermediate epochs = one every N years after the latest year, up to the target year; the target year is always last.
     **When markov conflicts with continuous prediction** (target/intermediate years off the integer cycle), show a three-way choice:
       ① Markov chain + piecewise interpolation (recommended, **hard-coded**, user decision 2026-11-13; off-cycle years interpolate demand from the nearest reachable years)
       ② Switch to linear regression, keep the transition maps
       ③ Keep Markov, only the target-year map

Round 3 · policy & output
  8. Which transition matrix?
     · Regional customization (AI decides automatically) (recommended): the AI gathers info about the region (water bodies, ecological red lines, drinking-water sources, relevant laws and literature) and sets rules from literature and policy; if no special constraints, it falls back to the default template and says so.
       **The "依据" (basis) field of every matrix rule must be written in English** — the summary report prints it verbatim and the report is fully English (2026-11-18).
       **Whether water is locked is part of the matrix rules and is decided here**: if the search shows the region's water matters (major river/lake/water source) → add "water → others forbidden" to the matrix rules automatically (attach the basis); if water is not important → do not lock, and explain why.
       **Water-scarce cities / water-source protection areas must use a two-way lock** (no out-conversion + no in-conversion): out-only lock lets other classes "pour into" water per historical probabilities and inflate it (Zhengzhou 2026-11-13 measured +32%); two-way lock freezes the water area;
       regions with ecological water replenishment / new water-surface plans may allow in-conversion, with the basis attached.
     · Default template (forest/built-up irreversible; all other classes convertible)
     · I define the rules myself (user gives specific rules)
  9. Driving-factor source:
     · Auto-download the default 17 factors (recommended)
     · I provide them (an input box for the folder path follows immediately; files named df_*.tif; inconsistent grids are auto-aligned; all-zero factors are rejected)
  10. Where to store outputs? (must show the full path)
     · Default directory (recommended): C:\Users\<username>\plus_skill_GIS_data\<region name>
     · I specify (an input box for the path follows immediately)
  11. Reclassification mapping: automatic (recommended, zero-pixel classes are auto-merged) / custom JSON
```

Execute only after all items are answered.

**When item 1 = "own data", or item 1b = Stanford**: immediately pop an input box for the data folder path (if the naming is irregular, guide the user to state each file's year); **ask for the dataset name** ("which product is this? CNLUCC/GlobeLand30/GLC_FCS30/MODIS/ESA CCI/FROM-GLC/GlobCover, or unknown?") → match it against the "Built-in legend library" below: a match → use the corresponding source key (e.g. cnlucc) in the answers, no legend table needed; no match → lulc_source=user, and the user must supply a classification legend JSON ({"code": "semantic name"} — the AI guides the user, or researches the legend and confirms it with the user; **the AI must never guess a legend**).

## Built-in legend library (for user-provided tifs; a match means no legend table needed)

| Dataset the user names | `--lulc-source` key | Years | Resolution | Legend basis |
|---|---|---|---|---|
| CNLUCC (CAS RESDC) | cnlucc | 13 epochs, 1980–2025, discontinuous | 30m | 6 first-level classes; second-level codes auto-merge |
| GlobeLand30 (MNR China) | globeland30 | 2000/2010/2020 | 30m | 10 classes: cropland/forest/grassland/shrub/wetland/water/tundra/built-up/bare/glacier→bare |
| GLC_FCS30 (AIRCAS) | glc_fcs30 | 1985-2022 | 30m | 35 second-level codes merged into 9 semantic classes |
| MODIS MCD12Q1 (IGBP) | modis_igbp | 2001-2023 annual | **500m (coarse; noted in the report)** | 17 classes merged into 9 semantic classes |
| MODIS MCD12Q1 (UMD) | modis_umd | 2001-2023 annual | **500m (coarse)** | 16 classes merged into 9 semantic classes; **⚠️ UMD's 0 = water conflicts with PLUS's 0 = background — re-code water 0 (e.g. 0→18) before upload, otherwise the pipeline errors out** |
| ESA CCI | esa_cci | 1992-2020 annual | 300m | 37 classes merged into 9 semantic classes |
| GlobCover (ESA MERIS) | globcover | 2005-06/2009 | 300m | 22 classes merged into 9 semantic classes |
| FROM-GLC (Tsinghua, Gong Peng) | from_glc | 2015 (30m) / 2017, 2019 (10m) | 30m/10m | 10 classes: tundra→grassland, snow/ice→bare |
| Unknown system | user | any | any | `--lulc-legend-json` required |

All of the above use the "manual download → folder via --lulc-dir" mode: the skill auto-recognizes years from filenames, auto-reclassifies, and everything downstream is identical to the auto-download channels (auto uint8 conversion, boundary cropping, multi-epoch grid alignment, value-range vs legend check, out-of-legend check, etc. run automatically inside the scripts and print to the console — the AI does not need to manage them step by step). The user only needs to provide **GeoTIFF format** data (convert HDF/NetCDF with GIS software first).

## Data source registration guide (CLCD only; all other sources are user-downloaded and provided as a folder — no registration guidance)

**CLCD (NCDC platform, annual 1990-2022; choose it when years before 2017 are needed)**:
1. Open the National Cryosphere Desert Data Center: https://ftp.ncdc.ac.cn (register an account)
2. After login, search the dataset catalog for "CLCD" (China Land Cover Dataset, Wuhan University, Yang & Huang)
3. Click "Apply for download" (data basket) → fill in the reason (e.g. "scientific land-use simulation") → submit and wait for platform approval (usually fast)
4. After approval, the platform provides **FTP credentials** (or they are visible in the account center)
5. Put the credentials in `C:\Users\<username>\.plus-full\ftp_config.json` in this format:
   ```json
   {"host": "ftp.ncdc.ac.cn", "port": 2121, "username": "your-account", "password": "your-password",
    "file_template": "CLCD_v01_{year}_albert.tif"}
   ```
   or simply tell the AI the credentials and let it write the file.
6. Re-run the download afterwards; the skill picks up the new credentials automatically.

**All other sources (CNLUCC/GlobeLand30/GLC_FCS30/MODIS/GlobCover/FROM-GLC etc.) get no registration guidance**: the user downloads the data themselves → provides the folder via "my own multi-year tifs" → the skill identifies the source (see the legend library table) → automatic preprocessing and simulation. The skill's job = correct identification and processing once the data is in hand — registration/downloading is out of scope.

## Execution

```
# Backtest (recommended mode; Esri two epochs 2017/2025 example, no registration)
python scripts/run_full.py --region 郑州市 --years 2017,2025 --predict 2025 --lulc-source esri --backtest train
# Backtest (recommended mode; CLCD two epochs 2000/2020 example, NCDC credentials required)
python scripts/run_full.py --region 鄂州市 --years 2000,2020 --predict 2020 --backtest train

# Prediction (single target year; Esri: from latest year 2025 onward)
python scripts/run_full.py --region 郑州市 --years 2017,2025 --predict 2030 --lulc-source esri
# Prediction (single target year; CLCD: from latest year 2020 onward)
python scripts/run_full.py --region 鄂州市 --years 2000,2020 --predict 2050

# Continuous prediction: 2025→2035 every 5 years → 2030, 2035 (target year is always last; Esri latest year 2025 example)
python scripts/run_full.py --region 郑州市 --years 2017,2025 --predict 2035 --sequence 5 --lulc-source esri --demand linear

# Backtest, two modes: real areas (recommended, --backtest train) / predicted areas (main paper number, needs 3 epochs, --backtest predict)
python scripts/run_full.py --region 鄂州市 --years 2000,2010,2020 --predict 2020 --backtest predict
# (--backtest real remains as an experimental parameter: real areas, CARS starts from the middle year; no longer shown in dialogs)

# Water locked against conversion (when the user chose "lock" in the Q&A)
python scripts/run_full.py --region 济南市 --years 2000,2010,2020 --predict 2035 --water lock

# WorldCover 30m (explicit; or auto-fallback when the 30m CLCD channel fails)
python scripts/run_full.py --region 鄂州市 --years 2020,2021 --predict 2025 --lulc-source worldcover
# 10m resolution (WorldCover native; only 2020/2021, small regions)
python scripts/run_full.py --region 鄂州市 --years 2020,2021 --predict 2025 --lulc-source worldcover --lulc-res 10

# User-supplied driving factors (skips auto-download; df_*.tif naming is enough, inconsistent grids are auto-resampled/aligned)
python scripts/run_full.py --region 鄂州市 --years 2010,2015,2020 --predict 2030 --drivers-dir D:\my_factors

# CNLUCC (RESDC, provided after manual download; built-in 6-class legend auto-reclassifies, second-level codes auto-merge)
python scripts/run_full.py --region 鄂州市 --years 2000,2010,2020 --predict 2030 --lulc-source cnlucc --lulc-dir D:\cnlucc_data

# User's own data (unknown classification system: must provide the legend {code: semantic name})
python scripts/run_full.py --region 鄂州市 --years 2000,2010,2020 --predict 2030 --lulc-source user --lulc-dir D:\my_lulc --lulc-legend-json "{\"1\":\"耕地\",\"2\":\"林地\",\"3\":\"水域\"}"

# Regenerate only the single summary report (no re-modeling; reuses existing products)
python scripts/make_report.py --data-dir ~/plus_skill_GIS_data/371700 --project project_full_2030.json
```

- Region names are Chinese administrative divisions (used by the boundary service).
- Interpreter: any Python 3.10–3.13 (see below for machine migration)
- **Single report**: `run_full.py` produces exactly one `<output dir>/summary_report.md`; per-step md files (download / factors / reclassification / modeling) are archived under `logs/sub_reports/`. `make_report.py` can regenerate this report anytime without re-running the modeling (reads `report.json` + `area_stats.csv` + `timing.json`; whichever is missing, that section is skipped)
- **Continuous prediction (--sequence) requirements**: prediction mode only; use the linear demand method (any year) — markov only supports integer cycles; demand is computed per epoch; CARS chains in chronological order (latest year → intermediate epochs … → target year); products = one simulated map per epoch + one multi-epoch comparison figure + a single target-year figure (`simulation_<target year>.jpg`). **`--sequence N` = interval in years; intermediate epochs run up to the target year, and the target year is always last** (example: 2025→2035 interval 5 → 2030, 2035; interval 3 → 2028, 2031, 2034, 2035; see FAQ.md F3)
- **Backtest choice (--backtest)**: `train` = real areas, starting from the first year (recommended mode; demand = real validation-year areas); `predict` = predicted areas, starting from the first year (main paper number, needs 3 epochs); `real` = real areas, starting from the middle year (experimental parameter, no longer in dialogs)
- **Accuracy source in prediction reports**: when a pure prediction has no real map to compare, `make_report.py` automatically looks for a backtest result with `metrics` in the same region directory (prefers directories whose name contains `bt`), and cites its Kappa/OA/FoM and change contingency table in a "Reliability reference" subsection (noting the mode; it reflects placement ability only); only if none is found does it suggest running `--backtest train`
- **Water lock (--water lock)**: locks the entire water row (only self-conversion, no out-conversion), protecting major rivers/lakes/reservoirs; it changes the simulation numbers (locked water no longer shrinks) and differs from previously finalized historical numbers — a re-run is required

## Troubleshooting protocol (fixed steps when the engine errors or results look wrong — do not skip)

1. **Step 1: check the bundled manual's "Common problems" chapter**. Open `docs/tutorial-1-plus-model-principles-and-software-intro-20250531.pdf` chapter 5, or first check the "error code / symptom" index in `docs/troubleshooting.md`, matching entries 5.1–5.8 (0xC0000005 crash → 5.8 "land expansion map missing one or more land-use classes").
2. If it matches → apply the manual's solution, and record "symptom → matched entry → outcome" in the run log (`<data_dir>/logs/`).
3. If it does not match → check the package's root `FAQ.md` (known pitfalls of the skill's own flow: auto-effective breakpoints, --sequence epoch counts, missing classes in the expansion map, report data source, target-practice analogy).
4. Still no match → follow "Automated handling rules" below; if that does not solve it either, **report to the user with the engine's original error text and run logs** — do not guess or change parameters on your own.

## Environment & dependencies (machine migration)

1. **Python**: 3.10–3.13 (tested 3.11.9 / 3.13.14). Create a venv, then `pip install -r requirements.txt` (rasterio/numpy/scipy/shapely/requests/matplotlib/pillow; the OSM pbf channel additionally needs osmium). **In China, switch the pip mirror first**, otherwise the default PyPI source runs at 60–70 kB/s: `pip install -i https://mirrors.aliyun.com/pypi/simple/ -r requirements.txt`.
2. **PLUS engine**: **bundled in the package** (`runtime\plus-backend\`, distributed with the authorization of PLUS author Prof. Xun Liang) — zero configuration on a new machine; `python scripts/setup.py --from-backend <existing engine dir>` can still rebuild from any engine directory and generate the 9 bat launchers. Engine path resolution order = env var `PLUS_BACKEND` > `scripts/config.json` > bundled default.
3. **Data root**: `--output` (root) or `--data-dir` (points directly at one region's directory); default = `plus_skill_GIS_data` under the user's home directory (portable across machines).
4. **Windows only**: the engine is a Windows binary, and paths must not contain Chinese characters or spaces (the scripts self-check this).
5. **Credentials are not in the package**: the NCDC FTP account lives in `~/.plus-full/ftp_config.json` (or `PLUS_FTP_CONFIG`); when missing, the download step errors out — it never silently degrades.

## Stages (①→⑨)

1. **①Land-use download**: Esri Land Cover (no registration, annual 2017-2025, server-side cropping by extent) / CLCD (NCDC FTP, per-province package fallback + national grid alignment, credentials required) / WorldCover (AWS S3 tiles, only 2020/2021, 10m→30m majority resampling, Albers projection); all cropped to the boundary, grids force-aligned across epochs; **user-provided data** (CNLUCC/own/Stanford: `--lulc-dir` points at the folder, filenames matched by 4-digit year and auto-imported, download skipped; CNLUCC has a built-in 6-class legend, own/Stanford need `--lulc-legend-json`)
2. **②Driving factors**: default 17 auto-downloaded (terrain/climate/population/road-water distances, auto-aligned to the reference raster; existing grid-consistent factors are reused directly) / user-supplied folder (`--drivers-dir`: df_*.tif; inconsistent grids/projections are **auto-resampled and aligned**, valid values must not be all-zero — rejected otherwise)
3. **③Semantic reclassification**: built-in source legends (CLCD 9 classes); automatic mapping = union of per-epoch classes → consecutive codes
4. **④Check & convert**: code continuity / uint8 / nodata validation + conversion to PLUS format (rasterio fast path, pixel-identical with engine products)
5. **⑤Modeling**: expansion → LEAS (random forest) → demand (markov/linear) → CARS patch simulation; (with --sequence, additional epochs are chained)
6. **⑥Accuracy**: Kappa/OA/FoM (10% sampling, fixed seed, pure Python — does not depend on the engine's validate module, which can hang)
7. **⑥bError decomposition** (on by default for predicted-area backtests; auto-skipped when the main mode already uses real areas): runs one more CARS with "demand = real areas" (same starting point), splitting FoM into quantity-error contribution and placement-error loss
8. **⑦Figures**: simulated / real maps → 300 dpi JPG (legend, scale bar, north arrow **all inside the frame**); legend columns adapt to class count (≤4 single / 5–8 double / >8 triple), bottom blank area adapts — never overlapping the map, never overflowing; **also produces a land-use evolution GIF** (all historical + simulated years in chronological order, lightweight frames with year labels, looping; requested by the user 2026-11-13 as a deliverable)
9. **⑧Single summary report + ⑨cleanup**: generated uniformly by `make_report.py` at `<output dir>/summary_report.md` — task parameters, data & factors, reclassification, accuracy (predictions automatically cite the region's backtest), area statistics & change highlights, product list, known limitations, per-step timings; **the download report / drivers report / reclassification notes / modeling report are all archived under `<data_dir>/logs/sub_reports/` — never scattered in the data directory**; temporary leftovers (.part / engine intermediate maps) are cleaned; full per-substep logs go to `<data_dir>/logs/`

**Target-year convention**: in continuous prediction, "target year" = the last year of the sequence (e.g. `--predict 2030 --sequence 5` → 2025, 2030, target year 2030). The report's title, target-year row, product list, and single-year figure (`simulation_2030.jpg`) all use the target year — never pass off an intermediate epoch as the task's target year.

## Automated handling rules (do not intervene manually)

- **Driving factors use only genuinely downloaded data (set by the advisor 2026-11-10, hard rule — do not change)**: if any factor download fails → error out and stop, go through `--manual` / manual handling; **never substitute any driving factor or modeling input with self-generated data (all-zero, random, or constant surfaces, i.e. "synthetic placeholder factors")** — synthetic factors make LEAS/CARS produce results that look normal but are scientifically meaningless; that is worse than failing. This skill provides no such option — do not write one yourself.
- **Zero-pixel class auto-merge**: when a class has 0 pixels in the starting year (markov would compute 0/0=NaN), first run a cause analysis on "location + trajectory across years"; if a built-in literature rule matches → **auto-merge** (e.g. bare land → built-up/cropland/grassland) and record it in the mapping and reclassification notes, then continue; stop for manual handling only when no rule matches. After merging, the class name may be like `bare/impervious`; the default matrix recognizes aliases for irreversible classes.
- **Tiny-class warning**: when a class in the final year has <1000 pixels (≈0.9 km²), warn "merging recommended" (not forced) — CARS cannot generate independent patches for it, and its accuracy contribution has no statistical meaning.
- **Grid consistency**: grids of all epochs and factors are validated before modeling; on inconsistency, error out and stop (listing the parameters) — **user data is never auto-deleted**.

## Known limitations (must be told to the user honestly)

1. **FoM is the real indicator of placement ability; Kappa is not**: in Jinan, OA was 88.9%/Kappa 0.81, yet FoM was only 0.062 (the changes are almost entirely propped up by the 90% unchanged pixels). With real-area demand, FoM rose to ≈0.14 — half the error is quantity, half is placement.
   **Target-practice analogy (use plain language when explaining FoM)**: computing FoM is like target practice — in high-change regions the target is big and easier to hit, so FoM is high; in low-change regions the target is small and harder to hit, so FoM is low.
   **Year rule**: nearer years (short prediction span) → fewer changes → Kappa naturally high, FoM low; farther years (long span) → more changes (bigger target) → FoM relatively high, Kappa falls back. Metrics with different prediction spans cannot be compared directly — check the span first when interpreting.
2. Climate data is 2.5° (NCEP/CMAP; WorldClim/CHELSA unreachable from China); population defaults to 2020.
3. OSM roads/water have omissions inside China; distance-factor accuracy is limited by OSM completeness.
4. The default matrix **does not lock water** (only forest/built-up): in cities with major river basins the water surface may shrink out of nowhere; a warning is printed before modeling. To protect it, forbid conversion in `matrix_restrictions` (changes historical numbers; re-run required).
5. Parameters are the bundled manual's defaults (neighborhood 3 / diffusion 0.1 / patch 0.2 / seed 0.1); parameter tuning is future work.
6. Large regions (province-level) take long in the engine: CARS already uses 8 threads; LEAS is single-threaded and may take >1 hour.
7. **Do not run two tasks concurrently on one machine**: engine parameter files are fixed at `plus-backend\PLUS_*.tmp`; concurrent runs overwrite each other (directory-level isolation is future work).

## License & distribution

- **CLCD**: scientific, educational, non-commercial use (users must comply with the Yang & Huang 2021 data agreement themselves).
- **PLUS engine (PLUS.exe)**: bundled (`runtime\plus-backend\`); PLUS author Prof. Xun Liang has authorized this skill to distribute it (GitHub and direct distribution are the same package); `setup.py --from-backend` only copies and generates bat files — it contains no private code.
- **Bundled manual PDFs** (three tutorials in `docs\`): shipped with the package; purpose = troubleshooting (see "Troubleshooting protocol"); copyright belongs to HPSCIL — do not redistribute them separately.
- **NCDC FTP account**: not committed, not packaged; externalized as described above.
