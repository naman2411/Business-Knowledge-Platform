from fastapi import APIRouter, HTTPException, status
from bson import ObjectId
from app.core.db import get_db
from app.core.security import hash_password, verify_password, create_access_token
from app.schemas.user import UserCreate, UserLogin
router = APIRouter()
@router.post("/register")
async def register(body: UserCreate):
    db = get_db()
    exists = await db.users.find_one({"email": body.email.lower()})
    if exists:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    doc = {
        "email": body.email.lower(),
        "password_hash": hash_password(body.password),
        "full_name": body.full_name,
        "settings": {},
    }
    res = await db.users.insert_one(doc)
    uid = str(res.inserted_id)
    token = create_access_token(uid)
    return {"access_token": token, "token_type": "bearer", "user": {"id": uid, "email": doc["email"], "full_name": doc.get("full_name")}}
@router.post("/login")
async def login(body: UserLogin):
    db = get_db()
    u = await db.users.find_one({"email": body.email.lower()})
    if not u or not verify_password(body.password, u["password_hash"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    token = create_access_token(str(u["_id"]))
    return {"access_token": token, "token_type": "bearer", "user": {"id": str(u["_id"]), "email": u["email"], "full_name": u.get("full_name")}}
