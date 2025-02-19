import hashlib
import json
import os
import uuid
from datetime import datetime
from typing import Optional, List

from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtGui import QClipboard, QImage
from sqlalchemy.orm import Session
from loguru import logger

from models import ClipboardItem, ContentType, Category

class ClipboardMonitor(QObject):
    content_changed = pyqtSignal(ClipboardItem)

    def __init__(self, clipboard: QClipboard, session: Session):
        super().__init__()
        self.clipboard = clipboard
        self.session = session
        self.device_id = self._get_device_id()
        self._setup_clipboard_monitoring()

    def _get_device_id(self) -> str:
        """获取或生成设备唯一标识"""
        config_file = 'device_config.json'
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                return json.load(f)['device_id']
        
        device_id = str(uuid.uuid4())
        with open(config_file, 'w') as f:
            json.dump({'device_id': device_id}, f)
        return device_id

    def _setup_clipboard_monitoring(self):
        """设置剪贴板监听"""
        self.clipboard.dataChanged.connect(self._handle_clipboard_change)

    def _handle_clipboard_change(self):
        """处理剪贴板内容变化"""
        try:
            content, content_type = self._get_clipboard_content()
            if not content:
                return

            # 创建新的剪贴板记录
            item = ClipboardItem(
                content=content,
                content_type=content_type,
                device_id=self.device_id
            )

            # 智能分类
            category = self._categorize_content(content, content_type)
            if category:
                item.category = category

            # 保存到数据库
            self.session.add(item)
            self.session.commit()

            # 发送信号通知UI更新
            self.content_changed.emit(item)

        except Exception as e:
            logger.error(f"处理剪贴板变化时出错: {str(e)}")

    def _get_clipboard_content(self) -> tuple[str, ContentType]:
        """获取剪贴板内容和类型"""
        mime_data = self.clipboard.mimeData()

        if mime_data.hasImage():
            image = mime_data.imageData()
            if isinstance(image, QImage):
                # 将图片转换为base64字符串
                temp_path = 'temp_image.png'
                image.save(temp_path)
                with open(temp_path, 'rb') as f:
                    content = f.read()
                os.remove(temp_path)
                return hashlib.md5(content).hexdigest(), ContentType.IMAGE

        if mime_data.hasUrls():
            urls = mime_data.urls()
            if urls:
                return str(urls[0].toString()), ContentType.URL

        if mime_data.hasText():
            text = mime_data.text()
            if self._is_code(text):
                return text, ContentType.CODE
            return text, ContentType.TEXT

        return "", ContentType.OTHER

    def _is_code(self, text: str) -> bool:
        """判断文本是否为代码"""
        code_indicators = [
            'def ', 'class ', 'import ', 'function', '{', '}',
            'var ', 'let ', 'const ', '</', '/>'
        ]
        return any(indicator in text for indicator in code_indicators)

    def _categorize_content(self, content: str, content_type: ContentType) -> Optional[Category]:
        """智能分类内容"""
        # 根据内容类型和关键词进行分类
        categories = {
            'URLs': ['http://', 'https://', 'www.'],
            '代码片段': ['def', 'class', 'function', 'import'],
            '文档': ['.doc', '.pdf', '.txt', '.md'],
            '图片': ['.jpg', '.png', '.gif', '.svg']
        }

        for category_name, keywords in categories.items():
            if any(keyword in content.lower() for keyword in keywords):
                # 检查分类是否已存在
                category = self.session.query(Category).filter_by(name=category_name).first()
                if not category:
                    category = Category(name=category_name)
                    self.session.add(category)
                    self.session.commit()
                return category

        return None

    def get_history(self, limit: int = 50) -> List[ClipboardItem]:
        """获取剪贴板历史记录"""
        return self.session.query(ClipboardItem)\
            .order_by(ClipboardItem.created_at.desc())\
            .limit(limit)\
            .all()

    def get_by_category(self, category_name: str) -> List[ClipboardItem]:
        """按分类获取剪贴板记录"""
        return self.session.query(ClipboardItem)\
            .join(Category)\
            .filter(Category.name == category_name)\
            .order_by(ClipboardItem.created_at.desc())\
            .all()