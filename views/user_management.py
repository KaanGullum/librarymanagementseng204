from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QPushButton, QTableWidget, QTableWidgetItem,
    QMessageBox, QDialog, QLineEdit, QComboBox, QHeaderView, QAbstractItemView
)
from PySide6.QtCore import Qt
from datetime import datetime

from database import SessionLocal
from models import User, RoleEnum
from auth import hash_password

class UserFormDialog(QDialog):
    def __init__(self, parent=None, user=None):
        super().__init__(parent)
        self.setWindowTitle("Add User" if not user else "Update User")
        self.setFixedSize(300, 200)
        self.setStyleSheet("""
            QDialog {
                background-color: white;
            }
            QLabel, QLineEdit, QComboBox {
                color: #333;
                font-family: 'Segoe UI', sans-serif;
                font-size: 13px;
            }
            QLineEdit, QComboBox {
                background-color: white;
                border: 1px solid #ced4da;
                border-radius: 4px;
                padding: 4px;
            }
            QPushButton {
                background-color: #3b4b61;
                color: white;
                border-radius: 3px;
                padding: 5px 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2c3545;
            }
        """)
        self.user = user

        layout = QVBoxLayout()
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Username")
        layout.addWidget(self.username_input)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password" if not user else "New Password (leave blank to keep)")
        self.password_input.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.password_input)

        self.role_combo = QComboBox()
        self.role_combo.addItems([r.value for r in RoleEnum])
        layout.addWidget(self.role_combo)

        if self.user:
            self.username_input.setText(self.user.username)
            self.role_combo.setCurrentText(self.user.role.value)

        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

        self.setLayout(layout)

    def get_data(self):
        return {
            "username": self.username_input.text().strip(),
            "password": self.password_input.text(),
            "role": RoleEnum(self.role_combo.currentText())
        }

class SummaryCard(QFrame):
    def __init__(self, title, count="0"):
        super().__init__()
        self.setStyleSheet("background-color: #3b4b61; color: white; border-radius: 5px;")
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        
        title_label = QLabel(title)
        title_font = title_label.font()
        title_font.setFamily("Segoe UI")
        title_font.setPointSize(11)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        
        self.count_label = QLabel(count)
        count_font = self.count_label.font()
        count_font.setPointSize(14)
        count_font.setBold(False)
        self.count_label.setFont(count_font)
        self.count_label.setAlignment(Qt.AlignCenter)
        self.count_label.setStyleSheet("color: #FFD700;") # highlight count in gold

        layout.addWidget(title_label)
        layout.addWidget(self.count_label)
        self.setMinimumHeight(80)

    def set_count(self, count):
        self.count_label.setText(str(count))

class UserManagementWidget(QWidget):
    def __init__(self, current_user):
        super().__init__()
        self.current_user = current_user
        self.setStyleSheet("background-color: #f4f6f9;")
        self.setup_ui()
        self.load_users()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # --- Top Cards ---
        cards_layout = QHBoxLayout()
        self.card_total = SummaryCard("Total Users:")
        self.card_admins = SummaryCard("Admins:")
        self.card_managers = SummaryCard("Librarians:")
        self.card_cashiers = SummaryCard("Assistants:")
        
        cards_layout.addWidget(self.card_total)
        cards_layout.addWidget(self.card_admins)
        cards_layout.addWidget(self.card_managers)
        cards_layout.addWidget(self.card_cashiers)
        
        layout.addLayout(cards_layout)

        # --- Action Buttons ---
        actions_layout = QHBoxLayout()
        
        self.btn_add = QPushButton("Add")
        self.btn_update = QPushButton("Update")
        self.btn_delete = QPushButton("Delete")
        
        for btn in (self.btn_add, self.btn_update):
            btn.setStyleSheet("background-color: #3b4b61; color: white; padding: 8px 15px; border-radius: 3px; font-weight: bold;")
            btn.setCursor(Qt.PointingHandCursor)
            
        self.btn_delete.setStyleSheet("background-color: #b84334; color: white; padding: 8px 15px; border-radius: 3px; font-weight: bold;")
        self.btn_delete.setCursor(Qt.PointingHandCursor)

        self.btn_add.clicked.connect(self.add_user)
        self.btn_update.clicked.connect(self.update_user)
        self.btn_delete.clicked.connect(self.delete_user)

        actions_layout.addWidget(self.btn_add)
        actions_layout.addWidget(self.btn_update)
        actions_layout.addStretch()
        actions_layout.addWidget(self.btn_delete)
        
        if self.current_user.role != RoleEnum.ADMIN:
            self.btn_add.hide()
            self.btn_update.hide()
            self.btn_delete.hide()

        layout.addLayout(actions_layout)

        # --- Table ---
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["ID", "Username", "Role", "Created at"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: white;
                gridline-color: #e0e0e0;
                border: 1px solid #ced4da;
            }
            QHeaderView::section {
                background-color: #ffffff;
                padding: 4px;
                border: 1px solid #e0e0e0;
                font-weight: bold;
            }
            QTableWidget::item:selected {
                background-color: #dbe4f0;
                color: black;
            }
        """)
        layout.addWidget(self.table)

        # --- Bottom Search Bar ---
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Enter a Username to Search...")
        self.search_input.setStyleSheet("padding: 8px; border: 1px solid #ced4da; border-radius: 3px; background-color: white;")
        self.search_input.textChanged.connect(self.filter_users)
        
        self.btn_clear = QPushButton("Clear")
        self.btn_clear.setStyleSheet("background-color: #3b4b61; color: white; padding: 8px 20px; border-radius: 3px; font-weight: bold;")
        self.btn_clear.clicked.connect(lambda: self.search_input.clear())

        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.btn_clear)
        layout.addLayout(search_layout)

    def load_users(self, filter_text=""):
        self.table.setRowCount(0)
        db = SessionLocal()
        try:
            query = db.query(User)
            if filter_text:
                query = query.filter(User.username.ilike(f"%{filter_text}%"))
            users = query.all()
            
            total, admins, librarians, assistants = 0, 0, 0, 0
            
            for row, user in enumerate(users):
                self.table.insertRow(row)
                self.table.setItem(row, 0, QTableWidgetItem(str(user.id)))
                self.table.setItem(row, 1, QTableWidgetItem(user.username))
                self.table.setItem(row, 2, QTableWidgetItem(user.role.value))
                
                # handle date
                created_str = user.created_at.strftime("%Y-%m-%d") if user.created_at else "N/A"
                self.table.setItem(row, 3, QTableWidgetItem(created_str))
                
                self.table.item(row, 0).setData(Qt.UserRole, user.id)

                total += 1
                if user.role == RoleEnum.ADMIN: admins += 1
                elif user.role == RoleEnum.LIBRARIAN: librarians += 1
                elif user.role == RoleEnum.ASSISTANT: assistants += 1
            
            # Update summary cards
            self.card_total.set_count(total)
            self.card_admins.set_count(admins)
            self.card_managers.set_count(librarians)
            self.card_cashiers.set_count(assistants)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load users: {e}")
        finally:
            db.close()

    def filter_users(self, text):
        self.load_users(text)

    def get_selected_user_id(self):
        selected = self.table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "Selection Required", "Please select a user from the table.")
            return None
        return self.table.item(selected[0].row(), 0).data(Qt.UserRole)

    def add_user(self):
        dialog = UserFormDialog(self)
        if dialog.exec() == QDialog.Accepted:
            data = dialog.get_data()
            if not data["username"] or not data["password"]:
                QMessageBox.warning(self, "Error", "Username and password are required.")
                return

            db = SessionLocal()
            try:
                existing = db.query(User).filter(User.username == data["username"]).first()
                if existing:
                    QMessageBox.warning(self, "Error", "Username already exists.")
                    return
                
                hashed_pw = hash_password(data["password"])
                new_user = User(
                    username=data["username"],
                    password_hash=hashed_pw,
                    role=data["role"]
                )
                db.add(new_user)
                db.commit()
                self.load_users(self.search_input.text())
            except Exception as e:
                db.rollback()
                QMessageBox.critical(self, "Error", f"Failed to add user: {e}")
            finally:
                db.close()

    def update_user(self):
        user_id = self.get_selected_user_id()
        if not user_id: return
        
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user: return
            
            dialog = UserFormDialog(self, user=user)
            if dialog.exec() == QDialog.Accepted:
                data = dialog.get_data()
                if not data["username"]:
                    QMessageBox.warning(self, "Error", "Username is required.")
                    return

                # Check if username changed and exists
                if data["username"] != user.username:
                    existing = db.query(User).filter(User.username == data["username"]).first()
                    if existing:
                        QMessageBox.warning(self, "Error", "Username already exists.")
                        return

                user.username = data["username"]
                user.role = data["role"]
                if data["password"]:
                    user.password_hash = hash_password(data["password"])
                
                db.commit()
                self.load_users(self.search_input.text())
        except Exception as e:
            db.rollback()
            QMessageBox.critical(self, "Error", f"Failed to update user: {e}")
        finally:
            db.close()

    def delete_user(self):
        user_id = self.get_selected_user_id()
        if not user_id: return
        
        if user_id == self.current_user.id:
            QMessageBox.warning(self, "Error", "You cannot delete yourself.")
            return

        confirm = QMessageBox.question(self, "Confirm", "Delete selected user?", QMessageBox.Yes | QMessageBox.No)
        if confirm == QMessageBox.Yes:
            db = SessionLocal()
            try:
                user = db.query(User).filter(User.id == user_id).first()
                if user:
                    db.delete(user)
                    db.commit()
                    self.load_users(self.search_input.text())
            except Exception as e:
                db.rollback()
                QMessageBox.critical(self, "Error", f"Failed to delete user: {e}")
            finally:
                db.close()
