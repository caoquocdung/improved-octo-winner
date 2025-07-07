from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from security import create_access_token, decode_access_token
from database import get_db
from models import User
from schemas.user import UserCreate, UserRead, UserUpdate
from services.user import (
    create_user, get_user_by_id, get_user_by_username,
    update_user_details, verify_password, user_read_safe, anonymize_user
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
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if user.status == "inactive":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is inactive")
    access_token = create_access_token({"sub": str(user.id)})
    return {"access_token": access_token, "token_type": "bearer"}

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/login")

async def get_current_user(token: str = Depends(oauth2_scheme), session: AsyncSession = Depends(get_db)):
    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    user = await get_user_by_id(session, int(payload["sub"]))
    if not user or user.status == "inactivee":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found or inactive")
    return user

@router.get("/me", response_model=UserRead)
async def read_me(current_user: User = Depends(get_current_user)):
    return current_user

@router.get("/{user_id}", response_model=UserRead)
async def get_user(
    user_id: int,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    user = await get_user_by_id(session, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user_read_safe(user, current_user)

@router.put("/{user_id}", response_model=UserRead)
async def update_user(
    user_id: int,
    user_in: UserUpdate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        updated_user = await update_user_details(session, user_id, user_in, current_user)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    return updated_user

@router.get("/by-username/{username}", response_model=UserRead)
async def get_user_by_username_route(
    username: str,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    user = await get_user_by_username(session, username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user_read_safe(user, current_user)

# @router.get("/by-email/{email}", response_model=UserRead)
# async def get_user_by_email_route(
#     email: str,
#     session: AsyncSession = Depends(get_db),
#     current_user: User = Depends(get_current_user)
# ):
#     user = await get_user_by_email(session, email)
#     if not user:
#         raise HTTPException(status_code=404, detail="User not found")
#     return user_read_safe(user, current_user)

@router.post("/{user_id}/anonymize", response_model=UserRead)
async def anonymize_user_route(
    user_id: int,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    user = await get_user_by_id(session, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    try:
        result = await anonymize_user(session, user, current_user)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    return result
