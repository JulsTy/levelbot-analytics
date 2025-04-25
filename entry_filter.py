from exchange.api import BinanceWrapper
from utils.logger import log_signal, debug_entry_log
from indicators import (
    calculate_trend,
    calculate_volume_profile,
    calculate_normalized_macd,
    calculate_candle_stats,
    calculate_atr,
    evaluate_direction,
    assess_confidence,
    classify_market_mode
)
from entry_filter_retest import entry_filter_retest
from risk_utils import select_structural_limit, select_structural_target
from trendline_detector import TrendlineDetector

def check_entry(symbol, key_levels, scenario_evaluator):
    print(f"\n▶️ Starting structural evaluation for {symbol}")

   
    binance = BinanceWrapper()
    klines_15m = binance.get_klines(symbol, interval='15m', limit=20)
    klines_1h = binance.get_klines(symbol, interval='1h', limit=50)
    klines_4h = binance.get_klines(symbol, interval='4h', limit=50)

    if not klines_15m or not klines_1h or not klines_4h:
        print(f"⛔ EXIT EARLY: Not enough data available for {symbol}")
        return None

    closes_15m = [float(k[4]) for k in klines_15m]
    volumes_15m = [float(k[5]) for k in klines_15m]
    highs_15m = [float(k[2]) for k in klines_15m]
    lows_15m = [float(k[3]) for k in klines_15m]
    closes_1h = [float(k[4]) for k in klines_1h]
    closes_4h = [float(k[4]) for k in klines_4h]
    highs_1h = [float(k[2]) for k in klines_1h]
    lows_1h = [float(k[3]) for k in klines_1h]
    current_price = closes_15m[-1]

    atr = calculate_atr(highs_15m, lows_15m, closes_15m, period=5)
    atr_slow = calculate_atr(highs_15m, lows_15m, closes_15m, period=15)
    atr_1h = calculate_atr(highs_1h, lows_1h, closes_1h)
    trend_1h = calculate_trend(closes_1h, atr_1h)
    trend_4h = calculate_trend(closes_4h, atr_1h)
    market_mode = classify_market_mode(trend_1h, atr, atr_slow, volumes_15m)
    last_candle = klines_15m[-1]
    candle_stats = calculate_candle_stats(last_candle, atr, volumes_15m)

    swing_high = key_levels.get("swing_high")
    swing_low = key_levels.get("swing_low")
    swing_age = key_levels.get("swing_age", 0)

    direction, reasons, in_middle = evaluate_direction(
        current_price=current_price,
        swing_high=swing_high,
        swing_low=swing_low,
        trend_1h=trend_1h,
        atr=atr,
        highs=highs_15m,
        lows=lows_15m,
        candle_stats=candle_stats
    )
    if direction is None:
        return {"status": "watch", "scenario_bias": None, "reason": "no direction", "atr": atr}

    detector = TrendlineDetector(binance)
    trendlines = detector.detect_trendlines_multi(symbol)
    for tf in ["15m", "1h"]:
        for side in ["up", "down"]:
            key_levels[f"trendline_{tf}_{side}"] = trendlines.get(tf, {}).get(f"{side}_trendline")

    breakout_reasons = detector.check_trendline_breakout(current_price, direction, key_levels)
    reasons.extend(breakout_reasons)

    trendline_breakout = None
    trendline_target = None
    if direction == "LONG":
        for tf in ["15m", "1h"]:
            up = key_levels.get(f"trendline_{tf}_up")
            down = key_levels.get(f"trendline_{tf}_down")
            if up and current_price > up.get("price_now", 0):
                trendline_breakout = up.get("price_now")
            if down:
                trendline_target = down.get("price_now")
    elif direction == "SHORT":
        for tf in ["15m", "1h"]:
            down = key_levels.get(f"trendline_{tf}_down")
            up = key_levels.get(f"trendline_{tf}_up")
            if down and current_price < down.get("price_now", float("inf")):
                trendline_breakout = down.get("price_now")
            if up:
                trendline_target = up.get("price_now")

    key_levels["trendline_breakout_price"] = trendline_breakout
    key_levels["trendline_opposite_target"] = trendline_target
    print(f"[DEBUG] ➕ Trendline breakout price: {trendline_breakout}")

    structural_limit = select_structural_limit(
        entry_price=current_price,
        atr=atr,
        swing_high=swing_high,
        swing_low=swing_low,
        trendline_price=trendline_breakout,
        poc=None,
        low_volume_exit=None,
        side=direction
    )
    if structural_limit is None:
        return {"status": "skip", "reason": "No valid structural limit found", "atr": atr}

    is_breakout = any("breakout" in r or "exit" in r for r in reasons)
    structural_target, partial_target, dynamic_target = select_structural_target(
        entry_price=current_price,
        structural_limit=structural_limit,
        atr=atr,
        swing_high=swing_high,
        swing_low=swing_low,
        next_swing_high=key_levels.get("next_swing_high"),
        next_swing_low=key_levels.get("next_swing_low"),
        trendline_target=trendline_target,
        poc=None,
        low_volume_exit=None,
        side=direction,
        breakout=is_breakout
    )

    rr = abs(structural_target - current_price) / abs(current_price - structural_limit)

    macd_data = calculate_normalized_macd(closes_1h)
    volume_profile = calculate_volume_profile(klines_15m)

    confidence, confidence_reasons = assess_confidence(
        direction=direction,
        reasons=list(reasons),
        swing_age=swing_age,
        trend_4h=trend_4h,
        vp=volume_profile,
        macd_data=macd_data,
        current_price=current_price,
        atr=atr
    )

    retest_check = entry_filter_retest(
        direction=direction,
        current_price=current_price,
        closes_15m=closes_15m,
        swing_high=swing_high,
        swing_low=swing_low,
        atr=atr,
        candle_stats=candle_stats,
        structural_target=structural_target,
        structural_limit=structural_limit,
        rr=rr,
        trend_1h=trend_1h,
        trend_4h=trend_4h,
        macd_confirms="MACD does not confirm" not in reasons,
        confidence=confidence,
        debug=False,
        retest_age=0,
        reasons=reasons
    )
    if retest_check:
        print(f"💡 Retest filter activated for {symbol}: {retest_check.get('reason', 'Reason not specified')}")
        return retest_check

    weak_candle = in_middle or candle_stats["doji"]
    weak_volume = candle_stats["weak_volume"] and not candle_stats["strong_body"]

    is_strong = (
        (not weak_candle) and
        candle_stats["volume_spike"] and
        (confidence >= 2)
    )

    if is_strong:
        status = "valid"
        final_target = structural_target
    elif confidence >= 1 and not (weak_candle and weak_volume):
        status = "valid_weak"
        final_target = current_price + (current_price - structural_limit) * 1.5 if direction == "LONG" else current_price - (structural_limit - current_price) * 1.5
    else:
        return {"status": "ignore", "reason": "Signal too weak", "atr": atr}

    result = {
        "status": status,
        "mode": "weak" if status == "valid_weak" else "normal",
        "scenario_bias": direction,
        "direction": direction,
        "structural_limit": structural_limit,
        "structural_target": final_target,
        "full_target": structural_target,
        "partial_target": partial_target,
        "dynamic_target": dynamic_target,
        "rr": rr,
        "atr": atr,
        "reason": ", ".join(reasons + confidence_reasons),
        "market_mode": market_mode,
        "confidence": confidence
    }
    result["trend_1h"] = trend_1h
    result["trend_4h"] = trend_4h
    log_signal(result, symbol, current_price)
    debug_entry_log(symbol, result, atr, candle_stats["volume_spike"])
    return result

