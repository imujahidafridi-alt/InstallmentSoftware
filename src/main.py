import sys
import os
from PyQt6.QtWidgets import QApplication, QMessageBox
from dotenv import load_dotenv

# Set python path to allow imports from workspace root directory
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config import ConfigManager
from src.views.login_view import LoginView
from src.views.main_window import MainWindow

def main():
    # Load environment variables (.env file)
    load_dotenv()

    # Verify that Supabase configuration is present
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    
    app = QApplication(sys.argv)

    # Set global application window icon
    from PyQt6.QtGui import QIcon
    icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "views", "assets", "app_icon.png")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    if not supabase_url or not supabase_key:
        QMessageBox.critical(
            None,
            "Configuration Missing",
            "Supabase credentials (SUPABASE_URL and SUPABASE_KEY) are not set in the environment.\n"
            "Please create a '.env' file in the root directory before running the application."
        )
        # We still start the app so they can see the error window, but we shouldn't crash
        # returning here exits
        return

    # Load and apply QSS theme stylesheet
    config = ConfigManager.load_config()
    theme = config.get("theme", "light")
    qss = ConfigManager.get_qss(theme)
    if qss:
        app.setStyleSheet(qss)

    # Launch login view
    login = LoginView()
    main_window = None

    def on_login_success():
        nonlocal main_window
        main_window = MainWindow()
        main_window.show()
        login.close()

    login.login_success.connect(on_login_success)
    login.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
