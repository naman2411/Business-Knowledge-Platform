from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.db import get_db
from fastapi.openapi.utils import get_openapi
from app.api import health, documents, auth, chat
app = FastAPI(title="Business Knowledge Platform", version="0.2.0")
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    schema = get_openapi(
        title=app.title,
        version="0.1.0",
        description="Business Knowledge Platform (Mongo + Chroma)",
        routes=app.routes,
    )
    schema.setdefault("components", {}).setdefault("securitySchemes", {})["bearerAuth"] = {
        "type": "http",
        "scheme": "bearer",
        "bearerFormat": "JWT",
    }
    schema["security"] = [{"bearerAuth": []}]
    app.openapi_schema = schema
    return schema

app.openapi = custom_openapi

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Routers
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(documents.router, prefix="/api/documents", tags=["documents"])
app.include_router(chat.router, prefix="/api", tags=["chat"])
app.include_router(health.router, prefix="/api", tags=["health"])
@app.on_event("startup")
async def startup():
    db = get_db()
    await db.users.create_index("email", unique=True)
    await db.events.create_index([("created_at", 1)])
    await db.events.create_index([("type", 1)])
    await db.documents.create_index([("uploaded_at", -1)])
    await db.documents.create_index([("filename", "text")])
