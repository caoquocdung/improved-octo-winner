from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError
from passlib.context import CryptContext
from models import User, UserRole, UserStatus
from schemas.user import UserCreate, UserUpdate

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
        raise ValueError("Username hoặc Email đã tồn tại!")


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
        raise ValueError("User not found")
    # Phân quyền: chỉ chính chủ hoặc admin mới update
    if current_user.id != user_id and current_user.role != UserRole.ADMIN:
        raise PermissionError("Not authorized")
    # Không cho phép update role thành admin
    data = user_in.model_dump(exclude_unset=True)
    if "role" in data and data["role"] == UserRole.ADMIN:
        raise PermissionError("You are not allowed to set role as admin")
    if "password" in data and data["password"]:
        data["hashed_password"] = get_password_hash(data.pop("password"))
    for key, value in data.items():
        setattr(user, key, value)
    await session.commit()
    await session.refresh(user)
    return user


# Đảm bảo chỉ cho chính chủ hoặc admin đọc info đầy đủ, còn lại thì ẩn email
def user_read_safe(user: User, current_user: User) -> dict:
    base = {
        "id": user.id,
        "username": user.username,
        "role": user.role,
        "status": user.status,
        "created_at": user.created_at,
        "deleted_at": getattr(user, "deleted_at", None),
    }
    if (current_user.id == user.id or current_user.role == UserRole.ADMIN) and hasattr(
        user, "email"
    ):
        base["email"] = user.email
    else:
        base["email"] = None  # hoặc không trả field email cũng được
    return base


async def is_user_active(session: AsyncSession, user_id: int) -> bool:
    user = await get_user_by_id(session, user_id)
    return user.status if user else False


async def delete_user(session: AsyncSession, user: User):
    await session.delete(user)
    await session.commit()


async def anonymize_user(session: AsyncSession, user: User, current_user: User):
    # Chỉ admin hoặc chính chủ mới được anonymize
    if current_user.id != user.id and current_user.role != UserRole.ADMIN:
        raise PermissionError("Not authorized")
    user.username = f"anonymous_{user.id}"
    user.email = None
    user.hashed_password = None
    user.status = UserStatus.ANONYMIZED
    await session.commit()
    await session.refresh(user)
    return user
