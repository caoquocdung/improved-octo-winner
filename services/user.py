from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError
from passlib.context import CryptContext
from models import User, UserRole
from schemas.user import UserCreate, UserUpdate

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

async def create_user(session: AsyncSession, user_in: UserCreate) -> User:
    hashed_pw = get_password_hash(user_in.password)
    user = User(
        username=user_in.username,
        email=user_in.email,
        hashed_password=hashed_pw,
        role=UserRole.USER,
        is_active=True
    )
    session.add(user)
    try:
        await session.commit()
        await session.refresh(user)
        return user
    except IntegrityError:
        await session.rollback()
        raise ValueError("Username hoặc Email đã tồn tại!")

async def get_user_by_id(session: AsyncSession, user_id: int) -> User | None:
    result = await session.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()

async def get_user_by_username(session: AsyncSession, username: str) -> User | None:
    result = await session.execute(select(User).where(User.username == username))
    return result.scalar_one_or_none()

async def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

async def update_user_details(session: AsyncSession, user: User, user_in: UserUpdate) -> User:
    data = user_in.model_dump(exclude_unset=True)
    if "password" in data and data["password"]:
        data["hashed_password"] = get_password_hash(data.pop("password"))
    for key, value in data.items():
        setattr(user, key, value)
    await session.commit()
    await session.refresh(user)
    return user
