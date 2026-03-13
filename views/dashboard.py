from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
    QHeaderView,
    QAbstractItemView,
)

from database import SessionLocal
from models import BorrowStatusEnum
from reporting import fetch_dashboard_metrics


class StatCard(QFrame):
    def __init__(self, title, accent_color="#3b4b61", parent=None):
        super().__init__(parent)
        self.setObjectName("StatCard")
        self.setStyleSheet(
            f"""
            QFrame#StatCard {{
                background-color: white;
                border: 1px solid #d8dde6;
                border-left: 5px solid {accent_color};
                border-radius: 8px;
            }}
            QLabel {{
                color: #2c3545;
            }}
        """
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(4)

        title_label = QLabel(title)
        title_font = title_label.font()
        title_font.setPointSize(10)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #5b6576;")

        self.value_label = QLabel("0")
        value_font = self.value_label.font()
        value_font.setPointSize(22)
        value_font.setBold(True)
        self.value_label.setFont(value_font)

        self.subtitle_label = QLabel("")
        self.subtitle_label.setStyleSheet("color: #6b7280; font-size: 11px;")

        layout.addWidget(title_label)
        layout.addWidget(self.value_label)
        layout.addWidget(self.subtitle_label)

    def set_value(self, value, subtitle=""):
        self.value_label.setText(str(value))
        self.subtitle_label.setText(subtitle or "")


class DashboardWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.refresh_data()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        header_layout = QHBoxLayout()
        title_layout = QVBoxLayout()
        title_layout.setSpacing(2)

        title_label = QLabel("Dashboard Overview")
        title_font = title_label.font()
        title_font.setPointSize(24)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #2c3545;")

        subtitle = QLabel("Live library metrics and recent borrowing activity")
        subtitle.setStyleSheet("color: #5b6576; font-size: 13px;")

        title_layout.addWidget(title_label)
        title_layout.addWidget(subtitle)

        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.setCursor(Qt.PointingHandCursor)
        self.refresh_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #3b4b61;
                color: white;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2c3545;
            }
        """
        )
        self.refresh_btn.clicked.connect(self.refresh_data)

        header_layout.addLayout(title_layout)
        header_layout.addStretch()
        header_layout.addWidget(self.refresh_btn)
        layout.addLayout(header_layout)

        cards_layout = QGridLayout()
        cards_layout.setSpacing(12)

        self.card_titles = StatCard("Registered Titles", "#0ea5a4")
        self.card_available = StatCard("Available Copies", "#2563eb")
        self.card_active = StatCard("Active Loans", "#f59e0b")
        self.card_overdue = StatCard("Overdue Loans", "#dc2626")
        self.card_members = StatCard("Members", "#16a34a")
        self.card_returns = StatCard("Returns This Month", "#7c3aed")

        cards = [
            self.card_titles,
            self.card_available,
            self.card_active,
            self.card_overdue,
            self.card_members,
            self.card_returns,
        ]
        for i, card in enumerate(cards):
            cards_layout.addWidget(card, i // 3, i % 3)

        layout.addLayout(cards_layout)

        tables_layout = QHBoxLayout()
        tables_layout.setSpacing(12)

        self.overdue_table = QTableWidget()
        self.overdue_table.setColumnCount(4)
        self.overdue_table.setHorizontalHeaderLabels(["Member", "Book", "Due Date", "Days Overdue"])
        self.configure_table(self.overdue_table)

        self.recent_table = QTableWidget()
        self.recent_table.setColumnCount(5)
        self.recent_table.setHorizontalHeaderLabels(["Member", "Book", "Borrowed", "Due Date", "Status"])
        self.configure_table(self.recent_table)

        overdue_frame = self.wrap_in_panel("Overdue Preview", self.overdue_table)
        recent_frame = self.wrap_in_panel("Recent Borrowing Activity", self.recent_table)

        tables_layout.addWidget(overdue_frame)
        tables_layout.addWidget(recent_frame)
        layout.addLayout(tables_layout)

    def configure_table(self, table):
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table.verticalHeader().setVisible(False)
        table.setSelectionBehavior(QAbstractItemView.SelectRows)
        table.setSelectionMode(QAbstractItemView.SingleSelection)
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        table.setAlternatingRowColors(True)
        table.setStyleSheet(
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
            QTableWidget::item:selected {
                background-color: #cfe3ff;
                color: #1f2937;
            }
        """
        )

    def wrap_in_panel(self, title, content_widget):
        panel = QFrame()
        panel.setStyleSheet(
            """
            QFrame {
                background-color: transparent;
            }
            QLabel {
                color: #2c3545;
                font-weight: bold;
                font-size: 14px;
            }
        """
        )
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(0, 0, 0, 0)
        panel_layout.setSpacing(8)
        panel_layout.addWidget(QLabel(title))
        panel_layout.addWidget(content_widget)
        return panel

    def refresh_data(self):
        db = SessionLocal()
        try:
            data = fetch_dashboard_metrics(db)

            self.card_titles.set_value(data["total_titles"], "Unique books in catalog")
            self.card_available.set_value(data["available_copies"], "Copies currently on shelves")
            self.card_active.set_value(data["active_loans"], "Borrowings not returned yet")
            self.card_overdue.set_value(data["overdue_loans"], "Loans past due date")
            self.card_members.set_value(data["total_members"], "Registered members")
            self.card_returns.set_value(data["returned_this_month"], "Completed in current month")

            self.populate_overdue_table(data["overdue_preview"])
            self.populate_recent_table(data["recent_activity"])
        finally:
            db.close()

    def populate_overdue_table(self, rows):
        self.overdue_table.setRowCount(0)
        for row_idx, row in enumerate(rows):
            self.overdue_table.insertRow(row_idx)
            self.overdue_table.setItem(row_idx, 0, QTableWidgetItem(row["member_name"]))
            self.overdue_table.setItem(row_idx, 1, QTableWidgetItem(row["book_title"]))
            self.overdue_table.setItem(row_idx, 2, QTableWidgetItem(row["due_date"].strftime("%Y-%m-%d")))

            days_item = QTableWidgetItem(str(row["days_overdue"]))
            days_item.setForeground(Qt.darkRed)
            self.overdue_table.setItem(row_idx, 3, days_item)

    def populate_recent_table(self, rows):
        self.recent_table.setRowCount(0)
        for row_idx, row in enumerate(rows):
            self.recent_table.insertRow(row_idx)
            self.recent_table.setItem(row_idx, 0, QTableWidgetItem(row["member"]))
            self.recent_table.setItem(row_idx, 1, QTableWidgetItem(row["book"]))
            self.recent_table.setItem(row_idx, 2, QTableWidgetItem(row["borrowed_on"].strftime("%Y-%m-%d")))
            self.recent_table.setItem(row_idx, 3, QTableWidgetItem(row["due_date"].strftime("%Y-%m-%d")))

            status_item = QTableWidgetItem(row["status"].value)
            if row["status"] == BorrowStatusEnum.OVERDUE:
                status_item.setForeground(Qt.darkRed)
            elif row["status"] == BorrowStatusEnum.RETURNED:
                status_item.setForeground(Qt.darkGreen)
            else:
                status_item.setForeground(Qt.darkBlue)
            self.recent_table.setItem(row_idx, 4, status_item)
