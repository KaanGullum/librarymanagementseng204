from PySide6.QtCore import QDate, Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QDateEdit,
    QFormLayout,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from database import SessionLocal
from reporting import fetch_borrowing_summary, fetch_overdue_records, validate_summary_range


class MiniStatCard(QFrame):
    def __init__(self, title, parent=None):
        super().__init__(parent)
        self.setObjectName("MiniStatCard")
        self.setStyleSheet(
            """
            QFrame#MiniStatCard {
                background-color: white;
                border: 1px solid #d8dde6;
                border-radius: 8px;
            }
            QLabel {
                color: #2c3545;
            }
        """
        )
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(2)

        title_label = QLabel(title)
        title_label.setStyleSheet("color: #64748b; font-size: 11px; font-weight: bold;")

        self.value_label = QLabel("0")
        value_font = self.value_label.font()
        value_font.setPointSize(18)
        value_font.setBold(True)
        self.value_label.setFont(value_font)

        layout.addWidget(title_label)
        layout.addWidget(self.value_label)

    def set_value(self, value):
        self.value_label.setText(str(value))


class ReportsWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.refresh_data()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        top_row = QHBoxLayout()
        title = QLabel("Reporting Center")
        title_font = title.font()
        title_font.setPointSize(24)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setStyleSheet("color: #2c3545;")

        subtitle = QLabel("Overdue monitoring and borrowing analytics")
        subtitle.setStyleSheet("color: #5b6576; font-size: 13px;")

        title_box = QVBoxLayout()
        title_box.setSpacing(2)
        title_box.addWidget(title)
        title_box.addWidget(subtitle)

        self.btn_refresh = QPushButton("Refresh")
        self.btn_refresh.setCursor(Qt.PointingHandCursor)
        self.btn_refresh.setStyleSheet(
            """
            QPushButton {
                background-color: #3b4b61;
                color: white;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2c3545;
            }
        """
        )
        self.btn_refresh.clicked.connect(self.refresh_data)

        top_row.addLayout(title_box)
        top_row.addStretch()
        top_row.addWidget(self.btn_refresh)
        layout.addLayout(top_row)

        filter_frame = QFrame()
        filter_frame.setStyleSheet(
            """
            QFrame {
                background-color: white;
                border: 1px solid #d8dde6;
                border-radius: 8px;
            }
            QLabel {
                color: #2c3545;
            }
            QLineEdit, QSpinBox, QDateEdit {
                border: 1px solid #ced4da;
                border-radius: 4px;
                padding: 5px;
                background-color: #ffffff;
            }
        """
        )
        filter_layout = QGridLayout(filter_frame)
        filter_layout.setContentsMargins(12, 12, 12, 12)
        filter_layout.setHorizontalSpacing(10)
        filter_layout.setVerticalSpacing(8)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by member, email, title, or ISBN...")
        self.search_input.textChanged.connect(self.load_overdue_table)

        self.min_days_spin = QSpinBox()
        self.min_days_spin.setRange(1, 365)
        self.min_days_spin.setValue(1)
        self.min_days_spin.valueChanged.connect(self.load_overdue_table)

        self.btn_clear_filters = QPushButton("Clear Filters")
        self.btn_clear_filters.clicked.connect(self.clear_filters)
        self.btn_clear_filters.setStyleSheet(
            """
            QPushButton {
                background-color: #eef2f7;
                color: #2c3545;
                border: 1px solid #d8dde6;
                padding: 7px 12px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #e2e8f0;
            }
        """
        )

        filter_layout.addWidget(QLabel("Search"), 0, 0)
        filter_layout.addWidget(self.search_input, 0, 1)
        filter_layout.addWidget(QLabel("Min. days overdue"), 0, 2)
        filter_layout.addWidget(self.min_days_spin, 0, 3)
        filter_layout.addWidget(self.btn_clear_filters, 0, 4)
        filter_layout.setColumnStretch(1, 1)
        layout.addWidget(filter_frame)

        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(10)
        self.card_total_overdue = MiniStatCard("Total Overdue Loans")
        self.card_avg_days = MiniStatCard("Average Delay (days)")
        self.card_max_days = MiniStatCard("Longest Delay (days)")
        cards_layout.addWidget(self.card_total_overdue)
        cards_layout.addWidget(self.card_avg_days)
        cards_layout.addWidget(self.card_max_days)
        layout.addLayout(cards_layout)

        self.overdue_table = QTableWidget()
        self.overdue_table.setColumnCount(8)
        self.overdue_table.setHorizontalHeaderLabels(
            ["Record ID", "Member", "Email", "Book", "ISBN", "Borrowed", "Due Date", "Days Overdue"]
        )
        self.overdue_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.overdue_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.overdue_table.verticalHeader().setVisible(False)
        self.overdue_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.overdue_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.overdue_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.overdue_table.setAlternatingRowColors(True)
        self.overdue_table.setStyleSheet(
            """
            QTableWidget {
                background-color: white;
                alternate-background-color: #f8f9fa;
                border: 1px solid #d8dde6;
                border-radius: 8px;
            }
            QHeaderView::section {
                background-color: #2c3545;
                color: white;
                border: none;
                padding: 8px;
                font-weight: bold;
            }
        """
        )
        layout.addWidget(self.overdue_table)

        summary_frame = QFrame()
        summary_frame.setStyleSheet(
            """
            QFrame {
                background-color: white;
                border: 1px solid #d8dde6;
                border-radius: 8px;
            }
            QLabel {
                color: #2c3545;
            }
            QDateEdit {
                border: 1px solid #ced4da;
                border-radius: 4px;
                padding: 5px;
                background-color: #ffffff;
            }
        """
        )
        summary_layout = QVBoxLayout(summary_frame)
        summary_layout.setContentsMargins(12, 12, 12, 12)
        summary_layout.setSpacing(8)

        summary_title = QLabel("Borrowing Summary")
        summary_title_font = summary_title.font()
        summary_title_font.setPointSize(16)
        summary_title_font.setBold(True)
        summary_title.setFont(summary_title_font)

        summary_subtitle = QLabel("Validate range and generate summary metrics")
        summary_subtitle.setStyleSheet("color: #64748b;")

        date_row = QHBoxLayout()
        date_form = QFormLayout()
        date_form.setLabelAlignment(Qt.AlignLeft)

        self.start_date_edit = QDateEdit()
        self.start_date_edit.setCalendarPopup(True)
        self.end_date_edit = QDateEdit()
        self.end_date_edit.setCalendarPopup(True)

        today = QDate.currentDate()
        self.end_date_edit.setDate(today)
        self.start_date_edit.setDate(today.addDays(-30))

        date_form.addRow("Start Date:", self.start_date_edit)
        date_form.addRow("End Date:", self.end_date_edit)
        date_row.addLayout(date_form)

        self.btn_generate_summary = QPushButton("Validate & Generate")
        self.btn_generate_summary.setCursor(Qt.PointingHandCursor)
        self.btn_generate_summary.setStyleSheet(
            """
            QPushButton {
                background-color: #14532d;
                color: white;
                border-radius: 4px;
                padding: 8px 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #166534;
            }
        """
        )
        self.btn_generate_summary.clicked.connect(self.generate_summary)

        date_row.addStretch()
        date_row.addWidget(self.btn_generate_summary)

        self.summary_results = QLabel("No summary generated yet.")
        self.summary_results.setStyleSheet("color: #334155; font-size: 12px;")
        self.summary_results.setWordWrap(True)

        summary_layout.addWidget(summary_title)
        summary_layout.addWidget(summary_subtitle)
        summary_layout.addLayout(date_row)
        summary_layout.addWidget(self.summary_results)
        layout.addWidget(summary_frame)

    def clear_filters(self):
        self.search_input.clear()
        self.min_days_spin.setValue(1)
        self.load_overdue_table()

    def refresh_data(self):
        self.load_overdue_table()
        self.generate_summary(silent_validation=True)

    def load_overdue_table(self):
        db = SessionLocal()
        try:
            rows = fetch_overdue_records(
                db,
                search_text=self.search_input.text(),
                min_days_overdue=self.min_days_spin.value(),
            )
        finally:
            db.close()

        self.overdue_table.setRowCount(0)
        for row_idx, row in enumerate(rows):
            self.overdue_table.insertRow(row_idx)
            self.overdue_table.setItem(row_idx, 0, QTableWidgetItem(str(row["record_id"])))
            self.overdue_table.setItem(row_idx, 1, QTableWidgetItem(row["member_name"]))
            self.overdue_table.setItem(row_idx, 2, QTableWidgetItem(row["member_email"]))
            self.overdue_table.setItem(row_idx, 3, QTableWidgetItem(row["book_title"]))
            self.overdue_table.setItem(row_idx, 4, QTableWidgetItem(row["isbn"]))
            self.overdue_table.setItem(row_idx, 5, QTableWidgetItem(row["borrow_date"].strftime("%Y-%m-%d")))
            self.overdue_table.setItem(row_idx, 6, QTableWidgetItem(row["due_date"].strftime("%Y-%m-%d")))

            days_item = QTableWidgetItem(str(row["days_overdue"]))
            days_item.setForeground(Qt.darkRed)
            self.overdue_table.setItem(row_idx, 7, days_item)

        total = len(rows)
        avg_days = round(sum(row["days_overdue"] for row in rows) / total, 1) if rows else 0
        max_days = max((row["days_overdue"] for row in rows), default=0)

        self.card_total_overdue.set_value(total)
        self.card_avg_days.set_value(avg_days)
        self.card_max_days.set_value(max_days)

    def generate_summary(self, silent_validation=False):
        start_date = self.start_date_edit.date().toPython()
        end_date = self.end_date_edit.date().toPython()

        is_valid, message = validate_summary_range(start_date, end_date)
        if not is_valid:
            if not silent_validation:
                QMessageBox.warning(self, "Validation Error", message)
            self.summary_results.setText(f"Validation failed: {message}")
            return

        db = SessionLocal()
        try:
            summary = fetch_borrowing_summary(db, start_date, end_date)
        finally:
            db.close()

        summary_text = (
            f"Range: {start_date.isoformat()} to {end_date.isoformat()} | "
            f"Issued: {summary['issued_count']} | Returned: {summary['returned_count']} | "
            f"Currently Open: {summary['current_open_loans']} | "
            f"Overdue Started in Range: {summary['overdue_started_in_range']} | "
            f"New Members: {summary['new_members']} | "
            f"Return Rate: %{summary['return_rate']} | "
            f"Top Book: {summary['top_book_title']} ({summary['top_book_borrows']})"
        )
        self.summary_results.setText(summary_text)
