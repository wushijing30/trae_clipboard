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
        self.setStyleSheet("""
            QMainWindow, QWidget {
                background: #ffffff;
            }
            QTabWidget::pane {
                background: #f5f5f5;
                border: 1px solid #ddd;
                border-radius: 4px;
            }
            QTabBar::tab {
                background: #e0e0e0;
                padding: 8px 12px;
                margin: 2px;
                border: 1px solid #ccc;
                border-radius: 4px;
            }
            QTabBar::tab:selected {
                background: #ffffff;
                border-bottom-color: #ffffff;
            }
            QScrollBar:vertical {
                border: none;
                background: #f0f0f0;
                width: 8px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #c0c0c0;
                min-height: 30px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical:hover {
                background: #a0a0a0;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
        """)
        # 设置窗口图标
        icon = QIcon('icons/icons8-clipboard-48.png')
        self.setWindowIcon(icon)
        
        # 初始化数据库
        logger.info("初始化数据库连接")
        engine = init_db('sqlite:///clipboards.db', echo=True)
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
        icon = QIcon('icons/icons8-clipboard-48.png')
        self.tray_icon.setIcon(icon)

        # 创建托盘菜单
        tray_menu = QMenu()
        show_action = QAction('显示主窗口', self)
        show_action.triggered.connect(self.show)
        quit_action = QAction('退出', self)
        quit_action.triggered.connect(QApplication.quit)

        tray_menu.addAction(show_action)
        tray_menu.addAction(quit_action)

        self.tray_icon.setContextMenu(tray_menu)
        # 添加托盘图标的activated信号处理
        self.tray_icon.activated.connect(self._handle_tray_activation)
        self.tray_icon.show()

    def _handle_tray_activation(self, reason):
        # 当用户左键单击托盘图标时显示窗口
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.show()
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