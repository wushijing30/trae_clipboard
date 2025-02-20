from sqlalchemy import create_engine, text
from models import init_db
from datetime import datetime

def migrate_add_last_accessed():
    """添加last_accessed字段到clipboard_items表"""
    # 连接到数据库
    engine = create_engine('sqlite:///clipboards.db')
    
    with engine.connect() as conn:
        # 检查是否已存在last_accessed字段
        result = conn.execute(text("""SELECT name FROM pragma_table_info('clipboard_items') WHERE name='last_accessed'"""))
        if not result.fetchone():
            # 添加last_accessed字段，不设置默认值
            conn.execute(text("""ALTER TABLE clipboard_items ADD COLUMN last_accessed DATETIME"""))
            # 更新现有记录的last_accessed为当前时间
            conn.execute(text("""UPDATE clipboard_items SET last_accessed = CURRENT_TIMESTAMP"""))
            conn.commit()
            print("成功添加last_accessed字段")
        else:
            print("last_accessed字段已存在")

def migrate_add_is_pinned():
    """添加is_pinned字段到clipboard_items表"""
    # 连接到数据库
    engine = create_engine('sqlite:///clipboards.db')
    
    with engine.connect() as conn:
        # 检查是否已存在is_pinned字段
        result = conn.execute(text("""SELECT name FROM pragma_table_info('clipboard_items') WHERE name='is_pinned'"""))
        if not result.fetchone():
            # 添加is_pinned字段
            conn.execute(text("""ALTER TABLE clipboard_items ADD COLUMN is_pinned INTEGER DEFAULT 0 NOT NULL"""))
            conn.commit()
            print("成功添加is_pinned字段")
        else:
            print("is_pinned字段已存在")

if __name__ == '__main__':
    #migrate_add_is_pinned()
    migrate_add_last_accessed()