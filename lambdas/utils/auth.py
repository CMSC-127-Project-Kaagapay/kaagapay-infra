from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt as pyjwt
from jwt import PyJWK
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
    token = credentials.credentials.strip('"')
    # Read the secret here to ensure dotenv has already been loaded by the app
    secret = os.getenv("SUPABASE_JWT_SECRET", "your-super-secret-jwt-token-with-at-least-32-characters-long")
    try:
        # Official Supabase Public Key for ES256 verification (from JWKS endpoint)
        SUPABASE_JWK_DATA = {
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

        # Determine algorithm from token header
        header = pyjwt.get_unverified_header(token)
        alg = header.get("alg")

        if alg == "ES256":
            # Use PyJWK to construct the key from the JWK data
            jwk_key = PyJWK(SUPABASE_JWK_DATA)
            payload = pyjwt.decode(
                token,
                jwk_key.key,
                algorithms=["ES256"],
                options={"verify_aud": False}
            )
        else:
            # Fallback to HS256 with the JWT secret
            payload = pyjwt.decode(
                token,
                secret,
                algorithms=["HS256"],
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
    except pyjwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except pyjwt.InvalidTokenError as e:
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

