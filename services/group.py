from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError

from models import Group, GroupRole, User, UserRole
from schemas.group import GroupCreate, GroupUpdate

async def create_group(
    session: AsyncSession, group_in: GroupCreate, current_user: User
) -> Group:
    if not (current_user.role == UserRole.ADMIN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized"
        )
    group = Group(**group_in.model_dump())
    session.add(group)
    await session.flush()  # Để group có id trước khi update user

    # Gán user làm leader group mới tạo
    current_user.group_id = group.id
    current_user.group_role = GroupRole.LEADER

    try:
        await session.commit()
        await session.refresh(group)
        return group
    except IntegrityError:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Group name already exists."
        )

async def get_group_by_id(session: AsyncSession, group_id: int) -> Group | None:
    result = await session.execute(select(Group).where(Group.id == group_id))
    return result.scalar_one_or_none()

async def list_groups(
    session: AsyncSession, skip: int = 0, limit: int = 20
) -> list[Group]:
    result = await session.execute(select(Group).offset(skip).limit(limit))
    return result.scalars().all()

async def update_group(
    session: AsyncSession, group: Group, group_in: GroupUpdate, current_user: User
) -> Group:
    if not (
        current_user.role == UserRole.ADMIN
        or (
            current_user.group_id == group.id
            and current_user.group_role == GroupRole.LEADER
        )
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized"
        )
    data = group_in.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(group, key, value)
    await session.commit()
    await session.refresh(group)
    return group

async def delete_group(session: AsyncSession, group: Group, current_user: User):
    if not (
        current_user.role == UserRole.ADMIN
        or (
            current_user.group_id == group.id
            and current_user.group_role == GroupRole.LEADER
        )
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized"
        )
    await session.delete(group)
    await session.commit()


async def add_member_to_group(
    session: AsyncSession,
    group: Group,
    user: User,
    current_user: User
) -> User:
    # Chỉ admin hoặc leader group này mới được add member
    if not (
        current_user.role == UserRole.ADMIN or
        (current_user.group_id == group.id and current_user.group_role == GroupRole.LEADER)
    ):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    
    # Kiểm tra user đã là member group khác chưa
    if user.group_id is not None and user.group_id != group.id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User already belongs to another group"
        )

    # Gán user vào group, set role là member
    user.group_id = group.id
    user.group_role = GroupRole.MEMBER
    await session.commit()
    await session.refresh(user)
    return user