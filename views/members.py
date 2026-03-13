from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QLineEdit, QTableWidget, QTableWidgetItem,
    QHeaderView, QDialog, QFormLayout, QMessageBox, QSplitter
)
from PySide6.QtCore import Qt
from sqlalchemy.exc import IntegrityError
from datetime import datetime

from database import SessionLocal
from models import Member, BorrowingRecord, BorrowStatusEnum, BookStatusEnum, Book
from views.borrowing import BorrowBookDialog

class MemberDialog(QDialog):
    def __init__(self, member=None, parent=None):
        super().__init__(parent)
        self.member = member
        self.setWindowTitle("Edit Member" if member else "Add New Member")
        self.setFixedSize(400, 250)
        self.setStyleSheet("""
            QDialog {
                background-color: white;
            }
            QLabel, QLineEdit {
                color: #333;
                font-family: 'Segoe UI', sans-serif;
                font-size: 13px;
            }
            QLineEdit {
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

        layout = QVBoxLayout(self)

        form_layout = QFormLayout()
        
        self.first_name_input = QLineEdit()
        self.last_name_input = QLineEdit()
        self.email_input = QLineEdit()
        self.phone_input = QLineEdit()

        if self.member:
            self.first_name_input.setText(self.member.first_name)
            self.last_name_input.setText(self.member.last_name)
            self.email_input.setText(self.member.email)
            self.phone_input.setText(self.member.phone)

        form_layout.addRow("First Name:", self.first_name_input)
        form_layout.addRow("Last Name:", self.last_name_input)
        form_layout.addRow("Email:", self.email_input)
        form_layout.addRow("Phone:", self.phone_input)

        layout.addLayout(form_layout)

        btn_layout = QHBoxLayout()
        self.save_btn = QPushButton("Save")
        self.save_btn.clicked.connect(self.save_member)
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)

        btn_layout.addWidget(self.save_btn)
        btn_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(btn_layout)

    def save_member(self):
        first_name = self.first_name_input.text().strip()
        last_name = self.last_name_input.text().strip()
        email = self.email_input.text().strip()
        
        if not first_name or not last_name:
            QMessageBox.warning(self, "Validation Error", "First and Last Name are required.")
            return

        db = SessionLocal()
        try:
            if self.member: # Edit mode
                member = db.query(Member).filter(Member.id == self.member.id).first()
                if not member:
                    QMessageBox.warning(self, "Error", "Member not found.")
                    return
                member.first_name = first_name
                member.last_name = last_name
                member.email = email
                member.phone = self.phone_input.text().strip()
            else: # Create mode
                new_member = Member(
                    first_name=first_name,
                    last_name=last_name,
                    email=email,
                    phone=self.phone_input.text().strip(),
                    membership_date=datetime.utcnow()
                )
                db.add(new_member)
            
            db.commit()
            self.accept()
        except IntegrityError:
            db.rollback()
            QMessageBox.warning(self, "Database Error", "A member with this email already exists.")
        except Exception as e:
            db.rollback()
            QMessageBox.critical(self, "Error", f"An error occurred: {str(e)}")
        finally:
            db.close()

class MemberManagementWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.load_members()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        # Top Bar
        top_bar = QHBoxLayout()
        
        title_label = QLabel("Member Management")
        font = title_label.font()
        font.setPointSize(24)
        font.setBold(True)
        title_label.setFont(font)
        title_label.setStyleSheet("color: #2c3545;")
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by Name, Email, or Phone...")
        self.search_input.setStyleSheet("padding: 8px; border: 1px solid #ced4da; border-radius: 3px; background-color: white;")
        self.search_input.textChanged.connect(self.load_members)
        
        self.btn_clear = QPushButton("Clear")
        self.btn_clear.setStyleSheet("background-color: #3b4b61; color: white; padding: 8px 20px; border-radius: 3px; font-weight: bold;")
        self.btn_clear.clicked.connect(lambda: self.search_input.clear())

        add_btn = QPushButton("Add Member")
        add_btn.setStyleSheet("background-color: #3b4b61; color: white; padding: 8px 15px; border-radius: 3px; font-weight: bold;")
        add_btn.setCursor(Qt.PointingHandCursor)
        add_btn.clicked.connect(self.show_add_member_dialog)

        top_bar.addWidget(title_label)
        top_bar.addStretch()
        top_bar.addWidget(add_btn)

        layout.addLayout(top_bar)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["ID", "First Name", "Last Name", "Email", "Phone", "Member Since"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setAlternatingRowColors(True)
        
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: white;
                alternate-background-color: #f8f9fa;
                border: 1px solid #ced4da;
                border-radius: 8px;
            }
            QHeaderView::section {
                background-color: #2c3545;
                color: white;
                padding: 8px;
                font-weight: bold;
                border: none;
            }
            QTableWidget::item {
                padding: 5px;
            }
            QTableWidget::item:selected {
                background-color: #0078D7;
                color: white;
            }
        """)
        
        self.table.doubleClicked.connect(self.edit_selected_member)
        self.table.itemSelectionChanged.connect(self.load_member_history)

        # Splitter to divide Top (Members) and Bottom (History)
        splitter = QSplitter(Qt.Vertical)
        
        # Members Top Widget
        top_widget = QWidget()
        # Bottom Search Bar (below top_widget table)
        search_layout = QHBoxLayout()
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.btn_clear)
        
        top_layout = QVBoxLayout(top_widget)
        top_layout.setContentsMargins(0,0,0,0)
        top_layout.addWidget(self.table)
        top_layout.addLayout(search_layout)

        # Bottom Widget for Borrowing History
        bottom_widget = QWidget()
        bottom_layout = QVBoxLayout(bottom_widget)
        bottom_layout.setContentsMargins(0,0,0,0)

        history_header = QHBoxLayout()
        history_title = QLabel("Borrowing History")
        font = history_title.font()
        font.setBold(True)
        font.setPointSize(16)
        history_title.setFont(font)

        self.issue_btn = QPushButton("Issue Book")
        self.issue_btn.setFixedSize(120, 35)
        self.issue_btn.setStyleSheet("""
            QPushButton {
                background-color: #17a2b8;
                color: white;
                font-weight: bold;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #138496;
            }
        """)
        self.issue_btn.clicked.connect(self.issue_book_to_selected)

        self.return_btn = QPushButton("Return Book")
        self.return_btn.setFixedSize(120, 35)
        self.return_btn.setStyleSheet("""
            QPushButton {
                background-color: #ffc107;
                color: #212529;
                font-weight: bold;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #e0a800;
            }
        """)
        self.return_btn.clicked.connect(self.return_selected_book)
        
        # Disable buttons until member/book is selected
        self.issue_btn.setEnabled(False)
        self.return_btn.setEnabled(False)

        history_header.addWidget(history_title)
        history_header.addStretch()
        history_header.addWidget(self.issue_btn)
        history_header.addWidget(self.return_btn)

        self.history_table = QTableWidget()
        self.history_table.setColumnCount(6)
        self.history_table.setHorizontalHeaderLabels(["Record ID", "Book", "Borrowed", "Due Date", "Returned", "Status"])
        self.history_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.history_table.verticalHeader().setVisible(False)
        self.history_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.history_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.history_table.setSelectionMode(QTableWidget.SingleSelection)
        self.history_table.setAlternatingRowColors(True)
        self.history_table.setStyleSheet(self.table.styleSheet()) # Reuse style
        
        self.history_table.itemSelectionChanged.connect(self.check_return_button_state)

        bottom_layout.addLayout(history_header)
        bottom_layout.addWidget(self.history_table)

        splitter.addWidget(top_widget)
        splitter.addWidget(bottom_widget)
        splitter.setSizes([400, 200])

        layout.addWidget(splitter)

    def load_members(self):
        search_term = self.search_input.text().strip()
        db = SessionLocal()
        
        try:
            query = db.query(Member)
            
            if search_term:
                terms = search_term.split()
                for term in terms:
                    pattern = f"%{term}%"
                    query = query.filter(
                        (Member.first_name.ilike(pattern)) |
                        (Member.last_name.ilike(pattern)) |
                        (Member.email.ilike(pattern)) |
                        (Member.phone.ilike(pattern))
                    )
                
            members = query.all()
            
            self.table.setRowCount(0)
            for row, member in enumerate(members):
                self.table.insertRow(row)
                self.table.setItem(row, 0, QTableWidgetItem(str(member.id)))
                self.table.setItem(row, 1, QTableWidgetItem(member.first_name))
                self.table.setItem(row, 2, QTableWidgetItem(member.last_name))
                self.table.setItem(row, 3, QTableWidgetItem(member.email or ""))
                self.table.setItem(row, 4, QTableWidgetItem(member.phone or ""))
                date_str = member.membership_date.strftime("%Y-%m-%d") if member.membership_date else ""
                self.table.setItem(row, 5, QTableWidgetItem(date_str))
                
        finally:
            db.close()

    def show_add_member_dialog(self):
        dialog = MemberDialog(parent=self)
        if dialog.exec() == QDialog.Accepted:
            self.load_members()

    def edit_selected_member(self):
        selected_rows = self.table.selectedItems()
        if not selected_rows:
            return
            
        member_id = int(self.table.item(selected_rows[0].row(), 0).text())
        
        db = SessionLocal()
        try:
            member = db.query(Member).filter(Member.id == member_id).first()
            if member:
                dialog = MemberDialog(member, parent=self)
                if dialog.exec() == QDialog.Accepted:
                    self.load_members()
        finally:
            db.close()

    def load_member_history(self):
        selected_rows = self.table.selectedItems()
        self.issue_btn.setEnabled(len(selected_rows) > 0)
        self.return_btn.setEnabled(False) # Reset return btn state
        self.history_table.setRowCount(0)

        if not selected_rows:
            return

        member_id = int(self.table.item(selected_rows[0].row(), 0).text())
        
        db = SessionLocal()
        try:
            records = db.query(BorrowingRecord).filter(BorrowingRecord.member_id == member_id).order_by(BorrowingRecord.borrow_date.desc()).all()
            
            for row, record in enumerate(records):
                self.history_table.insertRow(row)
                self.history_table.setItem(row, 0, QTableWidgetItem(str(record.id)))
                book_title = record.book.title if record.book else "Unknown Book"
                self.history_table.setItem(row, 1, QTableWidgetItem(book_title))
                self.history_table.setItem(row, 2, QTableWidgetItem(record.borrow_date.strftime("%Y-%m-%d")))
                self.history_table.setItem(row, 3, QTableWidgetItem(record.due_date.strftime("%Y-%m-%d")))
                
                return_date_str = record.return_date.strftime("%Y-%m-%d") if record.return_date else "-"
                self.history_table.setItem(row, 4, QTableWidgetItem(return_date_str))
                
                status_item = QTableWidgetItem(record.status.value)
                if record.status == BorrowStatusEnum.ACTIVE:
                    status_item.setForeground(Qt.darkBlue)
                elif record.status == BorrowStatusEnum.RETURNED:
                    status_item.setForeground(Qt.darkGreen)
                elif record.status == BorrowStatusEnum.OVERDUE:
                    status_item.setForeground(Qt.darkRed)
                self.history_table.setItem(row, 5, status_item)
                
        finally:
            db.close()

    def check_return_button_state(self):
        selected_history = self.history_table.selectedItems()
        if not selected_history:
            self.return_btn.setEnabled(False)
            return
            
        status = self.history_table.item(selected_history[0].row(), 5).text()
        self.return_btn.setEnabled(status != BorrowStatusEnum.RETURNED.value)

    def issue_book_to_selected(self):
        selected_rows = self.table.selectedItems()
        if not selected_rows:
            return
        
        member_id = int(self.table.item(selected_rows[0].row(), 0).text())
        dialog = BorrowBookDialog(member_id=member_id, parent=self)
        if dialog.exec() == QDialog.Accepted:
            self.load_member_history() # Refresh history
            # Ideally trigger books refresh if we were on books tab, but we'll load lazily

    def return_selected_book(self):
        selected_history = self.history_table.selectedItems()
        if not selected_history:
            return
            
        record_id = int(self.history_table.item(selected_history[0].row(), 0).text())
        
        db = SessionLocal()
        try:
            record = db.query(BorrowingRecord).filter(BorrowingRecord.id == record_id).first()
            if not record or record.status == BorrowStatusEnum.RETURNED:
                return

            record.status = BorrowStatusEnum.RETURNED
            record.return_date = datetime.utcnow()
            
            # Increase book stock and update book status
            if record.book:
                record.book.stock += 1
                record.book.status = BookStatusEnum.AVAILABLE
                
            db.commit()
            QMessageBox.information(self, "Success", f"Book '{record.book.title}' returned successfully.")
            self.load_member_history()
            
        except Exception as e:
            db.rollback()
            QMessageBox.critical(self, "Error", f"Failed to return book: {str(e)}")
        finally:
            db.close()
