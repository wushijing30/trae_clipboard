from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, Enum, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import enum

Base = declarative_base()

class ContentType(enum.Enum):
    TEXT = "text"
    IMAGE = "image"
    FILE = "file"
    URL = "url"
    CODE = "code"
    OTHER = "other"

class ClipboardItem(Base):
    __tablename__ = 'clipboard_items'

    id = Column(Integer, primary_key=True)
    content = Column(Text, nullable=False)
    content_type = Column(Enum(ContentType), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    device_id = Column(String(50), nullable=False)
    category_id = Column(Integer, ForeignKey('categories.id'))
    
    # 关联到分类
    category = relationship("Category", back_populates="items")

class Category(Base):
    __tablename__ = 'categories'

    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    description = Column(String(200))
    
    # 关联到剪贴板项目
    items = relationship("ClipboardItem", back_populates="category")

def init_db(db_url):
    """初始化数据库"""
    engine = create_engine(db_url)
    Base.metadata.create_all(engine)
    return engine