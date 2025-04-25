"""
ContextEvaluator — scenario validation counters for analysis hygiene.

This module simulates daily and consecutive rejection counters
to support scenario evaluation, filtering, and testing.

No trades are executed. These counters serve to track
how often scenarios are rejected or accepted based on analysis conditions.
"""

import csv
from pathlib import Path
from threading import Lock
from config import DAILY_REJECTION_LIMIT, MAX_CONSECUTIVE_REJECTIONS, LOG_PATH
from datetime import datetime

_FILE_LOCK = Lock()

def _TODAY_UTC() -> str:
    return datetime.utcnow().strftime("%Y-%m-%d")

def _write_csv_row(path: str | Path, row: dict, header: list[str]) -> None:
    path = Path(path)
    with _FILE_LOCK:
        file_exists = path.exists()
        with path.open("a", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=header)
            if not file_exists:
                writer.writeheader()
            writer.writerow(row)

class ContextEvaluator:
    """Tracks rejection counters for scenario validation (analysis hygiene)."""

    def __init__(self) -> None:
        self.daily_rejection_count: int = 0
        self.consecutive_rejections: int = 0
        self._load_today_stats()

    def check_daily_rejection_limit(self) -> bool:
        if self.daily_rejection_count >= abs(DAILY_REJECTION_LIMIT):
            print(f"🚫 Daily rejection limit reached: {self.daily_rejection_count} ≥ {DAILY_REJECTION_LIMIT}")
            return True
        return False

    def check_consecutive_rejections(self) -> bool:
        if self.consecutive_rejections >= MAX_CONSECUTIVE_REJECTIONS:
            print(f"⛔️ Consecutive rejection limit reached: {self.consecutive_rejections}")
            return True
        return False

    def log_scenario(self, date_utc: str, symbol: str, scenario_status: str) -> None:
        """
        Records whether a scenario was accepted or rejected.
        Used for internal evaluation of analysis hygiene.
        """
        row = {
            "date": date_utc,
            "symbol": symbol,
            "scenario_status": scenario_status.upper(),
        }
        _write_csv_row(LOG_PATH, row, header=["date", "symbol", "scenario_status"])

        today = _TODAY_UTC()
        if date_utc != today:
            return

        if scenario_status.upper() == "REJECTED":
            self.daily_rejection_count += 1
            self.consecutive_rejections += 1
        elif scenario_status.upper() == "ACCEPTED":
            self.consecutive_rejections = 0

    def _load_today_stats(self) -> None:
        path = Path(LOG_PATH)
        if not path.exists():
            return
        today = _TODAY_UTC()
        with path.open("r", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get("date") != today:
                    continue
                if row.get("scenario_status", "").upper() == "REJECTED":
                    self.daily_rejection_count += 1
                    self.consecutive_rejections += 1
                elif row.get("scenario_status", "").upper() == "ACCEPTED":
                    self.consecutive_rejections = 0

    def reset_counters(self) -> None:
        """Reset daily scenario counters (should be called at UTC midnight)."""
        print("🔄 Daily scenario counters reset")
        self.daily_rejection_count = 0
        self.consecutive_rejections = 0
