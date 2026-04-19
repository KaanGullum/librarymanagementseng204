import re

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QLineEdit, QTableWidget, QTableWidgetItem,
    QHeaderView, QDialog, QFormLayout, QComboBox, QMessageBox,
    QSpinBox
)
from PySide6.QtCore import Qt
from sqlalchemy.exc import IntegrityError

from database import SessionLocal
from models import Book, BookStatusEnum
from theme import build_spinbox_stylesheet


def normalize_isbn(isbn: str) -> str:
    return re.sub(r"[\s-]", "", isbn or "").upper()


def sanitize_isbn_for_storage(isbn: str) -> str:
    return re.sub(r"\s+", "", isbn or "").upper()


def is_valid_isbn(isbn: str) -> bool:
    normalized = normalize_isbn(isbn)

    if len(normalized) == 10:
        if not normalized[:-1].isdigit() or not (normalized[-1].isdigit() or normalized[-1] == "X"):
            return False

        total = 0
        for index, char in enumerate(normalized):
            value = 10 if char == "X" else int(char)
            total += (10 - index) * value
        return total % 11 == 0

    if len(normalized) == 13:
        if not normalized.isdigit():
            return False

        total = 0
        for index, char in enumerate(normalized[:12]):
            multiplier = 1 if index % 2 == 0 else 3
            total += int(char) * multiplier
        check_digit = (10 - (total % 10)) % 10
        return check_digit == int(normalized[-1])

    return False


class BookDialog(QDialog):
    def __init__(self, book=None, parent=None):
        super().__init__(parent)
        self.book = book
        self.setWindowTitle("Edit Book" if book else "Add New Book")
        self.setFixedSize(400, 350)
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
            QComboBox QAbstractItemView {
                background-color: white;
                color: #333;
                selection-background-color: #0078D7;
                selection-color: white;
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
        """ + build_spinbox_stylesheet())

        layout = QVBoxLayout(self)

        form_layout = QFormLayout()
        
        self.isbn_input = QLineEdit()
        self.isbn_input.setMaximumWidth(140)
        self.title_input = QLineEdit()
        self.author_input = QLineEdit()
        self.category_input = QLineEdit()
        
        self.stock_input = QSpinBox()
        self.stock_input.setRange(0, 1000)
        self.stock_input.setValue(1)

        self.status_combo = QComboBox()
        self.status_combo.addItems([e.value for e in BookStatusEnum])

        if self.book:
            self.isbn_input.setText(self.book.isbn)
            self.title_input.setText(self.book.title)
            self.author_input.setText(self.book.author)
            self.category_input.setText(self.book.category or "")
            self.stock_input.setValue(self.book.stock)
            self.status_combo.setCurrentText(self.book.status.value)

        isbn_row = QWidget()
        isbn_row_layout = QHBoxLayout(isbn_row)
        isbn_row_layout.setContentsMargins(0, 0, 0, 0)
        isbn_row_layout.setSpacing(8)

        isbn_format_label = QLabel("978-975-07-0056-9")
        isbn_format_label.setStyleSheet("color: #64748b; font-size: 12px;")

        isbn_row_layout.addWidget(self.isbn_input)
        isbn_row_layout.addWidget(isbn_format_label)
        isbn_row_layout.addStretch()

        form_layout.addRow("ISBN:", isbn_row)
        form_layout.addRow("Title:", self.title_input)
        form_layout.addRow("Author:", self.author_input)
        form_layout.addRow("Category:", self.category_input)
        form_layout.addRow("Stock:", self.stock_input)
        form_layout.addRow("Status:", self.status_combo)

        layout.addLayout(form_layout)

        btn_layout = QHBoxLayout()
        self.save_btn = QPushButton("Save")
        self.save_btn.clicked.connect(self.save_book)
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)

        btn_layout.addWidget(self.save_btn)
        btn_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(btn_layout)

    def save_book(self):
        isbn = sanitize_isbn_for_storage(self.isbn_input.text().strip())
        title = self.title_input.text().strip()
        author = self.author_input.text().strip()
        category = self.category_input.text().strip() or None
        
        if not isbn or not title or not author:
            QMessageBox.warning(self, "Validation Error", "ISBN, Title, and Author are required fields.")
            return
            
        if not is_valid_isbn(isbn):
            QMessageBox.warning(
                self,
                "Validation Error",
                "Please enter a valid ISBN-10 or ISBN-13. You may use digits with optional hyphens, for example 978-975-07-0056-9."
            )
            return

        db = SessionLocal()
        try:
            duplicate_book = next(
                (
                    existing_book
                    for existing_book in db.query(Book).all()
                    if normalize_isbn(existing_book.isbn) == normalize_isbn(isbn)
                    and (not self.book or existing_book.id != self.book.id)
                ),
                None,
            )
            if duplicate_book:
                QMessageBox.warning(self, "Database Error", "A book with this ISBN already exists.")
                return

            if self.book: # Edit mode
                book = db.query(Book).filter(Book.id == self.book.id).first()
                if not book:
                    QMessageBox.warning(self, "Error", "Book not found.")
                    return
                book.isbn = isbn
                book.title = title
                book.author = author
                book.category = category
                book.stock = self.stock_input.value()
                book.status = BookStatusEnum(self.status_combo.currentText())
            else: # Create mode
                new_book = Book(
                    isbn=isbn,
                    title=title,
                    author=author,
                    category=category,
                    stock=self.stock_input.value(),
                    status=BookStatusEnum(self.status_combo.currentText())
                )
                db.add(new_book)
            
            db.commit()
            self.accept()
        except IntegrityError:
            db.rollback()
            QMessageBox.warning(self, "Database Error", "A book with this ISBN already exists.")
        except Exception as e:
            db.rollback()
            QMessageBox.critical(self, "Error", f"An error occurred: {str(e)}")
        finally:
            db.close()

class BookInventoryWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.load_books()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        # Top Bar
        top_bar = QHBoxLayout()
        
        title_label = QLabel("Book Inventory")
        font = title_label.font()
        font.setPointSize(24)
        font.setBold(True)
        title_label.setFont(font)
        title_label.setStyleSheet("color: #2c3545;")
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by Title, Author, or ISBN...")
        self.search_input.setStyleSheet("padding: 8px; border: 1px solid #ced4da; border-radius: 3px; background-color: white;")
        self.search_input.textChanged.connect(self.load_books)
        
        self.btn_clear = QPushButton("Clear")
        self.btn_clear.setStyleSheet("background-color: #3b4b61; color: white; padding: 8px 20px; border-radius: 3px; font-weight: bold;")
        self.btn_clear.clicked.connect(lambda: self.search_input.clear())

        add_btn = QPushButton("Add Book")
        add_btn.setStyleSheet("background-color: #3b4b61; color: white; padding: 8px 15px; border-radius: 3px; font-weight: bold;")
        add_btn.setCursor(Qt.PointingHandCursor)
        add_btn.clicked.connect(self.show_add_book_dialog)

        del_btn = QPushButton("Delete Book")
        del_btn.setStyleSheet("background-color: #c9302c; color: white; padding: 8px 15px; border-radius: 3px; font-weight: bold;")
        del_btn.setCursor(Qt.PointingHandCursor)
        del_btn.clicked.connect(self.delete_selected_book)

        top_bar.addWidget(title_label)
        top_bar.addStretch()
        top_bar.addWidget(add_btn)
        top_bar.addWidget(del_btn)

        layout.addLayout(top_bar)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels(["ID", "ISBN", "Title", "Author", "Category", "Total Copies", "Available Copies", "Status"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
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
        
        self.table.doubleClicked.connect(self.edit_selected_book)

        layout.addWidget(self.table)
        
        # Bottom Search Bar
        search_layout = QHBoxLayout()
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.btn_clear)
        layout.addLayout(search_layout)

    def refresh_data(self):
        self.load_books()

    def load_books(self):
        search_term = self.search_input.text().strip()
        db = SessionLocal()
        
        try:
            query = db.query(Book)
            
            if search_term:
                terms = search_term.split()
                for term in terms:
                    pattern = f"%{term}%"
                    query = query.filter(
                        (Book.title.ilike(pattern)) |
                        (Book.author.ilike(pattern)) |
                        (Book.isbn.ilike(pattern))
                    )
                
            books = query.all()
            
            self.table.setRowCount(0)
            for row, book in enumerate(books):
                self.table.insertRow(row)
                self.table.setItem(row, 0, QTableWidgetItem(str(book.id)))
                self.table.setItem(row, 1, QTableWidgetItem(book.isbn))
                self.table.setItem(row, 2, QTableWidgetItem(book.title))
                self.table.setItem(row, 3, QTableWidgetItem(book.author))
                self.table.setItem(row, 4, QTableWidgetItem(book.category or ""))
                
                # Total copies are available stock plus every copy that is still out.
                open_borrowings = sum(1 for bw in book.borrowings if bw.return_date is None)
                total_copies = book.stock + open_borrowings
                
                self.table.setItem(row, 5, QTableWidgetItem(str(total_copies)))
                self.table.setItem(row, 6, QTableWidgetItem(str(book.stock))) # Available copies
                
                status_item = QTableWidgetItem(book.status.value)
                if book.status == BookStatusEnum.AVAILABLE:
                    status_item.setForeground(Qt.darkGreen)
                elif book.status == BookStatusEnum.BORROWED:
                    status_item.setForeground(Qt.darkYellow)
                else:
                    status_item.setForeground(Qt.darkRed)
                self.table.setItem(row, 7, status_item)
                
        finally:
            db.close()

    def show_add_book_dialog(self):
        dialog = BookDialog(parent=self)
        if dialog.exec() == QDialog.Accepted:
            self.load_books()

    def edit_selected_book(self):
        selected_rows = self.table.selectedItems()
        if not selected_rows:
            return
            
        book_id = int(self.table.item(selected_rows[0].row(), 0).text())
        
        db = SessionLocal()
        try:
            book = db.query(Book).filter(Book.id == book_id).first()
            if book:
                dialog = BookDialog(book, parent=self)
                if dialog.exec() == QDialog.Accepted:
                    self.load_books()
        finally:
            db.close()

    def delete_selected_book(self):
        selected_rows = self.table.selectedItems()
        if not selected_rows:
            QMessageBox.warning(self, "Selection Error", "Please select a book to delete by clicking on its row.")
            return
            
        book_id = int(self.table.item(selected_rows[0].row(), 0).text())
        title = self.table.item(selected_rows[0].row(), 2).text()
        
        reply = QMessageBox.question(
            self, 'Confirm Deletion',
            f"Are you sure you want to delete the book: '{title}'?\n\nThis will also permanently remove any past returned borrowing records associated with this book.",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            db = SessionLocal()
            try:
                book = db.query(Book).filter(Book.id == book_id).first()
                if book:
                    # Any unreturned borrowing means the book is still out and must not be deleted.
                    has_open_borrows = any(b.return_date is None for b in book.borrowings)
                    if has_open_borrows:
                        QMessageBox.warning(self, "Cannot Delete", f"Cannot delete '{title}' because there are open borrowings for it. Please make sure all copies are returned first.")
                        return
                    
                    db.delete(book)
                    db.commit()
                    QMessageBox.information(self, "Success", f"Book '{title}' has been successfully deleted.")
                    self.load_books()
                else:
                    QMessageBox.warning(self, "Error", "Book not found.")
            except Exception as e:
                db.rollback()
                QMessageBox.critical(self, "Error", f"Failed to delete book: {str(e)}")
            finally:
                db.close()
