"""Keycloak setup and configuration module."""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional

import httpx
from structlog import get_logger

from app.config.settings import settings

logger = get_logger(__name__)


class KeycloakSetup:
    """Handles Keycloak realm, client, roles, and user setup."""

    def __init__(self) -> None:
        """Initialize Keycloak setup."""
        self.base_url = settings.keycloak_server_url
        self.realm = settings.keycloak_realm
        self.client_id = settings.keycloak_client_id
        self.client_secret = settings.keycloak_client_secret
        self.admin_token: Optional[str] = None

    async def setup_keycloak(self) -> bool:
        """Complete Keycloak setup process."""
        try:
            logger.info("🔧 Starting Keycloak setup...")
            
            # Wait for Keycloak to be ready
            logger.info("⏳ Waiting for Keycloak to be ready...")
            await asyncio.sleep(10)  # Wait for Keycloak to fully start

            # Check if Keycloak is accessible
            if not await self._check_keycloak_accessible():
                logger.error("❌ Keycloak is not accessible")
                return False

            # Get admin token
            if not await self._get_admin_token():
                logger.error("❌ Failed to get admin token")
                return False

            # Create realm
            if not await self._create_realm():
                logger.warning("⚠️ Realm creation failed or already exists")

            # Create client
            if not await self._create_client():
                logger.warning("⚠️ Client creation failed or already exists")

            # Create roles
            if not await self._create_roles():
                logger.warning("⚠️ Role creation failed or already exists")

            # Create users
            if not await self._create_users():
                logger.warning("⚠️ User creation failed or already exists")

            # Setup role hierarchy
            await self._setup_role_hierarchy()

            # Verify setup
            await self._verify_setup()

            logger.info("✅ Keycloak setup completed successfully")
            return True

        except Exception as e:
            logger.error(f"❌ Keycloak setup failed: {e}")
            return False

    async def _check_keycloak_accessible(self) -> bool:
        """Check if Keycloak is accessible."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/")
                # Keycloak returns 302 (redirect) or 200 (OK) when accessible
                if response.status_code in [200, 302]:
                    logger.info("✅ Keycloak is accessible")
                    return True
                else:
                    logger.error(f"❌ Keycloak returned status code: {response.status_code}")
                    return False
        except Exception as e:
            logger.error(f"❌ Keycloak is not accessible: {e}")
            return False

    async def _get_admin_token(self) -> bool:
        """Get admin token from Keycloak."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/realms/master/protocol/openid-connect/token",
                    data={
                        "username": "admin",
                        "password": "admin",
                        "grant_type": "password",
                        "client_id": "admin-cli",
                    },
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                )
                response.raise_for_status()
                data = response.json()
                self.admin_token = data.get("access_token")
                if self.admin_token:
                    logger.info("✅ Admin token obtained")
                    return True
                else:
                    logger.error("❌ No access token in response")
                    return False
        except Exception as e:
            logger.error(f"❌ Failed to get admin token: {e}")
            return False

    async def _create_realm(self) -> bool:
        """Create the eShop realm."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/admin/realms",
                    headers={
                        "Authorization": f"Bearer {self.admin_token}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "realm": self.realm,
                        "enabled": True,
                        "displayName": "eShop Realm",
                    },
                )
                if response.status_code == 201:
                    logger.info(f"✅ Realm '{self.realm}' created")
                    return True
                elif response.status_code == 409:
                    logger.info(f"ℹ️ Realm '{self.realm}' already exists")
                    return True
                else:
                    logger.error(f"❌ Failed to create realm: {response.status_code}")
                    return False
        except Exception as e:
            logger.error(f"❌ Realm creation failed: {e}")
            return False

    async def _create_client(self) -> bool:
        """Create the eShop API client."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/admin/realms/{self.realm}/clients",
                    headers={
                        "Authorization": f"Bearer {self.admin_token}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "clientId": self.client_id,
                        "enabled": True,
                        "publicClient": False,
                        "clientAuthenticatorType": "client-secret",
                        "secret": self.client_secret,
                        "redirectUris": ["http://localhost:8000/*"],
                        "webOrigins": ["http://localhost:8000"],
                        "serviceAccountsEnabled": True,
                        "authorizationServicesEnabled": True,
                        "directAccessGrantsEnabled": True,
                        "standardFlowEnabled": True,
                    },
                )
                if response.status_code == 201:
                    logger.info(f"✅ Client '{self.client_id}' created")
                    return True
                elif response.status_code == 409:
                    logger.info(f"ℹ️ Client '{self.client_id}' already exists")
                    return True
                else:
                    logger.error(f"❌ Failed to create client: {response.status_code}")
                    return False
        except Exception as e:
            logger.error(f"❌ Client creation failed: {e}")
            return False

    async def _create_roles(self) -> bool:
        """Create RBAC roles."""
        roles = [
            {"name": "user", "description": "Basic user role - can read data"},
            {"name": "manager", "description": "Manager role - can read and write data"},
            {"name": "admin", "description": "Admin role - full access to all operations"},
        ]

        try:
            async with httpx.AsyncClient() as client:
                for role in roles:
                    response = await client.post(
                        f"{self.base_url}/admin/realms/{self.realm}/roles",
                        headers={
                            "Authorization": f"Bearer {self.admin_token}",
                            "Content-Type": "application/json",
                        },
                        json=role,
                    )
                    if response.status_code == 201:
                        logger.info(f"✅ Role '{role['name']}' created")
                    elif response.status_code == 409:
                        logger.info(f"ℹ️ Role '{role['name']}' already exists")
                    else:
                        logger.warning(f"⚠️ Failed to create role '{role['name']}': {response.status_code}")

            return True
        except Exception as e:
            logger.error(f"❌ Role creation failed: {e}")
            return False

    async def _create_users(self) -> bool:
        """Create test users with roles."""
        users = [
            ("adminuser", "admin"),
            ("manager", "manager"),
            ("user", "user"),
            ("testuser", "user"),
        ]

        try:
            async with httpx.AsyncClient() as client:
                for username, role in users:
                    # Create user
                    user_data = {
                        "username": username,
                        "email": f"{username}@example.com",
                        "enabled": True,
                        "emailVerified": True,
                        "firstName": f"{username.title()} Test",
                        "lastName": "User",
                        "credentials": [
                            {
                                "type": "password",
                                "value": "password",
                                "temporary": False,
                            }
                        ],
                    }

                    response = await client.post(
                        f"{self.base_url}/admin/realms/{self.realm}/users",
                        headers={
                            "Authorization": f"Bearer {self.admin_token}",
                            "Content-Type": "application/json",
                        },
                        json=user_data,
                    )

                    if response.status_code == 201:
                        logger.info(f"✅ User '{username}' created")
                    elif response.status_code == 409:
                        logger.info(f"ℹ️ User '{username}' already exists")
                        # Update password for existing user
                        await self._update_user_password(client, username)
                    else:
                        logger.warning(f"⚠️ Failed to create user '{username}': {response.status_code}")
                        continue

                    # Assign role to user
                    await self._assign_role_to_user(client, username, role)

            return True
        except Exception as e:
            logger.error(f"❌ User creation failed: {e}")
            return False

    async def _update_user_password(self, client: httpx.AsyncClient, username: str) -> None:
        """Update password for existing user."""
        try:
            # Get user ID
            response = await client.get(
                f"{self.base_url}/admin/realms/{self.realm}/users",
                headers={"Authorization": f"Bearer {self.admin_token}"},
                params={"username": username},
            )
            response.raise_for_status()
            users = response.json()
            if users:
                user_id = users[0]["id"]
                # Reset password
                password_response = await client.put(
                    f"{self.base_url}/admin/realms/{self.realm}/users/{user_id}/reset-password",
                    headers={
                        "Authorization": f"Bearer {self.admin_token}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "type": "password",
                        "value": "password",
                        "temporary": False,
                    },
                )
                if password_response.status_code == 204:
                    logger.info(f"✅ Password updated for user '{username}'")
        except Exception as e:
            logger.warning(f"⚠️ Failed to update password for '{username}': {e}")

    async def _assign_role_to_user(self, client: httpx.AsyncClient, username: str, role_name: str) -> None:
        """Assign role to user."""
        try:
            # Get user ID
            response = await client.get(
                f"{self.base_url}/admin/realms/{self.realm}/users",
                headers={"Authorization": f"Bearer {self.admin_token}"},
                params={"username": username},
            )
            response.raise_for_status()
            users = response.json()
            if not users:
                logger.warning(f"⚠️ User '{username}' not found for role assignment")
                return

            user_id = users[0]["id"]

            # Get role ID
            role_response = await client.get(
                f"{self.base_url}/admin/realms/{self.realm}/roles/{role_name}",
                headers={"Authorization": f"Bearer {self.admin_token}"},
            )
            role_response.raise_for_status()
            role_data = role_response.json()
            role_id = role_data["id"]

            # Assign role
            assign_response = await client.post(
                f"{self.base_url}/admin/realms/{self.realm}/users/{user_id}/role-mappings/realm",
                headers={
                    "Authorization": f"Bearer {self.admin_token}",
                    "Content-Type": "application/json",
                },
                json=[{"id": role_id, "name": role_name}],
            )

            if assign_response.status_code == 204:
                logger.info(f"✅ Role '{role_name}' assigned to user '{username}'")
            else:
                logger.warning(f"⚠️ Failed to assign role '{role_name}' to '{username}': {assign_response.status_code}")

        except Exception as e:
            logger.warning(f"⚠️ Failed to assign role '{role_name}' to '{username}': {e}")

    async def _setup_role_hierarchy(self) -> None:
        """Setup role hierarchy (admin includes manager, manager includes user)."""
        try:
            async with httpx.AsyncClient() as client:
                # Get role IDs
                roles_response = await client.get(
                    f"{self.base_url}/admin/realms/{self.realm}/roles",
                    headers={"Authorization": f"Bearer {self.admin_token}"},
                )
                roles_response.raise_for_status()
                roles = roles_response.json()

                role_ids = {role["name"]: role["id"] for role in roles}

                # Make admin role composite with manager and user roles
                if "admin" in role_ids and "manager" in role_ids and "user" in role_ids:
                    await client.post(
                        f"{self.base_url}/admin/realms/{self.realm}/roles/admin/composites",
                        headers={
                            "Authorization": f"Bearer {self.admin_token}",
                            "Content-Type": "application/json",
                        },
                        json=[
                            {"id": role_ids["manager"], "name": "manager"},
                            {"id": role_ids["user"], "name": "user"},
                        ],
                    )
                    logger.info("✅ Admin role configured as composite (includes manager and user)")

                # Make manager role composite with user role
                if "manager" in role_ids and "user" in role_ids:
                    await client.post(
                        f"{self.base_url}/admin/realms/{self.realm}/roles/manager/composites",
                        headers={
                            "Authorization": f"Bearer {self.admin_token}",
                            "Content-Type": "application/json",
                        },
                        json=[{"id": role_ids["user"], "name": "user"}],
                    )
                    logger.info("✅ Manager role configured as composite (includes user)")

        except Exception as e:
            logger.warning(f"⚠️ Failed to setup role hierarchy: {e}")

    async def _verify_setup(self) -> None:
        """Verify the setup by checking users and roles."""
        try:
            async with httpx.AsyncClient() as client:
                # Get all users
                response = await client.get(
                    f"{self.base_url}/admin/realms/{self.realm}/users",
                    headers={"Authorization": f"Bearer {self.admin_token}"},
                )
                response.raise_for_status()
                users = response.json()

                logger.info("🔍 Verifying Keycloak setup...")
                for user in users:
                    username = user.get("username", "")
                    if username in ["adminuser", "manager", "user", "testuser"]:
                        # Get user roles
                        roles_response = await client.get(
                            f"{self.base_url}/admin/realms/{self.realm}/users/{user['id']}/role-mappings/realm",
                            headers={"Authorization": f"Bearer {self.admin_token}"},
                        )
                        if roles_response.status_code == 200:
                            roles = roles_response.json()
                            role_names = [role["name"] for role in roles if role["name"] not in ["default-roles-eshop"]]
                            logger.info(f"✅ User '{username}' has roles: {', '.join(role_names)}")

        except Exception as e:
            logger.warning(f"⚠️ Setup verification failed: {e}")


async def setup_keycloak_async() -> bool:
    """Async function to setup Keycloak."""
    setup = KeycloakSetup()
    return await setup.setup_keycloak()


def setup_keycloak_sync() -> bool:
    """Synchronous wrapper for Keycloak setup."""
    try:
        return asyncio.run(setup_keycloak_async())
    except Exception as e:
        logger.error(f"❌ Keycloak setup failed: {e}")
        return False
