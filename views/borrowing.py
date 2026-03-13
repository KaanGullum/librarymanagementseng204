from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QComboBox, QMessageBox, QDateEdit, QFormLayout
)
from PySide6.QtCore import Qt, QDate
from datetime import datetime, timedelta

from database import SessionLocal
from models import Book, Member, BorrowingRecord, BookStatusEnum, BorrowStatusEnum

class BorrowBookDialog(QDialog):
    def __init__(self, member_id=None, parent=None):
        super().__init__(parent)
        self.member_id = member_id
        self.setWindowTitle("Issue Book")
        self.setFixedSize(400, 250)
        self.setStyleSheet("""
            QDialog {
                background-color: white;
            }
            QLabel, QComboBox, QDateEdit {
                color: #333;
                font-family: 'Segoe UI', sans-serif;
                font-size: 13px;
            }
            QComboBox, QDateEdit {
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

        # Member Selection (if not provided)
        self.member_combo = QComboBox()
        self.load_members()
        if self.member_id:
            # Set the current index to the member and disable
            index = self.member_combo.findData(self.member_id)
            if index >= 0:
                self.member_combo.setCurrentIndex(index)
            self.member_combo.setEnabled(False)

        # Book Selection
        self.book_combo = QComboBox()
        self.load_available_books()

        # Due Date
        self.due_date_input = QDateEdit()
        # Default due date is 14 days from today
        self.due_date_input.setDate(QDate.currentDate().addDays(14))
        self.due_date_input.setCalendarPopup(True)

        form_layout.addRow("Member:", self.member_combo)
        form_layout.addRow("Book:", self.book_combo)
        form_layout.addRow("Due Date:", self.due_date_input)

        layout.addLayout(form_layout)

        btn_layout = QHBoxLayout()
        self.issue_btn = QPushButton("Issue Book")
        self.issue_btn.clicked.connect(self.issue_book)
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)

        btn_layout.addWidget(self.issue_btn)
        btn_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(btn_layout)

    def load_members(self):
        db = SessionLocal()
        try:
            members = db.query(Member).all()
            for member in members:
                self.member_combo.addItem(f"{member.first_name} {member.last_name}", userData=member.id)
        finally:
            db.close()

    def load_available_books(self):
        db = SessionLocal()
        try:
            books = db.query(Book).filter(Book.status == BookStatusEnum.AVAILABLE, Book.stock > 0).all()
            for book in books:
                self.book_combo.addItem(f"{book.title} ({book.isbn})", userData=book.id)
        finally:
            db.close()

    def issue_book(self):
        selected_member_id = self.member_combo.currentData()
        selected_book_id = self.book_combo.currentData()
        due_date_qdate = self.due_date_input.date()

        if not selected_member_id or not selected_book_id:
            QMessageBox.warning(self, "Validation Error", "Please select both a member and an available book.")
            return

        db = SessionLocal()
        try:
            book = db.query(Book).filter(Book.id == selected_book_id).first()
            if not book or book.stock <= 0 or book.status != BookStatusEnum.AVAILABLE:
                QMessageBox.warning(self, "Error", "Selected book is no longer available.")
                self.load_available_books() # Refresh
                return

            # Decrease stock and update status
            book.stock -= 1
            if book.stock == 0:
                book.status = BookStatusEnum.BORROWED
                
            due_date = datetime(due_date_qdate.year(), due_date_qdate.month(), due_date_qdate.day())

            new_record = BorrowingRecord(
                book_id=selected_book_id,
                member_id=selected_member_id,
                due_date=due_date,
                status=BorrowStatusEnum.ACTIVE
            )
            
            db.add(new_record)
            db.commit()
            
            QMessageBox.information(self, "Success", "Book successfully issued.")
            self.accept()
        except Exception as e:
            db.rollback()
            QMessageBox.critical(self, "Error", f"An error occurred: {str(e)}")
        finally:
            db.close()
