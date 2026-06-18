import os
import json

CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")

class ConfigManager:
    @staticmethod
    def load_config() -> dict:
        if not os.path.exists(CONFIG_FILE):
            default_config = {
                "theme": "light",
                "shop_name": "Asif Mobile Center",
                "shop_address": "Main Market, Commercial Area",
                "shop_contact": "Ph: 0300-1234567"
            }
            ConfigManager.save_config(default_config)
            return default_config
        try:
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return {}

    @staticmethod
    def save_config(config_data: dict):
        with open(CONFIG_FILE, "w") as f:
            json.dump(config_data, f, indent=4)

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
