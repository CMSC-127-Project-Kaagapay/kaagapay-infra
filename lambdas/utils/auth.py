from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from sqlalchemy.orm import Session
import os
from pydantic import BaseModel
from typing import Optional
import uuid

from db import get_db
from repositories.adminRepository import AdminRepository

ALGORITHM = "HS256"

security = HTTPBearer()


class TokenData(BaseModel):
    user_id: Optional[uuid.UUID] = None

def get_current_user_id(credentials: HTTPAuthorizationCredentials = Depends(security)) -> uuid.UUID:
    token = credentials.credentials
    # Read the secret here to ensure dotenv has already been loaded by the app
    secret = os.getenv("SUPABASE_JWT_SECRET", "your-super-secret-jwt-token-with-at-least-32-characters-long")
    try:
        # Official Supabase Public Key for ES256 verification
        SUPABASE_JWK = {
            "alg": "ES256",
            "crv": "P-256",
            "ext": True,
            "key_ops": ["verify"],
            "kid": "1bb6da13-fb69-4f1f-a8e8-c54a84557247",
            "kty": "EC",
            "use": "sig",
            "x": "l3R5to18f1gC0_bVfgNYXGJB46MtCgBYdfx_PaOmnT4",
            "y": "JMWZ9uXkcWitF6lGFUVKbChSQQ7uaG2zdRiKkCBkn64"
        }
        
        # If the token is ES256, use the JWK. If HS256, use the secret.
        header = jwt.get_unverified_header(token)
        key = SUPABASE_JWK if header.get("alg") == "ES256" else secret
        
        payload = jwt.decode(
            token, 
            key, 
            algorithms=["HS256", "ES256"], 
            options={"verify_aud": False}
        )
        user_id_str: str = payload.get("sub")
        if user_id_str is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials (sub missing)",
                headers={"WWW-Authenticate": "Bearer"},
            )
        try:
            user_id = uuid.UUID(user_id_str)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid user ID format in token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return user_id
    except JWTError as e:
        print(f"JWT Error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Could not validate credentials: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )

def get_current_admin(
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db)
) -> uuid.UUID:
    try:
        admin_repo = AdminRepository(db)
        admin = admin_repo.getAdminById(user_id)
        if not admin:
            print(f"Auth Error: User {user_id} is not in the admins table.")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: User is not an admin",
            )
        return user_id
    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"Auth Exception: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Admin auth failed: {e}"
        )

