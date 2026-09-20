import pandas as pd
from pathlib import Path

# -------- Base paths (portable) --------
BASE_DIR = Path(__file__).resolve().parents[1]     # .../Sectoral_Scanner
DATA_DIR = BASE_DIR / "data"
CONFIG_DIR = BASE_DIR / "config"

# Input file paths
stock_scored_path  = DATA_DIR / "stock_strength_scored.csv"
sector_scored_path = DATA_DIR / "sector_strength_scored.csv"
sector_map_path    = CONFIG_DIR / "stock_sector_map.csv"
rs_scored_path     = DATA_DIR / "stock_rs_scored.csv"

# ===== 1) Load all required files =====
if not stock_scored_path.exists():
    print(f"❌ Missing file: {stock_scored_path}")
    raise SystemExit

if not sector_scored_path.exists():
    print(f"❌ Missing file: {sector_scored_path}")
    raise SystemExit

if not sector_map_path.exists():
    print(f"❌ Missing file: {sector_map_path}")
    raise SystemExit

if not rs_scored_path.exists():
    print(f"❌ Missing file: {rs_scored_path}")
    raise SystemExit

df_stock  = pd.read_csv(stock_scored_path)
df_sector = pd.read_csv(sector_scored_path)
df_map    = pd.read_csv(sector_map_path)
df_rs     = pd.read_csv(rs_scored_path)

print(f"Loaded stock_strength_scored:  {len(df_stock)} rows")
print(f"Loaded sector_strength_scored: {len(df_sector)} rows")
print(f"Loaded stock_sector_map:       {len(df_map)} rows")
print(f"Loaded stock_rs_scored:         {len(df_rs)} rows")

# ===== 2) Validate required columns =====
required_stock = {"ticker", "last_close", "ret_1m_pct", "ret_3m_pct", "score_1m", "score_3m"}
required_map   = {"ticker", "sector"}
required_sector = {"sector", "score_1m_sector", "score_3m_sector"}
required_rs    = {"ticker", "RS_1m_score", "RS_3m_score"}

if not required_stock.issubset(df_stock.columns):
    print("❌ Missing in stock_strength_scored:", required_stock)
    raise SystemExit

if not required_map.issubset(df_map.columns):
    print("❌ stock_sector_map.csv must contain:", required_map)
    raise SystemExit

if not required_sector.issubset(df_sector.columns):
    print("❌ Missing in sector_strength_scored:", required_sector)
    raise SystemExit

if not required_rs.issubset(df_rs.columns):
    print("❌ Missing in stock_rs_scored:", required_rs)
    raise SystemExit

# ===== 3) Rename stock columns for clarity =====
df_stock = df_stock.rename(columns={
    "score_1m": "score_1m_stock",
    "score_3m": "score_3m_stock",
})

# ===== 4) Merge stock with sector map =====
df = df_stock.merge(df_map, on="ticker", how="left")

# ===== 5) Merge sector scores =====
df = df.merge(
    df_sector[["sector", "score_1m_sector", "score_3m_sector"]],
    on="sector",
    how="left"
)

# ===== 6) Merge RS scores =====
df = df.merge(
    df_rs[["ticker", "RS_1m_score", "RS_3m_score"]],
    on="ticker",
    how="left"
)

# Fill missing RS with 0
df["RS_1m_score"] = df["RS_1m_score"].fillna(0.0)
df["RS_3m_score"] = df["RS_3m_score"].fillna(0.0)

# ===== 7) Compute final composite scores =====
# Weighted:
#   40% stock strength
#   40% sector strength
#   20% RS vs NIFTY

df["final_score_1m"] = (
    0.40 * df["score_1m_stock"] +
    0.40 * df["score_1m_sector"] +
    0.20 * df["RS_1m_score"]
)

df["final_score_3m"] = (
    0.40 * df["score_3m_stock"] +
    0.40 * df["score_3m_sector"] +
    0.20 * df["RS_3m_score"]
)

df["final_score_1m"] = df["final_score_1m"].round(2)
df["final_score_3m"] = df["final_score_3m"].round(2)

# ===== 8) Final columns =====
cols = [
    "ticker", "sector", "last_close",
    "ret_1m_pct", "ret_3m_pct",
    "score_1m_stock", "score_3m_stock",
    "score_1m_sector", "score_3m_sector",
    "RS_1m_score", "RS_3m_score",
    "final_score_1m", "final_score_3m",
]

df_final = df[cols]

# ===== 9) Save result =====
out_path = DATA_DIR / "merged_scores.csv"
df_final.to_csv(out_path, index=False)

print(f"\n✅ Saved merged_scores.csv to: {out_path}")
print(df_final.head())
