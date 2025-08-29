from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer
import jwt
from pydantic import BaseModel

import os
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")

security = HTTPBearer()

class UserClaims(BaseModel):
    user_id: int
    email: str
    role: str | None = None

def get_current_user(token: str = Depends(security)) -> UserClaims:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id_str: str = payload.get("sub")
        email: str = payload.get("email")
        role: str = payload.get("role")
        
        user_id = int(user_id_str)

        return UserClaims(user_id=user_id, email=email, role=role)
    
    # Catch both JWT errors and int conversion errors
    except (jwt.PyJWTError, ValueError):
        raise credentials_exception
