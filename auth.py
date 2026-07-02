import os
from datetime import datetime, timedelta, timezone

from dotenv import load_dotenv
from fastapi import HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

load_dotenv()

SECRET_KEY = os.environ.get("JWT_SECRET", "westeros-default-secret-change-in-prod")
ALGORITHM = "HS256"
TOKEN_EXPIRE_HOURS = 10

ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "changeme")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()


def verify_admin(username: str, password: str) -> bool:
    """Check submitted credentials against env-stored admin creds."""
    username_ok = username == ADMIN_USERNAME
    # Support both plain-text password (for ease of setup) and bcrypt hash
    if ADMIN_PASSWORD.startswith("$2b$") or ADMIN_PASSWORD.startswith("$2a$"):
        password_ok = pwd_context.verify(password, ADMIN_PASSWORD)
    else:
        password_ok = password == ADMIN_PASSWORD
    return username_ok and password_ok


def create_access_token(username: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(hours=TOKEN_EXPIRE_HOURS)
    payload = {"sub": username, "exp": expire}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def get_current_admin(
    credentials: HTTPAuthorizationCredentials = Security(security),
) -> str:
    """FastAPI dependency — validates the Bearer JWT on protected routes."""
    try:
        payload = jwt.decode(
            credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM]
        )
        username: str = payload.get("sub")
        if not username:
            raise HTTPException(status_code=401, detail="Invalid token payload")
        return username
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token — please log in again")
