#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""合并式汇总报告生成器(plus-automation 唯一报告出口)

设计原则:
1. 一个研究区只产出**一份** Markdown 报告: `<输出目录>/汇总报告.md`
2. 下载报告 / 驱动因子报告 / 重分类说明 / 建模报告 全部归档到 `logs/子报告/`,
   正文只摘取要点,避免用户在一堆 md 里翻找
3. 目标年以"连续预测序列的末年份"为准(--predict 2030 --sequence 5,2 → 目标 2040),
   不再把主模拟年当成任务目标年
4. 可独立运行:不重跑建模也能重生报告
   `python scripts/make_report.py --data-dir ~/plus_skill_GIS_data/<研究区> --project project_full_2030.json`

输入(缺哪个就跳过哪节,不报错):
  项目配置 project_full_*.json / 建模产物 report.json / 面积统计.csv / 各子报告 md / timing.json
"""
import csv
import json
import os
import re
import shutil
import sys

# 控制台编码防护:中文 Windows 默认 GBK,打印 ✅ 等符号会崩(2026-11-10 郑州报告重生实测)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import force_utf8

force_utf8()

SUBDIR = "sub_reports"     # archive subdirectory (logs/sub_reports)
REPORT_NAME = "summary_report.md"

# sub-report → (short label, location data|out, relative path, archived filename, one-line description)
SUB_REPORTS = [
    ("CLCD download report", "data", "download_report.md", "clcd_download_report.md",
     "data source, epochs, cropping extent and validation results"),
    ("Drivers report", "data", os.path.join("drivers", "drivers_report.md"), "drivers_report.md",
     "sources of the 17 factors and grid alignment"),
    ("Reclassification notes", "data", "reclass_notes.md", "reclass_notes.md",
     "semantic mapping, zero-pixel merges, special cases"),
    ("Modeling report", "out", "pipeline_report.md", "pipeline_report.md",
     "expansion/probability/demand/CARS step-by-step outputs"),
]


# ---------------- 小工具 ----------------
def _read(path):
    try:
        with open(path, encoding="utf-8") as f:
            return f.read()
    except Exception:
        return None


def _load_json(path):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def _num(x, nd=2):
    try:
        return f"{float(x):,.{nd}f}"
    except Exception:
        return "—"


def _signed(x, nd=2):
    try:
        v = float(x)
        return f"{v:+,.{nd}f}"
    except Exception:
        return "—"


def _pct(cur, base):
    try:
        cur, base = float(cur), float(base)
        if abs(base) < 1e-9:
            return "—"
        return f"{(cur - base) / base * 100:+.1f}%"
    except Exception:
        return "—"


def _year_of(col):
    """'2040模拟' → 2040;'2020' → 2020"""
    digits = "".join(ch for ch in str(col) if ch.isdigit())
    return int(digits) if digits else None


def read_area_table(csv_path):
    """读 面积统计.csv → (列名列表, 年份列表, {类名: {列名: 值}})"""
    if not os.path.exists(csv_path):
        return None
    try:
        with open(csv_path, encoding="utf-8-sig") as f:
            rows = list(csv.reader(f))
    except Exception:
        return None
    if len(rows) < 2:
        return None
    cols = rows[0][1:]
    table = {}
    order = []
    for r in rows[1:]:
        if not r or not r[0]:
            continue
        name = r[0]
        vals = {}
        for c, v in zip(cols, r[1:]):
            try:
                vals[c] = float(v)
            except Exception:
                vals[c] = 0.0
        if name == "total":
            table["_total"] = vals
        else:
            table[name] = vals
            order.append(name)
    return order, cols, table


def archive_sub_reports(data_dir, out_dir):
    """把分步 md 报告归档到 logs/子报告/,返回归档清单 [(简称, 原路径, 归档路径)]"""
    dest_root = os.path.join(data_dir, "logs", SUBDIR)
    moved = []
    for label, base, rel, dst_name, _desc in SUB_REPORTS:
        root = out_dir if base == "out" else data_dir
        src = os.path.join(root, rel)
        if not os.path.exists(src):
            continue
        try:
            os.makedirs(dest_root, exist_ok=True)
            dst = os.path.join(dest_root, dst_name)
            shutil.move(src, dst)
            moved.append((label, src, dst))
        except Exception as e:
            print(f"  ⚠️ archive failed {src}: {e}")
    return moved


def _data_source(proj, data_dir):
    """数据源判定:project.data_source 优先;旧项目(无此字段)按 CLCD 下载报告推断。

    2026-11-10 导师实测:模板曾写死"CLCD 30m",自有数据也被写成 CLCD,故参数化。
    """
    ds = proj.get("data_source")
    if not ds:
        ev = [os.path.join(data_dir, p) for p in
              ("clcd_download_report.md", "download_report.md",
               os.path.join("logs", "sub_reports", "clcd_download_report.md"))]
        ds = "clcd" if any(os.path.isfile(p) for p in ev) else "user"
    return ds


# ---------------- 正文各部分 ----------------
def _sec_meta(proj, predict, target, seq, region, backtest, water, mapping, factors):
    L = []
    L.append("## 1. Task & parameters\n")
    L.append("| Item | Setting |")
    L.append("|---|---|")
    L.append(f"| Study region | {region} |")
    _ds = _data_source(proj, proj.get("data_dir") or "")
    _wc = ("ESA WorldCover 10m global land cover (v100/v200, native 10m; CC BY 4.0)"
           if proj.get("lulc_res") == 10
           else "ESA WorldCover 10m global land cover (v100/v200, resampled 30m; CC BY 4.0)")
    _src = {"clcd": "CLCD 30m annual data (CAS, Yang & Huang 2021)",
            "worldcover": _wc,
            "esri": "Esri Sentinel-2 10m annual land cover (annual 2017-2025, aggregated to 30m; CC BY 4.0)",
            "cnlucc": "CNLUCC 30m multi-epoch land use (CAS RESDC, Xu Xinliang et al.; 13 epochs, downloaded manually)",
            "globeland30": "GlobeLand30 30m land cover (MNR China; 2000/2010/2020, downloaded manually)",
            "glc_fcs30": "GLC_FCS30 30m fine land cover (AIRCAS; 1985-2022, downloaded manually)",
            "modis_igbp": "MODIS MCD12Q1 IGBP 500m land cover (annual 2001-2023, coarse resolution, downloaded manually)",
            "esa_cci": "ESA CCI 300m land cover (annual 1992-2020, downloaded manually)",
            "from_glc": "FROM-GLC land cover (Tsinghua, Gong Peng's team; 30m 2015 / 10m 2017·2019, downloaded manually)",
            "globcover": "GlobCover 300m land cover (ESA MERIS; 2005-06/2009, downloaded manually)",
            "modis_umd": "MODIS MCD12Q1 UMD 500m land cover (annual 2001-2023, coarse resolution, downloaded manually)",
            "stanford": "Stanford derived data (downloaded via proxy, user-provided)",
            "user": "User-supplied land-use data (per-year tifs provided by the user)"}
    L.append(f"| Data source | {_src.get(_ds, _src['user'])} |")
    L.append(f"| Training period | {proj.get('early_year')}–{proj.get('late_year')} |")
    if seq:
        yrs = " / ".join(str(s["year"]) for s in seq)
        L.append(f"| Prediction years | {yrs} (chained, each epoch continues from the previous one) |")
        L.append(f"| **Target year** | **{target}** |")
    else:
        L.append(f"| **Target year** | **{target}** |")
    L.append(f"| Area demand method | {proj.get('demand')}"
             + (" (Markov chain, off-cycle years via piecewise interpolation)" if proj.get("demand") == "markov" else "") + " |")
    _bt = {"none": "No (pure prediction)", "real": "Real-area diagnostic (quantity given, placement only)",
           "predict": "Predicted-area backtest", "train": "Full training period (in-sample)"}.get(backtest, backtest)
    L.append(f"| Backtest | {_bt} |")
    L.append(f"| Validation mode | {'in-sample' if proj.get('validation_mode') == 'in' else 'out-of-sample'} |")
    locked = proj.get("locked_classes") or []
    L.append(f"| Water handling | {'locked, no out-conversion (' + ', '.join(locked) + ')' if locked else 'not locked'} |")
    L.append(f"| Transition matrix | default template (forest/built-up irreversible)" + (
        "; regional customization " + "; ".join(f"{r.get('from')}→{r.get('to')}" for r in
                                (proj.get("matrix_restrictions") or []))
        if proj.get("matrix_restrictions") else "") + " |")
    L.append(f"| Reclassification | {'custom mapping' if mapping else 'automatic (union of classes → consecutive codes)'} |")
    _drv = ("user-supplied (checked: grid-consistent and not all-zero)" if proj.get("drivers_source") == "user"
            else "default 17 auto-downloaded: terrain/climate/population/distance/soil")
    L.append(f"| Driving factors | {factors} items ({_drv}) |")
    L.append(f"| Data directory | `{proj.get('data_dir') or ''}` |")
    L.append("")
    return L


def _history_years(data_dir):
    """从裁切文件反推历史期次(lulc_YYYY_rc_uc.tif),不依赖项目配置"""
    ys = []
    try:
        for f in os.listdir(data_dir):
            if f.startswith("lulc_") and f.endswith("_rc_uc.tif"):
                y = f[5:9]
                if y.isdigit():
                    ys.append(int(y))
    except Exception:
        pass
    return sorted(ys)


def _sec_data(data_dir, proj, factors):
    L = []
    L.append("## 2. Data & driving factors\n")
    # raster spec: taken from the latest-year cropped map
    late_tif = proj.get("late") or ""
    spec = ""
    try:
        import rasterio
        if late_tif and os.path.exists(late_tif):
            with rasterio.open(late_tif) as s:
                proj_name = (s.crs.to_dict().get("proj") if s.crs else "") or ""
                crs_txt = "Albers equal-area (aea)" if proj_name.lower() == "aea" else (proj_name or "—")
                spec = (f"{s.width}×{s.height} px, {abs(s.res[0]):.0f} m resolution, {crs_txt}")
    except Exception:
        pass
    hys = _history_years(data_dir)
    L.append(f"- Base raster: {spec or 'see sub-reports'}")
    L.append(f"- Land-use epochs: {', '.join(str(y) for y in hys) if hys else 'see sub-reports'}"
             f" (cropped to the study boundary, one unified grid across the chain)")
    if proj.get("drivers_source") == "user":
        L.append(f"- Driving factors: {factors} items (user-supplied, checked: grid-consistent with the "
                 f"reference map and not all-zero; factor meanings and sources follow the user's notes)")
    else:
        L.append(f"- Driving factors: {factors} items, incl. elevation/slope/aspect, annual mean "
                 f"temperature/precipitation, population, distances to roads of all levels/railways/water/"
                 f"government seats, and soil")
        L.append("- Known factor shortcomings: climate data at 2.5° coarse resolution (NCEP/CMAP); OSM roads "
                 "and water have omissions inside China, and distance-factor accuracy is limited by OSM completeness")
    L.append("")
    return L


def _sec_matrix(proj):
    """## 3b. Transition matrix rules: baseline + changes + basis (user request 2026-11-10:
    the report must state what was changed)

    Default-template baseline = forest/built-up irreversible; regional customization / user-defined
    list every difference and its basis here; water locking is also explained here from the matrix viewpoint.
    """
    L = ["## 3b. Transition matrix rules\n"]
    locked = proj.get("locked_classes") or []
    rests = proj.get("matrix_restrictions") or []
    L.append("- Baseline: default template — forest and built-up are irreversible (no out-conversion once "
             "formed); all other classes convert freely")
    if locked:
        # Zhengzhou 2026-11-13 test: out-only lock lets other classes "pour into" water
        # per historical probabilities (+32%); if the matrix also bans "in-conversion to water",
        # the text says "two-way lock"
        _to_water_banned = any((r.get("to") == w or r.get("to") in locked)
                               and not r.get("allow", True) for r in rests for w in locked)
        L.append(f"- Water handling: {', '.join(locked)} "
                 + ("two-way lock (out-conversion banned, in-conversion from other classes also banned, "
                    "area frozen)"
                    if _to_water_banned
                    else "out-conversion banned only, in-conversion not banned (other classes may still "
                         "convert in per historical probabilities; area may grow)"))
    if rests:
        L.append("- **Regional customization** (changes vs the default template, %d in total):" % len(rests))
        for r in rests:
            allow = "forbidden" if not r.get("allow", True) else "allowed"
            line = f"  - {allow} {r.get('from', '?')} → {r.get('to', '?')}"
            if r.get("依据"):
                line += f"; basis: {r.get('依据')}"
            L.append(line)
    else:
        L.append("- No regional customization (default template used)")
    L.append("")
    return L


def _sec_reclass(data_dir, proj):
    """Extract the mapping and special cases from the reclassification notes / modeling report
    (files may already be archived; look them up at the archive paths)"""
    txt = _read(os.path.join(data_dir, "logs", SUBDIR, "reclass_notes.md"))
    L = ["## 3. Reclassification & special handling\n"]
    if not txt:
        return L + ["- See the archived reclassification notes.\n"]
    # extract the json mapping block
    mapping = None
    try:
        start = txt.index("{")
        end = txt.index("}", start) + 1
        mapping = json.loads(txt[start:end])
    except Exception:
        mapping = None
    if mapping:
        L.append("| Semantic class | Model code |")
        L.append("|---|---|")
        for k, v in mapping.items():
            L.append(f"| {k} | {v} |")
        L.append("")
    # only excerpt the "Special cases:" entry — do not swallow the whole notes
    # (code blocks included) into the report
    note = []
    hit = False
    for ln in txt.splitlines():
        if ln.startswith("## 特殊情况") or ln.startswith("## Special cases"):
            hit = True
            rest = re.split(r"(特殊情况|Special cases)", ln, 1)[-1].lstrip(":： ")
            if rest:
                note.append(rest)
            continue
        if hit:
            if ln.startswith("## ") or ln.startswith("# "):
                break
            s = ln.strip()
            if not s or s.startswith("```"):
                continue
            note.append(s)
    if note:
        L.append("**Special cases**: " + " ".join(note) + "\n")
    locked = proj.get("locked_classes") or []
    if locked:
        L.append(f"**Water lock**: {', '.join(locked)} whole row locked — self-conversion only, "
                 "no conversion to other classes; other classes may still convert into water "
                 "(so the water area may keep growing).\n")
    return L


def _find_backtest(data_dir, exclude_out):
    """在同研究区目录里找一份带精度指标的回测结果(供预测报告引用可靠性)"""
    best = None
    try:
        entries = os.listdir(data_dir)
    except Exception:
        return None
    for d in entries:
        if d == exclude_out:
            continue
        rj = _load_json(os.path.join(data_dir, d, "report.json"))
        if not rj or not rj.get("metrics"):
            continue
        # 回测的 sim 目录名通常带 bt / 目标年早于预测年
        score = 1 if "bt" in d.lower() else 0
        if best is None or score > best[0]:
            best = (score, d, rj)
    return (best[1], best[2]) if best else None


def _sec_accuracy(rj, backtest, proj, bt=None):
    L = ["## 4. Modeling & accuracy\n"]
    m = (rj or {}).get("metrics")
    dg = (rj or {}).get("diagnose") or {}
    if not m:
        L.append("This run is a **future scenario prediction** (target year after the historical data), "
                 "with no real map to compare, so this report does not output Kappa/FoM.")
        if bt:
            d, brj = bt
            bm = brj["metrics"]
            L.append(f"The backtest result of the same region and the same parameter set "
                     f"(directory `{d}`) serves as a reliability reference:\n")
            L.append("| Metric | Backtest value | Notes |")
            L.append("|---|---|---|")
            L.append(f"| Kappa | {bm.get('Kappa', 0):.4f} | overall agreement |")
            L.append(f"| Overall accuracy OA | {_num((bm.get('OA') or 0) * 100)}% | high unchanged-pixel share inflates it |")
            L.append(f"| FoM | {bm.get('FoM', 0):.4f} | placement ability on changed pixels |")
            A, B, C, D = bm.get("A"), bm.get("B"), bm.get("C"), bm.get("D")
            if None not in (A, B, C, D):
                L.append(f"| Change contingency (10% sample) | hits {A:,} / misses {B:,} / "
                         f"false alarms {C:,} / wrong class {D:,} | — |")
            L.append("")
            L.append("> This backtest is in **real-area diagnostic mode** (demand taken directly from the "
                     "validation year's real areas), so quantity is exactly right and its FoM reflects "
                     "placement allocation ability only — an upper bound of CARS capability; "
                     "the full mode (including quantity prediction) usually yields a lower FoM.\n")
        else:
            L.append("For reliability metrics, run a separate backtest with `--predict <latest year> --backtest real`.\n")
        return L
    ka, oa, fom = m.get("Kappa"), m.get("OA"), m.get("FoM")
    grade = "excellent" if (ka or 0) >= 0.8 else ("good" if (ka or 0) >= 0.6 else "fair")
    lv = "strong" if (fom or 0) >= 0.12 else ("moderate" if (fom or 0) >= 0.05 else "weak")
    L.append("| Metric | Value | Notes |")
    L.append("|---|---|---|")
    L.append(f"| Kappa | {ka:.4f} | overall agreement ({grade}) |")
    L.append(f"| Overall accuracy OA | {_num((oa or 0) * 100, 2)}% | high unchanged-pixel share inflates it |")
    L.append(f"| FoM | {fom:.4f} | placement ability on changed pixels ({lv}) |")
    A, B, C, D = m.get("A"), m.get("B"), m.get("C"), m.get("D")
    if None not in (A, B, C, D):
        L.append(f"| Change contingency (10% sample) | hits {A:,} / misses {B:,} / false alarms {C:,} / wrong class {D:,} | — |")
    L.append("")
    if dg.get("metrics"):
        d = dg["metrics"]
        L.append("**Error decomposition (quantity vs placement)**\n")
        L.append("| Mode | Demand source | FoM |")
        L.append("|---|---|---|")
        L.append(f"| Main mode | {proj.get('demand')} prediction | {fom:.4f} |")
        L.append(f"| Diagnostic mode | real validation-year areas | {d.get('FoM', 0):.4f} |")
        L.append("")
        L.append(f"- Quantity-error contribution **{dg.get('fom_gain', 0):+.4f} FoM**;"
                 f"placement-error loss **{dg.get('loc_loss', 0):.4f}**")
        L.append("")
    if backtest == "real" or proj.get("demand") == "real":
        L.append("> This backtest is in **real-area diagnostic mode**: demand is taken directly from the "
                 "validation year's real areas, so quantity is exactly right and FoM reflects placement "
                 "allocation ability only — an upper bound of CARS capability, and **not equivalent to "
                 "the full accuracy including quantity prediction**.\n")
    L.append("> Reading reminder: high Kappa/OA does not mean the prediction is trustworthy — changed "
             "pixels are usually under 10%, and 90% correct unchanged pixels alone push OA above 90%. "
             "For change, look at FoM.\n")
    return L


def _sec_area(order, cols, table, target, late_year, early_year):
    L = ["## 5. Area statistics & changes\n"]
    if not order:
        return L + ["- Area statistics missing (area_stats.csv was not generated).\n"]
    yrs = [(c, _year_of(c)) for c in cols]
    yrs = sorted([(c, y) for c, y in yrs if y], key=lambda t: t[1])
    L.append("Unit: km² (computed back from 30m pixels)\n")
    L.append("| Land class | " + " | ".join(str(y) for _, y in yrs) +
             " | " + f"change {late_year}→{target} | rate |")
    L.append("|---" * (len(yrs) + 3) + "|")
    tgt_col = next((c for c, y in yrs if y == target), None)
    base_col = next((c for c, y in yrs if y == late_year), None)
    for name in order:
        vals = table.get(name, {})
        cells = [_num(vals.get(c, 0)) for c, _ in yrs]
        dv = (vals.get(tgt_col, 0) - vals.get(base_col, 0)) if (tgt_col and base_col) else None
        L.append(f"| {name} | " + " | ".join(cells) +
                 f" | {_signed(dv) if dv is not None else '—'} | "
                 f"{_pct(vals.get(tgt_col, 0), vals.get(base_col, 0)) if (tgt_col and base_col) else '—'} |")
    if "_total" in table:
        tv = table["_total"]
        L.append("| **Total** | " + " | ".join(_num(tv.get(c, 0)) for c, _ in yrs) + " | — | — |")
    L.append("")

    # —— change highlights (auto-generated) ——
    L.append("**Change highlights**\n")
    if tgt_col and base_col:
        chg = []
        for name in order:
            v = table.get(name, {})
            b, t = v.get(base_col, 0), v.get(tgt_col, 0)
            chg.append((t - b, name, b, t))
        chg.sort(key=lambda x: -abs(x[0]))
        for dv, name, b, t in chg[:3]:
            if abs(dv) < 1e-6:
                continue
            ny = max(target - late_year, 1)
            L.append(f"- **{name}** {_num(b)} → {_num(t)} km² "
                     f"({ 'increase' if dv > 0 else 'decrease' } of {_num(abs(dv))} km², "
                     f"{_pct(t, b)}), {_signed(dv / ny)} km²/yr on average")
        # compare with the historical rate
        if early_year:
            ey = next((c for c, y in yrs if y == early_year), None)
            if ey:
                for nm in order:
                    v = table.get(nm, {})
                    h = (v.get(base_col, 0) - v.get(ey, 0)) / max(late_year - early_year, 1)
                    p = (v.get(tgt_col, 0) - v.get(base_col, 0)) / max(target - late_year, 1)
                    if abs(h) > 1 and abs(p) > 1 and (h * p) > 0:
                        tag = "slowing" if abs(p) < abs(h) else "accelerating"
                        L.append(f"- {nm}: change rate from historical {_signed(h)} km²/yr to "
                                 f"predicted {_signed(p)} km²/yr ({tag})")
                        break
        L.append("")
    return L


def _sec_products(out_dir, target, seq, fig_line, area_csv, report_path):
    L = ["## 6. Product list\n"]
    L.append("| Type | File |")
    L.append("|---|---|")
    if seq:
        for s in seq:
            L.append(f"| {s['year']} simulated raster | `{s['sim']}` |")
    figs = []
    for f in sorted(os.listdir(out_dir)) if os.path.isdir(out_dir) else []:
        if not f.lower().endswith((".jpg", ".png")):
            continue
        if "sequence" in f:
            tag = "multi-epoch comparison"
        elif str(target) in f:
            tag = f"**target-year ({target}) figure**"
        elif "real" in f.lower():
            tag = "real validation map (reference)"
        else:
            tag = "main simulation-year figure"
        figs.append((tag, f))
    for tag, f in figs:
        L.append(f"| {tag} | `{os.path.join(out_dir, f)}` |")
    if area_csv and os.path.exists(area_csv):
        L.append(f"| Area statistics table | `{area_csv}` |")
    L.append(f"| **This summary report** | `{report_path}` |")
    L.append("")
    if fig_line:
        L.append(f"> Figure log: {fig_line}\n")
    return L


def _sec_limits():
    L = ["## 7. Known limitations\n"]
    L.append("1. **FoM is the real indicator of placement ability; Kappa is not** — changed pixels are "
             "sparse, so OA is naturally high.")
    L.append("2. Climate factors at 2.5° coarse resolution; population defaults to 2020; OSM roads/water "
             "have omissions inside China.")
    L.append("3. Parameters are the bundled manual's defaults (neighborhood 3 / diffusion 0.1 / patch 0.2 / "
             "seed 0.1); no tuning/optimization performed.")
    L.append("4. Water lock only bans water out-conversion, not in-conversion from other classes; to freeze "
             "the water area, in-conversion must also be banned in the transition matrix, and a re-run is required.")
    L.append("5. Extremely small classes (final year <1000 pixels, ≈0.9 km²) can hardly form independent "
             "patches; their simulation results and accuracy contributions have no statistical meaning — merging recommended.")
    L.append("6. Prediction results depend on the stability of historical transition probabilities; major "
             "future policy/engineering disturbances (e.g. large-scale re-zoning, major water projects) will "
             "push the scenario off track.")
    L.append("7. **Engine non-determinism (measured)**: the PLUS engine's LEAS random forest does not fix a "
             "random seed; identical inputs re-run produce different probability bands, and CARS results "
             "fluctuate slightly. Two runs of the same region and parameters measured: major-class areas "
             "consistent (cropland differs <0.01%), but end-year minor classes (hundreds of pixels) can differ "
             "by over 25%, and pixel positions differ. Hence **major-class conclusions are stable; minor-class "
             "numbers and rasters are not bit-reproducible**. Papers should state \"statistically reproducible\", "
             "not bit-level consistency; never draw conclusions from minor classes.")
    L.append("")
    return L


def _sec_appendix(timings, moved, data_dir):
    L = ["## Appendix\n"]
    if timings:
        L.append("**A. Per-stage timings**\n")
        L.append("| Stage | Duration |")
        L.append("|---|---|")
        for t in timings:
            sec = t.get("seconds", 0) or 0
            L.append(f"| {t.get('stage', '')} | {sec / 60:.1f} min |")
        L.append("")
    else:
        L.append("**A. Per-stage timings**: this run was a report regeneration (no re-modeling); per-stage "
                 f"timing logs are under `{os.path.join(data_dir, 'logs')}`.\n")
    # sub-reports: list both the ones archived this run and the ones archived before
    # (the report can be regenerated; don't report only the ones moved this time)
    dest_root = os.path.join(data_dir, "logs", SUBDIR)
    listed = []
    seen = set()
    for label, _src, dst in moved:
        listed.append((label, dst))
        seen.add(os.path.basename(dst))
    if os.path.isdir(dest_root):
        for f in sorted(os.listdir(dest_root)):
            if f.endswith(".md") and f not in seen:
                listed.append((f[:-3], os.path.join(dest_root, f)))
    if listed:
        L.append("**B. Sub-reports** (archived; the main text excerpts only key points)\n")
        for label, dst in listed:
            L.append(f"- {label}: `{dst}`")
        L.append("")
    return L


# ---------------- 主入口 ----------------
def build_report(data_dir, out_name, proj, predict, region,
                 timings=None, fig_line="", area_csv=None,
                 backtest="none", mapping=None, water="open", archive=True):
    out_dir = os.path.join(data_dir, out_name) if out_name else data_dir
    rj = _load_json(os.path.join(out_dir, "report.json"))
    seq = (rj or {}).get("sequence") or []
    target = seq[-1]["year"] if seq else predict
    late_year = proj.get("late_year")
    early_year = proj.get("early_year")
    factors = 0
    ddir = os.path.join(data_dir, "drivers")
    if os.path.isdir(ddir):
        factors = len([x for x in os.listdir(ddir)
                       if x.startswith("df_") and x.endswith(".tif")])

    # area table: prefer the existing CSV (contains all historical epochs); skip this section if missing
    order, cols, table = None, None, None
    _at = read_area_table(area_csv or os.path.join(out_dir, "area_stats.csv"))
    if _at:
        order, cols, table = _at

    moved = archive_sub_reports(data_dir, out_dir) if archive else []
    # A prediction report cites a backtest result → the report inside the backtest directory has been
    # merged into this report's section 4, so archive it too — guaranteeing only one summary_report.md
    # is visible per region directory
    bt = _find_backtest(data_dir, out_name)
    if archive and bt and not (rj or {}).get("metrics"):
        dest_root = os.path.join(data_dir, "logs", SUBDIR)
        for fn, newname, label in (
                ("summary_report.md", f"{bt[0]}_merged_into_main.md", "backtest summary"),
                ("pipeline_report.md", f"{bt[0]}_pipeline.md", "backtest modeling")):
            src = os.path.join(data_dir, bt[0], fn)
            if not os.path.exists(src):
                continue
            try:
                os.makedirs(dest_root, exist_ok=True)
                dst = os.path.join(dest_root, newname)
                shutil.move(src, dst)
                moved.append((label, src, dst))
            except Exception as e:
                print(f"  ⚠️ archive failed {src}: {e}")

    report_path = os.path.join(out_dir, REPORT_NAME)
    class_names = proj.get("class_names") or {}

    L = []
    L.append(f"# {region} {target} Land-Use Simulation · Summary Report\n")
    _ds = _data_source(proj, data_dir)
    _head_src = {"clcd": "CLCD 30m ", "worldcover": "ESA WorldCover 10m ",
                 "esri": "Esri Sentinel-2 10m ",
                 "cnlucc": "CNLUCC 30m ", "stanford": "Stanford derived ",
                 "globeland30": "GlobeLand30 30m ", "glc_fcs30": "GLC_FCS30 30m ",
                 "modis_igbp": "MODIS MCD12Q1 500m ", "esa_cci": "ESA CCI 300m ",
                 "from_glc": "FROM-GLC ", "globcover": "GlobCover 300m ",
                 "modis_umd": "MODIS MCD12Q1 UMD 500m ",
                 "user": "user-supplied "}
    head = (f"Using {_head_src.get(_ds, _head_src['user'])}{early_year}–{late_year} multi-epoch "
            f"land-use data as the training period, the PLUS model (expansion analysis + LEAS random "
            f"forest + "
            f"{'Markov chain' if proj.get('demand') == 'markov' else 'linear regression'} demand + "
            f"CARS patch simulation)")
    if seq:
        head += f" projects the {target} land-use pattern in a chained manner (intermediate epochs {' / '.join(str(s['year']) for s in seq[:-1])})"
    else:
        head += f" projects the {target} land-use pattern"
    L.append(head + ".\n")
    m = (rj or {}).get("metrics")
    if m:
        L.append(f"> Accuracy: {'Kappa %.4f' % m['Kappa'] if m.get('Kappa') is not None else ''}"
                 f"{' / OA %.2f%%' % (m['OA'] * 100) if m.get('OA') is not None else ''}"
                 f"{' / FoM %.4f' % m['FoM'] if m.get('FoM') is not None else ''}"
                 f" ({'real-area diagnostic mode' if backtest == 'real' else 'backtest mode'})")
    else:
        if bt:
            bm = bt[1]["metrics"]
            # backtest year taken dynamically (fixed 2026-11-13: previously hard-coded "2020 backtest",
            # wrong when the Esri source's backtest year is 2025)
            _m = re.search(r"bt(\d+)", bt[0] or "")
            _bt_year = bt[1].get("predict_year") or (int(_m.group(1)) if _m else None)
            _bt_txt = f"{_bt_year} " if _bt_year else ""
            L.append(f"> Accuracy: pure prediction has no real map to compare; reliability reference from "
                     f"the same-parameter {_bt_txt}backtest "
                     f"Kappa {bm.get('Kappa', 0):.4f} / OA {(bm.get('OA') or 0) * 100:.2f}% / "
                     f"FoM {bm.get('FoM', 0):.4f} (real-area diagnostic mode; placement ability only)")
        else:
            L.append("> Accuracy: pure prediction, no real map to compare; for reliability metrics, "
                     "run an additional `--backtest real`")
    L.append("")

    L += _sec_meta(proj, predict, target, seq, region, backtest, water, mapping, factors)
    L += _sec_data(data_dir, proj, factors)
    L += _sec_reclass(data_dir, proj)
    L += _sec_matrix(proj)
    L += _sec_accuracy(rj, backtest, proj, bt)
    L += _sec_area(order, cols, table, target, late_year, early_year)
    L += _sec_products(out_dir, target, seq, fig_line, area_csv, report_path)
    L += _sec_limits()
    L += _sec_appendix(timings, moved, data_dir)

    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(L).replace("\n\n\n", "\n\n"))
    print(f"  ✅ single summary report: {report_path}")
    if moved:
        print(f"  📦 {len(moved)} sub-report(s) archived → {os.path.join(data_dir, 'logs', SUBDIR)}")
    return report_path


def _auto_project(data_dir):
    """没给 --project 时,挑 data_dir 下最新的 project_full_*.json"""
    cands = [os.path.join(data_dir, f) for f in os.listdir(data_dir)
             if f.startswith("project_full_") and f.endswith(".json")]
    if not cands:
        return None
    return max(cands, key=os.path.getmtime)


def main():
    import argparse
    p = argparse.ArgumentParser(description="Generate the single summary report (runs standalone, no re-modeling)")
    p.add_argument("--data-dir", required=True, help="study-region data directory")
    p.add_argument("--project", default=None, help="project config json; if omitted, auto-pick the newest project_full_*.json")
    p.add_argument("--region", default=None, help="region name; default = directory name")
    p.add_argument("--timing", default=None, help="per-stage timing json (optional)")
    p.add_argument("--no-archive", action="store_true", help="do not archive sub-reports")
    a = p.parse_args()

    data_dir = os.path.abspath(a.data_dir)
    proj_path = a.project or _auto_project(data_dir)
    if not proj_path or not os.path.exists(proj_path):
        print(f"❌ project config not found: {proj_path}")
        sys.exit(1)
    proj = _load_json(proj_path) or {}
    proj.setdefault("data_dir", data_dir)
    out_name = os.path.basename(proj.get("output_dir") or f"model_{proj.get('predict_year')}")
    region = a.region or proj.get("region")
    if not region:
        # fallback order: region name in _说明 ("郑州市 全流程预测…") → directory name.
        # Zhengzhou 2026-11-13 test: report regeneration dropped the city name (only the dir name 410100 remained)
        _m = re.match(r"^(\S+?)\s+(?:full pipeline|全流程)", proj.get("_说明") or "")
        region = _m.group(1) if _m else os.path.basename(data_dir)
    timings = _load_json(a.timing) if a.timing else _load_json(
        os.path.join(data_dir, out_name, "timing.json"))
    predict = int(proj.get("predict_year") or 0)

    build_report(data_dir, out_name, proj, predict, region,
                 timings=timings, area_csv=os.path.join(data_dir, out_name, "area_stats.csv"),
                 backtest=proj.get("backtest", "none"),
                 mapping=proj.get("mapping"), water="lock" if proj.get("locked_classes") else "open",
                 archive=not a.no_archive)


if __name__ == "__main__":
    main()
