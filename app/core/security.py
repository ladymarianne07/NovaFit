import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from ..config import settings


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash using PBKDF2"""
    try:
        parts = hashed_password.split(':')
        if len(parts) != 2:
            return False
        
        stored_salt = bytes.fromhex(parts[0])
        stored_key = bytes.fromhex(parts[1])
        
        # Verificar con el mismo algoritmo
        key = hashlib.pbkdf2_hmac('sha256', plain_password.encode('utf-8'), stored_salt, 100000)
        return secrets.compare_digest(stored_key, key)
    except Exception:
        return False


def get_password_hash(password: str) -> str:
    """Hash password using PBKDF2 (más estable que bcrypt)"""
    # Generar salt único
    salt = secrets.token_bytes(32)
    # Hash con PBKDF2
    key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
    # Combinar salt + hash para almacenamiento
    return salt.hex() + ':' + key.hex()


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """Verify and decode JWT token"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None


def extract_user_id_from_token(token: str) -> Optional[int]:
    """Extract user ID from JWT token"""
    payload = verify_token(token)
    if payload is None:
        return None
    
    user_id = payload.get("sub")
    if user_id is None:
        return None
    
    try:
        return int(user_id)
    except (ValueError, TypeError):
        return None
    return None