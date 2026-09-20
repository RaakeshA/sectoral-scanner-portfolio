# NSE Stage-2 & VCP Stock Scanner

A Python-based systematic stock screening engine designed to identify Stage-2 trends, Volatility Contraction Patterns (VCP), relative-strength leaders and sector momentum across the NSE universe.

## Overview

The scanner combines technical trend analysis, volatility contraction, relative strength, liquidity and sector-level analysis to systematically identify stocks exhibiting characteristics of strong technical setups.

## Key Features

- Stage-2 trend identification
- Stage-2A breakout detection
- Volatility Contraction Pattern (VCP) detection
- ATR-based volatility analysis
- Relative strength analysis versus the NIFTY
- Sector strength and stock strength scoring
- Liquidity filtering
- Breakout volume validation
- Candidate ranking and prioritisation
- Automated end-to-end screening pipeline

## Screening Framework

```text
NSE Stock Universe
        ↓
Market & Liquidity Filters
        ↓
Stage-2 Trend Detection
        ↓
Relative Strength Analysis
        ↓
Sector Strength Analysis
        ↓
VCP / Volatility Analysis
        ↓
Breakout & Volume Validation
        ↓
Scoring & Ranking
        ↓
Shortlisted Candidates\

## Technology
Python
Pandas
NumPy
yfinance
Technical indicator calculations


## Project Structure
├── config/
│   ├── indices.txt
│   ├── stock_sector_map.csv
│   └── tickers.txt
│
├── scripts/
│   ├── run_stage2_filter.py
│   ├── top_focus_ranker.py
│   ├── compute_rs_vs_nifty.py
│   ├── compute_sector_strength.py
│   ├── compute_stock_strength.py
│   └── merge_scores.py
│
├── requirements.txt
└── run_all.py

##Purpose

This project was built as a research and screening tool to automate a repeatable process for identifying technically strong stocks and reducing manual effort in equity market analysis.

Disclaimer

This project is intended for educational and research purposes only and does not constitute investment advice or a recommendation to buy or sell securities.
