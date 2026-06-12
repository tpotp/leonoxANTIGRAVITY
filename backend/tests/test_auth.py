import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.models.user import User

@pytest.mark.asyncio
async def test_register_and_login(client: AsyncClient, db: AsyncSession):
    # 1. Register User
    reg_data = {
        "email": "testuser@smartwms.com",
        "password": "testpassword123",
        "full_name": "Test User",
        "is_active": True
    }
    response = await client.post("/api/v1/auth/register", json=reg_data)
    assert response.status_code == 211 or response.status_code == 201
    user_data = response.json()
    assert user_data["email"] == "testuser@smartwms.com"
    assert "id" in user_data
    
    # 2. Login
    login_data = {
        "username": "testuser@smartwms.com",
        "password": "testpassword123"
    }
    # OAuth2 Form uses form-data encoding
    response = await client.post("/api/v1/auth/login", data=login_data)
    assert response.status_code == 200
    token_data = response.json()
    assert "access_token" in token_data
    assert token_data["token_type"] == "bearer"
