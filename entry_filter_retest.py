import numpy as np

def entry_filter_retest(
    direction,
    current_price,
    closes_15m,
    swing_high,
    swing_low,
    atr,
    candle_stats,
    structural_target,
    structural_limit,
    rr,
    trend_1h=None,
    trend_4h=None,
    macd_confirms=None,
    confidence=None,
    debug=False,
    retest_age=0,
    reasons: list = None
):
    if reasons:
        reason_str = " ".join(reasons).lower()
        if "breakout" in reason_str or "exit from low-volume area" in reason_str:
            if debug:
                print("✅ Breakout confirmed — overheated filter is not applied")
            return None

    last_3_closes = closes_15m[-4:]  # always the last three closed candles
    confirm = (
        candle_stats.get("strong_body") or
        candle_stats.get("volume_spike") or
        macd_confirms or
        (trend_1h == direction)
    )

    # Skip overheated check if trend and confirmation are present
    if trend_1h == direction and trend_4h == direction and confirm:
        if debug:
            print("✅ Overheated check skipped — strong trend + confirmation")
        return None

    # Additional candle body filter (overheated condition)
    body_sizes = [abs(closes_15m[i] - closes_15m[i - 1]) for i in range(-3, 0)]
    if retest_age > 0 and max(body_sizes) > atr * 1.2 and not confirm:
        if debug:
            print("💥 Overheated based on candle bodies:", body_sizes)
        return {
            "status": "skip",
            "reason": "body stretch — evaluation too late",
            "atr": atr
        }

    if direction == "LONG":
        impulse_phase = swing_high < current_price <= swing_high + atr * 0.3
        overheated_phase = current_price > swing_high + atr * 2.0
        retest_zone = abs(current_price - swing_high) <= atr * 0.1

        if debug:
            print(f"[LONG] current: {current_price:.2f}, swing_high: {swing_high}, ATR: {atr}")
            print(f"phase = impulse:{impulse_phase} / overheated:{overheated_phase} / retest:{retest_zone}")
            print(f"confirm: {confirm}")

        if impulse_phase:
            return None  # valid scenario

        if overheated_phase and confidence < 2:
            return {
                "status": "skip",
                "reason": "overheated long — price significantly above swing_high",
                "atr": atr
            }

        if retest_zone and confirm:
            return {
                "status": "valid",
                "scenario_bias": direction,  
                "evaluation_price": current_price,
                "structural_target": structural_target,
                "structural_limit": structural_limit,
                "reason": "validation after retest with confirmation (LONG)",
                "rr": round(rr, 2),
                "atr": atr
            }

        if retest_zone:
            return {
                "status": "wait_retest",
                "reason": "waiting for confirmation after return to swing_high (LONG)",
                "atr": atr
            }

    elif direction == "SHORT":
        impulse_phase = swing_low - atr * 0.3 <= current_price < swing_low
        overheated_phase = current_price < swing_low - atr * 2.0
        retest_zone = abs(current_price - swing_low) <= atr * 0.1

        if debug:
            print(f"[SHORT] current: {current_price:.2f}, swing_low: {swing_low}, ATR: {atr}")
            print(f"phase = impulse:{impulse_phase} / overheated:{overheated_phase} / retest:{retest_zone}")
            print(f"confirm: {confirm}")

        if impulse_phase:
            return None

        if overheated_phase and confidence < 2:
            return {
                "status": "skip",
                "reason": "overheated short — price significantly below swing_low",
                "atr": atr
            }

        if retest_zone and confirm:
            return {
                "status": "valid",
                "scenario_bias": direction,  
                "evaluation_price": current_price,
                "structural_target": structural_target,
                "structural_limit": structural_limit,
                "reason": "validation after retest with confirmation (SHORT)",
                "rr": round(rr, 2),
                "atr": atr
            }

        if retest_zone:
            return {
                "status": "wait_retest",
                "reason": "waiting for confirmation after return to swing_low (SHORT)",
                "atr": atr
            }

    return None  # no reason to evaluate further
