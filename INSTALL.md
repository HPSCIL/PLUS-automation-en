# plus-automation-en Installation (three steps on a new machine)

## Step 1: Python environment

- Requirements: Windows + Python 3.11 (or 3.10/3.12/3.13)
- Create a virtual environment and install dependencies:

```
python -m venv plus-venv
plus-venv\Scripts\activate
pip install -r requirements.txt
```

- Always run with `plus-venv\Scripts\python.exe` instead of the system python
- In China, switch the pip mirror first (`pip install -i https://mirrors.aliyun.com/pypi/simple/ -r requirements.txt`)

## Step 2: PLUS engine (bundled, author-authorized)

- The engine `runtime\plus-backend` (PLUS.exe + 8 .bat files) **is distributed together with the skill** —
  PLUS model author (Prof. Xun Liang, HPSCIL Lab) authorized this skill to bundle and distribute it; no separate acquisition needed
- Engine resolution prefers the bundled runtime automatically, **zero configuration required**; to switch engine versions, overwrite `runtime\` with a new `plus-backend`

## Step 3: Configuration

- Engine resolution order: env var `PLUS_BACKEND` > `scripts\config.json`'s `plus_backend` > the skill's bundled `runtime\plus-backend` > built-in default path. The package needs no configuration changes
- CLCD auto-download needs an NCDC account: put the credentials file at `C:\Users\<username>\.plus-full\ftp_config.json`
  (format: `{"host":"ftp.ncdc.ac.cn","port":2121,"username":"...","password":"...","file_template":"CLCD_v01_{year}_albert.tif"}`);
  skip this if you don't use auto-download (you provide the land-use maps yourself)
- Default output data root = `plus_skill_GIS_data` under the user's home directory; use `--output` / `--data-dir` to point elsewhere

## Verify the installation

```
python scripts\run_full.py --region 鄂州市 --years 2010,2015,2020 --predict 2020
```

A completed backtest with Kappa/FoM output means the installation works.

## Known limitations

- Windows only (the engine is a Windows executable; concurrency isolation / non-Windows support not implemented)
- Ships with no data; the engine is bundled (see DATA_SOURCES.md, item 9)
