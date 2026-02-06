#!/usr/bin/env python3
"""
数据库迁移脚本：添加终端尺寸字段
为 terminal_sessions 表添加 rows 和 cols 字段
"""

import sqlite3
import os

def migrate():
    db_path = os.path.join(os.path.dirname(__file__), 'terminal_sessions.db')
    
    if not os.path.exists(db_path):
        print(f"数据库文件不存在: {db_path}")
        print("首次运行时会自动创建，无需迁移")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 检查字段是否已存在
        cursor.execute("PRAGMA table_info(terminal_sessions)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'rows' not in columns:
            print("添加 rows 字段...")
            cursor.execute("ALTER TABLE terminal_sessions ADD COLUMN rows INTEGER DEFAULT 24")
            print("✓ rows 字段添加成功")
        else:
            print("rows 字段已存在，跳过")
        
        if 'cols' not in columns:
            print("添加 cols 字段...")
            cursor.execute("ALTER TABLE terminal_sessions ADD COLUMN cols INTEGER DEFAULT 80")
            print("✓ cols 字段添加成功")
        else:
            print("cols 字段已存在，跳过")
        
        conn.commit()
        print("\n迁移完成！")
        
    except Exception as e:
        print(f"迁移失败: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == '__main__':
    migrate()
