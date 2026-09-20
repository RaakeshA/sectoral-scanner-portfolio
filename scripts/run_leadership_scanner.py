import pandas as pd
from pathlib import Path

# -------- Base paths (portable) --------
BASE_DIR = Path(__file__).resolve().parents[1]   # .../Sectoral_Scanner
DATA_DIR = BASE_DIR / "data"

merged_path = DATA_DIR / "merged_scores.csv"

# ===== 1) Load merged_scores.csv =====
if not merged_path.exists():
    print(f"❌ merged_scores.csv not found at {merged_path}")
    print("Run merge_scores.py first.")
    raise SystemExit

df = pd.read_csv(merged_path)
print(f"✅ Loaded merged_scores.csv with {len(df)} rows")

required_cols = {
    "ticker",
    "sector",
    "last_close",
    "ret_1m_pct",
    "ret_3m_pct",
    "score_1m_stock",
    "score_3m_stock",
    "score_1m_sector",
    "score_3m_sector",
    "RS_1m_score",
    "RS_3m_score",
    "final_score_1m",
    "final_score_3m",
}
if not required_cols.issubset(df.columns):
    print("❌ merged_scores.csv is missing some required columns.")
    print("Required:", required_cols)
    print("Present:", df.columns.tolist())
    raise SystemExit

# ===== 2) Basic sanity filters =====
# Only positive returns, non-null scores, and meaningful prices
df = df.dropna(subset=["final_score_1m", "final_score_3m"])
df = df[df["last_close"] > 0]
df = df[(df["ret_1m_pct"] > 0) & (df["ret_3m_pct"] > 0)]

# Optional: drop UNKNOWN sector if you want cleaner sector play
# df = df[df["sector"].notna() & (df["sector"] != "UNKNOWN")]

print(f"After basic filters: {len(df)} rows")

# ===== 3) Leadership thresholds (RS-enhanced) =====
STRICT_MIN_FINAL_3M = 70.0
STRICT_MIN_FINAL_1M = 60.0

RELAXED_MIN_FINAL_3M = 60.0
RELAXED_MIN_FINAL_1M = 50.0

# Additional sanity: require RS to be at least mid-tier
MIN_RS_3M_RELAXED = 40.0   # 40th percentile
MIN_RS_3M_STRICT  = 60.0   # 60th percentile

# ===== 4) Strict leadership list =====
cond_strict = (
    (df["final_score_3m"] >= STRICT_MIN_FINAL_3M) &
    (df["final_score_1m"] >= STRICT_MIN_FINAL_1M) &
    (df["RS_3m_score"]    >= MIN_RS_3M_STRICT)
)

leaders_strict = df[cond_strict].copy()
leaders_strict = leaders_strict.sort_values(
    ["final_score_3m", "final_score_1m"],
    ascending=False
)

# ===== 5) Relaxed leadership list =====
cond_relaxed = (
    (df["final_score_3m"] >= RELAXED_MIN_FINAL_3M) &
    (df["final_score_1m"] >= RELAXED_MIN_FINAL_1M) &
    (df["RS_3m_score"]    >= MIN_RS_3M_RELAXED)
)

leaders_relaxed = df[cond_relaxed].copy()
leaders_relaxed = leaders_relaxed.sort_values(
    ["final_score_3m", "final_score_1m"],
    ascending=False
)

print(f"Strict leaders count:  {len(leaders_strict)}")
print(f"Relaxed leaders count: {len(leaders_relaxed)}")

# ===== 6) Select columns to keep =====
cols_out = [
    "ticker",
    "sector",
    "last_close",
    "ret_1m_pct",
    "ret_3m_pct",
    "score_1m_stock",
    "score_3m_stock",
    "score_1m_sector",
    "score_3m_sector",
    "RS_1m_score",
    "RS_3m_score",
    "final_score_1m",
    "final_score_3m",
]

leaders_strict_out  = leaders_strict[cols_out]
leaders_relaxed_out = leaders_relaxed[cols_out]

# ===== 7) Save outputs =====
strict_path  = DATA_DIR / "leadership_candidates.csv"
relaxed_path = DATA_DIR / "leadership_candidates_relaxed.csv"

leaders_strict_out.to_csv(strict_path, index=False)
leaders_relaxed_out.to_csv(relaxed_path, index=False)

print(f"\n✅ Saved strict leaders to:   {strict_path}")
print(f"✅ Saved relaxed leaders to: {relaxed_path}")

print("\nSample (strict):")
print(leaders_strict_out.head())

print("\nSample (relaxed):")
print(leaders_relaxed_out.head())
