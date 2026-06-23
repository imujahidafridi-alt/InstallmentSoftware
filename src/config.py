import os
import json

import sys

if getattr(sys, 'frozen', False):
    CONFIG_FILE = os.path.join(os.path.dirname(sys.executable), "config.json")
else:
    CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")


class ConfigManager:
    _cached_config = None

    @staticmethod
    def load_config() -> dict:
        if ConfigManager._cached_config is not None:
            return ConfigManager._cached_config

        if not os.path.exists(CONFIG_FILE):
            default_config = {
                "theme": "light",
                "shop_name": "Asif Mobile Center",
                "shop_address": "Main Market, Commercial Area",
                "shop_contact": "Ph: 0300-1234567",
                "decimal_places": 2
            }
            ConfigManager.save_config(default_config)
            ConfigManager._cached_config = default_config
            return default_config
        try:
            with open(CONFIG_FILE, "r") as f:
                ConfigManager._cached_config = json.load(f)
                return ConfigManager._cached_config
        except Exception:
            return {}

    @staticmethod
    def save_config(config_data: dict):
        ConfigManager._cached_config = config_data
        with open(CONFIG_FILE, "w") as f:
            json.dump(config_data, f, indent=4)

    @staticmethod
    def get_decimal_places() -> int:
        config = ConfigManager.load_config()
        return config.get("decimal_places", 2)

    @staticmethod
    def format_currency(value) -> str:
        if value is None:
            val = 0.0
        else:
            try:
                val = float(value)
            except (ValueError, TypeError):
                val = 0.0
        
        dec = ConfigManager.get_decimal_places()
        if dec == 0:
            return f"Rs. {val:,.0f}"
        else:
            return f"Rs. {val:,.2f}"

    @staticmethod
    def get_qss(theme_name: str) -> str:
        """Loads and returns the content of the QSS stylesheet for the given theme."""
        assets_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "views", "assets")
        theme_path = os.path.join(assets_dir, f"{theme_name}_theme.qss")
        if not os.path.exists(theme_path):
            return ""
        try:
            with open(theme_path, "r") as f:
                return f.read()
        except Exception:
            return ""
