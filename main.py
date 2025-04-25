from config import TRADING_PAIRS  # Keeping original name as requested
from exchange.api import api as bingx_api, binance as binance_wrapper
from levels_detector import LevelsDetector
from trendline_detector import TrendlineDetector
from entry_filter import check_entry
from scenario_evaluator import ScenarioEvaluator
from context_evaluator import ContextEvaluator
from utils.telegram import send_message
from indicators import calculate_atr
from datetime import datetime
import time
from utils.logger import log_signal
from exchange_info import ExchangeInfo
from utils.market_watch import top_liquid_pairs, VolatilityGuard, bingx_supported_symbols

vol_guard = VolatilityGuard()
BINGX_CONTRACTS = bingx_supported_symbols()

def main():
    print("🟢 LevelBot Analytics Engine — Context Evaluation Mode")
    api = bingx_api
    binance = binance_wrapper
    filters = check_entry
    exinfo = ExchangeInfo()
    context = ContextEvaluator()
    scenarios = ScenarioEvaluator()
    levels = LevelsDetector(binance_wrapper)

    last_refresh = 0
    SYMBOL_REFRESH_INTERVAL = 60 * 60 * 2

    def refresh_symbol_list():
        raw = top_liquid_pairs(limit=20)
        return [s for s in raw if s in BINGX_CONTRACTS]

    symbols = refresh_symbol_list()
    print("🧪 SYMBOLS SELECTED FOR ANALYSIS:", symbols)

    while True:
        now = time.time()
        if now - last_refresh > SYMBOL_REFRESH_INTERVAL:
            symbols = refresh_symbol_list()
            last_refresh = now
            print(f"📌 Active symbols updated: {symbols}")

        for symbol in symbols:
            print(f"\n🚀 Analyzing {symbol}")

            if context.check_daily_rejection_limit() or context.check_consecutive_rejections():
                continue

            key_levels = levels.detect_swing_levels(symbol)
            if not key_levels:
                continue
            key_levels = TrendlineDetector(binance).detect_combined_levels(symbol, key_levels)

            print(f"🧭 next_swing_high: {key_levels.get('next_swing_high')}")
            print(f"🧭 next_swing_low:  {key_levels.get('next_swing_low')}")

            klines_1m = binance.get_klines(symbol, "1m", limit=30)
            if not klines_1m:
                print(f"⚠️ No 1m data available for {symbol}")
                continue

            closes_1m = [float(k[4]) for k in klines_1m]
            highs_1m = [float(k[2]) for k in klines_1m]
            lows_1m = [float(k[3]) for k in klines_1m]
            atr_1m = calculate_atr(highs_1m, lows_1m, closes_1m, period=14)

            signal = filters(symbol, key_levels, None)
            current_price = float(klines_1m[-1][4]) if klines_1m else None

            if vol_guard.push(atr_1m) and not (
                signal and signal.get("direction") and
                signal["confidence"] >= 2 and
                signal.get("trend_1h") == signal["direction"] and
                signal.get("trend_4h") == signal["direction"]
            ):
                print(f"⚠️ High volatility detected for {symbol} — evaluation paused")
                continue

            if signal and signal["status"] in ["valid", "watch"] and signal.get("confidence", 0) > 0 and current_price:
                log_signal(signal, symbol, current_price)
                rr = signal.get("rr", "?")
                conf = signal.get("confidence", "?")
                reason = signal.get("reason", "?")
                direction = signal.get("direction", "?")  
                scenario_bias = direction  
                atr = signal.get("atr", 0.0)

                print(f"🚀 {symbol} | Scenario Bias: {scenario_bias} | RR: {rr} | ATR: {atr:.5f} | Confidence: {conf}")
                print(f"📌 Validation summary: {reason}")

            if not signal or signal["status"] != "valid":
                print("⚠️ No valid scenario detected (status = {})".format(
                    signal["status"] if signal else "None",
                ))
                print(f"🎯 Swing levels {symbol}: HIGH={key_levels['swing_high']:.2f}, LOW={key_levels['swing_low']:.2f}")

                klines_price = binance.get_klines(symbol, "1m", limit=1)
                if klines_price:
                    try:
                        current_price = float(klines_price[-1][4])
                        print(f"📈 Latest price {symbol}: {current_price:.2f}")
                    except Exception as e:
                        print(f"⚠️ Price parsing error: {e}")
                else:
                    print("⚠️ Failed to retrieve price from Binance")

                continue

        print("\n🟢 Cycle complete. Pausing 1 minute...\n")
        time.sleep(60)

if __name__ == "__main__":
    main()
