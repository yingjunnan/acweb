from fastapi import APIRouter, HTTPException, status
from datetime import timedelta
from ..models.user import UserLogin, Token, FAKE_USERS_DB
from ..core.security import verify_password, create_access_token
from ..core.config import settings

router = APIRouter()

@router.post("/login", response_model=Token)
async def login(user_data: UserLogin):
    """用户登录"""
    print(f"Login attempt - username: {user_data.username}")
    
    user = FAKE_USERS_DB.get(user_data.username)
    if not user:
        print(f"User not found: {user_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    print(f"User found, verifying password...")
    print(f"Stored hash: {user['hashed_password']}")
    
    if not verify_password(user_data.password, user["hashed_password"]):
        print("Password verification failed")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    print("Password verified successfully")
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user_data.username}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}
