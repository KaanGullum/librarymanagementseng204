from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QPushButton, QMessageBox, QApplication
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QIcon

from database import SessionLocal
from models import User
from auth import verify_password


class LoginWindow(QWidget):
    # Emits the User object upon successful login
    login_successful = Signal(object)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Library Management System - Login")
        self.setFixedSize(400, 300)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(20)

        # Title
        title_label = QLabel("Library System Login")
        title_font = QFont("Arial", 16, QFont.Bold)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        # Username
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Username")
        self.username_input.setMinimumHeight(35)
        layout.addWidget(self.username_input)

        # Password
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setMinimumHeight(35)
        layout.addWidget(self.password_input)

        # Error Label
        self.error_label = QLabel("")
        self.error_label.setStyleSheet("color: red;")
        self.error_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.error_label)

        # Login button
        self.login_btn = QPushButton("Login")
        self.login_btn.setMinimumHeight(40)
        self.login_btn.setCursor(Qt.PointingHandCursor)
        self.login_btn.setStyleSheet("""
            QPushButton {
                background-color: #0078D7;
                color: white;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #005A9E;
            }
        """)
        self.login_btn.clicked.connect(self.attempt_login)
        layout.addWidget(self.login_btn)

        self.setLayout(layout)

        # Handle Enter key
        self.username_input.returnPressed.connect(self.attempt_login)
        self.password_input.returnPressed.connect(self.attempt_login)

    def attempt_login(self):
        username = self.username_input.text().strip()
        password = self.password_input.text()

        if not username or not password:
            self.show_error("Please enter both username and password.")
            return

        db = SessionLocal()
        try:
            user = db.query(User).filter(User.username == username).first()
            if user and verify_password(user.password_hash, password):
                self.error_label.setText("")
                self.login_successful.emit(user)
            else:
                self.show_error("Invalid username or password.")
        except Exception as e:
            self.show_error(f"Database error: {e}")
        finally:
            db.close()

    def show_error(self, message):
        self.error_label.setText(message)

if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    window = LoginWindow()
    window.show()
    sys.exit(app.exec())
