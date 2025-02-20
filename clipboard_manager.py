import hashlib
import json
import os
import uuid
from datetime import datetime
from typing import Optional, List

from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtGui import QClipboard, QImage
from sqlalchemy.orm import Session
from sqlalchemy import text
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

            logger.info(f"检测到剪贴板内容变化，类型: {content_type.value}")

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
                logger.info(f"内容已分类为: {category.name}")

            # 保存到数据库
            self.session.add(item)
            self.session.commit()
            logger.info("剪贴板内容已保存到数据库")

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
                # 保存图片到指定目录
                save_dir = 'clipboard_images'
                os.makedirs(save_dir, exist_ok=True)
                file_name = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                save_path = os.path.join(save_dir, file_name)
                image.save(save_path)
                return save_path, ContentType.IMAGE
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
            text_content = mime_data.text()
            if self._is_code(text_content):
                return text_content, ContentType.CODE
            return text_content, ContentType.TEXT

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
        # 根据内容类型进行分类
        type_based_categories = {
            ContentType.URL: 'URLs',
            ContentType.CODE: '代码片段',
            ContentType.IMAGE: '图片',
            ContentType.TEXT: '文本',
            ContentType.OTHER: '其他'
        }

        if content_type in type_based_categories:
            category_name = type_based_categories[content_type]
            category = self.session.query(Category).filter(Category.name == category_name).first()
            if not category:
                category = Category(name=category_name)
                self.session.add(category)
                self.session.commit()
            return category

        return None

    def get_history(self, limit: int = 50) -> List[ClipboardItem]:
        """获取剪贴板历史记录"""
        try:
            logger.info(f"获取最近 {limit} 条历史记录")
            result = self.session.query(ClipboardItem.id, ClipboardItem.content, ClipboardItem.content_type,
                                      ClipboardItem.created_at, ClipboardItem.device_id, ClipboardItem.category_id)\
                .order_by(ClipboardItem.id.desc())\
                .limit(limit)\
                .all()
            return [ClipboardItem(
                id=row.id,
                content=row.content,
                content_type=row.content_type,
                created_at=row.created_at,
                device_id=row.device_id,
                category_id=row.category_id
            ) for row in result]
        except Exception as e:
            logger.error(f"获取历史记录时出错: {str(e)}")
            return []

    def get_by_category(self, category_name: str) -> List[ClipboardItem]:
        """按分类获取剪贴板记录"""
        try:
            # 先查询Category的ID
            category = self.session.query(Category.id)\
                .filter(Category.name == category_name)\
                .first()
            if not category:
                return []
            
            # 再查询关联的ClipboardItem
            result = self.session.query(ClipboardItem.id, ClipboardItem.content, ClipboardItem.content_type,
                                      ClipboardItem.created_at, ClipboardItem.device_id, ClipboardItem.category_id)\
                .filter(ClipboardItem.category_id == category.id)\
                .order_by(ClipboardItem.id.desc())\
                .all()
            return [ClipboardItem(
                id=row.id,
                content=row.content,
                content_type=row.content_type,
                created_at=row.created_at,
                device_id=row.device_id,
                category_id=row.category_id
            ) for row in result]
        except Exception as e:
            logger.error(f"按分类获取剪贴板记录时出错: {str(e)}")
            return []