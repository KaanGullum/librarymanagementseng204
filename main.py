import sys
from PySide6.QtWidgets import QApplication

from database import init_db
from login_window import LoginWindow
from main_window import MainWindow
from theme import apply_light_theme, configure_qt_for_light_mode

class AppController:
    def __init__(self):
        configure_qt_for_light_mode()
        self.app = QApplication(sys.argv)
        apply_light_theme(self.app)
        self.app.setStyleSheet("""
            QDialog, QMessageBox {
                background-color: white;
            }
            QLabel, QLineEdit, QComboBox, QPushButton {
                color: #333;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QTableWidget {
                color: #333;
            }
            QPushButton {
                background-color: #f0f0f0;
                border: 1px solid #ccc;
                border-radius: 3px;
                padding: 5px 15px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
        """)
        self.login_window = None
        self.main_window = None

    def start(self):
        self.show_login()
        sys.exit(self.app.exec())

    def show_login(self):
        if self.main_window:
            self.main_window.close()
            self.main_window = None

        self.login_window = LoginWindow()
        self.login_window.login_successful.connect(self.on_login_successful)
        self.login_window.show()

    def on_login_successful(self, user):
        self.login_window.close()
        self.login_window = None

        self.main_window = MainWindow(user)
        self.main_window.logout_requested.connect(self.show_login)
        self.main_window.show()

if __name__ == "__main__":
    init_db()
    controller = AppController()
    controller.start()
