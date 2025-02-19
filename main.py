import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QSystemTrayIcon, QMenu
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtCore import Qt
from loguru import logger
from sqlalchemy.orm import sessionmaker

from models import init_db
from ui import ClipboardHistoryWidget
from clipboard_manager import ClipboardMonitor

# 增加递归深度限制
sys.setrecursionlimit(3000)

class ClipboardManager(QMainWindow):
    def __init__(self):
        super().__init__()
        logger.info("初始化智能剪贴板应用")
        self.setWindowTitle('智能剪贴板')
        self.setGeometry(100, 100, 800, 600)
        
        # 初始化数据库
        logger.info("初始化数据库连接")
        engine = init_db('sqlite:///clipboard.db')
        Session = sessionmaker(bind=engine)
        self.session = Session()
        
        # 初始化剪贴板监控
        logger.info("初始化剪贴板监控")
        self.clipboard = QApplication.clipboard()
        self.monitor = ClipboardMonitor(self.clipboard, self.session)
        
        self.setup_ui()
        self.setup_tray()
        logger.info("应用初始化完成")

    def setup_ui(self):
        # 设置窗口标志，使其始终显示在最前面
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint)
        
        # 创建并设置剪贴板历史记录组件
        self.history_widget = ClipboardHistoryWidget(self.clipboard, self.monitor)
        self.setCentralWidget(self.history_widget)

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
        logger.info("窗口最小化到系统托盘")
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