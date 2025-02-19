from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QListWidget,
                             QListWidgetItem, QPushButton, QLabel, QComboBox,
                             QTabWidget, QSplitter, QLineEdit)
from PyQt6.QtCore import Qt, pyqtSlot
from PyQt6.QtGui import QClipboard
from loguru import logger

from models import ClipboardItem, Category
from clipboard_manager import ClipboardMonitor

class ClipboardHistoryWidget(QWidget):
    def __init__(self, clipboard: QClipboard, monitor: ClipboardMonitor):
        super().__init__()
        self.clipboard = clipboard
        self.monitor = monitor
        self.setup_ui()
        self.setup_connections()
        self.load_history()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # 创建搜索框
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText('搜索历史记录...')
        layout.addWidget(self.search_box)

        # 创建分类选择器
        self.category_combo = QComboBox()
        self.category_combo.addItem('全部')
        layout.addWidget(self.category_combo)

        # 创建选项卡
        self.tab_widget = QTabWidget()
        
        # 历史记录列表
        self.history_list = QListWidget()
        self.tab_widget.addTab(self.history_list, '历史记录')

        # 分类视图
        self.category_view = QListWidget()
        self.tab_widget.addTab(self.category_view, '分类')

        layout.addWidget(self.tab_widget)

        # 操作按钮
        button_layout = QHBoxLayout()
        self.copy_btn = QPushButton('复制选中项')
        self.delete_btn = QPushButton('删除')
        button_layout.addWidget(self.copy_btn)
        button_layout.addWidget(self.delete_btn)
        layout.addLayout(button_layout)

    def setup_connections(self):
        # 连接信号和槽
        self.monitor.content_changed.connect(self.on_clipboard_changed)
        self.copy_btn.clicked.connect(self.copy_selected_item)
        self.delete_btn.clicked.connect(self.delete_selected_item)
        self.search_box.textChanged.connect(self.filter_history)
        self.category_combo.currentTextChanged.connect(self.filter_by_category)

    def load_history(self):
        # 加载历史记录
        items = self.monitor.get_history()
        self.history_list.clear()
        for item in items:
            self._add_history_item(item)

        # 更新分类列表
        self._update_categories()

    def _add_history_item(self, item: ClipboardItem):
        # 创建列表项
        list_item = QListWidgetItem()
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # 显示内容预览
        content_label = QLabel(self._get_preview_text(item))
        content_label.setWordWrap(True)
        layout.addWidget(content_label)

        # 显示元信息
        meta_label = QLabel(f'类型: {item.content_type.value} | '
                          f'时间: {item.created_at.strftime("%Y-%m-%d %H:%M:%S")} | '
                          f'分类: {item.category.name if item.category else "未分类"}')
        meta_label.setStyleSheet('color: gray; font-size: 10px;')
        layout.addWidget(meta_label)

        widget.setLayout(layout)
        list_item.setSizeHint(widget.sizeHint())
        
        self.history_list.insertItem(0, list_item)
        self.history_list.setItemWidget(list_item, widget)

    def _get_preview_text(self, item: ClipboardItem) -> str:
        # 根据内容类型生成预览文本
        if item.content_type.value in ['text', 'code']:
            return item.content[:200] + '...' if len(item.content) > 200 else item.content
        elif item.content_type.value == 'url':
            return f'URL: {item.content}'
        elif item.content_type.value == 'image':
            return '[图片]'
        return f'[{item.content_type.value}]'

    def _update_categories(self):
        # 更新分类下拉框
        current_text = self.category_combo.currentText()
        self.category_combo.clear()
        self.category_combo.addItem('全部')
        
        categories = self.monitor.session.query(Category).all()
        for category in categories:
            self.category_combo.addItem(category.name)

        # 恢复之前的选择
        index = self.category_combo.findText(current_text)
        if index >= 0:
            self.category_combo.setCurrentIndex(index)

    @pyqtSlot(ClipboardItem)
    def on_clipboard_changed(self, item: ClipboardItem):
        # 处理剪贴板内容变化
        self._add_history_item(item)
        self._update_categories()

    def copy_selected_item(self):
        # 复制选中的内容到剪贴板
        current_item = self.history_list.currentItem()
        if not current_item:
            return

        widget = self.history_list.itemWidget(current_item)
        if widget:
            content_label = widget.findChild(QLabel)
            if content_label:
                self.clipboard.setText(content_label.text())

    def delete_selected_item(self):
        # 删除选中的记录
        current_item = self.history_list.currentItem()
        if current_item:
            self.history_list.takeItem(self.history_list.row(current_item))

    def filter_history(self, text: str):
        # 根据搜索文本过滤历史记录
        for i in range(self.history_list.count()):
            item = self.history_list.item(i)
            widget = self.history_list.itemWidget(item)
            if widget:
                content_label = widget.findChild(QLabel)
                if content_label:
                    item.setHidden(
                        text.lower() not in content_label.text().lower()
                    )

    def filter_by_category(self, category_name: str):
        # 根据分类过滤历史记录
        if category_name == '全部':
            self.load_history()
        else:
            items = self.monitor.get_by_category(category_name)
            self.history_list.clear()
            for item in items:
                self._add_history_item(item)