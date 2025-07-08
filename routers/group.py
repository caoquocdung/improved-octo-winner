from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
from models import User, UserRole
from routers.user import get_current_user
from schemas.group import GroupCreate, GroupRead, GroupUpdate
from services.group import (
    create_group,
    get_group_by_id,
    list_groups,
    update_group,
    delete_group,
)


router = APIRouter(prefix="/groups", tags=["groups"])


@router.post("/", response_model=GroupRead)
async def create_group_api(
    group_in: GroupCreate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        group = await create_group(session, group_in, current_user)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return group


@router.get("/", response_model=list[GroupRead])
async def list_groups_api(
    skip: int = 0, limit: int = 20, session: AsyncSession = Depends(get_db)
):
    return await list_groups(session, skip=skip, limit=limit)


@router.get("/{group_id}", response_model=GroupRead)
async def get_group_api(group_id: int, session: AsyncSession = Depends(get_db)):
    group = await get_group_by_id(session, group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    return group


@router.put("/{group_id}", response_model=GroupRead)
async def update_group_api(
    group_id: int, group_in: GroupUpdate, session: AsyncSession = Depends(get_db)
):
    group = await get_group_by_id(session, group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    updated_group = await update_group(session, group, group_in)
    return updated_group


@router.delete("/{group_id}")
async def delete_group_api(group_id: int, session: AsyncSession = Depends(get_db)):
    group = await get_group_by_id(session, group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    await delete_group(session, group)
    return {"detail": "Group deleted"}
