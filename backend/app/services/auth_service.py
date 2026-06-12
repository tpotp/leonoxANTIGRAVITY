from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import HTTPException, status
from backend.app.models.user import User, Role
from backend.app.schemas.user import UserCreate, UserUpdate
from backend.app.core.security import get_password_hash, verify_password, create_access_token
from typing import Optional, List

async def authenticate_user(db: AsyncSession, email: str, password: str) -> Optional[User]:
    result = await db.execute(select(User).filter(User.email == email))
    user = result.scalars().first()
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user

async def register_user(db: AsyncSession, user_in: UserCreate) -> User:
    # Check if exists
    result = await db.execute(select(User).filter(User.email == user_in.email))
    existing_user = result.scalars().first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El correo electrónico ya está registrado.",
        )
    
    hashed_password = get_password_hash(user_in.password)
    db_user = User(
        email=user_in.email,
        hashed_password=hashed_password,
        full_name=user_in.full_name,
        is_active=user_in.is_active,
    )
    db.add(db_user)
    await db.flush()
    
    # Assign default role (e.g. VIEWER or OPERADOR if no users exist, else VIEWER)
    result = await db.execute(select(Role).filter(Role.name == "VIEWER"))
    default_role = result.scalars().first()
    if default_role:
        db_user.roles.append(default_role)
        
    await db.commit()
    await db.refresh(db_user)
    return db_user

async def update_user(db: AsyncSession, user_id: str, user_in: UserUpdate) -> User:
    result = await db.execute(select(User).filter(User.id == user_id))
    db_user = result.scalars().first()
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado",
        )
    
    if user_in.email is not None:
        db_user.email = user_in.email
    if user_in.full_name is not None:
        db_user.full_name = user_in.full_name
    if user_in.is_active is not None:
        db_user.is_active = user_in.is_active
    if user_in.password is not None:
        db_user.hashed_password = get_password_hash(user_in.password)
        
    if user_in.role_ids is not None:
        # Clear existing
        db_user.roles = []
        for role_id in user_in.role_ids:
            role_result = await db.execute(select(Role).filter(Role.id == role_id))
            role = role_result.scalars().first()
            if role:
                db_user.roles.append(role)
                
    await db.commit()
    await db.refresh(db_user)
    return db_user
