from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.config import settings
from backend.app.database import engine, Base
from backend.app.api import auth, users, warehouses, products, inventory, reception, orders, dispatch, dashboard, alerts
from backend.app.seeds.seed_data import seed_all

app = FastAPI(
    title=settings.APP_NAME,
    description="Plataforma SaaS inteligente para gestión de almacenes (WMS)",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routers
app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["Autenticación"])
app.include_router(users.router, prefix=f"{settings.API_V1_STR}/users", tags=["Usuarios"])
app.include_router(warehouses.router, prefix=f"{settings.API_V1_STR}/warehouses", tags=["Bodegas y Ubicaciones"])
app.include_router(products.router, prefix=f"{settings.API_V1_STR}/products", tags=["Productos y Categorías"])
app.include_router(inventory.router, prefix=f"{settings.API_V1_STR}/inventory", tags=["Inventario y Stock"])
app.include_router(reception.router, prefix=f"{settings.API_V1_STR}/reception", tags=["Recepción de Mercadería"])
app.include_router(orders.router, prefix=f"{settings.API_V1_STR}/orders", tags=["Preparación de Pedidos (Picking)"])
app.include_router(dispatch.router, prefix=f"{settings.API_V1_STR}/dispatch", tags=["Despacho y Salidas"])
app.include_router(dashboard.router, prefix=f"{settings.API_V1_STR}/dashboard", tags=["KPIs y Dashboard"])
app.include_router(alerts.router, prefix=f"{settings.API_V1_STR}/alerts", tags=["Alertas Inteligentes"])

# Startup Event: Initialize database & run seed data
@app.on_event("startup")
async def startup_event():
    # 1. Create tables automatically on startup (perfect for zero-setup demo)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # 2. Run seeds
    await seed_all()

@app.get("/")
def read_root():
    return {"message": "Bienvenido a la API de SmartWMS AI", "docs": "/docs"}
