from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from backend.app.database import get_db
from backend.app.core.dependencies import get_current_user, require_admin
from backend.app.models.user import User, Role
from backend.app.schemas.user import UserOut, UserUpdate, RoleOut
from typing import List

router = APIRouter()

@router.get("/me", response_model=UserOut)
async def read_user_me(current_user: User = Depends(get_current_user)):
    return current_user

@router.get("/", response_model=List[UserOut], dependencies=[Depends(require_admin)])
async def read_users(
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 100
):
    res = await db.execute(select(User).offset(skip).limit(limit))
    return res.scalars().all()

@router.put("/{user_id}", response_model=UserOut, dependencies=[Depends(require_admin)])
async def update_user_by_id(
    user_id: str,
    user_in: UserUpdate,
    db: AsyncSession = Depends(get_db)
):
    from backend.app.services.auth_service import update_user
    return await update_user(db, user_id, user_in)

@router.get("/roles", response_model=List[RoleOut])
async def list_roles(db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(Role))
    return res.scalars().all()
