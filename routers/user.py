from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
from models import User
from schemas.user import UserCreate, UserRead, UserUpdate
from services.user import (
    create_user, get_user_by_id, get_user_by_username,
    update_user_details, verify_password
)
from pydantic import BaseModel

router = APIRouter(prefix="/users", tags=["users"])

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

@router.post("/register", response_model=UserRead)
async def register(user_in: UserCreate, session: AsyncSession = Depends(get_db)):
    try:
        user = await create_user(session, user_in)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return user

@router.post("/login", response_model=TokenResponse)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: AsyncSession = Depends(get_db)
):
    user = await get_user_by_username(session, form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    access_token = "dummy_token"  # bạn sẽ dùng JWT thật ở đây
    return {"access_token": access_token, "token_type": "bearer"}

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/login")

async def get_current_user(token: str = Depends(oauth2_scheme)):
    # fake get user từ token, bạn sẽ làm JWT thật ở đây
    return None

@router.get("/{user_id}", response_model=UserRead)
async def get_user(user_id: int, session: AsyncSession = Depends(get_db)):
    user = await get_user_by_id(session, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.put("/{user_id}", response_model=UserRead)
async def update_user(user_id: int, user_in: UserUpdate, session: AsyncSession = Depends(get_db)):
    user = await get_user_by_id(session, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    updated_user = await update_user_details(session, user, user_in)
    return updated_user
