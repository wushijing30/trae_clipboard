from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QListWidget,
                             QListWidgetItem, QPushButton, QLabel, QComboBox,
                             QTabWidget, QSplitter, QLineEdit)
from PyQt6.QtCore import Qt, pyqtSlot
from PyQt6.QtGui import QClipboard
from loguru import logger
from datetime import datetime

from models import ClipboardItem, Category
from clipboard_manager import ClipboardMonitor

class ClipboardHistoryWidget(QWidget):
    def __init__(self, clipboard: QClipboard, monitor: ClipboardMonitor):
        super().__init__()
        self.clipboard = clipboard
        self.monitor = monitor
        self._updating_categories = False  # 添加标志位
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

        # 移除底部按钮布局，改为在每个列表项中添加按钮

    def setup_connections(self):
        # 连接信号和槽
        self.monitor.content_changed.connect(self.on_clipboard_changed)
        self.search_box.textChanged.connect(self.filter_history)
        self.category_combo.currentTextChanged.connect(self.filter_by_category)

    def load_history(self):
        # 加载历史记录
        logger.info("加载剪贴板历史记录")
        items = self.monitor.get_history()
        self.history_list.clear()
        # 按照置顶状态和最后访问时间排序
        pinned_items = sorted([item for item in items if item.is_pinned],
                            key=lambda x: x.last_accessed, reverse=True)
        unpinned_items = sorted([item for item in items if not item.is_pinned],
                              key=lambda x: x.last_accessed, reverse=True)
        
        # 先添加置顶项，再添加未置顶项
        for item in pinned_items:
            self._add_history_item(item)
        for item in unpinned_items:
            self._add_history_item(item)

        # 更新分类列表
        self._update_categories()

    def _add_history_item(self, item: ClipboardItem):
        # 创建列表项
        list_item = QListWidgetItem()
        list_item.setData(Qt.ItemDataRole.UserRole, item.id)  # 存储记录ID
        widget = QWidget()
        layout = QHBoxLayout(widget)  # 使用水平布局
        
        # 创建内容区域
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        
        # 如果是置顶项，添加置顶标记
        if item.is_pinned:
            list_item.setBackground(Qt.GlobalColor.lightGray)  # 置顶项背景色

        # 显示内容预览
        content_label = QLabel(self._get_preview_text(item))
        content_label.setWordWrap(True)
        content_layout.addWidget(content_label)

        # 显示元信息
        meta_label = QLabel(f'类型: {item.content_type.value} | '
                          f'时间: {item.created_at.strftime("%Y-%m-%d %H:%M:%S")} | '
                          f'分类: {item.category.name if item.category else "未分类"}')
        meta_label.setStyleSheet('color: gray; font-size: 10px;')
        content_layout.addWidget(meta_label)
        
        # 添加内容区域到主布局
        layout.addWidget(content_widget, stretch=1)
        
        # 创建按钮区域
        button_widget = QWidget()
        button_layout = QVBoxLayout(button_widget)
        
        # 添加操作按钮
        copy_btn = QPushButton('复制')
        pin_btn = QPushButton('取消置顶' if item.is_pinned else '置顶')
        delete_btn = QPushButton('删除')
        
        # 设置按钮样式和大小
        for btn in [copy_btn, pin_btn, delete_btn]:
            btn.setFixedWidth(50)
            btn.setStyleSheet('padding: 2px;')
        
        button_layout.addWidget(copy_btn)
        button_layout.addWidget(pin_btn)
        button_layout.addWidget(delete_btn)
        button_layout.setSpacing(2)
        
        # 连接按钮信号
        item_id = item.id
        copy_btn.clicked.connect(lambda: self.copy_item(item_id))
        pin_btn.clicked.connect(lambda: self.pin_item(item_id))
        delete_btn.clicked.connect(lambda: self.delete_item(item_id))
        
        # 添加按钮区域到主布局
        layout.addWidget(button_widget)
        
        widget.setLayout(layout)
        list_item.setSizeHint(widget.sizeHint())
        
        self.history_list.addItem(list_item)
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
        self._updating_categories = True  # 设置标志位
        try:
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
        finally:
            self._updating_categories = False  # 重置标志位

    @pyqtSlot(ClipboardItem)
    def on_clipboard_changed(self, item: ClipboardItem):
        # 处理剪贴板内容变化
        self._add_history_item(item)
        self._update_categories()

    def copy_item(self, item_id):
        # 复制指定ID的内容到剪贴板
        item = self.monitor.get_item_by_id(item_id)
        if item:
            self.monitor.is_copying_selected = True  # 设置标记
            self.clipboard.setText(item.content)
            logger.info(f"已复制ID为{item_id}的内容到剪贴板")

    def delete_item(self, item_id):
        # 删除指定ID的记录
        if self.monitor.delete_item(item_id):
            # 从UI列表中找到并移除对应项
            for i in range(self.history_list.count()):
                item = self.history_list.item(i)
                if item.data(Qt.ItemDataRole.UserRole) == item_id:
                    self.history_list.takeItem(i)
                    break
            logger.info(f"已删除ID为{item_id}的历史记录")
        else:
            logger.warning(f"删除ID为{item_id}的记录失败")

    def filter_history(self, text: str):
        # 根据搜索文本过滤历史记录
        logger.info(f"根据关键词过滤历史记录: {text}")
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
        if self._updating_categories:  # 如果正在更新分类，则不执行过滤
            return
            
        logger.info(f"根据分类过滤历史记录: {category_name}")
        if category_name == '全部':
            self.load_history()
        else:
            items = self.monitor.get_by_category(category_name)
            self.history_list.clear()
            # 分类过滤时也保持置顶项在前
            pinned_items = [item for item in items if item.is_pinned]
            unpinned_items = [item for item in items if not item.is_pinned]
            
            for item in pinned_items:
                self._add_history_item(item)
            for item in unpinned_items:
                self._add_history_item(item)
                
    def pin_item(self, item_id):
        # 置顶或取消置顶选中的记录
        # 更新置顶状态和最后访问时间
        item = self.monitor.session.query(ClipboardItem).get(item_id)
        if item:
            item.is_pinned = not item.is_pinned
            item.last_accessed = datetime.now()
            self.monitor.session.commit()
            logger.info(f"{'置顶' if item.is_pinned else '取消置顶'}记录: {item_id}")
            # 重新加载列表以更新显示顺序
            self.load_history()