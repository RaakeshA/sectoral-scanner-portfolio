import subprocess
import sys
from pathlib import Path
from datetime import datetime

# ---------------- PATHS ----------------
BASE_DIR = Path(__file__).resolve().parent   # Sectoral_Scanner/
SCRIPTS_DIR = BASE_DIR / "scripts"
DATA_DIR = BASE_DIR / "data"

UPDATED_TICKERS_FILE = DATA_DIR / "updated_tickers_today.txt"

PYTHON = sys.executable  # correct python for venv / GitHub Actions


# ---------------- HELPERS ----------------
def run_script(script_name: str):
    script_path = SCRIPTS_DIR / script_name

    if not script_path.exists():
        print(f"❌ Script not found: {script_path}")
        sys.exit(1)

    print(f"\n▶ Running {script_name}")
    result = subprocess.run(
        [PYTHON, str(script_path)],
        cwd=str(BASE_DIR),
    )

    if result.returncode != 0:
        print(f"❌ Failed: {script_name}")
        sys.exit(result.returncode)


def has_new_data() -> bool:
    if not UPDATED_TICKERS_FILE.exists():
        return False

    with open(UPDATED_TICKERS_FILE, "r") as f:
        tickers = [line.strip() for line in f if line.strip()]

    return len(tickers) > 0


# ---------------- PIPELINE ----------------
print("\n" + "=" * 60)
print("🚀 SECTORAL SCANNER – DAILY PIPELINE")
print("🕒 Start:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
print("=" * 60)

# 1) Always run incremental price updater
run_script("download_all_price_data.py")

# 2) Stop early if no new trading data
if not has_new_data():
    print("\n🚫 No new market data detected.")
    print("✅ Pipeline stopped safely. No recomputation needed.")
    print("=" * 60)
    sys.exit(0)

print("\n📈 New data detected → running analytics pipeline")

# 3) Stock strength
run_script("compute_stock_strength.py")
run_script("compute_strength_scores.py")

# 4) Sector strength
run_script("compute_sector_strength.py")
run_script("compute_sector_scores.py")

# 5) Relative strength vs NIFTY
run_script("compute_rs_vs_nifty.py")
run_script("compute_rs_scores.py")

# 6) Merge + leadership + Stage-2 + VCP
run_script("merge_scores.py")
run_script("run_leadership_scanner.py")
run_script("run_stage2_filter.py")

# 7) Final ranking
run_script("top_focus_ranker.py")

print("\n" + "=" * 60)
print("✅ PIPELINE COMPLETED SUCCESSFULLY")
print("🕒 End:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
print("=" * 60)
