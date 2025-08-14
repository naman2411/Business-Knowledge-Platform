from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from passlib.context import CryptContext
from app.core.config import settings
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
ALGO = "HS256"
def hash_password(pw: str) -> str:
    return pwd_context.hash(pw)
def verify_password(pw: str, hashed: str) -> bool:
    return pwd_context.verify(pw, hashed)
def create_access_token(sub: str, minutes: int | None = None) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=minutes or settings.jwt_expire_minutes)
    to_encode = {"sub": sub, "exp": expire}
    return jwt.encode(to_encode, settings.jwt_secret, algorithm=ALGO)
def decode_token(token: str) -> str | None:
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[ALGO])
        return payload.get("sub")
    except JWTError:
        return None
