from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from backend.app.database import get_db
from backend.app.core.dependencies import require_supervisor, require_viewer
from backend.app.models.product import Product, Category
from backend.app.schemas.product import (
    ProductCreate, ProductUpdate, ProductOut,
    CategoryCreate, CategoryUpdate, CategoryOut
)
from typing import List

router = APIRouter()

# --- Categories ---
@router.post("/categories", response_model=CategoryOut, dependencies=[Depends(require_supervisor)])
async def create_category(cat_in: CategoryCreate, db: AsyncSession = Depends(get_db)):
    db_cat = Category(**cat_in.dict())
    db.add(db_cat)
    await db.commit()
    await db.refresh(db_cat)
    return db_cat

@router.get("/categories", response_model=List[CategoryOut], dependencies=[Depends(require_viewer)])
async def list_categories(db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(Category))
    return res.scalars().all()

# --- Products ---
@router.post("/", response_model=ProductOut, dependencies=[Depends(require_supervisor)])
async def create_product(prod_in: ProductCreate, db: AsyncSession = Depends(get_db)):
    # Check duplicate SKU
    exists = await db.execute(select(Product).filter(Product.sku == prod_in.sku))
    if exists.scalars().first():
        raise HTTPException(status_code=400, detail="Ya existe un producto con este SKU")
        
    db_prod = Product(**prod_in.dict())
    db.add(db_prod)
    await db.commit()
    await db.refresh(db_prod)
    
    # Reload with category relation
    res = await db.execute(
        select(Product)
        .options(selectinload(Product.category))
        .filter(Product.id == db_prod.id)
    )
    return res.scalars().first()

@router.get("/", response_model=List[ProductOut], dependencies=[Depends(require_viewer)])
async def list_products(db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(Product).options(selectinload(Product.category)))
    return res.scalars().all()

@router.get("/{product_id}", response_model=ProductOut, dependencies=[Depends(require_viewer)])
async def get_product(product_id: str, db: AsyncSession = Depends(get_db)):
    res = await db.execute(
        select(Product)
        .options(selectinload(Product.category))
        .filter(Product.id == product_id)
    )
    prod = res.scalars().first()
    if not prod:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return prod

@router.put("/{product_id}", response_model=ProductOut, dependencies=[Depends(require_supervisor)])
async def update_product(product_id: str, prod_in: ProductUpdate, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(Product).filter(Product.id == product_id))
    prod = res.scalars().first()
    if not prod:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
        
    for field, val in prod_in.dict(exclude_unset=True).items():
        setattr(prod, field, val)
        
    await db.commit()
    
    # Reload
    res = await db.execute(
        select(Product)
        .options(selectinload(Product.category))
        .filter(Product.id == product_id)
    )
    return res.scalars().first()
