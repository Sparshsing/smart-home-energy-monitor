import os
from contextlib import asynccontextmanager
from datetime import timedelta
from fastapi import FastAPI, Depends, HTTPException, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated

from database import init_db, get_session
from models.user_models import User, UserCreate, UserPublic, UserLogin
from security import generate_salt_and_hash, verify_password, create_access_token, decode_access_token
from config import settings

# Initialize debugpy for remote debugging when running in Docker
if os.getenv("ENABLE_DEBUGPY") == "true":
    import debugpy
    debugpy.listen(("0.0.0.0", 5678))
    print("Debugpy listening on port 5678. Ready for debugger to attach...")

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Creating tables...")
    await init_db()
    yield

app = FastAPI(lifespan=lifespan)
router = APIRouter(prefix="/auth")


# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Adjust for your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

DBSession = Annotated[AsyncSession, Depends(get_session)]

async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)], session: DBSession):
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    email = payload.get("sub")
    if email is None:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user = await session.exec(select(User).where(User.email == email))
    user = user.first()
    
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
        
    return user

@router.get("/health")
async def health_check():
    return {"status": "ok"}

@router.get("/")
async def root():
    return {"message": "Auth Service Running"}

@router.post("/register", response_model=UserPublic)
async def register_user(user_data: UserCreate, session: DBSession):
    user = await session.exec(select(User).where(User.email == user_data.email))
    if user.first():
        raise HTTPException(status_code=400, detail="Email already registered")

    salt, hashed_password = generate_salt_and_hash(user_data.password)
    
    new_user = User.model_validate(
        user_data,
        update={
            "salt": salt,
            "hashed_password": hashed_password
        }
    )
    
    session.add(new_user)
    await session.commit()
    await session.refresh(new_user)
    
    return new_user

@router.post("/login")
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()], 
    session: DBSession
):
    user = await session.exec(select(User).where(User.email == form_data.username))
    user = user.first()
    
    if not user or not verify_password(form_data.password, user.salt, user.hashed_password):
        raise HTTPException(
            status_code=401,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/users/me", response_model=UserPublic)
async def read_users_me(current_user: Annotated[User, Depends(get_current_user)]):
    return current_user

app.include_router(router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8001, reload=True)