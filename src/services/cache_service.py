import os
import json
import sys
from typing import Any, Dict, Optional

IS_TESTING = "pytest" in sys.modules or any("pytest" in arg for arg in sys.argv)

CACHE_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "cache_test.json" if IS_TESTING else "cache.json"
)


class CacheService:
    @staticmethod
    def _load_raw_cache() -> Dict[str, Any]:
        if not os.path.exists(CACHE_FILE):
            return {}
        try:
            with open(CACHE_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return {}

    @staticmethod
    def _save_raw_cache(data: Dict[str, Any]):
        try:
            with open(CACHE_FILE, "w") as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            print(f"Failed to save cache file: {e}")

    @staticmethod
    def get(key: str, default: Any = None) -> Any:
        """Retrieves a cached value by key from the persistent JSON store."""
        cache = CacheService._load_raw_cache()
        return cache.get(key, default)

    @staticmethod
    def set(key: str, value: Any):
        """Saves a cached value by key in the persistent JSON store."""
        cache = CacheService._load_raw_cache()
        cache[key] = value
        CacheService._save_raw_cache(cache)

    @staticmethod
    def clear():
        """Clears all cached entries in the persistent JSON store."""
        CacheService._save_raw_cache({})

    @staticmethod
    def check_and_update_state(category: str, client) -> bool:
        """
        Queries the database for lightweight state metadata (row count and max created_at timestamp).
        Compares it to the cached state metadata.
        Returns:
          - True: If a change is detected (or cache is empty). It updates the cached state metadata.
          - False: If the database is unchanged compared to the cached state.
        """
        table_mapping = {
            "customers": "customers",
            "devices": "devices",
            "sales": "sales",
            "payments": "payments"
        }

        # Multi-table mapping for compound categories
        compound_mapping = {
            "dashboard": ["customers", "sales", "payments"],
            "ledger": ["sales", "payments"],
            "reports": ["payments"],
            "due_overdue": ["installments", "payments", "customers"]
        }

        tables_to_check = []
        if category in table_mapping:
            tables_to_check = [table_mapping[category]]
        elif category in compound_mapping:
            tables_to_check = compound_mapping[category]
        else:
            return True # If unknown category, assume changed to be safe

        cache = CacheService._load_raw_cache()
        states = cache.setdefault("__states__", {})

        changed = False

        for table in tables_to_check:
            try:
                # Query count and maximum created_at timestamp
                res = client.table(table).select("created_at", count="exact").order("created_at", desc=True).limit(1).execute()
                count = res.count if res.count is not None else 0
                max_created_at = res.data[0]["created_at"] if res.data else None
            except Exception as e:
                print(f"Error querying state metadata for table '{table}': {e}")
                # In case of network error, treat as unchanged so we degrade gracefully to cache
                continue

            current_state = {"count": count, "max_created_at": max_created_at}
            cached_state = states.get(table)

            if cached_state != current_state:
                changed = True
                states[table] = current_state

        if changed:
            CacheService._save_raw_cache(cache)

        return changed
