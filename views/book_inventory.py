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
            QLabel, QLineEdit, QComboBox, QSpinBox {
                color: #333;
                font-family: 'Segoe UI', sans-serif;
                font-size: 13px;
            }
            QLineEdit, QComboBox, QSpinBox {
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
        
        self.isbn_input = QLineEdit()
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
            self.category_input.setText(self.book.category)
            self.stock_input.setValue(self.book.stock)
            self.status_combo.setCurrentText(self.book.status.value)

        form_layout.addRow("ISBN:", self.isbn_input)
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
        isbn = self.isbn_input.text().strip()
        title = self.title_input.text().strip()
        author = self.author_input.text().strip()
        
        if not isbn or not title or not author:
            QMessageBox.warning(self, "Validation Error", "ISBN, Title, and Author are required fields.")
            return
            
        if len(isbn) < 5:
            QMessageBox.warning(self, "Validation Error", "Please enter a valid ISBN.")
            return

        db = SessionLocal()
        try:
            if self.book: # Edit mode
                book = db.query(Book).filter(Book.id == self.book.id).first()
                if not book:
                    QMessageBox.warning(self, "Error", "Book not found.")
                    return
                book.isbn = isbn
                book.title = title
                book.author = author
                book.category = self.category_input.text().strip()
                book.stock = self.stock_input.value()
                book.status = BookStatusEnum(self.status_combo.currentText())
            else: # Create mode
                new_book = Book(
                    isbn=isbn,
                    title=title,
                    author=author,
                    category=self.category_input.text().strip(),
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

        top_bar.addWidget(title_label)
        top_bar.addStretch()
        top_bar.addWidget(add_btn)

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
                
                # Calculate Total Copies: available stock + currently active borrowings
                active_borrowings = sum(1 for bw in book.borrowings if bw.status.name == "ACTIVE")
                total_copies = book.stock + active_borrowings
                
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
