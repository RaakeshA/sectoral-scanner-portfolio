import pandas as pd
from pathlib import Path

# -------- Base paths (portable) --------
BASE_DIR = Path(__file__).resolve().parents[1]   # .../Sectoral_Scanner
DATA_DIR = BASE_DIR / "data"

rs_path = DATA_DIR / "stock_rs.csv"

# 1) Load stock_rs.csv (output of compute_rs_vs_nifty.py)
if not rs_path.exists():
    print(f"❌ stock_rs.csv not found at: {rs_path}")
    print("Run compute_rs_vs_nifty.py first.")
    raise SystemExit

df = pd.read_csv(rs_path)

required = {"ticker", "RS_1m_pct", "RS_3m_pct"}
if not required.issubset(df.columns):
    print("❌ stock_rs.csv is missing required RS columns.")
    print("Required:", required)
    print("Present:", df.columns.tolist())
    raise SystemExit

print(f"✅ Loaded stock_rs.csv with {len(df)} rows")

# 2) Compute RS scores (0–100 percentile ranks)
# Higher RS_1m_pct / RS_3m_pct → higher score (stronger vs NIFTY)

df["RS_1m_score"] = (df["RS_1m_pct"].rank(pct=True) * 100).round(2)
df["RS_3m_score"] = (df["RS_3m_pct"].rank(pct=True) * 100).round(2)

# 3) Save result
out_path = DATA_DIR / "stock_rs_scored.csv"
df.to_csv(out_path, index=False)

print(f"✅ Saved RS scores to: {out_path}")
print("Sample:")
print(df[["ticker", "RS_1m_pct", "RS_3m_pct", "RS_1m_score", "RS_3m_score"]].head())
