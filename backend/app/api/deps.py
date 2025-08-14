from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from bson import ObjectId
from app.core.db import get_db
from app.core.security import decode_token
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")
async def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    user_id = decode_token(token)
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    db = get_db()
    u = await db.users.find_one({"_id": ObjectId(user_id)})
    if not u:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return {"id": str(u["_id"]), "email": u["email"], "full_name": u.get("full_name")}
async def get_current_user_optional(token: str = Depends(oauth2_scheme)) -> dict | None:
    try:
        return await get_current_user(token)
    except Exception:
        return None
