from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError
from passlib.context import CryptContext
from models import User, UserRole, UserStatus
from schemas.user import UserCreate, UserRead, UserUpdate

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


async def create_user(session: AsyncSession, user_in: UserCreate) -> User:
    user_dict: dict = {
        **user_in.model_dump(),
        "hashed_password": get_password_hash(user_in.password),
    }
    user_dict.pop("password")
    user = User(**user_dict)

    session.add(user)
    try:
        await session.commit()
        await session.refresh(user)
        return user
    except IntegrityError:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username or Email already exists!",
        )


async def get_user_by_id(session: AsyncSession, user_id: int) -> User | None:
    result = await session.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def get_user_by_username(session: AsyncSession, username: str) -> User | None:
    result = await session.execute(select(User).where(User.username == username))
    return result.scalar_one_or_none()


async def update_user_details(
    session: AsyncSession, user_id: int, user_in: UserUpdate, current_user: User
) -> User:
    user = await get_user_by_id(session, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    # Only owner or admin can update
    if current_user.id != user_id and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized"
        )
    # Prevent role escalation to admin
    data = user_in.model_dump(exclude_unset=True)
    # if "role" in data:
    #     raise HTTPException(
    #         status_code=status.HTTP_403_FORBIDDEN,
    #         detail="You are not allowed to set role",
    #     )
    if "password" in data and data["password"]:
        data["hashed_password"] = get_password_hash(data.pop("password"))
    for key, value in data.items():
        setattr(user, key, value)
    try:
        await session.commit()
        await session.refresh(user)
        return user
    except IntegrityError:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username or Email already exists!",
        )


def user_read_safe(user: User, current_user: User) -> UserRead:
    user_copy = user
    # Ẩn email nếu không phải chính chủ hoặc admin
    if current_user.id != user.id and current_user.role != UserRole.ADMIN:
        user_copy.email = None
    return UserRead.model_validate(user_copy)


async def delete_user(session: AsyncSession, user: User, current_user: User):
    if current_user.id != user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized"
        )
    await session.delete(user)
    await session.commit()


async def anonymize_user(session: AsyncSession, user: User, current_user: User):
    if current_user.id != user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized"
        )
    user.username = f"anonymous_{user.id}"
    user.email = None
    user.hashed_password = None
    user.status = UserStatus.ANONYMIZED
    await session.commit()
    await session.refresh(user)
    return user
