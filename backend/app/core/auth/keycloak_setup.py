"""Keycloak setup and configuration module."""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional

import httpx
from app.core.logging.base_logger import BaseLogger

from app.config.settings import settings

logger = BaseLogger(__name__)


class KeycloakSetup:
    """Handles Keycloak realm, client, roles, and user setup."""

    def __init__(self) -> None:
        """Initialize Keycloak setup."""
        self.base_url = settings.keycloak_server_url
        self.realm = settings.keycloak_realm 
        self.client_id = settings.keycloak_client_id
        self.client_secret = settings.keycloak_client_secret
        self.master_admin_token: Optional[str] = None

    def _check_config_available(self) -> bool:
        """Check if all required Keycloak configuration settings are present."""
        logger.log_debug_with_context(
            "Checking Keycloak config",
            context={
                "base_url": self.base_url,
                "client_id": self.client_id,
                "client_secret": "***" if self.client_secret else "None",
                "realm": self.realm
            }
        )
        
        result = (
            self.base_url is not None and
            self.base_url != "" and
            self.client_id is not None and
            self.client_id != "" and
            self.client_secret is not None and
            self.client_secret != "" and
            self.realm is not None and
            self.realm != ""
        )
        
        logger.log_debug_with_context(
            "Keycloak config check result",
            context={"result": result}
        )
        return result

    async def setup_keycloak(self) -> bool:
        """Complete Keycloak setup process."""
        try:
            logger.log_with_context("🔧 Starting Keycloak setup...", "info")
            
            # Check if configuration is available
            if not self._check_config_available():
                logger.log_warning_with_context("⚠️ Keycloak configuration not available - skipping setup")
                return False
            
            # Wait for Keycloak to be ready
            logger.log_with_context("⏳ Waiting for Keycloak to be ready...", "info")
            await asyncio.sleep(10)  # Wait for Keycloak to fully start

            # Check if Keycloak is accessible
            if not await self._check_keycloak_accessible():
                logger.log_error_with_context("❌ Keycloak is not accessible")
                return False

            # Get master admin token (for all operations)
            if not await self._get_master_admin_token():
                logger.log_error_with_context("❌ Failed to get master admin token")
                return False

            # Create realm
            if not await self._create_realm():
                logger.log_warning_with_context("⚠️ Realm creation failed or already exists")

            # Create client
            if not await self._create_client():
                logger.log_warning_with_context("⚠️ Client creation failed or already exists")

            # Create realm admin user
            if not await self._create_realm_admin():
                logger.log_warning_with_context("⚠️ Realm admin creation failed or already exists")

            # Create roles using master admin (full permissions)
            if not await self._create_roles():
                logger.log_warning_with_context("⚠️ Role creation failed or already exists")

            # Create users using master admin (full permissions)
            if not await self._create_users():
                logger.log_warning_with_context("⚠️ User creation failed or already exists")

            # Setup role hierarchy using master admin (full permissions)
            await self._setup_role_hierarchy()

            # Verify setup using master admin (full permissions)
            await self._verify_setup()

            logger.log_with_context("✅ Keycloak setup completed successfully", "info")
            return True

        except Exception as e:
            logger.log_error_with_context(
                "❌ Keycloak setup failed",
                error=e
            )
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

    async def _get_master_admin_token(self) -> bool:
        """Get master admin token from Keycloak."""
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
                self.master_admin_token = data.get("access_token")
                if self.master_admin_token:
                    logger.info("✅ Master admin token obtained")
                    return True
                else:
                    logger.error("❌ No access token in response")
                    return False
        except Exception as e:
            logger.error(f"❌ Failed to get master admin token: {e}")
            return False

    async def _create_realm(self) -> bool:
        """Create the eShop realm."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/admin/realms",
                    headers={
                        "Authorization": f"Bearer {self.master_admin_token}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "realm": self.realm,
                        "enabled": True,
                        "displayName": "eShop4 Realm",
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
                        "Authorization": f"Bearer {self.master_admin_token}",
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

    async def _create_realm_admin(self) -> bool:
        """Create a realm admin user."""
        try:
            async with httpx.AsyncClient() as client:
                # Create realm admin user
                user_data = {
                    "username": "realm-admin",
                    "email": "realm-admin@eshop.com",
                    "enabled": True,
                    "emailVerified": True,
                    "firstName": "Realm",
                    "lastName": "Admin",
                    "credentials": [
                        {
                            "type": "password",
                            "value": "admin123",
                            "temporary": False,
                        }
                    ],
                }

                response = await client.post(
                    f"{self.base_url}/admin/realms/{self.realm}/users",
                    headers={
                        "Authorization": f"Bearer {self.master_admin_token}",
                        "Content-Type": "application/json",
                    },
                    json=user_data,
                )

                if response.status_code == 201:
                    logger.info("✅ Realm admin user created")
                    # Assign admin role to realm admin
                    await self._assign_role_to_user(client, "realm-admin", "admin")
                    return True
                elif response.status_code == 409:
                    logger.info("ℹ️ Realm admin user already exists")
                    # Ensure admin role is assigned to existing realm admin
                    await self._assign_role_to_user(client, "realm-admin", "admin")
                    return True
                else:
                    logger.error(f"❌ Failed to create realm admin: {response.status_code}")
                    return False
        except Exception as e:
            logger.error(f"❌ Realm admin creation failed: {e}")
            return False

    async def _create_roles(self) -> bool:
        """Create RBAC roles using master admin."""
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
                            "Authorization": f"Bearer {self.master_admin_token}",
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
        """Create test users with roles using master admin."""
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
                            "Authorization": f"Bearer {self.master_admin_token}",
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

                    # Assign role to user with retry logic
                    await self._assign_role_to_user_with_retry(client, username, role)

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
                headers={"Authorization": f"Bearer {self.master_admin_token}"},
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
                        "Authorization": f"Bearer {self.master_admin_token}",
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

    async def _assign_role_to_user_with_retry(self, client: httpx.AsyncClient, username: str, role_name: str) -> None:
        """Assign role to user with retry logic to handle timing issues."""
        max_retries = 3
        retry_delay = 2  # seconds
        
        for attempt in range(max_retries):
            try:
                success = await self._assign_role_to_user(client, username, role_name)
                if success:
                    return
                else:
                    logger.warning(f"⚠️ Role assignment attempt {attempt + 1} failed for '{username}' -> '{role_name}'")
                    if attempt < max_retries - 1:
                        await asyncio.sleep(retry_delay)
                        retry_delay *= 2  # Exponential backoff
            except Exception as e:
                logger.warning(f"⚠️ Role assignment attempt {attempt + 1} failed for '{username}' -> '{role_name}': {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
        
        logger.error(f"❌ Failed to assign role '{role_name}' to '{username}' after {max_retries} attempts")

    async def _assign_role_to_user(self, client: httpx.AsyncClient, username: str, role_name: str) -> bool:
        """Assign role to user."""
        try:
            # Get user ID
            response = await client.get(
                f"{self.base_url}/admin/realms/{self.realm}/users",
                headers={"Authorization": f"Bearer {self.master_admin_token}"},
                params={"username": username},
            )
            response.raise_for_status()
            users = response.json()
            if not users:
                logger.warning(f"⚠️ User '{username}' not found for role assignment")
                return False

            user_id = users[0]["id"]

            # Get role ID
            role_response = await client.get(
                f"{self.base_url}/admin/realms/{self.realm}/roles/{role_name}",
                headers={"Authorization": f"Bearer {self.master_admin_token}"},
            )
            role_response.raise_for_status()
            role_data = role_response.json()
            role_id = role_data["id"]

            # Check if role is already assigned
            current_roles_response = await client.get(
                f"{self.base_url}/admin/realms/{self.realm}/users/{user_id}/role-mappings/realm",
                headers={"Authorization": f"Bearer {self.master_admin_token}"},
            )
            if current_roles_response.status_code == 200:
                current_roles = current_roles_response.json()
                if any(role["name"] == role_name for role in current_roles):
                    logger.info(f"ℹ️ Role '{role_name}' already assigned to user '{username}'")
                    return True

            # Assign role with explicit role data
            role_payload = {
                "id": role_id,
                "name": role_name,
                "description": role_data.get("description", ""),
                "composite": role_data.get("composite", False),
                "clientRole": role_data.get("clientRole", False)
            }

            assign_response = await client.post(
                f"{self.base_url}/admin/realms/{self.realm}/users/{user_id}/role-mappings/realm",
                headers={
                    "Authorization": f"Bearer {self.master_admin_token}",
                    "Content-Type": "application/json",
                },
                json=[role_payload],
            )

            if assign_response.status_code == 204:
                logger.info(f"✅ Role '{role_name}' assigned to user '{username}'")
                
                # Verify the assignment was successful
                await asyncio.sleep(1)  # Small delay to ensure assignment is processed
                verify_response = await client.get(
                    f"{self.base_url}/admin/realms/{self.realm}/users/{user_id}/role-mappings/realm",
                    headers={"Authorization": f"Bearer {self.master_admin_token}"},
                )
                if verify_response.status_code == 200:
                    assigned_roles = verify_response.json()
                    if any(role["name"] == role_name for role in assigned_roles):
                        logger.info(f"✅ Verified: Role '{role_name}' successfully assigned to '{username}'")
                        return True
                    else:
                        logger.error(f"❌ Role assignment verification failed for '{username}' -> '{role_name}'")
                        return False
                else:
                    logger.error(f"❌ Could not verify role assignment for '{username}' -> '{role_name}'")
                    return False
            else:
                logger.error(f"❌ Failed to assign role '{role_name}' to '{username}': {assign_response.status_code} - {assign_response.text}")
                return False

        except Exception as e:
            logger.error(f"❌ Failed to assign role '{role_name}' to '{username}': {e}")
            return False

    async def _setup_role_hierarchy(self) -> None:
        """Setup role hierarchy (admin includes manager, manager includes user)."""
        try:
            async with httpx.AsyncClient() as client:
                # Get role IDs
                roles_response = await client.get(
                    f"{self.base_url}/admin/realms/{self.realm}/roles",
                    headers={"Authorization": f"Bearer {self.master_admin_token}"},
                )
                roles_response.raise_for_status()
                roles = roles_response.json()

                role_ids = {role["name"]: role["id"] for role in roles}

                # Make admin role composite with manager and user roles
                if "admin" in role_ids and "manager" in role_ids and "user" in role_ids:
                    await client.post(
                        f"{self.base_url}/admin/realms/{self.realm}/roles/admin/composites",
                        headers={
                            "Authorization": f"Bearer {self.master_admin_token}",
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
                            "Authorization": f"Bearer {self.master_admin_token}",
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
                    headers={"Authorization": f"Bearer {self.master_admin_token}"},
                )
                response.raise_for_status()
                users = response.json()

                logger.info("🔍 Verifying Keycloak setup...")
                for user in users:
                    username = user.get("username", "")
                    if username in ["adminuser", "manager", "user", "testuser", "realm-admin"]:
                        # Get user roles
                        roles_response = await client.get(
                            f"{self.base_url}/admin/realms/{self.realm}/users/{user['id']}/role-mappings/realm",
                            headers={"Authorization": f"Bearer {self.master_admin_token}"},
                        )
                        if roles_response.status_code == 200:
                            roles = roles_response.json()
                            # Filter out default roles - use the actual realm name
                            role_names = [role["name"] for role in roles if role["name"] not in [f"default-roles-{self.realm}"]]
                            logger.info(f"✅ User '{username}' has roles: {', '.join(role_names)}")
                            
                            # Test token generation for each user
                            await self._test_user_token(username)

        except Exception as e:
            logger.warning(f"⚠️ Setup verification failed: {e}")

    async def _test_user_token(self, username: str) -> None:
        """Test token generation for a user to verify roles are included."""
        try:
            async with httpx.AsyncClient() as client:
                # Use admin-cli for realm-admin, eshop-api for others
                client_id = "admin-cli" if username == "realm-admin" else self.client_id
                client_secret = "" if username == "realm-admin" else self.client_secret
                
                token_data = {
                    "grant_type": "password",
                    "username": username,
                    "password": "password" if username != "realm-admin" else "admin123",
                }
                
                if client_id == "admin-cli":
                    token_data["client_id"] = client_id
                else:
                    token_data["client_id"] = client_id
                    token_data["client_secret"] = client_secret
                
                response = await client.post(
                    f"{self.base_url}/realms/{self.realm}/protocol/openid-connect/token",
                    data=token_data,
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                )
                if response.status_code == 200:
                    data = response.json()
                    token = data.get("access_token")
                    if token:
                        # Decode token to check roles (basic check)
                        import jwt
                        try:
                            # Decode without verification to check payload
                            decoded = jwt.decode(token, options={"verify_signature": False})
                            roles = decoded.get("realm_access", {}).get("roles", [])
                            # Filter out default roles
                            default_roles = ["offline_access", "uma_authorization", f"default-roles-{self.realm}"]
                            user_roles = [role for role in roles if role not in default_roles]
                            
                            # Special handling for realm-admin (admin-cli tokens don't include realm roles)
                            if username == "realm-admin":
                                if user_roles:
                                    logger.info(f"✅ User '{username}' token includes roles: {', '.join(user_roles)}")
                                else:
                                    logger.info(f"ℹ️ User '{username}' token generated successfully (admin-cli tokens typically don't include realm roles)")
                            else:
                                if user_roles:
                                    logger.info(f"✅ User '{username}' token includes roles: {', '.join(user_roles)}")
                                else:
                                    logger.warning(f"⚠️ User '{username}' token missing expected roles")
                        except Exception as e:
                            logger.warning(f"⚠️ Could not decode token for '{username}': {e}")
                else:
                    logger.warning(f"⚠️ Could not generate token for '{username}': {response.status_code}")
        except Exception as e:
            logger.warning(f"⚠️ Token test failed for '{username}': {e}")


async def setup_keycloak_async() -> bool:
    """Async function to setup Keycloak."""
    setup = KeycloakSetup()
    return await setup.setup_keycloak()



