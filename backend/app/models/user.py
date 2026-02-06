from pydantic import BaseModel

class User(BaseModel):
    username: str
    hashed_password: str

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

# 模拟数据库 - 生产环境应使用真实数据库
FAKE_USERS_DB = {
    "admin": {
        "username": "admin",
        "hashed_password": "$2b$12$uosDjmfwSIh.wrGzjJGDjOb4XCIvn4HK/9JAP1OdoUfzyGMpxO71."  # admin123
    }
}
