"""Shared security utilities for authentication and authorization."""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class TokenData(BaseModel):
    """JWT token payload data."""

    user_id: str
    email: str
    org_id: Optional[str] = None
    roles: list[str] = []
    scopes: list[str] = []


class SecurityManager:
    """Security manager for JWT and password operations."""

    def __init__(
        self,
        secret_key: str,
        algorithm: str = "HS256",
        access_token_expire_minutes: int = 30,
        refresh_token_expire_days: int = 7,
    ):
        """Initialize security manager.

        Args:
            secret_key: Secret key for JWT encoding
            algorithm: JWT algorithm
            access_token_expire_minutes: Access token expiration time
            refresh_token_expire_days: Refresh token expiration time
        """
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.access_token_expire_minutes = access_token_expire_minutes
        self.refresh_token_expire_days = refresh_token_expire_days

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash.

        Args:
            plain_password: Plain text password
            hashed_password: Hashed password

        Returns:
            bool: True if password matches
        """
        return pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str) -> str:
        """Hash a password.

        Args:
            password: Plain text password

        Returns:
            str: Hashed password
        """
        return pwd_context.hash(password)

    def create_access_token(
        self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None
    ) -> str:
        """Create JWT access token.

        Args:
            data: Token payload data
            expires_delta: Custom expiration time

        Returns:
            str: Encoded JWT token
        """
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)

        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "access"
        })

        encoded_jwt = jwt.encode(
            to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt

    def create_refresh_token(self, data: Dict[str, Any]) -> str:
        """Create JWT refresh token.

        Args:
            data: Token payload data

        Returns:
            str: Encoded JWT refresh token
        """
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=self.refresh_token_expire_days)

        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "refresh"
        })

        encoded_jwt = jwt.encode(
            to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt

    def decode_token(self, token: str) -> Optional[TokenData]:
        """Decode and verify JWT token.

        Args:
            token: JWT token string

        Returns:
            Optional[TokenData]: Decoded token data or None if invalid
        """
        try:
            payload = jwt.decode(token, self.secret_key,
                                 algorithms=[self.algorithm])
            return TokenData(
                user_id=payload.get("sub"),
                email=payload.get("email"),
                org_id=payload.get("org_id"),
                roles=payload.get("roles", []),
                scopes=payload.get("scopes", [])
            )
        except JWTError as e:
            logger.error(f"JWT decode error: {e}")
            return None

    def verify_api_key(self, api_key: str, stored_hash: str) -> bool:
        """Verify API key against stored hash.

        Args:
            api_key: Plain text API key
            stored_hash: Stored hash

        Returns:
            bool: True if API key is valid
        """
        return self.verify_password(api_key, stored_hash)
