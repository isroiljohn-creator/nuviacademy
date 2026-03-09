import os
import jwt
from datetime import datetime, timedelta
from fastapi import HTTPException, Header
from typing import Optional

SECRET_KEY = os.getenv("JWT_SECRET")
if not SECRET_KEY:
    # Only raise error if we are NOT in a CI/Build environment (optional, but good for build stages)
    # For strict security as requested:
    print("❌ CRITICAL: JWT_SECRET is missing! Application cannot start securely.")
    raise RuntimeError("JWT_SECRET is required environment variable.")

ALGORITHM = "HS256"

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=7)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

async def get_current_user(authorization: Optional[str] = Header(None)):
    if not authorization:
        print("❌ Auth Failed: No Authorization header")
        raise HTTPException(status_code=401, detail="Authorization header required")
    
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            print(f"❌ Auth Failed: Invalid scheme {scheme}")
            raise HTTPException(status_code=401, detail="Invalid authentication scheme")
        
        payload = verify_token(token)
        return payload
    except ValueError:
        print("❌ Auth Failed: ValueError splitting header")
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    except Exception as e:
        print(f"❌ Auth Failed: {e}")
        raise e
