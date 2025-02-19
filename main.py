import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QSystemTrayIcon, QMenu
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtCore import Qt
from loguru import logger

class ClipboardManager(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('智能剪贴板')
        self.setGeometry(100, 100, 800, 600)
        self.setup_ui()
        self.setup_tray()

    def setup_ui(self):
        # 设置窗口标志，使其始终显示在最前面
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint)

    def setup_tray(self):
        # 创建系统托盘图标
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setToolTip('智能剪贴板')

        # 创建托盘菜单
        tray_menu = QMenu()
        show_action = QAction('显示主窗口', self)
        show_action.triggered.connect(self.show)
        quit_action = QAction('退出', self)
        quit_action.triggered.connect(QApplication.quit)

        tray_menu.addAction(show_action)
        tray_menu.addAction(quit_action)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()

    def closeEvent(self, event):
        # 关闭窗口时最小化到系统托盘
        event.ignore()
        self.hide()

def main():
    logger.add("clipboard.log", rotation="10 MB")
    app = QApplication(sys.argv)
    window = ClipboardManager()
    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()