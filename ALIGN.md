# plus-automation-en — Alignment & Drift Notes (中文版 ↔ English pack)

This pack is a translated copy of `plus-automation` (方案 B: independent English pack).
The Chinese dev version is the **source of truth for logic**; this pack is the **source of truth for English wording**.
When the two drift, logic changes flow 中文版 → this pack, and never the reverse (sync.py is one-way, same rule).

## 1. Translation scope (what was translated)

| Item | Chinese version | English pack |
|---|---|---|
| SKILL.md (incl. dialog wording) | `plus-automation\SKILL.md` | `SKILL.md` (name: `plus-automation-en`) |
| FAQ.md | `FAQ.md` | `FAQ.md` |
| README.md | `README.md` | `README.md` |
| Install guide | `安装说明.md` | `INSTALL.md` |
| Data sources & copyright | `数据来源与版权说明.md` | `DATA_SOURCES.md` |
| Troubleshooting index | `docs\常见问题速查.md` | `docs\troubleshooting.md` |
| Manual PDFs (renamed, content still Chinese) | `docs\教程一…pdf` | `docs\tutorial-1-…pdf` |
| | `docs\教程二…pdf` | `docs\tutorial-2-…pdf` |
| | `docs\plus模型原理和软件介绍-v3.pdf` | `docs\plus-model-principles-v3.pdf` |
| Dialog text (script) | `scripts\ask_questions.py` questions()/validate() | same file, English strings |
| Summary report template | `scripts\make_report.py` | same file, English template |

## 2. Product-file naming (English pack uses English names)

| Chinese version | English pack |
|---|---|
| 汇总报告.md | `summary_report.md` |
| 下载报告.md | `download_report.md` |
| CLCD下载报告.md | `clcd_download_report.md` |
| 驱动因子报告.md | `drivers_report.md` |
| 重分类说明.md | `reclass_notes.md` |
| 报告.md (modeling) | `pipeline_report.md` |
| 面积统计.csv | `area_stats.csv` |
| logs\子报告\ | `logs\sub_reports\` |
| CSV 列 `{year}模拟` / 行 `地类/类别N/合计` | `{year}_sim` / `class/class_N/total` |

Files carrying these strings (must be edited together if renamed again):
`make_report.py`, `run_full.py`, `run_pipeline.py`, `download_lulc.py`,
`download_drivers.py`, `reclassify_lulc.py`, `smoke_test.py`.

## 3. NOT translated (deliberately, per user decision 2026-11-17)

- Code comments and docstrings — kept in Chinese (both packs).
- Internal `print`s in scripts — kept in Chinese.
- Sub-report **contents** (download_report / drivers_report / reclass_notes / pipeline_report)
  — file names are English, contents are still Chinese. `make_report.py` excerpts the
  `## 特殊情况 / ## Special cases` heading from reclass_notes (both patterns accepted).
- Land-class semantic names (CLCD legend in `reclassify_lulc.py`, legend labels in
  `landuse_map.py`, synonym groups in `run_pipeline.py`) — **data-level Chinese strings**.
  English-pack figures/matrices will therefore show Chinese class names. Changing them touches
  reclassification output, matrix matching and reports — treat as a separate project if ever needed.
- The three manual PDFs — contents remain Chinese (copyright HPSCIL; referenced by English names).

## 4. Known product-level limitations of the English pack (not translation bugs)

- `--region` takes **Chinese administrative division names** (DataV boundary service is China-only).
  Non-China study areas must use the "own data" path (all downloads except CLCD work globally,
  but region boundary retrieval does not).
- Registration guide (CLCD) targets Chinese platforms (NCDC); kept in English for completeness.

## 5. Drift-alignment procedure (run when the Chinese version changes logic)

1. Diff the two script trees, ignoring wording:
   ```
   diff -rq D:/plus_skill/plus-automation/scripts D:/plus_skill/plus-automation-en/scripts
   ```
2. For every logic-only change in the Chinese version (any change that is not a translated string),
   port it to this pack with `Edit` — **never copy the Chinese file over** (that would destroy
   the English translations).
3. For wording changes in the Chinese version (option text, report sentences, rules), translate
   the change and apply it here.
4. After porting, re-run:
   - `python -m py_compile` on all edited scripts
   - `python scripts/ask_questions.py --dump` (check English output)
   - a synthetic `make_report.py` run (see 冒烟 fixture pattern used on 2026-11-17)
5. Document non-synced diffs here (date + list), so the drift is always visible.

## 6. Fixes made in the English pack first (pending backport decision)

- **2026-11-17**: `make_report.py` `_head_src` in `build_report` was missing the `esri` key →
  Esri-source reports said "user-supplied …" in the opening line. Verified by live run (opening line
  said "user-supplied" while the parameter table said "Esri" — self-contradictory), fixed here by
  adding `"esri": "Esri Sentinel-2 10m "`. **Backported to the Chinese dev version the same day
  (user confirmed after verification), synced to both installed platforms, and pushed to GitHub
  HPSCIL/PLUS-automation (commit d18e610).**
- Minor English typography (spaces after punctuation in the accuracy line and change highlights) —
  English-only, no backport needed.
