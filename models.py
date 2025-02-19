from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from enum import Enum

Base = declarative_base()

class ContentType(Enum):
    TEXT = 'text'
    CODE = 'code'
    URL = 'url'
    IMAGE = 'image'
    OTHER = 'other'

class Category(Base):
    __tablename__ = 'categories'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False)
    description = Column(String(200))
    items = relationship('ClipboardItem', back_populates='category', lazy='dynamic')

class ClipboardItem(Base):
    __tablename__ = 'clipboard_items'
    
    id = Column(Integer, primary_key=True)
    content = Column(String, nullable=False)
    content_type = Column(SQLEnum(ContentType), nullable=False)
    created_at = Column(DateTime, default=datetime.now)
    device_id = Column(String(36), nullable=False)
    category_id = Column(Integer, ForeignKey('categories.id'))
    category = relationship('Category', back_populates='items', lazy='joined')

def init_db(url):
    engine = create_engine(url)
    Base.metadata.create_all(engine)
    return engine