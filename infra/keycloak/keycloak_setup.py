"""Keycloak setup and configuration module with credentials file support."""

import asyncio
import json

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
            logger.log_with_context("[SETUP] Starting Keycloak setup...", "info")

            # Check if configuration is available
            if not self._check_config_available():
                logger.log_warning_with_context(
                    "[WARNING] Keycloak configuration not available - skipping setup"
                )
                return False

            # Load credentials from file
            try:
                self._load_credentials()
                logger.info("[OK] Successfully loaded credentials from file")
            except Exception as e:
                logger.error(f"[FAILED] Failed to load credentials: {e}")
                return False

            # Wait for Keycloak to be ready
            logger.log_with_context("Waiting for Keycloak to be ready...", "info")
            await asyncio.sleep(10)  # Wait for Keycloak to fully start

            # Check if Keycloak is accessible
            if not await self._check_keycloak_accessible():
                logger.log_error_with_context("[FAILED] Keycloak is not accessible")
                return False

            # Get master admin token (for realm creation)
            if not await self._get_master_admin_token():
                logger.log_error_with_context("[FAILED] Failed to get master admin token")
                return False

            # Verify master admin token is valid by testing it
            if not await self._verify_master_admin_token():
                logger.log_error_with_context("[FAILED] Master admin token is invalid")
                return False

            # Create realm
            if not await self._create_realm():
                logger.log_warning_with_context(
                    "[WARNING] Realm creation failed or already exists"
                )

            # Create clients
            if not await self._create_clients():
                logger.log_warning_with_context(
                    "[WARNING] Client creation failed or already exists"
                )

            # Verify and fix client configuration
            if not await self._verify_client_configuration():
                logger.log_warning_with_context(
                    "[WARNING] Client configuration verification failed"
                )

            # Configure client service account permissions
            if not await self._configure_client_permissions():
                logger.log_warning_with_context(
                    "[WARNING] Client permissions configuration failed"
                )

            # Create realm admin user (using master admin)
            if not await self._create_realm_admin():
                logger.log_warning_with_context(
                    "[WARNING] Realm admin creation failed or already exists"
                )

            # Get realm admin token (for subsequent operations)
            if not await self._get_realm_admin_token():
                logger.log_warning_with_context(
                    "[WARNING] Failed to get realm admin token, will use master admin token"
                )
                # Continue with master admin token
                self.realm_admin_token = self.master_admin_token

            # Create roles using realm admin (or master admin as fallback)
            if not await self._create_roles():
                logger.log_warning_with_context(
                    "[WARNING] Role creation failed or already exists"
                )

            # Create users using realm admin (or master admin as fallback)
            if not await self._create_users():
                logger.log_warning_with_context(
                    "[WARNING] User creation failed or already exists"
                )

            # Setup role hierarchy using realm admin (or master admin as fallback)
            await self._setup_role_hierarchy()

            # Verify setup
            await self._verify_setup()

            logger.log_with_context("[OK] Keycloak setup completed successfully", "info")
            return True

        except Exception as e:
            logger.log_error_with_context("[FAILED] Keycloak setup failed", error=e)
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
                    logger.info("[OK] Keycloak is accessible")
                    return True
                else:
                    logger.error(
                        f"[FAILED] Keycloak returned status code: {response.status_code}"
                    )
                    return False
        except Exception as e:
            logger.error(f"[FAILED] Keycloak is not accessible: {e}")
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
                    logger.info("[OK] Master admin token obtained")
                    return True
                else:
                    logger.error("[FAILED] No access token in response")
                    return False
        except Exception as e:
            logger.error(f"[FAILED] Failed to get master admin token: {e}")
            return False

    async def _verify_master_admin_token(self) -> bool:
        """Verify that master admin token is valid by making a test API call."""
        try:
            async with httpx.AsyncClient() as client:
                # Try to get list of realms - this requires admin privileges
                response = await client.get(
                    f"{self.base_url}/admin/realms",
                    headers={
                        "Authorization": f"Bearer {self.master_admin_token}",
                        "Content-Type": "application/json",
                    },
                )
                if response.status_code == 200:
                    logger.info("[OK] Master admin token verified")
                    return True
                else:
                    logger.error(
                        f"[FAILED] Master admin token verification failed: {response.status_code} - {response.text}"
                    )
                    return False
        except Exception as e:
            logger.error(f"[FAILED] Failed to verify master admin token: {e}")
            return False

    async def _get_realm_admin_token(self) -> bool:
        """Get realm admin token from Keycloak."""
        try:
            creds = self._load_credentials()
            realm_admin = creds.realm_admin

            # Find the first client config (we'll use it for realm admin authentication)
            if not creds.clients:
                logger.warning("[WARNING] No clients configured, cannot get realm admin token")
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
                    logger.info("[OK] Realm admin token obtained")
                    return True
                else:
                    logger.error("[FAILED] No access token in realm admin response")
                    return False
        except Exception as e:
            logger.warning(f"[WARNING] Failed to get realm admin token: {e}")
            return False

    async def _assign_realm_admin_role(self, client: httpx.AsyncClient, username: str) -> bool:
        """Assign realm-admin role to user using master admin token.
        
        This gives the user admin permissions in the realm.
        """
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
                logger.warning(f"[WARNING] User '{username}' not found for realm admin role assignment")
                return False

            user_id = users[0]["id"]

            # Get realm-admin role from realm-management client
            role_response = await client.get(
                f"{self.base_url}/admin/realms/{self.realm}/clients",
                headers={"Authorization": f"Bearer {self.master_admin_token}"},
                params={"clientId": "realm-management"},
            )
            role_response.raise_for_status()
            clients = role_response.json()
            if not clients:
                logger.warning("[WARNING] realm-management client not found")
                return False

            realm_management_client_id = clients[0]["id"]

            # Get realm-admin role from realm-management client
            admin_role_response = await client.get(
                f"{self.base_url}/admin/realms/{self.realm}/clients/{realm_management_client_id}/roles/realm-admin",
                headers={"Authorization": f"Bearer {self.master_admin_token}"},
            )
            admin_role_response.raise_for_status()
            admin_role = admin_role_response.json()

            # Check if role is already assigned
            current_roles_response = await client.get(
                f"{self.base_url}/admin/realms/{self.realm}/users/{user_id}/role-mappings/clients/{realm_management_client_id}",
                headers={"Authorization": f"Bearer {self.master_admin_token}"},
            )
            if current_roles_response.status_code == 200:
                current_roles = current_roles_response.json()
                if any(role["name"] == "realm-admin" for role in current_roles):
                    logger.info(f"[INFO] Realm-admin role already assigned to user '{username}'")
                    return True

            # Assign realm-admin role
            role_payload = {
                "id": admin_role["id"],
                "name": "realm-admin",
                "description": admin_role.get("description", ""),
                "composite": admin_role.get("composite", False),
                "clientRole": True,
            }

            assign_response = await client.post(
                f"{self.base_url}/admin/realms/{self.realm}/users/{user_id}/role-mappings/clients/{realm_management_client_id}",
                headers={
                    "Authorization": f"Bearer {self.master_admin_token}",
                    "Content-Type": "application/json",
                },
                json=[role_payload],
            )

            if assign_response.status_code == 204:
                logger.info(f"[OK] Realm-admin role assigned to user '{username}'")
                return True
            else:
                logger.error(f"[FAILED] Failed to assign realm-admin role to '{username}': {assign_response.status_code}")
                return False

        except Exception as e:
            logger.error(f"[FAILED] Failed to assign realm-admin role to '{username}': {e}")
            return False

    async def _create_realm(self) -> bool:
        """Create the eShop realm."""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                realm_payload = {
                    "realm": self.realm,
                    "enabled": True,
                    "displayName": f"{self.realm.title()} Realm",
                    "accessTokenLifespan": 7200,  # 2 hours
                    "accessTokenLifespanForImplicitFlow": 7200,  # 2 hours
                    "ssoSessionIdleTimeout": 7200,  # 2 hours
                    "ssoSessionMaxLifespan": 14400,  # 4 hours
                }
                
                logger.debug(f"[DEBUG] Creating realm with payload: {json.dumps(realm_payload)}")
                
                response = await client.post(
                    f"{self.base_url}/admin/realms",
                    headers={
                        "Authorization": f"Bearer {self.master_admin_token}",
                        "Content-Type": "application/json",
                    },
                    json=realm_payload,
                )
                
                logger.debug(f"[DEBUG] Realm creation response: {response.status_code}")
                
                if response.status_code == 201:
                    logger.info(f"[OK] Realm '{self.realm}' created")
                    return True
                elif response.status_code == 409:
                    logger.info(f"[INFO] Realm '{self.realm}' already exists")
                    # Update existing realm with token configuration
                    await self._update_realm_token_config()
                    return True
                else:
                    error_msg = response.text if hasattr(response, 'text') else str(response.content)
                    logger.error(
                        f"[FAILED] Failed to create realm: {response.status_code} - {error_msg}"
                    )
                    logger.error(f"[DEBUG] Request URL: {self.base_url}/admin/realms")
                    logger.error(f"[DEBUG] Request payload: {json.dumps(realm_payload)}")
                    logger.error(f"[DEBUG] Response headers: {dict(response.headers)}")
                    if self.master_admin_token:
                        logger.debug(f"[DEBUG] Token present (length: {len(self.master_admin_token)})")
                    else:
                        logger.error("[DEBUG] No master admin token!")
                    return False
        except httpx.HTTPStatusError as e:
            logger.error(f"[FAILED] Realm creation HTTP error: {e.response.status_code}")
            logger.error(f"[DEBUG] Response: {e.response.text}")
            return False
        except httpx.RequestError as e:
            logger.error(f"[FAILED] Realm creation request error: {e}")
            return False
        except Exception as e:
            logger.error(f"[FAILED] Realm creation failed: {e}")
            import traceback
            logger.error(f"[DEBUG] Traceback: {traceback.format_exc()}")
            return False

    async def _update_realm_token_config(self) -> None:
        """Update existing realm with extended token lifetimes."""
        try:
            async with httpx.AsyncClient() as client:
                # Get current realm configuration
                get_response = await client.get(
                    f"{self.base_url}/admin/realms/{self.realm}",
                    headers={
                        "Authorization": f"Bearer {self.master_admin_token}",
                        "Content-Type": "application/json",
                    },
                )
                
                if get_response.status_code == 200:
                    realm_config = get_response.json()
                    
                    # Update token lifetimes
                    realm_config.update({
                        "accessTokenLifespan": 7200,  # 2 hours
                        "accessTokenLifespanForImplicitFlow": 7200,  # 2 hours
                        "ssoSessionIdleTimeout": 7200,  # 2 hours
                        "ssoSessionMaxLifespan": 14400,  # 4 hours
                    })
                    
                    # Update the realm
                    update_response = await client.put(
                        f"{self.base_url}/admin/realms/{self.realm}",
                        headers={
                            "Authorization": f"Bearer {self.master_admin_token}",
                            "Content-Type": "application/json",
                        },
                        json=realm_config,
                    )
                    
                    if update_response.status_code == 204:
                        logger.info(f"[OK] Realm '{self.realm}' token configuration updated")
                    else:
                        logger.warning(f"[WARNING] Failed to update realm token config: {update_response.status_code}")
                else:
                    logger.warning(f"[WARNING] Could not get realm configuration: {get_response.status_code}")
        except Exception as e:
            logger.warning(f"[WARNING] Failed to update realm token configuration: {e}")

    async def _create_clients(self) -> bool:
        """Create OAuth/OIDC clients from credentials file."""
        try:
            creds = self._load_credentials()
            clients = creds.clients

            if not clients:
                logger.warning("[WARNING] No clients configured in credentials file")
                return False

            async with httpx.AsyncClient() as client_http:
                for client_config in clients:
                    # Check if client already exists
                    existing_client_response = await client_http.get(
                        f"{self.base_url}/admin/realms/{self.realm}/clients",
                        headers={"Authorization": f"Bearer {self.master_admin_token}"},
                        params={"clientId": client_config.client_id},
                    )
                    
                    if existing_client_response.status_code == 200:
                        existing_clients = existing_client_response.json()
                        if existing_clients:
                            # Update existing client to ensure it's configured correctly
                            client_id = existing_clients[0]["id"]
                            logger.info(f"[INFO] Client '{client_config.client_id}' already exists, updating configuration...")
                            
                            update_response = await client_http.put(
                                f"{self.base_url}/admin/realms/{self.realm}/clients/{client_id}",
                                headers={
                                    "Authorization": f"Bearer {self.master_admin_token}",
                                    "Content-Type": "application/json",
                                },
                                json={
                                    "clientId": client_config.client_id,
                                    "enabled": True,
                                    "publicClient": False,  # Ensure it's confidential
                                    "clientAuthenticatorType": "client-secret",
                                    "secret": client_config.client_secret,
                                    "redirectUris": client_config.redirect_uris,
                                    "webOrigins": client_config.web_origins,
                                    "serviceAccountsEnabled": client_config.service_accounts_enabled,
                                    "authorizationServicesEnabled": client_config.authorization_services_enabled,
                                    "directAccessGrantsEnabled": client_config.direct_access_grants_enabled,
                                    "standardFlowEnabled": client_config.standard_flow_enabled,
                                    "protocol": "openid-connect",
                                    "attributes": {
                                        "access.token.lifespan": "3600",
                                        "client.secret.creation.time": "1640995200",
                                        "user.info.response.signature.alg": "RS256"
                                    }
                                },
                            )
                            
                            if update_response.status_code == 204:
                                logger.info(f"[OK] Client '{client_config.client_id}' updated successfully")
                            else:
                                logger.warning(f"[WARNING] Failed to update client '{client_config.client_id}': {update_response.status_code}")
                            
                            # Update client secret
                            secret_response = await client_http.put(
                                f"{self.base_url}/admin/realms/{self.realm}/clients/{client_id}/client-secret",
                                headers={
                                    "Authorization": f"Bearer {self.master_admin_token}",
                                    "Content-Type": "application/json",
                                },
                                json={
                                    "value": client_config.client_secret,
                                    "temporary": False
                                },
                            )
                            
                            if secret_response.status_code == 204:
                                logger.info(f"[OK] Client secret updated for '{client_config.client_id}'")
                            elif secret_response.status_code == 404:
                                # Client doesn't exist yet or secret endpoint not available - this is expected for new clients
                                logger.debug(f"[DEBUG] Client secret endpoint not found for '{client_config.client_id}' (client may not exist yet)")
                            else:
                                logger.warning(f"[WARNING] Failed to update client secret for '{client_config.client_id}': {secret_response.status_code}")
                            
                            continue
                    
                    # Create new client if it doesn't exist
                    response = await client_http.post(
                        f"{self.base_url}/admin/realms/{self.realm}/clients",
                        headers={
                            "Authorization": f"Bearer {self.master_admin_token}",
                            "Content-Type": "application/json",
                        },
                        json={
                            "clientId": client_config.client_id,
                            "enabled": True,
                            "publicClient": False,  # Ensure it's confidential
                            "clientAuthenticatorType": "client-secret",
                            "secret": client_config.client_secret,
                            "redirectUris": client_config.redirect_uris,
                            "webOrigins": client_config.web_origins,
                            "serviceAccountsEnabled": client_config.service_accounts_enabled,
                            "authorizationServicesEnabled": client_config.authorization_services_enabled,
                            "directAccessGrantsEnabled": client_config.direct_access_grants_enabled,
                            "standardFlowEnabled": client_config.standard_flow_enabled,
                            "protocol": "openid-connect",
                            "attributes": {
                                "access.token.lifespan": "7200",  # 2 hours
                                "client.secret.creation.time": "1640995200",
                                "user.info.response.signature.alg": "RS256"
                            }
                        },
                    )
                    if response.status_code == 201:
                        logger.info(f"[OK] Client '{client_config.client_id}' created")
                    elif response.status_code == 409:
                        logger.info(
                            f"[INFO] Client '{client_config.client_id}' already exists"
                        )
                    else:
                        logger.error(
                            f"[FAILED] Failed to create client '{client_config.client_id}': {response.status_code}"
                        )

            return True
        except Exception as e:
            logger.error(f"[FAILED] Client creation failed: {e}")
            return False

    async def _verify_client_configuration(self) -> bool:
        """Verify and fix client configuration to ensure it's confidential."""
        try:
            creds = self._load_credentials()
            clients = creds.clients

            if not clients:
                logger.warning("[WARNING] No clients configured for verification")
                return False

            async with httpx.AsyncClient() as client:
                for client_config in clients:
                    # Get client details
                    client_response = await client.get(
                        f"{self.base_url}/admin/realms/{self.realm}/clients",
                        headers={"Authorization": f"Bearer {self.master_admin_token}"},
                        params={"clientId": client_config.client_id},
                    )
                    client_response.raise_for_status()
                    clients_data = client_response.json()
                    if not clients_data:
                        logger.warning(f"[WARNING] Client '{client_config.client_id}' not found")
                        continue

                    client_id = clients_data[0]["id"]
                    client_data = clients_data[0]

                    # Check if client is public (this is the problem)
                    if client_data.get("publicClient", True):
                        logger.warning(f"[WARNING] Client '{client_config.client_id}' is configured as public, fixing...")
                        
                        # Update client to be confidential
                        update_response = await client.put(
                            f"{self.base_url}/admin/realms/{self.realm}/clients/{client_id}",
                            headers={
                                "Authorization": f"Bearer {self.master_admin_token}",
                                "Content-Type": "application/json",
                            },
                            json={
                                "clientId": client_config.client_id,
                                "enabled": True,
                                "publicClient": False,  # Make it confidential
                                "clientAuthenticatorType": "client-secret",
                                "secret": client_config.client_secret,
                                "redirectUris": client_config.redirect_uris,
                                "webOrigins": client_config.web_origins,
                                "serviceAccountsEnabled": client_config.service_accounts_enabled,
                                "authorizationServicesEnabled": client_config.authorization_services_enabled,
                                "directAccessGrantsEnabled": client_config.direct_access_grants_enabled,
                                "standardFlowEnabled": client_config.standard_flow_enabled,
                                "protocol": "openid-connect",
                                "attributes": {
                                    "access.token.lifespan": "3600",
                                    "client.secret.creation.time": "1640995200",
                                    "user.info.response.signature.alg": "RS256"
                                }
                            },
                        )
                        
                        if update_response.status_code == 204:
                            logger.info(f"[OK] Client '{client_config.client_id}' updated to confidential")
                            
                            # Update client secret
                            secret_response = await client.put(
                                f"{self.base_url}/admin/realms/{self.realm}/clients/{client_id}/client-secret",
                                headers={
                                    "Authorization": f"Bearer {self.master_admin_token}",
                                    "Content-Type": "application/json",
                                },
                                json={
                                    "value": client_config.client_secret,
                                    "temporary": False
                                },
                            )
                            
                            if secret_response.status_code == 204:
                                logger.info(f"[OK] Client secret updated for '{client_config.client_id}'")
                            elif secret_response.status_code == 404:
                                # Client doesn't exist yet or secret endpoint not available - this is expected for new clients
                                logger.debug(f"[DEBUG] Client secret endpoint not found for '{client_config.client_id}' (client may not exist yet)")
                            else:
                                logger.warning(f"[WARNING] Failed to update client secret for '{client_config.client_id}': {secret_response.status_code}")
                        else:
                            logger.error(f"[FAILED] Failed to update client '{client_config.client_id}': {update_response.status_code}")
                    else:
                        logger.info(f"[OK] Client '{client_config.client_id}' is already configured as confidential")

            return True
        except Exception as e:
            logger.error(f"[FAILED] Client configuration verification failed: {e}")
            return False

    async def _configure_client_permissions(self) -> bool:
        """Configure client service account permissions for admin operations."""
        try:
            creds = self._load_credentials()
            clients = creds.clients

            if not clients:
                logger.warning("[WARNING] No clients configured for permissions setup")
                return False

            async with httpx.AsyncClient() as client:
                for client_config in clients:
                    # Get the client ID
                    client_response = await client.get(
                        f"{self.base_url}/admin/realms/{self.realm}/clients",
                        headers={"Authorization": f"Bearer {self.master_admin_token}"},
                        params={"clientId": client_config.client_id},
                    )
                    client_response.raise_for_status()
                    clients_data = client_response.json()
                    if not clients_data:
                        logger.warning(f"[WARNING] Client '{client_config.client_id}' not found")
                        continue

                    client_id = clients_data[0]["id"]

                    # Get realm-management client
                    realm_mgmt_response = await client.get(
                        f"{self.base_url}/admin/realms/{self.realm}/clients",
                        headers={"Authorization": f"Bearer {self.master_admin_token}"},
                        params={"clientId": "realm-management"},
                    )
                    realm_mgmt_response.raise_for_status()
                    realm_mgmt_clients = realm_mgmt_response.json()
                    if not realm_mgmt_clients:
                        logger.warning("[WARNING] realm-management client not found")
                        continue

                    realm_mgmt_client_id = realm_mgmt_clients[0]["id"]

                    # Get service account user for the client
                    service_account_response = await client.get(
                        f"{self.base_url}/admin/realms/{self.realm}/clients/{client_id}/service-account-user",
                        headers={"Authorization": f"Bearer {self.master_admin_token}"},
                    )
                    service_account_response.raise_for_status()
                    service_account_user = service_account_response.json()
                    service_account_user_id = service_account_user["id"]

                    # Assign realm-admin role to service account
                    admin_role_response = await client.get(
                        f"{self.base_url}/admin/realms/{self.realm}/clients/{realm_mgmt_client_id}/roles/realm-admin",
                        headers={"Authorization": f"Bearer {self.master_admin_token}"},
                    )
                    admin_role_response.raise_for_status()
                    admin_role = admin_role_response.json()

                    # Check if role is already assigned
                    current_roles_response = await client.get(
                        f"{self.base_url}/admin/realms/{self.realm}/users/{service_account_user_id}/role-mappings/clients/{realm_mgmt_client_id}",
                        headers={"Authorization": f"Bearer {self.master_admin_token}"},
                    )
                    if current_roles_response.status_code == 200:
                        current_roles = current_roles_response.json()
                        if any(role["name"] == "realm-admin" for role in current_roles):
                            logger.info(f"[INFO] Realm-admin role already assigned to service account for '{client_config.client_id}'")
                            continue

                    # Assign realm-admin role to service account
                    role_payload = {
                        "id": admin_role["id"],
                        "name": "realm-admin",
                        "description": admin_role.get("description", ""),
                        "composite": admin_role.get("composite", False),
                        "clientRole": True,
                    }

                    assign_response = await client.post(
                        f"{self.base_url}/admin/realms/{self.realm}/users/{service_account_user_id}/role-mappings/clients/{realm_mgmt_client_id}",
                        headers={
                            "Authorization": f"Bearer {self.master_admin_token}",
                            "Content-Type": "application/json",
                        },
                        json=[role_payload],
                    )

                    if assign_response.status_code == 204:
                        logger.info(f"[OK] Realm-admin role assigned to service account for '{client_config.client_id}'")
                    else:
                        logger.warning(f"[WARNING] Failed to assign realm-admin role to service account for '{client_config.client_id}': {assign_response.status_code}")

            return True
        except Exception as e:
            logger.error(f"[FAILED] Client permissions configuration failed: {e}")
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
                    logger.info(f"[OK] Realm admin user '{realm_admin.username}' created")
                    # Assign realm-admin role to realm admin (this gives them admin permissions)
                    await self._assign_realm_admin_role(
                        client, realm_admin.username
                    )
                    return True
                elif response.status_code == 409:
                    logger.info(
                        f"[INFO] Realm admin user '{realm_admin.username}' already exists"
                    )
                    # Ensure realm-admin role is assigned to existing realm admin
                    await self._assign_realm_admin_role(
                        client, realm_admin.username
                    )
                    # Update password for existing realm admin
                    await self._update_user_password(
                        client, realm_admin.username, realm_admin.password, use_master_admin=True
                    )
                    return True
                else:
                    logger.error(
                        f"[FAILED] Failed to create realm admin: {response.status_code}"
                    )
                    return False
        except Exception as e:
            logger.error(f"[FAILED] Realm admin creation failed: {e}")
            return False

    async def _create_roles(self) -> bool:
        """Create RBAC roles from credentials file using realm admin (or master admin as fallback)."""
        try:
            creds = self._load_credentials()
            roles = creds.roles

            if not roles:
                logger.warning("[WARNING] No roles configured in credentials file")
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
                        logger.info(f"[OK] Role '{role.name}' created by realm admin")
                    elif response.status_code == 409:
                        logger.info(f"[INFO] Role '{role.name}' already exists")
                    else:
                        logger.warning(
                            f"[WARNING] Failed to create role '{role.name}': {response.status_code}"
                        )

            return True
        except Exception as e:
            logger.error(f"[FAILED] Role creation failed: {e}")
            return False

    async def _create_users(self) -> bool:
        """Create users with roles from credentials file using realm admin (or master admin as fallback)."""
        try:
            creds = self._load_credentials()
            users = creds.users

            if not users:
                logger.warning("[WARNING] No users configured in credentials file")
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
                            f"[OK] User '{user_config.username}' created by realm admin"
                        )
                    elif response.status_code == 409:
                        logger.info(f"[INFO] User '{user_config.username}' already exists")
                        # Update password for existing user
                        await self._update_user_password(
                            client, user_config.username, user_config.password
                        )
                    else:
                        logger.warning(
                            f"[WARNING] Failed to create user '{user_config.username}': {response.status_code}"
                        )
                        continue

                    # Assign roles to user with retry logic
                    for role_name in user_config.roles:
                        await self._assign_role_to_user_with_retry(
                            client, user_config.username, role_name
                        )

            return True
        except Exception as e:
            logger.error(f"[FAILED] User creation failed: {e}")
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
                    logger.info(f"[OK] Password updated for user '{username}'")
        except Exception as e:
            logger.warning(f"[WARNING] Failed to update password for '{username}': {e}")

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
                        f"[WARNING] Role assignment attempt {attempt + 1} failed for '{username}' -> '{role_name}'"
                    )
                    if attempt < max_retries - 1:
                        await asyncio.sleep(retry_delay)
                        retry_delay *= 2  # Exponential backoff
            except Exception as e:
                logger.warning(
                    f"[WARNING] Role assignment attempt {attempt + 1} failed for '{username}' -> '{role_name}': {e}"
                )
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff

        logger.error(
            f"[FAILED] Failed to assign role '{role_name}' to '{username}' after {max_retries} attempts"
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
                logger.warning(f"[WARNING] User '{username}' not found for role assignment")
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
                        f"[INFO] Role '{role_name}' already assigned to user '{username}'"
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
                    f"[OK] Role '{role_name}' assigned to user '{username}' by realm admin"
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
                            f"[OK] Verified: Role '{role_name}' successfully assigned to '{username}'"
                        )
                        return True
                    else:
                        logger.error(
                            f"[FAILED] Role assignment verification failed for '{username}' -> '{role_name}'"
                        )
                        return False
                else:
                    logger.error(
                        f"[FAILED] Could not verify role assignment for '{username}' -> '{role_name}'"
                    )
                    return False
            else:
                logger.error(
                    f"[FAILED] Failed to assign role '{role_name}' to '{username}': {assign_response.status_code} - {assign_response.text}"
                )
                return False

        except Exception as e:
            logger.error(f"[FAILED] Failed to assign role '{role_name}' to '{username}': {e}")
            return False

    async def _setup_role_hierarchy(self) -> None:
        """Setup role hierarchy from credentials file using realm admin (or master admin as fallback)."""
        try:
            creds = self._load_credentials()
            role_hierarchy = creds.role_hierarchy

            if not role_hierarchy:
                logger.info("[INFO] No role hierarchy configured")
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
                            f"[WARNING] Parent role '{parent_role_name}' not found in role hierarchy setup"
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
                                f"[WARNING] Child role '{child_role_name}' not found for parent '{parent_role_name}'"
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
                                f"[OK] Role '{parent_role_name}' configured as composite (includes: {', '.join([r['name'] for r in composite_roles])})"
                            )
                        else:
                            logger.warning(
                                f"[WARNING] Failed to setup hierarchy for '{parent_role_name}': {response.status_code}"
                            )

        except Exception as e:
            logger.warning(f"[WARNING] Failed to setup role hierarchy: {e}")

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

                logger.info("[VERIFY] Verifying Keycloak setup...")
                
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
                                f"[OK] User '{username}' has roles: {', '.join(role_names) if role_names else 'none (only default roles)'}"
                            )

                            # Test token generation for each user
                            await self._test_user_token(username)

        except Exception as e:
            logger.warning(f"[WARNING] Setup verification failed: {e}")

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
                logger.warning(f"[WARNING] Could not find password for user '{username}'")
                return

            # Use the first client for authentication
            if not creds.clients:
                logger.warning("[WARNING] No clients configured for token testing")
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
                                    f"[OK] User '{username}' token includes roles: {', '.join(user_roles)}"
                                )
                            else:
                                logger.info(
                                    f"[INFO] User '{username}' token generated successfully (no custom roles found)"
                                )
                        except Exception as e:
                            logger.warning(f"[WARNING] Could not decode token for '{username}': {e}")
                else:
                    logger.warning(
                        f"[WARNING] Could not generate token for '{username}': {response.status_code}"
                    )
        except Exception as e:
            logger.warning(f"[WARNING] Token test failed for '{username}': {e}")


async def setup_keycloak_async(credentials_path: str | None = None) -> bool:
    """Async function to setup Keycloak with credentials from file.

    Args:
        credentials_path: Optional path to credentials file

    Returns:
        True if setup was successful, False otherwise
    """
    setup = KeycloakSetup(credentials_path)
    return await setup.setup_keycloak()
