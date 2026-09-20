import pandas as pd
from pathlib import Path

# -------- Base paths (portable, cross-platform) --------
BASE_DIR = Path(__file__).resolve().parents[1]   # .../Sectoral_Scanner
DATA_DIR = BASE_DIR / "data"

in_path = DATA_DIR / "stock_strength.csv"

# 1) Load stock_strength.csv
if not in_path.exists():
    print(f"❌ Input file not found: {in_path}")
    raise SystemExit

df = pd.read_csv(in_path)

required_cols = {"ticker", "ret_1m_pct", "ret_3m_pct"}
if not required_cols.issubset(df.columns):
    print("❌ stock_strength.csv missing required columns:", required_cols)
    print("Columns present:", df.columns.tolist())
    raise SystemExit

print(f"✅ Loaded stock_strength.csv with {len(df)} rows")

# 2) Compute percentile ranks (0–100)
df["score_1m"] = (df["ret_1m_pct"].rank(pct=True) * 100).round(2)
df["score_3m"] = (df["ret_3m_pct"].rank(pct=True) * 100).round(2)

# Sort by stronger 3M performance
df = df.sort_values("score_3m", ascending=False)

# 3) Save output
out_path = DATA_DIR / "stock_strength_scored.csv"
df.to_csv(out_path, index=False)

print(f"✅ Saved scored stock strength to {out_path}")
print(df.head())
