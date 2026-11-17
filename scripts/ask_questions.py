#!/usr/bin/env python
"""引导问答标准器(2026-11-13 试验版,新文件,不替代现有流程)

解决"执行 AI 自由发挥弹窗"问题:所有问题的选项文字、标注、分支联动
全部在本文件写死。AI 的职责 = 搬运,不是发挥。

三种模式:
  1. --dump
     输出标准问题清单 JSON(问题文字、选项逐字、分支规则)。
     AI 读它 → 用 AskUserQuestion 逐字弹窗 → 收集用户答案。
  2. --finalize '<答案 JSON 字符串>' 或 --finalize-file 文件
     校验答案(分支联动/年份范围/选项合法性)→ 通过则写 answers.json。
     不合法 → 打印具体错误,exit 1,AI 必须回头改答案重新问。
  3. --dry-run answers.json
     仅展示 answers.json 将翻译成的 run_full 参数(不执行)。

答案 JSON 示例:
{
  "lulc_source": "esri",            # esri | clcd | worldcover | stanford | user
  "lulc_res": 30,                   # 30 | 10
  "years": [2017, 2025],
  "demand": "markov",               # markov | linear
  "do_backtest": true,
  "backtest": "train",              # train(真实面积推荐) | predict(预测面积,需三期)
  "predict": 2035,
  "sequence": 5,                    # 0 = 不要连续预测;>0 = 间隔年数
  "water_lock": "",                 # 开放题:AI 检索后填,如 "lock:该地有黄河干流..."
  "matrix_choice": "regional",      # regional(区域化修改,推荐) | default | custom
  "matrix_restrictions": [],        # regional 时 AI 检索后填 [{"from","to","allow","依据"}]
  "output_dir": ""                  # 空 = 默认(用户主目录)
}
"""
import json
import sys
import os

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ESRI_YEARS = (2017, 2025)
CLCD_YEARS = (1990, 2022)
WC_YEARS = (2020, 2021)


def questions():
    """标准问题清单(选项文字逐字写死,AI 弹窗必须照抄)"""
    return {
        "_flow": (
            "Dialog flow (must be followed strictly): Q1 and Q1b are **two independent questions, "
            "both asked unconditionally**; Q1b's first option 'None' lets users who already picked "
            "one of the first 3 in Q1 skip it — there is no conditional branch, hence no possibility "
            "of skipping a question (user decision 2026-11-13). "
            "If Q4 = 'Yes' → immediately ask Q5. Q7 is an open question: the AI researches first, then fills in the basis."
        ),
        "Q1_data_source": {
            "question": ("Which land-use data source? (Esri = no registration, years 2017-2025, "
                         "at 30m it is auto-aggregated from 10m, at 10m it is native; CLCD = register yourself "
                         "and provide the account, 1990-2022; among other sources: WorldCover = no registration, "
                         "only 2020-2021; Stanford = proxy required; own data = user-provided)"),
            "options": [
                "Esri 30m (no registration, recommended)",
                "Esri 10m (no registration)",
                "CLCD 30m (registration required)",
                "Other sources",
            ],
        },
        "Q1b_data_source_more": {
            "question": ("Additional data source (second question; users who picked one of the first 3 "
                         "in the first question just choose option 1 'None')"),
            "options": [
                "None — use the source from the first question",
                "WorldCover 30m/10m 2020-2021 (no registration; only 2020/2021)",
                "Stanford derived data (proxy required; after downloading via proxy, provide via --manual)",
                "My own multi-year tifs (choosing this immediately pops an input box for the folder path)",
            ],
        },
        "Q2_years": {
            "question": "Which historical years for modeling? (longer span = more change samples)",
            "branch_esri": [
                "2017, 2025 two epochs (recommended, longest span = most change samples)",
                "2017, 2021, 2025 three epochs",
                "Other years (input box, comma-separated)",
            ],
            "branch_clcd": [
                "2000, 2020 two epochs (recommended, longest span = most change samples)",
                "2000, 2010, 2020 three epochs",
                "Other years (input box, comma-separated)",
            ],
            "branch_worldcover": [
                "2020, 2021 two epochs (recommended, this source has only these two)",
                "Other years (input box, comma-separated)",
            ],
        },
        "Q3_demand": {
            "question": "How should future per-class areas be projected?",
            "options": [
                "Markov chain (recommended; standard method for two historical epochs)",
                "Linear regression (more suitable with three historical epochs)",
            ],
        },
        "Q4_backtest_need": {
            "question": "Do you want a backtest accuracy check first?",
            "options": [
                "Yes, produce Kappa/FoM (recommended; the backtest validates against a historical year)",
                "No, pure prediction (target year is after the latest year; no real map to compare)",
            ],
        },
        "Q5_backtest_mode": {
            "question": "Which backtest mode? (validation year = latest year; fill [first]/[latest] per the chosen epochs)",
            "options": [
                "Simulate from the [first]-year map to [latest] using the [latest] year's real areas (recommended)",
                "Simulate from the [first]-year map to [latest] using predicted areas (needs three historical epochs)",
            ],
        },
        "Q6_sequence": {
            "question": "Do you need intermediate transition-year maps?",
            "options_template": (
                "No, only the {target} map (recommended) / "
                "Yes (every candidate must be written as 'every N years, X epochs in total: full year list'; "
                "never write only 'every N years')"
            ),
        },
        "Q8_matrix": {
            "question": ("Which transition matrix? (whether water is locked is part of the matrix rules and is "
                         "decided here: if the AI's research finds the region's water matters → the matrix rules "
                         "automatically add 'water → others forbidden' with the basis attached; "
                         "water-scarce cities / water-source protection areas must use a two-way lock "
                         "[no out-conversion + no in-conversion] to prevent historical probabilities from "
                         "pouring into and inflating water — Zhengzhou 2026-11-13 measured +32% with out-only lock; "
                         "if water is not important → do not lock, and explain why)"),
            "options": [
                "Regional customization (AI decides automatically) (recommended; the AI gathers literature/policy/field "
                "info on the region and sets the rules automatically)",
                "Default template (forest/built-up irreversible, all others open)",
                "I define the rules myself (user gives specific rules)",
            ],
        },
        "Q9_output": {
            "question": "Where to store outputs? (must show the full path, never just 'default directory')",
            "options_template": (
                "Default directory (recommended): C:\\Users\\<username>\\plus_skill_GIS_data\\<region name> / "
                "I specify (an input box for the path follows immediately)"
            ),
        },
    }


def validate(answers):
    """校验答案,返回 (ok, 错误列表)"""
    errs = []
    src = answers.get("lulc_source")
    years = answers.get("years") or []
    if src not in ("esri", "clcd", "worldcover", "stanford", "user"):
        errs.append(f"invalid lulc_source: {src}")
        return False, errs
    if src == "esri" and any(not (ESRI_YEARS[0] <= y <= ESRI_YEARS[1]) for y in years):
        errs.append(f"Esri years must be {ESRI_YEARS[0]}-{ESRI_YEARS[1]}, got {years}")
    if src == "clcd" and any(not (CLCD_YEARS[0] <= y <= CLCD_YEARS[1]) for y in years):
        errs.append(f"CLCD years must be {CLCD_YEARS[0]}-{CLCD_YEARS[1]}, got {years}")
    if src == "worldcover" and any(y not in WC_YEARS for y in years):
        errs.append(f"WorldCover only has {list(WC_YEARS)}, got {years}")
    if len(years) < 2:
        errs.append("at least 2 historical epochs are required")
    res = answers.get("lulc_res")
    if src in ("esri", "worldcover") and res not in (10, 30):
        errs.append(f"lulc_res for {src} must be 10 or 30, got {res}")
    if src == "clcd" and res != 30:
        errs.append("CLCD only has 30m")
    if answers.get("demand") not in ("markov", "linear"):
        errs.append("area method only allows markov / linear (auto has been removed)")
    bt = answers.get("backtest")
    if answers.get("do_backtest") and bt not in ("train", "predict"):
        errs.append("backtest mode only allows train (real areas, recommended) / predict (predicted areas)")
    if bt == "predict" and len(years) < 3:
        errs.append("the predicted-area mode needs 3 historical epochs; currently fewer than 3")
    seq = answers.get("sequence") or 0
    if seq and (not isinstance(seq, int) or seq <= 0):
        errs.append("sequence must be a positive integer interval in years")
    if answers.get("matrix_choice") == "regional" and not answers.get("matrix_restrictions"):
        errs.append("regional customization chosen: matrix_restrictions must not be empty (the AI fills it after research)")
    return (not errs), errs


def main():
    if "--dump" in sys.argv:
        print(json.dumps(questions(), ensure_ascii=False, indent=2))
        return
    if "--finalize" in sys.argv:
        raw = sys.argv[sys.argv.index("--finalize") + 1]
        answers = json.loads(raw)
        ok, errs = validate(answers)
        if not ok:
            print("❌ Answer validation failed:")
            for e in errs:
                print(f"   - {e}")
            sys.exit(1)
        with open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               "..", "answers.json"), "w", encoding="utf-8") as f:
            json.dump(answers, f, ensure_ascii=False, indent=2)
        print("✅ Answers validated, answers.json written")
        return
    print(__doc__)


if __name__ == "__main__":
    main()
