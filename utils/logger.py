import csv
import os
from datetime import datetime

def log_signal(result, symbol, entry):
    if result["status"] == "ignore":
        return  # Skipping irrelevant signals

    if result.get("confidence", 0) == 0:
        return  # Skipping weak signals

    # Filename in the format signals_2025-04-13.csv
    date_str = datetime.utcnow().strftime("%Y-%m-%d")
    filename = f"signals_{date_str}.csv"

    data = {
        "datetime": datetime.utcnow().isoformat(),
        "symbol": symbol,
        "direction": result["scenario_bias"], #'direction' means bias assessment (not a trade signal)
        "status": result["status"],
        "confidence": result.get("confidence"),
        "entry": entry,
        "stop": result.get("stop"), # 'stop' and 'tp' refer to structural level detection (not order placement)
        "tp": result.get("tp"),
        "rr": result.get("rr"),
        "reason": result.get("reason"),
        "mode": result.get("market_mode", "unknown")
    }

    file_exists = os.path.isfile(filename)
    with open(filename, mode="a", newline='', encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=data.keys())
        if not file_exists:
            writer.writeheader()
        writer.writerow(data)
        
def debug_entry_log(symbol, result, atr, volume_spike):
    print(f"📊 {symbol} | Status: {result['status'].upper()} | Confidence: {result.get('confidence', '-')}")
    print(f"    Direction: {result.get('direction', '-')}")
    print(f"    Market mode: {result.get('market_mode', '-')}")
    print(f"    RR: {result.get('rr', '-')}, ATR: {atr:.4f}")
    print(f"    Volume spike: {volume_spike}")
    print(f"    Reasons: {result.get('reason', '-')}")

import logging

logger = logging.getLogger("level_bot")
logger.setLevel(logging.INFO)

handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s — %(levelname)s — %(message)s')
handler.setFormatter(formatter)

logger.addHandler(handler)
