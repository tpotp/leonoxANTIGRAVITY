import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.models.user import User, Role
from backend.app.models.warehouse import Warehouse, Zone, Location
from backend.app.models.product import Category, Product
from backend.app.models.inventory import Stock
from backend.app.core.security import get_password_hash
import uuid

async def create_auth_headers(client: AsyncClient, db: AsyncSession) -> dict:
    # Set up test admin user in DB
    email = f"wmsadmin_{str(uuid.uuid4())[:6]}@smartwms.com"
    hashed = get_password_hash("adminpwd")
    admin = User(email=email, hashed_password=hashed, full_name="Admin Test", is_superuser=True)
    db.add(admin)
    await db.commit()
    await db.refresh(admin)
    
    # Login to get token
    res = await client.post("/api/v1/auth/login", data={"username": email, "password": "adminpwd"})
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

@pytest.mark.asyncio
async def test_wms_workflow(client: AsyncClient, db: AsyncSession):
    headers = await create_auth_headers(client, db)
    
    # 1. Create Warehouse
    wh_data = {"name": "Test Warehouse", "code": "T-WH", "address": "123 Test St"}
    response = await client.post("/api/v1/warehouses/", json=wh_data, headers=headers)
    assert response.status_code == 200
    wh_id = response.json()["id"]
    
    # 2. Create Zone
    zone_data = {"warehouse_id": wh_id, "name": "Storage Zone", "code": "Z-STO", "zone_type": "STORAGE"}
    response = await client.post("/api/v1/warehouses/zones", json=zone_data, headers=headers)
    assert response.status_code == 200
    zone_id = response.json()["id"]
    
    # 3. Create Location
    loc_data = {
        "zone_id": zone_id,
        "warehouse_id": wh_id,
        "code": "LOC-A-01",
        "aisle": "A",
        "rack": "01",
        "level": "01",
        "position": "01",
        "max_weight": 1000.0,
        "max_volume": 10.0
    }
    response = await client.post("/api/v1/warehouses/locations", json=loc_data, headers=headers)
    assert response.status_code == 200
    loc_id = response.json()["id"]
    
    # 4. Create Category
    cat_data = {"name": "Test Category", "description": "Category for testing"}
    response = await client.post("/api/v1/products/categories", json=cat_data, headers=headers)
    assert response.status_code == 200
    cat_id = response.json()["id"]
    
    # 5. Create Product
    prod_data = {
        "sku": "TEST-SKU-01",
        "name": "Test Product",
        "description": "Product description",
        "category_id": cat_id,
        "barcode": "1234567890",
        "unit_of_measure": "UNIDAD",
        "weight": 1.5,
        "volume": 0.002,
        "min_stock": 5.0,
        "max_stock": 50.0,
        "reorder_point": 10.0
    }
    response = await client.post("/api/v1/products/", json=prod_data, headers=headers)
    assert response.status_code == 200
    prod_id = response.json()["id"]
    
    # 6. Adjust Stock (Positive)
    adjust_data = {
        "product_id": prod_id,
        "location_id": loc_id,
        "new_quantity": 20.0,
        "notes": "Initial test load"
    }
    response = await client.post("/api/v1/inventory/adjust", json=adjust_data, headers=headers)
    assert response.status_code == 200
    stock_data = response.json()
    assert stock_data["quantity"] == 20.0
    
    # Verify stock levels get endpoint
    response = await client.get(f"/api/v1/inventory/stock?product_id={prod_id}&warehouse_id={wh_id}", headers=headers)
    assert response.status_code == 200
    stocks = response.json()
    assert len(stocks) == 1
    assert stocks[0]["quantity"] == 20.0
