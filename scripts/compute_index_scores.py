import pandas as pd
from pathlib import Path

# -------- Base paths (portable) --------
BASE_DIR = Path(__file__).resolve().parents[1]   # .../Sectoral_Scanner
DATA_DIR = BASE_DIR / "data"

in_path = DATA_DIR / "index_strength.csv"

# 1) Load index_strength.csv
if not in_path.exists():
    print(f"❌ index_strength.csv not found at: {in_path}")
    raise SystemExit

df = pd.read_csv(in_path)

required = {"index_name", "ret_1m_pct", "ret_3m_pct"}
if not required.issubset(df.columns):
    print("❌ index_strength.csv is missing required columns:", required)
    print("Columns present:", df.columns.tolist())
    raise SystemExit

print(f"✅ Loaded index_strength.csv with {len(df)} rows")

# 2) Compute percentile scores (0–100)
df["score_1m"] = (df["ret_1m_pct"].rank(pct=True) * 100).round(2)
df["score_3m"] = (df["ret_3m_pct"].rank(pct=True) * 100).round(2)

# Sort strongest indices at top
df = df.sort_values("score_3m", ascending=False)

# 3) Save output
out_path = DATA_DIR / "index_strength_scored.csv"
df.to_csv(out_path, index=False)

print(f"✅ Saved index strength scored to {out_path}")
print(df.head())
