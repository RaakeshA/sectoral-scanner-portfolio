import pandas as pd
from pathlib import Path

# -------- Base paths (portable) --------
BASE_DIR = Path(__file__).resolve().parents[1]   # .../Sectoral_Scanner
DATA_DIR = BASE_DIR / "data"

sector_strength_path = DATA_DIR / "sector_strength.csv"

# 1) Load sector_strength.csv
if not sector_strength_path.exists():
    print(f"❌ sector_strength.csv not found at: {sector_strength_path}")
    raise SystemExit

df = pd.read_csv(sector_strength_path)

required = {"sector", "ret_1m_pct", "ret_3m_pct"}
if not required.issubset(df.columns):
    print(f"❌ sector_strength.csv is missing required columns: {required}")
    print("Columns present:", df.columns.tolist())
    raise SystemExit

print(f"✅ Loaded sector_strength.csv with {len(df)} rows")

# 2) Compute percentile sector ranks (0–100)
df["score_1m_sector"] = (df["ret_1m_pct"].rank(pct=True) * 100).round(2)
df["score_3m_sector"] = (df["ret_3m_pct"].rank(pct=True) * 100).round(2)

# Sort strongest sectors at the top
df = df.sort_values("score_3m_sector", ascending=False)

# 3) Save output
out_path = DATA_DIR / "sector_strength_scored.csv"
df.to_csv(out_path, index=False)

print(f"✅ Saved sector_strength_scored.csv to: {out_path}")
print(df.head())
