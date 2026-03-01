from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QStackedWidget, QLabel, QFrame, QDialog
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon

from models import User, RoleEnum
from views.user_management import UserManagementWidget

class AccountInformationDialog(QDialog):
    def __init__(self, user: User, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Account Information")
        self.setFixedSize(350, 250)
        self.user = user
        self.logout_clicked = False
        
        self.setStyleSheet("""
            QDialog {
                background-color: #f4f6f9;
            }
            QLabel {
                color: white;
                font-family: 'Segoe UI', sans-serif;
                font-size: 14px;
                font-weight: bold;
            }
            QFrame#InfoBox {
                background-color: #465669;
                border: 1px solid #ced4da;
                border-radius: 6px;
                padding: 10px;
            }
            QPushButton#LogoutBtn {
                background-color: #465669;
                color: white;
                border-radius: 6px;
                padding: 10px;
                font-size: 14px;
                font-weight: bold;
                margin-top: 10px;
            }
            QPushButton#LogoutBtn:hover {
                background-color: #3b4b61;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        # Info Box Frame
        info_frame = QFrame()
        info_frame.setObjectName("InfoBox")
        info_layout = QVBoxLayout(info_frame)
        
        # Username Row
        user_row = QHBoxLayout()
        user_lbl = QLabel("Username:")
        user_val = QLabel(self.user.username)
        user_val.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        user_row.addWidget(user_lbl)
        user_row.addWidget(user_val)
        
        # Line separator can be simulated with a styled frame
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        line.setStyleSheet("background-color: #ced4da; max-height: 1px;")
        
        # Role Row
        role_row = QHBoxLayout()
        role_lbl = QLabel("Role:")
        role_val = QLabel(self.user.role.value)
        role_val.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        role_row.addWidget(role_lbl)
        role_row.addWidget(role_val)
        
        info_layout.addLayout(user_row)
        info_layout.addWidget(line)
        info_layout.addLayout(role_row)
        
        layout.addWidget(info_frame)

        # Logout Button
        logout_btn = QPushButton("Log out")
        logout_btn.setObjectName("LogoutBtn")
        logout_btn.setCursor(Qt.PointingHandCursor)
        logout_btn.clicked.connect(self.on_logout)
        
        layout.addWidget(logout_btn)

    def on_logout(self):
        self.logout_clicked = True
        self.accept()

class SidebarButton(QPushButton):
    def __init__(self, text):
        super().__init__(text)
        self.setMinimumHeight(45)
        self.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                text-align: left;
                padding-left: 20px;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 14px;
                color: white;
            }
            QPushButton:hover {
                background-color: #3b4b61;
            }
            QPushButton:checked {
                background-color: white;
                color: #2c3545;
                font-weight: bold;
                border-left: 4px solid #0078D7;
            }
        """)
        self.setCheckable(True)
        self.setCursor(Qt.PointingHandCursor)

class PlaceholderWidget(QWidget):
    def __init__(self, title):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        lbl = QLabel(f"{title} (Coming Soon)")
        font = lbl.font()
        font.setPointSize(24)
        lbl.setFont(font)
        lbl.setStyleSheet("color: #3b4b61;")
        layout.addWidget(lbl)

class MainWindow(QMainWindow):
    logout_requested = Signal()

    def __init__(self, current_user: User):
        super().__init__()
        self.current_user = current_user
        self.setWindowTitle("Library Management System - Dashboard")
        self.setMinimumSize(1000, 700)
        
        self.setup_ui()

    def setup_ui(self):
        # Central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Sidebar
        self.sidebar = QFrame()
        self.sidebar.setFixedWidth(220)
        self.sidebar.setStyleSheet("background-color: #2c3545;")
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(0, 20, 0, 20)
        sidebar_layout.setSpacing(0)

        # Sidebar Header (Clickable for Account Info)
        self.btn_account_info = QPushButton("Library\nManagement\nSystem")
        self.btn_account_info.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                color: white;
                text-align: left;
                padding-left: 20px;
                padding-bottom: 20px;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                color: #e2c044;
            }
        """)
        self.btn_account_info.setCursor(Qt.PointingHandCursor)
        self.btn_account_info.clicked.connect(self.show_account_info)
        sidebar_layout.addWidget(self.btn_account_info)

        # Sidebar Buttons
        self.btn_dashboard = SidebarButton("  Dashboard")
        self.btn_books = SidebarButton("  Books")
        self.btn_reports = SidebarButton("  Reports")
        self.btn_users = SidebarButton("  Users")
        
        self.btn_dashboard.clicked.connect(lambda: self.switch_view(0))
        self.btn_books.clicked.connect(lambda: self.switch_view(1))
        self.btn_reports.clicked.connect(lambda: self.switch_view(2))
        self.btn_users.clicked.connect(lambda: self.switch_view(3))

        sidebar_layout.addWidget(self.btn_dashboard)
        sidebar_layout.addWidget(self.btn_books)
        sidebar_layout.addWidget(self.btn_reports)

        if self.current_user.role == RoleEnum.ADMIN:
            sidebar_layout.addWidget(self.btn_users)

        sidebar_layout.addStretch()

        # Logout Button
        self.btn_logout = SidebarButton("  Exit")
        self.btn_logout.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                text-align: left;
                padding-left: 20px;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 14px;
                color: #e2c044;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #3b4b61;
            }
        """)
        self.btn_logout.setCheckable(False)
        self.btn_logout.clicked.connect(self.logout_requested.emit)
        sidebar_layout.addWidget(self.btn_logout)

        main_layout.addWidget(self.sidebar)

        # Content Area (Stacked Widget)
        self.content_area = QStackedWidget()
        self.content_area.setStyleSheet("background-color: #f4f6f9;")
        main_layout.addWidget(self.content_area)

        # Views
        self.dashboard_view = self.create_dashboard_view()
        self.books_view = PlaceholderWidget("Books Inventory")
        self.reports_view = PlaceholderWidget("System Reports")
        
        self.content_area.addWidget(self.dashboard_view)
        self.content_area.addWidget(self.books_view)
        self.content_area.addWidget(self.reports_view)
        
        if self.current_user.role == RoleEnum.ADMIN:
            self.user_mgt_view = UserManagementWidget(self.current_user)
            self.content_area.addWidget(self.user_mgt_view)

        # Default View
        if self.current_user.role == RoleEnum.ADMIN:
            self.switch_view(3) # Show Users by default like the image
        else:
            self.switch_view(0)

    def create_dashboard_view(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        label = QLabel("Welcome to the Library Management Dashboard!")
        label.setAlignment(Qt.AlignCenter)
        font = label.font()
        font.setPointSize(20)
        label.setFont(font)
        label.setStyleSheet("color: #3b4b61;")
        layout.addWidget(label)
        return widget

    def switch_view(self, index):
        self.content_area.setCurrentIndex(index)
        self.btn_dashboard.setChecked(index == 0)
        self.btn_books.setChecked(index == 1)
        self.btn_reports.setChecked(index == 2)
        
        if self.current_user.role == RoleEnum.ADMIN:
            self.btn_users.setChecked(index == 3)

    def show_account_info(self):
        dialog = AccountInformationDialog(self.current_user, self)
        if dialog.exec() == QDialog.Accepted and dialog.logout_clicked:
            self.logout_requested.emit()
