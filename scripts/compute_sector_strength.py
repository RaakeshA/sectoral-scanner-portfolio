import pandas as pd
from pathlib import Path

# -------- Base paths (portable) --------
BASE_DIR = Path(__file__).resolve().parents[1]   # .../Sectoral_Scanner
DATA_DIR = BASE_DIR / "data"
CONFIG_DIR = BASE_DIR / "config"

stock_strength_path = DATA_DIR / "stock_strength.csv"
sector_map_path = CONFIG_DIR / "stock_sector_map.csv"

# 1) Basic file checks
if not stock_strength_path.exists():
    print(f"❌ stock_strength.csv not found at {stock_strength_path}")
    raise SystemExit

if not sector_map_path.exists():
    print(f"❌ stock_sector_map.csv not found at {sector_map_path}")
    raise SystemExit

# 2) Load stock strength (per-stock 1M & 3M returns)
df_stock = pd.read_csv(stock_strength_path)

if "ticker" not in df_stock.columns:
    print("❌ 'ticker' column missing in stock_strength.csv")
    print("Columns present:", df_stock.columns.tolist())
    raise SystemExit

required_strength_cols = {"ret_1m_pct", "ret_3m_pct"}
if not required_strength_cols.issubset(df_stock.columns):
    print("❌ stock_strength.csv missing return columns:", required_strength_cols)
    print("Columns present:", df_stock.columns.tolist())
    raise SystemExit

# 3) Load ticker → sector map
df_map = pd.read_csv(sector_map_path)

if not {"ticker", "sector"}.issubset(df_map.columns):
    print("❌ stock_sector_map.csv must have 'ticker' and 'sector' columns")
    print("Columns present:", df_map.columns.tolist())
    raise SystemExit

# 4) Merge strength with sector info
df = df_stock.merge(df_map[["ticker", "sector"]], on="ticker", how="left")

if "sector" not in df.columns:
    print("❌ 'sector' column missing after merge.")
    raise SystemExit

# Optional: if sector has NaN, you can tag them as 'UNKNOWN'
df["sector"] = df["sector"].fillna("UNKNOWN")

# 5) Group by sector: average 1M & 3M returns
grouped = df.groupby("sector", as_index=False).agg(
    {
        "ret_1m_pct": "mean",
        "ret_3m_pct": "mean",
    }
)

# Sort by 3M return desc for convenience
grouped = grouped.sort_values("ret_3m_pct", ascending=False)

# 6) Save output
out_path = DATA_DIR / "sector_strength.csv"
grouped.to_csv(out_path, index=False)

print(f"✅ Saved sector_strength.csv to {out_path}")
print(grouped.head())
