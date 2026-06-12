# SmartWMS AI - Sistema Inteligente de Gestión de Almacenes

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/tpotp/leonoxANTIGRAVITY)

SmartWMS AI es una plataforma SaaS moderna e inteligente diseñada para optimizar las operaciones de almacén (WMS) utilizando algoritmos avanzados de inteligencia artificial.

## 🚀 Arquitectura del Proyecto

El proyecto está estructurado como un monorepositorio con dos componentes principales:

1. **Backend (`/backend`)**:
   - **Framework**: FastAPI (Python 3.10+)
   - **Base de Datos**: SQLAlchemy (con soporte para SQLite en desarrollo y PostgreSQL en producción)
   - **Características**: Autenticación JWT, gestión de inventario, optimización de picking (preparación de pedidos), recepción de mercadería, alertas inteligentes y analíticas.

2. **Frontend (`/frontend`)**:
   - **Framework**: React 19 + Vite + TailwindCSS / Ant Design
   - **Gestión de Estado**: Zustand
   - **Gráficos**: Recharts
   - **Características**: Dashboard interactivo con KPIs en tiempo real, mapas visuales de bodegas, control de stock y panel de alertas.

---

## 🛠️ Instalación y Desarrollo Local

### 1. Requisitos Previos
- Python 3.10 o superior
- Node.js 18 o superior
- Git

### 2. Configurar el Backend
```bash
# Entrar al directorio del backend
cd backend

# Crear un entorno virtual
python -m venv env

# Activar el entorno virtual
# En Windows:
env\Scripts\activate
# En macOS/Linux:
source env/bin/activate

# Instalar dependencias
pip install -r requirements.txt

# Iniciar el servidor de desarrollo
uvicorn app.main:app --reload
```
La API estará disponible en `http://localhost:8000`. La documentación interactiva (Swagger UI) se puede acceder en `http://localhost:8000/docs`.

### 3. Configurar el Frontend
```bash
# Entrar al directorio del frontend
cd frontend

# Instalar dependencias
npm install

# Iniciar el servidor de desarrollo
npm run dev
```
El cliente web estará disponible en `http://localhost:5173`.

---

## ☁️ Despliegue en Render (Un Clic)

Este repositorio está configurado como un **Render Blueprint**. Para desplegar toda la infraestructura (API Backend + Sitio Estático Frontend) de forma automática:

1. Haz clic en el siguiente botón:
   [![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/tpotp/leonoxANTIGRAVITY)
2. Inicia sesión en tu cuenta de Render (si aún no lo has hecho).
3. Ingresa un nombre para el grupo de servicios si es requerido y haz clic en **Apply**.
4. Render creará y enlazará automáticamente:
   - **Backend Web Service**: Hospeda la API FastAPI y genera automáticamente la base de datos y semillas.
   - **Frontend Static Site**: Compila y sirve la app React, configurando las rutas SPA y enlazando dinámicamente la URL del backend.

---

## 🔒 Variables de Entorno (Render Blueprint)
El despliegue autoconfigura las siguientes variables:
- `VITE_API_URL`: Enlazada automáticamente al servicio del Backend.
- `SECRET_KEY`: Generada de forma segura para las firmas JWT.
- `DATABASE_URL`: Por defecto utiliza SQLite persistente para la demostración, ampliable a PostgreSQL.
