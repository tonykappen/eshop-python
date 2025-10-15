"""Keycloak setup and configuration module with credentials file support."""

import asyncio

import httpx

from app.config.settings import settings
from app.core.logging.base_logger import BaseLogger
from infra.keycloak.credentials import (
    ClientConfig,
    CredentialsLoader,
    KeycloakCredentials,
    RoleConfig,
    UserConfig,
)

logger = BaseLogger(__name__)


class KeycloakSetup:
    """Handles Keycloak realm, client, roles, and user setup using credentials file."""

    def __init__(self, credentials_path: str | None = None) -> None:
        """Initialize Keycloak setup.

        Args:
            credentials_path: Optional path to credentials file. If None, uses default search locations.
        """
        self.base_url = settings.keycloak_server_url
        self.realm = settings.keycloak_realm
        
        # Load credentials from file
        self.credentials_loader = CredentialsLoader(
            credentials_path or settings.keycloak_credentials_path
        )
        self.credentials: KeycloakCredentials | None = None
        
        # Tokens for different admin contexts
        self.master_admin_token: str | None = None
        self.realm_admin_token: str | None = None

    def _load_credentials(self) -> KeycloakCredentials:
        """Load credentials from file if not already loaded."""
        if self.credentials is None:
            self.credentials = self.credentials_loader.load()
        return self.credentials

    def _check_config_available(self) -> bool:
        """Check if all required Keycloak configuration settings are present."""
        logger.log_debug_with_context(
            "Checking Keycloak config",
            context={
                "base_url": self.base_url,
                "realm": self.realm,
            },
        )

        result = (
            self.base_url is not None
            and self.base_url != ""
            and self.realm is not None
            and self.realm != ""
        )

        logger.log_debug_with_context(
            "Keycloak config check result", context={"result": result}
        )
        return result

    async def setup_keycloak(self) -> bool:
        """Complete Keycloak setup process."""
        try:
            logger.log_with_context("🔧 Starting Keycloak setup...", "info")

            # Check if configuration is available
            if not self._check_config_available():
                logger.log_warning_with_context(
                    "⚠️ Keycloak configuration not available - skipping setup"
                )
                return False

            # Load credentials from file
            try:
                self._load_credentials()
                logger.info("✅ Successfully loaded credentials from file")
            except Exception as e:
                logger.error(f"❌ Failed to load credentials: {e}")
                return False

            # Wait for Keycloak to be ready
            logger.log_with_context("⏳ Waiting for Keycloak to be ready...", "info")
            await asyncio.sleep(10)  # Wait for Keycloak to fully start

            # Check if Keycloak is accessible
            if not await self._check_keycloak_accessible():
                logger.log_error_with_context("❌ Keycloak is not accessible")
                return False

            # Get master admin token (for realm creation)
            if not await self._get_master_admin_token():
                logger.log_error_with_context("❌ Failed to get master admin token")
                return False

            # Create realm
            if not await self._create_realm():
                logger.log_warning_with_context(
                    "⚠️ Realm creation failed or already exists"
                )

            # Create clients
            if not await self._create_clients():
                logger.log_warning_with_context(
                    "⚠️ Client creation failed or already exists"
                )

            # Create realm admin user (using master admin)
            if not await self._create_realm_admin():
                logger.log_warning_with_context(
                    "⚠️ Realm admin creation failed or already exists"
                )

            # Get realm admin token (for subsequent operations)
            if not await self._get_realm_admin_token():
                logger.log_warning_with_context(
                    "⚠️ Failed to get realm admin token, will use master admin token"
                )
                # Continue with master admin token
                self.realm_admin_token = self.master_admin_token

            # Create roles using realm admin (or master admin as fallback)
            if not await self._create_roles():
                logger.log_warning_with_context(
                    "⚠️ Role creation failed or already exists"
                )

            # Create users using realm admin (or master admin as fallback)
            if not await self._create_users():
                logger.log_warning_with_context(
                    "⚠️ User creation failed or already exists"
                )

            # Setup role hierarchy using realm admin (or master admin as fallback)
            await self._setup_role_hierarchy()

            # Verify setup
            await self._verify_setup()

            logger.log_with_context("✅ Keycloak setup completed successfully", "info")
            return True

        except Exception as e:
            logger.log_error_with_context("❌ Keycloak setup failed", error=e)
            return False

    def _get_admin_token(self) -> str:
        """Get the appropriate admin token (realm admin or master admin).

        Returns:
            The realm admin token if available, otherwise master admin token
        """
        return self.realm_admin_token or self.master_admin_token or ""

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
                    logger.error(
                        f"❌ Keycloak returned status code: {response.status_code}"
                    )
                    return False
        except Exception as e:
            logger.error(f"❌ Keycloak is not accessible: {e}")
            return False

    async def _get_master_admin_token(self) -> bool:
        """Get master admin token from Keycloak."""
        try:
            creds = self._load_credentials()
            master_admin = creds.master_admin

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/realms/master/protocol/openid-connect/token",
                    data={
                        "username": master_admin.username,
                        "password": master_admin.password,
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

    async def _get_realm_admin_token(self) -> bool:
        """Get realm admin token from Keycloak."""
        try:
            creds = self._load_credentials()
            realm_admin = creds.realm_admin

            # Find the first client config (we'll use it for realm admin authentication)
            if not creds.clients:
                logger.warning("⚠️ No clients configured, cannot get realm admin token")
                return False

            client = creds.clients[0]

            async with httpx.AsyncClient() as client_http:
                response = await client_http.post(
                    f"{self.base_url}/realms/{self.realm}/protocol/openid-connect/token",
                    data={
                        "username": realm_admin.username,
                        "password": realm_admin.password,
                        "grant_type": "password",
                        "client_id": client.client_id,
                        "client_secret": client.client_secret,
                    },
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                )
                response.raise_for_status()
                data = response.json()
                self.realm_admin_token = data.get("access_token")
                if self.realm_admin_token:
                    logger.info("✅ Realm admin token obtained")
                    return True
                else:
                    logger.error("❌ No access token in realm admin response")
                    return False
        except Exception as e:
            logger.warning(f"⚠️ Failed to get realm admin token: {e}")
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
                        "displayName": f"{self.realm.title()} Realm",
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

    async def _create_clients(self) -> bool:
        """Create OAuth/OIDC clients from credentials file."""
        try:
            creds = self._load_credentials()
            clients = creds.clients

            if not clients:
                logger.warning("⚠️ No clients configured in credentials file")
                return False

            async with httpx.AsyncClient() as client_http:
                for client_config in clients:
                    response = await client_http.post(
                        f"{self.base_url}/admin/realms/{self.realm}/clients",
                        headers={
                            "Authorization": f"Bearer {self.master_admin_token}",
                            "Content-Type": "application/json",
                        },
                        json={
                            "clientId": client_config.client_id,
                            "enabled": True,
                            "publicClient": False,
                            "clientAuthenticatorType": "client-secret",
                            "secret": client_config.client_secret,
                            "redirectUris": client_config.redirect_uris,
                            "webOrigins": client_config.web_origins,
                            "serviceAccountsEnabled": client_config.service_accounts_enabled,
                            "authorizationServicesEnabled": client_config.authorization_services_enabled,
                            "directAccessGrantsEnabled": client_config.direct_access_grants_enabled,
                            "standardFlowEnabled": client_config.standard_flow_enabled,
                        },
                    )
                    if response.status_code == 201:
                        logger.info(f"✅ Client '{client_config.client_id}' created")
                    elif response.status_code == 409:
                        logger.info(
                            f"ℹ️ Client '{client_config.client_id}' already exists"
                        )
                    else:
                        logger.error(
                            f"❌ Failed to create client '{client_config.client_id}': {response.status_code}"
                        )

            return True
        except Exception as e:
            logger.error(f"❌ Client creation failed: {e}")
            return False

    async def _create_realm_admin(self) -> bool:
        """Create a realm admin user using master admin token."""
        try:
            creds = self._load_credentials()
            realm_admin = creds.realm_admin

            async with httpx.AsyncClient() as client:
                # Create realm admin user
                user_data = {
                    "username": realm_admin.username,
                    "email": realm_admin.email,
                    "enabled": True,
                    "emailVerified": True,
                    "firstName": realm_admin.first_name,
                    "lastName": realm_admin.last_name,
                    "credentials": [
                        {
                            "type": "password",
                            "value": realm_admin.password,
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
                    logger.info(f"✅ Realm admin user '{realm_admin.username}' created")
                    # Assign admin role to realm admin
                    await self._assign_role_to_user(
                        client, realm_admin.username, "admin", use_master_admin=True
                    )
                    return True
                elif response.status_code == 409:
                    logger.info(
                        f"ℹ️ Realm admin user '{realm_admin.username}' already exists"
                    )
                    # Ensure admin role is assigned to existing realm admin
                    await self._assign_role_to_user(
                        client, realm_admin.username, "admin", use_master_admin=True
                    )
                    # Update password for existing realm admin
                    await self._update_user_password(
                        client, realm_admin.username, realm_admin.password, use_master_admin=True
                    )
                    return True
                else:
                    logger.error(
                        f"❌ Failed to create realm admin: {response.status_code}"
                    )
                    return False
        except Exception as e:
            logger.error(f"❌ Realm admin creation failed: {e}")
            return False

    async def _create_roles(self) -> bool:
        """Create RBAC roles from credentials file using realm admin (or master admin as fallback)."""
        try:
            creds = self._load_credentials()
            roles = creds.roles

            if not roles:
                logger.warning("⚠️ No roles configured in credentials file")
                return False

            admin_token = self._get_admin_token()

            async with httpx.AsyncClient() as client:
                for role in roles:
                    response = await client.post(
                        f"{self.base_url}/admin/realms/{self.realm}/roles",
                        headers={
                            "Authorization": f"Bearer {admin_token}",
                            "Content-Type": "application/json",
                        },
                        json={
                            "name": role.name,
                            "description": role.description,
                        },
                    )
                    if response.status_code == 201:
                        logger.info(f"✅ Role '{role.name}' created by realm admin")
                    elif response.status_code == 409:
                        logger.info(f"ℹ️ Role '{role.name}' already exists")
                    else:
                        logger.warning(
                            f"⚠️ Failed to create role '{role.name}': {response.status_code}"
                        )

            return True
        except Exception as e:
            logger.error(f"❌ Role creation failed: {e}")
            return False

    async def _create_users(self) -> bool:
        """Create users with roles from credentials file using realm admin (or master admin as fallback)."""
        try:
            creds = self._load_credentials()
            users = creds.users

            if not users:
                logger.warning("⚠️ No users configured in credentials file")
                return False

            admin_token = self._get_admin_token()

            async with httpx.AsyncClient() as client:
                for user_config in users:
                    # Create user
                    user_data = {
                        "username": user_config.username,
                        "email": user_config.email,
                        "enabled": user_config.enabled,
                        "emailVerified": user_config.email_verified,
                        "firstName": user_config.first_name,
                        "lastName": user_config.last_name,
                        "credentials": [
                            {
                                "type": "password",
                                "value": user_config.password,
                                "temporary": False,
                            }
                        ],
                    }

                    response = await client.post(
                        f"{self.base_url}/admin/realms/{self.realm}/users",
                        headers={
                            "Authorization": f"Bearer {admin_token}",
                            "Content-Type": "application/json",
                        },
                        json=user_data,
                    )

                    if response.status_code == 201:
                        logger.info(
                            f"✅ User '{user_config.username}' created by realm admin"
                        )
                    elif response.status_code == 409:
                        logger.info(f"ℹ️ User '{user_config.username}' already exists")
                        # Update password for existing user
                        await self._update_user_password(
                            client, user_config.username, user_config.password
                        )
                    else:
                        logger.warning(
                            f"⚠️ Failed to create user '{user_config.username}': {response.status_code}"
                        )
                        continue

                    # Assign roles to user with retry logic
                    for role_name in user_config.roles:
                        await self._assign_role_to_user_with_retry(
                            client, user_config.username, role_name
                        )

            return True
        except Exception as e:
            logger.error(f"❌ User creation failed: {e}")
            return False

    async def _update_user_password(
        self, client: httpx.AsyncClient, username: str, password: str, use_master_admin: bool = False
    ) -> None:
        """Update password for existing user.

        Args:
            client: HTTP client
            username: Username to update
            password: New password
            use_master_admin: If True, use master admin token; otherwise use realm admin token
        """
        try:
            admin_token = self.master_admin_token if use_master_admin else self._get_admin_token()
            
            # Get user ID
            response = await client.get(
                f"{self.base_url}/admin/realms/{self.realm}/users",
                headers={"Authorization": f"Bearer {admin_token}"},
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
                        "Authorization": f"Bearer {admin_token}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "type": "password",
                        "value": password,
                        "temporary": False,
                    },
                )
                if password_response.status_code == 204:
                    logger.info(f"✅ Password updated for user '{username}'")
        except Exception as e:
            logger.warning(f"⚠️ Failed to update password for '{username}': {e}")

    async def _assign_role_to_user_with_retry(
        self, client: httpx.AsyncClient, username: str, role_name: str
    ) -> None:
        """Assign role to user with retry logic to handle timing issues."""
        max_retries = 3
        retry_delay = 2  # seconds

        for attempt in range(max_retries):
            try:
                success = await self._assign_role_to_user(client, username, role_name)
                if success:
                    return
                else:
                    logger.warning(
                        f"⚠️ Role assignment attempt {attempt + 1} failed for '{username}' -> '{role_name}'"
                    )
                    if attempt < max_retries - 1:
                        await asyncio.sleep(retry_delay)
                        retry_delay *= 2  # Exponential backoff
            except Exception as e:
                logger.warning(
                    f"⚠️ Role assignment attempt {attempt + 1} failed for '{username}' -> '{role_name}': {e}"
                )
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff

        logger.error(
            f"❌ Failed to assign role '{role_name}' to '{username}' after {max_retries} attempts"
        )

    async def _assign_role_to_user(
        self, client: httpx.AsyncClient, username: str, role_name: str, use_master_admin: bool = False
    ) -> bool:
        """Assign role to user.

        Args:
            client: HTTP client
            username: Username to assign role to
            role_name: Role name to assign
            use_master_admin: If True, use master admin token; otherwise use realm admin token
        """
        try:
            admin_token = self.master_admin_token if use_master_admin else self._get_admin_token()
            
            # Get user ID
            response = await client.get(
                f"{self.base_url}/admin/realms/{self.realm}/users",
                headers={"Authorization": f"Bearer {admin_token}"},
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
                headers={"Authorization": f"Bearer {admin_token}"},
            )
            role_response.raise_for_status()
            role_data = role_response.json()
            role_id = role_data["id"]

            # Check if role is already assigned
            current_roles_response = await client.get(
                f"{self.base_url}/admin/realms/{self.realm}/users/{user_id}/role-mappings/realm",
                headers={"Authorization": f"Bearer {admin_token}"},
            )
            if current_roles_response.status_code == 200:
                current_roles = current_roles_response.json()
                if any(role["name"] == role_name for role in current_roles):
                    logger.info(
                        f"ℹ️ Role '{role_name}' already assigned to user '{username}'"
                    )
                    return True

            # Assign role with explicit role data
            role_payload = {
                "id": role_id,
                "name": role_name,
                "description": role_data.get("description", ""),
                "composite": role_data.get("composite", False),
                "clientRole": role_data.get("clientRole", False),
            }

            assign_response = await client.post(
                f"{self.base_url}/admin/realms/{self.realm}/users/{user_id}/role-mappings/realm",
                headers={
                    "Authorization": f"Bearer {admin_token}",
                    "Content-Type": "application/json",
                },
                json=[role_payload],
            )

            if assign_response.status_code == 204:
                logger.info(
                    f"✅ Role '{role_name}' assigned to user '{username}' by realm admin"
                )

                # Verify the assignment was successful
                await asyncio.sleep(1)  # Small delay to ensure assignment is processed
                verify_response = await client.get(
                    f"{self.base_url}/admin/realms/{self.realm}/users/{user_id}/role-mappings/realm",
                    headers={"Authorization": f"Bearer {admin_token}"},
                )
                if verify_response.status_code == 200:
                    assigned_roles = verify_response.json()
                    if any(role["name"] == role_name for role in assigned_roles):
                        logger.info(
                            f"✅ Verified: Role '{role_name}' successfully assigned to '{username}'"
                        )
                        return True
                    else:
                        logger.error(
                            f"❌ Role assignment verification failed for '{username}' -> '{role_name}'"
                        )
                        return False
                else:
                    logger.error(
                        f"❌ Could not verify role assignment for '{username}' -> '{role_name}'"
                    )
                    return False
            else:
                logger.error(
                    f"❌ Failed to assign role '{role_name}' to '{username}': {assign_response.status_code} - {assign_response.text}"
                )
                return False

        except Exception as e:
            logger.error(f"❌ Failed to assign role '{role_name}' to '{username}': {e}")
            return False

    async def _setup_role_hierarchy(self) -> None:
        """Setup role hierarchy from credentials file using realm admin (or master admin as fallback)."""
        try:
            creds = self._load_credentials()
            role_hierarchy = creds.role_hierarchy

            if not role_hierarchy:
                logger.info("ℹ️ No role hierarchy configured")
                return

            admin_token = self._get_admin_token()

            async with httpx.AsyncClient() as client:
                # Get all roles
                roles_response = await client.get(
                    f"{self.base_url}/admin/realms/{self.realm}/roles",
                    headers={"Authorization": f"Bearer {admin_token}"},
                )
                roles_response.raise_for_status()
                roles = roles_response.json()

                role_ids = {role["name"]: role["id"] for role in roles}

                # Setup hierarchy for each parent role
                for parent_role_name, hierarchy_config in role_hierarchy.items():
                    if parent_role_name not in role_ids:
                        logger.warning(
                            f"⚠️ Parent role '{parent_role_name}' not found in role hierarchy setup"
                        )
                        continue

                    # Build composite roles payload
                    composite_roles = []
                    for child_role_name in hierarchy_config.includes:
                        if child_role_name in role_ids:
                            composite_roles.append(
                                {"id": role_ids[child_role_name], "name": child_role_name}
                            )
                        else:
                            logger.warning(
                                f"⚠️ Child role '{child_role_name}' not found for parent '{parent_role_name}'"
                            )

                    if composite_roles:
                        response = await client.post(
                            f"{self.base_url}/admin/realms/{self.realm}/roles/{parent_role_name}/composites",
                            headers={
                                "Authorization": f"Bearer {admin_token}",
                                "Content-Type": "application/json",
                            },
                            json=composite_roles,
                        )
                        if response.status_code in [200, 204]:
                            logger.info(
                                f"✅ Role '{parent_role_name}' configured as composite (includes: {', '.join([r['name'] for r in composite_roles])})"
                            )
                        else:
                            logger.warning(
                                f"⚠️ Failed to setup hierarchy for '{parent_role_name}': {response.status_code}"
                            )

        except Exception as e:
            logger.warning(f"⚠️ Failed to setup role hierarchy: {e}")

    async def _verify_setup(self) -> None:
        """Verify the setup by checking users and roles."""
        try:
            admin_token = self._get_admin_token()

            async with httpx.AsyncClient() as client:
                # Get all users
                response = await client.get(
                    f"{self.base_url}/admin/realms/{self.realm}/users",
                    headers={"Authorization": f"Bearer {admin_token}"},
                )
                response.raise_for_status()
                users = response.json()

                logger.info("🔍 Verifying Keycloak setup...")
                
                creds = self._load_credentials()
                expected_usernames = [u.username for u in creds.users] + [
                    creds.realm_admin.username
                ]

                for user in users:
                    username = user.get("username", "")
                    if username in expected_usernames:
                        # Get user roles
                        roles_response = await client.get(
                            f"{self.base_url}/admin/realms/{self.realm}/users/{user['id']}/role-mappings/realm",
                            headers={"Authorization": f"Bearer {admin_token}"},
                        )
                        if roles_response.status_code == 200:
                            roles = roles_response.json()
                            # Filter out default roles
                            role_names = [
                                role["name"]
                                for role in roles
                                if role["name"] not in [f"default-roles-{self.realm}"]
                            ]
                            logger.info(
                                f"✅ User '{username}' has roles: {', '.join(role_names) if role_names else 'none (only default roles)'}"
                            )

                            # Test token generation for each user
                            await self._test_user_token(username)

        except Exception as e:
            logger.warning(f"⚠️ Setup verification failed: {e}")

    async def _test_user_token(self, username: str) -> None:
        """Test token generation for a user to verify roles are included."""
        try:
            creds = self._load_credentials()
            
            # Find user config to get password
            user_password = None
            if username == creds.realm_admin.username:
                user_password = creds.realm_admin.password
            else:
                for user_config in creds.users:
                    if user_config.username == username:
                        user_password = user_config.password
                        break

            if not user_password:
                logger.warning(f"⚠️ Could not find password for user '{username}'")
                return

            # Use the first client for authentication
            if not creds.clients:
                logger.warning("⚠️ No clients configured for token testing")
                return

            client_config = creds.clients[0]

            async with httpx.AsyncClient() as client:
                token_data = {
                    "grant_type": "password",
                    "username": username,
                    "password": user_password,
                    "client_id": client_config.client_id,
                    "client_secret": client_config.client_secret,
                }

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
                            default_roles = [
                                "offline_access",
                                "uma_authorization",
                                f"default-roles-{self.realm}",
                            ]
                            user_roles = [role for role in roles if role not in default_roles]

                            if user_roles:
                                logger.info(
                                    f"✅ User '{username}' token includes roles: {', '.join(user_roles)}"
                                )
                            else:
                                logger.info(
                                    f"ℹ️ User '{username}' token generated successfully (no custom roles found)"
                                )
                        except Exception as e:
                            logger.warning(f"⚠️ Could not decode token for '{username}': {e}")
                else:
                    logger.warning(
                        f"⚠️ Could not generate token for '{username}': {response.status_code}"
                    )
        except Exception as e:
            logger.warning(f"⚠️ Token test failed for '{username}': {e}")


async def setup_keycloak_async(credentials_path: str | None = None) -> bool:
    """Async function to setup Keycloak with credentials from file.

    Args:
        credentials_path: Optional path to credentials file

    Returns:
        True if setup was successful, False otherwise
    """
    setup = KeycloakSetup(credentials_path)
    return await setup.setup_keycloak()
