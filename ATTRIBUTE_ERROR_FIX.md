# AttributeError 修复

## 问题
```
AttributeError: 'TerminalSession' object has no attribute 'db'
```

## 原因
在修改代码时，移除了 `self.db` 属性，但在 `_save_buffer_to_db()` 方法开头还保留了旧的检查：
```python
if not self.db:  # ❌ self.db 已经不存在
    return
```

## 修复
删除了这个检查，因为新的实现不再需要它：

```python
def _save_buffer_to_db(self):
    """保存缓冲区到数据库 - 线程安全版本"""
    # 直接开始，不检查 self.db
    try:
        from ..db.database import SessionLocal
        db = SessionLocal()
        # ...
```

## 状态
✅ 已修复

## 测试
```bash
# 重启服务
./start.sh

# 创建终端会话
# 应该不再有 AttributeError
```
