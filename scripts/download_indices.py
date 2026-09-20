import pandas as pd
import yfinance as yf
from pathlib import Path

# -------- Base paths (portable) --------
BASE_DIR = Path(__file__).resolve().parents[1]   # .../Sectoral_Scanner
CONFIG_DIR = BASE_DIR / "config"
DATA_DIR = BASE_DIR / "data"

INDEX_FILE = CONFIG_DIR / "indices.txt"

# 1) Read indices.txt
if not INDEX_FILE.exists():
    print(f"❌ Index file not found: {INDEX_FILE}")
    raise SystemExit

indices = []
with INDEX_FILE.open("r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        # Expect NAME,TICKER
        parts = line.split(",")
        if len(parts) != 2:
            print(f"⚠ Skipping malformed line in indices.txt: {line}")
            continue
        name, ticker = parts[0].strip(), parts[1].strip()
        indices.append((name, ticker))

if not indices:
    print("❌ No valid indices found in indices.txt")
    raise SystemExit

print("✅ Indices to download:", indices)

DATA_DIR.mkdir(parents=True, exist_ok=True)

# 2) Download and save each index
for name, ticker in indices:
    print(f"\nDownloading daily data for index {name} ({ticker})...")

    try:
        data = yf.download(
            ticker,
            period="5y",
            interval="1d",
            auto_adjust=False,
            progress=False,
        )

        if data.empty:
            print(f"  ⚠ No data for {name} / {ticker}, skipping.")
            continue

        data = data.reset_index()

        # Save as index_<NAME>.csv (e.g., index_NIFTY50.csv)
        safe_name = name.replace(" ", "_")
        out_path = DATA_DIR / f"index_{safe_name}.csv"
        data.to_csv(out_path, index=False)

        print(f"  ✅ Saved {len(data)} rows to {out_path}")

    except Exception as e:
        print(f"  ❌ Error downloading {name} / {ticker}: {e}")
