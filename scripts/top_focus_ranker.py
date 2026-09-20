import os
import pandas as pd
from pathlib import Path

# =====================================================
# Paths
# =====================================================
BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"

STAGE2_VCP_PATH = DATA_DIR / "stage2_vcp_candidates.csv"
STAGE2_PATH = DATA_DIR / "stage2_candidates.csv"
UPDATED_TICKERS_FILE = DATA_DIR / "updated_tickers_today.txt"

# =====================================================
# Helpers
# =====================================================
def normalize(ticker: str) -> str:
    return ticker.replace(".NS", "").replace("_NS", "").upper()

# =====================================================
# Load candidates
# =====================================================
df = None
source = None

if STAGE2_VCP_PATH.exists():
    df = pd.read_csv(STAGE2_VCP_PATH)
    source = "Stage-2 VCP candidates"
    if df.empty:
        df = None

if df is None:
    if not STAGE2_PATH.exists():
        print("❌ No Stage-2 candidate files found.")
        raise SystemExit
    df = pd.read_csv(STAGE2_PATH)
    source = "Stage-2 candidates"

if df.empty:
    print("🚫 No candidates available to rank.")
    raise SystemExit

print(f"▶ Loaded {len(df)} rows from {source}")

# =====================================================
# Restrict to updated tickers (SAFE)
# =====================================================
if UPDATED_TICKERS_FILE.exists():
    updated = {
        normalize(t)
        for t in UPDATED_TICKERS_FILE.read_text().splitlines()
        if t.strip()
    }

    df["_norm"] = df["ticker"].apply(normalize)

    before = len(df)
    df = df[df["_norm"].isin(updated)]
    after = len(df)

    df = df.drop(columns=["_norm"])

    print(f"🔎 Restricting focus ranking to updated tickers: {before} → {after}")

    if df.empty:
        print("🚫 No updated Stage-2 candidates to rank today.")
        raise SystemExit

# =====================================================
# Required columns check
# =====================================================
required_cols = [
    "ticker",
    "sector",
    "last_close",
    "score_3m_stock",
    "score_3m_sector",
    "RS_3m_score",
    "VCP_score",
    "vol_ratio_vs_50d",
    "avg_vol_50d",
    "pct_above_200dma",
]

missing = [c for c in required_cols if c not in df.columns]
if missing:
    print("❌ Missing required columns:", missing)
    print("Columns present:", df.columns.tolist())
    raise SystemExit

# =====================================================
# Numeric cleanup
# =====================================================
for col in required_cols:
    if col not in ["ticker", "sector"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

# =====================================================
# Leadership score (recompute defensively)
# =====================================================
df["final_score_3m"] = (
    0.40 * df["score_3m_stock"] +
    0.40 * df["score_3m_sector"] +
    0.20 * df["RS_3m_score"]
)

# =====================================================
# Ranking components (0–1 scale)
# =====================================================
df["rank_leadership"] = df["final_score_3m"].rank(pct=True)
df["rank_rs"] = df["RS_3m_score"].rank(pct=True)
df["rank_vcp"] = df["VCP_score"].rank(pct=True)
df["rank_vol"] = df["vol_ratio_vs_50d"].rank(pct=True)
df["rank_liquidity"] = df["avg_vol_50d"].rank(pct=True)
df["rank_extension"] = (-df["pct_above_200dma"]).rank(pct=True)

# =====================================================
# Composite Focus Score
# =====================================================
df["focus_score"] = (
    0.35 * df["rank_leadership"] +
    0.25 * df["rank_rs"] +
    0.20 * df["rank_vcp"] +
    0.10 * df["rank_vol"] +
    0.10 * df["rank_extension"]
)

df["focus_score"] = df["focus_score"].round(4)

# =====================================================
# Sort & Save
# =====================================================
df = df.sort_values("focus_score", ascending=False).reset_index(drop=True)
top_n = min(10, len(df))
top_focus = df.head(top_n)

out_path = DATA_DIR / "top_focus_list.csv"
top_focus.to_csv(out_path, index=False)

print(f"\n✅ Saved Top {top_n} focus stocks to {out_path}\n")

print(top_focus[[
    "ticker",
    "sector",
    "last_close",
    "final_score_3m",
    "RS_3m_score",
    "VCP_score",
    "vol_ratio_vs_50d",
    "pct_above_200dma",
    "focus_score"
]])
