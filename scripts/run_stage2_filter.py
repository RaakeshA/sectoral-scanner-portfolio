import os
import pandas as pd
from pathlib import Path

# =====================================================
# Paths
# =====================================================
BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"

leaders_path = DATA_DIR / "leadership_candidates_relaxed.csv"
UPDATED_TICKERS_FILE = DATA_DIR / "updated_tickers_today.txt"

# =====================================================
# Parameters
# =====================================================
DAYS_SMA50 = 50
DAYS_SMA150 = 150
DAYS_SMA200 = 200
LOOKBACK_HIGH = 60
DAYS_3W = 15
DAYS_3M = 60

ATR_LEN_SHORT = 14
ATR_LEN_LONG = 21
ATR_LOOKBACK_VCP = 60

MAX_ABOVE_50DMA = 10.0
MAX_ABOVE_200DMA = 20.0
MAX_RUNUP_3W = 20.0
MAX_RUNUP_3M = 40.0
NEAR_HIGH_BAND = 5.0
MAX_BREAKOUT_ABOVE_HIGH = 10.0

MIN_AVG_VOL_50D = 50000
BREAKOUT_VOL_MULTIPLIER = 1.5

# =====================================================
# Helpers
# =====================================================
def normalize(ticker: str) -> str:
    return ticker.replace(".NS", "").replace("_NS", "").upper()

# =====================================================
# Load leadership list
# =====================================================
if not leaders_path.exists():
    print("❌ leadership_candidates_relaxed.csv not found.")
    raise SystemExit

leaders = pd.read_csv(leaders_path)

if leaders.empty:
    print("🚫 No leadership candidates available.")
    raise SystemExit

print(f"▶ Loaded leadership candidates: {len(leaders)}")

# =====================================================
# Restrict to updated tickers (SAFE & OPTIONAL)
# =====================================================
if UPDATED_TICKERS_FILE.exists():
    updated = {
        normalize(t)
        for t in UPDATED_TICKERS_FILE.read_text().splitlines()
        if t.strip()
    }

    leaders["_norm"] = leaders["ticker"].apply(normalize)

    before = len(leaders)
    leaders = leaders[leaders["_norm"].isin(updated)]
    after = len(leaders)

    leaders = leaders.drop(columns=["_norm"])

    print(f"🔎 Restricting Stage-2 check to updated tickers: {before} → {after}")

    if leaders.empty:
        print("🚫 No updated leadership tickers to process today.")
        raise SystemExit

# =====================================================
# Stage-2 + VCP Scan
# =====================================================
results = []

for _, row in leaders.iterrows():
    ticker = row["ticker"]
    safe_name = ticker.replace(".", "_")
    csv_path = DATA_DIR / f"{safe_name}.csv"

    print(f"Processing {ticker}")

    if not csv_path.exists():
        continue

    df = pd.read_csv(csv_path)

    # --- Date handling ---
    if "Date" in df.columns:
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    elif "timestamp" in df.columns:
        df["Date"] = pd.to_datetime(df["timestamp"], errors="coerce")
    else:
        continue

    df = df.dropna(subset=["Date"]).sort_values("Date")

    # --- Price cleanup ---
    for col in ["Close", "High", "Low"]:
        if col not in df.columns:
            df[col] = df["Close"]
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df["Volume"] = pd.to_numeric(df.get("Volume", 0), errors="coerce").fillna(0)

    df = df.dropna(subset=["Close"])

    if len(df) < max(DAYS_SMA200, DAYS_3M, LOOKBACK_HIGH) + 5:
        continue

    # --- Indicators ---
    df["SMA50"] = df["Close"].rolling(DAYS_SMA50).mean()
    df["SMA150"] = df["Close"].rolling(DAYS_SMA150).mean()
    df["SMA200"] = df["Close"].rolling(DAYS_SMA200).mean()
    df["avg_vol_50d"] = df["Volume"].rolling(50).mean()

    df["prev_close"] = df["Close"].shift(1)
    df["TR"] = pd.concat([
        df["High"] - df["Low"],
        (df["High"] - df["prev_close"]).abs(),
        (df["Low"] - df["prev_close"]).abs()
    ], axis=1).max(axis=1)

    df["ATR14"] = df["TR"].rolling(ATR_LEN_SHORT).mean()
    df["ATR21"] = df["TR"].rolling(ATR_LEN_LONG).mean()

    df = df.dropna()
    if len(df) < 5:
        continue

    last = df.iloc[-1]
    prev = df.iloc[-2]

    # --- Core Stage-2 conditions ---
    cond_alignment = (
        last["Close"] > last["SMA50"] >
        last["SMA150"] > last["SMA200"]
    )

    cond_slope = last["SMA50"] > prev["SMA50"]

    recent_high = df.tail(LOOKBACK_HIGH)["High"].max()
    pct_vs_high = (last["Close"] - recent_high) / recent_high * 100

    cond_near_high = -NEAR_HIGH_BAND <= pct_vs_high <= NEAR_HIGH_BAND
    cond_not_far_breakout = pct_vs_high <= MAX_BREAKOUT_ABOVE_HIGH

    pct_above_50dma = (last["Close"] - last["SMA50"]) / last["SMA50"] * 100
    pct_above_200dma = (last["Close"] - last["SMA200"]) / last["SMA200"] * 100

    cond_50dma = pct_above_50dma <= MAX_ABOVE_50DMA
    cond_200dma = pct_above_200dma <= MAX_ABOVE_200DMA

    runup_3w = (last["Close"] - df.iloc[-1 - DAYS_3W]["Close"]) / df.iloc[-1 - DAYS_3W]["Close"] * 100
    runup_3m = (last["Close"] - df.iloc[-1 - DAYS_3M]["Close"]) / df.iloc[-1 - DAYS_3M]["Close"] * 100

    cond_runup = runup_3w <= MAX_RUNUP_3W and runup_3m <= MAX_RUNUP_3M

    cond_liquidity = last["avg_vol_50d"] >= MIN_AVG_VOL_50D

    vol_ratio = last["Volume"] / last["avg_vol_50d"] if last["avg_vol_50d"] > 0 else 0

    # --- VCP ---
    atr_ratio = last["ATR14"] / last["ATR21"] if last["ATR21"] > 0 else 999
    atr_window = df["ATR14"].tail(ATR_LOOKBACK_VCP)

    cond_atr_tight = last["ATR14"] <= atr_window.median()
    cond_range_contracting = (
        (df["High"] - df["Low"]).tail(10).mean()
        < 0.9 * (df["High"] - df["Low"]).tail(30).head(20).mean()
    )

    VCP_score = max(0, min(100, (1 - atr_ratio) * 100 + (20 if cond_range_contracting else 0)))

    is_stage2 = (
        cond_alignment and cond_slope and cond_near_high and
        cond_not_far_breakout and cond_50dma and cond_200dma and
        cond_runup and cond_liquidity
    )

    is_vcp = is_stage2 and atr_ratio < 1 and (cond_atr_tight or cond_range_contracting)

    results.append({
        "ticker": ticker,
        "sector": row.get("sector"),
        "last_close": last["Close"],
        "pct_above_200dma": pct_above_200dma,
        "vol_ratio_vs_50d": vol_ratio,
        "ATR14": last["ATR14"],
        "ATR21": last["ATR21"],
        "atr_ratio": atr_ratio,
        "VCP_score": round(VCP_score, 2),
        "is_stage2_candidate": is_stage2,
        "is_stage2_vcp_candidate": is_vcp,
    })

# =====================================================
# Save outputs
# =====================================================
stage2_df = pd.DataFrame(results)

out_all = DATA_DIR / "stage2_check_all.csv"
out_stage2 = DATA_DIR / "stage2_candidates.csv"
out_vcp = DATA_DIR / "stage2_vcp_candidates.csv"

stage2_df.to_csv(out_all, index=False)
stage2_df[stage2_df["is_stage2_candidate"]].to_csv(out_stage2, index=False)
stage2_df[stage2_df["is_stage2_vcp_candidate"]].to_csv(out_vcp, index=False)

print(f"\n✅ Stage-2 scan complete")
print(f"Stage-2 candidates: {len(stage2_df[stage2_df['is_stage2_candidate']])}")
print(f"Stage-2 VCP candidates: {len(stage2_df[stage2_df['is_stage2_vcp_candidate']])}")
