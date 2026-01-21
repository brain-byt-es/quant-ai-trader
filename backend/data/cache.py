from __future__ import annotations
import json
import sqlite3
from pathlib import Path
from typing import Any, Optional

class Cache:
    """Persistent SQLite-backed cache for API responses."""

    def __init__(self):
        # Store cache in a separate db file to keep main db clean
        self.db_path = Path(__file__).parent.parent / "api_cache.db"
        self._init_db()

    def _init_db(self):
        """Initialize the cache database schema."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS api_cache (
                    category TEXT,
                    key TEXT,
                    data TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (category, key)
                )
            """)
            conn.commit()

    def _get(self, category: str, key: str) -> Optional[list[dict[str, Any]]]:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "SELECT data FROM api_cache WHERE category = ? AND key = ?", 
                    (category, key)
                )
                row = cursor.fetchone()
                if row:
                    return json.loads(row[0])
        except Exception as e:
            print(f"Cache Read Error: {e}")
        return None

    def _set(self, category: str, key: str, data: list[dict[str, Any]]):
        try:
            # 1. Fetch existing
            existing = self._get(category, key) or []
            
            # 2. Merge (Logic from original cache)
            key_fields = {
                "prices": "time",
                "financial_metrics": "report_period",
                "line_items": "report_period",
                "insider_trades": "filing_date",
                "company_news": "date"
            }
            key_field = key_fields.get(category, "id")
            
            existing_keys = {item.get(key_field) for item in existing if item.get(key_field)}
            merged = existing.copy()
            merged.extend([item for item in data if item.get(key_field) not in existing_keys])
            
            # 3. Save
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "INSERT OR REPLACE INTO api_cache (category, key, data) VALUES (?, ?, ?)",
                    (category, key, json.dumps(merged))
                )
                conn.commit()
        except Exception as e:
            print(f"Cache Write Error: {e}")

    def get_prices(self, ticker: str) -> list[dict[str, Any]] | None:
        return self._get("prices", ticker)

    def set_prices(self, ticker: str, data: list[dict[str, Any]]):
        self._set("prices", ticker, data)

    def get_financial_metrics(self, ticker: str) -> list[dict[str, Any]] | None:
        return self._get("financial_metrics", ticker)

    def set_financial_metrics(self, ticker: str, data: list[dict[str, Any]]):
        self._set("financial_metrics", ticker, data)

    def get_line_items(self, ticker: str) -> list[dict[str, Any]] | None:
        return self._get("line_items", ticker)

    def set_line_items(self, ticker: str, data: list[dict[str, Any]]):
        self._set("line_items", ticker, data)

    def get_insider_trades(self, ticker: str) -> list[dict[str, Any]] | None:
        return self._get("insider_trades", ticker)

    def set_insider_trades(self, ticker: str, data: list[dict[str, Any]]):
        self._set("insider_trades", ticker, data)

    def get_company_news(self, ticker: str) -> list[dict[str, Any]] | None:
        return self._get("company_news", ticker)

    def set_company_news(self, ticker: str, data: list[dict[str, Any]]):
        self._set("company_news", ticker, data)


# Global cache instance
_cache = Cache()


def get_cache() -> Cache:
    """Get the global cache instance."""
    return _cache
