import bcrypt

password = "admin123"
hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
print(f"Password: {password}")
print(f"Hash: {hashed.decode('utf-8')}")

# 验证
is_valid = bcrypt.checkpw(password.encode('utf-8'), hashed)
print(f"Verification: {is_valid}")
