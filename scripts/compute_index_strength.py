import pandas as pd
from pathlib import Path

# -------- Base paths (portable) --------
BASE_DIR = Path(__file__).resolve().parents[1]   # .../Sectoral_Scanner
DATA_DIR = BASE_DIR / "data"
CONFIG_DIR = BASE_DIR / "config"
INDEX_FILE = CONFIG_DIR / "indices.txt"

DAYS_1M = 21
DAYS_3M = 63

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
        parts = line.split(",")
        if len(parts) != 2:
            print(f"⚠ Skipping malformed line: {line}")
            continue
        name, ticker = parts[0].strip(), parts[1].strip()
        # Currently we only use name; ticker is for reference / future use
        indices.append(name)

if not indices:
    print("❌ No indices found in indices.txt")
    raise SystemExit

print("✅ Indices loaded:", indices)

rows = []

# 2) Process each index
for name in indices:
    safe_name = name.replace(" ", "_")
    csv_path = DATA_DIR / f"index_{safe_name}.csv"

    if not csv_path.exists():
        print(f"⚠ Missing data file for index {name}: {csv_path}")
        continue

    try:
        df = pd.read_csv(csv_path)
    except Exception as e:
        print(f"❌ Error reading {csv_path}: {e}")
        continue

    if "Date" not in df.columns:
        print(f"⚠ No 'Date' column in {csv_path}, skipping {name}.")
        continue

    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df = df.dropna(subset=["Date"]).sort_values("Date").reset_index(drop=True)

    # Restrict to data from 2021 onwards
    df = df[df["Date"] >= "2021-01-01"]

    if "Close" not in df.columns:
        print(f"⚠ No 'Close' column in {csv_path}, skipping {name}.")
        continue

    # Clean and convert Close to numeric
    df["Close"] = (
        df["Close"]
        .astype(str)
        .str.replace(",", "", regex=False)
    )
    df["Close"] = pd.to_numeric(df["Close"], errors="coerce")
    df = df.dropna(subset=["Close"])

    if len(df) < DAYS_3M + 1:
        print(f"⚠ Not enough data for 3M return for {name}")
        continue

    last_close = float(df.iloc[-1]["Close"])
    last_date = df.iloc[-1]["Date"]

    price_1m = float(df.iloc[max(0, len(df) - 1 - DAYS_1M)]["Close"])
    price_3m = float(df.iloc[max(0, len(df) - 1 - DAYS_3M)]["Close"])

    ret_1m = (last_close - price_1m) / price_1m * 100.0
    ret_3m = (last_close - price_3m) / price_3m * 100.0

    rows.append(
        {
            "index_name": name,
            "last_date": last_date,
            "last_close": last_close,
            "ret_1m_pct": ret_1m,
            "ret_3m_pct": ret_3m,
        }
    )

if not rows:
    print("❌ No valid index rows to save.")
    raise SystemExit

summary_df = pd.DataFrame(rows)
summary_df = summary_df.sort_values("ret_3m_pct", ascending=False)

out_path = DATA_DIR / "index_strength.csv"
summary_df.to_csv(out_path, index=False)

print(f"\n✅ Saved index strength summary to: {out_path}")
print(summary_df.head())
