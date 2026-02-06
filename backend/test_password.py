#!/usr/bin/env python3
"""测试密码哈希和验证"""

import sys
sys.path.insert(0, '.')

from app.core.security import get_password_hash, verify_password

# 生成新的密码哈希
password = "admin123"
new_hash = get_password_hash(password)

print("=" * 60)
print("密码哈希生成器")
print("=" * 60)
print(f"原始密码: {password}")
print(f"生成哈希: {new_hash}")
print()

# 测试验证
print("验证测试:")
print(f"验证 'admin123': {verify_password('admin123', new_hash)}")
print(f"验证 'wrong': {verify_password('wrong', new_hash)}")
print()

# 测试现有哈希
existing_hash = "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYIq8B8hX3S"
print(f"测试现有哈希: {existing_hash}")
print(f"验证结果: {verify_password('admin123', existing_hash)}")
print()

print("请将上面生成的新哈希复制到 backend/app/models/user.py 中")
