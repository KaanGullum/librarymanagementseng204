import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer
from models import User, RoleEnum
from main_window import MainWindow

def take_screenshots():
    # 1. Books tab (index 1)
    window.switch_view(1)
    window.grab().save(r"C:\Users\kaang\.gemini\antigravity\brain\5e631045-ff0a-44f2-80f0-950372c2f2c0\app_books.png")
    
    # 2. Members tab (index 2)
    window.switch_view(2)
    window.grab().save(r"C:\Users\kaang\.gemini\antigravity\brain\5e631045-ff0a-44f2-80f0-950372c2f2c0\app_members.png")

    window.close()
    app.quit()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Mock Admin User
    admin_user = User(username="admin_tester", role=RoleEnum.ADMIN)
    
    window = MainWindow(admin_user)
    window.resize(1000, 700)
    window.show()
    
    QTimer.singleShot(1500, take_screenshots) # wait 1.5s for render
    
    sys.exit(app.exec())
