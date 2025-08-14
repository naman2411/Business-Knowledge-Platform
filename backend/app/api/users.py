from fastapi import APIRouter, Depends
from bson import ObjectId
from app.api.deps import get_current_user
from app.core.db import get_db
from app.schemas.user import UserUpdate
router = APIRouter()
@router.get("/me")
async def me(user=Depends(get_current_user)):
    return user
@router.patch("/me")
async def update_me(body: UserUpdate, user=Depends(get_current_user)):
    db = get_db()
    update = {}
    if body.full_name is not None:
        update["full_name"] = body.full_name
    if body.settings is not None:
        update["settings"] = body.settings
    if update:
        await db.users.update_one({"_id": ObjectId(user["id"])}, {"$set": update})
    u = await db.users.find_one({"_id": ObjectId(user["id"])})
    return {"id": user["id"], "email": u["email"], "full_name": u.get("full_name"), "settings": u.get("settings", {})}
