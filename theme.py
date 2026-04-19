import os

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPalette


ASSETS_DIR = os.path.join(os.path.dirname(__file__), "assets")


def configure_qt_for_light_mode():
    # Force Qt to use a consistent widget style instead of inheriting OS dark widgets.
    os.environ["QT_STYLE_OVERRIDE"] = "Fusion"


def apply_light_theme(app):
    app.setStyle("Fusion")

    palette = QPalette()
    palette.setColor(QPalette.Window, QColor("#f4f6f9"))
    palette.setColor(QPalette.WindowText, QColor("#1f2933"))
    palette.setColor(QPalette.Base, QColor("#ffffff"))
    palette.setColor(QPalette.AlternateBase, QColor("#eef2f6"))
    palette.setColor(QPalette.ToolTipBase, QColor("#ffffff"))
    palette.setColor(QPalette.ToolTipText, QColor("#1f2933"))
    palette.setColor(QPalette.Text, QColor("#1f2933"))
    palette.setColor(QPalette.Button, QColor("#f0f0f0"))
    palette.setColor(QPalette.ButtonText, QColor("#1f2933"))
    palette.setColor(QPalette.BrightText, QColor("#ffffff"))
    palette.setColor(QPalette.Link, QColor("#0078D7"))
    palette.setColor(QPalette.Highlight, QColor("#0078D7"))
    palette.setColor(QPalette.HighlightedText, QColor("#ffffff"))

    palette.setColor(QPalette.Disabled, QPalette.Text, QColor("#7a7a7a"))
    palette.setColor(QPalette.Disabled, QPalette.ButtonText, QColor("#7a7a7a"))
    palette.setColor(QPalette.Disabled, QPalette.WindowText, QColor("#7a7a7a"))

    app.setPalette(palette)

    style_hints = app.styleHints()
    if hasattr(style_hints, "setColorScheme") and hasattr(Qt, "ColorScheme"):
        style_hints.setColorScheme(Qt.ColorScheme.Light)


def build_spinbox_stylesheet():
    up_arrow = os.path.join(ASSETS_DIR, "spinbox-up.svg").replace("\\", "/")
    down_arrow = os.path.join(ASSETS_DIR, "spinbox-down.svg").replace("\\", "/")

    return f"""
        QSpinBox {{
            background-color: white;
            border: 1px solid #ced4da;
            border-radius: 4px;
            color: #333;
            padding: 4px 24px 4px 4px;
        }}
        QSpinBox::up-button {{
            subcontrol-origin: border;
            subcontrol-position: top right;
            width: 20px;
            background-color: #f8fafc;
            border-left: 1px solid #ced4da;
            border-top-right-radius: 4px;
            border-bottom: 1px solid #ced4da;
        }}
        QSpinBox::down-button {{
            subcontrol-origin: border;
            subcontrol-position: bottom right;
            width: 20px;
            background-color: #f8fafc;
            border-left: 1px solid #ced4da;
            border-bottom-right-radius: 4px;
        }}
        QSpinBox::up-button:hover, QSpinBox::down-button:hover {{
            background-color: #eef2f7;
        }}
        QSpinBox::up-arrow {{
            image: url({up_arrow});
            width: 10px;
            height: 6px;
        }}
        QSpinBox::down-arrow {{
            image: url({down_arrow});
            width: 10px;
            height: 6px;
        }}
    """
