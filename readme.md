# LevelBot Analytics Engine

**Structured market insights — infrastructure for research, analytics platforms, and ecosystem tools.**

---

## About the project

### Problem

Crypto markets generate massive amounts of raw data — but most of it is either low-level price feeds or speculative “Buy/Sell” signals.

This leaves a critical gap for neutral, structured, high-quality market context that helps analysts, data providers, DeFi platforms, and research teams understand:

- Where are the key levels?  
- Is this breakout meaningful or just noise?  
- Are momentum and volatility aligned to support this move?  
- Which market phase are we really in — trend, consolidation, impulse, or overheated?

Without this context, data remains fragmented, noisy, and hard to act on responsibly.

---

### Solution

**LevelBot Analytics Engine** provides structured, multi-factor market insights — not speculative signals.

It detects:

- **Key price levels** (Swing High/Low clusters, trendlines, breakouts)  
- **Market phases** (trend, range, impulse, overheated)  
- **Momentum and confirmation factors** (ATR, MACD, Volume Profile, multi-timeframe trend alignment)  
- **Confidence scoring** based on multi-layer validation of signal quality  

Instead of telling users what to do, the engine provides reliable market context that supports:

- Analytics platforms and dashboards (level detection, phase analysis)  
- Research teams and data providers (scenario validation, enriched reports)  
- DeFi tools and builders (market context for strategies, bots, DAO logic)  
- Educational projects and developer tooling (teaching market structure)

---

### What makes this project different

- **Signal hygiene, not hype**  
  The engine applies a risk-aware validation system that filters out weak setups, misaligned trends, and overextended conditions.

- **Designed for integration**  
  Modular, open-source architecture — easy to use in other projects via API or direct integration.

- **Analytics-first approach**  
  Focused on supporting data quality, transparency, and infrastructure growth across the crypto ecosystem.

- **Production-grade design**  
  Vectorized calculations, clean modular structure, and reproducible analysis logic.

## Current status

- Fully working MVP: Python-based analytics engine with multi-layer signal validation  
- Designed as an analytics-first engine with no execution layer — safe for open-source use and ecosystem integration  
- Modular structure ready for open-source publication  
- Clear roadmap for API exposure, ecosystem integration, and GUI/dashboard development  
- Code available on GitHub (private repo, access on request)

---

## How to run

1. Install Python 3.9+.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the analysis:
   ```bash
   python main.py
   ```
4. The output will show detected levels, trendlines, phases, and signal confidence.

---

## Example output

```
 Analyzing TAO-USDT
🧭 next_swing_high: 344.86
🧭 next_swing_low:  316.55555555555554

▶️ Starting structural evaluation for TAO-USDT
[DEBUG] ➕ Trendline breakout price: 354.4260869565218
[DEBUG] ✅ Evaluation level selected from trendline: 352.98109
[DEBUG] poc_val: 356.318
[DEBUG] final confidence: 3.0
📊 TAO-USDT | Status: VALID_WEAK | Confidence: 3.0
    Direction: LONG
    Market mode: neutral
    RR: 3.0, ATR: 5.7800
    Volume spike: False
    Reasons: Simple up breakout, breakout of upward trendline 15m, breakout of upward trendline 1h, Simple up breakout, breakout of upward trendline 15m, breakout of upward trendline 1h, very old level, 4H confirms, near POC, MACD confirms
⚠️ No valid scenario detected (status = valid_weak)
🎯 Swing levels TAO-USDT: HIGH=338.81, LOW=331.91
📈 Latest price TAO-USDT: 355.50

This is a real log excerpt from LevelBot Analytics Engine.  
The engine analyzes multiple pairs, detects swing levels, trendlines, market phases, and validates signals with multi-factor scoring.

---

## Repository structure

levelbot-analytics/
├── README.md                # Project description and usage instructions
├── LICENSE                  # License file (Apache 2.0 recommended)
├── requirements.txt         # Python dependencies
├── config.py                # Configuration file
├── entry_filter.py          # Scenario evaluation logic and market condition filters
├── entry_filter_retest.py   # Alternative scenario evaluation (retest logic)
├── exchange_info.py         # Exchange metadata and precision utilities (for accurate level calculations)
├── indicators.py            # Indicators: ATR, MACD, EMA, Volume Profile (used for momentum and context analysis)
├── levels_detector.py       # Swing High/Low level detection and clustering logic
├── main.py                  # Main script to run the analytics engine
├── scenario_evaluator.py    # Scenario evaluation logic and structural level assessment
├── context_evaluator.py     # Scenario hygiene tools: enforce context checks, avoid invalid or noisy setups
├── risk_utils.py            # Helper functions for structural assessment (used for level evaluation and scoring)
├── symbol_selector.py       # Symbol selection logic (based on liquidity, volatility, or defined lists)
├── trendline_detector.py    # Trendline detection and breakout analysis
├── exchange/
│   └── api.py               # Exchange metadata and utilities (used for information retrieval only)
└── utils/
    ├── logger.py            # Logging utilities for signal evaluation and scenario tracking
    ├── market_watch.py      # Market monitoring tools for data inspection and validation
    ├── telegram.py          # Optional Telegram notifications 
    └── volume_profile.py    # Volume Profile calculations (Point of Control and low-volume areas)




## License

LevelBot Analytics is open-source software licensed under the Apache License 2.0.  
See the LICENSE file in this repository for the full license text.

