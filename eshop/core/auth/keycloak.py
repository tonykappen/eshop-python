"""Keycloak authentication service."""

import logging
from typing import Any, Dict, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from keycloak import KeycloakOpenID
from pydantic import BaseModel

from eshop.config.settings import settings

logger = logging.getLogger(__name__)

# Security scheme
security = HTTPBearer()


class KeycloakUser(BaseModel):
    """Keycloak user model."""
    sub: str
    email: Optional[str] = None
    name: Optional[str] = None
    preferred_username: Optional[str] = None
    roles: list[str] = []


class KeycloakService:
    """Keycloak authentication service."""

    def __init__(self):
        """Initialize Keycloak service."""
        self._keycloak_openid = None
        self._public_key = None

    @property
    def keycloak_openid(self):
        """Lazy load Keycloak OpenID client."""
        if self._keycloak_openid is None:
            self._keycloak_openid = KeycloakOpenID(
                server_url=settings.keycloak_server_url,
                client_id=settings.keycloak_client_id,
                realm_name=settings.keycloak_realm,
                client_secret_key=settings.keycloak_client_secret,
                verify=True,
            )
        return self._keycloak_openid

    @property
    def public_key(self):
        """Lazy load public key."""
        if self._public_key is None:
            try:
                self._public_key = self.keycloak_openid.public_key()
            except Exception as e:
                logger.warning(f"Failed to load Keycloak public key: {e}")
                self._public_key = None
        return self._public_key

    async def verify_token(self, token: str) -> Dict[str, Any]:
        """Verify JWT token with Keycloak."""
        try:
            # Decode token
            token_info = self.keycloak_openid.decode_token(
                token,
                key=self.public_key,
                options={
                    "verify_signature": True,
                    "verify_aud": False,
                    "verify_exp": True,
                },
            )
            return token_info
        except Exception as e:
            logger.error(f"Token verification failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
                headers={"WWW-Authenticate": "Bearer"},
            )

    async def get_user_info(self, token: str) -> KeycloakUser:
        """Get user information from token."""
        token_info = await self.verify_token(token)
        
        # Extract user information
        user = KeycloakUser(
            sub=token_info.get("sub", ""),
            email=token_info.get("email"),
            name=token_info.get("name"),
            preferred_username=token_info.get("preferred_username"),
            roles=token_info.get("realm_access", {}).get("roles", [])
        )
        
        return user

    async def check_role(self, user: KeycloakUser, required_role: str) -> bool:
        """Check if user has required role."""
        return required_role in user.roles

    async def health_check(self) -> Dict[str, Any]:
        """Check Keycloak service health."""
        try:
            # Try to get public key to verify connection
            if self.public_key is None:
                raise Exception("Unable to load public key")
            return {
                "status": "healthy",
                "service": "keycloak",
                "realm": settings.keycloak_realm,
                "server_url": settings.keycloak_server_url,
            }
        except Exception as e:
            logger.error(f"Keycloak health check failed: {e}")
            return {
                "status": "unhealthy",
                "service": "keycloak",
                "error": str(e),
            }


# Global instance
keycloak_service = KeycloakService()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> KeycloakUser:
    """Get current authenticated user."""
    return await keycloak_service.get_user_info(credentials.credentials)


async def require_role(required_role: str):
    """Dependency to require specific role."""
    async def role_checker(current_user: KeycloakUser = Depends(get_current_user)):
        has_role = await keycloak_service.check_role(current_user, required_role)
        if not has_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{required_role}' required",
            )
        return current_user
    return role_checker 